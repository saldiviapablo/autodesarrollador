# ==============================================================================
# scripts/web-research.ps1 — Wrapper de Investigación Web y Extracción
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 13: Web Research)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Query = "",

    [Parameter(Mandatory = $false)]
    [string]$Url = "",

    [Parameter(Mandatory = $false)]
    [string[]]$Domains = @(),

    [Parameter(Mandatory = $false)]
    [int]$MaxResults = 5,

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 25,

    [Parameter(Mandatory = $false)]
    [int]$ProcessTimeoutSeconds = 0,

    [Parameter(Mandatory = $false)]
    [switch]$FetchTop,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$pythonExe = "C:\Python314\python.exe"
$pyScript = Join-Path $infraRoot "tools\web-research.py"

if (-not (Test-Path -LiteralPath $pyScript)) {
    throw "No se encontró el script de investigación web en $pyScript"
}

$pyArgs = [System.Collections.Generic.List[string]]::new()
$pyArgs.Add($pyScript)

if (-not [string]::IsNullOrWhiteSpace($Url)) {
    $pyArgs.Add("--url")
    $pyArgs.Add($Url)
} elseif (-not [string]::IsNullOrWhiteSpace($Query)) {
    $pyArgs.Add("--query")
    $pyArgs.Add($Query)
} else {
    throw "Debe especificar -Query o -Url para la investigación web."
}

if ($Domains -and $Domains.Count -gt 0) {
    $pyArgs.Add("--domains")
    foreach ($d in $Domains) {
        $pyArgs.Add($d)
    }
}

$pyArgs.Add("--max-results")
$pyArgs.Add("$MaxResults")

$pyArgs.Add("--timeout")
$pyArgs.Add("$TimeoutSeconds")

if ($FetchTop) {
    $pyArgs.Add("--fetch-top")
}

$effectiveTimeout = $TimeoutSeconds + 5
if ($ProcessTimeoutSeconds -gt 0) {
    if ($ProcessTimeoutSeconds -gt 180 -or $ProcessTimeoutSeconds -lt $TimeoutSeconds) {
        throw "INVALID_RESEARCH_PROCESS_TIMEOUT"
    }
    $effectiveTimeout = $ProcessTimeoutSeconds
}

# Ejecutar proceso Python con captura
$pInfo = New-Object System.Diagnostics.ProcessStartInfo
$pInfo.FileName = $pythonExe
$pInfo.Arguments = ($pyArgs | ForEach-Object {
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

$procExited = $proc.WaitForExit($effectiveTimeout * 1000)
if (-not $procExited) {
    try { $proc.Kill() } catch {}
    throw "Timeout en web-research.py tras ${TimeoutSeconds}s"
}

$stdout = $stdoutTask.Result
$stderr = $stderrTask.Result

if ($proc.ExitCode -ne 0 -or [string]::IsNullOrWhiteSpace($stdout)) {
    throw "Error ejecutando web-research.py (ExitCode $($proc.ExitCode)): $stderr"
}

$resultObj = $stdout | ConvertFrom-Json

if (-not [string]::IsNullOrWhiteSpace($OutputPath)) {
    $outDir = Split-Path -Parent $OutputPath
    if ($outDir -and -not (Test-Path -LiteralPath $outDir)) {
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($OutputPath, $stdout, [System.Text.Encoding]::UTF8)
}

return [PSCustomObject]@{
    Success      = $true
    Query        = $resultObj.query
    TotalSources = $resultObj.total_sources
    Sources      = $resultObj.sources
    RawJson      = $stdout
    ResultObj    = $resultObj
}
