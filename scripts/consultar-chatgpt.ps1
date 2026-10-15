# ==============================================================================
# scripts/consultar-chatgpt.ps1 — Herramienta Reusable de Consulta a ChatGPT
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Question = "",

    [Parameter(Mandatory = $false)]
    [string]$Context = "",

    [Parameter(Mandatory = $false)]
    [string]$Purpose = "Revisión técnica y segunda opinión arquitectónica",

    [Parameter(Mandatory = $false)]
    [string]$ConsultationId = "",

    [Parameter(Mandatory = $false)]
    [string]$StatePath = "",

    [Parameter(Mandatory = $false)]
    [int]$MaxQueries = 5,

    [Parameter(Mandatory = $false)]
    [string]$Action = "consult",

    [string]$HumanEvidencePath = "",

    [Parameter(Mandatory = $false)]
    [string]$TargetUrl = "https://chatgpt.com",

    [Parameter(Mandatory = $false)]
    [string]$MockResponse = "",

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 45,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "",

    [Parameter(Mandatory = $false)]
    [switch]$RawPrompt,
    [switch]$NewConversation
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

. (Join-Path $infraRoot "scripts\state-manager.ps1")
$bridgeJs = Join-Path $infraRoot "tools\chatgpt-bridge.js"
$profileDir = Join-Path $infraRoot "data\browser\HERMES-CHATGPT"

if ([string]::IsNullOrWhiteSpace($ConsultationId)) {
    $ConsultationId = "consult-" + (Get-Date).ToString("yyyyMMdd-HHmmss") + '-' + [guid]::NewGuid().ToString('N')
}

# 1. VERIFICACIÓN ESTRICTA DE DOMAIN LOCK
. (Join-Path $scriptDir 'chatgpt-domain-policy.ps1')
$isAllowedDomain = Test-ChatGptUrl -Url $TargetUrl

if (-not $isAllowedDomain) {
    $blockedObj = [ordered]@{
        status          = "DOMAIN_BLOCKED"
        error           = "Navegación rechazada: dominio no autorizado por política estricta de Domain Lock ($TargetUrl)."
        consultation_id = $ConsultationId
        timestamp       = (Get-Date).ToString("o")
    }
    return [PSCustomObject]$blockedObj
}

