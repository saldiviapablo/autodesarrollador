# ==============================================================================
# scripts/close-hermes-chrome.ps1 — Cierre Controlado y Limpio de Chrome HERMES-CHATGPT
# ==============================================================================
param()

$cdpPort = 9222
$cdpBase = "http://127.0.0.1:$cdpPort"

Write-Host "Verificando si Chrome HERMES-CHATGPT está activo en $cdpBase..."
try {
    $ver = Invoke-RestMethod -Uri "$cdpBase/json/version" -TimeoutSec 3 -ErrorAction Stop
    Write-Host "Instancia detectada: $($ver.Browser)"
    
    # 1. Intentar cierre grácil mediante CDP Browser.close
    if ($ver.webSocketDebuggerUrl) {
        Write-Host "Enviando comando Browser.close vía CDP..."
        $ws = [System.Net.WebSockets.ClientWebSocket]::new()
        $cts = [System.Threading.CancellationTokenSource]::new(5000)
        $ws.ConnectAsync([System.Uri]$ver.webSocketDebuggerUrl, $cts.Token).Wait()
        
        $closeCmd = @{ id = 9999; method = "Browser.close" } | ConvertTo-Json -Compress
        $bytes = [System.Text.Encoding]::UTF8.GetBytes($closeCmd)
        $ws.SendAsync([System.ArraySegment[byte]]::new($bytes), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [System.Threading.CancellationToken]::None).Wait()
        
        Start-Sleep -Seconds 2
        $ws.Dispose()
    }
} catch {
    Write-Host "No se pudo conectar a CDP ($($_.Exception.Message))."
}

# 2. Si todavía queda algún proceso ligado a este perfil específico, terminarlo por PID registrado
$conn = Get-NetTCPConnection -LocalPort $cdpPort -State Listen -ErrorAction SilentlyContinue
if ($conn) {
    Write-Host "Proceso aún en puerto $cdpPort (PID $($conn.OwningProcess)). Terminando proceso específico..."
    Stop-Process -Id $conn.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 1
}

# 3. Comprobación final de puerto libre
$finalConn = Get-NetTCPConnection -LocalPort $cdpPort -State Listen -ErrorAction SilentlyContinue
if ($null -eq $finalConn) {
    Write-Host "[OK] Puerto CDP $cdpPort completamente libre. Perfil preservado intacto en disco."
} else {
    Write-Host "[WARN] Puerto CDP $cdpPort aún ocupado por PID $($finalConn.OwningProcess)."
}
