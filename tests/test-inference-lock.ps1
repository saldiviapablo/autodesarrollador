# ==============================================================================
# tests/test-inference-lock.ps1 — Suite de Verificación de Inference Lock (Fase 7)
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 7 — Inference Lock / Serialización)
# ==============================================================================
[CmdletBinding()]
param(
    [string]$EvidenceDir = "",
    [string]$LogFile = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $EvidenceDir) { $EvidenceDir = Join-Path $infraRoot "evidence\integration" }
if (-not $LogFile) {
    $timestamp = (Get-Date).ToString("yyyyMMdd-HHmmss")
    $LogFile = Join-Path $infraRoot "logs\phase-07-inference-lock-$timestamp.log"
}

$logParent = Split-Path -Parent $LogFile
if (-not (Test-Path -LiteralPath $logParent)) { New-Item -ItemType Directory -Path $logParent -Force | Out-Null }
if (-not (Test-Path -LiteralPath $EvidenceDir)) { New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null }

$runtimeDir = Join-Path $infraRoot "runtime"
if (-not (Test-Path -LiteralPath $runtimeDir)) { New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null }

. (Join-Path $infraRoot "scripts\inference-lock.ps1")

function Log-Msg {
    param([string]$Msg, [string]$Level = "INFO")
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss.fff")
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
Log-Msg "INICIANDO VERIFICACION DE INFERENCE LOCK / SERIALIZACION (FASE 7)"
Log-Msg "EvidenceDir: $EvidenceDir"
Log-Msg "LogFile:     $LogFile"
Log-Msg "=============================================================================="

$lockScriptPath = Join-Path $infraRoot "scripts\inference-lock.ps1"

# ------------------------------------------------------------------------------
# TEST 1: Exclusión Mutua Concurrente (Proceso A y Proceso B)
# ------------------------------------------------------------------------------
Log-Msg "[1/4] Test 1: Exclusion Mutua Concurrente entre Procesos Windows..."
$t1Evidence = [System.Collections.Generic.List[string]]::new()
$t1Evidence.Add("# Evidencia: Exclusión Mutua Concurrente (Inference Lock)")
$t1Evidence.Add("")

$fileA = Join-Path $runtimeDir "test_proc_a.json"
$fileB = Join-Path $runtimeDir "test_proc_b.json"
$workerPs1A = Join-Path $runtimeDir "worker_a.ps1"
$workerPs1B = Join-Path $runtimeDir "worker_b.ps1"

if (Test-Path -LiteralPath $fileA) { Remove-Item -LiteralPath $fileA -Force }
if (Test-Path -LiteralPath $fileB) { Remove-Item -LiteralPath $fileB -Force }

# Worker script A: Toma lock por 2.5 segundos
@"
`$ErrorActionPreference = 'Stop'
. '$lockScriptPath'
`$res = Acquire-InferenceLock -Owner 'ProcessA' -Purpose 'test-mutual-exclusion' -TimeoutSeconds 15
`$didAcquire = `$res.Acquired
`$start = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
Start-Sleep -Milliseconds 2500
`$end = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
`$null = Release-InferenceLock -LockToken `$res
@{
    Owner = 'ProcessA'
    Acquired = `$didAcquire
    StartTimeMs = `$start
    EndTimeMs = `$end
} | ConvertTo-Json | Set-Content -LiteralPath '$fileA' -Encoding UTF8
"@ | Set-Content -LiteralPath $workerPs1A -Encoding UTF8

# Worker script B: Espera hasta 15 segundos para tomar el lock, duerme 1 segundo y libera
@"
`$ErrorActionPreference = 'Stop'
. '$lockScriptPath'
`$res = Acquire-InferenceLock -Owner 'ProcessB' -Purpose 'test-mutual-exclusion' -TimeoutSeconds 15
`$didAcquire = `$res.Acquired
`$start = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
Start-Sleep -Milliseconds 1000
`$end = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
`$null = Release-InferenceLock -LockToken `$res
@{
    Owner = 'ProcessB'
    Acquired = `$didAcquire
    StartTimeMs = `$start
    EndTimeMs = `$end
} | ConvertTo-Json | Set-Content -LiteralPath '$fileB' -Encoding UTF8
"@ | Set-Content -LiteralPath $workerPs1B -Encoding UTF8

$procA = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command & '$workerPs1A'" -PassThru
Start-Sleep -Milliseconds 500
$procB = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command & '$workerPs1B'" -PassThru

$procA.WaitForExit(20000) | Out-Null
$procB.WaitForExit(20000) | Out-Null

$dataA = if (Test-Path -LiteralPath $fileA) { Get-Content -LiteralPath $fileA -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }
$dataB = if (Test-Path -LiteralPath $fileB) { Get-Content -LiteralPath $fileB -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }

$t1Pass = $false
$t1Detail = ""
if ($dataA -and $dataB -and $dataA.Acquired -and $dataB.Acquired) {
    $aEnd = $dataA.EndTimeMs
    $bStart = $dataB.StartTimeMs
    if ($bStart -ge $aEnd) {
        $t1Pass = $true
        $gap = $bStart - $aEnd
        $t1Detail = "A libero a los $aEnd ms, B adquirio a los $bStart ms (Gap: $gap ms). Cero solapamiento."
    } else {
        $t1Detail = "ERROR: Solapamiento detectado! A fin: $aEnd, B inicio: $bStart"
    }
} else {
    $t1Detail = "ERROR: Uno o ambos procesos fallaron en adquirir o registrar datos. (A: $($dataA -ne $null), B: $($dataB -ne $null))"
}

Record-Test "Test 1: Exclusion Mutua Concurrente" $t1Pass $t1Detail

$t1Evidence.Add("- **Proceso A:** Adquirido=$($dataA.Acquired), Fin=$($dataA.EndTimeMs) ms")
$t1Evidence.Add("- **Proceso B:** Adquirido=$($dataB.Acquired), Inicio=$($dataB.StartTimeMs) ms")
$t1Evidence.Add("- **Resultado:** $(if ($t1Pass) { 'PASS' } else { 'FAIL' }) ($t1Detail)")
$t1Evidence | Set-Content -LiteralPath (Join-Path $EvidenceDir "inference-lock.md") -Encoding UTF8

# ------------------------------------------------------------------------------
# TEST 2: Crash Recovery (Proceso que muere abruptamente con lock tomado)
# ------------------------------------------------------------------------------
Log-Msg "[2/4] Test 2: Crash Recovery tras terminacion abrupta de proceso..."
$t2Evidence = [System.Collections.Generic.List[string]]::new()
$t2Evidence.Add("# Evidencia: Recuperación de Crash en Inference Lock")
$t2Evidence.Add("")

$fileCrashA = Join-Path $runtimeDir "test_proc_crash_a.json"
$workerPs1Crash = Join-Path $runtimeDir "worker_crash.ps1"
if (Test-Path -LiteralPath $fileCrashA) { Remove-Item -LiteralPath $fileCrashA -Force }

@"
`$ErrorActionPreference = 'Stop'
. '$lockScriptPath'
`$res = Acquire-InferenceLock -Owner 'ProcessCrashA' -Purpose 'test-crash-recovery' -TimeoutSeconds 10
@{
    Owner = 'ProcessCrashA'
    Pid = `$PID
    Acquired = `$res.Acquired
} | ConvertTo-Json | Set-Content -LiteralPath '$fileCrashA' -Encoding UTF8
Start-Sleep -Milliseconds 500
Stop-Process -Id `$PID -Force
"@ | Set-Content -LiteralPath $workerPs1Crash -Encoding UTF8

$procCrashA = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command & '$workerPs1Crash'" -PassThru
$procCrashA.WaitForExit(10000) | Out-Null

# Proceso B intenta adquirir el lock inmediatamente
$lockTokenB = Acquire-InferenceLock -Owner 'ProcessSurvivorB' -Purpose 'verify-crash-recovery' -TimeoutSeconds 5
$t2Pass = ($lockTokenB.Acquired -eq $true)
$t2Detail = "Survivor adquirio lock correctamente (WasAbandoned=$($lockTokenB.WasAbandoned), Duracion=$($lockTokenB.DurationMs) ms)"

Record-Test "Test 2: Crash Recovery sin intervencion manual" $t2Pass $t2Detail

$t2Evidence.Add("- **Proceso Muerto:** PID $($procCrashA.Id) finalizado abruptamente mientras sostenía el lock.")
$t2Evidence.Add("- **Proceso Sobreviviente:** Adquirió exitosamente el lock en $($lockTokenB.DurationMs) ms.")
$t2Evidence.Add("- **WasAbandoned Flag:** $($lockTokenB.WasAbandoned)")
$t2Evidence.Add("- **Resultado:** $(if ($t2Pass) { 'PASS' } else { 'FAIL' })")
$t2Evidence | Set-Content -LiteralPath (Join-Path $EvidenceDir "inference-lock-crash.md") -Encoding UTF8

Release-InferenceLock -LockToken $lockTokenB | Out-Null

# ------------------------------------------------------------------------------
# TEST 3: Lock Timeout (Espera acotada)
# ------------------------------------------------------------------------------
Log-Msg "[3/4] Test 3: Manejo de Lock Timeout..."
$holderToken = Acquire-InferenceLock -Owner 'LockHolder' -Purpose 'test-timeout-holder' -TimeoutSeconds 10

$fileTimeout = Join-Path $runtimeDir "test_proc_timeout.json"
$workerPs1Timeout = Join-Path $runtimeDir "worker_timeout.ps1"
if (Test-Path -LiteralPath $fileTimeout) { Remove-Item -LiteralPath $fileTimeout -Force }

@"
`$ErrorActionPreference = 'Stop'
. '$lockScriptPath'
`$sw = [System.Diagnostics.Stopwatch]::StartNew()
`$res = Acquire-InferenceLock -Owner 'TimeoutRequester' -Purpose 'test-timeout' -TimeoutSeconds 2
`$sw.Stop()
@{
    Acquired = `$res.Acquired
    Status = `$res.Status
    DurationMs = `$sw.Elapsed.TotalMilliseconds
    Error = `$res.Error
} | ConvertTo-Json | Set-Content -LiteralPath '$fileTimeout' -Encoding UTF8
"@ | Set-Content -LiteralPath $workerPs1Timeout -Encoding UTF8

$procTimeout = Start-Process powershell.exe -ArgumentList "-NoProfile -ExecutionPolicy Bypass -Command & '$workerPs1Timeout'" -PassThru
$procTimeout.WaitForExit(10000) | Out-Null

$dataTimeout = if (Test-Path -LiteralPath $fileTimeout) { Get-Content -LiteralPath $fileTimeout -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }

Release-InferenceLock -LockToken $holderToken | Out-Null

$t3Pass = ($dataTimeout -and ($dataTimeout.Acquired -eq $false) -and ($dataTimeout.Status -eq "LOCK_TIMEOUT"))
$t3Detail = "Status=$($dataTimeout.Status), Duracion=$([Math]::Round($dataTimeout.DurationMs, 2)) ms"
Record-Test "Test 3: Lock Timeout Controlado" $t3Pass $t3Detail

# ------------------------------------------------------------------------------
# TEST 4: Metadata Observable
# ------------------------------------------------------------------------------
Log-Msg "[4/4] Test 4: Verificacion de Metadata Observable en runtime/locks/..."
$obsToken = Acquire-InferenceLock -Owner 'ObservableInspector' -Purpose 'test-metadata' -TimeoutSeconds 5
$ownerJsonPath = Join-Path $infraRoot "runtime\locks\inference-owner.json"
$lockFileExists = Test-Path -LiteralPath (Join-Path $infraRoot "runtime\locks\inference.lock")
$ownerMeta = if (Test-Path -LiteralPath $ownerJsonPath) { Get-Content -LiteralPath $ownerJsonPath -Raw -Encoding UTF8 | ConvertFrom-Json } else { $null }

$t4Pass = ($lockFileExists -and $ownerMeta -and ($ownerMeta.owner -eq 'ObservableInspector') -and ($ownerMeta.status -eq 'ACQUIRED'))
$t4Detail = "LockFile=$lockFileExists, Owner=$($ownerMeta.owner), Status=$($ownerMeta.status)"
Record-Test "Test 4: Metadata Observable Valida" $t4Pass $t4Detail

Release-InferenceLock -LockToken $obsToken | Out-Null

# Cleanup de archivos temporales de pruebas
@($fileA, $fileB, $workerPs1A, $workerPs1B, $fileCrashA, $workerPs1Crash, $fileTimeout, $workerPs1Timeout) | ForEach-Object {
    if (Test-Path -LiteralPath $_) { Remove-Item -LiteralPath $_ -Force -ErrorAction SilentlyContinue }
}

Log-Msg "=============================================================================="
Log-Msg "RESUMEN DE PRUEBAS DE FASE 7 (INFERENCE LOCK):"
foreach ($t in $testResults) {
    $resStr = if ($t.Pass) { "PASS" } else { "FAIL" }
    Log-Msg "  [$resStr] $($t.Name) - $($t.Detail)"
}
Log-Msg "=============================================================================="

if ($allPass) {
    Log-Msg "RESULTADO FINAL DE FASE 7: [PASS]" "OK"
    exit 0
} else {
    Log-Msg "RESULTADO FINAL DE FASE 7: [FAIL]" "ERROR"
    exit 1
}
