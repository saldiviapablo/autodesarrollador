[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$EvidencePath)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
function Parse-Smoke($Value) { return (($Value -join "`n") | ConvertFrom-Json) }
$checks=[ordered]@{}
$hook=Parse-Smoke (& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action VerifyHookIntegrity)
$checks['hook_sha256']=($hook.allowed -and $hook.status -eq 'PASS')
$fake='sk-'+('X'*25)
$san=Parse-Smoke (& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action SanitizeText -Text $fake)
$checks['secret_sanitization']=($san.was_modified -and $san.sanitized_text -eq '[REDACTED]')
$health=Parse-Smoke (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action TestMcpHealth)
$checks['mcp_health']=($health.health_state -eq 'HEALTHY')
$allow=Parse-Smoke (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action CheckMcpToolCall -McpToolName da_echo)
$deny=Parse-Smoke (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action CheckMcpToolCall -McpToolName da_forbidden_test)
$checks['mcp_allowlist']=($allow.allowed -and -not $deny.allowed)
$plugin=Parse-Smoke (& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action VerifyPluginIntegrity)
$checks['plugin_sha256']=($plugin.allowed -and $plugin.status -eq 'PASS')
$node=Parse-Smoke (& node (Join-Path $root 'tests/test-chatgpt-domain-lock.js'))
$checks['chatgpt_exact_domain']=($node.status -eq 'PASS')
# Reuse the REAL UTF-8/consultation smoke only while its implementation is unchanged.
$protectedBridge=@('tools/chatgpt-bridge.js','scripts/consultar-chatgpt.ps1','scripts/chatgpt-domain-policy.ps1','scripts/start-hermes-chatgpt.ps1')
$bridgeDiff=@(& git -C $root diff f133bab -- $protectedBridge)
$real=Get-Content -LiteralPath (Join-Path $root 'evidence/preflight-7a-correction-20261013/chatgpt-real-consultation.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$utf8=Get-Content -LiteralPath (Join-Path $root 'evidence/preflight-7a-correction-20261013/chatgpt-utf8-roundtrip.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$checks['unchanged_bridge_real_smoke']=($bridgeDiff.Count -eq 0 -and $real.status -eq 'PASS' -and $utf8.status -eq 'PASS')
$remaining=@(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python.*\.exe$' -and $_.CommandLine -match 'mcp-sandbox-server.py' })
$checks['mcp_cleanup']=($remaining.Count -eq 0)
$passed=@($checks.Values | Where-Object { -not $_ }).Count -eq 0
$report=[ordered]@{status=$(if($passed){'PASS'}else{'FAIL'});timestamp=(Get-Date).ToString('o');checks=$checks;local_inferences=0;full_7a1_7a2_suites_rerun=$false;real_utf8_evidence='evidence/preflight-7a-correction-20261013';bridge_baseline_commit='f133bab';real_smoke_repeated=$false}
$parent=Split-Path -Parent $EvidencePath
if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
$report | ConvertTo-Json -Depth 8
if (-not $passed) { exit 1 }
