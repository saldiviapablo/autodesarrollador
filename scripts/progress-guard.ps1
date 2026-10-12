# ==============================================================================
# scripts/progress-guard.ps1 — Motor Anti-Loop, Timeouts y Control de Progreso
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Macrofase 6 — Fase 16: Anti-Loop / Timeouts / Control de Progreso)
# ==============================================================================
# Implementa el control determinista de bucles, la escalera de escalamiento,
# firmas de error normalizadas, fingerprints de avance real y ejecución con timeout
# con garantía de ownership de procesos y terminación de subárboles (no huérfanos).
# ==============================================================================
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

function bt([string]$val) {
    $tick = [char]96
    return "$tick$val$tick"
}

# ------------------------------------------------------------------------------
# 1. Normalización Determinista de Errores (Error Signature)
# ------------------------------------------------------------------------------
function Get-NormalizedErrorSignature {
    param(
        [Parameter(Mandatory = $true)]
        [string]$ErrorText
    )

    if ([string]::IsNullOrWhiteSpace($ErrorText)) {
        return [PSCustomObject]@{
            RawText        = ""
            NormalizedText = ""
            SignatureHash  = "NONE"
            Category       = "NONE"
        }
    }

    $norm = $ErrorText

    # 1. Eliminar PIDs y Process IDs variables (ej: PID 1234, Process 5678, Thread 9)
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '(?i)\b(pid|process|thread|id)\s*[:=]?\s*\d+\b', '[PID]')

    # 2. Eliminar marcas de tiempo (ISO 8601, fechas YYYY-MM-DD, horas HH:MM:SS)
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:?\d{2})?', '[TIMESTAMP]')
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '\d{2}:\d{2}:\d{2}(\.\d+)?', '[TIME]')

    # 3. Eliminar direcciones de memoria (ej: 0x7fffabcd1234)
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '0x[0-9a-fA-F]{4,16}', '[ADDR]')

    # 4. Eliminar GUIDs / UUIDs
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}', '[GUID]')

    # 5. Eliminar rutas temporales de Windows variables
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '(?i)[a-zA-Z]:\\(?:[^\\\s]+\\)*(?:temp|tmp)\\[^\s"''`]+', '[TEMP_FILE]')
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '(?i)C:\\Users\\[^\\]+\\AppData\\Local\\Temp\\[^\s"''`]+', '[TEMP_FILE]')

    # 6. Eliminar números de línea específicos cuando aparecen en stacktraces variables (ej: :180 o at line 45)
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '(?i)(?:at\s+line\s+|línea\s+|carácter\s+|:\s*)\d+', '$1[N]')

    # 7. Reducir espacios múltiples y trim
    $norm = [System.Text.RegularExpressions.Regex]::Replace($norm, '\s+', ' ').Trim()

    # Categorización básica
    $category = "GENERIC_ERROR"
    if ($norm -match '(?i)(syntax|token|expected|parse)') {
        $category = "SYNTAX_ERROR"
    } elseif ($norm -match '(?i)(timeout|timed out|exceeded)') {
        $category = "TIMEOUT_ERROR"
    } elseif ($norm -match '(?i)(test failed|assertionerror|fail)') {
        $category = "TEST_FAILURE"
    } elseif ($norm -match '(?i)(connection refused|socket|network|http 5)') {
        $category = "NETWORK_ERROR"
    } elseif ($norm -match '(?i)(permission denied|unauthorized|access denied)') {
        $category = "SECURITY_OR_PERMISSION_ERROR"
    }

    # Cálculo de Hash SHA-256 de los primeros 500 caracteres
    $sample = if ($norm.Length -gt 500) { $norm.Substring(0, 500) } else { $norm }
    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($sample)
    $hashBytes = $sha256.ComputeHash($bytes)
    $hashStr = ([System.BitConverter]::ToString($hashBytes) -replace '-', '').ToLowerInvariant().Substring(0, 16)

    return [PSCustomObject]@{
        RawText        = $ErrorText
        NormalizedText = $norm
        SignatureHash  = $hashStr
        Category       = $category
    }
}

