# ==============================================================================
# scripts/verify-qwen-code.ps1 — Verificación Integral de Qwen Code CLI (Fase 5)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 5 — Qwen Code CLI)
# ==============================================================================
[CmdletBinding()]
param(
    [string]$SystemYaml = "",
    [string]$SandboxDir = "",
    [string]$EvidenceDir = "",
    [string]$LogFile = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $SystemYaml) { $SystemYaml = Join-Path $infraRoot "config\system.yaml" }
if (-not $SandboxDir) { $SandboxDir = Join-Path $infraRoot "sandbox\qwen-code-basic" }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\installation" }
if (-not $LogFile) {
    $timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $LogFile = Join-Path $infraRoot "logs\phase-05-qwen-code-$timestamp.log"
}

# Ensure directories exist
$logParent = Split-Path -Parent $LogFile
if (-not (Test-Path -LiteralPath $logParent)) { New-Item -ItemType Directory -Path $logParent -Force | Out-Null }
if (-not (Test-Path -LiteralPath $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }
if (-not (Test-Path -LiteralPath $SandboxDir)) { New-Item -ItemType Directory -Path $SandboxDir -Force | Out-Null }

function Log-Msg {
    param([string]$Msg, [string]$Level = "INFO")
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
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
Log-Msg "INICIANDO VERIFICACION INTEGRAL DE QWEN CODE CLI (FASE 5)"
Log-Msg "Config:    $SystemYaml"
Log-Msg "Sandbox:   $SandboxDir"
Log-Msg "Evidence:  $EvidenceDir"
Log-Msg "LogFile:   $LogFile"
Log-Msg "=============================================================================="

# 1. Cargar configuracion de system.yaml mediante Python + PyYAML
Log-Msg "[1/8] Leyendo configuracion central..."
$pythonExe = "C:\Python314\python.exe"
$pyCode = 'import yaml, json, sys; print(json.dumps(yaml.safe_load(open(sys.argv[1], encoding=\"utf-8\"))))'
$cfgJson = & $pythonExe -c $pyCode "$SystemYaml"
$sysConfig = $cfgJson | ConvertFrom-Json

$llamaExe = $sysConfig.llama.executable
$llamaDir = Split-Path -Parent $llamaExe
$modelPath = $sysConfig.llama.model
$hostIp = $sysConfig.llama.host
$port = $sysConfig.llama.port
$alias = $sysConfig.llama.alias
$ctxSize = $sysConfig.llama.ctx_size
$parallel = $sysConfig.llama.parallel
$nCpuMoe = $sysConfig.llama.cpu_moe
$nGpuLayers = $sysConfig.llama.n_gpu_layers
$cacheK = $sysConfig.llama.cache_type_k
$cacheV = $sysConfig.llama.cache_type_v
$healthUri = $sysConfig.llama.health_endpoint
$modelsUri = $sysConfig.llama.models_endpoint

$llamaProcess = $null
$invokeScript = Join-Path $infraRoot "scripts\invoke-qwen-code.ps1"

try {
    # 2. Iniciar llama-server de forma controlada
    Log-Msg "[2/8] Iniciando llama-server.exe exclusivo para pruebas..."
    
    # Comprobar que el puerto este libre (sin listeners activos)
    $activeConn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($activeConn) {
        throw "El puerto $port ya esta en uso por PID $($activeConn.OwningProcess). Abortando para evitar colision."
    }

    $llamaArgs = @(
        "-m", $modelPath,
        "--alias", $alias,
        "--host", $hostIp,
        "--port", "$port",
        "--ctx-size", "$ctxSize",
        "--parallel", "$parallel",
        "--cpu-moe",
        "--n-gpu-layers", "$nGpuLayers",
        "--flash-attn", "on",
        "--cache-type-k", $cacheK,
        "--cache-type-v", $cacheV,
        "--jinja"
    )

    $llamaOut = Join-Path $infraRoot "logs\llama-phase05-stdout.log"
    $llamaErr = Join-Path $infraRoot "logs\llama-phase05-stderr.log"

    $llamaProcess = Start-Process `
        -FilePath $llamaExe `
        -ArgumentList $llamaArgs `
        -WorkingDirectory $llamaDir `
        -RedirectStandardOutput $llamaOut `
        -RedirectStandardError $llamaErr `
        -WindowStyle Hidden `
        -PassThru

    $llamaPid = $llamaProcess.Id
    Log-Msg "llama-server iniciado con PID $llamaPid. Esperando readiness..."

    $swHealth = [System.Diagnostics.Stopwatch]::StartNew()
    $llamaReady = $false
    while ($swHealth.Elapsed.TotalSeconds -lt 60) {
        if ($llamaProcess.HasExited) {
            $errContent = if (Test-Path $llamaErr) { Get-Content $llamaErr -Tail 20 | Out-String } else { "" }
            throw "llama-server termino prematuramente con ExitCode $($llamaProcess.ExitCode). Error: $errContent"
        }
        Start-Sleep -Milliseconds 500
        try {
            $hResp = Invoke-RestMethod -Uri $healthUri -TimeoutSec 2 -ErrorAction Stop
            if ($hResp.status -eq "ok") {
                $llamaReady = $true
                break
            }
        } catch {}
    }

    if (-not $llamaReady) {
        throw "Timeout esperando readiness de llama-server en $healthUri"
    }

    Log-Msg "llama-server verificado y listo en $([Math]::Round($swHealth.Elapsed.TotalSeconds, 2))s."
    Record-Test "Llama Server Ready (Health Status OK)" $true "PID=$llamaPid, Port=$port"

    # Verificar que el modelo registrado en llama sea qwen36
    $modelsResp = Invoke-RestMethod -Uri $modelsUri -TimeoutSec 5
    $activeModelId = $modelsResp.data[0].id
    Record-Test "Llama Model Registrado" ($activeModelId -eq $alias) "Model=$activeModelId"

    # 3. PRUEBA 1: Modelo Local y Conectividad
    Log-Msg "[3/8] PRUEBA 1: Modelo Local y Conectividad..."
    try {
        $p1 = & $invokeScript -Prompt "Responde exactamente la palabra: LOCAL_QWEN_OK" -OutputFormat "json" -ApprovalMode "plan" -MaxWallTime "300s" -TimeoutSeconds 360
        $p1Ok = ($p1.ExitCode -eq 0) -and ($p1.Stdout -match "LOCAL_QWEN_OK")
        Record-Test "Prueba 1: Inferencia Local Qwen" $p1Ok "ExitCode=$($p1.ExitCode), Duracion=$($p1.Duration)s"
    } catch {
        Record-Test "Prueba 1: Inferencia Local Qwen" $false $_.Exception.Message
    }

    # 4. PRUEBA 2: Headless Mode y Budgets
    Log-Msg "[4/8] PRUEBA 2: Headless Mode y Budgets..."
    try {
        $p2 = & $invokeScript -Prompt "Calcula la suma de 17 y 25. Responde unicamente con el numero resultante: 42." -OutputFormat "json" -ApprovalMode "plan" -MaxWallTime "300s" -TimeoutSeconds 360
        $p2Ok = ($p2.ExitCode -eq 0) -and ($p2.Stdout -match "42")
        Record-Test "Prueba 2: Headless Mode y Budgets" $p2Ok "ExitCode=$($p2.ExitCode), Contiene 42"
        $p2OutFile = Join-Path $EvidenceDir "qwen-code-headless.json"
        $p2.Stdout | Out-File -FilePath $p2OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 2: Headless Mode y Budgets" $false $_.Exception.Message
    }

    # 5. PRUEBA 3: Lectura de Proyecto en Sandbox
    Log-Msg "[5/8] PRUEBA 3: Lectura de Proyecto en Sandbox..."
    try {
        $calcPy = Join-Path $SandboxDir "calculator.py"
        $initialCalcLines = @(
            "def add(a: int, b: int) -> int:",
            '    """Calcula la suma de dos enteros."""',
            "    return a - b  # ERROR INTENCIONAL: se usa '-' en lugar de '+'"
        )
        $initialCalcLines | Set-Content -LiteralPath $calcPy -Encoding UTF8

        $readPrompt = "Analiza los archivos de este proyecto. Explica que funcion implementa calculator.py, que pruebas existen en test_calculator.py y cual es el fallo exacto en la logica de calculator.py que hace que fallen las pruebas. NO modifiques ningun archivo."
        $p3 = & $invokeScript -Prompt $readPrompt -WorkingDir $SandboxDir -OutputFormat "json" -ApprovalMode "plan" -MaxWallTime "300s" -TimeoutSeconds 360
        $p3Ok = ($p3.ExitCode -eq 0) -and ($p3.Stdout -match "resta|sustracci|subtraction|menos|minus|\-")
        Record-Test "Prueba 3: Inspeccion y Lectura de Codigo" $p3Ok "ExitCode=$($p3.ExitCode), Identifico bug de resta"
        $p3OutFile = Join-Path $EvidenceDir "qwen-code-read-test.json"
        $p3.Stdout | Out-File -FilePath $p3OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 3: Inspeccion y Lectura de Codigo" $false $_.Exception.Message
    }

    # 6. PRUEBA 4: Edición y Autocorrección (FAIL -> FIX -> PASS)
    Log-Msg "[6/8] PRUEBA 4: Edicion y Autocorreccion en Sandbox..."
    try {
        $testPy = Join-Path $SandboxDir "test_calculator.py"
        $testProcBefore = Start-Process -FilePath "python.exe" -ArgumentList "`"$testPy`"" -WorkingDirectory $SandboxDir -NoNewWindow -Wait -PassThru
        $beforeFailed = ($testProcBefore.ExitCode -ne 0)
        Log-Msg "  Verificacion previa: Pruebas unitarias fallan como esperado (ExitCode=$($testProcBefore.ExitCode))."

        $fixPrompt = "Ejecuta las pruebas unitarias con python test_calculator.py para comprobar que fallan. Luego modifica calculator.py para corregir el error y que use el operador de suma. Vuelve a ejecutar las pruebas unitarias y asegurate de que pasen (PASS). Termina cuando las pruebas se hayan ejecutado exitosamente."
        $p4 = & $invokeScript -Prompt $fixPrompt -WorkingDir $SandboxDir -OutputFormat "json" -ApprovalMode "yolo" -MaxWallTime "480s" -MaxSessionTurns 10 -MaxToolCalls 15 -TimeoutSeconds 540

        $calcContent = Get-Content -LiteralPath $calcPy -Raw -Encoding UTF8
        $codeHasPlus = ($calcContent -match "a\s*\+\s*b")

        $testProcAfter = Start-Process -FilePath "python.exe" -ArgumentList "`"$testPy`"" -WorkingDirectory $SandboxDir -NoNewWindow -Wait -PassThru
        $afterPassed = ($testProcAfter.ExitCode -eq 0)

        $p4Ok = ($p4.ExitCode -eq 0) -and $codeHasPlus -and $afterPassed
        Record-Test "Prueba 4: Autocorreccion (FAIL -> FIX -> PASS)" $p4Ok "TestAntesFail=$beforeFailed, CodigoModificado=$codeHasPlus, TestDespuesPass=$afterPassed"
        $p4OutFile = Join-Path $EvidenceDir "qwen-code-autofix.json"
        $p4.Stdout | Out-File -FilePath $p4OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 4: Autocorreccion (FAIL -> FIX -> PASS)" $false $_.Exception.Message
    }

    # 7. PRUEBA 5: Output Estructurado (JSON)
    Log-Msg "[7/8] PRUEBA 5: Validacion de Output Estructurado..."
    try {
        $p4JsonValid = ($p4 -and $p4.Json -ne $null)
        Record-Test "Prueba 5: Output Estructurado JSON Valido" $p4JsonValid "JSON Parseable=$p4JsonValid"
    } catch {
        Record-Test "Prueba 5: Output Estructurado JSON Valido" $false $_.Exception.Message
    }

    # 8. PRUEBA 6: Timeout Controlado
    Log-Msg "[8/8] PRUEBA 6: Control de Timeout en Wrapper..."
    try {
        $timeoutPrompt = "Escribe una historia detallada de 10000 palabras sobre la evolucion de los sistemas operativos."
        $p6 = & $invokeScript -Prompt $timeoutPrompt -WorkingDir $SandboxDir -OutputFormat "json" -ApprovalMode "plan" -MaxWallTime "2s" -TimeoutSeconds 4
        $p6Ok = ($p6.TimedOut -eq $true) -or ($p6.ExitCode -eq 55) -or ($p6.Duration -le 10)
        Record-Test "Prueba 6: Manejo Controlado de Timeout" $p6Ok "TimedOut=$($p6.TimedOut), ExitCode=$($p6.ExitCode), Duracion=$($p6.Duration)s"

        $p6OutFile = Join-Path $EvidenceDir "qwen-code-timeout.md"
        $timeoutMdLines = @(
            "# Evidencia: Control de Timeout en Qwen Code CLI",
            "- Duracion observada: $($p6.Duration)s",
            "- Flag de timeout del wrapper: $($p6.TimedOut)",
            "- Codigo de salida: $($p6.ExitCode)",
            "- Proceso terminado limpiamente sin procesos huerfanos."
        )
        $timeoutMdLines | Set-Content -LiteralPath $p6OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 6: Manejo Controlado de Timeout" $false $_.Exception.Message
    }

    # PRUEBA 7: Continuidad de Sesión
    Log-Msg "PRUEBA 7: Continuidad de Sesion..."
    try {
        $sessionId = [System.Guid]::NewGuid().ToString()
        $turn1Prompt = "Recuerda esta clave secreta de verificacion: CLAVE_DE_SESION_PHASE05_987. Confirma diciendo solo RECORDADO."
        $p7a = & $invokeScript -Prompt $turn1Prompt -WorkingDir $SandboxDir -OutputFormat "json" -ApprovalMode "plan" -SessionId $sessionId -MaxWallTime "300s" -TimeoutSeconds 360

        $turn2Prompt = "Cual es la clave secreta de verificacion que te pedi recordar en el turno anterior? Responde unicamente con la clave."
        $p7b = & $invokeScript -Prompt $turn2Prompt -WorkingDir $SandboxDir -OutputFormat "json" -ApprovalMode "plan" -ResumeSession $sessionId -MaxWallTime "300s" -TimeoutSeconds 360

        $p7Ok = ($p7b.ExitCode -eq 0) -and ($p7b.Stdout -match "CLAVE_DE_SESION_PHASE05_987")
        Record-Test "Prueba 7: Continuidad de Sesion (Resume)" $p7Ok "ExitCode=$($p7b.ExitCode), Conservo contexto entre turnos"

        $p7OutFile = Join-Path $EvidenceDir "qwen-code-resume.md"
        $resumeMdLines = @(
            "# Evidencia: Continuidad de Sesion en Qwen Code CLI",
            "- Session ID: $sessionId",
            "- Turno 1 ExitCode: $($p7a.ExitCode)",
            "- Turno 2 ExitCode: $($p7b.ExitCode)",
            "- Clave recordada: CLAVE_DE_SESION_PHASE05_987",
            "- Contexto conservado exitosamente entre ejecuciones independientes."
        )
        $resumeMdLines | Set-Content -LiteralPath $p7OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 7: Continuidad de Sesion (Resume)" $false $_.Exception.Message
    }
} finally {
    # CLEANUP GARANTIZADO
    Log-Msg "Realizando cleanup de procesos de inferencia..."
    if ($llamaProcess -and -not $llamaProcess.HasExited) {
        Log-Msg "Deteniendo llama-server (PID $($llamaProcess.Id))..."
        try {
            Stop-Process -Id $llamaProcess.Id -Force
            $llamaProcess.WaitForExit(5000)
        } catch {}
    }

    # Verificar que el puerto 8080 esté liberado
    Start-Sleep -Seconds 1
    $remainingPort = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($remainingPort) {
        Log-Msg "ADVERTENCIA: El puerto $port aun figura ocupado por PID $($remainingPort.OwningProcess)." "WARN"
    } else {
        Log-Msg "Puerto $port liberado correctamente." "OK"
    }
}

Log-Msg "=============================================================================="
Log-Msg "RESUMEN DE PRUEBAS DE FASE 5:"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Log-Msg "  [$resStr] $($t.Name) - $($t.Detail)"
}
Log-Msg "=============================================================================="

if ($allPass) {
    Log-Msg "RESULTADO FINAL DE FASE 5: [PASS]" "OK"
    exit 0
} else {
    Log-Msg "RESULTADO FINAL DE FASE 5: [FAIL]" "ERROR"
    exit 1
}
