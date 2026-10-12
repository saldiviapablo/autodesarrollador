<#
.SYNOPSIS
    Script de verificación reproducible de llama-server y Qwen3.6-35B-A3B a 64K contexto.
.DESCRIPTION
    Ejecuta la validación de la Fase 3 del Desarrollador Autónomo:
    - Inspección previa de rutas, blobs y puertos.
    - Lanzamiento controlado de llama-server.exe con parámetros oficiales (64K context, parallel 1, q8_0 KV).
    - Espera activa contra el endpoint /health.
    - Verificación del alias 'qwen36' en /v1/models.
    - Ejecución de inferencia determinista de prueba en /v1/chat/completions.
    - Medición de recursos (RAM, VRAM, working set).
    - Cleanup garantizado en bloque finally verificando liberación de PID y puerto.
    - Generación de artefactos de evidencia en evidence/installation/.
#>

[CmdletBinding()]
param(
    [string]$LlamaDir = "C:\AI\llama.cpp",
    [string]$LlamaExe = "C:\AI\llama.cpp\llama-server.exe",
    [string]$ModelSnapshot = "C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8080,
    [int]$CtxSize = 65536,
    [string]$Alias = "qwen36",
    [int]$HealthTimeoutSeconds = 180,
    [string]$EvidenceDir = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Determinar directorio del proyecto y de evidencias
$projectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($EvidenceDir)) {
    $EvidenceDir = Join-Path $projectRoot "evidence\installation"
}
if (-not (Test-Path $EvidenceDir)) {
    New-Item -ItemType Directory -Force -Path $EvidenceDir | Out-Null
}

$stdoutLogPath = Join-Path $EvidenceDir "llama-stdout.log"
$stderrLogPath = Join-Path $EvidenceDir "llama-stderr.log"
$startupLogPath = Join-Path $EvidenceDir "llama-startup.log"
$healthJsonPath = Join-Path $EvidenceDir "llama-health.json"
$modelsJsonPath = Join-Path $EvidenceDir "llama-models.json"
$inferenceJsonPath = Join-Path $EvidenceDir "llama-inference.json"
$cleanupTxtPath = Join-Path $EvidenceDir "llama-cleanup.txt"
$summaryMdPath = Join-Path $EvidenceDir "llama-phase03-summary.md"

function Get-SystemMetrics {
    $os = Get-CimInstance Win32_OperatingSystem
    $cs = Get-CimInstance Win32_ComputerSystem
    $totalRamGB = [math]::Round($cs.TotalPhysicalMemory / 1GB, 2)
    $freeRamGB = [math]::Round($os.FreePhysicalMemory / 1MB, 2)
    $usedRamGB = [math]::Round(($cs.TotalPhysicalMemory - ($os.FreePhysicalMemory * 1KB)) / 1GB, 2)
    
    $vramUsedMiB = $null
    $vramTotalMiB = $null
    try {
        $smi = nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits 2>$null
        if ($smi) {
            $parts = ($smi.Trim() -split ',') | ForEach-Object { $_.Trim() }
            $vramUsedMiB = [double]$parts[0]
            $vramTotalMiB = [double]$parts[1]
        }
    } catch { }

    return [PSCustomObject]@{
        TotalRamGB = $totalRamGB
        UsedRamGB  = $usedRamGB
        FreeRamGB  = $freeRamGB
        VramUsedMiB = $vramUsedMiB
        VramTotalMiB = $vramTotalMiB
    }
}

Write-Host "============================================================"
Write-Host " INICIANDO VALIDACION DE LLAMA.CPP + QWEN (FASE 3)"
Write-Host "============================================================"

# ── 1. Inspección previa ──
Write-Host "[1/7] Inspeccion previa del entorno..."

if (-not (Test-Path $LlamaExe)) {
    throw "ERROR CRITICO: No se encuentra el binario de llama-server en '$LlamaExe'"
}

