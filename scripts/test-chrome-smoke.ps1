# ==============================================================================
# scripts/test-chrome-smoke.ps1 — Prueba Aislada de Arranque (Chrome Smoke Test)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT)
# ==============================================================================
# Verifica de forma visible, aislada y determinista el perfil HERMES-CHATGPT:
#   - chrome.exe real visible (no headless)
#   - Perfil dedicado: runtime\chrome\HERMES-CHATGPT
#   - Una sola ventana / pestaña
#   - Carga inicial: https://chatgpt.com/
#   - Remote debugging: 127.0.0.1:9222
#   - Timeout determinista: 25 segundos
#   - Detección de login humano: BLOCKED_REQUIRES_HUMAN_LOGIN (deja ventana abierta)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 25,

    [Parameter(Mandatory = $false)]
    [string]$TargetUrl = "https://chatgpt.com/"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$chromeExe = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$profileDir = Join-Path $infraRoot "runtime\chrome\HERMES-CHATGPT"
$cdpPort = 9222
$cdpBase = "http://127.0.0.1:$cdpPort"

Write-Host "=============================================================================="
Write-Host "INICIANDO CHROME SMOKE TEST (FASE 14 - DIAGNOSTICO AISLADO)"
Write-Host "Chrome Exe:    $chromeExe"
Write-Host "Perfil:        $profileDir"
Write-Host "URL Objetivo:  $TargetUrl"
Write-Host "Timeout:       $TimeoutSeconds segundos"
Write-Host "=============================================================================="

# 1. Verificar existencia de chrome.exe
if (-not (Test-Path -LiteralPath $chromeExe)) {
    Write-Host "[FAIL] chrome.exe no existe en: $chromeExe" -ForegroundColor Red
    return [PSCustomObject]@{
        Status    = "FAIL"
        Reason    = "CHROME_NOT_FOUND"
        Detail    = "El ejecutable de Google Chrome no fue hallado en $chromeExe."
        ChromePid = $null
    }
}

$chromeVer = (Get-Item -LiteralPath $chromeExe).VersionInfo.ProductVersion
Write-Host "[INFO] Version detectada de Google Chrome: $chromeVer"

# 2. Asegurar existencia de directorio de perfil dedicado
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
    Write-Host "[INFO] Directorio de perfil creado: $profileDir"
} else {
    Write-Host "[INFO] Directorio de perfil existente: $profileDir"
}

# 3. Comprobar si ya hay una instancia con este perfil y CDP activo
$cdpReady = $false
try {
    $verResp = Invoke-RestMethod -Uri "$cdpBase/json/version" -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($verResp -and $verResp.Browser) {
        $cdpReady = $true
        Write-Host "[INFO] Instancia existente de Chrome CDP ya responde en $cdpBase ($($verResp.Browser))"
    }
} catch { }

$chromeProcess = $null

# 4. Si CDP no responde, iniciar Chrome visible con el perfil dedicado
if (-not $cdpReady) {
    Write-Host "[INFO] Iniciando Chrome en modo visible con perfil dedicado (vía Win32_Process)..."
    $cmdLine = "`"$chromeExe`" --user-data-dir=`"$profileDir`" --remote-debugging-port=$cdpPort --remote-debugging-address=127.0.0.1 --remote-allow-origins=* --no-first-run --no-default-browser-check --window-size=1280,960 `"$TargetUrl`""

    $wmiRes = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = $cmdLine }
    $chromePid = $wmiRes.ProcessId

    Write-Host "[INFO] Proceso de Chrome iniciado con PID=$chromePid (ReturnCode=$($wmiRes.ReturnValue))"
}

# 5. Esperar readiness de CDP dentro del timeout determinista
$sw = [System.Diagnostics.Stopwatch]::StartNew()
$versionInfo = $null
while ($sw.Elapsed.TotalSeconds -lt $TimeoutSeconds) {
    try {
        $versionInfo = Invoke-RestMethod -Uri "$cdpBase/json/version" -TimeoutSec 2 -ErrorAction SilentlyContinue
        if ($versionInfo -and $versionInfo.Browser) {
            $cdpReady = $true
            break
        }
    } catch { }
    Start-Sleep -Milliseconds 600
}
$sw.Stop()

