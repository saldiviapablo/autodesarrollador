[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$prompt='Use the native browser_navigate tool to open https://docs.python.org/3/library/json.html and use browser_snapshot. Do not use terminal or shell for browsing. Confirm the page title includes JSON and answer exactly NATIVE_BROWSER_HERMES_INTEGRATION_OK. This is read-only documentation research.'
$result=& (Join-Path $root 'scripts/invoke-hermes.ps1') -Prompt $prompt -Mode chat-stream-json -MaxTurns 5 -WorkingDir (Join-Path $root 'sandbox/phase7a4-browser') -TimeoutSeconds 240
$result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $root 'evidence/phase-7a4/hermes-live-integration.json') -Encoding UTF8
$passed=$result.ExitCode -eq 0 -and $result.Stdout.Contains('browser_navigate') -and $result.Stdout.Contains('NATIVE_BROWSER_HERMES_INTEGRATION_OK')
[ordered]@{test_id='T-7A-BROWSER-005';status=$(if($passed){'PASS'}else{'FAIL'});exit_code=$result.ExitCode;timed_out=$result.TimedOut;duration=$result.Duration;hook_integrity=$result.HookIntegrity;plugin_integrity=$result.PluginIntegrity;native_browser_called=$result.Stdout.Contains('browser_navigate');success_marker=$result.Stdout.Contains('NATIVE_BROWSER_HERMES_INTEGRATION_OK')}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'evidence/phase-7a4/T-7A-BROWSER-005.json') -Encoding UTF8
$result|Select-Object Status,ExitCode,TimedOut,Duration,HookIntegrity,PluginIntegrity,Stderr|ConvertTo-Json -Depth 5
if(-not $passed){exit 1}
