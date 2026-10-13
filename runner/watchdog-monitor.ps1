param([string]$ProjectRoot,[int]$ParentId,[long]$ParentStartTicks,[int]$StaleSeconds=120)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=Join-Path $PSHOME 'Modules'}
. (Join-Path $PSScriptRoot 'core.ps1')
. (Join-Path $PSScriptRoot 'report.ps1')
. (Join-Path $PSScriptRoot 'cleanup.ps1')
$auto=Join-Path $ProjectRoot '.autopilot';$signal=Join-Path $auto 'WATCHDOG-SIGNAL.json'
$lastGood=[datetimeoffset]::Now;$reason='PARENT_PROCESS_LOST'
while($true){
    $parent=Get-Process -Id $ParentId -ErrorAction SilentlyContinue
    if(-not $parent -or $parent.StartTime.ToUniversalTime().Ticks -ne $ParentStartTicks){break}
    $age=([datetimeoffset]::Now-$lastGood).TotalSeconds
    try{
        $hb=Get-Content -LiteralPath (Join-Path $auto 'HEARTBEAT.json') -Raw -Encoding UTF8|ConvertFrom-Json
        if($hb.status -ne 'RUNNING'){exit 0}
        $lastGood=[datetimeoffset]::Parse($hb.timestamp);$age=([datetimeoffset]::Now-$lastGood).TotalSeconds
        Write-RunnerJson (Join-Path $auto 'WATCHDOG.json') @{parent_pid=$ParentId;heartbeat_age=$age;monitor='WATCHDOG';timestamp=[datetimeoffset]::Now.ToString('o')}
    }catch{}
    if($age -gt $StaleSeconds){
        $reason='HEARTBEAT_STALE'
        Write-RunnerJson $signal @{kind=$reason;age_seconds=$age;parent_pid=$ParentId;start_ticks=$ParentStartTicks}
        Start-Sleep -Milliseconds 300
        $again=Get-Process -Id $ParentId -ErrorAction SilentlyContinue
        if($again -and $again.StartTime.ToUniversalTime().Ticks -eq $ParentStartTicks){Stop-Process -Id $ParentId -Force}
    }
    Start-Sleep -Milliseconds 500
}
# Guardian survives its parent only long enough for bounded finalization.
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$acquired=$false
try{
    try{$acquired=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$acquired=$true}
    if(-not $acquired){exit 0} # A newly admitted run owns recovery; never overwrite it.
    $info=Get-RunnerAdmission inspect $ProjectRoot
    $lockPath=Join-Path $auto 'LOCK.json'
    if(Test-Path -LiteralPath $lockPath){$old=Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8|ConvertFrom-Json;if($old.owner_pid -ne $ParentId){exit 0}}
    $state=Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
    if($state.status -notin @('RUNNING','RECOVERING')){exit 0}
    $deadline=[datetimeoffset]::Now.AddSeconds(5)
    do{$alive=@(Get-RunnerSurvivors $auto $PID);if($alive.Count){Start-Sleep -Milliseconds 100}}while($alive.Count -and [datetimeoffset]::Now -lt $deadline)
    $state.status='FAILED';$state.current_phase='WATCHDOG_FAILOVER';$state.current_task=$reason;$state.next_action='Recover from persisted state; no blind restart'
    $null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
    $null=Update-AutopilotHeartbeat -AutopilotDir $auto -RunId $state.run_id -ProcessId $PID -Status 'FAILED' -CurrentTask $reason
    $null=Add-AutopilotEvent -AutopilotDir $auto -RunId $state.run_id -Actor 'watchdog' -Type 'PARENT_CRASH_RECOVERED' -Payload @{reason=$reason;parent_pid=$ParentId}
    $null=& (Join-Path $script:RunnerInfra 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $ProjectRoot -CheckpointId ('chk-watchdog-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason $reason
    Remove-RunnerOwnedLock $auto $state.run_id $ParentId
    $cleanup=@{job_closed=$true;owned_survivors=$alive;guardian_exits_after_report=$true;run_lock_removed=$true;inference_mutex=(Test-RunnerInferenceReleased);parent_identity_verified=$true}
    $started=[datetimeoffset]::Now
    foreach($line in @(Get-Content -LiteralPath (Join-Path $auto 'EVENTS.jsonl') -Encoding UTF8)){try{$evt=$line|ConvertFrom-Json;if($evt.type -eq 'RUN_STARTED'){$started=[datetimeoffset]::Parse($evt.timestamp);break}}catch{}}
    $null=Write-RunnerReport -Project $ProjectRoot -RunId $state.run_id -State $state -Status 'FAILED' -Technical 'INTERRUPTED' -Reason $reason -Duration ([datetimeoffset]::Now-$started).TotalSeconds -Cleanup $cleanup
    Write-RunnerJson (Join-Path $auto 'reports/watchdog-failure.json') @{status='FAILED';reason=$reason;cleanup=$cleanup}
}finally{if($acquired){$mutex.ReleaseMutex()};$mutex.Dispose()}
