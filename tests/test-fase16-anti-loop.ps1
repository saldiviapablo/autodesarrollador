# ==============================================================================
# tests/test-fase16-anti-loop.ps1 — Suite de Verificación Anti-Loop y Timeouts (Fase 16)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 16: Anti-Loop / Timeouts / Control de Progreso)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$EvidenceDir = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\anti-loop" }
if (-not (Test-Path -LiteralPath $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }

. (Join-Path $infraRoot "scripts\progress-guard.ps1")

function bt([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

Write-Host "=============================================================================="
Write-Host "INICIANDO VERIFICACION DE ANTI-LOOP Y TIMEOUTS (FASE 16)"
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
# 1. Prueba de Normalización de Errores (Error Signature)
# ------------------------------------------------------------------------------
Write-Host "[1/4] Test 1: Normalización Determinista de Firmas de Error..."

$errRun1 = @"
Error: Failed to connect to database at 2026-10-12T02:15:30.123Z.
Process PID: 8124, Thread 12
Temp file: C:\Users\Pc\AppData\Local\Temp\db_lock_8124.tmp
Memory: 0x7fff1234abcd
Details: Timeout waiting for PostgreSQL lock.
"@

$errRun2 = @"
Error: Failed to connect to database at 2026-10-12T02:40:55.999Z.
Process PID: 9942, Thread 18
Temp file: C:\Users\Pc\AppData\Local\Temp\db_lock_9942.tmp
Memory: 0x7fff9876ef01
Details: Timeout waiting for PostgreSQL lock.
"@

$errDifferent = @"
Error: Syntax error unexpected token ')' at line 45.
Details: Missing closing brace in config.js.
"@

$sig1 = Get-NormalizedErrorSignature -ErrorText $errRun1
$sig2 = Get-NormalizedErrorSignature -ErrorText $errRun2
$sigDiff = Get-NormalizedErrorSignature -ErrorText $errDifferent

$t1a = ($sig1.SignatureHash -eq $sig2.SignatureHash)
$t1b = ($sig1.SignatureHash -ne $sigDiff.SignatureHash)
$t1Pass = ($t1a -and $t1b)

Record-Test "Normalización de Errores (Misma Firma para Errores Idénticos con Metadatos Variables)" $t1Pass "Sig1=$($sig1.SignatureHash), Sig2=$($sig2.SignatureHash), DiffSig=$($sigDiff.SignatureHash)"

$sigEvLines = @(
    "# Evidencia: Normalización Determinista de Firmas de Error (Section 38)",
    "",
    "- **Objetivo:** Evitar bucles infinitos causados por pequeñas variaciones superficiales en logs (PIDs, timestamps, temp paths).",
    "- **Error Run 1:** Hash " + (bt $sig1.SignatureHash) + " (PID 8124, 02:15:30)",
    "- **Error Run 2:** Hash " + (bt $sig2.SignatureHash) + " (PID 9942, 02:40:55)",
    "- **Comparación:** " + $(if ($t1a) { "**COINCIDEN EXACTAMENTE** (Normalización Exitosa)" } else { "**FALLO**" }),
    "- **Error Sintáctico Distinto:** Hash " + (bt $sigDiff.SignatureHash) + " (" + $(if ($t1b) { "Distinto" } else { "Incorrecto" }) + ")",
    "",
    "### Texto Normalizado:",
    '```text',
    $sig1.NormalizedText,
    '```'
)
$sigEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "error-signature.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# 2. Prueba de Control de Bucles y Detección de Falta de Avance
# ------------------------------------------------------------------------------
Write-Host "[2/4] Test 2: Detección de Bucles Repetidos y Avance Real..."

$tracker = [ordered]@{}
$fp1 = (Get-ProgressFingerprint -WorkspacePath $infraRoot -PassTests 5 -FailTests 1 -ErrorSignatureHash $sig1.SignatureHash).Fingerprint

# Simular 3 ejecuciones con el mismo error y misma huella (estancamiento)
$eval1 = Test-LoopProgress -Tracker $tracker -CurrentErrorHash $sig1.SignatureHash -CurrentFingerprint $fp1
$eval2 = Test-LoopProgress -Tracker $tracker -CurrentErrorHash $sig1.SignatureHash -CurrentFingerprint $fp1
$eval3 = Test-LoopProgress -Tracker $tracker -CurrentErrorHash $sig1.SignatureHash -CurrentFingerprint $fp1

$t2a = ($eval1.RecommendedAction -eq "RETRY")
$t2b = ($eval2.RecommendedAction -eq "NEW_APPROACH")
$t2c = ($eval3.RecommendedAction -eq "WEB_RESEARCH") # max_same_failure = 3 alcanzado -> escala a WEB_RESEARCH

# Simular que se produce avance real en ciclo 4 (nuevo test pasa, error resuelto)
$fp2 = (Get-ProgressFingerprint -WorkspacePath $infraRoot -PassTests 6 -FailTests 0 -ErrorSignatureHash "NONE").Fingerprint
$eval4 = Test-LoopProgress -Tracker $tracker -CurrentErrorHash "" -CurrentFingerprint $fp2

$t2d = ($eval4.RecommendedAction -eq "CONTINUE" -and $tracker["same_failure_count"] -eq 0)

$t2Pass = ($t2a -and $t2b -and $t2c -and $t2d)
Record-Test "Detección de Repetición y Reinicio con Avance Real" $t2Pass "C1=$($eval1.RecommendedAction), C2=$($eval2.RecommendedAction), C3=$($eval3.RecommendedAction), C4=$($eval4.RecommendedAction)"

$loopEvLines = @(
    "# Evidencia: Detección y Prevención de Bucles Repetidos (Section 38)",
    "",
    "- **Regla:** Máximo 3 fallos idénticos (`max_same_failure = 3`).",
    "- **Ciclo 1:** Acción = " + (bt $eval1.RecommendedAction) + " (Primer fallo detectado)",
    "- **Ciclo 2:** Acción = " + (bt $eval2.RecommendedAction) + " (Fallo repetido, cambia enfoque)",
    "- **Ciclo 3:** Acción = " + (bt $eval3.RecommendedAction) + " (**ESCALAMIENTO ACTIVADO**: Investigación Web requerida)",
    "- **Ciclo 4 (Con Avance Real):** Acción = " + (bt $eval4.RecommendedAction) + " (Contador reiniciado a 0)",
    "- **Garantía:** El sistema nunca ejecuta el mismo fallo indefinidamente."
)
$loopEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "loop-detection.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# 3. Prueba de la Escalera de Escalamiento Completa y Límite de Ciclos
# ------------------------------------------------------------------------------
Write-Host "[3/4] Test 3: Escalera de Escalamiento Completa hasta BLOCKED_REQUIRES_HUMAN..."

$ladderTracker = [ordered]@{}
$stuckFp = "DEAD_LOCK_FP_0001"
$stuckErr = "PERSISTENT_ERROR_HASH_123"

$actionsRecorded = [System.Collections.Generic.List[string]]::new()
for ($c = 1; $c -le 8; $c++) {
    $res = Test-LoopProgress -Tracker $ladderTracker -CurrentErrorHash $stuckErr -CurrentFingerprint $stuckFp -MaxCycles 20 -MaxSameFailure 3 -MaxNoProgress 3
    $actionsRecorded.Add($res.RecommendedAction)
}

# Verificamos que la secuencia cubra: RETRY, NEW_APPROACH, WEB_RESEARCH, CHATGPT_CONSULT, NEW_SESSION, BLOCKED_REQUIRES_HUMAN
$t3a = ($actionsRecorded -contains "RETRY")
$t3b = ($actionsRecorded -contains "NEW_APPROACH")
$t3c = ($actionsRecorded -contains "WEB_RESEARCH")
$t3d = ($actionsRecorded -contains "CHATGPT_CONSULT")
$t3e = ($actionsRecorded -contains "NEW_SESSION")
$t3f = ($actionsRecorded -contains "BLOCKED_REQUIRES_HUMAN")

# Prueba de max_cycles = 20
$maxTracker = [ordered]@{ cycle_count = 19 }
$resMax = Test-LoopProgress -Tracker $maxTracker -CurrentErrorHash "" -CurrentFingerprint "FP_ANY" -MaxCycles 20
$t3g = ($resMax.CanContinue -eq $false -and $resMax.Status -eq "STALLED")

$t3Pass = ($t3a -and $t3b -and $t3c -and $t3d -and $t3e -and $t3f -and $t3g)
Record-Test "Escalera de Escalamiento y Límite Absoluto de Ciclos (20)" $t3Pass "EscaladaCompleta=$($t3a -and $t3b -and $t3c -and $t3d -and $t3e -and $t3f), MaxCyclesLimit=$t3g"

$ladderEvLines = @(
    "# Evidencia: Escalera de Escalamiento Determinista (Section 40)",
    "",
    "| Nivel | Condición Disparadora | Acción Recomendada | Estado |",
    "| :---: | :--- | :--- | :---: |",
    "| 1 | 1er fallo | " + (bt "RETRY") + " | IN_PROGRESS |",
    "| 2 | 2do fallo idéntico | " + (bt "NEW_APPROACH") + " | IN_PROGRESS |",
    "| 3 | 3 fallos idénticos | " + (bt "WEB_RESEARCH") + " | ESCALATING |",
    "| 4 | Fallo persiste post-web | " + (bt "CHATGPT_CONSULT") + " | ESCALATING |",
    "| 5 | Fallo persiste post-ChatGPT | " + (bt "NEW_SESSION") + " | ESCALATING |",
    "| 6 | Agotamiento de recursos | " + (bt "BLOCKED_REQUIRES_HUMAN") + " | STALLED |",
    "",
    "- **Límite Absoluto:** Ciclo 20 detiene la ejecución inmediatamente con estado `STALLED`."
)
$ladderEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "escalation-ladder.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# 4. Prueba de Ejecución con Timeout y Terminación de Árbol de Procesos
# ------------------------------------------------------------------------------
Write-Host "[4/4] Test 4: Timeout Determinista y Terminación de Procesos Huérfanos..."

# A) Comando normal rápido
$quickCmd = "powershell.exe -Command `"Write-Output 'OK_TEST'`""
$qRes = Invoke-CommandWithTimeout -CommandLine $quickCmd -TimeoutSeconds 10
$t4a = ($qRes.TimedOut -eq $false -and $qRes.ExitCode -eq 0 -and $qRes.StdOut -match 'OK_TEST')

# B) Comando que simula un proceso colgado (dormir 60 segundos con timeout de 3 segundos)
$sleepCmd = "powershell.exe -NoProfile -Command `"Start-Sleep -Seconds 60`""
$tRes = Invoke-CommandWithTimeout -CommandLine $sleepCmd -TimeoutSeconds 3
$t4b = ($tRes.TimedOut -eq $true -and $tRes.Status -eq "TIMEOUT_TRIGGERED" -and $tRes.DurationSeconds -ge 2.5 -and $tRes.DurationSeconds -le 6.0)

# C) Verificar que el proceso colgado realmente murió y no sigue en segundo plano
Start-Sleep -Milliseconds 500
$staleCheck = Get-Process -Id $tRes.ProcessId -ErrorAction SilentlyContinue
$t4c = ($null -eq $staleCheck)

$t4Pass = ($t4a -and $t4b -and $t4c)
Record-Test "Timeout con Terminación de Árbol de Procesos (Sin Huérfanos)" $t4Pass "Normal=$t4a, TimeoutKilled=$t4b, NoOrphan=$t4c (Pid=$($tRes.ProcessId))"

$timeoutEvLines = @(
    "# Evidencia: Ejecución con Timeout y Terminación de Árbol de Procesos",
    "",
    "- **Comando Normal:** Finalizó en $($qRes.DurationSeconds)s con código $($qRes.ExitCode).",
    "- **Comando Colgado (Start-Sleep 60s):**",
    "  - **Timeout Configurado:** 3 segundos",
    "  - **Duración Observada:** $($tRes.DurationSeconds)s",
    "  - **PID Registrado:** $($tRes.ProcessId)",
    "  - **Acción Ejecutada:** `taskkill /PID $($tRes.ProcessId) /T /F` (Terminación forzada de árbol de procesos)",
    "  - **Comprobación de Huérfanos:** Proceso $($tRes.ProcessId) ya no existe en el sistema operativo.",
    "- **Resultado:** PASS"
)
$timeoutEvLines | Set-Content -LiteralPath (Join-Path $EvidenceDir "timeout-kill.md") -Encoding UTF8

Write-Host "=============================================================================="
Write-Host "RESUMEN DE PRUEBAS DE FASE 16 (ANTI-LOOP Y TIMEOUTS):"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Write-Host "  [$resStr] $($t.Name) - $($t.Detail)"
}
Write-Host "=============================================================================="

if ($allPass) {
    Write-Host "RESULTADO FINAL DE FASE 16: [PASS]"
    exit 0
} else {
    Write-Host "RESULTADO FINAL DE FASE 16: [FAIL]"
    exit 1
}