# 2. ENFORCEMENT DE PRESUPUESTO GLOBAL DE CONSULTAS (Section 22)
$humanConfirmedRetry=$false
$preSendRetry=$false
if($Action -eq 'consult' -and [string]::IsNullOrWhiteSpace($MockResponse)){
    $lookupRaw=& node.exe $bridgeJs --action consultation-status --consultation-id $ConsultationId --url $TargetUrl
    $lookup=($lookupRaw -join "`n")|ConvertFrom-Json
    if($lookup.status -in @('ALREADY_SENT','UNKNOWN_DELIVERY')){
        return [PSCustomObject]@{Status=$lookup.status;ConsultationId=$ConsultationId;ResultObj=$lookup;RawJson=($lookupRaw -join "`n");Response='';Error=''}
    }
    $preSendRetry=($lookup.status -eq 'RETRY_SAFE' -and $lookup.retry_kind -eq 'PRE_SEND')
    $humanConfirmedRetry=($lookup.status -eq 'RETRY_SAFE' -and -not $preSendRetry)
    if($lookup.status -notin @('NOT_SEEN','RETRY_SAFE')){throw 'CONSULTATION_LEDGER_LOOKUP_FAILED_CLOSED'}
    if(($humanConfirmedRetry -or $preSendRetry) -and [string]::IsNullOrWhiteSpace($StatePath)){throw 'CONFIRMED_RETRY_REQUIRES_ORIGINAL_BUDGET_STATE'}
}
$stateObj = $null
$autopilotDir = ""
if(-not [string]::IsNullOrWhiteSpace($StatePath) -and -not(Test-Path -LiteralPath $StatePath)){
    return [PSCustomObject]@{Status='INVALID_STATE_DENY';Error='Explicit STATE path is missing';ConsultationId=$ConsultationId}
}
if (-not [string]::IsNullOrWhiteSpace($StatePath) -and (Test-Path -LiteralPath $StatePath)) {
    $autopilotDir = Split-Path -Parent $StatePath
    $keyBytes=[Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($StatePath).ToLowerInvariant())
    $keyHash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($keyBytes))).Replace('-','')
    $budgetMutex=New-Object Threading.Mutex($false,('Local\DesarrolladorAutonomo_ChatGPTBudget_'+$keyHash))
    $budgetHeld=$false
    try {
        try{$budgetHeld=$budgetMutex.WaitOne(10000)}catch [Threading.AbandonedMutexException]{$budgetHeld=$true}
        if(-not $budgetHeld){throw 'CHATGPT_BUDGET_LOCK_TIMEOUT'}
        $stateObj = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if((Test-FileSchemaValidation -filePath $StatePath -schemaPath (Join-Path $infraRoot 'schemas/autopilot-state.schema.json')) -ne 'VALID'){throw 'STATE_SCHEMA_DENIED'}
        $policyJson=& C:/Python314/python.exe (Join-Path $infraRoot 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $infraRoot 'config/security.yaml')
        $policy=($policyJson -join "`n")|ConvertFrom-Json
        $MaxQueries=[Math]::Min($policy.chatgpt.max_queries,[Math]::Max(0,$MaxQueries))
        if (-not $stateObj.PSObject.Properties['chatgpt']) {
            $stateObj | Add-Member -MemberType NoteProperty -Name "chatgpt" -Value ([PSCustomObject]@{
                queries_used = 0
                max_queries  = $MaxQueries
            })
        }
        $stateObj.chatgpt.max_queries=[Math]::Min($stateObj.chatgpt.max_queries,$MaxQueries)

        # Comprobar límite presupuestario antes de abrir nada
        if(($humanConfirmedRetry -or $preSendRetry) -and ($stateObj.chatgpt.queries_used -lt 1 -or $stateObj.chatgpt.queries_used -gt $stateObj.chatgpt.max_queries)){throw 'CONFIRMED_RETRY_BUDGET_INVALID'}
        if ($Action -eq "consult" -and -not ($humanConfirmedRetry -or $preSendRetry) -and $stateObj.chatgpt.queries_used -ge $stateObj.chatgpt.max_queries) {
            $budgetExceededObj = [ordered]@{
                status          = "CHATGPT_BUDGET_EXCEEDED"
                error           = "Presupuesto de consultas a ChatGPT agotado para este run ($($stateObj.chatgpt.queries_used)/$($stateObj.chatgpt.max_queries))."
                consultation_id = $ConsultationId
                queries_used    = $stateObj.chatgpt.queries_used
                max_queries     = $stateObj.chatgpt.max_queries
                timestamp       = (Get-Date).ToString("o")
            }

            # Registrar evento de presupuesto excedido si hay autopilotDir
            if ($autopilotDir) {
                $null = Add-AutopilotEvent `
                    -AutopilotDir $autopilotDir `
                    -RunId $stateObj.run_id `
                    -Actor "chatgpt-guard" `
                    -Type "CHATGPT_BUDGET_EXCEEDED" `
                    -Payload @{
                        queries_used = $stateObj.chatgpt.queries_used
                        max_queries  = $stateObj.chatgpt.max_queries
                        consultation = $ConsultationId
                    }
            }

            return [PSCustomObject]$budgetExceededObj
        }
        if($Action -eq 'consult' -and -not ($humanConfirmedRetry -or $preSendRetry)){
            $stateObj.chatgpt.queries_used += 1
            $null=Write-AtomicState -StateObj $stateObj -AutopilotDir $autopilotDir -ValidateTransition $false
        }
    } catch { return [PSCustomObject]@{Status='INVALID_STATE_DENY';Error=$_.Exception.Message;ConsultationId=$ConsultationId} }
    finally{if($budgetHeld){$budgetMutex.ReleaseMutex()};$budgetMutex.Dispose()}
}

# 3. SANITIZACIÓN DE SECRETOS ANTES DE ENVIAR (Section 21)
function Redact-SecretsText([string]$text) {
    if ([string]::IsNullOrWhiteSpace($text)) { return "" }
    $t = $text
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, 'sk-[a-zA-Z0-9]{20,}', '[REDACTED]')
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, 'ghp_[a-zA-Z0-9]{20,}', '[REDACTED]')
    $t = [System.Text.RegularExpressions.Regex]::Replace($t, '(?i)(api[_-]?key|password|secret|bearer)\s*[:=]\s*[^\s,;]+', '$1: [REDACTED]')
    return $t
}

$sanitizedQuestion = Redact-SecretsText $Question
$sanitizedContext = Redact-SecretsText $Context

# 4. EJECUTAR PUENTE CDP NODE.JS
$nodeExe = "node.exe"
$nodeArgs = [System.Collections.Generic.List[string]]::new()
$nodeArgs.Add($bridgeJs)
$nodeArgs.Add("--action")
$nodeArgs.Add($Action)
$nodeArgs.Add("--profile-dir")
$nodeArgs.Add($profileDir)
$nodeArgs.Add("--url")
$nodeArgs.Add($TargetUrl)
$nodeArgs.Add("--consultation-id")
$nodeArgs.Add($ConsultationId)
$nodeArgs.Add("--purpose")
$nodeArgs.Add($Purpose)
$nodeArgs.Add("--timeout")
$nodeArgs.Add("$TimeoutSeconds")
if($HumanEvidencePath){$nodeArgs.Add('--human-evidence');$nodeArgs.Add($HumanEvidencePath)}

if (-not [string]::IsNullOrWhiteSpace($sanitizedQuestion)) {
    $qBytes = [System.Text.Encoding]::UTF8.GetBytes($sanitizedQuestion)
    $nodeArgs.Add("--question-b64")
    $nodeArgs.Add([Convert]::ToBase64String($qBytes))
}
if (-not [string]::IsNullOrWhiteSpace($sanitizedContext)) {
    $cBytes = [System.Text.Encoding]::UTF8.GetBytes($sanitizedContext)
    $nodeArgs.Add("--context-b64")
    $nodeArgs.Add([Convert]::ToBase64String($cBytes))
}
if (-not [string]::IsNullOrWhiteSpace($MockResponse)) {
    $nodeArgs.Add("--mock-response")
    $nodeArgs.Add($MockResponse)
}
if($NewConversation){$nodeArgs.Add('--new-conversation')}
if ($RawPrompt) {
    $nodeArgs.Add("--raw-prompt")
}

$pInfo = New-Object System.Diagnostics.ProcessStartInfo
$pInfo.FileName = $nodeExe
$pInfo.Arguments = ($nodeArgs | ForEach-Object {
    if ($_ -match '\s') { "`"$_`"" } else { $_ }
}) -join " "
$pInfo.RedirectStandardOutput = $true
$pInfo.RedirectStandardError = $true
$pInfo.UseShellExecute = $false
$pInfo.CreateNoWindow = $true
$pInfo.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$pInfo.StandardErrorEncoding = [System.Text.Encoding]::UTF8

# The logical attempt was reserved atomically under the per-STATE budget mutex before launch.

$parentTraceFile=''
if($Action -eq 'consult' -and [string]::IsNullOrWhiteSpace($MockResponse)){
    $idHash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($ConsultationId)))).Replace('-','').ToLowerInvariant()
    $parentTraceFile=Join-Path $infraRoot ('runtime/chatgpt-consultations/'+$idHash+'.parent.trace.jsonl')
    if((Test-Path -LiteralPath $parentTraceFile) -and ((Get-Item -LiteralPath $parentTraceFile).Attributes -band [IO.FileAttributes]::ReparsePoint)){throw 'TRACE_PATH_DENIED'}
}
function Write-ParentTrace([string]$Event){
    if(-not $parentTraceFile){return}
    $line=@{event=$Event;consultation_id=$ConsultationId;at=[datetimeoffset]::UtcNow.ToString('o');mono_ms=([Diagnostics.Stopwatch]::GetTimestamp()*1000.0/[Diagnostics.Stopwatch]::Frequency);pid=$PID}|ConvertTo-Json -Compress
    $stream=[IO.File]::Open($parentTraceFile,[IO.FileMode]::Append,[IO.FileAccess]::Write,[IO.FileShare]::Read)
    try{$bytes=[Text.Encoding]::UTF8.GetBytes($line+"`n");$stream.Write($bytes,0,$bytes.Length);$stream.Flush($true)}finally{$stream.Dispose()}
}
Write-ParentTrace 'PARENT_START'
$proc = [System.Diagnostics.Process]::Start($pInfo)
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()

