# ==============================================================================
# scripts/state-manager.ps1 — Administrador Canónico de Estado y Memoria
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 10: Estado Persistente .autopilot)
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$pythonExe = "C:\Python314\python.exe"
$stateSchemaPath = Join-Path $infraRoot "schemas\autopilot-state.schema.json"
$contractSchemaPath = Join-Path $infraRoot "schemas\run-contract.schema.json"

# ------------------------------------------------------------------------------
# 1. Sanitización de Secretos y Credenciales
# ------------------------------------------------------------------------------
function Sanitize-StringContent([string]$text) {
    if ([string]::IsNullOrEmpty($text)) { return $text }
    
    $sanitized = $text
    # API Keys / Tokens comunes
    $sanitized = $sanitized -replace 'sk-[a-zA-Z0-9_\-]{20,}', '[REDACTED]'
    $sanitized = $sanitized -replace 'ghp_[a-zA-Z0-9]{30,}', '[REDACTED]'
    $sanitized = $sanitized -replace 'Bearer\s+[a-zA-Z0-9_\-\.]{20,}', 'Bearer [REDACTED]'
    $sanitized = $sanitized -replace '(?i)(api[_-]?key|password|secret|token|cookie|auth|authorization)\s*[:=]\s*["'']?[a-zA-Z0-9_\-\.\$]{8,}["'']?', '$1: "[REDACTED]"'
    $sanitized = $sanitized -replace '(?i)"(password|secret|token|authorization|cookie)"\s*:\s*"[^"]+"', '"$1": "[REDACTED]"'

    return $sanitized
}

function Sanitize-ObjectDeep($obj) {
    if ($null -eq $obj) { return $null }
    if ($obj -is [string]) {
        return (Sanitize-StringContent $obj)
    } elseif ($obj -is [System.Collections.IDictionary]) {
        $clone = [ordered]@{}
        foreach ($k in $obj.Keys) {
            $val = $obj[$k]
            if ($k -match '(?i)(key|secret|password|token|cookie|auth|credential)') {
                $clone[$k] = "[REDACTED]"
            } else {
                $clone[$k] = Sanitize-ObjectDeep $val
            }
        }
        return $clone
    } elseif ($obj -is [PSCustomObject]) {
        $clone = [ordered]@{}
        foreach ($p in $obj.PSObject.Properties.Name) {
            $val = $obj.$p
            if ($p -match '(?i)(key|secret|password|token|cookie|auth|credential)') {
                $clone[$p] = "[REDACTED]"
            } else {
                $clone[$p] = Sanitize-ObjectDeep $val
            }
        }
        return (New-Object PSCustomObject -Property $clone)
    } elseif ($obj -is [System.Collections.IEnumerable]) {
        $list = [System.Collections.Generic.List[object]]::new()
        foreach ($item in $obj) {
            $list.Add((Sanitize-ObjectDeep $item))
        }
        return , $list.ToArray()
    }
    return $obj
}

# ------------------------------------------------------------------------------
# 2. Máquina de Estados Cerrada y Transiciones Deterministas
# ------------------------------------------------------------------------------
$script:AllowedStates = @(
    "INITIALIZED",
    "PREFLIGHT",
    "AUTHORIZED",
    "RUNNING",
    "CHECKPOINTING",
    "RECOVERING",
    "BLOCKED_REQUIRES_HUMAN",
    "STALLED",
    "FAILED",
    "COMPLETED",
    "ABORTED"
)

