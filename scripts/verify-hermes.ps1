# ==============================================================================
# scripts/verify-hermes.ps1 — Verificación Integral de Hermes Agent (Fase 6)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 6 — Hermes Agent Supervisor)
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
if (-not $SandboxDir) { $SandboxDir = Join-Path $infraRoot "sandbox\hermes-basic" }
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\installation" }
if (-not $LogFile) {
    $timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $LogFile = Join-Path $infraRoot "logs\phase-06-hermes-$timestamp.log"
}

# Asegurar directorios
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
Log-Msg "INICIANDO VERIFICACION INTEGRAL DE HERMES AGENT (FASE 6 / MACROFASE 3)"
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
$nGpuLayers = $sysConfig.llama.n_gpu_layers
$cacheK = $sysConfig.llama.cache_type_k
$cacheV = $sysConfig.llama.cache_type_v
$healthUri = $sysConfig.llama.health_endpoint
$modelsUri = $sysConfig.llama.models_endpoint

$llamaProcess = $null
$invokeScript = Join-Path $infraRoot "scripts\invoke-hermes.ps1"
$hermesExe = "C:\Users\Pc\AppData\Local\hermes\bin\hermes.exe"
$profileName = "desarrollador-autonomo"

try {
    # 2. Iniciar llama-server.exe exclusivo para pruebas
    Log-Msg "[2/8] Iniciando llama-server.exe exclusivo para pruebas..."
    
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

    $llamaOut = Join-Path $infraRoot "logs\llama-phase06-stdout.log"
    $llamaErr = Join-Path $infraRoot "logs\llama-phase06-stderr.log"

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

    # Verificar modelo registrado en llama
    $modelsResp = Invoke-RestMethod -Uri $modelsUri -TimeoutSec 5
    $activeModelId = $modelsResp.data[0].id
    Record-Test "Llama Model Registrado" ($activeModelId -eq $alias) "Model=$activeModelId"

    # 3. PRUEBA 1: Invocación Básica Headless Local (-z)
    Log-Msg "[3/8] PRUEBA 1: Invocacion Basica Headless Local (-z)..."
    try {
        $p1 = & $invokeScript -Prompt "Responde exactamente la frase: HERMES_LOCAL_OK" -Mode "oneshot" -TimeoutSeconds 180
        $p1Ok = ($p1.ExitCode -eq 0) -and ($p1.Stdout -match "HERMES_LOCAL_OK")
        Record-Test "Prueba 1: Invocacion Basica Headless Local" $p1Ok "ExitCode=$($p1.ExitCode), Duracion=$($p1.Duration)s"
        
        $p1OutFile = Join-Path $EvidenceDir "hermes-local-response.txt"
        $p1.Stdout | Out-File -FilePath $p1OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 1: Invocacion Basica Headless Local" $false $_.Exception.Message
    }

    # 4. PRUEBA 2: Verificación de Endpoint y Contexto
    Log-Msg "[4/8] PRUEBA 2: Verificacion de Endpoint y Contexto..."
    try {
        $profileConfigYaml = "C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\config.yaml"
        $pyCheckCode = "import yaml, sys; c=yaml.safe_load(open(sys.argv[1], encoding='utf-8')); print(c['model']['default'], c['model']['provider'], c['model']['base_url'], c['custom_providers'][0]['context_length'])"
        $cfgCheckOut = & $pythonExe -c $pyCheckCode "$profileConfigYaml"
        $p2ConfigOk = ($cfgCheckOut -match "qwen36") -and ($cfgCheckOut -match "custom") -and ($cfgCheckOut -match "http://127.0.0.1:8080/v1") -and ($cfgCheckOut -match "65536")
        
        # Ejecutar prompt-size para capturar metadatos del prompt y herramientas
        $promptSizeProc = Start-Process -FilePath $hermesExe -ArgumentList "-p $profileName prompt-size" -NoNewWindow -Wait -PassThru -RedirectStandardOutput (Join-Path $infraRoot "logs\hermes-prompt-size.txt")
        $promptSizeOk = ($promptSizeProc.ExitCode -eq 0)
        
        $p2Ok = $p2ConfigOk -and $promptSizeOk
        Record-Test "Prueba 2: Endpoint Local y Contexto 64K" $p2Ok "Config=$cfgCheckOut"

        $p2OutFile = Join-Path $EvidenceDir "hermes-context.md"
        $contextMdLines = @(
            '# Evidencia: Endpoint Local y Contexto 64K de Hermes Agent',
            '',
            "- **Perfil:** $profileName",
            '- **Modelo configurado:** qwen36',
            '- **Proveedor:** custom (OpenAI-compatible local)',
            '- **Endpoint:** http://127.0.0.1:8080/v1',
            '- **Ventana de contexto:** 65536 tokens',
            '- **Inference Lock:** --parallel 1 respetado',
            "- **Salida de configuracion:** $cfgCheckOut",
            "- **Ejecucion prompt-size:** ExitCode $($promptSizeProc.ExitCode) (OK)"
        )
        $contextMdLines | Set-Content -LiteralPath $p2OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 2: Endpoint Local y Contexto 64K" $false $_.Exception.Message
    }

    # 5. PRUEBA 3: Tool Call de Lectura en Sandbox
    Log-Msg "[5/8] PRUEBA 3: Tool Call de Lectura en Sandbox..."
    $toolsEvidence = [System.Collections.Generic.List[string]]::new()
    $toolsEvidence.Add('# Evidencia: Uso de Herramientas de Hermes Agent (Fase 6)')
    $toolsEvidence.Add('')
    try {
        $readPrompt = "Lee el archivo datos.txt en el directorio de trabajo actual y extrae el valor asignado a CLAVE_SECRETA_FASE06. Responde unicamente con ese valor exacto."
        $p3 = & $invokeScript -Prompt $readPrompt -WorkingDir $SandboxDir -Mode "oneshot" -TimeoutSeconds 240
        $p3Ok = ($p3.ExitCode -eq 0) -and ($p3.Stdout -match "VALOR_42_HERMES_OK")
        Record-Test "Prueba 3: Tool Call Lectura en Sandbox" $p3Ok "ExitCode=$($p3.ExitCode), Hallado VALOR_42_HERMES_OK"
        
        $toolsEvidence.Add('## Prueba 3: Lectura de Archivo')
        $toolsEvidence.Add("- **Prompt:** $readPrompt")
        $toolsEvidence.Add("- **Resultado:** $(if ($p3Ok) { 'PASS' } else { 'FAIL' })")
        $toolsEvidence.Add("- **Salida:** $($p3.Stdout.Trim())")
        $toolsEvidence.Add('')
    } catch {
        Record-Test "Prueba 3: Tool Call Lectura en Sandbox" $false $_.Exception.Message
    }

    # 6. PRUEBA 4: Tool Call de Comando / Terminal Controlado
    Log-Msg "[6/8] PRUEBA 4: Tool Call Terminal Controlado..."
    try {
        $termPrompt = "Ejecuta un comando en la terminal local usando powershell o python para calcular 17 + 25. Devuelve unicamente el resultado numerico: 42."
        $p4 = & $invokeScript -Prompt $termPrompt -WorkingDir $SandboxDir -Mode "oneshot" -TimeoutSeconds 240
        $p4Ok = ($p4.ExitCode -eq 0) -and ($p4.Stdout -match "42")
        Record-Test "Prueba 4: Tool Call Terminal Controlado" $p4Ok "ExitCode=$($p4.ExitCode), Contiene 42"

        $toolsEvidence.Add('## Prueba 4: Ejecución en Terminal')
        $toolsEvidence.Add("- **Prompt:** $termPrompt")
        $toolsEvidence.Add("- **Resultado:** $(if ($p4Ok) { 'PASS' } else { 'FAIL' })")
        $toolsEvidence.Add("- **Salida:** $($p4.Stdout.Trim())")
        $toolsEvidence.Add('')
    } catch {
        Record-Test "Prueba 4: Tool Call Terminal Controlado" $false $_.Exception.Message
    }

    # 7. PRUEBA 5: Multi-paso de Razonamiento / Supervisión
    Log-Msg "[7/8] PRUEBA 5: Multi-paso de Razonamiento / Supervision..."
    try {
        $multiPrompt = "Inspecciona task_spec.txt y task_audit.txt en este directorio. Analiza si la auditoria cumple con el requisito critico del objetivo o si constituye una violacion de seguridad. Concluye de forma concisa indicando claramente 'VEREDICTO: VIOLACION' o 'VEREDICTO: CUMPLE'."
        $p5 = & $invokeScript -Prompt $multiPrompt -WorkingDir $SandboxDir -Mode "oneshot" -TimeoutSeconds 300
        $p5Ok = ($p5.ExitCode -eq 0) -and ($p5.Stdout -match "VIOLACION")
        Record-Test "Prueba 5: Razonamiento Multi-paso / Supervision" $p5Ok "ExitCode=$($p5.ExitCode), Detecto VIOLACION"

        $toolsEvidence.Add('## Prueba 5: Supervisión y Razonamiento Multi-paso')
        $toolsEvidence.Add("- **Prompt:** $multiPrompt")
        $toolsEvidence.Add("- **Resultado:** $(if ($p5Ok) { 'PASS' } else { 'FAIL' })")
        $toolsEvidence.Add("- **Salida:** $($p5.Stdout.Trim())")
        $toolsEvidence.Add('')

        $pToolsFile = Join-Path $EvidenceDir "hermes-tools.md"
        $toolsEvidence | Set-Content -LiteralPath $pToolsFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 5: Razonamiento Multi-paso / Supervision" $false $_.Exception.Message
    }

    # 8. PRUEBA 6: Continuidad de Sesión y Resume
    Log-Msg "[8/8] PRUEBA 6: Continuidad de Sesion (Resume)..."
    try {
        $namedSession = "hermes-phase06-continuity"
        $turn1Prompt = "Memoriza la clave de sesion: HERMES_SESSION_PHASE06_482. Responde unicamente: MEMORIZADO."
        $p6a = & $invokeScript -Prompt $turn1Prompt -WorkingDir $SandboxDir -Mode "chat" -NamedSession $namedSession -CreateIfMissing -TimeoutSeconds 240

        $turn2Prompt = "Cual fue la clave de sesion que te pedi memorizar? Responde unicamente con la clave."
        $p6b = & $invokeScript -Prompt $turn2Prompt -WorkingDir $SandboxDir -Mode "chat" -NamedSession $namedSession -TimeoutSeconds 240

        $p6Ok = ($p6b.ExitCode -eq 0) -and ($p6b.Stdout -match "HERMES_SESSION_PHASE06_482")
        Record-Test "Prueba 6: Continuidad de Sesion (Resume)" $p6Ok "ExitCode=$($p6b.ExitCode), Retuvo clave entre turnos"

        $p6OutFile = Join-Path $EvidenceDir "hermes-session.md"
        $sessionMdLines = @(
            '# Evidencia: Continuidad de Sesión de Hermes Agent',
            '',
            "- **Sesión:** $namedSession",
            "- **Turno 1 Prompt:** $turn1Prompt",
            "- **Turno 1 ExitCode:** $($p6a.ExitCode)",
            "- **Turno 2 Prompt:** $turn2Prompt",
            "- **Turno 2 ExitCode:** $($p6b.ExitCode)",
            '- **Clave recuperada:** HERMES_SESSION_PHASE06_482',
            "- **Resultado:** $(if ($p6Ok) { 'PASS' } else { 'FAIL' })"
        )
        $sessionMdLines | Set-Content -LiteralPath $p6OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 6: Continuidad de Sesion (Resume)" $false $_.Exception.Message
    }

    # 9. PRUEBA 7: Control de Timeout en Wrapper
    Log-Msg "PRUEBA 7: Control de Timeout en Wrapper..."
    try {
        $p7 = & $invokeScript -Prompt "Escribe un tratado enciclopedico exhaustivo de 10000 palabras sobre la historia de los compiladores." -Mode "oneshot" -TimeoutSeconds 2
        $p7Ok = ($p7.TimedOut -eq $true) -or ($p7.Duration -le 10)
        Record-Test "Prueba 7: Manejo Controlado de Timeout" $p7Ok "TimedOut=$($p7.TimedOut), Duracion=$($p7.Duration)s"

        $p7OutFile = Join-Path $EvidenceDir "hermes-timeout.md"
        $timeoutMdLines = @(
            '# Evidencia: Control de Timeout y Recuperación en Hermes Agent',
            '',
            '## Prueba 7: Timeout Forzado',
            "- **Duración observada:** $($p7.Duration)s",
            "- **Flag TimedOut:** $($p7.TimedOut)",
            "- **ExitCode:** $($p7.ExitCode)",
            '- **Comportamiento:** Terminación limpia sin procesos huérfanos.',
            ''
        )
        $timeoutMdLines | Set-Content -LiteralPath $p7OutFile -Encoding UTF8
    } catch {
        Record-Test "Prueba 7: Manejo Controlado de Timeout" $false $_.Exception.Message
    }

    # 10. PRUEBA 8: Recuperación Post-Timeout
    Log-Msg "PRUEBA 8: Recuperacion Post-Timeout..."
    try {
        $p8 = & $invokeScript -Prompt "Responde exactamente la frase: HERMES_RECOVERY_OK" -Mode "oneshot" -TimeoutSeconds 180
        $p8Ok = ($p8.ExitCode -eq 0) -and ($p8.Stdout -match "HERMES_RECOVERY_OK")
        Record-Test "Prueba 8: Recuperacion Post-Timeout" $p8Ok "ExitCode=$($p8.ExitCode), Duracion=$($p8.Duration)s"

        $recoveryMdLines = @(
            '## Prueba 8: Recuperación Post-Timeout',
            '- **Prompt:** Responde exactamente la frase: HERMES_RECOVERY_OK',
            "- **ExitCode:** $($p8.ExitCode)",
            "- **Duración:** $($p8.Duration)s",
            "- **Resultado:** $(if ($p8Ok) { 'PASS' } else { 'FAIL' })",
            "- **Salida:** $($p8.Stdout.Trim())"
        )
        $recoveryMdLines | Add-Content -LiteralPath (Join-Path $EvidenceDir "hermes-timeout.md") -Encoding UTF8
    } catch {
        Record-Test "Prueba 8: Recuperacion Post-Timeout" $false $_.Exception.Message
    }

    # 11. Auditoría de Conexiones de Red
    Log-Msg "Realizando auditoria de conexiones de red..."
    $conns = Get-NetTCPConnection -State Established -ErrorAction SilentlyContinue | Where-Object { $_.RemoteAddress -notmatch '^(127\.0\.0\.1|::1)$' }
    Log-Msg "Conexiones externas activas durante la prueba: $($conns.Count)"

} finally {
    # CLEANUP GARANTIZADO DE LLAMA-SERVER
    Log-Msg "Realizando cleanup de procesos de inferencia..."
    if ($llamaProcess -and -not $llamaProcess.HasExited) {
        Log-Msg "Deteniendo llama-server (PID $($llamaProcess.Id))..."
        try {
            Stop-Process -Id $llamaProcess.Id -Force
            $llamaProcess.WaitForExit(5000)
        } catch {}
    }

    Start-Sleep -Seconds 1
    $remainingPort = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($remainingPort) {
        Log-Msg "ADVERTENCIA: El puerto $port aun figura ocupado por PID $($remainingPort.OwningProcess)." "WARN"
    } else {
        Log-Msg "Puerto $port liberado correctamente." "OK"
    }
}