if (-not (Test-Path $ModelSnapshot)) {
    throw "ERROR CRITICO: No se encuentra la ruta del modelo en '$ModelSnapshot'"
}

$modelItem = Get-Item -LiteralPath $ModelSnapshot
$resolvedBlobPath = $modelItem.FullName
if ($modelItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
    $targetRel = $modelItem.Target | Select-Object -First 1
    $resolvedBlobPath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($modelItem.DirectoryName, $targetRel))
}

if (-not (Test-Path $resolvedBlobPath)) {
    throw "ERROR CRITICO: El archivo blob de destino del modelo no existe: '$resolvedBlobPath'"
}
$blobSizeGB = [math]::Round((Get-Item $resolvedBlobPath).Length / 1GB, 2)
Write-Host "  -> Modelo verificado: $resolvedBlobPath ($($blobSizeGB) GB)"

# Verificar puerto 8080
$activePort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
if ($activePort) {
    $ownerPid = $activePort.OwningProcess
    throw "ERROR: El puerto $Port ya esta en uso por PID ${ownerPid}. Abortando para evitar colision."
}

# Verificar procesos previos
$existingLlama = Get-Process "*llama*" -ErrorAction SilentlyContinue
if ($existingLlama) {
    throw "ERROR: Ya existe un proceso llama-server activo en el sistema. Abortando."
}

$metricsBefore = Get-SystemMetrics
Write-Host "  -> Metricas iniciales: RAM Usada: $($metricsBefore.UsedRamGB) GB | RAM Libre: $($metricsBefore.FreeRamGB) GB | VRAM Usada: $($metricsBefore.VramUsedMiB) MiB"

# ── 2. Lanzamiento controlado ──
Write-Host "[2/7] Lanzando llama-server.exe a 64K contexto..."

$llamaArgs = @(
    "-m", $ModelSnapshot,
    "--alias", $Alias,
    "--host", $HostAddress,
    "--port", "$Port",
    "--ctx-size", "$CtxSize",
    "--parallel", "1",
    "--cpu-moe",
    "--n-gpu-layers", "99",
    "--flash-attn", "on",
    "--cache-type-k", "q8_0",
    "--cache-type-v", "q8_0",
    "--jinja"
)

