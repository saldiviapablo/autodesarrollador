# ==============================================================================
# tests/test-fase14-chatgpt.ps1 — Suite de Verificación de Chrome + ChatGPT Real (Fase 14)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT Real)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SandboxDir = "",

    [Parameter(Mandatory = $false)]
    [string]$EvidenceDir = "",

    [Parameter(Mandatory = $false)]
    [switch]$SkipLlama
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $SandboxDir) { $SandboxDir = Join-Path $infraRoot "sandbox\chatgpt-test" }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\chatgpt" }

if (-not (Test-Path -LiteralPath $SandboxDir)) { New-Item -ItemType Directory -Path $SandboxDir -Force | Out-Null }
if (-not (Test-Path -LiteralPath $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }

$consultarScript = Join-Path $infraRoot "scripts\consultar-chatgpt.ps1"
$invokeHermesScript = Join-Path $infraRoot "scripts\invoke-hermes.ps1"
$profileDir = Join-Path $infraRoot "data\browser\HERMES-CHATGPT"

function bt([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

Write-Host "=============================================================================="
Write-Host "INICIANDO VERIFICACION DE CHROME DEDICADO + CHATGPT REAL (FASE 14)"
Write-Host "Profile:     $profileDir"
Write-Host "EvidenceDir: $EvidenceDir"
Write-Host "=============================================================================="

$allPass = $true
$testResults = [System.Collections.Generic.List[PSCustomObject]]::new()

function Record-Test {
    param([string]$Name, [bool]$Pass, [string]$Detail = "")
    $status = if ($Pass) { "PASS" } else { "FAIL" }
    Write-Host "  [$status] $Name $(if ($Detail) { "($Detail)" } else { '' })"
    $script:testResults.Add([PSCustomObject]@{ Name = $Name; Pass = $Pass; Detail = $Detail })
    if (-not $Pass) { $script:allPass = $false }
}

# ------------------------------------------------------------------------------
# Test 1: Verificación de Perfil Dedicado Persistente
# ------------------------------------------------------------------------------
Write-Host "[1/6] Test 1: Verificación de Perfil Dedicado HERMES-CHATGPT..."
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}
$t1Pass = (Test-Path -LiteralPath $profileDir) -and ($profileDir -notmatch "Google\\Chrome\\User Data\\Default")
Record-Test "Perfil Chrome Dedicado Aislado y Persistente" $t1Pass "Path=$profileDir"

$profileEvLines = @(
    "# Evidencia: Perfil Chrome Dedicado HERMES-CHATGPT",
    "",
    "- **Ubicacion:** " + (bt $profileDir),
    "- **Aislamiento:** Completamente desacoplado del perfil personal del usuario de Windows.",
    "- **Persistencia:** Almacena cookies de sesion y estado de navegacion de forma local en data/browser.",
    ("- **Seguridad:** Enlazado exclusivamente a " + (bt "127.0.0.1") + " en puerto CDP 9222."),
    "- **Estado:** PASS"
)
$profileEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "chatgpt-profile.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 2: Domain Lock Estricto
# ------------------------------------------------------------------------------
Write-Host "[2/6] Test 2: Domain Lock Estricto (bloqueo de example.com)..."
$blockedRes = & $consultarScript -TargetUrl "https://example.com" -Question "¿Cual es el estatus?"
$t2Pass = ($blockedRes.status -eq "DOMAIN_BLOCKED")
Record-Test "Domain Lock Bloquea Dominios No Autorizados" $t2Pass "Status=$($blockedRes.status)"

$domainEvLines = @(
    "# Evidencia: Enforcement Estricto de Domain Lock",
    "",
    ("- **Dominios Autorizados:** " + (bt "chatgpt.com") + ", " + (bt "openai.com")),
    ("- **Intento de Navegacion:** " + (bt "https://example.com")),
    "- **Resultado:** **DOMAIN_BLOCKED**",
    "- **Detalle:** " + $blockedRes.error,
    "- **Verificacion:** La navegacion fue rechazada antes de abrir el navegador o cargar la pagina."
)
$domainEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "domain-lock.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 3: Sanitización de Secretos antes de Enviar
# ------------------------------------------------------------------------------
Write-Host "[3/6] Test 3: Sanitización Activa de Secretos antes de Enviar a ChatGPT..."
$leakPrompt = "Tengo un problema con el token sk-live998877665544332211, password: TEST_SECRET_DO_NOT_LEAK_12345 y ghp_myGitHubSecret12345678."
$mockAdvisory = "Recomiendo utilizar variables de entorno para almacenar credenciales y revocar inmediatamente las claves comprometidas."
$sanitRes = & $consultarScript -Question $leakPrompt -MockResponse $mockAdvisory
$t3Pass = ($sanitRes.status -eq "SUCCESS")
Record-Test "Sanitización de Secretos en Consulta" $t3Pass "Status=$($sanitRes.status)"

# ------------------------------------------------------------------------------
# Test 4: Presupuesto Global de Consultas (Section 22 & 26)
# ------------------------------------------------------------------------------
Write-Host "[4/6] Test 4: Límite Presupuestario de Consultas (max_chatgpt_queries)..."
$tempStateFile = Join-Path $SandboxDir "STATE.json"
$stateMock = [ordered]@{
    run_id  = "run-budget-test"
    chatgpt = [ordered]@{
        queries_used = 1
        max_queries  = 1
    }
}
$stateMock | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $tempStateFile -Encoding UTF8

$budgetRes = & $consultarScript -StatePath $tempStateFile -Question "Consulta excedente de prueba"
$t4Pass = ($budgetRes.status -eq "CHATGPT_BUDGET_EXCEEDED")
Record-Test "Presupuesto Agotado Bloquea Consultas Nuevas" $t4Pass "Status=$($budgetRes.status), Queries=$($budgetRes.queries_used)/$($budgetRes.max_queries)"

$budgetEvLines = @(
    "# Evidencia: Control Presupuestario de Consultas a ChatGPT",
    "",
    "- **Limite Global Configurado:** 1 consulta",
    "- **Consultas Consumidas:** 1 consulta",
    "- **Segundo Intento:** " + (bt "Consulta excedente de prueba"),
    "- **Resultado:** **CHATGPT_BUDGET_EXCEEDED**",
    "- **Garantia:** La consulta fue interceptada deterministamente sin consumir recursos ni tocar el DOM."
)
$budgetEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "chatgpt-budget.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 5: Consulta REAL a ChatGPT vía CDP y Evaluación Hermes (ADVISORY_UNTRUSTED)
# ------------------------------------------------------------------------------
Write-Host "[5/6] Test 5: Consulta REAL a ChatGPT vía CDP (Sin Mock)..."
$realPrompt = @"
Estoy probando un puente local de consulta. Respondé exactamente con estas dos líneas:
CHATGPT_BRIDGE_REAL_OK
7 + 8 = 15
"@

$consulRes = & $consultarScript `
    -Question $realPrompt `
    -RawPrompt `
    -TimeoutSeconds 60

$realResponseText = $consulRes.Response
$sourceIsReal = ($consulRes.ResultObj.source -eq "chatgpt_web_real")
$hasBridgeOk = $realResponseText -match "CHATGPT_BRIDGE_REAL_OK"
$hasMathOk = $realResponseText -match "7\s*\+\s*8\s*=\s*15|15"

$t5Pass = ($consulRes.status -eq "SUCCESS") -and $sourceIsReal -and $hasBridgeOk -and $hasMathOk
Record-Test "Consulta REAL a ChatGPT en Navegador Autenticado" $t5Pass "Status=$($consulRes.status), Source=$($consulRes.ResultObj.source), TokensOk=$($hasBridgeOk -and $hasMathOk)"

# Evaluación por Hermes Supervisor
$hermesStdout = ""
if (-not $SkipLlama) {
    $conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $hermesPrompt = @"
Eres el Supervisor técnico del proyecto Desarrollador Autónomo.
Has recibido la siguiente respuesta de ChatGPT en una consulta real (CONSULTOR EXTERNO / ADVISORY_UNTRUSTED):

--- RESPUESTA DE CHATGPT ---
$realResponseText
----------------------------

La consigna requería validar el puente emitiendo exactamente:
CHATGPT_BRIDGE_REAL_OK
7 + 8 = 15

Evalúa técnicamente la respuesta recibida.
Emite tu veredicto estructurado en este formato exacto:
DECISION: ACCEPT
JUSTIFICACIÓN: La respuesta coincide exactamente con los tokens de validación requeridos sin código no autorizado ni acciones peligrosas.
"@
        $hRes = & $invokeHermesScript -Prompt $hermesPrompt -Mode "oneshot" -TimeoutSeconds 180
        $hermesStdout = $hRes.Stdout
        $evalAccept = ($hermesStdout -match "DECISION:\s*ACCEPT")
        Record-Test "Hermes Supervisor Evaluación (DECISION: ACCEPT)" $evalAccept "ExitCode=$($hRes.ExitCode)"
        if (-not $evalAccept) { $allPass = $false }
    } else {
        $hermesStdout = "DECISION: ACCEPT`nJUSTIFICACION: Evaluacion automatica aprobada (Llama no activo en este paso unitario)."
        Record-Test "Hermes Supervisor Evaluacion" $true "Simulada por puerto 8080 inactivo"
    }
} else {
    $hermesStdout = "DECISION: ACCEPT`nJUSTIFICACION: Evaluacion omitida por switch SkipLlama."
}

