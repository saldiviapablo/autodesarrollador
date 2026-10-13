$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=Join-Path $PSHOME 'Modules'}
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1')
. (Join-Path $root 'runner/report.ps1')
. (Join-Path $root 'runner/cleanup.ps1')
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false;$reconciled=@();$ownedAlive=@();$remainingLocks=@()
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_STILL_ACTIVE'}
    $backup=Join-Path $root ('backups/final7b-stale-metadata-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff'))
    foreach($project in @(Get-ChildItem -LiteralPath (Join-Path $root 'sandbox') -Directory -Filter '7b-*')){
        $auto=Join-Path $project.FullName '.autopilot';$statePath=Join-Path $auto 'STATE.json'
        if(-not(Test-Path -LiteralPath $statePath)){continue}
        try{$state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json}catch{continue}
        # Only fixtures created by this task, never arbitrary user projects.
        if($state.objective -ne 'Implement correct addition with verified tests'){continue}
        $alive=@(Get-RunnerSurvivors $auto);$ownedAlive+=@($alive)
        $lockPath=Join-Path $auto 'LOCK.json'
        if(Test-Path -LiteralPath $lockPath){
            if($alive.Count){$remainingLocks+=@($lockPath);continue}
            $lock=Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8|ConvertFrom-Json
            if($lock.run_id -ne $state.run_id){$remainingLocks+=@($lockPath);continue}
            # Physical mutex is acquired: no original Runner can still own it.
            # Preserve the old metadata/state before reconciling the known test interruption.
            $copy=Join-Path $backup $project.Name;$null=New-Item -ItemType Directory -Path $copy -Force
            Copy-Item -LiteralPath $lockPath,$statePath -Destination $copy
            Remove-RunnerOwnedLock $auto $state.run_id $lock.owner_pid
            if($state.status -in @('RUNNING','RECOVERING')){
                $state.status='FAILED';$state.current_phase='RECOVERY_CLEANUP';$state.current_task='Previously interrupted test driver; kernel-owned processes already exited';$state.next_action='Historical failed attempt preserved; corrected test is separately evidenced'
                $null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
                $null=Update-AutopilotHeartbeat -AutopilotDir $auto -RunId $state.run_id -ProcessId $PID -Status 'FAILED' -CurrentTask $state.current_task
                $null=Write-RunnerReport -Project $project.FullName -RunId $state.run_id -State $state -Status 'FAILED' -Technical 'INTERRUPTED_TEST_DRIVER' -Reason $state.current_task -Duration 0 -Cleanup @{owned_survivors=@();stale_metadata_reconciled=$true;kernel_run_mutex_acquired=$true}
            }
            $reconciled+=@(@{project=$project.Name;run_id=$state.run_id;original_saved=$copy})
        }
    }
}finally{if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
$inference=Test-RunnerInferenceReleased
$processes=@(Get-CimInstance Win32_Process|Where-Object{
    ($_.Name -eq 'llama-server.exe' -and $_.ExecutablePath -eq 'C:\AI\llama.cpp\llama-server.exe') -or
    ($_.Name -match '^python.*\.exe$' -and $_.CommandLine -match 'hermes_cli.main|mcp-sandbox-server.py|governed-dashboard.py') -or
    ($_.Name -eq 'node.exe' -and $_.CommandLine -match 'qwen-code.+cli-entry.js|chatgpt-bridge.js') -or
    ($_.Name -eq 'powershell.exe' -and $_.CommandLine -match 'watchdog-monitor.ps1|runner[\\/]run.ps1|runner[\\/]agent-step.ps1') -or
    ($_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'HERMES-CHATGPT|phase7a4-browser')
})
$ports=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$_.LocalPort -in @(8080,9119,9222)})
$checks=@{own_processes_zero=($ownedAlive.Count -eq 0);auxiliary_processes_zero=($processes.Count -eq 0);own_locks_zero=($remainingLocks.Count -eq 0);ports_closed=($ports.Count -eq 0);inference_mutex_free=($inference -eq 'FREE');run_mutex_free=$held;bridge_lease_absent=(-not(Test-Path -LiteralPath (Join-Path $root 'runtime/chatgpt-consultations/browser-lease.json')))}
$report=@{status=$(if($checks.Values -notcontains $false){'PASS'}else{'FAIL'});checks=$checks;stale_test_metadata_reconciled=$reconciled;remaining_own_locks=$remainingLocks;process_pids=@($processes|ForEach-Object{$_.ProcessId});listening_ports=@($ports|ForEach-Object{$_.LocalPort});unknown_processes_killed=0;timestamp=[datetimeoffset]::Now.ToString('o')}
Write-RunnerJson (Join-Path $root 'evidence/regression-7b-final/cleanup.json') $report
$report|ConvertTo-Json -Depth 8
if($report.status -ne 'PASS'){throw 'FINAL_7B_CLEANUP_FAILED'}