$script:AllowedTransitions = @{
    "INITIALIZED"            = @("PREFLIGHT", "AUTHORIZED", "ABORTED")
    "PREFLIGHT"              = @("AUTHORIZED", "BLOCKED_REQUIRES_HUMAN", "FAILED", "ABORTED")
    "AUTHORIZED"             = @("RUNNING", "ABORTED")
    "RUNNING"                = @("CHECKPOINTING", "RECOVERING", "BLOCKED_REQUIRES_HUMAN", "STALLED", "FAILED", "COMPLETED", "ABORTED")
    "CHECKPOINTING"          = @("RUNNING", "COMPLETED", "FAILED", "ABORTED")
    "RECOVERING"             = @("RUNNING", "BLOCKED_REQUIRES_HUMAN", "STALLED", "FAILED", "ABORTED")
    "BLOCKED_REQUIRES_HUMAN" = @("AUTHORIZED", "RUNNING", "ABORTED")
    "STALLED"                = @("RECOVERING", "BLOCKED_REQUIRES_HUMAN", "FAILED", "ABORTED")
    "FAILED"                 = @("RECOVERING", "ABORTED")
    "COMPLETED"              = @()
    "ABORTED"                = @()
}

function Test-StateTransition([string]$fromState, [string]$toState) {
    if ($script:AllowedStates -notcontains $fromState) {
        return @{ Valid = $false; Error = "Estado de origen desconocido: '$fromState'" }
    }
    if ($script:AllowedStates -notcontains $toState) {
        return @{ Valid = $false; Error = "Estado de destino desconocido: '$toState'" }
    }
    if ($fromState -eq $toState) {
        return @{ Valid = $true; Error = $null }
    }
    
    $validTargets = $script:AllowedTransitions[$fromState]
    if ($null -eq $validTargets -or $validTargets -notcontains $toState) {
        return @{ Valid = $false; Error = "Transición inválida de '$fromState' hacia '$toState'." }
    }
    return @{ Valid = $true; Error = $null }
}

# ------------------------------------------------------------------------------
# 3. Validación de Schemas JSON con Python + jsonschema
# ------------------------------------------------------------------------------
function Test-SchemaValidation([string]$jsonContent, [string]$schemaPath) {
    $validatePy = @'
import sys, json, jsonschema
try:
    data = json.load(sys.stdin)
    schema = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    jsonschema.validate(instance=data, schema=schema)
    print('VALID')
except Exception as e:
    print('INVALID: ' + str(e))
'@
    $res = $jsonContent | & $pythonExe -c $validatePy "$schemaPath"
    return $res
}

function Test-FileSchemaValidation([string]$filePath, [string]$schemaPath) {
    $validatePy = @'
import sys, json, jsonschema
try:
    data = json.load(open(sys.argv[1], encoding='utf-8-sig'))
    schema = json.load(open(sys.argv[2], encoding='utf-8-sig'))
    jsonschema.validate(instance=data, schema=schema)
    print('VALID')
except Exception as e:
    print('INVALID: ' + str(e))
'@
    $res = & $pythonExe -c $validatePy "$filePath" "$schemaPath"
    return $res
}

