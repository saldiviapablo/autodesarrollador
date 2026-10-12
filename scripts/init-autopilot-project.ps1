# ==============================================================================
# scripts/init-autopilot-project.ps1 — Inicializador de Proyecto .autopilot
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 5 — Fase 10: Estado Persistente .autopilot)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectPath,

    [Parameter(Mandatory = $true)]
    [string]$Objective,

    [Parameter(Mandatory = $true)]
    [string[]]$AcceptanceCriteria,

    [Parameter(Mandatory = $false)]
    [ValidateSet("unattended", "interactive", "supervised")]
    [string]$AutonomyMode = "unattended",

    [Parameter(Mandatory = $false)]
    [int]$TimeBudgetMinutes = 120,

    [Parameter(Mandatory = $false)]
    [string[]]$TestCommands = @(),

    [Parameter(Mandatory = $false)]
    [string[]]$BuildCommands = @(),

    [Parameter(Mandatory = $false)]
    [ValidateSet("new-run", "resume")]
    [string]$Mode = "new-run",

    [Parameter(Mandatory = $false)]
    [switch]$Force
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

. (Join-Path $infraRoot "scripts\state-manager.ps1")

# 1. Canonicalizar ruta del proyecto
if (-not (Test-Path -LiteralPath $ProjectPath)) {
    New-Item -ItemType Directory -Path $ProjectPath -Force | Out-Null
}
$canonicalProjectPath = (Resolve-Path -LiteralPath $ProjectPath).Path
$autopilotDir = Join-Path $canonicalProjectPath ".autopilot"
$projectName = Split-Path -Leaf $canonicalProjectPath

# 2. Comprobar si ya existe un run previo
if (Test-Path -LiteralPath $autopilotDir) {
    $existingStateFile = Join-Path $autopilotDir "STATE.json"
    if (Test-Path -LiteralPath $existingStateFile) {
        if ($Mode -eq "resume") {
            $existingState = Get-Content -LiteralPath $existingStateFile -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Verbose "Proyecto $canonicalProjectPath ya inicializado. Modo resume activado."
            return [PSCustomObject]@{
                Status       = "RESUMED"
                ProjectPath  = $canonicalProjectPath
                AutopilotDir = $autopilotDir
                State        = $existingState
            }
        } elseif (-not $Force) {
            throw "El proyecto ya contiene un directorio .autopilot activo con estado existente. Especifique -Mode resume para continuar o -Force para sobrescribir."
        }
    }
}

# 3. Crear estructura de carpetas de .autopilot
@("logs", "evidence", "checkpoints", "reports") | ForEach-Object {
    $subDir = Join-Path $autopilotDir $_
    if (-not (Test-Path -LiteralPath $subDir)) {
        New-Item -ItemType Directory -Path $subDir -Force | Out-Null
    }
}

