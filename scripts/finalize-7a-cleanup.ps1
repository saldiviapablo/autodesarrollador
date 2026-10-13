$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$evidence=Join-Path $root 'evidence/regression-7a-final'
. (Join-Path $root 'scripts/inference-lock.ps1')
$owner=Get-Content -LiteralPath (Join-Path $root 'runtime/macro7a-llama-owner.json') -Raw -Encoding UTF8|ConvertFrom-Json
$proc=Get-Process -Id $owner.pid -ErrorAction SilentlyContinue
$health=$null;$models=$null;$identityVerified=$false
if($proc){
    $actual=[datetimeoffset]$proc.StartTime;$recorded=[datetimeoffset]::Parse($owner.start_time)
    if($proc.Path -ne $owner.executable -or [Math]::Abs(($actual-$recorded).TotalMilliseconds) -gt 1){throw 'BLOCKED_REQUIRES_HUMAN: owned llama PID identity changed'}
    $command=(Get-CimInstance Win32_Process -Filter ('ProcessId='+$owner.pid)).CommandLine
    if($command -notmatch '--ctx-size\s+65536' -or $command -notmatch '--parallel\s+1' -or $command -notmatch '--alias\s+qwen36'){throw 'LLAMA_PARAMETER_REGRESSION'}
    $identityVerified=$true
    $health=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/health' -TimeoutSec 5
    $models=Invoke-RestMethod -Uri 'http://127.0.0.1:8080/v1/models' -TimeoutSec 5
    if($health.status -ne 'ok' -or @($models.data.id) -notcontains 'qwen36'){throw 'LIVE_MODEL_HEALTH_REGRESSION'}
    Stop-Process -Id $proc.Id -Force
    $null=$proc.WaitForExit(10000)
    if(-not $proc.HasExited){throw 'OWNED_LLAMA_CLEANUP_FAILED'}
}
$token=Acquire-InferenceLock -Owner 'final-regression-audit' -Purpose 'verify free mutex after all workers' -TimeoutSeconds 2 -InfraPath $root
if(-not $token.Acquired){throw 'INFERENCE_MUTEX_STILL_HELD'}
$null=Release-InferenceLock -LockToken $token
$metadata=Get-InferenceLockStatus -InfraPath $root
$auxiliary=@(Get-CimInstance Win32_Process | Where-Object {
    ($_.Name -match '^python.*\.exe$' -and $_.CommandLine -match 'mcp-sandbox-server.py|governed-dashboard.py|test-native-subagent.py') -or
    ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'chatgpt-bridge.js|qwen-code.+cli-entry.js') -or
    ($_.Name -eq 'agent-browser-win32-x64.exe' -and $_.CommandLine -match 'autopilot|phase7a') -or
    ($_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT|phase7a4-browser')
})
$ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object {$_.LocalPort -in @(8080,9119,9222)})
$lease=Test-Path -LiteralPath (Join-Path $root 'runtime/chatgpt-consultations/browser-lease.json')
$temporaries=@(Get-ChildItem -LiteralPath (Join-Path $root 'runtime/chatgpt-consultations') -Filter '*.tmp' -File -ErrorAction SilentlyContinue)
$jobReady=@(Get-ChildItem -LiteralPath (Join-Path $root 'runtime/dashboard-jobs') -File -ErrorAction SilentlyContinue)+@(Get-ChildItem -LiteralPath (Join-Path $root 'runtime/browser-jobs') -File -ErrorAction SilentlyContinue)
$checks=@{owned_llama_stopped=(-not(Get-Process -Id $owner.pid -ErrorAction SilentlyContinue));live_identity_verified_before_stop=$identityVerified;health_and_model_alias_before_stop=($health.status -eq 'ok');auxiliary_processes_zero=($auxiliary.Count -eq 0);ports_closed=($ports.Count -eq 0);mutex_free_and_released=($metadata.Status -eq 'RELEASED');browser_lease_absent=(-not $lease);ledger_temp_files_zero=($temporaries.Count -eq 0);job_ready_files_zero=($jobReady.Count -eq 0)}
$result=@{status=$(if($checks.Values -notcontains $false){'PASS'}else{'FAIL'});checks=$checks;owned_llama_pid=$owner.pid;unknown_processes_killed=0;health_before_stop=$health;auxiliary_pids=@($auxiliary|ForEach-Object{$_.ProcessId});listening_ports=@($ports|ForEach-Object{$_.LocalPort});timestamp=(Get-Date).ToString('o')}
$result|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $evidence 'cleanup.json') -Encoding UTF8
$result|ConvertTo-Json -Depth 10
if($result.status -ne 'PASS'){throw 'FINAL_CLEANUP_GATE_FAILED'}
