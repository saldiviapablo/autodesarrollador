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

    [Parameter(Mandatory = $false)]
    [string]$TargetUrl = "https://chatgpt.com",

    [Parameter(Mandatory = $false)]
    [string]$MockResponse = "",

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 45,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = "",

    [Parameter(Mandatory = $false)]
    [switch]$RawPrompt
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
    $ConsultationId = "consult-" + (Get-Date).ToString("yyyyMMdd-HHmmss")
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
$stateObj = $null
$autopilotDir = ""
if (-not [string]::IsNullOrWhiteSpace($StatePath) -and (Test-Path -LiteralPath $StatePath)) {
    $autopilotDir = Split-Path -Parent $StatePath
    try {
        $stateObj = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $stateObj.PSObject.Properties['chatgpt']) {
            $stateObj | Add-Member -MemberType NoteProperty -Name "chatgpt" -Value ([PSCustomObject]@{
                queries_used = 0
                max_queries  = $MaxQueries
            })
        }

        # Comprobar límite presupuestario antes de abrir nada
        if ($Action -eq "consult" -and $stateObj.chatgpt.queries_used -ge $stateObj.chatgpt.max_queries) {
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
    } catch { }
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

$proc = [System.Diagnostics.Process]::Start($pInfo)
$stdoutTask = $proc.StandardOutput.ReadToEndAsync()
$stderrTask = $proc.StandardError.ReadToEndAsync()

$procExited = $proc.WaitForExit($TimeoutSeconds * 1000 + 8000)
if (-not $procExited) {
    try { $proc.Kill() } catch {}
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
if ($resultObj.status -eq "SUCCESS" -and $Action -eq "consult" -and $stateObj -and $autopilotDir) {
    $stateObj.chatgpt.queries_used += 1
    $null = Write-AtomicState -StateObj $stateObj -AutopilotDir $autopilotDir -ValidateTransition $false

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
