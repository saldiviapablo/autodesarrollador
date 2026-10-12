# ==============================================================================
# scripts/build-recovery-context.ps1 — Generador de Contexto Compacto de Recuperación
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 12: Continuidad entre Sesiones)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $false)]
    [string]$OutputPath = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$canonicalProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$autopilotDir = Join-Path $canonicalProjectPath ".autopilot"
if (-not (Test-Path -LiteralPath $autopilotDir)) {
    throw "No se encontró el directorio .autopilot en $canonicalProjectPath"
}

# 1. Cargar STATE.json
$statePath = Join-Path $autopilotDir "STATE.json"
$stateObj = Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json

# 2. Cargar RUN-CONTRACT.yaml
$contractPath = Join-Path $autopilotDir "RUN-CONTRACT.yaml"
$pythonExe = "C:\Python314\python.exe"
$readYamlPy = @'
import sys, json, yaml
with open(sys.argv[1], encoding='utf-8') as f:
    data = yaml.safe_load(f)
print(json.dumps(data))
'@
$contractJson = & $pythonExe -c $readYamlPy "$contractPath"
$contractObj = $contractJson | ConvertFrom-Json

# 3. Cargar últimos 5 eventos de EVENTS.jsonl
$recentEvents = [System.Collections.Generic.List[string]]::new()
$eventsPath = Join-Path $autopilotDir "EVENTS.jsonl"
if (Test-Path -LiteralPath $eventsPath) {
    $allLines = [System.IO.File]::ReadAllLines($eventsPath, [System.Text.Encoding]::UTF8)
    $takeCount = [Math]::Min(5, $allLines.Length)
    $startIndex = $allLines.Length - $takeCount
    for ($i = $startIndex; $i -lt $allLines.Length; $i++) {
        if (-not [string]::IsNullOrWhiteSpace($allLines[$i])) {
            try {
                $ev = $allLines[$i] | ConvertFrom-Json
                $recentEvents.Add("- [seq=$($ev.seq)] $($ev.timestamp) | $($ev.type) ($($ev.actor))")
            } catch {}
        }
    }
}

# 4. Formatear contexto compacto
$completedStr = if ($stateObj.completed_tasks.Count -gt 0) {
    ($stateObj.completed_tasks | ForEach-Object { "- [x] $_" }) -join "`n"
} else { "- *(ninguna)*" }

$pendingStr = if ($stateObj.pending_tasks.Count -gt 0) {
    ($stateObj.pending_tasks | ForEach-Object { "- [ ] $_" }) -join "`n"
} else { "- *(ninguna)*" }

function Get-Backticked([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

$criteriaStr = if ($stateObj.acceptance_criteria.Count -gt 0) {
    ($stateObj.acceptance_criteria | ForEach-Object { "- $_" }) -join "`n"
} else { "- *(sin criterios)*" }

$changedStr = if ($stateObj.git.changed_files.Count -gt 0) {
    ($stateObj.git.changed_files | ForEach-Object { Get-Backticked $_ }) -join ", "
} else { "*(ninguno)*" }

$eventsStr = if ($recentEvents.Count -gt 0) { $recentEvents -join "`n" } else { "- *(sin eventos recientes)*" }

$chkStr = if ($stateObj.checkpoint.last_id) { Get-Backticked $stateObj.checkpoint.last_id } else { 'Ninguno' }

$ctxLines = @(
    "# CONTEXTO DE RECUPERACION COMPACTO (DERIVADO)",
    "> **Principio de Memoria:** CONVERSATION != SOURCE OF TRUTH. Este resumen refleja el estado real verificado en filesystem/Git/tests.",
    "",
    "## 1. Identificacion y Objetivo",
    ("- **Run ID:** " + (Get-Backticked $stateObj.run_id)),
    ("- **Proyecto:** " + (Get-Backticked $stateObj.project_id)),
    ("- **Objetivo General:** " + $stateObj.objective),
    ("- **Estado Operativo:** **" + $stateObj.status + "**"),
    ("- **Fase:** " + (Get-Backticked $stateObj.current_phase)),
    ("- **Tarea Activa:** " + $stateObj.current_task),
    ("- **Ciclo Actual:** " + $stateObj.cycle + " / " + $stateObj.max_cycles),
    "",
    "## 2. Criterios de Aceptacion",
    $criteriaStr,
    "",
    "## 3. Estado de Tareas",
    "### Completadas",
    $completedStr,
    "### Pendientes",
    $pendingStr,
    "",
    "## 4. Evidencia Tecnica Real (Git & Tests)",
    ("- **Branch:** " + (Get-Backticked $stateObj.git.branch) + " | **HEAD:** " + (Get-Backticked $stateObj.git.head) + " | **Dirty:** " + $stateObj.git.dirty),
    ("- **Archivos modificados:** " + $changedStr),
    ("- **Ultimo Test:** " + (Get-Backticked $stateObj.tests.last_command) + " -> **" + $stateObj.tests.status + "** (ExitCode: " + $stateObj.tests.last_exit_code + ")"),
    ("- **Ultimo Checkpoint:** " + $chkStr),
    "",
    "## 5. Proxima Accion Inmediata",
    ("**" + $stateObj.next_action + "**"),
    "",
    "## 6. Historial Reciente de Eventos",
    $eventsStr,
    ""
)

$contextText = $ctxLines -join "`n"
$charCount = $contextText.Length
$approxTokens = [Math]::Round($charCount / 4.0)

if ([string]::IsNullOrWhiteSpace($OutputPath)) {
    $OutputPath = Join-Path $autopilotDir "reports\recovery-context.md"
}
$outDir = Split-Path -Parent $OutputPath
if (-not (Test-Path -LiteralPath $outDir)) {
    New-Item -ItemType Directory -Path $outDir -Force | Out-Null
}
[System.IO.File]::WriteAllText($OutputPath, $contextText, [System.Text.Encoding]::UTF8)

return [PSCustomObject]@{
    FilePath     = $OutputPath
    CharCount    = $charCount
    ApproxTokens = $approxTokens
    Content      = $contextText
}
