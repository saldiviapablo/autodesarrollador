# ==============================================================================
# scripts/test-real-chatgpt.ps1 — Prueba de Consulta REAL a ChatGPT vía CDP
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT Real)
# ==============================================================================
[CmdletBinding()]
param(
    [switch]$KeepBrowserOpen
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

Write-Host "=============================================================================="
Write-Host "Iniciando Test de Consulta REAL a ChatGPT (Fase 14)..."
Write-Host "=============================================================================="

# 1. Asegurar que Chrome HERMES-CHATGPT esté activo
& "$infraRoot\scripts\start-hermes-chatgpt.ps1"

# 2. Verificar sesión activa
Write-Host "[INFO] Verificando sesión en ChatGPT..."
$sess = & "$infraRoot\scripts\consultar-chatgpt.ps1" -Action "check-session"
if ($sess.Status -ne "SUCCESS" -or -not $sess.ResultObj.session_ready) {
    throw "Sesión de ChatGPT no lista ($($sess.Status), ready=$($sess.ResultObj.session_ready))"
}
Write-Host "[OK] Sesión verificada y lista en ChatGPT."

# 3. Ejecutar consulta real requerida
$promptReq = @"
Estoy probando un puente local de consulta. Respondé exactamente con estas dos líneas:
CHATGPT_BRIDGE_REAL_OK
7 + 8 = 15
"@

Write-Host "[INFO] Enviando prompt real a ChatGPT:"
Write-Host $promptReq
Write-Host "------------------------------------------------------------------------------"

$consultRes = & "$infraRoot\scripts\consultar-chatgpt.ps1" `
    -Question $promptReq `
    -RawPrompt `
    -TimeoutSeconds 60

Write-Host "[INFO] Resultado devuelto por el puente:"
Write-Host "Status:           $($consultRes.Status)"
Write-Host "ConsultationId:   $($consultRes.ConsultationId)"
Write-Host "Response received: $($consultRes.ResultObj.response_received)"
Write-Host "Message sent:     $($consultRes.ResultObj.message_sent)"
Write-Host "Source:           $($consultRes.ResultObj.source)"
Write-Host "Response text:"
Write-Host $consultRes.Response
Write-Host "------------------------------------------------------------------------------"

if ($consultRes.Status -ne "SUCCESS") {
    throw "Fallo en consulta real: $($consultRes.Error)"
}

$respText = $consultRes.Response
$hasBridgeOk = $respText -match "CHATGPT_BRIDGE_REAL_OK"
$hasMathOk = $respText -match "7\s*\+\s*8\s*=\s*15|15"

Write-Host "[CHECK] Contiene CHATGPT_BRIDGE_REAL_OK: $hasBridgeOk"
Write-Host "[CHECK] Contiene 7 + 8 = 15:            $hasMathOk"

if (-not $hasBridgeOk -or -not $hasMathOk) {
    throw "La respuesta de ChatGPT no contiene los tokens requeridos (BridgeOK=$hasBridgeOk, MathOK=$hasMathOk)"
}

Write-Host "[PASS] Consulta real completada exitosamente con tokens esperados."

return [PSCustomObject]@{
    Status           = "PASS"
    ConsultationId   = $consultRes.ConsultationId
    Response         = $respText
    MessageSent      = $consultRes.ResultObj.message_sent
    ResponseReceived = $consultRes.ResultObj.response_received
    Source           = $consultRes.ResultObj.source
}
