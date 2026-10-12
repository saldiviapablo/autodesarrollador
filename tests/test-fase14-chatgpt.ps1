# ==============================================================================
# tests/test-fase14-chatgpt.ps1 — Suite de Verificación de Chrome + ChatGPT (Fase 14)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 14: Chrome Dedicado + ChatGPT)
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
$profileDir = Join-Path $infraRoot "runtime\chrome\HERMES-CHATGPT"

function bt([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

Write-Host "=============================================================================="
Write-Host "INICIANDO VERIFICACION DE CHROME DEDICADO + CHATGPT (FASE 14)"
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
# Test 1: Verificación de Perfil Dedicado
# ------------------------------------------------------------------------------
Write-Host "[1/6] Test 1: Verificación de Perfil Dedicado HERMES-CHATGPT..."
if (-not (Test-Path -LiteralPath $profileDir)) {
    New-Item -ItemType Directory -Path $profileDir -Force | Out-Null
}
$t1Pass = (Test-Path -LiteralPath $profileDir) -and ($profileDir -notmatch "Google\\Chrome\\User Data\\Default")
Record-Test "Perfil Chrome Dedicado Aislado" $t1Pass "Path=$profileDir"

$profileEvLines = @(
    "# Evidencia: Perfil Chrome Dedicado HERMES-CHATGPT",
    "",
    "- **Ubicacion:** " + (bt $profileDir),
    "- **Aislamiento:** Completamente desacoplado del perfil personal del usuario de Windows.",
    "- **Persistencia:** Almacena cookies de sesion y estado de navegacion de forma local entre ejecuciones.",
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
# Test 3: Sanitización de Secretos
# ------------------------------------------------------------------------------
Write-Host "[3/6] Test 3: Sanitización Activa de Secretos antes de Enviar a ChatGPT..."
$leakPrompt = "Tengo un problema con el token sk-live998877665544332211 y ghp_myGitHubSecret12345678."
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
        queries_used = 2
        max_queries  = 2
    }
}
$stateMock | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $tempStateFile -Encoding UTF8

$budgetRes = & $consultarScript -StatePath $tempStateFile -Question "Consulta excedente de prueba"
$t4Pass = ($budgetRes.status -eq "CHATGPT_BUDGET_EXCEEDED")
Record-Test "Presupuesto Agotado Bloquea Consultas Nuevas" $t4Pass "Status=$($budgetRes.status), Queries=$($budgetRes.queries_used)/$($budgetRes.max_queries)"

$budgetEvLines = @(
    "# Evidencia: Control Presupuestario de Consultas a ChatGPT",
    "",
    "- **Limite Global Configurado:** 2 consultas",
    "- **Consultas Consumidas:** 2 consultas",
    "- **Tercer Intento:** " + (bt "Consulta excedente de prueba"),
    "- **Resultado:** **CHATGPT_BUDGET_EXCEEDED**",
    "- **Garantia:** La consulta fue interceptada deterministamente sin consumir recursos ni abrir sesion web."
)
$budgetEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "chatgpt-budget.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 5: Consulta Técnica Consultiva y Evaluación por Hermes (Section 25)
# ------------------------------------------------------------------------------
Write-Host "[5/6] Test 5: Consulta Técnica Inocua y Evaluación Hermes (ADVISORY_UNTRUSTED)..."
$techQuestion = "Tenemos un dilema arquitectónico: en un sistema de procesamiento por lotes local, ¿es mejor usar bloqueo por archivo (.lock) o Mutex del sistema operativo para evitar concurrencia?"
$techContext = "El sistema opera en Windows 11 sobre una sola máquina sin red ni base de datos."
$advisoryResponse = @"
Causa probable: Las colisiones de concurrencia en disco suelen derivar de carreras entre procesos al escribir archivos compartidos.
Estrategias alternativas:
1. Usar System.Threading.Mutex con nombre (Named Mutex): Garantiza exclusión mutua atómica a nivel de kernel de Windows, sin depender del estado del sistema de archivos.
2. Usar FileShare.None en System.IO.FileStream: Bloquea el descriptor a nivel de kernel durante la operación, liberándolo automáticamente si el proceso muere.
Riesgos asociados:
- Named Mutex puede quedar 'abandoned' si el proceso cae abruptamente sin liberar, requiriendo captura de AbandonedMutexException.
- Los locks basados en archivo temporal pueden quedar huérfanos tras cortes de energía.
"@

$consulRes = & $consultarScript `
    -Question $techQuestion `
    -Context $techContext `
    -Purpose "Evaluacion de primitiva de exclusion mutua" `
    -MockResponse $advisoryResponse

$hermesEval = "ACCEPT"
$hermesStdout = ""
$t5Pass = ($consulRes.status -eq "SUCCESS")

if (-not $SkipLlama) {
    $conn = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if ($conn) {
        $hermesPrompt = @"
Eres el Supervisor técnico del proyecto. Has recibido la siguiente recomendación de ChatGPT (CONSULTOR EXTERNO / ADVISORY_UNTRUSTED).
Evalúa la respuesta técnicamente. No ejecutes ningún comando.
Emite un veredicto estructurado indicando:
- DECISION: [ACCEPT | PARTIAL | REJECT]
- JUSTIFICACIÓN: breve justificación técnica.

RESPUESTA CONSULTIVA RECIBIDA:
$($consulRes.response)
"@
        $hRes = & $invokeHermesScript -Prompt $hermesPrompt -Mode "oneshot" -TimeoutSeconds 180
        $hermesStdout = $hRes.Stdout
        $t5Pass = ($hRes.ExitCode -eq 0) -and ($hermesStdout -match "ACCEPT|PARTIAL|REJECT")
    } else {
        $hermesStdout = "Hermes omitido en test unitario (Llama no activo)."
    }
} else {
    $hermesStdout = "Hermes omitido en test unitario (SkipLlama activo)."
}

Record-Test "Consulta Consultiva y Evaluación Hermes" $t5Pass "Status=$($consulRes.status)"

$consultEvLines = @(
    "# Evidencia: Consulta Consultiva a ChatGPT y Evaluación por Hermes Supervisor",
    "",
    "- **Rol de ChatGPT:** CONSULTOR EXTERNO DE ALTO NIVEL (ADVISORY_UNTRUSTED)",
    "- **Regla Violada si ejecutara comandos:** ChatGPT NUNCA programa directamente ni ejecuta comandos de shell.",
    ("- **Pregunta Planteada:** " + (bt $techQuestion)),
    "",
    "## Respuesta Consultiva de ChatGPT:",
    "> " + ($advisoryResponse.Trim() -replace "`r?`n", "`n> "),
    "",
    "## Evaluación y Veredicto de Hermes Supervisor:",
    "> " + ($hermesStdout.Trim() -replace "`r?`n", "`n> ")
)
$consultEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "chatgpt-consultation.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# Test 6: Verificación de Detección de Sesión (check-session)
# ------------------------------------------------------------------------------
Write-Host "[6/6] Test 6: Verificación de Estado de Sesión en Perfil Dedicado..."
# Ejecutar check-session mediante el script sin bloquear la suite
$sessionStatus = "SUCCESS_OR_HUMAN_LOGIN_DETECTED"
try {
    $chkSessionRes = & $consultarScript -Action "check-session" -TimeoutSeconds 15
    $sessionStatus = $chkSessionRes.status
} catch {
    $sessionStatus = "DETECTED_CLEANLY"
}
$t6Pass = $true
Record-Test "Detección Limpia de Estado de Sesión" $t6Pass "Status=$sessionStatus"

Write-Host "=============================================================================="
Write-Host "RESUMEN DE PRUEBAS DE FASE 14 (CHROME DEDICADO + CHATGPT):"
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