# ------------------------------------------------------------------------------
# 2. Huella Determinista de Avance Real (Progress Fingerprint)
# ------------------------------------------------------------------------------
function Get-ProgressFingerprint {
    param(
        [Parameter(Mandatory = $true)]
        [string]$WorkspacePath,

        [Parameter(Mandatory = $false)]
        [int]$PassTests = 0,

        [Parameter(Mandatory = $false)]
        [int]$FailTests = 0,

        [Parameter(Mandatory = $false)]
        [string]$ErrorSignatureHash = "",

        [Parameter(Mandatory = $false)]
        [string]$CustomContext = ""
    )

    $gitHead = "NO_GIT"
    $diffSummary = "CLEAN"

    if (Test-Path -LiteralPath (Join-Path $WorkspacePath ".git")) {
        try {
            $headRes = & git.exe -C $WorkspacePath rev-parse HEAD 2>&1
            if ($LASTEXITCODE -eq 0 -and $headRes) {
                $gitHead = $headRes.Trim()
            }
        } catch { }

        try {
            $statRes = & git.exe -C $WorkspacePath diff --stat 2>&1
            if ($LASTEXITCODE -eq 0 -and $statRes) {
                $diffSummary = ($statRes | Out-String).Trim()
            }
        } catch { }
    }

    # Huella combinada
    $rawCombination = "GIT_HEAD:$gitHead|DIFF:$diffSummary|TESTS:PASS=$PassTests,FAIL=$FailTests|ERR:$ErrorSignatureHash|CTX:$CustomContext"

    $sha256 = [System.Security.Cryptography.SHA256]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes($rawCombination)
    $hashBytes = $sha256.ComputeHash($bytes)
    $fingerprint = ([System.BitConverter]::ToString($hashBytes) -replace '-', '').ToLowerInvariant().Substring(0, 16)

    return [PSCustomObject]@{
        Fingerprint    = $fingerprint
        GitHead        = $gitHead
        DiffSummary    = $diffSummary
        PassTests      = $PassTests
        FailTests      = $FailTests
        ErrorSignature = $ErrorSignatureHash
        Combination    = $rawCombination
    }
}

# ------------------------------------------------------------------------------
# 3. Control de Bucles y Escalera de Escalamiento (Anti-Loop Engine)
# ------------------------------------------------------------------------------
function Test-LoopProgress {
    param(
        [Parameter(Mandatory = $true)]
        [System.Collections.IDictionary]$Tracker,

        [Parameter(Mandatory = $false)]
        [string]$CurrentErrorHash = "",

        [Parameter(Mandatory = $false)]
        [string]$CurrentFingerprint = "",

        [Parameter(Mandatory = $false)]
        [int]$MaxCycles = 20,

        [Parameter(Mandatory = $false)]
        [int]$MaxSameFailure = 3,

        [Parameter(Mandatory = $false)]
        [int]$MaxNoProgress = 3
    )

    # Inicialización de tracker si es nuevo
    if (-not $Tracker.Contains("cycle_count"))        { $Tracker["cycle_count"] = 0 }
    if (-not $Tracker.Contains("same_failure_count")) { $Tracker["same_failure_count"] = 0 }
    if (-not $Tracker.Contains("no_progress_cycles")) { $Tracker["no_progress_cycles"] = 0 }
    if (-not $Tracker.Contains("last_error_hash"))    { $Tracker["last_error_hash"] = "" }
    if (-not $Tracker.Contains("last_fingerprint"))   { $Tracker["last_fingerprint"] = "" }
    if (-not $Tracker.Contains("escalation_step"))    { $Tracker["escalation_step"] = "RETRY" }

    $Tracker["cycle_count"] = [int]$Tracker["cycle_count"] + 1
    $cycle = [int]$Tracker["cycle_count"]

    # 1. Comprobación de límite absoluto de ciclos (Section 38: max_cycles = 20)
    if ($cycle -ge $MaxCycles) {
        $Tracker["escalation_step"] = "MAX_CYCLES_REACHED"
        return [PSCustomObject]@{
            CanContinue       = $false
            Status            = "STALLED"
            RecommendedAction = "BLOCKED_REQUIRES_HUMAN"
            Reason            = "Se alcanzó el límite máximo de $MaxCycles ciclos sin convergencia."
            CycleCount        = $cycle
            SameFailureCount  = $Tracker["same_failure_count"]
            NoProgressCycles  = $Tracker["no_progress_cycles"]
            EscalationStep    = "STALLED"
        }
    }

    # 2. Evaluación de error idéntico repetido
    $isSameError = $false
    if (-not [string]::IsNullOrWhiteSpace($CurrentErrorHash) -and $CurrentErrorHash -ne "NONE") {
        if ($CurrentErrorHash -eq $Tracker["last_error_hash"]) {
            $Tracker["same_failure_count"] = [int]$Tracker["same_failure_count"] + 1
            $isSameError = $true
        } else {
            $Tracker["same_failure_count"] = 1
            $Tracker["last_error_hash"] = $CurrentErrorHash
        }
    } else {
        $Tracker["same_failure_count"] = 0
        $Tracker["last_error_hash"] = ""
    }

    # 3. Evaluación de falta de avance (Fingerprint estancado)
    $isNoProgress = $false
    if (-not [string]::IsNullOrWhiteSpace($CurrentFingerprint)) {
        if ($CurrentFingerprint -eq $Tracker["last_fingerprint"]) {
            $Tracker["no_progress_cycles"] = [int]$Tracker["no_progress_cycles"] + 1
            $isNoProgress = $true
        } else {
            $Tracker["no_progress_cycles"] = 0
            $Tracker["last_fingerprint"] = $CurrentFingerprint
        }
    }

    $sameFailures = [int]$Tracker["same_failure_count"]
    $noProgress   = [int]$Tracker["no_progress_cycles"]

    # 4. Escalera de escalamiento determinista (Section 40)
    # Secuencia: RETRY -> NEW_APPROACH -> WEB_RESEARCH -> CHATGPT -> NEW_SESSION -> STALLED/HUMAN
    $action = "CONTINUE"
    $status = "IN_PROGRESS"
    $reason = "Progreso normal detectado en ciclo $cycle."
    $canContinue = $true

    if ($sameFailures -ge $MaxSameFailure -or $noProgress -ge $MaxNoProgress) {
        # Umbral crítico de bucle alcanzado
        if ($sameFailures -ge ($MaxSameFailure + 3) -or $noProgress -ge ($MaxNoProgress + 3)) {
            $action = "BLOCKED_REQUIRES_HUMAN"
            $status = "STALLED"
            $reason = "Agotadas todas las alternativas de escalamiento automático. Requiere intervención humana."
            $canContinue = $false
        } elseif ($sameFailures -ge ($MaxSameFailure + 2) -or $noProgress -ge ($MaxNoProgress + 2)) {
            $action = "NEW_SESSION"
            $status = "ESCALATING"
            $reason = "Contexto saturado o contaminado tras intentos fallidos. Crear sesión limpia desde .autopilot."
        } elseif ($sameFailures -ge ($MaxSameFailure + 1) -or $noProgress -ge ($MaxNoProgress + 1)) {
            $action = "CHATGPT_CONSULT"
            $status = "ESCALATING"
            $reason = "Fallo persistente tras búsqueda web. Consultar a ChatGPT como asesor de arquitectura."
        } else {
            $action = "WEB_RESEARCH"
            $status = "ESCALATING"
            $reason = "Fallo idéntico repetido $sameFailures veces o $noProgress ciclos sin avance. Iniciar investigación Web técnica."
        }
    } elseif ($sameFailures -eq 2) {
        $action = "NEW_APPROACH"
        $status = "IN_PROGRESS"
        $reason = "Mismo error repetido 2 veces. Cambiar enfoque o método de implementación."
    } elseif ($sameFailures -eq 1) {
        $action = "RETRY"
        $status = "IN_PROGRESS"
        $reason = "Primer fallo detectado. Reintento simple con corrección."
    }

    $Tracker["escalation_step"] = $action

    return [PSCustomObject]@{
        CanContinue       = $canContinue
        Status            = $status
        RecommendedAction = $action
        Reason            = $reason
        CycleCount        = $cycle
        SameFailureCount  = $sameFailures
        NoProgressCycles  = $noProgress
        EscalationStep    = $action
    }
}

