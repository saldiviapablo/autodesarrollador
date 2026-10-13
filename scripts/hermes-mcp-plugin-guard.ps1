# ==============================================================================
# scripts/hermes-mcp-plugin-guard.ps1 - Deterministic Guard for Hermes MCP & Plugins
# Proyecto: Desarrollador Autonomo (Subfase 7A.2)
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet(
        "VerifyPluginIntegrity",
        "TestMcpHealth",
        "CheckMcpToolCall",
        "InvokeMcpTool",
        "InvokePluginTool"
    )]
    [string]$Action,

    [Parameter(Mandatory = $false)]
    [string]$PluginName = "desarrollador-autonomo-health",

    [Parameter(Mandatory = $false)]
    [string]$PluginEntrypointOverride = "",

    [Parameter(Mandatory = $false)]
    [string]$PluginManifestOverride = "",

    [Parameter(Mandatory = $false)]
    [string]$McpServerName = "da_local_sandbox",

    [Parameter(Mandatory = $false)]
    [string]$McpToolName = "",

    [Parameter(Mandatory = $false)]
    [string]$ArgumentsJson = "{}",

    [Parameter(Mandatory = $false)]
    [double]$TimeoutSeconds = 30.0,

    [Parameter(Mandatory = $false)]
    [string]$SecurityYamlPath = "",

    [Parameter(Mandatory = $false)]
    [string]$McpServerScriptOverride = ""
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
$infraRoot = (Resolve-Path "$scriptDir\..").Path
$pythonExe = "C:\Python314\python.exe"
$helperPy = Join-Path $infraRoot "scripts\mcp-sandbox-server.py"

$secYaml = if (-not [string]::IsNullOrWhiteSpace($SecurityYamlPath)) {
    $SecurityYamlPath
} else {
    Join-Path $infraRoot "config\security.yaml"
}

if (-not (Test-Path -LiteralPath $secYaml)) {
    $errObj = [ordered]@{
        allowed  = $false
        status   = "SECURITY_CONFIG_MISSING"
        decision = "DENY"
        reason   = "Security configuration file not found: $secYaml"
    }
    Write-Output ($errObj | ConvertTo-Json -Depth 6 -Compress)
    exit 0
}

$secConfigJson = & $pythonExe "$helperPy" --dump-yaml-json "$secYaml"
$secConfig = ($secConfigJson -join "`n") | ConvertFrom-Json

$argsB64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($ArgumentsJson))

