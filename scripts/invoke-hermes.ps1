# ==============================================================================
# scripts/invoke-hermes.ps1 — Wrapper de Invocación para Hermes Agent CLI
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 6 — Hermes Agent)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Position = 0, Mandatory = $false)]
    [string]$Prompt = "",

    [Parameter(Mandatory = $false)]
    [ValidateSet("oneshot", "chat", "chat-stream-json")]
    [string]$Mode = "oneshot",

    [Parameter(Mandatory = $false)]
    [string]$WorkingDir = "",

    [Parameter(Mandatory = $false)]
    [string]$SessionId = "",

    [Parameter(Mandatory = $false)]
    [switch]$ContinueSession,

    [Parameter(Mandatory = $false)]
    [int]$MaxTurns = 0,

    [Parameter(Mandatory = $false)]
    [string]$UsageFile = "",

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 300,

    [Parameter(Mandatory = $false)]
    [string]$Profile = "desarrollador-autonomo",

    [Parameter(Mandatory = $false)]
    [string]$NamedSession = "",

    [Parameter(Mandatory = $false)]
    [switch]$CreateIfMissing,

    [Parameter(Mandatory = $false)]
    [switch]$SkipLock,

    [Parameter(Mandatory = $false)]
    [string[]]$Skills = @(),

    [Parameter(Mandatory = $false)]
    [string]$SecurityYamlPath = "",

    [Parameter(Mandatory = $false)]
    [string]$HookScriptOverride = "",

    [Parameter(Mandatory = $false)]
    [string[]]$ExtraArgs = @()
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

# 2. Localizar Hermes CLI
$hermesExe = "C:\Users\Pc\AppData\Local\hermes\bin\hermes.exe"
if (-not (Test-Path -LiteralPath $hermesExe)) {
    $hermesCmd = Get-Command "hermes" -ErrorAction SilentlyContinue
    if ($hermesCmd) {
        $hermesExe = $hermesCmd.Source
    } else {
        throw "Hermes CLI ejecutable no encontrado en $hermesExe ni en PATH."
    }
}

# 3. Determinar directorio de trabajo
$targetWorkDir = if (-not [string]::IsNullOrEmpty($WorkingDir) -and (Test-Path -LiteralPath $WorkingDir)) {
    (Resolve-Path $WorkingDir).Path
} else {
    $infraRoot
}

# 4. Construir argumentos CLI
$argList = [System.Collections.Generic.List[string]]::new()
$argList.Add("-p")
$argList.Add($Profile)

if ($Mode -eq "oneshot") {
    if (-not [string]::IsNullOrEmpty($Prompt)) {
        $argList.Add("-z")
        $argList.Add($Prompt)
    }
    if (-not [string]::IsNullOrEmpty($UsageFile)) {
        $argList.Add("--usage-file")
        $argList.Add($UsageFile)
    }
    if (-not [string]::IsNullOrEmpty($SessionId)) {
        $argList.Add("--resume")
        $argList.Add($SessionId)
    }
    if ($ContinueSession) {
        $argList.Add("-c")
    }
    if (-not [string]::IsNullOrEmpty($WorkingDir)) {
        $argList.Add("--in")
        $argList.Add($targetWorkDir)
    }
} elseif ($Mode -eq "chat" -or $Mode -eq "chat-stream-json") {
    $argList.Add("chat")
    if (-not [string]::IsNullOrEmpty($Prompt)) {
        $argList.Add("-q")
        $argList.Add($Prompt)
    }
    $argList.Add("--oneshot")
    $argList.Add("-Q")
    if ($Mode -eq "chat-stream-json") {
        $argList.Add("--format")
        $argList.Add("stream-json")
    }
    $argList.Add("--yolo")
    if ($Skills -and $Skills.Count -gt 0) {
        foreach ($sk in $Skills) {
            if (-not [string]::IsNullOrWhiteSpace($sk)) {
                $argList.Add("-s")
                $argList.Add($sk.Trim())
            }
        }
    }
    if ($MaxTurns -gt 0) {
        $argList.Add("--max-turns")
        $argList.Add($MaxTurns.ToString())
    }
    if (-not [string]::IsNullOrEmpty($SessionId)) {
        $argList.Add("--resume")
        $argList.Add($SessionId)
    }
    if (-not [string]::IsNullOrEmpty($NamedSession)) {
        $argList.Add("-c")
        $argList.Add($NamedSession)
        if ($CreateIfMissing) {
            $argList.Add("--create-if-missing")
        }
    } elseif ($ContinueSession) {
        $argList.Add("-c")
    }
    if (-not [string]::IsNullOrEmpty($WorkingDir)) {
        $argList.Add("--in")
        $argList.Add($targetWorkDir)
    }
}

if ($ExtraArgs -and $ExtraArgs.Count -gt 0) {
    foreach ($extra in $ExtraArgs) {
        $argList.Add($extra)
    }
}

function Format-CliArg([string]$arg) {
    if ($arg -match '[\s"]') {
        return '"' + ($arg -replace '(\\*)(")', '$1$1\"' -replace '(\\+)$', '$1$1') + '"'
    }
    return $arg
}

$argString = ($argList | ForEach-Object { Format-CliArg $_ }) -join " "

# 5. Configurar ProcessStartInfo
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $hermesExe
$psi.Arguments = $argString
$psi.WorkingDirectory = $targetWorkDir
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.RedirectStandardInput = $true
$psi.StandardOutputEncoding = [System.Text.Encoding]::UTF8
$psi.StandardErrorEncoding = [System.Text.Encoding]::UTF8
$psi.UseShellExecute = $false
$psi.CreateNoWindow = $true