# ------------------------------------------------------------------------------
# 4. Escritura Atómica y Segura de STATE.json
# ------------------------------------------------------------------------------
function Write-AtomicState {
    param(
        [Parameter(Mandatory = $true)]
        [object]$StateObj,

        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir,

        [Parameter(Mandatory = $false)]
        [bool]$ValidateTransition = $true
    )

    if (-not (Test-Path -LiteralPath $AutopilotDir)) {
        New-Item -ItemType Directory -Path $AutopilotDir -Force | Out-Null
    }

    $statePath = Join-Path $AutopilotDir "STATE.json"
    $previousPath = Join-Path $AutopilotDir "STATE.previous.json"
    $tmpPath = Join-Path $AutopilotDir "STATE.tmp.json"

    # Verificar transición de estado si el archivo actual existe
    if ($ValidateTransition -and (Test-Path -LiteralPath $statePath)) {
        try {
            $currentStateJson = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8
            $currentObj = $currentStateJson | ConvertFrom-Json
            if ($currentObj -and $currentObj.status) {
                $transCheck = Test-StateTransition $currentObj.status $StateObj.status
                if (-not $transCheck.Valid) {
                    throw "Transición inválida: $($transCheck.Error)"
                }
            }
        } catch {
            if ($_.ToString() -match "Transición inválida") {
                throw
            }
            # Si el STATE actual estaba corrupto, permitir avanzar para recuperación
        }
    }

    # Actualizar timestamp
    $StateObj.updated_at = (Get-Date).ToString("o")

    # Sanitizar objeto completo antes de serializar
    $sanitizedObj = Sanitize-ObjectDeep $StateObj
    $jsonContent = $sanitizedObj | ConvertTo-Json -Depth 10

    # 1. Escribir archivo temporal
    [System.IO.File]::WriteAllText($tmpPath, $jsonContent, [System.Text.Encoding]::UTF8)

    # 2. Validar contra el schema formal
    $valResult = Test-FileSchemaValidation $tmpPath $stateSchemaPath
    if ($valResult -notmatch "^VALID") {
        if (Test-Path -LiteralPath $tmpPath) { Remove-Item -LiteralPath $tmpPath -Force -ErrorAction SilentlyContinue }
        throw "Error de validación contra autopilot-state.schema.json: $valResult"
    }

    # 3. Guardar copia de respaldo en STATE.previous.json si existe STATE.json
    if (Test-Path -LiteralPath $statePath) {
        Copy-Item -LiteralPath $statePath -Destination $previousPath -Force
    }

    # 4. Reemplazo atómico utilizando Python os.replace()
    $replacePy = @'
import os, sys
src = sys.argv[1]
dst = sys.argv[2]
os.replace(src, dst)
print('REPLACED')
'@
    $repRes = & $pythonExe -c $replacePy "$tmpPath" "$statePath"
    if ($repRes -notmatch "^REPLACED") {
        throw "Fallo en el reemplazo atómico de STATE.json: $repRes"
    }

    # 5. Verificación determinista de lectura posterior
    try {
        $readBack = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($readBack.run_id -ne $StateObj.run_id) {
            throw "El archivo escrito no coincide con el run_id esperado."
        }
    } catch {
        throw "Verificación posterior de STATE.json falló: $_"
    }

    # 6. Actualizar vista humana derivada STATE.md
    Update-DerivedStateMd -StateObj $readBack -AutopilotDir $AutopilotDir

    return $readBack
}