if (-not $cdpReady) {
    Write-Host "[FAIL] Timeout ($TimeoutSeconds s) esperando respuesta de CDP en $cdpBase." -ForegroundColor Red
    return [PSCustomObject]@{
        Status    = "FAIL"
        Reason    = "CDP_TIMEOUT"
        Detail    = "Chrome no respondió en el endpoint CDP http://127.0.0.1:$cdpPort tras $TimeoutSeconds segundos."
        ChromePid = if ($chromeProcess) { $chromeProcess.Id } else { $null }
    }
}

Write-Host "[OK] Endpoint CDP conectado exitosamente en $([Math]::Round($sw.Elapsed.TotalSeconds, 1))s: $($versionInfo.Browser)"

# 6. Obtener lista de páginas abiertas y enforzar 1 sola pestaña
Start-Sleep -Seconds 2 # Breve espera para que la pestaña inicial cargue
$tabs = @()
try {
    $tabs = Invoke-RestMethod -Uri "$cdpBase/json" -TimeoutSec 3 -ErrorAction SilentlyContinue
} catch { }

$pageTabs = @($tabs | Where-Object { $_.type -eq "page" })
Write-Host "[INFO] Pestanias abiertas detectadas: $($pageTabs.Count)"

if ($pageTabs.Count -eq 0) {
    Write-Host "[FAIL] No se encontraron paginas tipo 'page' en Chrome." -ForegroundColor Red
    return [PSCustomObject]@{
        Status    = "FAIL"
        Reason    = "NO_TABS_FOUND"
        Detail    = "CDP conectado pero no hay páginas activas."
        ChromePid = if ($chromeProcess) { $chromeProcess.Id } else { $null }
    }
}

# Enforzar una sola pestaña: cerrar las excedentes
if ($pageTabs.Count -gt 1) {
    Write-Host "[INFO] Cerrando pestañas excedentes para garantizar máximo 1 pestaña..."
    for ($i = 1; $i -lt $pageTabs.Count; $i++) {
        $extraId = $pageTabs[$i].id
        try {
            $null = Invoke-RestMethod -Uri "$cdpBase/json/close/$extraId" -TimeoutSec 2 -ErrorAction SilentlyContinue
            Write-Host "  - Pestaña extra $extraId cerrada."
        } catch { }
    }
}

$activeTab = $pageTabs[0]
$activeUrl = $activeTab.url
$activeTitle = $activeTab.title
Write-Host "[INFO] Pestaña activa: URL='$activeUrl' | Titulo='$activeTitle'"

# 7. Validar Domain Lock
$allowedDomains = @("chatgpt.com", "openai.com")
$isDomainAllowed = $false
try {
    $u = [System.Uri]$activeUrl
    $hostLower = $u.Host.ToLowerInvariant()
    foreach ($ad in $allowedDomains) {
        if ($hostLower -eq $ad -or $hostLower.EndsWith(".$ad")) {
            $isDomainAllowed = $true
            break
        }
    }
} catch { }

if (-not $isDomainAllowed -and $activeUrl -ne "about:blank") {
    Write-Host "[FAIL] Violación de Domain Lock: URL '$activeUrl' no pertenece a chatgpt.com" -ForegroundColor Red
    return [PSCustomObject]@{
        Status    = "FAIL"
        Reason    = "DOMAIN_BLOCKED"
        Detail    = "La URL activa '$activeUrl' no pertenece a chatgpt.com ni openai.com."
        ChromePid = if ($chromeProcess) { $chromeProcess.Id } else { $null }
        Url       = $activeUrl
    }
}

# 8. Evaluar estado de sesión y presencia de login vía CDP WebSocket
$wsUrl = $activeTab.webSocketDebuggerUrl
$evalState = [PSCustomObject]@{
    HasPromptBox    = $false
    HasLoginButton  = $false
    Url             = $activeUrl
    Title           = $activeTitle
}