function Get-VerifyPluginIntegrityResult {
    $pluginsPolicy = $secConfig.plugins
    if (-not $pluginsPolicy) {
        return [ordered]@{
            allowed  = $false
            status   = "PLUGIN_INTEGRITY_MISMATCH"
            decision = "DENY"
            reason   = "Missing 'plugins' section in security.yaml"
        }
    }

    $approvedMap = $pluginsPolicy.approved_plugins
    $pluginProp = $approvedMap.PSObject.Properties[$PluginName]
    if (-not $pluginProp) {
        return [ordered]@{
            allowed     = $false
            status      = "PLUGIN_INTEGRITY_MISMATCH"
            decision    = "DENY"
            plugin_name = $PluginName
            reason      = "DENY [PLUGIN_INTEGRITY_MISMATCH]: Plugin '$PluginName' is not registered in security.yaml approved_plugins."
        }
    }

    $pInfo = $pluginProp.Value
    $profilePluginDir = $pInfo.profile_dir
    $entrypointFile = if (-not [string]::IsNullOrWhiteSpace($PluginEntrypointOverride)) {
        $PluginEntrypointOverride
    } else {
        Join-Path $profilePluginDir $pInfo.entrypoint
    }
    $manifestFile = if (-not [string]::IsNullOrWhiteSpace($PluginManifestOverride)) {
        $PluginManifestOverride
    } else {
        Join-Path $profilePluginDir "plugin.yaml"
    }

    $approvedSha = ([string]$pInfo.sha256).ToLowerInvariant().Trim()
    $approvedManifestSha = ([string]$pInfo.manifest_sha256).ToLowerInvariant().Trim()

    if (-not (Test-Path -LiteralPath $entrypointFile)) {
        return [ordered]@{
            allowed                 = $false
            status                  = "PLUGIN_INTEGRITY_MISMATCH"
            decision                = "DENY"
            plugin_name             = $PluginName
            entrypoint_path         = $entrypointFile
            approved_sha256         = $approvedSha
            runtime_sha256          = "MISSING"
            reason                  = "DENY [PLUGIN_INTEGRITY_MISMATCH]: Plugin entrypoint file missing: $entrypointFile"
        }
    }

    if (-not (Test-Path -LiteralPath $manifestFile)) {
        return [ordered]@{
            allowed                  = $false
            status                   = "PLUGIN_INTEGRITY_MISMATCH"
            decision                 = "DENY"
            plugin_name              = $PluginName
            manifest_path            = $manifestFile
            approved_manifest_sha256 = $approvedManifestSha
            runtime_manifest_sha256  = "MISSING"
            reason                   = "DENY [PLUGIN_INTEGRITY_MISMATCH]: Plugin manifest file missing: $manifestFile"
        }
    }

    $runtimeSha = (Get-FileHash -LiteralPath $entrypointFile -Algorithm SHA256).Hash.ToLowerInvariant()
    $runtimeManifestSha = (Get-FileHash -LiteralPath $manifestFile -Algorithm SHA256).Hash.ToLowerInvariant()

    if ($runtimeSha -ne $approvedSha) {
        return [ordered]@{
            allowed                  = $false
            status                   = "PLUGIN_INTEGRITY_MISMATCH"
            decision                 = "DENY"
            plugin_name              = $PluginName
            entrypoint_path          = $entrypointFile
            manifest_path            = $manifestFile
            approved_sha256          = $approvedSha
            runtime_sha256           = $runtimeSha
            approved_manifest_sha256 = $approvedManifestSha
            runtime_manifest_sha256  = $runtimeManifestSha
            reason                   = "DENY [PLUGIN_INTEGRITY_MISMATCH]: SHA-256 mismatch for plugin '$PluginName' entrypoint '$entrypointFile'. Approved=$approvedSha, Runtime=$runtimeSha."
        }
    }

    if (-not [string]::IsNullOrWhiteSpace($approvedManifestSha) -and ($runtimeManifestSha -ne $approvedManifestSha)) {
        return [ordered]@{
            allowed                  = $false
            status                   = "PLUGIN_INTEGRITY_MISMATCH"
            decision                 = "DENY"
            plugin_name              = $PluginName
            entrypoint_path          = $entrypointFile
            manifest_path            = $manifestFile
            approved_sha256          = $approvedSha
            runtime_sha256           = $runtimeSha
            approved_manifest_sha256 = $approvedManifestSha
            runtime_manifest_sha256  = $runtimeManifestSha
            reason                   = "DENY [PLUGIN_INTEGRITY_MISMATCH]: SHA-256 mismatch for plugin '$PluginName' manifest '$manifestFile'. Approved=$approvedManifestSha, Runtime=$runtimeManifestSha."
        }
    }

    if (-not $pluginsPolicy.allow_unapproved_plugins -and [string]::IsNullOrWhiteSpace($PluginEntrypointOverride)) {
        $parentPluginsDir = Split-Path -Parent $profilePluginDir
        if (Test-Path -LiteralPath $parentPluginsDir) {
            $dirs = Get-ChildItem -LiteralPath $parentPluginsDir -Directory -ErrorAction SilentlyContinue
            foreach ($d in $dirs) {
                if (-not $approvedMap.PSObject.Properties[$d.Name]) {
                    return [ordered]@{
                        allowed     = $false
                        status      = "PLUGIN_INTEGRITY_MISMATCH"
                        decision    = "DENY"
                        plugin_name = $d.Name
                        reason      = "DENY [PLUGIN_INTEGRITY_MISMATCH]: Unapproved plugin directory detected in profile: $($d.FullName)"
                    }
                }
            }
        }
    }

    return [ordered]@{
        allowed                  = $true
        status                   = "PASS"
        decision                 = "ALLOW"
        plugin_name              = $PluginName
        entrypoint_path          = $entrypointFile
        manifest_path            = $manifestFile
        approved_sha256          = $approvedSha
        runtime_sha256           = $runtimeSha
        approved_manifest_sha256 = $approvedManifestSha
        runtime_manifest_sha256  = $runtimeManifestSha
        reason                   = "Plugin SHA-256 cryptographic integrity verified."
    }
}