# Variables de entorno seguras locales (HERMES_ACCEPT_HOOKS explícitamente ausente)
$psi.EnvironmentVariables["OPENAI_BASE_URL"] = $baseUrl
$psi.EnvironmentVariables["OPENAI_API_KEY"] = "local-not-required"
$psi.EnvironmentVariables["OPENAI_MODEL"] = $modelName
$psi.EnvironmentVariables["PYTHONUTF8"] = "1"
$psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8"
if ($psi.EnvironmentVariables.ContainsKey("HERMES_ACCEPT_HOOKS")) {
    $psi.EnvironmentVariables.Remove("HERMES_ACCEPT_HOOKS")
}
$hermesAcceptHooksActive = $psi.EnvironmentVariables.ContainsKey("HERMES_ACCEPT_HOOKS")

# 5.1 Verificación determinista de integridad criptográfica (SHA-256) del hook antes de iniciar Hermes
$memoryGuardScript = Join-Path $infraRoot "scripts\hermes-memory-guard.ps1"
$secYamlEffective = if (-not [string]::IsNullOrWhiteSpace($SecurityYamlPath)) { $SecurityYamlPath } else { Join-Path $infraRoot "config\security.yaml" }
$guardArgs = @{
    Action           = "VerifyHookIntegrity"
    SecurityYamlPath = $secYamlEffective
}
if (-not [string]::IsNullOrWhiteSpace($HookScriptOverride)) {
    $guardArgs["HookScriptPath"] = $HookScriptOverride
}
$integrityRaw = & $memoryGuardScript @guardArgs
$integrityObj = ($integrityRaw -join "`n") | ConvertFrom-Json

if (-not $integrityObj.allowed -or $integrityObj.status -ne "PASS") {
    return [PSCustomObject]@{
        Success            = $false
        Status             = "HOOK_INTEGRITY_MISMATCH"
        Decision           = "DENY"
        HookIntegrity      = "HOOK_INTEGRITY_MISMATCH"
        ApprovedHookSha256 = $integrityObj.approved_sha256
        RuntimeHookSha256  = $integrityObj.runtime_sha256
        HookPath           = $integrityObj.hook_path
        HermesAcceptHooks  = $hermesAcceptHooksActive
        ExitCode           = -3
        TimedOut           = $false
        Duration           = 0
        Stdout             = ""
        Stderr             = "DENY [HOOK_INTEGRITY_MISMATCH]: SHA-256 mismatch for hook '$($integrityObj.hook_path)'. Approved=$($integrityObj.approved_sha256), Runtime=$($integrityObj.runtime_sha256)."
        SessionId          = ""
        BaseUrl            = $baseUrl
        Model              = $modelName
        Profile            = $Profile
        WorkingDir         = $targetWorkDir
    }
}

$lockToken = $null
if (-not $SkipLock) {
    . (Join-Path $infraRoot "scripts\inference-lock.ps1")
    $lockToken = Acquire-InferenceLock -Owner "hermes" -Purpose "supervisor-orchestration" -TimeoutSeconds $TimeoutSeconds -InfraPath $infraRoot
    if (-not $lockToken.Acquired) {
        return [PSCustomObject]@{
            Success            = $false
            Status             = "LOCK_FAILURE"
            Decision           = "DENY"
            HookIntegrity      = "PASS"
            ApprovedHookSha256 = $integrityObj.approved_sha256
            RuntimeHookSha256  = $integrityObj.runtime_sha256
            HookPath           = $integrityObj.hook_path
            HermesAcceptHooks  = $hermesAcceptHooksActive
            ExitCode           = -2
            TimedOut           = $false
            LockStatus         = $lockToken.Status
            Duration           = 0
            Stdout             = ""
            Stderr             = "Error de adquisicion de Inference Lock: $($lockToken.Error)"
            SessionId          = ""
            BaseUrl            = $baseUrl
            Model              = $modelName
            Profile            = $Profile
            WorkingDir         = $targetWorkDir
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
    $rawErr = $_.Exception.Message
} finally {
    $duration = [Math]::Round(((Get-Date) - $startTime).TotalSeconds, 2)
    if ($lockToken) {
        $null = Release-InferenceLock -LockToken $lockToken
    }
}

# 6. Intentar extraer session_id si está presente
$extractedSessionId = ""
if ($rawOut -match 'session[_-]id[:\s]+([a-zA-Z0-9_\-]+)') {
    $extractedSessionId = $matches[1]
}

$resultObj = [PSCustomObject]@{
    Success            = (-not $timedOut -and ($exitCode -eq 0))
    Status             = if (-not $timedOut -and ($exitCode -eq 0)) { "OK" } else { "ERROR" }
    Decision           = "ALLOW"
    HookIntegrity      = "PASS"
    ApprovedHookSha256 = $integrityObj.approved_sha256
    RuntimeHookSha256  = $integrityObj.runtime_sha256
    HookPath           = $integrityObj.hook_path
    HermesAcceptHooks  = $hermesAcceptHooksActive
    ExitCode           = $exitCode
    TimedOut           = $timedOut
    Duration           = $duration
    Stdout             = $rawOut
    Stderr             = $rawErr
    SessionId          = $extractedSessionId
    BaseUrl            = $baseUrl
    Model              = $modelName
    Profile            = $Profile
    WorkingDir         = $targetWorkDir
}

return $resultObj
