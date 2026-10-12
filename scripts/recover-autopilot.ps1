# ==============================================================================
# scripts/recover-autopilot.ps1 — Protocolo Determinista de Recuperación y Reconciliación
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 11: Recovery y Reconciliación)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $false)]
    [string]$CheckpointId = "",

    [Parameter(Mandatory = $false)]
    [switch]$StayInRecovering
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

. (Join-Path $infraRoot "scripts\state-manager.ps1")

# 1. Canonicalizar project_root
$canonicalProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$autopilotDir = Join-Path $canonicalProjectPath ".autopilot"
if (-not (Test-Path -LiteralPath $autopilotDir)) {
    throw "No se encontró el directorio .autopilot en $canonicalProjectPath. No se puede recuperar."
}

$reconcileReport = [System.Collections.Generic.List[string]]::new()
$recoveredFromBackup = $false
$stateFile = Join-Path $autopilotDir "STATE.json"
$previousFile = Join-Path $autopilotDir "STATE.previous.json"
$stateSchemaPath = Join-Path $infraRoot "schemas\autopilot-state.schema.json"

# 1.1 Si se solicitó un CheckpointId específico, verificar su integridad criptográfica
if (-not [string]::IsNullOrWhiteSpace($CheckpointId)) {
    $specificChkDir = Join-Path $autopilotDir "checkpoints\$CheckpointId"
    $specIntegrity = Test-CheckpointIntegrity -CheckpointDir $specificChkDir
    if (-not $specIntegrity.Valid) {
        throw "CHECKPOINT_INTEGRITY_FAILED: Checkpoint '$CheckpointId' no es válido ($($specIntegrity.Detail))."
    }
    $reconcileReport.Add("Checkpoint '$CheckpointId' verificado criptográficamente con éxito (CHECKPOINT_INTEGRITY_OK).")
}

# 2. Leer RUN-CONTRACT.yaml
$contractPath = Join-Path $autopilotDir "RUN-CONTRACT.yaml"
if (-not (Test-Path -LiteralPath $contractPath)) {
    throw "No se encontró RUN-CONTRACT.yaml en $autopilotDir"
}
$readYamlPy = @'
import sys, json, yaml
with open(sys.argv[1], encoding='utf-8-sig') as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
'@
$contractJson = & $pythonExe -c $readYamlPy "$contractPath"
$runContract = $contractJson | ConvertFrom-Json

# 3. Validar y recuperar STATE.json (o STATE.previous.json / checkpoints)
$stateObj = $null
$stateNeedsRegen = $false

if (Test-Path -LiteralPath $stateFile) {
    try {
        $valRes = Test-FileSchemaValidation "$stateFile" "$stateSchemaPath"
        if ($valRes -match "^VALID") {
            $rawStateText = Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8
            $stateObj = $rawStateText | ConvertFrom-Json
        } else {
            $stateNeedsRegen = $true
            $reconcileReport.Add("STATE.json corrupto o inválido contra schema ($valRes).")
        }
    } catch {
        $stateNeedsRegen = $true
        $reconcileReport.Add("Error leyendo STATE.json: $($_.Exception.Message)")
    }
} else {
    $stateNeedsRegen = $true
    $reconcileReport.Add("STATE.json no existía.")
}

if ($stateNeedsRegen) {
    # Intentar recuperación desde STATE.previous.json
    if (Test-Path -LiteralPath $previousFile) {
        try {
            $valPrev = Test-FileSchemaValidation "$previousFile" "$stateSchemaPath"
            if ($valPrev -match "^VALID") {
                $rawPrevText = Get-Content -LiteralPath $previousFile -Raw -Encoding UTF8
                $stateObj = $rawPrevText | ConvertFrom-Json
                $recoveredFromBackup = $true
                $reconcileReport.Add("Recuperado exitosamente desde STATE.previous.json.")
            }
        } catch { }
    }

    # Si previous no fue suficiente, buscar en el último checkpoint
    if ($null -eq $stateObj) {
        $checkpointsDir = Join-Path $autopilotDir "checkpoints"
        if (Test-Path -LiteralPath $checkpointsDir) {
            $chkDirs = Get-ChildItem -Path $checkpointsDir -Directory | Sort-Object CreationTime -Descending
            foreach ($cd in $chkDirs) {
                # Validar integridad criptográfica del checkpoint antes de confiar en él
                $chkIntegrity = Test-CheckpointIntegrity -CheckpointDir $cd.FullName
                if (-not $chkIntegrity.Valid) {
                    $reconcileReport.Add("Checkpoint $($cd.Name) descartado: CHECKPOINT_INTEGRITY_FAILED ($($chkIntegrity.Detail)).")
                    continue
                }

                $chkStatePath = Join-Path $cd.FullName "state.json"
                if (Test-Path -LiteralPath $chkStatePath) {
                    try {
                        $valChk = Test-FileSchemaValidation "$chkStatePath" "$stateSchemaPath"
                        if ($valChk -match "^VALID") {
                            $rawChkText = Get-Content -LiteralPath $chkStatePath -Raw -Encoding UTF8
                            $stateObj = $rawChkText | ConvertFrom-Json
                            $recoveredFromBackup = $true
                            $reconcileReport.Add("Recuperado exitosamente desde checkpoint $($cd.Name) íntegro.")
                            break
                        }
                    } catch { }
                }
            }
        }
    }

    if ($null -eq $stateObj) {
        throw "Corrupción fatal: STATE.json no es válido y no se pudo recuperar de previous ni de checkpoints."
    }
}

