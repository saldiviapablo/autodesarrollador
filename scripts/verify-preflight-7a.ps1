[CmdletBinding()]
param([string]$EvidenceDir = '')
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$root = Split-Path -Parent $PSScriptRoot
if (-not $EvidenceDir) { $EvidenceDir = Join-Path $root ('evidence/preflight-7a-' + (Get-Date -Format 'yyyyMMdd-HHmmss')) }
New-Item -ItemType Directory -Path $EvidenceDir -Force | Out-Null
$EvidenceDir = (Resolve-Path -LiteralPath $EvidenceDir).Path
. (Join-Path $root 'scripts/state-manager.ps1')
$autopilot = Join-Path $root 'sandbox/preflight-7a/.autopilot'
$checks = [ordered]@{}
$failure = $null
$beforeChrome = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT' })
$ownedChrome = @()
$cleanupOk = $false
function Save-Check([string]$Name, $Data, [bool]$Passed) {
    $checks[$Name] = $(if ($Passed) { 'PASS' } else { 'FAIL' })
    [ordered]@{ check_id=$Name; status=$checks[$Name]; timestamp=(Get-Date).ToString('o'); data=$Data } |
        ConvertTo-Json -Depth 20 | Set-Content -LiteralPath (Join-Path $EvidenceDir ($Name + '.json')) -Encoding UTF8
    Write-Host "$Name = $($checks[$Name])"
    if (-not $Passed) { throw "MANDATORY_TEST_FAILED: $Name" }
}
function Parse-Guard($Raw) { return (($Raw -join "`n") | ConvertFrom-Json) }
function Update-PreflightState([string]$Status, [string]$Next) {
    if (Test-Path -LiteralPath (Join-Path $autopilot 'STATE.json')) {
        $state = Get-Content -LiteralPath (Join-Path $autopilot 'STATE.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $state.status = $Status
        $state.current_phase = 'PREFLIGHT_7A_CONTINUATION'
        $state.current_task = 'Verificacion de preflight y regression smoke acotado'
        $state.next_action = $Next
        $state.tests.status = $(if ($Status -eq 'COMPLETED') { 'PASS' } elseif ($Status -eq 'FAILED') { 'FAIL' } else { 'RUNNING' })
        $state.tests.last_command = 'scripts/verify-preflight-7a.ps1'
        $state.tests.last_run_at = (Get-Date).ToString('o')
        $null = Write-AtomicState -StateObj $state -AutopilotDir $autopilot -ValidateTransition $false
        $null = Add-AutopilotEvent -AutopilotDir $autopilot -RunId $state.run_id -Actor 'preflight-verifier' -Type 'TEST' -Payload @{status=$Status;checks=$checks;evidence=$EvidenceDir}
    }
}
try {
    Update-PreflightState 'RUNNING' 'Completar smokes antes de iniciar 7A.3'
    $domainNode = (& node (Join-Path $root 'tests/test-chatgpt-domain-lock.js') | Out-String) | ConvertFrom-Json
    Save-Check 'domain-node' $domainNode ($domainNode.status -eq 'PASS')
    $domainPs = (& (Join-Path $root 'tests/test-chatgpt-domain-lock.ps1') | Out-String) | ConvertFrom-Json
    Save-Check 'domain-powershell' $domainPs ($domainPs.status -eq 'PASS')
    $hook = Parse-Guard (& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action VerifyHookIntegrity)
    Save-Check 'hook-sha256' $hook ($hook.status -eq 'PASS' -and $hook.allowed)
    $fake = 'sk-' + ('X' * 25)
    $sanitized = Parse-Guard (& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action SanitizeText -Text ('preflight ' + $fake + ' password=synthetic-only-7a'))
    Save-Check 'secret-sanitization' $sanitized ($sanitized.was_modified -and $sanitized.sanitized_text -notmatch [regex]::Escape($fake) -and $sanitized.sanitized_text -notmatch 'synthetic-only-7a' -and $sanitized.sanitized_text -match '\[REDACTED\]')
    $health = Parse-Guard (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action TestMcpHealth)
    Save-Check 'mcp-health' $health ($health.health_state -eq 'HEALTHY')
    $allow = Parse-Guard (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action CheckMcpToolCall -McpToolName da_echo)
    $deny = Parse-Guard (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action CheckMcpToolCall -McpToolName da_forbidden_test)
    Save-Check 'mcp-allowlist' @{allowed=$allow;denied=$deny} ($allow.allowed -and -not $deny.allowed -and $deny.decision -eq 'DENY')
    $plugin = Parse-Guard (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action VerifyPluginIntegrity)
    Save-Check 'plugin-sha256' $plugin ($plugin.status -eq 'PASS' -and $plugin.allowed)

    # Never adopt an unknown CDP endpoint or preexisting personal browser.
    $listener = Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue
    if ($listener -and @($beforeChrome | Where-Object { $_.ProcessId -in $listener.OwningProcess }).Count -eq 0) {
        throw 'BLOCKED_REQUIRES_HUMAN: CDP endpoint ownership unknown'
    }
    if ($beforeChrome.Count -gt 0) { throw 'BLOCKED_REQUIRES_HUMAN: Dedicated browser already in use; preserve existing session' }

    $session = $null
    for ($attempt = 0; $attempt -lt 6; $attempt++) {
        $session = & (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action check-session -TimeoutSeconds 25
        $ownedChrome = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT' -and $_.ProcessId -notin $beforeChrome.ProcessId })
        if ($session.Status -eq 'BLOCKED_REQUIRES_HUMAN_LOGIN') { throw 'BLOCKED_REQUIRES_HUMAN: Dedicated ChatGPT profile needs manual login' }
        if ($session.Status -eq 'SUCCESS' -and $session.ResultObj.session_ready) { break }
        if ($session.Status -eq 'DOMAIN_BLOCKED') { throw 'SECURITY_REGRESSION: Runtime domain outside policy' }
        Start-Sleep -Seconds 2
    }
    Save-Check 'chatgpt-real-session' $session.ResultObj ($session.Status -eq 'SUCCESS' -and $session.ResultObj.session_ready -and $session.ResultObj.url -match '^https://chatgpt\.com/')
    $unicode = "Prueba UTF-8:`náéíóú ÁÉÍÓÚ`nñ Ñ`n¿Dónde está?`n¡Funciona!`n— € °"
    $roundtrip = & (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action unicode-roundtrip -Question $unicode -TimeoutSeconds 25
    Save-Check 'chatgpt-utf8-roundtrip' $roundtrip.ResultObj ($roundtrip.Status -eq 'SUCCESS' -and $roundtrip.SourceTextEqualsDomText)
    $marker = 'PREFLIGHT_7A_REAL_' + (Get-Date -Format 'yyyyMMddHHmmss')
    $prompt = "Prueba técnica del bridge. Respondé exactamente con estas dos líneas:`n$marker`náéíóú ñ ¿sí?"
    $real = & (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $prompt -RawPrompt -ConsultationId $marker -TimeoutSeconds 60
    Save-Check 'chatgpt-real-consultation' $real.ResultObj ($real.Status -eq 'SUCCESS' -and $real.ResultObj.source -eq 'chatgpt_web_real' -and $real.ResultObj.message_sent -and $real.SourceTextEqualsDomText -and $real.Response.Contains($marker) -and $real.Response.Contains('áéíóú ñ ¿sí?'))
} catch {
    $failure = $_.Exception.Message
    Write-Host $failure
} finally {
    $ownedChrome = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT' -and $_.ProcessId -notin $beforeChrome.ProcessId })
    if ($ownedChrome.Count -gt 0) {
        try { $null = & (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action close-browser -TimeoutSeconds 8 } catch {}
        foreach ($owner in $ownedChrome) {
            $current = Get-CimInstance Win32_Process -Filter ("ProcessId = " + $owner.ProcessId)
            if ($current -and $current.CreationDate -eq $owner.CreationDate -and $current.CommandLine -match 'HERMES-CHATGPT') {
                $null = & taskkill.exe /PID $owner.ProcessId /T /F 2>&1
            }
        }
    }
    $remainingChrome = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT' -and $_.ProcessId -notin $beforeChrome.ProcessId })
    $remainingMcp = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python.*\.exe$' -and $_.CommandLine -match 'mcp-sandbox-server.py' })
    $cleanupOk = ($remainingChrome.Count -eq 0 -and $remainingMcp.Count -eq 0)
    $checks['cleanup'] = $(if ($cleanupOk) { 'PASS' } else { 'FAIL' })
    $status = $(if (-not $failure -and $cleanupOk) { 'PASS' } else { 'FAIL' })
    $summary = [ordered]@{gate='PREFLIGHT_7A_CONTINUATION';status=$status;timestamp=(Get-Date).ToString('o');checks=$checks;failure=$failure;cleanup_ok=$cleanupOk;remaining_chrome=$remainingChrome.Count;remaining_mcp=$remainingMcp.Count;local_inferences=0;idempotency_test_run=$false;full_7a1_7a2_suites_rerun=$false}
    $summary | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath (Join-Path $EvidenceDir 'smoke-summary.json') -Encoding UTF8
    Update-PreflightState $(if ($status -eq 'PASS') { 'COMPLETED' } elseif ($failure -match 'BLOCKED_REQUIRES_HUMAN') { 'BLOCKED_REQUIRES_HUMAN' } else { 'FAILED' }) $(if ($status -eq 'PASS') { 'Verificar documentación y commit correctivo antes de 7A.3' } else { 'Resolver bloqueo registrado en smoke-summary.json; no iniciar 7A.3' })
    $summary | ConvertTo-Json -Depth 15
}
if ($failure -or -not $cleanupOk) { exit 1 }