# ------------------------------------------------------------------------------
# 4. Ejecución Segura con Timeout y Garantía de Árbol de Procesos
# ------------------------------------------------------------------------------
function Invoke-CommandWithTimeout {
    param(
        [Parameter(Mandatory = $true)]
        [string]$CommandLine,

        [Parameter(Mandatory = $false)]
        [string]$WorkingDirectory = "",

        [Parameter(Mandatory = $false)]
        [int]$TimeoutSeconds = 30,

        [Parameter(Mandatory = $false)]
        [string]$RunId = ""
    )

    if (-not $WorkingDirectory) {
        $WorkingDirectory = Get-Location
    }

    $psi = [System.Diagnostics.ProcessStartInfo]::new()
    $psi.FileName               = "cmd.exe"
    $psi.Arguments              = "/c $CommandLine"
    $psi.WorkingDirectory       = $WorkingDirectory
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.UseShellExecute        = $false
    $psi.CreateNoWindow         = $true

    $proc = [System.Diagnostics.Process]::new()
    $proc.StartInfo = $psi

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $null = $proc.Start()
    $pidRegistered = $proc.Id

    $exitedInTime = $proc.WaitForExit($TimeoutSeconds * 1000)
    $sw.Stop()

    if (-not $exitedInTime) {
        # Timeout vencido: TERMINACIÓN INMEDIATA DE TODO EL ÁRBOL DE PROCESOS
        try {
            $null = & taskkill.exe /PID $pidRegistered /T /F 2>&1
        } catch { }

        # Esperar confirmación de muerte
        try {
            $proc.WaitForExit(3000) | Out-Null
        } catch { }

        $proc.Dispose()

        return [PSCustomObject]@{
            TimedOut        = $true
            ExitCode        = -1
            StdOut          = ""
            StdErr          = "TIMEOUT: Comando excedió el tiempo límite de $TimeoutSeconds segundos y su árbol de procesos fue terminado."
            ProcessId       = $pidRegistered
            DurationSeconds = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
            Status          = "TIMEOUT_TRIGGERED"
        }
    }

    $outText = $proc.StandardOutput.ReadToEnd()
    $errText = $proc.StandardError.ReadToEnd()
    $exitCode = $proc.ExitCode
    $proc.Dispose()

    return [PSCustomObject]@{
        TimedOut        = $false
        ExitCode        = $exitCode
        StdOut          = $outText
        StdErr          = $errText
        ProcessId       = $pidRegistered
        DurationSeconds = [Math]::Round($sw.Elapsed.TotalSeconds, 2)
        Status          = if ($exitCode -eq 0) { "SUCCESS" } else { "FAILED" }
    }
}