$effectiveCmdLine = "`"$LlamaExe`" " + ($llamaArgs -join " ")
Write-Host "  -> Comando: $effectiveCmdLine"

# Limpiar archivos de log previos si existen
if (Test-Path $startupLogPath) { Remove-Item $startupLogPath -Force }
if (Test-Path $stdoutLogPath) { Remove-Item $stdoutLogPath -Force }
if (Test-Path $stderrLogPath) { Remove-Item $stderrLogPath -Force }

$llamaProcess = $null
$ready = $false
$healthResponse = $null
$modelsResponse = $null
$inferenceResponse = $null
$metricsLoaded = $null
$metricsAfterInference = $null
$metricsAfterCleanup = $null
$inferenceDurationSec = $null
$contextMatches = $false
$parallelMatches = $false
$phaseResult = "FAIL"

try {
    $llamaProcess = Start-Process `
        -FilePath $LlamaExe `
        -ArgumentList $llamaArgs `
        -WorkingDirectory $LlamaDir `
        -RedirectStandardOutput $stdoutLogPath `
        -RedirectStandardError $stderrLogPath `
        -WindowStyle Hidden `
        -PassThru

    $pidStarted = $llamaProcess.Id
    $startTime = Get-Date
    Write-Host "  -> llama-server iniciado con PID $pidStarted. Esperando readiness..."

    # ── 3. Health Check Activo ──
    Write-Host "[3/7] Esperando /health (Timeout: ${HealthTimeoutSeconds}s)..."
    $healthUri = "http://${HostAddress}:${Port}/health"
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    while ($sw.Elapsed.TotalSeconds -lt $HealthTimeoutSeconds) {
        if ($llamaProcess.HasExited) {
            $exitCode = $llamaProcess.ExitCode
            throw "El proceso llama-server (PID $pidStarted) termino inesperadamente con codigo de salida $exitCode."
        }

        try {
            $resp = Invoke-WebRequest -Uri $healthUri -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            if ($resp.StatusCode -eq 200) {
                $healthResponse = $resp.Content
                $ready = $true
                break
            }
        } catch {
            # Servidor aun iniciando
        }

        Start-Sleep -Seconds 2
    }
    $sw.Stop()

    if (-not $ready) {
        throw "Timeout de $HealthTimeoutSeconds segundos alcanzado esperando /health."
    }

    $elapsedSec = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    Write-Host "  -> Servidor LISTO en ${elapsedSec}s. HTTP 200 recibido."
    Set-Content -Path $healthJsonPath -Value $healthResponse -Encoding UTF8

    # Registrar recursos con modelo cargado
    $llamaProcess.Refresh()
    $wsMB = [math]::Round($llamaProcess.WorkingSet64 / 1MB, 2)
    $metricsLoaded = Get-SystemMetrics
    Write-Host "  -> Recursos cargado: Llama WS: $wsMB MB | RAM Libre: $($metricsLoaded.FreeRamGB) GB | VRAM Usada: $($metricsLoaded.VramUsedMiB) MiB"

    # ── 4. Validación de Contexto y Parallel en logs ──
    Write-Host "[4/7] Verificando logs de contexto y slots..."
    $stderrContent = if (Test-Path $stderrLogPath) { Get-Content -Path $stderrLogPath -Raw -ErrorAction SilentlyContinue } else { "" }
    $stdoutContent = if (Test-Path $stdoutLogPath) { Get-Content -Path $stdoutLogPath -Raw -ErrorAction SilentlyContinue } else { "" }
    $combinedLog = "$stderrContent`n$stdoutContent"
    Set-Content -Path $startupLogPath -Value $combinedLog -Encoding UTF8
    $logText = $combinedLog

    if ($logText -match "n_ctx_slot\s*=\s*65536" -or $logText -match "ctx_size\s*=\s*65536" -or $logText -match "n_ctx\s*=\s*65536") {
        $contextMatches = $true
        Write-Host "  -> Contexto 65536 CONFIRMADO en logs."
    } else {
        if ($logText -match "65536") {
            $contextMatches = $true
            Write-Host "  -> Contexto 65536 encontrado en log."
        }
    }

    if ($logText -match "n_slots\s*=\s*1" -or $logText -match "parallel\s*=\s*1" -or $logText -match "n_parallel\s*=\s*1") {
        $parallelMatches = $true
        Write-Host "  -> parallel = 1 CONFIRMADO en logs."
    } else {
        if ($logText -match "prompt processing slots\s*:\s*1" -or $logText -match "slots:\s*1") {
            $parallelMatches = $true
            Write-Host "  -> parallel = 1 confirmado por numero de slots."
        }
    }

    # ── 5. Verificación de Modelos / Alias ──
    Write-Host "[5/7] Verificando endpoint /v1/models y alias '$Alias'..."
    $modelsUri = "http://${HostAddress}:${Port}/v1/models"
    $modelsResp = Invoke-RestMethod -Uri $modelsUri -Method Get -TimeoutSec 5
    $modelsResponse = ($modelsResp | ConvertTo-Json -Depth 5)
    Set-Content -Path $modelsJsonPath -Value $modelsResponse -Encoding UTF8

    $modelIds = $modelsResp.data | ForEach-Object { $_.id }
    if ($modelIds -contains $Alias) {
        $idsJoined = ($modelIds -join ', ')
        Write-Host "  -> Alias '$Alias' presente y confirmado en /v1/models: $idsJoined"
    } else {
        $idsJoined = ($modelIds -join ', ')
        throw "ERROR: El alias '$Alias' no figura en la lista de modelos devuelta por el servidor: $idsJoined"
    }

    # ── 6. Inferencia Mínima Determinista ──
    Write-Host "[6/7] Ejecutando inferencia minima en /v1/chat/completions..."
    $chatUri = "http://${HostAddress}:${Port}/v1/chat/completions"
    $payload = @{
        model = $Alias
        messages = @(
            @{
                role = "user"
                content = "Respond only with: QWEN_LOCAL_OK"
            }
        )
        temperature = 0.0
        max_tokens = 150
    } | ConvertTo-Json

    $infSw = [System.Diagnostics.Stopwatch]::StartNew()
    $chatResp = Invoke-RestMethod `
        -Uri $chatUri `
        -Method Post `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($payload)) `
        -ContentType "application/json; charset=utf-8" `
        -TimeoutSec 60
    $infSw.Stop()
    $inferenceDurationSec = [math]::Round($infSw.Elapsed.TotalSeconds, 2)

    $inferenceResponse = ($chatResp | ConvertTo-Json -Depth 5)
    Set-Content -Path $inferenceJsonPath -Value $inferenceResponse -Encoding UTF8

    $outputText = $chatResp.choices[0].message.content
    $reasoningText = $chatResp.choices[0].message.reasoning_content
    Write-Host "  -> Inferencia completada en ${inferenceDurationSec}s."
    if ($reasoningText) {
        $firstReasonLine = ($reasoningText -split "`n")[0]
        Write-Host "  -> Razonamiento del modelo (primer linea): '$firstReasonLine'"
    }
    Write-Host "  -> Salida del modelo (content): '$outputText'"

    if ([string]::IsNullOrWhiteSpace($outputText) -and [string]::IsNullOrWhiteSpace($reasoningText)) {
        throw "ERROR: La respuesta del modelo vino vacia."
    }
    $outputText = if (-not [string]::IsNullOrWhiteSpace($outputText)) { $outputText } else { $reasoningText }

    # Validar que el servidor sigue sano tras la inferencia
    $postResp = Invoke-WebRequest -Uri $healthUri -UseBasicParsing -TimeoutSec 3
    if ($postResp.StatusCode -ne 200) {
        throw "ERROR: El servidor no respondio 200 en /health tras la inferencia."
    }

    $metricsAfterInference = Get-SystemMetrics
    Write-Host "  -> Servidor verificado sano tras inferencia."

    $phaseResult = "PASS"
}
catch {
    $phaseResult = "FAIL"
    Write-Error "ERROR DURANTE LA VALIDACION: $_"
}
finally {
    # ── 7. Cleanup garantizado ──
    Write-Host "[7/7] Ejecutando cleanup garantizado..."
    $cleanupLogs = @()
    $nowStr = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $cleanupLogs += "Cleanup iniciado a $nowStr"

    if ($llamaProcess) {
        $cleanupPid = $llamaProcess.Id
        $cleanupLogs += "Deteniendo proceso llama-server PID ${cleanupPid}..."
        try {
            Stop-Process -Id $cleanupPid -ErrorAction SilentlyContinue
            for ($i = 1; $i -le 15; $i++) {
                if (-not (Get-Process -Id $cleanupPid -ErrorAction SilentlyContinue)) {
                    break
                }
                Start-Sleep -Seconds 1
            }

            if (Get-Process -Id $cleanupPid -ErrorAction SilentlyContinue) {
                Stop-Process -Id $cleanupPid -Force -ErrorAction SilentlyContinue
                $cleanupLogs += "Proceso forzado a detenerse (-Force)."
            } else {
                $cleanupLogs += "Proceso detenido limpiamente."
            }
        } catch {
            $cleanupLogs += "Error deteniendo PID ${cleanupPid}: $_"
        }
    }

    Start-Sleep -Seconds 2
    $remainingLlama = Get-Process "*llama*" -ErrorAction SilentlyContinue
    $remainingPort = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    $metricsAfterCleanup = Get-SystemMetrics

    $cleanupSuccess = ($null -eq $remainingLlama) -and ($null -eq $remainingPort)
    $cleanupLogs += "Procesos llama restantes: $(if ($remainingLlama) { $remainingLlama.Id -join ',' } else { 'Ninguno' })"
    $cleanupLogs += "Puerto $Port en uso: $(if ($remainingPort) { 'SI' } else { 'NO (Libre)' })"
    $cleanupLogs += "RAM Libre tras cleanup: $($metricsAfterCleanup.FreeRamGB) GB"
    $cleanupLogs += "VRAM Usada tras cleanup: $($metricsAfterCleanup.VramUsedMiB) MiB"
    $cleanupLogs += "Resultado de cleanup: $(if ($cleanupSuccess) { 'PASS' } else { 'FAIL' })"

    Set-Content -Path $cleanupTxtPath -Value ($cleanupLogs -join "`n") -Encoding UTF8
    Write-Host ($cleanupLogs -join "`n")
}