# ------------------------------------------------------------------------------
# 5. Generación de Vista Humana Derivada STATE.md
# ------------------------------------------------------------------------------
function Update-DerivedStateMd {
    param(
        [Parameter(Mandatory = $true)]
        [object]$StateObj,

        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir
    )

    $stateMdPath = Join-Path $AutopilotDir "STATE.md"
    
    $completedList = if ($StateObj.completed_tasks -and $StateObj.completed_tasks.Count -gt 0) {
        ($StateObj.completed_tasks | ForEach-Object { "- [x] $_" }) -join "`n"
    } else {
        "- *(ninguna tarea completada aún)*"
    }

    $pendingList = if ($StateObj.pending_tasks -and $StateObj.pending_tasks.Count -gt 0) {
        ($StateObj.pending_tasks | ForEach-Object { "- [ ] $_" }) -join "`n"
    } else {
        "- *(ninguna tarea pendiente)*"
    }

    $criteriaList = if ($StateObj.acceptance_criteria -and $StateObj.acceptance_criteria.Count -gt 0) {
        ($StateObj.acceptance_criteria | ForEach-Object { "- $_" }) -join "`n"
    } else {
        "- *(sin criterios registrados)*"
    }

    $changedFilesList = if ($StateObj.git.changed_files -and $StateObj.git.changed_files.Count -gt 0) {
        ($StateObj.git.changed_files | ForEach-Object { '`' + $_.Trim() + '`' }) -join ", "
    } else {
        "*(ninguno)*"
    }

    $mdLines = @(
        "# Estado Operativo del Autopilot (Vista Humana)",
        "",
        "> **Nota:** Este archivo es generado automáticamente desde ``STATE.json``. La fuente operativa de verdad es ``STATE.json``.",
        "",
        "## Resumen del Run",
        ("- **Run ID:** ``{0}``" -f $StateObj.run_id),
        ("- **Proyecto:** ``{0}``" -f $StateObj.project_id),
        ("- **Objetivo:** {0}" -f $StateObj.objective),
        ("- **Estado Actual:** **{0}**" -f $StateObj.status),
        ("- **Fase:** ``{0}``" -f $StateObj.current_phase),
        ("- **Tarea Activa:** {0}" -f $StateObj.current_task),
        ("- **Ciclo:** {0} de {1}" -f $StateObj.cycle, $StateObj.max_cycles),
        ("- **Última Actualización:** {0}" -f $StateObj.updated_at),
        "",
        "## Tareas",
        "### Completadas",
        $completedList,
        "",
        "### Pendientes",
        $pendingList,
        "",
        "## Criterios de Aceptación",
        $criteriaList,
        "",
        "## Snapshot Técnico (Git & Tests)",
        ("- **Git Branch:** ``{0}``" -f $StateObj.git.branch),
        ("- **Git HEAD:** ``{0}``" -f $StateObj.git.head),
        ("- **Git Dirty:** {0}" -f $StateObj.git.dirty),
        "- **Archivos modificados:** $changedFilesList",
        ("- **Último Test:** ``{0}`` -> **{1}** (ExitCode: {2})" -f $StateObj.tests.last_command, $StateObj.tests.status, $StateObj.tests.last_exit_code),
        ("- **Build:** {0}" -f $StateObj.build.status),
        "",
        "## Diagnóstico y Próximo Paso",
        ("- **Falla recurrente:** {0} (Repeticiones: {1})" -f $(if ($StateObj.failure.last_signature) { $StateObj.failure.last_signature } else { 'Ninguna' }), $StateObj.failure.repeated_count),
        ("- **Último Checkpoint:** {0}" -f $(if ($StateObj.checkpoint.last_id) { $StateObj.checkpoint.last_id } else { 'Ninguno' })),
        ("- **Próxima Acción:** **{0}**" -f $StateObj.next_action),
        ""
    )

    $mdContent = $mdLines -join "`n"
    [System.IO.File]::WriteAllText($stateMdPath, $mdContent, [System.Text.Encoding]::UTF8)
}

# ------------------------------------------------------------------------------
# 6. Registro de Eventos Append-Only (EVENTS.jsonl)
# ------------------------------------------------------------------------------
function Add-AutopilotEvent {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir,

        [Parameter(Mandatory = $true)]
        [string]$RunId,

        [Parameter(Mandatory = $true)]
        [string]$Actor,

        [Parameter(Mandatory = $true)]
        [string]$Type,

        [Parameter(Mandatory = $true)]
        [object]$Payload
    )

    $eventsPath = Join-Path $AutopilotDir "EVENTS.jsonl"
    
    # Calcular seq estrictamente monotónica
    $currentSeq = 1
    if (Test-Path -LiteralPath $eventsPath) {
        $lines = [System.IO.File]::ReadAllLines($eventsPath, [System.Text.Encoding]::UTF8)
        if ($lines.Length -gt 0) {
            $lastLine = $lines[$lines.Length - 1]
            if (-not [string]::IsNullOrWhiteSpace($lastLine)) {
                try {
                    $lastEvt = $lastLine | ConvertFrom-Json
                    if ($lastEvt.seq) {
                        $currentSeq = [int]$lastEvt.seq + 1
                    }
                } catch {
                    $currentSeq = $lines.Length + 1
                }
            }
        }
    }

    $sanitizedPayload = Sanitize-ObjectDeep $Payload
    $eventId = "evt-" + [System.Guid]::NewGuid().ToString("N").Substring(0, 12)
    $timestamp = (Get-Date).ToString("o")

    $eventRecord = [ordered]@{
        schema_version = "1.0"
        seq            = $currentSeq
        event_id       = $eventId
        timestamp      = $timestamp
        run_id         = $RunId
        actor          = $Actor
        type           = $Type
        payload        = $sanitizedPayload
    }

    $eventLine = $eventRecord | ConvertTo-Json -Compress -Depth 10
    
    # Append atómico a la línea
    [System.IO.File]::AppendAllText($eventsPath, $eventLine + [System.Environment]::NewLine, [System.Text.Encoding]::UTF8)
    
    return $eventRecord
}