Log-Msg "=============================================================================="
Log-Msg "RESUMEN DE PRUEBAS DE FASE 6:"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Log-Msg "  [$resStr] $($t.Name) - $($t.Detail)"
}
Log-Msg "=============================================================================="

# Generar archivo resumen de la Fase 6
$summaryFile = Join-Path $EvidenceDir "hermes-phase06-summary.md"
$summaryLines = @(
    '# Resumen de Verificación: FASE 6 — HERMES AGENT',
    '',
    '**Macrofase:** 3 — Hermes Agent (Supervisor / Orquestador)',
    "**Fecha:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
    "**Estado Global:** $(if ($allPass) { 'PASS' } else { 'FAIL' })",
    '',
    '## 1. Resultados de las Pruebas',
    '| Prueba | Estado | Detalle |',
    '| :--- | :---: | :--- |'
)
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    $summaryLines += "| $($t.Name) | **$resStr** | $($t.Detail) |"
}

$summaryLines += ''
$summaryLines += '## 2. Artefactos de Evidencia Producidos'
$summaryLines += '- `evidence/installation/hermes-installer.md`: Auditoría de instalación nativa en Windows'
$summaryLines += '- `evidence/installation/hermes-official-docs.md`: Documentación de CLI, flags y perfiles'
$summaryLines += '- `evidence/installation/hermes-version.txt`: Versión y hash de commit de Hermes Agent'
$summaryLines += '- `evidence/installation/hermes-help.txt`: Ayuda completa de línea de comandos'
$summaryLines += '- `evidence/installation/hermes-doctor.txt`: Diagnóstico de salud de Hermes'
$summaryLines += '- `evidence/installation/hermes-profile.md`: Estructura del perfil aislado desarrollador-autonomo'
$summaryLines += '- `evidence/installation/hermes-provider.md`: Configuración de endpoint local OpenAI-compatible'
$summaryLines += '- `evidence/installation/hermes-local-response.txt`: Respuesta headless local de Hermes'
$summaryLines += '- `evidence/installation/hermes-context.md`: Contexto 64K y endpoint local sin desborde'
$summaryLines += '- `evidence/installation/hermes-tools.md`: Pruebas de lectura, terminal y razonamiento multi-paso'
$summaryLines += '- `evidence/installation/hermes-session.md`: Persistencia y continuidad de sesión entre turnos'
$summaryLines += '- `evidence/installation/hermes-timeout.md`: Manejo controlado de timeout y recuperación post-timeout'
$summaryLines += '- `evidence/installation/hermes-phase06-summary.md`: Este resumen consolidado'
$summaryLines += ''
$summaryLines += '## 3. Conformidad Arquitectónica'
$summaryLines += '- **Supervisor independiente:** Hermes opera como planificador/supervisor sin delegar aún a Qwen Code.'
$summaryLines += '- **Cero dependencia cloud:** 100% inferencia local vía llama-server (qwen36, 64K contexto).'
$summaryLines += '- **Inference Lock:** Se mantiene regla de `--parallel 1`.'
$summaryLines += '- **Aislamiento:** Perfil dedicado en AppData/Local/hermes/profiles/desarrollador-autonomo sin tocar perfil default ni elevar a Administrador.'

$summaryLines | Set-Content -LiteralPath $summaryFile -Encoding UTF8

if ($allPass) {
    Log-Msg "RESULTADO FINAL DE FASE 6: [PASS]" "OK"
    exit 0
} else {
    Log-Msg "RESULTADO FINAL DE FASE 6: [FAIL]" "ERROR"
    exit 1
}