# 4. Crear QWEN.md si no existe en la raíz del proyecto
$qwenMdPath = Join-Path $canonicalProjectPath "QWEN.md"
if (-not (Test-Path -LiteralPath $qwenMdPath)) {
    $templatePath = Join-Path $infraRoot "templates\QWEN.md.template"
    $templateContent = if (Test-Path -LiteralPath $templatePath) {
        Get-Content -LiteralPath $templatePath -Raw -Encoding UTF8
    } else {
        "# QWEN.md`n## PROJECT`n- Nombre: $projectName`n"
    }

    $filledTemplate = $templateContent `
        -replace '\{\{PROJECT_NAME\}\}', $projectName `
        -replace '\{\{PROJECT_PURPOSE\}\}', $Objective `
        -replace '\{\{PROJECT_ARCHITECTURE\}\}', "Modular Scripting / Clean Architecture" `
        -replace '\{\{PROJECT_LANGUAGES\}\}', "Python, PowerShell" `
        -replace '\{\{PROJECT_STACK\}\}', "Standard Library" `
        -replace '\{\{PROJECT_PACKAGE_MANAGER\}\}', "pip" `
        -replace '\{\{COMMAND_INSTALL\}\}', "pip install -r requirements.txt" `
        -replace '\{\{COMMAND_BUILD\}\}', "echo 'No build required'" `
        -replace '\{\{COMMAND_RUN\}\}', "python main.py" `
        -replace '\{\{TEST_FRAMEWORK\}\}', "unittest / pytest" `
        -replace '\{\{COMMAND_TEST\}\}', ($TestCommands -join '; ')

    [System.IO.File]::WriteAllText($qwenMdPath, $filledTemplate, [System.Text.Encoding]::UTF8)
}

# 5. Generar y validar RUN-CONTRACT.yaml
$runTimestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
$runId = "run-" + $runTimestamp
$contractPath = Join-Path $autopilotDir "RUN-CONTRACT.yaml"

$runContractObj = [ordered]@{
    schema_version             = "1.0"
    run_id                     = $runId
    project_id                 = $projectName
    project_root               = ($canonicalProjectPath -replace '\\', '/')
    objective                  = $Objective
    acceptance_criteria        = @($AcceptanceCriteria)
    autonomy_mode              = $AutonomyMode
    authorized                 = $true
    authorized_at              = (Get-Date).ToString("o")
    created_at                 = (Get-Date).ToString("o")
    time_budget_minutes        = $TimeBudgetMinutes
    allowed_actions            = @("edit_file", "run_test", "git_commit_local")
    forbidden_actions          = @("git_push", "delete_root", "modify_runner_guardrails")
    test_commands              = @($TestCommands)
    build_commands             = @($BuildCommands)
    security_policy_reference  = "config/security.yaml"
}

# Serializar a YAML mediante Python + PyYAML y validar contra schema
$contractJson = $runContractObj | ConvertTo-Json -Depth 5
$tmpContractJson = Join-Path $autopilotDir "contract.tmp.json"
[System.IO.File]::WriteAllText($tmpContractJson, $contractJson, [System.Text.Encoding]::UTF8)

$genYamlPy = @'
import sys, json, yaml, jsonschema

contract_data = json.load(open(sys.argv[1], encoding='utf-8-sig'))
schema_path = sys.argv[2]
yaml_out_path = sys.argv[3]

schema = json.load(open(schema_path, encoding='utf-8-sig'))
jsonschema.validate(instance=contract_data, schema=schema)

with open(yaml_out_path, 'w', encoding='utf-8') as f:
    yaml.dump(contract_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
print('VALID_YAML_WRITTEN')
'@
$contractSchema = Join-Path $infraRoot "schemas\run-contract.schema.json"
$yamlRes = & $pythonExe -c $genYamlPy "$tmpContractJson" "$contractSchema" "$contractPath"
if (Test-Path -LiteralPath $tmpContractJson) { Remove-Item -LiteralPath $tmpContractJson -Force -ErrorAction SilentlyContinue }
if ($yamlRes -notmatch "^VALID_YAML_WRITTEN") {
    throw "Error generando o validando RUN-CONTRACT.yaml: $yamlRes"
}

# 6. Inspeccionar Git en el proyecto para estado inicial
$gitBranch = "main"
$gitHead = "none"
$gitDirty = $false
$changedFiles = @()

try {
    $bOut = & git -C "$canonicalProjectPath" rev-parse --abbrev-ref HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $bOut) { $gitBranch = $bOut.Trim() }
    $hOut = & git -C "$canonicalProjectPath" rev-parse --short HEAD 2>&1
    if ($LASTEXITCODE -eq 0 -and $hOut) { $gitHead = $hOut.Trim() }
    $statusOut = & git -C "$canonicalProjectPath" status --porcelain 2>&1
    if ($statusOut) {
        $gitDirty = $true
        foreach ($line in ($statusOut -split "`r?`n")) {
            if ($line -match '^\s*[MADRCU?]+\s+(.+)$') {
                $f = $matches[1].Trim()
                if ($f -notmatch '__pycache__' -and $f -notmatch '\.pyc$') {
                    $changedFiles += $f
                }
            }
        }
    }
} catch {}

# 7. Construir y persistir STATE.json inicial (status: INITIALIZED)
$initialStateObj = [ordered]@{
    schema_version        = "1.0"
    run_id                = $runId
    project_id            = $projectName
    objective             = $Objective
    status                = "INITIALIZED"
    created_at            = (Get-Date).ToString("o")
    updated_at            = (Get-Date).ToString("o")
    cycle                 = 0
    max_cycles            = 20
    current_phase         = "FASE_0_INITIALIZATION"
    current_task          = "Inicialización del espacio de trabajo y contratos"
    completed_tasks       = @()
    pending_tasks         = @($Objective)
    acceptance_criteria   = @($AcceptanceCriteria)
    current_delegation_id = $null
    hermes_session_id     = $null
    qwen_session_id       = $null
    git                   = [ordered]@{
        branch        = $gitBranch
        head          = $gitHead
        dirty         = $gitDirty
        changed_files = @($changedFiles)
    }
    tests                 = [ordered]@{
        status         = "NONE"
        last_command   = $null
        last_exit_code = $null
        last_run_at    = $null
    }
    build                 = [ordered]@{
        status         = "NONE"
        last_command   = $null
        last_exit_code = $null
    }
    progress              = [ordered]@{
        score              = 0
        last_progress_at   = $null
        no_progress_cycles = 0
    }
    failure               = [ordered]@{
        last_signature = $null
        repeated_count = 0
    }
    checkpoint            = [ordered]@{
        last_id         = $null
        last_created_at = $null
    }
    next_action           = "Ejecutar preflight checks y autorizar el inicio del ciclo"
}

$writtenState = Write-AtomicState -StateObj $initialStateObj -AutopilotDir $autopilotDir -ValidateTransition $false

# 8. Registrar evento inicial en EVENTS.jsonl
$initEvent = Add-AutopilotEvent `
    -AutopilotDir $autopilotDir `
    -RunId $runId `
    -Actor "init-script" `
    -Type "RUN_INITIALIZED" `
    -Payload @{
        project_id  = $projectName
        objective   = $Objective
        run_contract= "RUN-CONTRACT.yaml"
        status      = "INITIALIZED"
    }

# 9. Inicializar HEARTBEAT.json y LOCK.json
$currentPid = [System.Diagnostics.Process]::GetCurrentProcess().Id
$null = Update-AutopilotHeartbeat -AutopilotDir $autopilotDir -RunId $runId -ProcessId $currentPid -Status "INITIALIZED" -CurrentTask "Inicializado"
$null = Write-RunLockMeta -AutopilotDir $autopilotDir -RunId $runId -OwnerPid $currentPid -ProjectRoot ($canonicalProjectPath -replace '\\', '/')

return [PSCustomObject]@{
    Status       = "INITIALIZED"
    RunId        = $runId
    ProjectPath  = $canonicalProjectPath
    AutopilotDir = $autopilotDir
    ContractPath = $contractPath
    State        = $writtenState
    InitialEvent = $initEvent
}