# ------------------------------------------------------------------------------
# 7. Heartbeat y Detección de Procesos Stale (HEARTBEAT.json)
# ------------------------------------------------------------------------------
function Update-AutopilotHeartbeat {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir,

        [Parameter(Mandatory = $true)]
        [string]$RunId,

        [Parameter(Mandatory = $true)]
        [int]$ProcessId,

        [Parameter(Mandatory = $true)]
        [string]$Status,

        [Parameter(Mandatory = $false)]
        [string]$CurrentTask = ""
    )

    $heartbeatPath = Join-Path $AutopilotDir "HEARTBEAT.json"
    $hbObj = [ordered]@{
        run_id       = $RunId
        pid          = $ProcessId
        timestamp    = (Get-Date).ToString("o")
        status       = $Status
        current_task = $CurrentTask
    }

    $hbJson = $hbObj | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($heartbeatPath, $hbJson, [System.Text.Encoding]::UTF8)
    return $hbObj
}

function Test-HeartbeatStale {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir,

        [Parameter(Mandatory = $false)]
        [int]$ThresholdSeconds = 120
    )

    $heartbeatPath = Join-Path $AutopilotDir "HEARTBEAT.json"
    if (-not (Test-Path -LiteralPath $heartbeatPath)) {
        return @{ IsStale = $true; Reason = "No existe HEARTBEAT.json" }
    }

    try {
        $hb = Get-Content -LiteralPath $heartbeatPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $hbTime = [DateTime]::Parse($hb.timestamp)
        $diffSec = ((Get-Date) - $hbTime).TotalSeconds

        # 1. Comprobar si el proceso sigue vivo
        $procAlive = $false
        if ($hb.pid -and $hb.pid -gt 0) {
            $p = Get-Process -Id $hb.pid -ErrorAction SilentlyContinue
            if ($p -and -not $p.HasExited) { $procAlive = $true }
        }

        if (-not $procAlive) {
            return @{ IsStale = $true; Reason = "El proceso PID $($hb.pid) ya no existe en el sistema."; Heartbeat = $hb }
        }

        if ($diffSec -gt $ThresholdSeconds) {
            return @{ IsStale = $true; Reason = "Heartbeat expirado ($([Math]::Round($diffSec, 1))s > ${ThresholdSeconds}s)."; Heartbeat = $hb }
        }

        return @{ IsStale = $false; Reason = "Heartbeat activo ($([Math]::Round($diffSec, 1))s transcurridos, PID $($hb.pid) vivo)."; Heartbeat = $hb }
    } catch {
        return @{ IsStale = $true; Reason = "Error leyendo HEARTBEAT.json: $_" }
    }
}