$budgetRaw=& node.exe $bridgeJs --action budget --timeout $TimeoutSeconds
$transportBudget=($budgetRaw -join "`n")|ConvertFrom-Json
if($transportBudget.parent_ms -le ($transportBudget.internal_ms+$transportBudget.cleanup_margin_ms)){throw 'INVALID_TRANSPORT_DEADLINES'}
. (Join-Path $scriptDir 'wait-chatgpt-child.ps1')
$procExited = Wait-ChatGptChild $proc ([int]$transportBudget.parent_ms) {param($event) Write-ParentTrace $event}
Write-ParentTrace 'CHILD_WAIT_FINISHED'
if (-not $procExited) {
    try { $proc.Kill();$null=$proc.WaitForExit(3000) } catch {}
    if($Action -eq 'consult' -and [string]::IsNullOrWhiteSpace($MockResponse)){
        $lookupRaw=& node.exe $bridgeJs --action consultation-status --consultation-id $ConsultationId --url $TargetUrl
        $lookup=($lookupRaw -join "`n")|ConvertFrom-Json
        if(-not $lookup.message_sent -and $lookup.send_attempts -ge 1){$lookup.status='UNKNOWN_DELIVERY'};$lookup.no_resend=$true
        return [PSCustomObject]@{Status=$lookup.status;Error='Bridge parent deadline expired; no resend';ConsultationId=$ConsultationId;ResultObj=$lookup;Response='';RawJson=($lookup|ConvertTo-Json -Depth 8)}
    }
    return [PSCustomObject]@{
        Status         = "TIMEOUT"
        Error          = "Timeout ejecutando chatgpt-bridge.js tras ${TimeoutSeconds}s"
        ConsultationId = $ConsultationId
        ResultObj      = [PSCustomObject]@{ status = "TIMEOUT"; response = ""; source = ""; message_sent = $false; response_received = $false }
        Response       = ""
        RawJson        = ""
    }
}

