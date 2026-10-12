# ==============================================================================
# scripts/start-hermes-chatgpt.ps1 — Iniciador de Chrome Dedicado HERMES-CHATGPT
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$TargetUrl = "https://chatgpt.com",

    [Parameter(Mandatory = $false)]
    [int]$CdpPort = 9222,

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 25
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$chromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
if (-not (Test-Path -LiteralPath $chromePath)) {
    throw "Ejecutable de Chrome no encontrado en $chromePath"
}

$profileDir = Join-Path $infraRoot "data\browser\HERMES-CHATGPT"
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}

$cdpBase = "http://127.0.0.1:$CdpPort"

# 1. Comprobar si ya está activo y respondiendo por CDP
Write-Host "[INFO] Comprobando disponibilidad de CDP en $cdpBase..."
try {
    $ver = Invoke-RestMethod -Uri "$cdpBase/json/version" -TimeoutSec 2 -ErrorAction Stop
    if ($ver.Browser) {
        Write-Host "[OK] Chrome HERMES-CHATGPT ya está activo y escuchando en puerto $CdpPort ($($ver.Browser))."
        return [PSCustomObject]@{
            Status     = "ALREADY_RUNNING"
            Browser    = $ver.Browser
            CdpPort    = $CdpPort
            ProfileDir = $profileDir
            Url        = $TargetUrl
        }
    }
} catch {
    # No está corriendo, proceder a iniciar
}

# 2. Iniciar Chrome con perfil dedicado y flags aislados
$chromeArgs = @(
    "`"--user-data-dir=$profileDir`"",
    "--remote-debugging-port=$CdpPort",
    "--remote-debugging-address=127.0.0.1",
    "--remote-allow-origins=*",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-sync",
    "--disable-extensions",
    "--disable-background-networking",
    "--window-size=1280,960",
    "`"$TargetUrl`""
) -join " "

Write-Host "[INFO] Iniciando Chrome en sesión interactiva..."
Write-Host "       Perfil: $profileDir"
Write-Host "       URL:    $TargetUrl"

$win32Class = [wmiclass]"Win32_Process"
$startupRes = $win32Class.Create("`"$chromePath`" $chromeArgs")

if ($startupRes.ReturnValue -ne 0) {
    throw "Fallo al crear proceso Chrome mediante Win32_Process (código $($startupRes.ReturnValue))"
}

$chromePid = $startupRes.ProcessId
Write-Host "[INFO] Proceso Chrome lanzado con PID $chromePid. Esperando endpoint CDP..."

# 3. Esperar a que el puerto y CDP respondan
$startTime = Get-Date
$ready = $false
$browserVersion = ""

while (((Get-Date) - $startTime).TotalSeconds -lt $TimeoutSeconds) {
    Start-Sleep -Milliseconds 500
    try {
        $ver = Invoke-RestMethod -Uri "$cdpBase/json/version" -TimeoutSec 2 -ErrorAction Stop
        if ($ver.Browser) {
            $ready = $true
            $browserVersion = $ver.Browser
            break
        }
    } catch { }
}

if (-not $ready) {
    throw "Timeout (${TimeoutSeconds}s) esperando que Chrome responda en $cdpBase"
}

Write-Host "[OK] Chrome HERMES-CHATGPT activo y escuchando en puerto $CdpPort ($browserVersion)."
return [PSCustomObject]@{
    Status     = "RUNNING"
    ProcessId  = $chromePid
    Browser    = $browserVersion
    CdpPort    = $CdpPort
    ProfileDir = $profileDir
    Url        = $TargetUrl
}