# ------------------------------------------------------------------------------
# 8. Metadatos de Bloqueo de Ejecución de Proyecto (LOCK.json)
# NOTA ARQUITECTÓNICA (HARDENING PREVIO):
# LOCK.json dentro de .autopilot es METADATA para observabilidad, detección de PID,
# run_id y procesos abandonados (stale runs). NO constituye una primitiva atómica
# de exclusión mutua de run (dos procesos concurrentes podrían competir antes de
# escribirlo). La exclusión atómica de ejecución global se implementará en el
# Runner de Macrofase 7 mediante una primitiva atómica de kernel.
# ------------------------------------------------------------------------------
function Write-RunLockMeta {
    param(
        [Parameter(Mandatory = $true)]
        [string]$AutopilotDir,

        [Parameter(Mandatory = $true)]
        [string]$RunId,

        [Parameter(Mandatory = $true)]
        [int]$OwnerPid,

        [Parameter(Mandatory = $true)]
        [string]$ProjectRoot
    )

    $lockPath = Join-Path $AutopilotDir "LOCK.json"
    $lockObj = [ordered]@{
        note         = "METADATA de observabilidad de run autónomo. NO es lock atómico de SO. La exclusión mutua atómica reside en el Runner."
        run_id       = $RunId
        owner_pid    = $OwnerPid
        started_at   = (Get-Date).ToString("o")
        project_root = $ProjectRoot
    }

    $lockJson = $lockObj | ConvertTo-Json -Depth 4
    [System.IO.File]::WriteAllText($lockPath, $lockJson, [System.Text.Encoding]::UTF8)
    return $lockObj
}

# ------------------------------------------------------------------------------
# 9. Verificación Criptográfica de Integridad de Checkpoints
# ------------------------------------------------------------------------------
function Test-CheckpointIntegrity {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CheckpointDir
    )

    if (-not (Test-Path -LiteralPath $CheckpointDir)) {
        return [PSCustomObject]@{
            Valid  = $false
            Status = "CHECKPOINT_NOT_FOUND"
            Detail = "El directorio del checkpoint no existe: $CheckpointDir"
        }
    }

    $manifestPath = Join-Path $CheckpointDir "checkpoint-manifest.json"
    if (-not (Test-Path -LiteralPath $manifestPath)) {
        return [PSCustomObject]@{
            Valid  = $false
            Status = "CHECKPOINT_INTEGRITY_FAILED"
            Detail = "Falta checkpoint-manifest.json en $CheckpointDir"
        }
    }

    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if (-not $manifest.files -or $manifest.files.Count -eq 0) {
            return [PSCustomObject]@{
                Valid  = $false
                Status = "CHECKPOINT_INTEGRITY_FAILED"
                Detail = "checkpoint-manifest.json no contiene lista de archivos"
            }
        }

        foreach ($entry in $manifest.files) {
            $fPath = Join-Path $CheckpointDir $entry.filename
            if (-not (Test-Path -LiteralPath $fPath)) {
                return [PSCustomObject]@{
                    Valid  = $false
                    Status = "CHECKPOINT_INTEGRITY_FAILED"
                    Detail = "Archivo registrado en manifiesto no existe: $($entry.filename)"
                }
            }

            $item = Get-Item -LiteralPath $fPath
            if ($item.Length -ne $entry.size_bytes) {
                return [PSCustomObject]@{
                    Valid  = $false
                    Status = "CHECKPOINT_INTEGRITY_FAILED"
                    Detail = "Discrepancia de tamaño en $($entry.filename): esperado $($entry.size_bytes), real $($item.Length)"
                }
            }

            $hash = (Get-FileHash -LiteralPath $fPath -Algorithm SHA256).Hash
            if ($hash -ne $entry.sha256) {
                return [PSCustomObject]@{
                    Valid  = $false
                    Status = "CHECKPOINT_INTEGRITY_FAILED"
                    Detail = "Discrepancia de SHA-256 en $($entry.filename): esperado $($entry.sha256), real $hash"
                }
            }
        }

        return [PSCustomObject]@{
            Valid  = $true
            Status = "CHECKPOINT_INTEGRITY_OK"
            Detail = "Todos los artefactos verificados contra SHA-256 de checkpoint-manifest.json ($($manifest.files.Count) archivos)"
        }
    } catch {
        return [PSCustomObject]@{
            Valid  = $false
            Status = "CHECKPOINT_INTEGRITY_FAILED"
            Detail = "Error parseando o verificando checkpoint-manifest.json: $_"
        }
    }
}
