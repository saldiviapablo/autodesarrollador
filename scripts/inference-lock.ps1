# ==============================================================================
# scripts/inference-lock.ps1 — Mecanismo de Exclusión Mutua de Inferencia
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 7 — Inference Lock / Serialización)
# ==============================================================================
# Implementa serialización determinista cross-process para cumplir la regla
# inviolable: NUNCA DOS INFERENCIAS LOCALES SIMULTÁNEAS (--parallel 1).
# ==============================================================================
[CmdletBinding()]
param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

function Get-InferenceLockConfig {
    param([string]$InfraPath = $infraRoot)
    $yamlPath = Join-Path $InfraPath "config\system.yaml"
    $defaultTimeout = 120
    $defaultStale = 300
    if (Test-Path -LiteralPath $yamlPath) {
        try {
            $pyExe = "C:\Python314\python.exe"
            $code = "import yaml, sys; c=yaml.safe_load(open(sys.argv[1], encoding='utf-8')); print(c.get('inference_lock', {}).get('timeout_seconds', 120), c.get('inference_lock', {}).get('stale_threshold_seconds', 300))"
            $out = & $pyExe -c $code "$yamlPath"
            $parts = $out.Trim().Split(" ")
            if ($parts.Count -ge 2) {
                return @{
                    TimeoutSeconds      = [int]$parts[0]
                    StaleThresholdSeconds = [int]$parts[1]
                }
            }
        } catch { }
    }
    return @{
        TimeoutSeconds      = $defaultTimeout
        StaleThresholdSeconds = $defaultStale
    }
}

function Get-LockRuntimeDirectory {
    param([string]$InfraPath = $infraRoot)
    $runtimeLocks = Join-Path $InfraPath "runtime\locks"
    if (-not (Test-Path -LiteralPath $runtimeLocks)) {
        New-Item -ItemType Directory -Path $runtimeLocks -Force | Out-Null
    }
    return $runtimeLocks
}

function Acquire-InferenceLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [string]$Owner,

        [Parameter(Mandatory = $false)]
        [string]$Purpose = "local-inference",

        [Parameter(Mandatory = $false)]
        [string]$InvocationId = "",

        [Parameter(Mandatory = $false)]
        [int]$TimeoutSeconds = 0,

        [Parameter(Mandatory = $false)]
        [string]$InfraPath = $infraRoot
    )

    if ([string]::IsNullOrEmpty($InvocationId)) {
        $InvocationId = "inv-" + [System.Guid]::NewGuid().ToString("N").Substring(0, 12)
    }

    $lockCfg = Get-InferenceLockConfig -InfraPath $InfraPath
    if ($TimeoutSeconds -le 0) {
        $TimeoutSeconds = $lockCfg.TimeoutSeconds
    }

    $runtimeDir = Get-LockRuntimeDirectory -InfraPath $InfraPath
    $lockFilePath = Join-Path $runtimeDir "inference.lock"
    $ownerFilePath = Join-Path $runtimeDir "inference-owner.json"

    $mutexName = "DesarrolladorAutonomo_InferenceMutex"
    $mutex = [System.Threading.Mutex]::new($false, $mutexName)

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $timeoutMs = $TimeoutSeconds * 1000
    $acquired = $false
    $wasAbandoned = $false
    $errorMessage = ""

    try {
        $acquired = $mutex.WaitOne($timeoutMs)
    } catch [System.Threading.AbandonedMutexException] {
        # Si el proceso anterior que poseía el mutex murió abruptamente sin liberarlo,
        # el SO Windows genera AbandonedMutexException y TRANSFIERE la propiedad
        # del mutex inmediatamente al hilo actual.
        $acquired = $true
        $wasAbandoned = $true
    } catch {
        $errorMessage = $_.Exception.Message
    }

    $sw.Stop()

    if ($acquired) {
        $acquiredAt = (Get-Date).ToString("o")
        $metaObj = [ordered]@{
            owner           = $Owner
            pid             = $PID
            invocation_id   = $InvocationId
            acquired_at     = $acquiredAt
            purpose         = $Purpose
            status          = "ACQUIRED"
            was_abandoned   = $wasAbandoned
            wait_duration_ms= [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        }
        $metaJson = $metaObj | ConvertTo-Json -Depth 5
        try {
            $metaJson | Set-Content -LiteralPath $ownerFilePath -Encoding UTF8 -Force
            (Get-Date).ToString("o") | Set-Content -LiteralPath $lockFilePath -Encoding UTF8 -Force
        } catch { }

        return [PSCustomObject]@{
            Acquired       = $true
            Status         = "ACQUIRED"
            Owner          = $Owner
            Pid            = $PID
            InvocationId   = $InvocationId
            AcquiredAt     = $acquiredAt
            Mutex          = $mutex
            LockFilePath   = $lockFilePath
            OwnerFilePath  = $ownerFilePath
            DurationMs     = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
            WasAbandoned   = $wasAbandoned
            Error          = $null
        }
    } else {
        try { $mutex.Dispose() } catch { }
        return [PSCustomObject]@{
            Acquired       = $false
            Status         = if ([string]::IsNullOrEmpty($errorMessage)) { "LOCK_TIMEOUT" } else { "FAILED" }
            Owner          = $Owner
            Pid            = $PID
            InvocationId   = $InvocationId
            AcquiredAt     = $null
            Mutex          = $null
            LockFilePath   = $lockFilePath
            OwnerFilePath  = $ownerFilePath
            DurationMs     = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
            WasAbandoned   = $false
            Error          = if ([string]::IsNullOrEmpty($errorMessage)) { "Timeout esperando adquisicion del lock tras $($TimeoutSeconds)s" } else { $errorMessage }
        }
    }
}

