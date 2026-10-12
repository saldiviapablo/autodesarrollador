# ==============================================================================
# scripts/test-real-chatgpt.ps1 — Prueba de Consulta REAL a ChatGPT con UTF-8
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Hardening de Unicode / UTF-8)
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
Write-Host "Iniciando Test de Verificación UTF-8 y Consulta REAL a ChatGPT (Fase 14)..."
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

# 3. Test de UNICODE_ROUNDTRIP Canónico (DOM Composer sin enviar)
Write-Host "[INFO] Ejecutando Test 1: UNICODE_ROUNDTRIP canónico..."
$canonicalStr = @"
Prueba UTF-8:
áéíóú ÁÉÍÓÚ
ñ Ñ
¿Dónde está?
¡Funciona!
— € °
"@

$rtRes = & "$infraRoot\scripts\consultar-chatgpt.ps1" -Action "unicode-roundtrip" -Question $canonicalStr
Write-Host "Roundtrip Status:            $($rtRes.Status)"
Write-Host "Unicode Roundtrip:           $($rtRes.ResultObj.unicode_roundtrip)"
Write-Host "SourceText Equals DomText:   $($rtRes.SourceTextEqualsDomText)"

if ($rtRes.Status -ne "SUCCESS" -or -not $rtRes.SourceTextEqualsDomText) {
    throw "Fallo en UNICODE_ROUNDTRIP: DOM no coincide con el texto origen."
}
Write-Host "[PASS] UNICODE_ROUNDTRIP exitoso: DOM y Source coinciden carácter por carácter."

# 4. Test 2: Consulta REAL con prompt UTF-8 específico
Write-Host "------------------------------------------------------------------------------"
Write-Host "[INFO] Ejecutando Test 2: Consulta REAL con prompt UTF-8..."
$promptReq = @"
Estoy probando un puente local de consulta.
Respondé exactamente con estas dos líneas:
CHATGPT_BRIDGE_UTF8_OK
áéíóú ñ ¿sí?
"@

Write-Host "[INFO] Prompt origen a enviar:"
Write-Host $promptReq
Write-Host "------------------------------------------------------------------------------"

$consultRes = & "$infraRoot\scripts\consultar-chatgpt.ps1" `
    -Question $promptReq `
    -RawPrompt `
    -TimeoutSeconds 60

Write-Host "[INFO] Resultado devuelto por el puente:"
Write-Host "Status:                     $($consultRes.Status)"
Write-Host "ConsultationId:             $($consultRes.ConsultationId)"
Write-Host "SourceText Equals DomText:  $($consultRes.SourceTextEqualsDomText)"
Write-Host "Message sent:               $($consultRes.ResultObj.message_sent)"
Write-Host "Response received:          $($consultRes.ResultObj.response_received)"
Write-Host "Source:                     $($consultRes.ResultObj.source)"
Write-Host "DOM Composer Text:          $($consultRes.DomText)"
Write-Host "Response text:"
Write-Host $consultRes.Response
Write-Host "------------------------------------------------------------------------------"

if ($consultRes.Status -ne "SUCCESS") {
    throw "Fallo en consulta real: $($consultRes.Error)"
}

$unicodeSend = if ($consultRes.SourceTextEqualsDomText) { "PASS" } else { "FAIL" }
Write-Host "[CHECK] UNICODE_SEND: $unicodeSend"

$respText = $consultRes.Response
$hasBridgeOk = $respText -match "CHATGPT_BRIDGE_UTF8_OK"
$hasVowelsOk = $respText -match "áéíóú"
$hasEnyeOk   = $respText -match "ñ"
$hasQuestionOk = $respText -match "¿sí\?"

Write-Host "[CHECK] Contiene CHATGPT_BRIDGE_UTF8_OK: $hasBridgeOk"
Write-Host "[CHECK] Contiene áéíóú:                 $hasVowelsOk"
Write-Host "[CHECK] Contiene ñ:                     $hasEnyeOk"
Write-Host "[CHECK] Contiene ¿sí?:                  $hasQuestionOk"

$unicodeReceive = if ($hasBridgeOk -and $hasVowelsOk -and $hasEnyeOk -and $hasQuestionOk) { "PASS" } else { "FAIL" }
Write-Host "[CHECK] UNICODE_RECEIVE: $unicodeReceive"

if ($unicodeSend -ne "PASS" -or $unicodeReceive -ne "PASS") {
    throw "Fallo en verificación bidireccional UTF-8 (Send=$unicodeSend, Receive=$unicodeReceive)"
}

Write-Host "[PASS] Test bidireccional UTF-8 completado exitosamente."

return [PSCustomObject]@{
    Status                  = "PASS"
    ConsultationId          = $consultRes.ConsultationId
    UnicodeRoundtrip        = $rtRes.ResultObj.unicode_roundtrip
    SourceTextEqualsDomText = $consultRes.SourceTextEqualsDomText
    UnicodeSend             = $unicodeSend
    UnicodeReceive          = $unicodeReceive
    SourceText              = $consultRes.SourceText
    DomText                 = $consultRes.DomText
    Response                = $respText
    Source                  = $consultRes.ResultObj.source
}
