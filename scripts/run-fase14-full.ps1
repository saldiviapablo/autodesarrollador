# ==============================================================================
# scripts/run-fase14-full.ps1 — Ejecución Integral de Verificación de Fase 14 Real
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

$llamaExe = "C:\AI\llama.cpp\llama-server.exe"
$llamaModel = "C:\Users\Pc\.cache\huggingface\hub\models--ggml-org--Qwen3.6-35B-A3B-GGUF\snapshots\baec3ebee244827cda0f4557eafa8b28f7545fa6\Qwen3.6-35B-A3B-Q4_K_M.gguf"
$healthUri = "http://127.0.0.1:8080/health"

$llamaProcess = $null
$llamaPid = $null

try {
    # 1. Iniciar Chrome dedicado si no está corriendo
    Write-Host "[1/4] Asegurando que Chrome HERMES-CHATGPT esté activo..."
    & "$infraRoot\scripts\start-hermes-chatgpt.ps1"

    # 2. Iniciar llama-server si no está corriendo
    $conn8080 = Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue
    if (-not $conn8080) {
        Write-Host "[2/4] Iniciando llama-server.exe con flags validados..."
        $llamaArgs = @(
            "-m", "`"$llamaModel`"",
            "--alias", "qwen36",
            "--host", "127.0.0.1",
            "--port", "8080",
            "--ctx-size", "65536",
            "--parallel", "1",
            "--cpu-moe",
            "--n-gpu-layers", "99",
            "--flash-attn", "on",
            "--cache-type-k", "q8_0",
            "--cache-type-v", "q8_0",
            "--jinja"
        )

        $pInfo = New-Object System.Diagnostics.ProcessStartInfo
        $pInfo.FileName = $llamaExe
        $pInfo.Arguments = $llamaArgs -join " "
        $pInfo.UseShellExecute = $false
        $pInfo.CreateNoWindow = $true
        $pInfo.RedirectStandardOutput = $true
        $pInfo.RedirectStandardError = $true

        $llamaProcess = [System.Diagnostics.Process]::Start($pInfo)
        $llamaPid = $llamaProcess.Id
        Write-Host "       llama-server lanzado con PID $llamaPid. Esperando health check..."

        $healthOk = $false
        $sw = [System.Diagnostics.Stopwatch]::StartNew()
        while ($sw.Elapsed.TotalSeconds -lt 180) {
            if ($llamaProcess.HasExited) {
                throw "llama-server terminó prematuramente (código $($llamaProcess.ExitCode))"
            }
            try {
                $h = Invoke-RestMethod -Uri $healthUri -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($h.status -eq "ok") {
                    $healthOk = $true
                    break
                }
            } catch { }
            Start-Sleep -Seconds 2
        }

        if (-not $healthOk) {
            throw "Timeout esperando que llama-server responda en $healthUri"
        }
        Write-Host "[OK] llama-server listo en $healthUri ($([Math]::Round($sw.Elapsed.TotalSeconds, 1))s)."
    } else {
        Write-Host "[2/4] llama-server ya está escuchando en puerto 8080."
    }

    # 3. Ejecutar suite de pruebas de Fase 14
    Write-Host "[3/4] Ejecutando suite de pruebas de Fase 14 (Chrome Dedicado + ChatGPT Real)..."
    & "$infraRoot\tests\test-fase14-chatgpt.ps1"

    if ($LASTEXITCODE -ne 0) {
        throw "La suite test-fase14-chatgpt.ps1 falló con código $LASTEXITCODE"
    }
    Write-Host "[OK] Suite test-fase14-chatgpt.ps1 finalizada con PASS."

} finally {
    # 4. Cleanup controlado de procesos
    Write-Host "[4/4] Ejecutando cleanup controlado de procesos..."
    if ($llamaProcess -and -not $llamaProcess.HasExited) {
        Write-Host "       Deteniendo llama-server (PID $llamaPid)..."
        try { Stop-Process -Id $llamaPid -Force -ErrorAction SilentlyContinue } catch {}
        Start-Sleep -Seconds 2
    }

    Write-Host "       Cerrando Chrome HERMES-CHATGPT de forma grácil vía CDP..."
    & "$infraRoot\scripts\close-hermes-chrome.ps1"
}

Write-Host "=============================================================================="
Write-Host "EJECUCION INTEGRAL DE FASE 14 FINALIZADA EXITOSAMENTE."
Write-Host "=============================================================================="