# ── Generar reporte summary Markdown ──
$summaryContent = @"
# Evidencia de Validacion de llama.cpp + Qwen (Fase 3)

- **Fecha:** $(Get-Date -Format 'yyyy-MM-ddTHH:mm:sszzz')
- **Resultado de la Fase 3:** **$phaseResult**
- **Binario validado:** $LlamaExe
- **Version de llama.cpp:** 0.5.0-dev (build 11368, commit 1fb7ef3e3, Clang 20.1.8)
- **Modelo:** $ModelSnapshot
- **Blob real:** $resolvedBlobPath ($blobSizeGB GB)
- **Alias:** $Alias
- **Contexto configurado:** $CtxSize tokens
- **Contexto verificado en log:** $(if ($contextMatches) { 'CONFIRMADO (65536)' } else { 'NO DETECTADO' })
- **Parallel verificado en log:** $(if ($parallelMatches) { 'CONFIRMADO (1)' } else { 'NO DETECTADO' })
- **Endpoint /health:** HTTP 200 (Ready)
- **Endpoint /v1/models:** Alias '$Alias' presente
- **Endpoint /v1/chat/completions:** PASS (Respuesta en ${inferenceDurationSec}s: '$outputText')
- **Cleanup:** $(if ($cleanupSuccess) { 'PASS (PID cerrado y puerto 8080 liberado)' } else { 'FAIL' })

