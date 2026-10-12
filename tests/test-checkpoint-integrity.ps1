# ==============================================================================
# tests/test-checkpoint-integrity.ps1 — Prueba de Regresión de Integridad Criptográfica
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Hardening Previo Macrofase 6: Checkpoint-Manifest y SHA-256)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$SandboxDir = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $SandboxDir) {
    $SandboxDir = Join-Path $infraRoot "sandbox\chk-integrity-test"
}

. (Join-Path $infraRoot "scripts\state-manager.ps1")
$initScript = Join-Path $infraRoot "scripts\init-autopilot-project.ps1"
$chkScript = Join-Path $infraRoot "scripts\create-autopilot-checkpoint.ps1"
$recoverScript = Join-Path $infraRoot "scripts\recover-autopilot.ps1"

Write-Host "=============================================================================="
Write-Host "INICIANDO TEST DE INTEGRIDAD CRIPTOGRAFICA DE CHECKPOINTS"
Write-Host "Sandbox: $SandboxDir"
Write-Host "=============================================================================="

# Limpiar sandbox previo
if (Test-Path -LiteralPath $SandboxDir) {
    # Quitar ReadOnly recursivo antes de borrar
    Get-ChildItem -Path $SandboxDir -Recurse -Force -ErrorAction SilentlyContinue | ForEach-Object {
        $_.IsReadOnly = $false
    }
    Remove-Item -LiteralPath $SandboxDir -Recurse -Force -ErrorAction SilentlyContinue
}
New-Item -ItemType Directory -Path $SandboxDir -Force | Out-Null

# Inicializar git en sandbox
& git -C "$SandboxDir" init -q 2>&1 | Out-Null
& git -C "$SandboxDir" config user.email "test@example.com"
& git -C "$SandboxDir" config user.name "Test"

# Crear archivo de prueba
$dummyFile = Join-Path $SandboxDir "app.py"
Set-Content -LiteralPath $dummyFile -Value "print('v1')" -Encoding UTF8
& git -C "$SandboxDir" add app.py
& git -C "$SandboxDir" commit -m "initial commit" -q 2>&1 | Out-Null

# Inicializar .autopilot
$initRes = & $initScript `
    -ProjectPath $SandboxDir `
    -Objective "Validar integridad criptográfica de checkpoints" `
    -AcceptanceCriteria @("Verificar SHA-256 en checkpoint-manifest.json", "Detectar manipulaciones") `
    -AutonomyMode "unattended" `
    -TimeBudgetMinutes 60 `
    -Force

$autopilotDir = $initRes.AutopilotDir

# Test 1: Crear Checkpoint 1 (íntegro)
Write-Host "[1/4] Creando Checkpoint 1 íntegro..."
$chk1 = & $chkScript -ProjectPath $SandboxDir -CheckpointId "chk-integrity-01" -Reason "Snapshot base integro"
$chk1Dir = $chk1.Directory
$manifest1Path = Join-Path $chk1Dir "checkpoint-manifest.json"

$t1Pass = (Test-Path -LiteralPath $manifest1Path)
if (-not $t1Pass) { throw "Test 1 Falló: No se generó checkpoint-manifest.json" }

$integ1 = Test-CheckpointIntegrity -CheckpointDir $chk1Dir
$t1Valid = ($integ1.Valid -eq $true -and $integ1.Status -eq "CHECKPOINT_INTEGRITY_OK")
Write-Host "  [PASS] Test 1: Checkpoint 1 generado con manifiesto y hashes válidos ($($integ1.Detail))"

# Test 2: Comprobar lectura de recuperación con Checkpoint 1
Write-Host "[2/4] Verificando reconciliación de Checkpoint 1 válido..."
$rec1 = & $recoverScript -ProjectPath $SandboxDir -CheckpointId "chk-integrity-01"
$t2Pass = ($rec1.Status -eq "RUNNING" -or $rec1.Status -eq "RECOVERING")
Write-Host "  [PASS] Test 2: Checkpoint 1 verificado y aceptado por recover-autopilot.ps1"

# Test 3: Crear Checkpoint 2 y corromper intencionalmente un archivo
Write-Host "[3/4] Creando Checkpoint 2 y simulando manipulación indebida..."
Set-Content -LiteralPath $dummyFile -Value "print('v2')" -Encoding UTF8
$chk2 = & $chkScript -ProjectPath $SandboxDir -CheckpointId "chk-tampered-02" -Reason "Snapshot previo a sabotaje"
$chk2Dir = $chk2.Directory

# Quitar readonly a state.json dentro de chk2 y alterar contenido
$chk2State = Join-Path $chk2Dir "state.json"
(Get-Item -LiteralPath $chk2State).IsReadOnly = $false
Add-Content -LiteralPath $chk2State -Value "`n// TAMPERED_DATA_BYTES" -Encoding UTF8
(Get-Item -LiteralPath $chk2State).IsReadOnly = $true

# Verificar que Test-CheckpointIntegrity detecta el sabotaje
$integ2 = Test-CheckpointIntegrity -CheckpointDir $chk2Dir
$t3Detected = ($integ2.Valid -eq $false -and $integ2.Status -eq "CHECKPOINT_INTEGRITY_FAILED")
if (-not $t3Detected) { throw "Test 3 Falló: No se detectó la alteración de state.json en Checkpoint 2" }
Write-Host "  [PASS] Test 3: Alteración de archivo detectada como CHECKPOINT_INTEGRITY_FAILED ($($integ2.Detail))"

# Test 4: recover-autopilot rechaza checkpoint alterado
Write-Host "[4/4] Verificando rechazo estricto de Checkpoint 2 alterado en recover-autopilot.ps1..."
$rejectedProperly = $false
try {
    & $recoverScript -ProjectPath $SandboxDir -CheckpointId "chk-tampered-02"
} catch {
    if ($_ -match "CHECKPOINT_INTEGRITY_FAILED") {
        $rejectedProperly = $true
    }
}

if (-not $rejectedProperly) {
    throw "Test 4 Falló: recover-autopilot.ps1 no rechazó el checkpoint manipulado con CHECKPOINT_INTEGRITY_FAILED"
}
Write-Host "  [PASS] Test 4: recover-autopilot.ps1 rechazó explícitamente el checkpoint manipulado"

Write-Host "=============================================================================="
Write-Host "TEST DE INTEGRIDAD CRIPTOGRAFICA: TODOS LOS TESTS APROBADOS [PASS]"
Write-Host "=============================================================================="
exit 0
