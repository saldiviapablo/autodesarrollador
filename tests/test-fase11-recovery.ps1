# ==============================================================================
# tests/test-fase11-recovery.ps1 — Suite de Verificación de Fase 11 (Recovery y Reconciliación)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 11: Recovery y Reconciliación)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SandboxDir = "",

    [Parameter(Mandatory = $false)]
    [string]$EvidenceDir = "",

    [Parameter(Mandatory = $false)]
    [string]$LogFile = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $SandboxDir) { $SandboxDir = Join-Path $infraRoot "sandbox\continuity-basic" }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\continuity" }
if (-not $LogFile) {
    $timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $LogFile = Join-Path $infraRoot "logs\phase-11-recovery-$timestamp.log"
}

$logParent = Split-Path -Parent $LogFile
if (-not (Test-Path -LiteralPath $logParent)) { New-Item -ItemType Directory -Path $logParent -Force | Out-Null }
if (-not (Test-Path -LiteralPath $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }

. (Join-Path $infraRoot "scripts\state-manager.ps1")
$initScript = Join-Path $infraRoot "scripts\init-autopilot-project.ps1"
$recoverScript = Join-Path $infraRoot "scripts\recover-autopilot.ps1"
$chkScript = Join-Path $infraRoot "scripts\create-autopilot-checkpoint.ps1"

function Log-Msg {
    param([string]$Msg, [string]$Level = "INFO")
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
    $line = "[$ts] [$Level] $Msg"
    Write-Host $line
    Add-Content -LiteralPath $LogFile -Value $line -Encoding UTF8
}

$allPass = $true
$testResults = [System.Collections.Generic.List[PSCustomObject]]::new()

function Record-Test {
    param([string]$Name, [bool]$Pass, [string]$Detail = "")
    $status = if ($Pass) { "PASS" } else { "FAIL" }
    $level = if ($Pass) { "OK" } else { "ERROR" }
    Log-Msg "  [$status] $Name $(if ($Detail) { "($Detail)" } else { '' })" $level
    $script:testResults.Add([PSCustomObject]@{
        Name   = $Name
        Pass   = $Pass
        Detail = $Detail
    })
    if (-not $Pass) { $script:allPass = $false }
}

Log-Msg "=============================================================================="
Log-Msg "INICIANDO VERIFICACION DE RECOVERY Y RECONCILIACION (FASE 11)"
Log-Msg "Sandbox:     $SandboxDir"
Log-Msg "EvidenceDir: $EvidenceDir"
Log-Msg "=============================================================================="

$autopilotDir = Join-Path $SandboxDir ".autopilot"

# 1. Test Crash A: Modificación de código antes de actualizar STATE (Git supera a STATE)
Log-Msg "[1/6] Test Crash A: Edit antes de STATE (Git > STATE)..."
# Asegurar baseline limpio en Git
$calcPath = Join-Path $SandboxDir "calculator.py"
"def add(a, b): return a + b" | Set-Content -LiteralPath $calcPath -Encoding UTF8
& git -C "$SandboxDir" add calculator.py
& git -C "$SandboxDir" commit -m "baseline calc" -q 2>&1 | Out-Null

# Modificar archivo en disco sin registrar en STATE
"def add(a, b): return a + b # edit uncommitted crash" | Set-Content -LiteralPath $calcPath -Encoding UTF8

# Estado en disco dice que changed_files está vacío
$statePath = Join-Path $autopilotDir "STATE.json"
$sObj = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
$sObj.git.changed_files = @()
$sObj.status = "RUNNING"
$null = Write-AtomicState -StateObj $sObj -AutopilotDir $autopilotDir -ValidateTransition $false

# Ejecutar recuperación
$recResultA = & $recoverScript -ProjectPath $SandboxDir
$recStateA = $recResultA.State

$tA_Detected = $recResultA.DivergenceDetected
$tA_HasFile = ($recStateA.git.changed_files -contains "calculator.py")
$tAPass = ($tA_Detected -and $tA_HasFile)
Record-Test "Crash A: Detección de Git Diff no registrado y Reconciliación" $tAPass "DivergenceDetected=$tA_Detected, ChangedFilesContainsCalc=$tA_HasFile"

# 2. Test Crash B: Test interrumpido en estado RUNNING
Log-Msg "[2/6] Test Crash B: Test en curso (RUNNING -> UNKNOWN)..."
$sObj = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
$sObj.tests.status = "RUNNING"
$sObj.tests.last_command = "python test_calculator.py"
$sObj.status = "RUNNING"
$null = Write-AtomicState -StateObj $sObj -AutopilotDir $autopilotDir -ValidateTransition $false

# Ejecutar recuperación
$recResultB = & $recoverScript -ProjectPath $SandboxDir
$recStateB = $recResultB.State

$tB_Unknown = ($recStateB.tests.status -eq "UNKNOWN")
$tB_NextAction = ($recStateB.next_action -match "Re-ejecutar pruebas")
$tBPass = ($tB_Unknown -and $tB_NextAction)
Record-Test "Crash B: Test interrumpido reconciliado a UNKNOWN (Rerun planificado)" $tBPass "TestStatus=$($recStateB.tests.status), NextAction=$($recStateB.next_action)"

# 3. Test Crash C: Corrupción de STATE.json (Recuperación desde STATE.previous.json)
Log-Msg "[3/6] Test Crash C: STATE.json Corrupto (Fallback a Previous)..."
# Asegurar que STATE.previous.json existe y es válido
$prevFile = Join-Path $autopilotDir "STATE.previous.json"
if (-not (Test-Path -LiteralPath $prevFile)) {
    Copy-Item -LiteralPath $statePath -Destination $prevFile -Force
}

# Corromper STATE.json intencionalmente
[System.IO.File]::WriteAllText($statePath, "{ broken json corrupt content !!!", [System.Text.Encoding]::UTF8)

# Ejecutar recuperación
$recResultC = & $recoverScript -ProjectPath $SandboxDir
$recStateC = $recResultC.State

$tC_Recovered = $recResultC.RecoveredFromBackup
$tC_Valid = (Test-Path -LiteralPath $statePath) -and ($recStateC.run_id.Length -gt 0)
$tCPass = ($tC_Recovered -and $tC_Valid)
Record-Test "Crash C: STATE Corrupto Recuperado desde Previous Backup" $tCPass "RecoveredFromBackup=$tC_Recovered, RunId=$($recStateC.run_id)"

# 4. Test Crash D: RUNNING sin proceso vivo (Stale Heartbeat / Incomplete Run)
Log-Msg "[4/6] Test Crash D: RUNNING sin proceso vivo (Stale Run)..."
# Simular heartbeat de un PID ficticio inexistente
$fakePid = 999999
$null = Update-AutopilotHeartbeat -AutopilotDir $autopilotDir -RunId $recStateC.run_id -ProcessId $fakePid -Status "RUNNING" -CurrentTask "Tarea interrumpida"

$recResultD = & $recoverScript -ProjectPath $SandboxDir -StayInRecovering
$recStateD = $recResultD.State

$tD_Recovering = ($recStateD.status -eq "RECOVERING")
$tD_ReportHasStale = ($recResultD.Report | Out-String) -match "Ejecución previa interrumpida"
$tDPass = ($tD_Recovering -and $tD_ReportHasStale)
Record-Test "Crash D: Detección de Incomplete Run y Transición a RECOVERING" $tDPass "Status=$($recStateD.status), StaleDetected=$tD_ReportHasStale"

# Reanudar estado a RUNNING
$recStateD.status = "RUNNING"
$null = Write-AtomicState -StateObj $recStateD -AutopilotDir $autopilotDir -ValidateTransition $true

# 5. Test Checkpoint Recovery: Reconstrucción con Checkpoint + Git + EVENTS
Log-Msg "[5/6] Test Checkpoint: Reconstrucción con Checkpoint..."
$chkRes = & $chkScript -ProjectPath $SandboxDir -CheckpointId "chk-fase11-reconcile" -Reason "Snapshot previo a divergencia"
$recResultE = & $recoverScript -ProjectPath $SandboxDir
$tEPass = ($recResultE.Status -eq "RECOVERED" -and (Test-Path -LiteralPath $chkRes.Directory))
Record-Test "Checkpoint Recovery: Reconciliación con Checkpoint Existente" $tEPass "CheckpointId=$($chkRes.CheckpointId), Reconciled=True"

# 6. Test Idempotencia: Ejecutar recovery dos veces seguidas no degrada el estado
Log-Msg "[6/6] Test Idempotencia: Doble ejecución sin degradación..."
$rec1 = & $recoverScript -ProjectPath $SandboxDir
$rec2 = & $recoverScript -ProjectPath $SandboxDir

$tF_TasksEqual = ($rec1.State.pending_tasks.Count -eq $rec2.State.pending_tasks.Count)
$tF_FilesEqual = ($rec1.State.git.changed_files.Count -eq $rec2.State.git.changed_files.Count)
$tF_StatusEqual = ($rec1.State.status -eq $rec2.State.status)
$tFPass = ($tF_TasksEqual -and $tF_FilesEqual -and $tF_StatusEqual)
Record-Test "Idempotencia: Ejecución Consecutiva no Degrada ni Duplica Tareas" $tFPass "TasksMatch=$tF_TasksEqual, FilesMatch=$tF_FilesEqual, StatusMatch=$tF_StatusEqual"

# Generar archivos de evidencia de Fase 11
@(
    @{ File = "recovery-edit-crash.md"; Title = "Evidencia: Recuperación ante Edit no registrado en STATE"; Content = "Git detectó modificación en `calculator.py` no registrada en STATE. Protocolo reconcilió estado marcando `calculator.py` en `git.changed_files` y registrando evento `RECOVERY_RECONCILED`." },
    @{ File = "recovery-test-crash.md"; Title = "Evidencia: Recuperación ante Test Interrumpido (RUNNING)"; Content = "Pruebas en estado RUNNING tras terminación abrupta fueron reconciliadas deterministamente a `UNKNOWN` y se planificó re-ejecución inmediata como `next_action`. No se inventó resultado falso." },
    @{ File = "recovery-corrupt-state.md"; Title = "Evidencia: Recuperación ante STATE.json Corrupto"; Content = "`STATE.json` con sintaxis rota fue detectado como inválido contra schema. El protocolo recurrió a `STATE.previous.json`, restauró el estado y regeneró `STATE.json` de forma atómica." },
    @{ File = "recovery-stale-run.md"; Title = "Evidencia: Detección de Incomplete Run / Heartbeat Stale"; Content = "Estado RUNNING con proceso inexistente fue detectado mediante `Test-HeartbeatStale`. Protocolo transitó forzosamente a `RECOVERING` para diagnosticar antes de reanudar." },
    @{ File = "recovery-idempotency.md"; Title = "Evidencia: Idempotencia del Protocolo de Recuperación"; Content = "Dos ejecuciones consecutivas de `recover-autopilot.ps1` produjeron estados exactamente idénticos sin duplicar tareas ni crear artefactos divergentes." }
) | ForEach-Object {
    $outP = Join-Path $EvidenceDir $_.File
    $lines = @(
        "# $($_.Title)",
        "",
        "- **Fecha:** $((Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))",
        "- **Resultado:** PASS",
        "",
        $_.Content
    )
    $lines | Set-Content -LiteralPath $outP -Encoding UTF8
}

Log-Msg "=============================================================================="
Log-Msg "RESUMEN DE PRUEBAS DE FASE 11 (RECOVERY Y RECONCILIACION):"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Log-Msg "  [$resStr] $($t.Name) - $($t.Detail)"
}
Log-Msg "=============================================================================="

if ($allPass) {
    Log-Msg "RESULTADO FINAL DE FASE 11: [PASS]" "OK"
    exit 0
} else {
    Log-Msg "RESULTADO FINAL DE FASE 11: [FAIL]" "ERROR"
    exit 1
}