$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result

$resultObj = $null
try {
    $resultObj = $stdout | ConvertFrom-Json
} catch {
    return [PSCustomObject]@{
        Status         = "ERROR"
        Error          = "Respuesta no JSON del puente: $stdout ($stderr)"
        ConsultationId = $ConsultationId
        ResultObj      = [PSCustomObject]@{ status = "ERROR"; response = ""; source = ""; message_sent = $false; response_received = $false }
        Response       = ""
        RawJson        = $stdout
    }
}

# 5. ACTUALIZAR CONTADOR DE PRESUPUESTO SI LA CONSULTA FUE EXITOSA
if (($resultObj.status -in @("SUCCESS","SENT_CONFIRMED") -or ($resultObj.status -eq 'UNKNOWN_DELIVERY' -and $resultObj.message_sent -and -not $resultObj.deduplicated)) -and $Action -eq "consult" -and $stateObj -and $autopilotDir) {
    $eventMutex=New-Object Threading.Mutex($false,('Local\DesarrolladorAutonomo_ChatGPTBudget_'+$keyHash))
    $eventHeld=$false
    try{
        try{$eventHeld=$eventMutex.WaitOne(10000)}catch [Threading.AbandonedMutexException]{$eventHeld=$true}
        if(-not $eventHeld){throw 'CHATGPT_EVENT_LOCK_TIMEOUT'}
    # Registrar evento CHATGPT_CONSULTED
    $null = Add-AutopilotEvent `
        -AutopilotDir $autopilotDir `
        -RunId $stateObj.run_id `
        -Actor "chatgpt-client" `
        -Type "CHATGPT_CONSULTED" `
        -Payload @{
            consultation_id = $ConsultationId
            queries_used    = $stateObj.chatgpt.queries_used
            max_queries     = $stateObj.chatgpt.max_queries
            purpose         = $Purpose
        }
    }finally{if($eventHeld){$eventMutex.ReleaseMutex()};$eventMutex.Dispose()}
}

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $outDir = Split-Path -Parent $OutputPath
    if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($OutputPath, $stdout, [System.Text.Encoding]::UTF8)
}

return [PSCustomObject]@{
    Status                  = $resultObj.status
    Response                = $resultObj.response
    ConsultationId          = $ConsultationId
    Error                   = $resultObj.error
    ResultObj               = $resultObj
    RawJson                 = $stdout
    SourceTextEqualsDomText = $resultObj.source_text_equals_dom_text
    DomText                 = $resultObj.dom_text
    SourceText              = $resultObj.source_text
}
