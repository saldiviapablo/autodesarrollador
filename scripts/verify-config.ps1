# ==============================================================================
# scripts/verify-config.ps1 — Verificación Determinista de Configuración Central
# Proyecto: Desarrollador Autónomo
# Versión: 2.0 (Fase 4 — Configuración Central)
# ==============================================================================
[CmdletBinding()]
param(
    [string]$ConfigDir = "",
    [string]$LogFile = "",
    [string]$PythonExe = "C:\Python314\python.exe"
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
$infraRoot = (Resolve-Path "$scriptDir\..").Path

if (-not $ConfigDir) {
    $ConfigDir = Join-Path $infraRoot "config"
}
if (-not $LogFile) {
    $LogFile = Join-Path $infraRoot "logs\config-verification-20261011.log"
}

$scriptStartTime = Get-Date
$allPass = $true
$testCount = 0
$passCount = 0
$failCount = 0

# Ensure logs dir exists
$logDir = [System.IO.Path]::GetDirectoryName($LogFile)
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Log-Message {
    param([string]$Msg, [string]$Level = "INFO")
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $formatted = "[$timestamp] [$Level] $Msg"
    Write-Host $formatted
    Add-Content -LiteralPath $LogFile -Value $formatted -Encoding UTF8
}

function Assert-Test {
    param(
        [string]$TestName,
        [bool]$Condition,
        [string]$Details = ""
    )
    $script:testCount++
    if ($Condition) {
        $script:passCount++
        Log-Message "  [PASS] $TestName $(if ($Details) { "($Details)" } else { '' })" "OK"
    } else {
        $script:failCount++
        $script:allPass = $false
        Log-Message "  [FAIL] $TestName $(if ($Details) { "($Details)" } else { '' })" "ERROR"
    }
}

Log-Message "=============================================================================="
Log-Message "Iniciando verificación determinista de configuración (Fase 4)"
Log-Message "ConfigDir: $ConfigDir"
Log-Message "LogFile:   $LogFile"
Log-Message "Python:    $PythonExe"
Log-Message "=============================================================================="

# ------------------------------------------------------------------------------
# 1. Comprobación de existencia y tamaño de archivos
# ------------------------------------------------------------------------------
Log-Message "1. Verificando existencia física de archivos de configuración..."

$systemYaml = Join-Path $ConfigDir "system.yaml"
$securityYaml = Join-Path $ConfigDir "security.yaml"
$versionsLock = Join-Path $ConfigDir "VERSIONS.lock"
$readmeMd = Join-Path $ConfigDir "README.md"

Assert-Test "system.yaml existe" (Test-Path -LiteralPath $systemYaml) $systemYaml
Assert-Test "system.yaml no está vacío" ((Get-Item -LiteralPath $systemYaml).Length -gt 100) "$((Get-Item -LiteralPath $systemYaml).Length) bytes"

Assert-Test "security.yaml existe" (Test-Path -LiteralPath $securityYaml) $securityYaml
Assert-Test "security.yaml no está vacío" ((Get-Item -LiteralPath $securityYaml).Length -gt 100) "$((Get-Item -LiteralPath $securityYaml).Length) bytes"

Assert-Test "VERSIONS.lock existe" (Test-Path -LiteralPath $versionsLock) $versionsLock
Assert-Test "VERSIONS.lock no está vacío" ((Get-Item -LiteralPath $versionsLock).Length -gt 100) "$((Get-Item -LiteralPath $versionsLock).Length) bytes"

Assert-Test "README.md existe" (Test-Path -LiteralPath $readmeMd) $readmeMd

# ------------------------------------------------------------------------------
# 2. Validación de sintaxis YAML mediante Python + PyYAML
# ------------------------------------------------------------------------------
Log-Message "2. Validando sintaxis YAML de los archivos..."
Assert-Test "Python ejecutable disponible" (Test-Path -LiteralPath $PythonExe) $PythonExe

function Parse-YamlFile([string]$FilePath) {
    $code = @"
import yaml, json, sys
try:
    with open(sys.argv[1], 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    print(json.dumps(data))
except Exception as e:
    sys.stderr.write(str(e))
    sys.exit(1)
"@
    $pinfo = New-Object System.Diagnostics.ProcessStartInfo
    $pinfo.FileName = $PythonExe
    $pinfo.Arguments = "-c `"$code`" `"$FilePath`""
    $pinfo.RedirectStandardOutput = $true
    $pinfo.RedirectStandardError = $true
    $pinfo.UseShellExecute = $false
    $pinfo.CreateNoWindow = $true

    $proc = [System.Diagnostics.Process]::Start($pinfo)
    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()

    if ($proc.ExitCode -ne 0) {
        throw "Error parseando YAML ($FilePath): $stderr"
    }

    return ($stdout | ConvertFrom-Json)
}

try {
    $sysObj = Parse-YamlFile -FilePath $systemYaml
    Assert-Test "system.yaml sintaxis YAML válida" $true
} catch {
    Assert-Test "system.yaml sintaxis YAML válida" $false $_.Exception.Message
}

try {
    $secObj = Parse-YamlFile -FilePath $securityYaml
    Assert-Test "security.yaml sintaxis YAML válida" $true
} catch {
    Assert-Test "security.yaml sintaxis YAML válida" $false $_.Exception.Message
}

try {
    $verObj = Parse-YamlFile -FilePath $versionsLock
    Assert-Test "VERSIONS.lock sintaxis YAML válida" $true
} catch {
    Assert-Test "VERSIONS.lock sintaxis YAML válida" $false $_.Exception.Message
}

# ------------------------------------------------------------------------------
# 3. Verificación de campos obligatorios
# ------------------------------------------------------------------------------
Log-Message "3. Verificando campos obligatorios en los esquemas..."

# system.yaml fields
Assert-Test "system.yaml contiene system.name" (-not [string]::IsNullOrEmpty($sysObj.system.name)) $sysObj.system.name
Assert-Test "system.yaml contiene system.environment" (-not [string]::IsNullOrEmpty($sysObj.system.environment)) $sysObj.system.environment
Assert-Test "system.yaml contiene paths.infrastructure_root" (-not [string]::IsNullOrEmpty($sysObj.paths.infrastructure_root)) $sysObj.paths.infrastructure_root
Assert-Test "system.yaml contiene llama.executable" (-not [string]::IsNullOrEmpty($sysObj.llama.executable)) $sysObj.llama.executable
Assert-Test "system.yaml contiene llama.model" (-not [string]::IsNullOrEmpty($sysObj.llama.model)) $sysObj.llama.model
Assert-Test "system.yaml contiene llama.endpoints" (($sysObj.llama.health_endpoint -match "/health") -and ($sysObj.llama.chat_completions_endpoint -match "/chat/completions")) "health & completions endpoints"
Assert-Test "system.yaml contiene runner timeouts" (($sysObj.runner.llama_start_timeout_seconds -gt 0) -and ($sysObj.runner.request_timeout_seconds -gt 0)) "llama_start_timeout=$($sysObj.runner.llama_start_timeout_seconds)s"
Assert-Test "system.yaml contiene inference_lock" (($sysObj.inference_lock.timeout_seconds -gt 0) -and ($sysObj.inference_lock.stale_threshold_seconds -gt 0)) "lock_timeout=$($sysObj.inference_lock.timeout_seconds)s"
Assert-Test "system.yaml contiene limits" (($sysObj.limits.max_cycles -gt 0) -and ($sysObj.limits.max_same_failure -gt 0)) "max_cycles=$($sysObj.limits.max_cycles)"
Assert-Test "system.yaml contiene logging" (-not [string]::IsNullOrEmpty($sysObj.logging.level)) "level=$($sysObj.logging.level)"
Assert-Test "system.yaml contiene recovery" ($sysObj.recovery.auto_reconcile -eq $true) "auto_reconcile=$($sysObj.recovery.auto_reconcile)"
Assert-Test "system.yaml contiene chatgpt" ($sysObj.chatgpt.profile_name -eq "HERMES-CHATGPT") "profile=$($sysObj.chatgpt.profile_name)"
Assert-Test "system.yaml contiene known_warnings" ($sysObj.llama.known_warnings.Count -ge 1) "$($sysObj.llama.known_warnings[0].id)"

# security.yaml fields
Assert-Test "security.yaml contiene workspace bounds" ($sysObj.paths.infrastructure_root -ne $null) "canonical bounds"
Assert-Test "security.yaml contiene git policies" ($secObj.git.allow_push -ne $null) "git section defined"
Assert-Test "security.yaml contiene system policies" ($secObj.system.allow_shutdown -ne $null) "system section defined"
Assert-Test "security.yaml contiene network policies" ($secObj.network.llama_host -ne $null) "network section defined"
Assert-Test "security.yaml contiene browser policies" ($secObj.browser.dedicated_profile_required -eq $true) "browser section defined"
Assert-Test "security.yaml contiene chatgpt policies" ($secObj.chatgpt.allowed_domain -eq "chatgpt.com") "chatgpt domain locked"
Assert-Test "security.yaml contiene autonomy limits" ($secObj.autonomy.max_cycles -gt 0) "autonomy section defined"
Assert-Test "security.yaml contiene secret_policy" ($secObj.secret_policy.redact_logs -eq $true) "secret policy defined"
Assert-Test "security.yaml contiene protected_paths" ($secObj.protected_paths.Count -ge 5) "$($secObj.protected_paths.Count) paths"
Assert-Test "security.yaml contiene blocked_commands" ($secObj.blocked_commands.patterns.Count -ge 10) "$($secObj.blocked_commands.patterns.Count) patterns"

# VERSIONS.lock fields
Assert-Test "VERSIONS.lock contiene lock_version" (-not [string]::IsNullOrEmpty($verObj.lock_version)) "version $($verObj.lock_version)"
Assert-Test "VERSIONS.lock contiene environment OS & HW" (($verObj.environment.operating_system.build -eq "26200") -and ($verObj.environment.hardware.vram_mib -gt 0)) "Win11 Build 26200"
Assert-Test "VERSIONS.lock contiene llama_cpp VALIDATED" ($verObj.inference.llama_cpp.status -eq "VALIDATED") "Build $($verObj.inference.llama_cpp.build)"
Assert-Test "VERSIONS.lock contiene qwen_model VALIDATED" ($verObj.inference.qwen_model.status -eq "VALIDATED") "Qwen3.6-35B-A3B"
Assert-Test "VERSIONS.lock contiene runtimes (python, node, powershell)" (($verObj.runtimes.python_main.version -match "^3\.") -and ($verObj.runtimes.node.version -match "^24\.")) "Python & Node locked"
Assert-Test "VERSIONS.lock contiene tools (git, chrome)" (($verObj.tools.git.version -match "^2\.") -and ($verObj.tools.chrome.version -match "^154\.")) "Git & Chrome locked"

# ------------------------------------------------------------------------------
# 4. Verificación de existencia real de rutas clave en el host
# ------------------------------------------------------------------------------
Log-Message "4. Verificando rutas configuradas contra el sistema de archivos real..."

$llamaExe = $sysObj.llama.executable
Assert-Test "Ruta llama.executable existe físicamente" (Test-Path -LiteralPath $llamaExe) $llamaExe

$qwenModel = $sysObj.llama.model
Assert-Test "Ruta llama.model existe físicamente" (Test-Path -LiteralPath $qwenModel) $qwenModel

# Verificar resolución de symlink del modelo si aplica
if (Test-Path -LiteralPath $qwenModel) {
    $modelItem = Get-Item -LiteralPath $qwenModel
    if ($modelItem.LinkType -eq "SymbolicLink") {
        $target = $modelItem.Target
        if ($target -is [array]) { $target = $target[0] }
        if (-not [System.IO.Path]::IsPathRooted($target)) {
            $target = [System.IO.Path]::GetFullPath((Join-Path $modelItem.DirectoryName $target))
        }
        Assert-Test "Symlink llama.model apunta a blob existente" (Test-Path -LiteralPath $target) $target
    } else {
        Assert-Test "llama.model es archivo regular existente" ($modelItem.Length -gt 10GB) "$([Math]::Round($modelItem.Length / 1GB, 2)) GB"
    }
}

$infraroot = $sysObj.paths.infrastructure_root
Assert-Test "Ruta paths.infrastructure_root existe" (Test-Path -LiteralPath $infraroot) $infraroot

# ------------------------------------------------------------------------------
# 5. Verificación de valores críticos y guardrails aprobados
# ------------------------------------------------------------------------------
Log-Message "5. Verificando correspondencia de valores críticos aprobados..."

# llama.cpp critical parameters
Assert-Test "llama.host == '127.0.0.1'" ($sysObj.llama.host -eq "127.0.0.1") $sysObj.llama.host
Assert-Test "llama.port == 8080" ($sysObj.llama.port -eq 8080) $sysObj.llama.port
Assert-Test "llama.ctx_size == 65536" ($sysObj.llama.ctx_size -eq 65536) "$($sysObj.llama.ctx_size) tokens"
Assert-Test "llama.parallel == 1" ($sysObj.llama.parallel -eq 1) "$($sysObj.llama.parallel) slot"
Assert-Test "llama.alias == 'qwen36'" ($sysObj.llama.alias -eq "qwen36") $sysObj.llama.alias
Assert-Test "llama.cpu_moe == true" ($sysObj.llama.cpu_moe -eq $true) "cpu_moe=$($sysObj.llama.cpu_moe)"
Assert-Test "llama.n_gpu_layers == 99" ($sysObj.llama.n_gpu_layers -eq 99) "n_gpu_layers=$($sysObj.llama.n_gpu_layers)"
Assert-Test "llama.flash_attention == true" ($sysObj.llama.flash_attention -eq $true) "flash_attn=$($sysObj.llama.flash_attention)"
Assert-Test "llama.cache_type_k == 'q8_0'" ($sysObj.llama.cache_type_k -eq "q8_0") $sysObj.llama.cache_type_k
Assert-Test "llama.cache_type_v == 'q8_0'" ($sysObj.llama.cache_type_v -eq "q8_0") $sysObj.llama.cache_type_v
Assert-Test "llama.jinja == true" ($sysObj.llama.jinja -eq $true) "jinja=$($sysObj.llama.jinja)"

# Security critical parameters
Assert-Test "security.git.allow_push == false" ($secObj.git.allow_push -eq $false) "push disabled"
Assert-Test "security.git.allow_force_push == false" ($secObj.git.allow_force_push -eq $false) "force push disabled"
Assert-Test "security.git.allow_destructive_reset == false" ($secObj.git.allow_destructive_reset -eq $false) "reset hard disabled"
Assert-Test "security.git.allow_clean_fdx == false" ($secObj.git.allow_clean_fdx -eq $false) "clean fdx disabled"
Assert-Test "security.network.llama_public == false" ($secObj.network.llama_public -eq $false) "network public disabled"
Assert-Test "security.network.llama_host == '127.0.0.1'" ($secObj.network.llama_host -eq "127.0.0.1") "local host enforced"
Assert-Test "security.workspace.allow_write_outside == false" ($secObj.workspace.allow_write_outside -eq $false) "writes jailed to workspace"
Assert-Test "security.system.allow_admin_runtime == false" ($secObj.system.allow_admin_runtime -eq $false) "no admin required"
Assert-Test "security.system.allow_shutdown == false" ($secObj.system.allow_shutdown -eq $false) "shutdown blocked"
Assert-Test "security.chatgpt.allowed_domain == 'chatgpt.com'" ($secObj.chatgpt.allowed_domain -eq "chatgpt.com") "domain locked"

# ------------------------------------------------------------------------------
# 6. Escaneo de secretos accidentales en los archivos de configuración
# ------------------------------------------------------------------------------
Log-Message "6. Verificando ausencia de secretos o credenciales en archivos..."

$secretRegexes = @(
    "sk-[a-zA-Z0-9]{20,}",
    "ghp_[a-zA-Z0-9]{20,}",
    "gho_[a-zA-Z0-9]{20,}",
    "Bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    "password\s*:\s*[`"'].+[`"']",
    "secret\s*:\s*[`"'].+[`"']"
)

$secretFound = $false
foreach ($filePath in @($systemYaml, $securityYaml, $versionsLock)) {
    $content = Get-Content -LiteralPath $filePath -Raw -Encoding UTF8
    foreach ($regex in $secretRegexes) {
        if ($content -match $regex) {
            $secretFound = $true
            Log-Message "  Patrón de secreto sospechoso detectado en $($filePath): $regex" "ERROR"
        }
    }
}
Assert-Test "Sin secretos ni API keys en config/" (-not $secretFound) "Escaneo regex limpio"

# ------------------------------------------------------------------------------
# Resumen y resultado final
# ------------------------------------------------------------------------------
$duration = [Math]::Round(((Get-Date) - $scriptStartTime).TotalSeconds, 2)
Log-Message "=============================================================================="
Log-Message "Resumen de Verificación de Configuración Central:"
Log-Message "  Total pruebas: $testCount"
Log-Message "  Aprobadas:     $passCount"
Log-Message "  Fallidas:      $failCount"
Log-Message "  Duración:      ${duration}s"

if ($allPass) {
    Log-Message "RESULTADO GLOBAL: [PASS] Configuración válida y determinista." "OK"
    exit 0
} else {
    Log-Message "RESULTADO GLOBAL: [FAIL] Se detectaron discrepancias o errores en la configuración." "ERROR"
    exit 1
}