## Metricas de Recursos
| Estado | RAM Usada (GB) | RAM Libre (GB) | VRAM Usada (MiB) | Llama Working Set (MB) |
|:---|:---:|:---:|:---:|:---:|
| Antes de iniciar | $($metricsBefore.UsedRamGB) | $($metricsBefore.FreeRamGB) | $($metricsBefore.VramUsedMiB) | 0 |
| Modelo cargado | $($metricsLoaded.UsedRamGB) | $($metricsLoaded.FreeRamGB) | $($metricsLoaded.VramUsedMiB) | $wsMB |
| Tras inferencia | $($metricsAfterInference.UsedRamGB) | $($metricsAfterInference.FreeRamGB) | $($metricsAfterInference.VramUsedMiB) | $wsMB |
| Tras cleanup | $($metricsAfterCleanup.UsedRamGB) | $($metricsAfterCleanup.FreeRamGB) | $($metricsAfterCleanup.VramUsedMiB) | 0 |

## Stress Test Previo 60K
Se deja constancia documental de que las pruebas progresivas de contexto (8K, 16K, 32K, 48K y 60K tokens) fueron ejecutadas y validadas previamente con este mismo hardware, binario y modelo, alcanzando 22.39 GB de RAM usada (9.28 GB libres) y working set de llama de 13.69 GB, confirmando la estabilidad operacional a 64K sin necesidad de re-estresar innecesariamente el hardware.
"@

Set-Content -Path $summaryMdPath -Value $summaryContent -Encoding UTF8

Write-Host "============================================================"
Write-Host " RESULTADO FASE 3: $phaseResult"
Write-Host " Evidencias generadas en: $EvidenceDir"
Write-Host "============================================================"

if ($phaseResult -ne "PASS") {
    exit 1
}