function Release-InferenceLock {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory = $true)]
        [PSCustomObject]$LockToken
    )

    if (-not $LockToken -or -not $LockToken.Acquired) {
        return $false
    }

    $released = $false
    try {
        # 1. Limpiar o marcar estado liberado en archivos observables
        if ($LockToken.OwnerFilePath -and (Test-Path -LiteralPath $LockToken.OwnerFilePath)) {
            try {
                $releasedMeta = [ordered]@{
                    owner         = $LockToken.Owner
                    pid           = $LockToken.Pid
                    invocation_id = $LockToken.InvocationId
                    released_at   = (Get-Date).ToString("o")
                    status        = "RELEASED"
                }
                $releasedMeta | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $LockToken.OwnerFilePath -Encoding UTF8 -Force
            } catch { }
        }

        if ($LockToken.LockFilePath -and (Test-Path -LiteralPath $LockToken.LockFilePath)) {
            try { Remove-Item -LiteralPath $LockToken.LockFilePath -Force -ErrorAction SilentlyContinue } catch { }
        }

        # 2. Liberar el Mutex del sistema operativo
        if ($LockToken.Mutex) {
            try {
                $LockToken.Mutex.ReleaseMutex()
                $released = $true
            } catch { }
            try {
                $LockToken.Mutex.Dispose()
            } catch { }
        }
    } catch { }

    $LockToken.Acquired = $false
    $LockToken.Status = "RELEASED"
    return $released
}

function Get-InferenceLockStatus {
    [CmdletBinding()]
    param([string]$InfraPath = $infraRoot)

    $runtimeDir = Get-LockRuntimeDirectory -InfraPath $InfraPath
    $ownerFilePath = Join-Path $runtimeDir "inference-owner.json"
    $lockFilePath = Join-Path $runtimeDir "inference.lock"

    if (Test-Path -LiteralPath $ownerFilePath) {
        try {
            $rawJson = Get-Content -LiteralPath $ownerFilePath -Raw -Encoding UTF8
            $meta = $rawJson | ConvertFrom-Json
            $ownerPid = $meta.pid
            $processAlive = $false
            if ($ownerPid) {
                $p = Get-Process -Id $ownerPid -ErrorAction SilentlyContinue
                if ($p) { $processAlive = $true }
            }
            return [PSCustomObject]@{
                Exists       = $true
                Status       = $meta.status
                Owner        = $meta.owner
                Pid          = $ownerPid
                ProcessAlive = $processAlive
                AcquiredAt   = $meta.acquired_at
                Purpose      = $meta.purpose
                InvocationId = $meta.invocation_id
            }
        } catch { }
    }

    return [PSCustomObject]@{
        Exists       = $false
        Status       = "FREE"
        Owner        = $null
        Pid          = $null
        ProcessAlive = $false
        AcquiredAt   = $null
        Purpose      = $null
        InvocationId = $null
    }
}