if ($wsUrl) {
    try {
        $wsClient = [System.Net.WebSockets.ClientWebSocket]::new()
        $cts = [System.Threading.CancellationTokenSource]::new(5000)
        $wsUri = [System.Uri]$wsUrl
        $wsClient.ConnectAsync($wsUri, $cts.Token).Wait()

        if ($wsClient.State -eq [System.Net.WebSockets.WebSocketState]::Open) {
            # Enviar Runtime.evaluate
            $evalScript = @"
(() => {
    const url = window.location.href;
    const bodyText = document.body ? document.body.innerText : '';
    const hasPromptBox = !!document.querySelector('#prompt-textarea') || !!document.querySelector('div[contenteditable="true"]');
    const hasLoginButton = !!document.querySelector('button[data-testid="login-button"]') || url.includes('/auth/login') || bodyText.includes('Log in') || bodyText.includes('Iniciar sesión');
    return { url, hasPromptBox, hasLoginButton, title: document.title };
})()
"@
            $reqPayload = @{
                id     = 1001
                method = "Runtime.evaluate"
                params = @{
                    expression    = $evalScript
                    returnByValue = $true
                }
            } | ConvertTo-Json -Compress

            $sendBytes = [System.Text.Encoding]::UTF8.GetBytes($reqPayload)
            $sendSegment = [System.ArraySegment[byte]]::new($sendBytes)
            $wsClient.SendAsync($sendSegment, [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [System.Threading.CancellationToken]::None).Wait()

            # Leer respuesta
            $buffer = [byte[]]::new(65536)
            $recvSegment = [System.ArraySegment[byte]]::new($buffer)
            $recvResult = $wsClient.ReceiveAsync($recvSegment, [System.Threading.CancellationToken]::None).Result

            if ($recvResult.Count -gt 0) {
                $respJson = [System.Text.Encoding]::UTF8.GetString($buffer, 0, $recvResult.Count)
                $respObj = $respJson | ConvertFrom-Json
                if ($respObj.result -and $respObj.result.result -and $respObj.result.result.value) {
                    $v = $respObj.result.result.value
                    $evalState.HasPromptBox   = [bool]$v.hasPromptBox
                    $evalState.HasLoginButton = [bool]$v.hasLoginButton
                    $evalState.Url            = [string]$v.url
                    $evalState.Title          = [string]$v.title
                }
            }

            # Cerrar WebSocket limpiamente
            $wsClient.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Done", [System.Threading.CancellationToken]::None).Wait(2000)
            $wsClient.Dispose()
        }
    } catch {
        Write-Host "[WARN] No se pudo evaluar DOM via WebSocket ($($_.Exception.Message)), usando metadatos de pestania."
    }
}

# 9. Determinar Estado Final (PASS vs BLOCKED_REQUIRES_HUMAN_LOGIN)
$finalStatus = "UNKNOWN"
$detailMsg = ""

if ($evalState.HasPromptBox) {
    $finalStatus = "PASS"
    $detailMsg = "Sesión activa detectada con caja de prompt disponible en ChatGPT."
    Write-Host "[PASS] Sesión activa confirmada en ChatGPT ($($evalState.Url))." -ForegroundColor Green
} elseif ($evalState.HasLoginButton -or $evalState.Url -match '/auth/login' -or $activeTitle -match 'login|log in') {
    $finalStatus = "BLOCKED_REQUIRES_HUMAN_LOGIN"
    $detailMsg = "ChatGPT requiere autenticación manual. La ventana de Chrome se mantiene abierta y visible."
    Write-Host "[BLOCKED_REQUIRES_HUMAN_LOGIN] $detailMsg" -ForegroundColor Yellow
} else {
    # Si aún está cargando la página principal
    if ($evalState.Url -match 'chatgpt\.com') {
        $finalStatus = "BLOCKED_REQUIRES_HUMAN_LOGIN"
        $detailMsg = "Página chatgpt.com abierta. Si requiere inicio de sesión, el usuario debe autenticarse."
        Write-Host "[BLOCKED_REQUIRES_HUMAN_LOGIN] $detailMsg" -ForegroundColor Yellow
    } else {
        $finalStatus = "FAIL"
        $detailMsg = "Estado de página desconocido: $($evalState.Url)"
        Write-Host "[FAIL] $detailMsg" -ForegroundColor Red
    }
}

$retObj = [PSCustomObject]@{
    Status         = $finalStatus
    Detail         = $detailMsg
    Url            = $evalState.Url
    Title          = $evalState.Title
    HasPromptBox   = $evalState.HasPromptBox
    HasLoginButton = $evalState.HasLoginButton
    ChromePid      = if ($chromeProcess) { $chromeProcess.Id } else { "EXISTING" }
    ProfileDir     = $profileDir
    CdpPort        = $cdpPort
}

Write-Host "=============================================================================="
Write-Host "RESULTADO SMOKE TEST: [$finalStatus]"
Write-Host "=============================================================================="

return $retObj
