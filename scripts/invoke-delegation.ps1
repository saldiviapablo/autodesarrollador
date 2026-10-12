# ==============================================================================
# scripts/invoke-delegation.ps1 — Mediador de Delegación Estructurada
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 8 — Worker Qwen Code / Handoff)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$RequestFile = "",

    [Parameter(Mandatory = $false)]
    [string]$RequestJson = "",

    [Parameter(Mandatory = $false)]
    [string]$MaxWallTime = "300s",

    [Parameter(Mandatory = $false)]
    [int]$TimeoutSeconds = 360,

    [Parameter(Mandatory = $false)]
    [string[]]$ExtraWorkerArgs = @()
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$pythonExe = "C:\Python314\python.exe"
$reqSchemaPath = Join-Path $infraRoot "schemas\delegation-request.schema.json"
$resSchemaPath = Join-Path $infraRoot "schemas\delegation-result.schema.json"

# 1. Obtener y parsear el request
$rawRequestText = ""
if (-not [string]::IsNullOrEmpty($RequestFile) -and (Test-Path -LiteralPath $RequestFile)) {
    $rawRequestText = Get-Content -LiteralPath $RequestFile -Raw -Encoding UTF8
} elseif (-not [string]::IsNullOrEmpty($RequestJson)) {
    $rawRequestText = $RequestJson
} else {
    throw "Debe proporcionar -RequestFile o -RequestJson."
}

# 2. Validar schema de DelegationRequest usando Python + jsonschema
function Test-JsonAgainstSchema([string]$jsonContent, [string]$schemaPath) {
    $tempFile = [System.IO.Path]::GetTempFileName()
    try {
        [System.IO.File]::WriteAllText($tempFile, $jsonContent, [System.Text.Encoding]::UTF8)
        $validatePy = "import sys, json, jsonschema; d = json.load(open(sys.argv[1], encoding='utf-8-sig')); s = json.load(open(sys.argv[2], encoding='utf-8-sig')); jsonschema.validate(instance=d, schema=s); print('VALID')"
        $res = & $pythonExe -c $validatePy $tempFile $schemaPath 2>&1
        $resStr = ($res | Out-String).Trim()
        return $resStr
    } catch {
        return "INVALID: $($_.Exception.Message)"
    } finally {
        if (Test-Path -LiteralPath $tempFile) { Remove-Item -LiteralPath $tempFile -Force -ErrorAction SilentlyContinue }
    }
}

$reqValidation = Test-JsonAgainstSchema $rawRequestText $reqSchemaPath
if ($reqValidation -notmatch "^VALID") {
    return [PSCustomObject]@{
        Status   = "INVALID_DELEGATION"
        Error    = "Schema de DelegationRequest no válido: $reqValidation"
        Summary  = "La solicitud de delegación no cumple con schemas/delegation-request.schema.json"
        Request  = $null
        Result   = $null
    }
}

$requestObj = $rawRequestText | ConvertFrom-Json
$delId = $requestObj.delegation_id

# 3. Canonicalización y validación de Workspace Boundary
$rawWorkspace = $requestObj.workspace
if (-not (Test-Path -LiteralPath $rawWorkspace)) {
    return [PSCustomObject]@{
        Status   = "INVALID_WORKSPACE"
        Error    = "La ruta de workspace no existe: $rawWorkspace"
        Summary  = "El espacio de trabajo solicitado no es accesible."
        Request  = $requestObj
        Result   = $null
    }
}
$canonicalWorkspace = (Resolve-Path -LiteralPath $rawWorkspace).Path

