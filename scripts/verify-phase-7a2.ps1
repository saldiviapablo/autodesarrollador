# ==============================================================================
# scripts/verify-phase-7a2.ps1 - Suite de Verificacion Determinista Subfase 7A.2
# Proyecto: Desarrollador Autonomo
# Subfase 7A.2: Servidores MCP + Plugins / Custom Tools Gobernados
# ==============================================================================
[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [int]$McpTimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
if (-not $scriptDir) { $scriptDir = $PSScriptRoot }
$infraRoot = (Resolve-Path "$scriptDir\..").Path
$evidenceDir = Join-Path $infraRoot "evidence\phase-7a2"
$sandboxDir = Join-Path $infraRoot "sandbox\phase7a2-mcp"
$guardScript = Join-Path $infraRoot "scripts\hermes-mcp-plugin-guard.ps1"
$memoryGuardScript = Join-Path $infraRoot "scripts\hermes-memory-guard.ps1"
$invokeHermesScript = Join-Path $infraRoot "scripts\invoke-hermes.ps1"
$mcpServerPy = Join-Path $infraRoot "scripts\mcp-sandbox-server.py"
$hermesExe = "C:\Users\Pc\AppData\Local\hermes\bin\hermes.exe"
$pythonExe = "C:\Python314\python.exe"

New-Item -ItemType Directory -Path $evidenceDir -Force | Out-Null
New-Item -ItemType Directory -Path $sandboxDir -Force | Out-Null

$spawnedPids = [System.Collections.Generic.List[int]]::new()
$profileConfigYaml = "C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\config.yaml"
$profilePluginInit = "C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\plugins\desarrollador-autonomo-health\__init__.py"
$originalPluginInitBytes = [System.IO.File]::ReadAllBytes($profilePluginInit)
$junctionPath = Join-Path $sandboxDir "junction-escape"

function ConvertTo-B64([string]$text) {
    return [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($text))
}

$results = [ordered]@{}

try {
    Write-Host "==================================================================" -ForegroundColor Cyan
    Write-Host " INICIANDO VERIFICACION SUBFASE 7A.2 (MCP + PLUGINS GOBERNADOS)" -ForegroundColor Cyan
    Write-Host "==================================================================" -ForegroundColor Cyan

    # Pre-check: Ensure Frozen Hook SHA-256 from 7A.1 is intact
    $hookCheckRaw = & $memoryGuardScript -Action VerifyHookIntegrity
    $hookCheck = ($hookCheckRaw -join "`n") | ConvertFrom-Json
    if (-not $hookCheck.allowed -or $hookCheck.status -ne "PASS") {
        throw "Precheck failed: 7A.1 pre_tool_call hook integrity is not PASS: $($hookCheck.status)"
    }

    # Ensure sandbox fixture exists
    $fixturePath = Join-Path $sandboxDir "sample-allowed.txt"
    "Desarrollador Autonomo - Subfase 7A.2 MCP Sandbox Fixture`nStatus: ALLOWED_SANDBOX_READ`nScope: sandbox/phase7a2-mcp" | Set-Content -Path $fixturePath -Encoding UTF8

    # ==========================================================================
    # T-7A-MCP-001: Funcional (Conexion local, descubrimiento, herramientas allowlisted)
    # ==========================================================================
    Write-Host "`n[T-7A-MCP-001] Ejecutando prueba funcional de servidor MCP gobernado..." -ForegroundColor Yellow

    $mcpListOut = (& $hermesExe -p desarrollador-autonomo mcp list 2>&1 | Out-String).Trim()
    $mcpTestOut = (& $hermesExe -p desarrollador-autonomo mcp test da_local_sandbox 2>&1 | Out-String).Trim()

    $healthRaw = & $guardScript -Action TestMcpHealth -McpServerName "da_local_sandbox" -TimeoutSeconds 15
    $healthObj = ($healthRaw -join "`n") | ConvertFrom-Json

    $echoRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_echo" -ArgumentsJson '{"message":"Hola desde MCP 7A.2"}' -TimeoutSeconds 15
    $echoObj = ($echoRaw -join "`n") | ConvertFrom-Json

    $readRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_read_sandbox" -ArgumentsJson '{"relative_path":"sample-allowed.txt"}' -TimeoutSeconds 15
    $readObj = ($readRaw -join "`n") | ConvertFrom-Json

    $t1Pass = (
        ($mcpListOut -match "da_local_sandbox") -and
        ($mcpListOut -match "4 selected") -and
        ($mcpTestOut -match "Connected") -and
        ($healthObj.health_state -eq "HEALTHY") -and
        ($echoObj.status -eq "OK") -and
        ($echoObj.result.echo -eq "Hola desde MCP 7A.2") -and
        ($readObj.status -eq "OK") -and
        ($readObj.result.content -match "ALLOWED_SANDBOX_READ")
    )

    $t1Evidence = [ordered]@{
        test_id          = "T-7A-MCP-001"
        name             = "MCP Functional Connection and Allowlisted Tool Execution"
        status           = if ($t1Pass) { "PASS" } else { "FAIL" }
        timestamp        = (Get-Date).ToString("o")
        hermes_mcp_list  = $mcpListOut
        hermes_mcp_test  = $mcpTestOut
        health_check     = $healthObj
        da_echo_call     = $echoObj
        da_read_call     = $readObj
    }
    $t1Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-MCP-001.json") -Encoding UTF8
    $results["T-7A-MCP-001"] = $t1Evidence.status
    Write-Host "[T-7A-MCP-001] Resultado: $($t1Evidence.status)" -ForegroundColor ($(if ($t1Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-MCP-002: Seguridad / Filtrado de Herramientas (da_forbidden_test -> DENY)
    # ==========================================================================
    Write-Host "`n[T-7A-MCP-002] Ejecutando prueba de bloqueo de herramienta fuera de allowlist..." -ForegroundColor Yellow

    # Layer 1: Hermes native _make_tool_filter check + Plugin pre_tool_call hook check
    $layer1Raw = & $pythonExe "$mcpServerPy" --test-allowlist "$profileConfigYaml" "$profilePluginInit"
    $layer1Obj = ($layer1Raw -join "`n") | ConvertFrom-Json

    # Layer 2: PowerShell Guard CheckMcpToolCall / InvokeMcpTool
    $guardForbiddenRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_forbidden_test" -ArgumentsJson '{"payload":"unauthorized"}'
    $guardForbiddenObj = ($guardForbiddenRaw -join "`n") | ConvertFrom-Json

    # Layer 3: Direct MCP Server internal policy enforcement
    $forbB64 = ConvertTo-B64 '{"payload":"unauthorized"}'
    $srvForbiddenRaw = & $pythonExe "$mcpServerPy" --call-tool "da_forbidden_test" --args-b64 "$forbB64"
    $srvForbiddenObj = ($srvForbiddenRaw -join "`n") | ConvertFrom-Json

    $t2Pass = (
        ($layer1Obj.hermes_native_filter_allows_da_echo -eq $true) -and
        ($layer1Obj.hermes_native_filter_allows_da_forbidden_test -eq $false) -and
        ($layer1Obj.plugin_pre_tool_hook_verdict.action -eq "block") -and
        ($layer1Obj.plugin_pre_tool_hook_verdict.message -match "TOOL_NOT_ALLOWED") -and
        ($guardForbiddenObj.status -eq "TOOL_NOT_ALLOWED") -and
        ($guardForbiddenObj.decision -eq "DENY") -and
        ($srvForbiddenObj.status -eq "TOOL_NOT_ALLOWED") -and
        ($srvForbiddenObj.decision -eq "DENY")
    )

    $t2Evidence = [ordered]@{
        test_id                  = "T-7A-MCP-002"
        name                     = "MCP Tool Allowlist Enforcement (da_forbidden_test -> DENY)"
        status                   = if ($t2Pass) { "PASS" } else { "FAIL" }
        timestamp                = (Get-Date).ToString("o")
        hermes_and_hook_layer    = $layer1Obj
        powershell_guard_verdict = $guardForbiddenObj
        mcp_server_inner_verdict = $srvForbiddenObj
    }
    $t2Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-MCP-002.json") -Encoding UTF8
    $results["T-7A-MCP-002"] = $t2Evidence.status
    Write-Host "[T-7A-MCP-002] Resultado: $($t2Evidence.status)" -ForegroundColor ($(if ($t2Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-MCP-003: Fallo / Timeout Determinista (30s timeout -> MCP_TIMEOUT)
    # ==========================================================================
    Write-Host "`n[T-7A-MCP-003] Ejecutando prueba de timeout determinista ($McpTimeoutSeconds s)..." -ForegroundColor Yellow

    $sleepTarget = $McpTimeoutSeconds + 8
    $slowArgs = (@{ sleep_seconds = $sleepTarget } | ConvertTo-Json -Compress)
    $timeoutCallRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_slow_test" -ArgumentsJson $slowArgs -TimeoutSeconds $McpTimeoutSeconds
    $timeoutCallObj = ($timeoutCallRaw -join "`n") | ConvertFrom-Json

    $childAliveAfterTimeout = $false
    if ($timeoutCallObj.child_pid) {
        $pCheck = Get-Process -Id $timeoutCallObj.child_pid -ErrorAction SilentlyContinue
        if ($pCheck) { $childAliveAfterTimeout = $true }
    }

    # Verify MCP server is immediately usable after timeout
    $postTimeoutHealthRaw = & $guardScript -Action TestMcpHealth -McpServerName "da_local_sandbox" -TimeoutSeconds 15
    $postTimeoutHealthObj = ($postTimeoutHealthRaw -join "`n") | ConvertFrom-Json

    $t3Pass = (
        ($timeoutCallObj.status -eq "MCP_TIMEOUT") -and
        ($timeoutCallObj.decision -eq "DENY") -and
        ($timeoutCallObj.duration_seconds -ge ($McpTimeoutSeconds - 1)) -and
        ($timeoutCallObj.duration_seconds -le ($McpTimeoutSeconds + 5)) -and
        ($childAliveAfterTimeout -eq $false) -and
        ($postTimeoutHealthObj.health_state -eq "HEALTHY")
    )

    $t3Evidence = [ordered]@{
        test_id                        = "T-7A-MCP-003"
        name                           = "Deterministic MCP Timeout and Clean Child Process Termination"
        status                         = if ($t3Pass) { "PASS" } else { "FAIL" }
        timestamp                      = (Get-Date).ToString("o")
        configured_timeout_seconds     = $McpTimeoutSeconds
        requested_sleep_seconds        = $sleepTarget
        timeout_response               = $timeoutCallObj
        child_process_alive_after_kill = $childAliveAfterTimeout
        post_timeout_health            = $postTimeoutHealthObj
    }
    $t3Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-MCP-003.json") -Encoding UTF8
    $results["T-7A-MCP-003"] = $t3Evidence.status
    Write-Host "[T-7A-MCP-003] Resultado: $($t3Evidence.status) (duracion=$($timeoutCallObj.duration_seconds)s)" -ForegroundColor ($(if ($t3Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-MCP-004: Confinamiento de Rutas (../, C:\Windows, symlink/junction -> DENY)
    # ==========================================================================
    Write-Host "`n[T-7A-MCP-004] Ejecutando prueba de confinamiento de rutas (../, C:\Windows, junction)..." -ForegroundColor Yellow

    # 1. Relative traversal ../
    $travRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_read_sandbox" -ArgumentsJson '{"relative_path":"../../config/security.yaml"}'
    $travObj = ($travRaw -join "`n") | ConvertFrom-Json

    # 2. Absolute path outside sandbox (C:\Windows\win.ini)
    $absRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_read_sandbox" -ArgumentsJson '{"relative_path":"C:\\Windows\\win.ini"}'
    $absObj = ($absRaw -join "`n") | ConvertFrom-Json

    # 3. NTFS Junction escape inside sandbox/phase7a2-mcp/
    if (Test-Path -LiteralPath $junctionPath) {
        cmd.exe /c rmdir "$junctionPath" 2>&1 | Out-Null
    }
    $configTarget = Join-Path $infraRoot "config"
    cmd.exe /c mklink /J "$junctionPath" "$configTarget" | Out-Null

    $juncRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_read_sandbox" -ArgumentsJson '{"relative_path":"junction-escape/security.yaml"}'
    $juncObj = ($juncRaw -join "`n") | ConvertFrom-Json

    # Also test direct server call on junction to verify defense-in-depth inside mcp-sandbox-server.py
    $juncB64 = ConvertTo-B64 '{"relative_path":"junction-escape/security.yaml"}'
    $srvJuncRaw = & $pythonExe "$mcpServerPy" --call-tool "da_read_sandbox" --args-b64 "$juncB64"
    $srvJuncObj = ($srvJuncRaw -join "`n") | ConvertFrom-Json

    if (Test-Path -LiteralPath $junctionPath) {
        cmd.exe /c rmdir "$junctionPath" 2>&1 | Out-Null
    }

    $t4Pass = (
        ($travObj.status -eq "PATH_CONFINEMENT_VIOLATION") -and ($travObj.decision -eq "DENY") -and
        ($absObj.status -eq "PATH_CONFINEMENT_VIOLATION") -and ($absObj.decision -eq "DENY") -and
        ($juncObj.status -eq "PATH_CONFINEMENT_VIOLATION") -and ($juncObj.decision -eq "DENY") -and
        ($srvJuncObj.status -eq "PATH_CONFINEMENT_VIOLATION") -and ($srvJuncObj.decision -eq "DENY")
    )

    $t4Evidence = [ordered]@{
        test_id                    = "T-7A-MCP-004"
        name                       = "MCP Canonical Path Confinement (Traversal, Outside Path, NTFS Junction)"
        status                     = if ($t4Pass) { "PASS" } else { "FAIL" }
        timestamp                  = (Get-Date).ToString("o")
        relative_traversal_attempt = $travObj
        outside_path_attempt       = $absObj
        junction_escape_guard      = $juncObj
        junction_escape_server     = $srvJuncObj
    }
    $t4Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-MCP-004.json") -Encoding UTF8
    $results["T-7A-MCP-004"] = $t4Evidence.status
    Write-Host "[T-7A-MCP-004] Resultado: $($t4Evidence.status)" -ForegroundColor ($(if ($t4Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-MCP-005: Caida y Recuperacion de Servidor MCP
    # ==========================================================================
    Write-Host "`n[T-7A-MCP-005] Ejecutando prueba de caida de proceso MCP y recuperacion..." -ForegroundColor Yellow

    # 1. Start a live MCP stdio process and verify it is running
    $psiMcp = New-Object System.Diagnostics.ProcessStartInfo
    $psiMcp.FileName = $pythonExe
    $psiMcp.Arguments = "`"$mcpServerPy`""
    $psiMcp.RedirectStandardInput = $true
    $psiMcp.RedirectStandardOutput = $true
    $psiMcp.RedirectStandardError = $true
    $psiMcp.UseShellExecute = $false
    $psiMcp.CreateNoWindow = $true
    $liveMcpProc = [System.Diagnostics.Process]::Start($psiMcp)
    $killedPid = $liveMcpProc.Id
    $spawnedPids.Add($killedPid)

    # Send initialize request to prove it's alive
    $initReq = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"crash-test","version":"1.0"}}}'
    $liveMcpProc.StandardInput.WriteLine($initReq)
    $liveMcpProc.StandardInput.Flush()
    $initReplyLine = $liveMcpProc.StandardOutput.ReadLine()
    $initReplyObj = $initReplyLine | ConvertFrom-Json

    # 2. Abruptly kill the MCP server process mid-session
    Stop-Process -Id $killedPid -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 300
    $isDeadAfterKill = -not (Get-Process -Id $killedPid -ErrorAction SilentlyContinue)

    # 3. Verify health check against unavailable endpoint reports structured UNAVAILABLE without hanging
    $missingScriptPath = Join-Path $sandboxDir "non-existent-mcp-server.py"
    $downHealthRaw = & $guardScript -Action TestMcpHealth -McpServerName "da_local_sandbox" -McpServerScriptOverride $missingScriptPath -TimeoutSeconds 5
    $downHealthObj = ($downHealthRaw -join "`n") | ConvertFrom-Json

    # 4. Reconnect / recover using the primary MCP server and verify full health and tool execution
    $recoveredHealthRaw = & $guardScript -Action TestMcpHealth -McpServerName "da_local_sandbox" -TimeoutSeconds 15
    $recoveredHealthObj = ($recoveredHealthRaw -join "`n") | ConvertFrom-Json

    $recoveredEchoRaw = & $guardScript -Action InvokeMcpTool -McpServerName "da_local_sandbox" -McpToolName "da_echo" -ArgumentsJson '{"message":"Recovered after crash"}' -TimeoutSeconds 15
    $recoveredEchoObj = ($recoveredEchoRaw -join "`n") | ConvertFrom-Json

    $hermesRetestOut = (& $hermesExe -p desarrollador-autonomo mcp test da_local_sandbox 2>&1 | Out-String).Trim()

    $t5Pass = (
        ($null -ne $initReplyObj.result.serverInfo) -and
        ($isDeadAfterKill -eq $true) -and
        ($downHealthObj.health_state -eq "UNAVAILABLE") -and
        ($downHealthObj.decision -eq "DENY") -and
        ($recoveredHealthObj.health_state -eq "HEALTHY") -and
        ($recoveredEchoObj.status -eq "OK") -and
        ($recoveredEchoObj.result.echo -eq "Recovered after crash") -and
        ($hermesRetestOut -match "Connected")
    )

    $t5Evidence = [ordered]@{
        test_id                  = "T-7A-MCP-005"
        name                     = "MCP Server Process Crash Handling and Recovery"
        status                   = if ($t5Pass) { "PASS" } else { "FAIL" }
        timestamp                = (Get-Date).ToString("o")
        initial_live_pid         = $killedPid
        initial_handshake_ok     = ($null -ne $initReplyObj.result.serverInfo)
        process_terminated_clean = $isDeadAfterKill
        unavailable_state_probe  = $downHealthObj
        recovered_health_probe   = $recoveredHealthObj
        recovered_tool_call      = $recoveredEchoObj
        hermes_cli_retest        = $hermesRetestOut
    }
    $t5Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-MCP-005.json") -Encoding UTF8
    $results["T-7A-MCP-005"] = $t5Evidence.status
    Write-Host "[T-7A-MCP-005] Resultado: $($t5Evidence.status)" -ForegroundColor ($(if ($t5Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-PLUGIN-001: Integracion + Integridad Criptografica (SHA-256)
    # ==========================================================================
    Write-Host "`n[T-7A-PLUGIN-001] Ejecutando prueba de integracion e integridad criptografica de plugin..." -ForegroundColor Yellow

    # Case A: Intact approved plugin
    $intactVerifyRaw = & $guardScript -Action VerifyPluginIntegrity
    $intactVerifyObj = ($intactVerifyRaw -join "`n") | ConvertFrom-Json

    $pluginDoctorOut = (& $hermesExe -p desarrollador-autonomo plugins doctor desarrollador-autonomo-health 2>&1 | Out-String).Trim()
    $pluginValidateOut = (& $hermesExe -p desarrollador-autonomo plugins validate "C:\Users\Pc\AppData\Local\hermes\profiles\desarrollador-autonomo\plugins\desarrollador-autonomo-health" 2>&1 | Out-String).Trim()

    $pluginExecRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"read_health"}'
    $pluginExecObj = ($pluginExecRaw -join "`n") | ConvertFrom-Json

    # Case B: Tamper with plugin __init__.py without updating security.yaml -> PLUGIN_INTEGRITY_MISMATCH / DENY
    $tamperedContent = [System.Text.Encoding]::UTF8.GetString($originalPluginInitBytes) + "`n# TAMPERED_UNAPPROVED_CHANGE`n"
    [System.IO.File]::WriteAllText($profilePluginInit, $tamperedContent, (New-Object System.Text.UTF8Encoding($false)))

    $tamperVerifyRaw = & $guardScript -Action VerifyPluginIntegrity
    $tamperVerifyObj = ($tamperVerifyRaw -join "`n") | ConvertFrom-Json

    $tamperExecRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"read_health"}'
    $tamperExecObj = ($tamperExecRaw -join "`n") | ConvertFrom-Json

    $tamperHermesInvoke = & $invokeHermesScript -Prompt "Check health" -SkipLock

    # Restore original plugin byte-for-byte immediately
    [System.IO.File]::WriteAllBytes($profilePluginInit, $originalPluginInitBytes)
    $restoredVerifyRaw = & $guardScript -Action VerifyPluginIntegrity
    $restoredVerifyObj = ($restoredVerifyRaw -join "`n") | ConvertFrom-Json

    # Case C: Legitimate update flow in sandbox (new hash registered in sandbox security.yaml)
    $sandboxPluginUpdateDir = Join-Path $sandboxDir "plugin-update-test"
    New-Item -ItemType Directory -Path $sandboxPluginUpdateDir -Force | Out-Null
    $updatedPluginPy = Join-Path $sandboxPluginUpdateDir "__init__.py"
    $legitUpdatedContent = [System.Text.Encoding]::UTF8.GetString($originalPluginInitBytes) + "`n# LEGITIMATE_APPROVED_PLUGIN_UPDATE_V1_0_1`n"
    [System.IO.File]::WriteAllText($updatedPluginPy, $legitUpdatedContent, (New-Object System.Text.UTF8Encoding($false)))
    $newApprovedSha = (Get-FileHash -LiteralPath $updatedPluginPy -Algorithm SHA256).Hash.ToLowerInvariant()

    $origSecText = Get-Content -LiteralPath (Join-Path $infraRoot "config\security.yaml") -Raw -Encoding UTF8
    $oldShaStr = [string]$intactVerifyObj.approved_sha256
    $updatedSecText = $origSecText -replace [regex]::Escape($oldShaStr), [string]$newApprovedSha
    $sandboxSecYaml = Join-Path $sandboxPluginUpdateDir "security-updated.yaml"
    [System.IO.File]::WriteAllText($sandboxSecYaml, $updatedSecText, (New-Object System.Text.UTF8Encoding($false)))

    $legitVerifyRaw = & $guardScript -Action VerifyPluginIntegrity -SecurityYamlPath $sandboxSecYaml -PluginEntrypointOverride $updatedPluginPy
    $legitVerifyObj = ($legitVerifyRaw -join "`n") | ConvertFrom-Json

    Remove-Item -LiteralPath $sandboxPluginUpdateDir -Recurse -Force -ErrorAction SilentlyContinue

    $t6Pass = (
        ($intactVerifyObj.status -eq "PASS") -and
        ($intactVerifyObj.decision -eq "ALLOW") -and
        ($intactVerifyObj.approved_sha256 -eq $intactVerifyObj.runtime_sha256) -and
        ($pluginDoctorOut -match "OK: runtime discovery, manifest parsing, import, and registration passed") -and
        ($pluginValidateOut -match "Validation passed") -and
        ($pluginExecObj.status -eq "HEALTHY") -and
        ($pluginExecObj.decision -eq "ALLOW") -and
        ($tamperVerifyObj.status -eq "PLUGIN_INTEGRITY_MISMATCH") -and
        ($tamperVerifyObj.decision -eq "DENY") -and
        ($tamperExecObj.status -eq "PLUGIN_INTEGRITY_MISMATCH") -and
        ($tamperExecObj.decision -eq "DENY") -and
        ($tamperHermesInvoke.Status -eq "PLUGIN_INTEGRITY_MISMATCH") -and
        ($tamperHermesInvoke.Decision -eq "DENY") -and
        ($restoredVerifyObj.status -eq "PASS") -and
        ($restoredVerifyObj.runtime_sha256 -eq $intactVerifyObj.approved_sha256) -and
        ($legitVerifyObj.status -eq "PASS") -and
        ($legitVerifyObj.decision -eq "ALLOW") -and
        ($legitVerifyObj.runtime_sha256 -eq $newApprovedSha)
    )

    $t6Evidence = [ordered]@{
        test_id                         = "T-7A-PLUGIN-001"
        name                            = "Plugin Integration and Cryptographic SHA-256 Integrity Verification"
        status                          = if ($t6Pass) { "PASS" } else { "FAIL" }
        timestamp                       = (Get-Date).ToString("o")
        case_a_intact_verification      = $intactVerifyObj
        case_a_hermes_plugins_doctor    = $pluginDoctorOut
        case_a_hermes_plugins_validate  = $pluginValidateOut
        case_a_tool_execution           = $pluginExecObj
        case_b_tampered_guard_verify    = $tamperVerifyObj
        case_b_tampered_tool_invoke     = $tamperExecObj
        case_b_tampered_hermes_launcher = [ordered]@{
            Status               = $tamperHermesInvoke.Status
            Decision             = $tamperHermesInvoke.Decision
            PluginIntegrity      = $tamperHermesInvoke.PluginIntegrity
            ApprovedPluginSha256 = $tamperHermesInvoke.ApprovedPluginSha256
            RuntimePluginSha256  = $tamperHermesInvoke.RuntimePluginSha256
            ExitCode             = $tamperHermesInvoke.ExitCode
        }
        case_b_restored_verification    = $restoredVerifyObj
        case_c_legitimate_update_flow   = $legitVerifyObj
    }
    $t6Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-PLUGIN-001.json") -Encoding UTF8
    $results["T-7A-PLUGIN-001"] = $t6Evidence.status
    Write-Host "[T-7A-PLUGIN-001] Resultado: $($t6Evidence.status)" -ForegroundColor ($(if ($t6Pass) { "Green" } else { "Red" }))

    # ==========================================================================
    # T-7A-PLUGIN-002: Seguridad (PLUGIN != PRIVILEGE ESCALATION)
    # ==========================================================================
    Write-Host "`n[T-7A-PLUGIN-002] Ejecutando prueba de seguridad de plugin (PLUGIN != PRIVILEGE ESCALATION)..." -ForegroundColor Yellow

    # 1. Blocked command attempt (git push --force)
    $pCmdRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"git push --force"}'
    $pCmdObj = ($pCmdRaw -join "`n") | ConvertFrom-Json

    # 2. Protected path modification attempt (config/security.yaml)
    $pProtRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"modify_security_yaml","target_path":"config/security.yaml"}'
    $pProtObj = ($pProtRaw -join "`n") | ConvertFrom-Json

    # 3. Outside workspace path attempt (C:\Windows\System32\cmd.exe)
    $pOutRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"read_health","target_path":"C:\\Windows\\System32\\cmd.exe"}'
    $pOutObj = ($pOutRaw -join "`n") | ConvertFrom-Json

    # 4. Relative path traversal attempt (..\..\Outside\secret.txt)
    $pTravRaw = & $guardScript -Action InvokePluginTool -ArgumentsJson '{"requested_action":"read_health","target_path":"..\\..\\Outside\\secret.txt"}'
    $pTravObj = ($pTravRaw -join "`n") | ConvertFrom-Json

    # Verify frozen 7A.1 hook and security.yaml remain intact
    $postHookCheckRaw = & $memoryGuardScript -Action VerifyHookIntegrity
    $postHookCheck = ($postHookCheckRaw -join "`n") | ConvertFrom-Json

    $t7Pass = (
        ($pCmdObj.status -eq "SECURITY_BLOCKED") -and ($pCmdObj.decision -eq "DENY") -and
        ($pProtObj.status -eq "SECURITY_BLOCKED") -and ($pProtObj.decision -eq "DENY") -and
        ($pOutObj.status -eq "SECURITY_BLOCKED") -and ($pOutObj.decision -eq "DENY") -and
        ($pTravObj.status -eq "SECURITY_BLOCKED") -and ($pTravObj.decision -eq "DENY") -and
        ($postHookCheck.status -eq "PASS") -and ($postHookCheck.allowed -eq $true)
    )

    $t7Evidence = [ordered]@{
        test_id                        = "T-7A-PLUGIN-002"
        name                           = "Plugin Security Guardrail Enforcement (PLUGIN != PRIVILEGE ESCALATION)"
        status                         = if ($t7Pass) { "PASS" } else { "FAIL" }
        timestamp                      = (Get-Date).ToString("o")
        blocked_command_attempt        = $pCmdObj
        protected_config_attempt       = $pProtObj
        outside_workspace_path_attempt = $pOutObj
        path_traversal_attempt         = $pTravObj
        hook_7a1_integrity_preserved   = $postHookCheck
    }
    $t7Evidence | ConvertTo-Json -Depth 8 | Set-Content -Path (Join-Path $evidenceDir "T-7A-PLUGIN-002.json") -Encoding UTF8
    $results["T-7A-PLUGIN-002"] = $t7Evidence.status
    Write-Host "[T-7A-PLUGIN-002] Resultado: $($t7Evidence.status)" -ForegroundColor ($(if ($t7Pass) { "Green" } else { "Red" }))

} finally {
    Write-Host "`n[CLEANUP] Ejecutando limpieza garantizada de Subfase 7A.2..." -ForegroundColor Cyan

    # 1. Restore plugin __init__.py if modified
    if ($originalPluginInitBytes -and (Test-Path -LiteralPath $profilePluginInit)) {
        $currentBytes = [System.IO.File]::ReadAllBytes($profilePluginInit)
        $same = ($currentBytes.Length -eq $originalPluginInitBytes.Length)
        if ($same) {
            for ($i = 0; $i -lt $currentBytes.Length; $i++) {
                if ($currentBytes[$i] -ne $originalPluginInitBytes[$i]) { $same = $false; break }
            }
        }
        if (-not $same) {
            [System.IO.File]::WriteAllBytes($profilePluginInit, $originalPluginInitBytes)
        }
    }

    # 2. Remove any temporary NTFS junction in sandbox
    if (Test-Path -LiteralPath $junctionPath) {
        cmd.exe /c rmdir "$junctionPath" 2>&1 | Out-Null
    }

    # 3. Terminate any spawned MCP child processes owned by this verification
    foreach ($pidToKill in $spawnedPids) {
        if (Get-Process -Id $pidToKill -ErrorAction SilentlyContinue) {
            Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        }
    }

    Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match "mcp-sandbox-server\.py"
    } | ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
}

$remainingMcpProcs = @(Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -match "mcp-sandbox-server\.py"
}).Count

$allPass = ($results.Values | Where-Object { $_ -ne "PASS" }).Count -eq 0 -and ($results.Count -eq 7) -and ($remainingMcpProcs -eq 0)

$summary = [ordered]@{
    subphase                     = "7A.2"
    title                        = "Servidores MCP + Plugins / Custom Tools Gobernados"
    status                       = if ($allPass) { "PASS" } else { "FAIL" }
    timestamp                    = (Get-Date).ToString("o")
    tests                        = $results
    cleanup_verified             = ($remainingMcpProcs -eq 0)
    remaining_mcp_processes      = $remainingMcpProcs
    hook_7a1_sha256_preserved    = "49a28be99803169841c82b99e48573d966fe26e5a348228417cc94ad46a7573c"
    plugin_7a2_entrypoint_sha256 = "88516ba97a93fdc30a4eda9dfa72f3316d8e586ea2f664c5827ac10885de011e"
    plugin_7a2_manifest_sha256   = "f4838d484d99006183474da8aa496fc1e148174838f43b98574d4b7e1a100a3c"
    mcp_server_7a2_sha256        = "ab4c23e4c68dde352c63fbac9bef53dbdb747a411d52fb949d996413b20807c3"
}

$summaryPath = Join-Path $evidenceDir "phase-7a2-summary.json"
$summary | ConvertTo-Json -Depth 6 | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host " RESUMEN FINAL SUBFASE 7A.2: $($summary.status)" -ForegroundColor ($(if ($allPass) { "Green" } else { "Red" }))
Write-Host "==================================================================" -ForegroundColor Cyan
$summary | ConvertTo-Json -Depth 6 | Write-Output

if (-not $allPass) {
    exit 1
}
exit 0
