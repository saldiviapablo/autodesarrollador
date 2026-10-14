$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
$e=Join-Path $root 'evidence/hermes-prompt-transport-20261014'
$checks=@{}
$hook=(& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action VerifyHookIntegrity)|ConvertFrom-Json
$checks.hook_sha256=($hook.allowed -and $hook.status -eq 'PASS')
$plugin=(& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action VerifyPluginIntegrity)|ConvertFrom-Json
$checks.plugin_sha256=($plugin.allowed -and $plugin.status -eq 'PASS')
$sanitized=(& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action SanitizeText -Text 'api_key=synthetic_transport_probe_123456789')|ConvertFrom-Json
$checks.secret_sanitization=($sanitized|ConvertTo-Json -Compress) -notmatch 'synthetic_transport_probe_123456789'
# Native invocation through the unchanged worker wrapper, with no model call.
$worker=& (Join-Path $root 'scripts/invoke-qwen-code.ps1') -ExtraArgs @('--version') -TimeoutSeconds 30
$checks.qwen_worker_invocation=($worker.Success -and $worker.ExitCode -eq 0 -and $worker.Stdout -match '0\.25\.1')
. (Join-Path $root 'scripts/inference-lock.ps1')
$lease=Acquire-InferenceLock -Owner 'transport-regression-parent' -TimeoutSeconds 5 -InfraPath $root
if(-not $lease.Acquired){throw 'MANDATORY_TEST_FAILED: INFERENCE_LOCK_PARENT'}
try{
    $child="`$env:PSModulePath=Join-Path `$PSHOME 'Modules';[Console]::OutputEncoding=[Text.Encoding]::UTF8;. '"+(Join-Path $root 'scripts/inference-lock.ps1')+"';`$lease=Acquire-InferenceLock -Owner 'transport-regression-child' -TimeoutSeconds 1 -InfraPath '"+$root+"';@{acquired=`$lease.Acquired;status=`$lease.Status}|ConvertTo-Json -Compress;if(`$lease.Acquired){`$null=Release-InferenceLock -LockToken `$lease}"
    $encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($child))
    $lockResult=(& powershell.exe -NoProfile -NonInteractive -EncodedCommand $encoded)|ConvertFrom-Json
    $checks.inference_lock_cross_process=(-not $lockResult.acquired -and $lockResult.status -match 'TIMEOUT')
}finally{$null=Release-InferenceLock -LockToken $lease}
$free=Acquire-InferenceLock -Owner 'transport-regression-cleanup' -TimeoutSeconds 1 -InfraPath $root
$checks.inference_lock_released=$free.Acquired
if($free.Acquired){$null=Release-InferenceLock -LockToken $free}
$complex=Get-Content -LiteralPath (Join-Path $e 'complex-transport.json') -Raw -Encoding UTF8|ConvertFrom-Json
$checks.supervisor_transport=($complex.status -eq 'PASS' -and @($complex.results|Where-Object{$_.role -eq 'supervisor' -and $_.PROMPT_INTEGRITY}).Count -eq 1)
$checks.UTF8=($complex.UTF8 -eq 'PASS')
$live=Get-Content -LiteralPath (Join-Path $e 'f23-reviewer-continuation.json') -Raw -Encoding UTF8|ConvertFrom-Json
$checks.reviewer_isolation=$live.reviewer_isolation
$checks.cleanup=($live.cleanup.job_closed -and $live.cleanup.run_lock_removed -and $live.cleanup.run_mutex_released -and $live.cleanup.inference_mutex -eq 'FREE' -and @($live.cleanup.errors).Count -eq 0 -and @($live.cleanup.owned_survivors).Count -eq 0)
$result=@{status=$(if(@($checks.Values|Where-Object{-not $_}).Count){'FAIL'}else{'PASS'});checks=$checks;hook=$hook;plugin=$plugin;worker=$worker;lock_contender=$lockResult;new_dependencies=@();local_inferences=0}
[IO.File]::WriteAllText((Join-Path $e 'regression-smoke.json'),($result|ConvertTo-Json -Depth 14),(New-Object Text.UTF8Encoding($false)))
$result|ConvertTo-Json -Depth 4
if($result.status -ne 'PASS'){throw 'MANDATORY_TEST_FAILED: TRANSPORT_REGRESSION_SMOKE'}