# Validar que no intente escapar a directorios del sistema protegidos
$protectedPrefixes = @("C:\Windows", "C:\Program Files", "C:\Program Files (x86)")
foreach ($prot in $protectedPrefixes) {
    if ($canonicalWorkspace.StartsWith($prot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return [PSCustomObject]@{
            Status   = "SECURITY_VIOLATION"
            Error    = "Workspace en directorio protegido de Windows: $canonicalWorkspace"
            Summary  = "Violación de límites de workspace según config/security.yaml"
            Request  = $requestObj
            Result   = $null
        }
    }
}

# 4. Guardar request en runtime/delegations/<delId>/request.json
$delRuntimeDir = Join-Path $infraRoot "runtime\delegations\$delId"
if (-not (Test-Path -LiteralPath $delRuntimeDir)) {
    New-Item -ItemType Directory -Path $delRuntimeDir -Force | Out-Null
}
$storedReqPath = Join-Path $delRuntimeDir "request.json"
$rawRequestText | Set-Content -LiteralPath $storedReqPath -Encoding UTF8

# 5. Construir prompt para Qwen Code Worker a partir del contrato
$promptParts = [System.Collections.Generic.List[string]]::new()
$promptParts.Add("OBJETIVO GENERAL: $($requestObj.objective)")
$promptParts.Add("TAREA ESPECIFICA: $($requestObj.task)")

if ($requestObj.acceptance_criteria -and $requestObj.acceptance_criteria.Count -gt 0) {
    $promptParts.Add("CRITERIOS DE ACEPTACION:")
    foreach ($crit in $requestObj.acceptance_criteria) {
        $promptParts.Add("- $crit")
    }
}

if ($requestObj.tests -and $requestObj.tests.Count -gt 0) {
    $promptParts.Add("PRUEBAS A VERIFICAR:")
    foreach ($testCmd in $requestObj.tests) {
        $promptParts.Add("- $testCmd")
    }
}

if ($requestObj.forbidden_actions -and $requestObj.forbidden_actions.Count -gt 0) {
    $promptParts.Add("ACCIONES PROHIBIDAS (ESTRICTO):")
    foreach ($forbid in $requestObj.forbidden_actions) {
        $promptParts.Add("- $forbid")
    }
}

$promptParts.Add("INSTRUCCIONES DE EJECUCION: Inspecciona los archivos relevantes en el proyecto, identifica la causa raiz del fallo, modifica el codigo para corregirlo, ejecuta las pruebas unitarias y confirma que pasen.")

$workerPrompt = $promptParts -join "`n"

# 6. Invocar Qwen Code Worker (adquiere Inference Lock automáticamente)
$invokeQwenScript = Join-Path $infraRoot "scripts\invoke-qwen-code.ps1"
$workerResult = & $invokeQwenScript `
    -Prompt $workerPrompt `
    -WorkingDir $canonicalWorkspace `
    -ApprovalMode "yolo" `
    -OutputFormat "json" `
    -MaxWallTime $MaxWallTime `
    -TimeoutSeconds $TimeoutSeconds `
    -ExtraArgs $ExtraWorkerArgs

# 7. Ejecutar y auditar pruebas unitarias de forma determinista
$executedTests = [System.Collections.Generic.List[PSCustomObject]]::new()
$allTestsPassed = $true

if ($requestObj.tests -and $requestObj.tests.Count -gt 0) {
    foreach ($tCmd in $requestObj.tests) {
        $swTest = [System.Diagnostics.Stopwatch]::StartNew()
        $tOut = ""
        $tExit = -1
        try {
            $tProc = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command $tCmd" -WorkingDirectory $canonicalWorkspace -RedirectStandardOutput (Join-Path $delRuntimeDir "test_stdout.log") -RedirectStandardError (Join-Path $delRuntimeDir "test_stderr.log") -Wait -PassThru
            $tExit = $tProc.ExitCode
            $tOutContent = if (Test-Path (Join-Path $delRuntimeDir "test_stdout.log")) { Get-Content (Join-Path $delRuntimeDir "test_stdout.log") -Raw } else { "" }
            $tOut = $tOutContent
        } catch {
            $tOut = $_.Exception.Message
        }
        $swTest.Stop()

        $tStatus = if ($tExit -eq 0) { "PASS" } else { "FAIL"; $allTestsPassed = $false }
        $executedTests.Add([PSCustomObject]@{
            command   = $tCmd
            status    = $tStatus
            exit_code = $tExit
            output    = if ($tOut) { $tOut.Trim() } else { "" }
        })
    }
}

# 8. Identificar archivos modificados en Git dentro del workspace (filtrando artefactos temporales/runtime)
function Test-IsSignificantChange([string]$filePath) {
    if ([string]::IsNullOrWhiteSpace($filePath)) { return $false }
    $norm = $filePath -replace '\\', '/'
    if ($norm -match '(^|/)__pycache__(/|$)' -or
        $norm -match '\.(pyc|pyo|pyd|log|tmp|swp)$' -or
        $norm -match '(^|/)\.pytest_cache(/|$)' -or
        $norm -match '(^|/)\.coverage($|/)') {
        return $false
    }
    return $true
}

$changedFiles = [System.Collections.Generic.List[string]]::new()
try {
    $gitStatusOut = & git -C "$canonicalWorkspace" status --porcelain 2>&1
    foreach ($line in ($gitStatusOut -split "`r?`n")) {
        if ($line -match '^\s*[MADRCU?]+\s+(.+)$') {
            $f = $matches[1].Trim()
            if (Test-IsSignificantChange $f) {
                $changedFiles.Add($f)
            }
        }
    }
    if ($changedFiles.Count -eq 0) {
        $recentFiles = & git -C "$canonicalWorkspace" log -1 --name-only --pretty="" 2>&1
        foreach ($line in ($recentFiles -split "`r?`n")) {
            if (-not [string]::IsNullOrWhiteSpace($line)) {
                $f = $line.Trim()
                if (Test-IsSignificantChange $f) {
                    $changedFiles.Add($f)
                }
            }
        }
    }
} catch { }

# 9. Determinar estado de la delegación
$finalStatus = if ($workerResult.Success -and $allTestsPassed -and ($changedFiles.Count -gt 0)) {
    "SUCCESS"
} elseif (-not $workerResult.Success -and $workerResult.TimedOut) {
    "TIMEOUT"
} else {
    "FAILED"
}

$summaryText = if ($workerResult.Json -and $workerResult.Json.response) {
    $workerResult.Json.response
} elseif ($workerResult.Stdout) {
    $workerResult.Stdout.Trim()
} else {
    "Qwen Code Worker finalizó con estado $finalStatus."
}

if ($summaryText.Length -gt 800) {
    $summaryText = $summaryText.Substring(0, 800) + "... [truncado]"
}
if ([string]::IsNullOrWhiteSpace($summaryText)) {
    $summaryText = "Ejecución completada por Qwen Code Worker."
}

# 10. Construir objeto DelegationResult estructurado
$resultObj = [ordered]@{
    schema_version = "1.0"
    delegation_id  = $delId
    status         = $finalStatus
    summary        = $summaryText
    files_changed  = @($changedFiles)
    tests          = @($executedTests)
    commands       = @($requestObj.tests)
    errors         = if ($workerResult.Stderr) { @($workerResult.Stderr.Trim()) } else { @() }
    needs_review   = $true
    review_notes   = "Tarea procesada por Qwen Code Worker. Pruebas unitarias: $(if ($allTestsPassed) { 'PASS' } else { 'FAIL' }). Archivos modificados: $($changedFiles.Count)."
}

$resultJsonText = $resultObj | ConvertTo-Json -Depth 6

# 11. Validar contra schemas/delegation-result.schema.json
$resValidation = Test-JsonAgainstSchema $resultJsonText $resSchemaPath
if ($resValidation -notmatch "^VALID") {
    # Si falla la validación del resultado, estructurar fallback válido
    $resultObj.errors += @("Error de validacion de schema de resultado: $resValidation")
}

$storedResPath = Join-Path $delRuntimeDir "result.json"
$resultJsonText | Set-Content -LiteralPath $storedResPath -Encoding UTF8

return [PSCustomObject]@{
    Status      = $finalStatus
    ResultObj   = ($resultJsonText | ConvertFrom-Json)
    ResultJson  = $resultJsonText
    ResultFile  = $storedResPath
    WorkerOutput= $workerResult
}