# 4. Leer QWEN.md si existe
$qwenMdPath = Join-Path $canonicalProjectPath "QWEN.md"
$hasQwenMd = (Test-Path -LiteralPath $qwenMdPath)

# 5. Inspeccionar Git (JERARQUÍA DE VERDAD: Git supera a STATE)
$gitBranch = "unknown"
$gitHead = "unknown"
$gitDirty = $false
$realChangedFiles = [System.Collections.Generic.List[string]]::new()

try {
    $bOut = & git -C "$canonicalProjectPath" rev-parse --abbrev-ref HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $bOut) { $gitBranch = $bOut.Trim() }
    $hOut = & git -C "$canonicalProjectPath" rev-parse --short HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $hOut) { $gitHead = $hOut.Trim() }
    
    $statusOut = & git -C "$canonicalProjectPath" status --porcelain 2>&1
    if ($statusOut) {
        foreach ($line in ($statusOut -split "`r?`n")) {
            if ($line -match '^\s*[MADRCU?]+\s+(.+)$') {
                $f = $matches[1].Trim()
                if ($f -notmatch '__pycache__' -and $f -notmatch '\.pyc$') {
                    $realChangedFiles.Add($f)
                }
            }
        }
        if ($realChangedFiles.Count -gt 0) { $gitDirty = $true }
    }
} catch {
    $reconcileReport.Add("Advertencia inspeccionando Git: $_")
}

# Reconciliación Git vs STATE:
$stateChanged = @($stateObj.git.changed_files)
$divergenceDetected = $false
foreach ($rf in $realChangedFiles) {
    if ($stateChanged -notcontains $rf) {
        $divergenceDetected = $true
        $reconcileReport.Add("Git detectó archivo modificado no registrado en STATE: $rf")
    }
}

$stateObj.git.branch = $gitBranch
$stateObj.git.head = $gitHead
$stateObj.git.dirty = $gitDirty
$stateObj.git.changed_files = @($realChangedFiles)

# 6. Inspeccionar tests y reconciliar con cambios en código
if ($stateObj.tests.status -eq "RUNNING") {
    $reconcileReport.Add("Tests figuraban en estado RUNNING pero el proceso terminó abruptamente. Reconciliado a UNKNOWN.")
    $stateObj.tests.status = "UNKNOWN"
}

# Si el código tiene cambios sin comitear o nuevos y el último test fue PASS antes del crash:
if ($divergenceDetected -and $stateObj.tests.status -eq "PASS") {
    $reconcileReport.Add("Existen cambios en código posteriores al último test PASS. Marcando tests como UNKNOWN.")
    $stateObj.tests.status = "UNKNOWN"
}

# 7. Inspeccionar Heartbeat y detectar si la ejecución previa quedó huérfana/stale
$hbCheck = Test-HeartbeatStale -AutopilotDir $autopilotDir -ThresholdSeconds 120
if ($stateObj.status -eq "RUNNING" -and $hbCheck.IsStale) {
    $reconcileReport.Add("Ejecución previa interrumpida detectada: status era RUNNING pero $($hbCheck.Reason)")
}

# 8. Transición determinista a RECOVERING
$stateObj.status = "RECOVERING"
$stateObj.current_phase = "RECOVERY_AND_RECONCILIATION"
$stateObj.current_task = "Reconciliación de estado tras evento o interrupción"

# Determinar próxima acción
if ($stateObj.tests.status -eq "UNKNOWN") {
    $stateObj.next_action = "Re-ejecutar pruebas unitarias para certificar estado técnico tras cambios"
} elseif ($stateObj.pending_tasks.Count -gt 0) {
    $stateObj.next_action = "Continuar ejecución de tarea pendiente: $($stateObj.pending_tasks[0])"
} else {
    $stateObj.next_action = "Verificar criterios de aceptación para cierre"
}

# Escribir estado atómico en RECOVERING
$recoveringState = Write-AtomicState -StateObj $stateObj -AutopilotDir $autopilotDir -ValidateTransition $false

# 9. Registrar evento RECOVERY_RECONCILED en EVENTS.jsonl
$null = Add-AutopilotEvent `
    -AutopilotDir $autopilotDir `
    -RunId $stateObj.run_id `
    -Actor "recovery-protocol" `
    -Type "RECOVERY_RECONCILED" `
    -Payload @{
        recovered_from_backup = $recoveredFromBackup
        reconciled_git_files  = @($realChangedFiles)
        divergence_detected   = $divergenceDetected
        tests_status          = $stateObj.tests.status
        next_action           = $stateObj.next_action
        details               = @($reconcileReport)
    }

# 10. Transición final de vuelta a RUNNING (si no se solicitó StayInRecovering)
$finalState = $recoveringState
if (-not $StayInRecovering) {
    $stateObj.status = "RUNNING"
    $stateObj.current_phase = "ACTIVE_EXECUTION"
    $stateObj.current_task = if ($stateObj.pending_tasks.Count -gt 0) { $stateObj.pending_tasks[0] } else { "Verificación técnica" }
    $finalState = Write-AtomicState -StateObj $stateObj -AutopilotDir $autopilotDir -ValidateTransition $true
}

return [PSCustomObject]@{
    Status              = "RECOVERED"
    RecoveredFromBackup = $recoveredFromBackup
    DivergenceDetected  = $divergenceDetected
    Report              = @($reconcileReport)
    State               = $finalState
}
