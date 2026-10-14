# ==============================================================================
# scripts/invoke-qwen-code.ps1 — Wrapper de Invocación para Qwen Code CLI
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 5 — Qwen Code CLI)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Prompt = "",

    [Parameter(Mandatory = $false)]
    [string]$WorkingDir = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("plan", "default", "auto-edit", "auto", "yolo")]
    [string]$ApprovalMode = "plan",

    [Parameter(Mandatory = $false)]
    [ValidateSet("text", "json", "stream-json")]
    [string]$OutputFormat = "json",

    [Parameter(Mandatory = $false)]
    [string]$MaxWallTime = "300s",

    [Parameter(Mandatory = $false)]
    [int]$MaxSessionTurns = 0,

    [Parameter(Mandatory = $false)]
    [int]$MaxToolCalls = -1,

    [Parameter(Mandatory = $false)]
    [string]$SessionId = "",

    [Parameter(Mandatory = $false)]
    [switch]$ContinueSession,

    [Parameter(Mandatory = $false)]
    [string]$ResumeSession = "",

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 360,

    [Parameter(Mandatory = $false)]
    [switch]$SkipLock,

    [Parameter(Mandatory = $false)]
    [string[]]$ExtraArgs = @(),
    [string]$ResearchProject = ''
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

# 1. Leer config/system.yaml usando Python + PyYAML
$systemYaml = Join-Path $infraRoot "config\system.yaml"
if (-not (Test-Path -LiteralPath $systemYaml)) {
    throw "No se encontró el archivo de configuración: $systemYaml"
}

$pythonExe = "C:\Python314\python.exe"
$pyCode = 'import yaml, json, sys; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding=\"utf-8\"))))'
$configJson = & $pythonExe -c $pyCode "$systemYaml"
$sysConfig = $configJson | ConvertFrom-Json

$hostIp = $sysConfig.llama.host
$port = $sysConfig.llama.port
$modelName = $sysConfig.llama.alias
$baseUrl = "http://${hostIp}:${port}/v1"

# 2. Localizar Qwen Code CLI
$nodeExe = "C:\Program Files\nodejs\node.exe"
if (-not (Test-Path $nodeExe)) {
    $nodeCmd = Get-Command "node" -ErrorAction SilentlyContinue
    if ($nodeCmd) { $nodeExe = $nodeCmd.Source } else { throw "Node.js no encontrado." }
}

$cliEntry = "C:\Users\Pc\AppData\Roaming\npm\node_modules\@qwen-code\qwen-code\cli-entry.js"
if (-not (Test-Path $cliEntry)) {
    $qwenCmd = Get-Command "qwen" -ErrorAction SilentlyContinue
    if ($qwenCmd) {
        $cliDir = Split-Path -Parent $qwenCmd.Source
        $altEntry = Join-Path $cliDir "node_modules\@qwen-code\qwen-code\cli-entry.js"
        if (Test-Path $altEntry) { $cliEntry = $altEntry }
    }
}
if (-not (Test-Path $cliEntry)) {
    throw "cli-entry.js de @qwen-code/qwen-code no encontrado en $cliEntry"
}

# 3. Construir argumentos CLI
$researchDispatchId=''
if($ResearchProject){
    if([IO.Path]::GetFullPath($ResearchProject) -ne [IO.Path]::GetFullPath($WorkingDir)){throw 'RESEARCH_WORKSPACE_MISMATCH'}
    if($SessionId -or $ContinueSession -or $ResumeSession){throw 'RESEARCH_FRESH_SESSION_REQUIRED'}
    . (Join-Path $infraRoot 'scripts/state-manager.ps1')
    if((Sanitize-StringContent $Prompt) -cne $Prompt){throw 'SECRET_IN_RESEARCH_WORKER_INPUT'}
    $SessionId=[guid]::NewGuid().ToString();$researchDispatchId=[guid]::NewGuid().ToString()
    $dispatchDir=Join-Path $ResearchProject ('.autopilot/evidence/worker-dispatch/'+$researchDispatchId)
    $initProof=& $pythonExe (Join-Path $infraRoot 'runner/research-handoff.py') init --project $ResearchProject --dispatch $researchDispatchId
    if($LASTEXITCODE -ne 0){throw 'RESEARCH_DISPATCH_PATH_DENIED'}
    [IO.File]::WriteAllText((Join-Path $dispatchDir 'input.txt'),$Prompt,(New-Object Text.UTF8Encoding($false)))
    $proof=& $pythonExe (Join-Path $infraRoot 'runner/research-handoff.py') prepare --project $ResearchProject --dispatch $researchDispatchId --session $SessionId
    if($LASTEXITCODE -ne 0){throw ('RESEARCH_DISPATCH_DENIED: '+($proof -join ' '))}
}
$argList = [System.Collections.Generic.List[string]]::new()
$argList.Add($cliEntry)
$argList.Add("-m")
$argList.Add($modelName)
$argList.Add("--auth-type")
$argList.Add("openai")
$argList.Add("--openai-base-url")
$argList.Add($baseUrl)
$argList.Add("--openai-api-key")
$argList.Add("local-not-required")
$argList.Add("--approval-mode")
$argList.Add($ApprovalMode)
$argList.Add("-o")
$argList.Add($OutputFormat)