if ($Action -eq "VerifyPluginIntegrity") {
    $res = Get-VerifyPluginIntegrityResult
    Write-Output ($res | ConvertTo-Json -Depth 6 -Compress)
    exit 0
}

if ($Action -eq "TestMcpHealth") {
    $mcpPolicy = $secConfig.mcp
    if (-not $mcpPolicy -or (-not $mcpPolicy.enabled)) {
        $out = [ordered]@{
            health_state = "DISABLED"
            allowed      = $false
            decision     = "DENY"
            server       = $McpServerName
            reason       = "MCP is disabled by security policy."
        }
        Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    $srvProp = $mcpPolicy.servers.PSObject.Properties[$McpServerName]
    if (-not $srvProp) {
        $out = [ordered]@{
            health_state = "SECURITY_BLOCKED"
            allowed      = $false
            decision     = "DENY"
            server       = $McpServerName
            reason       = "MCP server '$McpServerName' is not in security.yaml approved servers."
        }
        Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    $srvCfg = $srvProp.Value
    if (-not $srvCfg.enabled) {
        $out = [ordered]@{
            health_state = "DISABLED"
            allowed      = $false
            decision     = "DENY"
            server       = $McpServerName
            reason       = "MCP server '$McpServerName' is disabled in security.yaml."
        }
        Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    $scriptPath = if (-not [string]::IsNullOrWhiteSpace($McpServerScriptOverride)) {
        $McpServerScriptOverride
    } else {
        Join-Path $infraRoot $srvCfg.script_path
    }

    if (-not (Test-Path -LiteralPath $scriptPath)) {
        $out = [ordered]@{
            health_state = "UNAVAILABLE"
            allowed      = $false
            decision     = "DENY"
            server       = $McpServerName
            script_path  = $scriptPath
            reason       = "MCP server script not found: $scriptPath"
        }
        Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    if ([string]::IsNullOrWhiteSpace($McpServerScriptOverride) -and $srvCfg.sha256) {
        $actualHash = (Get-FileHash -LiteralPath $scriptPath -Algorithm SHA256).Hash.ToLowerInvariant()
        $expectedHash = ([string]$srvCfg.sha256).ToLowerInvariant().Trim()
        if ($actualHash -ne $expectedHash) {
            $out = [ordered]@{
                health_state    = "SECURITY_BLOCKED"
                allowed         = $false
                decision        = "DENY"
                server          = $McpServerName
                script_path     = $scriptPath
                approved_sha256 = $expectedHash
                runtime_sha256  = $actualHash
                reason          = "MCP server script SHA-256 mismatch."
            }
            Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
            exit 0
        }
    }

    $rawProbe = & $pythonExe "$scriptPath" --health-check --timeout $TimeoutSeconds 2>&1
    $probeText = ($rawProbe | Out-String).Trim()
    try {
        $probeObj = $probeText | ConvertFrom-Json
        Write-Output ($probeObj | ConvertTo-Json -Depth 8 -Compress)
    } catch {
        $out = [ordered]@{
            health_state = "UNAVAILABLE"
            allowed      = $false
            decision     = "DENY"
            server       = $McpServerName
            reason       = "Health check failed to parse: $probeText"
        }
        Write-Output ($out | ConvertTo-Json -Depth 6 -Compress)
    }
    exit 0
}

function Get-CheckMcpToolCallResult {
    $mcpPolicy = $secConfig.mcp
    if (-not $mcpPolicy -or (-not $mcpPolicy.enabled)) {
        return [ordered]@{
            allowed  = $false
            status   = "DISABLED"
            decision = "DENY"
            server   = $McpServerName
            tool     = $McpToolName
            reason   = "DENY [MCP_DISABLED]: MCP is disabled in security.yaml."
        }
    }

    $srvProp = $mcpPolicy.servers.PSObject.Properties[$McpServerName]
    if (-not $srvProp) {
        return [ordered]@{
            allowed  = $false
            status   = "SERVER_NOT_ALLOWED"
            decision = "DENY"
            server   = $McpServerName
            tool     = $McpToolName
            reason   = "DENY [SERVER_NOT_ALLOWED]: MCP server '$McpServerName' is not in security.yaml."
        }
    }

    $srvCfg = $srvProp.Value
    $allowedTools = @($srvCfg.allowed_tools | ForEach-Object { [string]$_ })
    $normalizedTool = $McpToolName
    if ($normalizedTool -match '^mcp__[^_]+(?:_[^_]+)*__(.+)$') {
        $parts = $normalizedTool -split '__', 3
        if ($parts.Count -eq 3) {
            $normalizedTool = $parts[2]
        }
    }

    if ($allowedTools -notcontains $normalizedTool) {
        return [ordered]@{
            allowed       = $false
            status        = "TOOL_NOT_ALLOWED"
            decision      = "DENY"
            server        = $McpServerName
            tool          = $normalizedTool
            allowed_tools = $allowedTools
            reason        = "DENY [TOOL_NOT_ALLOWED]: Tool '$normalizedTool' is not in the approved allowlist for server '$McpServerName'."
        }
    }

    if ($normalizedTool -eq "da_read_sandbox") {
        $checkRaw = & $pythonExe "$helperPy" --validate-path-b64 --args-b64 "$argsB64"
        $checkObj = ($checkRaw -join "`n") | ConvertFrom-Json
        if (-not $checkObj.allowed) {
            return [ordered]@{
                allowed  = $false
                status   = "PATH_CONFINEMENT_VIOLATION"
                decision = "DENY"
                server   = $McpServerName
                tool     = $normalizedTool
                reason   = $checkObj.reason
            }
        }
    }

    return [ordered]@{
        allowed  = $true
        status   = "ALLOW"
        decision = "ALLOW"
        server   = $McpServerName
        tool     = $normalizedTool
        reason   = "MCP tool call allowed by security policy and sandbox confinement."
    }
}

if ($Action -eq "CheckMcpToolCall") {
    $res = Get-CheckMcpToolCallResult
    Write-Output ($res | ConvertTo-Json -Depth 6 -Compress)
    exit 0
}

if ($Action -eq "InvokeMcpTool") {
    $check = Get-CheckMcpToolCallResult
    if (-not $check.allowed) {
        Write-Output ($check | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    $normalizedTool = $check.tool
    $mcpPy = if (-not [string]::IsNullOrWhiteSpace($McpServerScriptOverride)) {
        $McpServerScriptOverride
    } else {
        $helperPy
    }

    $rawCall = & $pythonExe "$mcpPy" --call-tool "$normalizedTool" --args-b64 "$argsB64" --timeout $TimeoutSeconds 2>&1
    $callText = ($rawCall | Out-String).Trim()
    try {
        $callObj = $callText | ConvertFrom-Json
        Write-Output ($callObj | ConvertTo-Json -Depth 8 -Compress)
    } catch {
        $errOut = [ordered]@{
            status   = "UNAVAILABLE"
            decision = "DENY"
            is_error = $true
            server   = $McpServerName
            tool     = $normalizedTool
            reason   = "Failed to parse MCP tool output: $callText"
        }
        Write-Output ($errOut | ConvertTo-Json -Depth 6 -Compress)
    }
    exit 0
}

if ($Action -eq "InvokePluginTool") {
    $integrity = Get-VerifyPluginIntegrityResult
    if (-not $integrity.allowed -or $integrity.status -ne "PASS") {
        Write-Output ($integrity | ConvertTo-Json -Depth 6 -Compress)
        exit 0
    }

    $entrypointFile = $integrity.entrypoint_path
    $pluginOutRaw = & $pythonExe "$helperPy" --invoke-plugin "$entrypointFile" --args-b64 "$argsB64"
    Write-Output ($pluginOutRaw -join "`n")
    exit 0
}