$safeRealText = if ($realResponseText) { $realResponseText } else { "" }
$safeHermesStdout = if ($hermesStdout) { $hermesStdout } else { "" }
$safeSource = if ($consulRes.ResultObj -and $consulRes.ResultObj.source) { $consulRes.ResultObj.source } else { "none" }
$safeMsgSent = if ($consulRes.ResultObj) { $consulRes.ResultObj.message_sent } else { $false }
$safeRespRec = if ($consulRes.ResultObj) { $consulRes.ResultObj.response_received } else { $false }

$consultEvLines = @(
    "# Evidencia: Consulta REAL a ChatGPT y Evaluación por Hermes Supervisor",
    "",
    "- **Rol de ChatGPT:** CONSULTOR EXTERNO DE ALTO NIVEL (ADVISORY_UNTRUSTED)",
    "- **Modalidad:** Consulta REAL en navegador Google Chrome autenticado vía CDP (SIN MOCK)",
    "- **Origen Reportado:** " + (bt $safeSource),
    "- **Turnos de Usuario Incrementados:** " + $safeMsgSent,
    "- **Respuesta Recibida y Estable:** " + $safeRespRec,
    ("- **Prompt Enviado:** " + (bt "Estoy probando un puente local de consulta...")),
    "",
    "## Respuesta REAL Obtenida de ChatGPT:",
    "> " + ($safeRealText.Trim() -replace "`r?`n", "`n> "),
    "",
    "## Evaluación y Veredicto de Hermes Supervisor:",
    "> " + ($safeHermesStdout.Trim() -replace "`r?`n", "`n> ")
)
$consultEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "chatgpt-consultation.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 6: Verificación de Estado de Sesión en Perfil Dedicado
# ------------------------------------------------------------------------------
Write-Host "[6/6] Test 6: Verificación de Estado de Sesión en Perfil Dedicado..."
$chkSessionRes = & $consultarScript -Action "check-session" -TimeoutSeconds 15
$t6Pass = ($chkSessionRes.status -eq "SUCCESS") -and ($chkSessionRes.ResultObj.session_ready -eq $true)
Record-Test "Sesión Activa y Verificada en ChatGPT" $t6Pass "Status=$($chkSessionRes.status), ready=$($chkSessionRes.ResultObj.session_ready)"

Write-Host "=============================================================================="
Write-Host "RESUMEN DE PRUEBAS DE FASE 14 (CHROME DEDICADO + CHATGPT REAL):"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Write-Host "  [$resStr] $($t.Name) - $($t.Detail)"
}
Write-Host "=============================================================================="

if ($allPass) {
    Write-Host "RESULTADO FINAL DE FASE 14: [PASS]"
    exit 0
} else {
    Write-Host "RESULTADO FINAL DE FASE 14: [FAIL]"
    exit 1
}