if (-not [string]::IsNullOrEmpty($MaxWallTime)) {
    $argList.Add("--max-wall-time")
    $argList.Add($MaxWallTime)
}
if ($MaxSessionTurns -gt 0) {
    $argList.Add("--max-session-turns")
    $argList.Add($MaxSessionTurns.ToString())
}
if ($MaxToolCalls -ge 0) {
    $argList.Add("--max-tool-calls")
    $argList.Add($MaxToolCalls.ToString())
}
if (-not [string]::IsNullOrEmpty($SessionId)) {
    $argList.Add("--session-id")
    $argList.Add($SessionId)
}
if ($ContinueSession) {
    $argList.Add("-c")
}
if (-not [string]::IsNullOrEmpty($ResumeSession)) {
    $argList.Add("-r")
    $argList.Add($ResumeSession)
}

if ($ExtraArgs -and $ExtraArgs.Count -gt 0) {
    foreach ($extra in $ExtraArgs) {
        $argList.Add($extra)
    }
}

if (-not [string]::IsNullOrEmpty($Prompt)) {
    $argList.Add($Prompt)
}

# 4. Formatear argumentos para ProcessStartInfo
function Format-CliArg([string]$arg) {
    if ($arg -match '[\s"]') {
        return '"' + ($arg -replace '(\\*)(")', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }
    return $arg
}

$argString = ($argList | ForEach-Object { Format-CliArg $_ }) -join " "

$targetWorkDir = if (-not [string]::IsNullOrEmpty($WorkingDir) -and (Test-Path -LiteralPath $WorkingDir)) {
    (Resolve-Path $WorkingDir).Path
} else {
    $infraRoot
}

$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $nodeExe
$psi.Arguments = $argString
$psi.WorkingDirectory = $targetWorkDir
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.RedirectStandardInput = $true
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true
$psi.StandardOutputEncoding=[Text.Encoding]::UTF8
$psi.StandardErrorEncoding=[Text.Encoding]::UTF8

$psi.EnvironmentVariables["OPENAI_BASE_URL"] = $baseUrl
$psi.EnvironmentVariables["OPENAI_API_KEY"] = "local-not-required"
$psi.EnvironmentVariables["OPENAI_MODEL"] = $modelName
$psi.EnvironmentVariables["QWEN_TELEMETRY"] = "false"

$lockToken = $null
if (-not $SkipLock) {
    . (Join-Path $infraRoot "scripts\inference-lock.ps1")
    $lockToken = Acquire-InferenceLock -Owner "qwen_code" -Purpose "coding-worker" -TimeoutSeconds $TimeoutSeconds -InfraPath $infraRoot
    if (-not $lockToken.Acquired) {
        return [PSCustomObject]@{
            Success       = $false
            ExitCode      = -2
            TimedOut      = $false
            LockStatus    = $lockToken.Status
            Duration      = 0
            Stdout        = ""
            Stderr        = "Error de adquisicion de Inference Lock: $($lockToken.Error)"
            Json          = $null
            BaseUrl       = $baseUrl
            Model         = $modelName
            ApprovalMode  = $ApprovalMode
            WorkingDir    = $targetWorkDir
        }
    }
}

$startTime = Get-Date
$timedOut = $false
$exitCode = -1

$rawOut = ""
$rawErr = ""

try {
    $proc = [System.Diagnostics.Process]::Start($psi)
    $proc.StandardInput.Close()
    if($researchDispatchId){
        $proof=& $pythonExe (Join-Path $infraRoot 'runner/research-handoff.py') started --project $ResearchProject --dispatch $researchDispatchId --session $SessionId --pid $proc.Id --birth $proc.StartTime.ToUniversalTime().Ticks
        if($LASTEXITCODE -ne 0){$proc.Kill();$null=$proc.WaitForExit(3000);throw ('RESEARCH_DISPATCH_CHANGED: '+($proof -join ' '))}
    }

    $stdoutTask = $proc.StandardOutput.ReadToEndAsync()
    $stderrTask = $proc.StandardError.ReadToEndAsync()

    $waitMs = $TimeoutSeconds * 1000
    $exited = $proc.WaitForExit($waitMs)

    if (-not $exited) {
        $timedOut = $true
        try {
            $proc.Kill()
            Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $proc.Id } | ForEach-Object {
                Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            }
        } catch { }
    } else {
        $null = [System.Threading.Tasks.Task]::WaitAll(@($stdoutTask, $stderrTask), 3000)
    }

    $exitCode = if ($timedOut) { -1 } else { $proc.ExitCode }

    if ($stdoutTask.IsCompleted) { $rawOut = $stdoutTask.Result }
    if ($stderrTask.IsCompleted) { $rawErr = $stderrTask.Result }
} catch {
    $err = $_.Exception.Message
} finally {
    $duration = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    if ($lockToken) {
        $null = Release-InferenceLock -LockToken $lockToken
    }
}

$parsedJson = $null
if ($OutputFormat -eq "json" -and -not [string]::IsNullOrWhiteSpace($rawOut)) {
    try {
        $parsedJson = $rawOut | ConvertFrom-Json
    } catch {
        # Si contiene texto previo/posterior a un bloque JSON, intentar extraer
        if ($rawOut -match '(?s)(\{.*\})') {
            try { $parsedJson = $matches[1] | ConvertFrom-Json } catch { }
        }
    }
}

$resultObj = [PSCustomObject]@{
    Success       = (-not $timedOut -and ($exitCode -eq 0))
    ExitCode      = $exitCode
    TimedOut      = $timedOut
    Duration      = $duration
    Stdout        = $rawOut
    Stderr        = $rawErr
    Json          = $parsedJson
    BaseUrl       = $baseUrl
    Model         = $modelName
    ApprovalMode  = $ApprovalMode
    WorkingDir    = $targetWorkDir
    ResearchDispatchId = $researchDispatchId
    WorkerSessionId = $SessionId
}

return $resultObj
