# ==============================================================================
# scripts/create-autopilot-checkpoint.ps1 — Creador Inmutable de Checkpoints
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 10: Estado Persistente .autopilot)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $false)]
    [string]$CheckpointId = "",

    [Parameter(Mandatory = $true)]
    [string]$Reason = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

. (Join-Path $infraRoot "scripts\state-manager.ps1")

$canonicalProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$autopilotDir = Join-Path $canonicalProjectPath ".autopilot"
if (-not (Test-Path -LiteralPath $autopilotDir)) {
    throw "No se encontró el directorio .autopilot en $canonicalProjectPath"
}

$stateFile = Join-Path $autopilotDir "STATE.json"
if (-not (Test-Path -LiteralPath $stateFile)) {
    throw "No se encontró STATE.json en $autopilotDir"
}
$stateObj = Get-Content -LiteralPath $stateFile -Raw -Encoding UTF8 | ConvertFrom-Json

if ([string]::IsNullOrWhiteSpace($CheckpointId)) {
    $CheckpointId = "chk-" + (Get-Date).ToString("yyyyMMdd-HHmmss-fff")
}

$checkpointsBase = Join-Path $autopilotDir "checkpoints"
if (-not (Test-Path -LiteralPath $checkpointsBase)) {
    New-Item -ItemType Directory -Path $checkpointsBase -Force | Out-Null
}

$targetChkDir = Join-Path $checkpointsBase $CheckpointId

# Regla de Inmutabilidad: Si el checkpoint ya existe, fallar inmediatamente
if (Test-Path -LiteralPath $targetChkDir) {
    throw "El checkpoint '$CheckpointId' ya existe. Los checkpoints son estrictamente inmutables."
}

New-Item -ItemType Directory -Path $targetChkDir -Force | Out-Null

# 1. Inspeccionar Git detalladamente
$gitBranch = "unknown"
$gitHead = "unknown"
$gitDirty = $false
$gitStatus = ""
$gitDiff = ""

try {
    $gitBranch = (& git -C "$canonicalProjectPath" rev-parse --abbrev-ref HEAD 2>&1).Trim()
    $gitHead = (& git -C "$canonicalProjectPath" rev-parse --short HEAD 2>&1).Trim()
    $gitStatus = & git -C "$canonicalProjectPath" status --porcelain 2>&1
    if ($gitStatus) { $gitDirty = $true }
    $gitDiff = & git -C "$canonicalProjectPath" diff HEAD 2>&1
} catch {}

$gitMeta = [ordered]@{
    branch        = $gitBranch
    head          = $gitHead
    dirty         = $gitDirty
    status_output = if ($gitStatus) { $gitStatus.Trim() } else { "" }
    changed_files = $stateObj.git.changed_files
}

# 2. Persistir diff.patch si existe diferencia
if (-not [string]::IsNullOrWhiteSpace($gitDiff)) {
    [System.IO.File]::WriteAllText((Join-Path $targetChkDir "diff.patch"), $gitDiff, [System.Text.Encoding]::UTF8)
}

# 3. Guardar snapshots
$gitMetaJson = $gitMeta | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText((Join-Path $targetChkDir "git.json"), $gitMetaJson, [System.Text.Encoding]::UTF8)

$testsMetaJson = $stateObj.tests | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText((Join-Path $targetChkDir "tests.json"), $testsMetaJson, [System.Text.Encoding]::UTF8)

$stateJson = $stateObj | ConvertTo-Json -Depth 10
[System.IO.File]::WriteAllText((Join-Path $targetChkDir "state.json"), $stateJson, [System.Text.Encoding]::UTF8)

# 4. Construir checkpoint.json maestro
$chkMasterObj = [ordered]@{
    schema_version    = "1.0"
    run_id            = $stateObj.run_id
    checkpoint_id     = $CheckpointId
    created_at        = (Get-Date).ToString("o")
    reason            = $Reason
    current_task      = $stateObj.current_task
    next_action       = $stateObj.next_action
    hermes_session_id = $stateObj.hermes_session_id
    qwen_session_id   = $stateObj.qwen_session_id
    status            = $stateObj.status
    has_diff_patch    = (-not [string]::IsNullOrWhiteSpace($gitDiff))
}
$chkMasterJson = $chkMasterObj | ConvertTo-Json -Depth 5
[System.IO.File]::WriteAllText((Join-Path $targetChkDir "checkpoint.json"), $chkMasterJson, [System.Text.Encoding]::UTF8)

# 5. Generar checkpoint-manifest.json con SHA-256 criptográfico de todos los artefactos
$manifestFiles = [System.Collections.Generic.List[object]]::new()
Get-ChildItem -LiteralPath $targetChkDir -File | Where-Object { $_.Name -ne "checkpoint-manifest.json" } | ForEach-Object {
    $fHash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    $manifestFiles.Add([ordered]@{
        filename   = $_.Name
        size_bytes = $_.Length
        sha256     = $fHash
    })
}

$manifestObj = [ordered]@{
    schema_version = "1.0"
    checkpoint_id  = $CheckpointId
    created_at     = (Get-Date).ToString("o")
    files          = @($manifestFiles)
}
$manifestJson = $manifestObj | ConvertTo-Json -Depth 5
$manifestPath = Join-Path $targetChkDir "checkpoint-manifest.json"
[System.IO.File]::WriteAllText($manifestPath, $manifestJson, [System.Text.Encoding]::UTF8)

# 6. Marcar todos los archivos como ReadOnly en Windows
Get-ChildItem -LiteralPath $targetChkDir -File | ForEach-Object {
    $_.IsReadOnly = $true
}

# 7. Registrar evento en EVENTS.jsonl
$null = Add-AutopilotEvent `
    -AutopilotDir $autopilotDir `
    -RunId $stateObj.run_id `
    -Actor "checkpoint-manager" `
    -Type "CHECKPOINT_CREATED" `
    -Payload @{
        checkpoint_id = $CheckpointId
        reason        = $Reason
        git_head      = $gitHead
        git_dirty     = $gitDirty
        manifest_files= $manifestFiles.Count
    }

# 8. Actualizar metadatos de checkpoint en STATE.json
$stateObj.checkpoint.last_id = $CheckpointId
$stateObj.checkpoint.last_created_at = (Get-Date).ToString("o")
$updatedState = Write-AtomicState -StateObj $stateObj -AutopilotDir $autopilotDir -ValidateTransition $false

return [PSCustomObject]@{
    CheckpointId  = $CheckpointId
    Directory     = $targetChkDir
    Master        = $chkMasterObj
    Manifest      = $manifestObj
    UpdatedState  = $updatedState
}
