# Uses the existing recursive secret sanitizer from core.ps1.
function Read-RunnerEvidence([string]$Path,$Fallback){
    if(Test-Path -LiteralPath $Path){try{return (Get-Content -LiteralPath $Path -Raw -Encoding UTF8|ConvertFrom-Json)}catch{}}
    return $Fallback
}
function Write-RunnerPrestartBlock($Info,[string]$Reason){
    # A denied second launcher must never overwrite another active run's STATE.
    $mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$acquired=$false
    try{
        try{$acquired=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$acquired=$true}
        if(-not $acquired){return}
        $auto=$Info.auto;$state=Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
        $state.status='BLOCKED_REQUIRES_HUMAN';$state.current_phase='PREFLIGHT';$state.current_task=$Reason;$state.next_action='Approve the reviewed contract before START'
        $null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
        $null=Update-AutopilotHeartbeat -AutopilotDir $auto -RunId $state.run_id -ProcessId $PID -Status 'BLOCKED_REQUIRES_HUMAN' -CurrentTask $Reason
        $null=& (Join-Path $script:RunnerInfra 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $Info.project -CheckpointId ('chk-blocked-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason $Reason
        $null=Write-RunnerReport -Project $Info.project -RunId $state.run_id -State $state -Status 'BLOCKED_REQUIRES_HUMAN' -Technical 'NOT_STARTED' -Reason $Reason -Duration 0 -Cleanup @{started=$false;owned_processes=0;job_closed=$true}
    }finally{if($acquired){$mutex.ReleaseMutex()};$mutex.Dispose()}
}
function Write-RunnerReport([string]$Project,[string]$RunId,$State,[string]$Status,[string]$Technical,[string]$Reason,[double]$Duration,$Cleanup,[string]$ReportRoot=''){
    $auto=Join-Path $Project '.autopilot';$events=@()
    if(-not $ReportRoot){$ReportRoot=Join-Path $auto 'reports'}
    $null=New-Item -ItemType Directory -Path $ReportRoot -Force
    foreach($line in @(Get-Content -LiteralPath (Join-Path $auto 'EVENTS.jsonl') -Encoding UTF8 -ErrorAction SilentlyContinue)){try{$evt=$line|ConvertFrom-Json;if($evt.run_id -eq $RunId){$events+=@($evt)}}catch{}}
    $checks=Read-RunnerEvidence (Join-Path $auto 'evidence/checks.json') @{tests=@();builds=@();linters=@();evidence_missing=$true}
    $gate=Read-RunnerEvidence (Join-Path $auto 'evidence/completion-gate.json') @{status='NOT_EVALUATED';reason=$Reason}
    $restarts=Read-RunnerEvidence (Join-Path $auto 'RESTARTS.json') @{}
    $start=@($events|Where-Object{$_.type -eq 'RUN_STARTED'}|Select-Object -First 1)
    $baseline='';if($start.Count){$baseline=$start[0].payload.git_head}
    $changed=@(& git -C $Project diff --name-only HEAD)
    $changed+=@(& git -C $Project ls-files --others --exclude-standard)
    $changed=@($changed|Where-Object{$_ -and -not $_.StartsWith('.autopilot/')}|Sort-Object -Unique)
    $commits=@();if($baseline){$commits=@(& git -C $Project log ($baseline+'..HEAD') --format='%H %s')}
    $processes=@($events|Where-Object{$_.type -eq 'PROCESS_STARTED'}|ForEach-Object{$_.payload})
    $errors=@($events|Where-Object{$_.type -match 'RESTART|ERROR|FAILED'}|ForEach-Object{$_.payload})
    if($Reason){$errors+=@($Reason)}
    $report=[ordered]@{
        schema_version='1.0';run_id=$RunId;project=$Project;objective=$State.objective
        duration_seconds=$Duration;status=$Status;technical_status=$Technical;reason=$Reason
        tasks_completed=@($State.completed_tasks);pending_tasks=@($State.pending_tasks)
        changed_files=$changed;commits=$commits;tests=@($checks.tests);builds=@($checks.builds);linters=@($checks.linters)
        errors=$errors;retries=$restarts;recoveries=@($events|Where-Object{$_.type -in @('RUN_RECOVERED_FROM_DISK','PARENT_CRASH_RECOVERED') -or $_.type -match 'WATCHDOG_.*RESTART'})
        web_queries=@($events|Where-Object{$_.type -eq 'WEB_QUERY'});chatgpt_queries_used=$State.chatgpt.queries_used
        blocks=@($(if($Status -eq 'BLOCKED_REQUIRES_HUMAN'){$Reason}));completion_gate=$gate
        cleanup=$Cleanup;processes=$processes;generated_at=[datetimeoffset]::Now.ToString('o')
    }
    $safe=Sanitize-ObjectDeep $report
    Write-RunnerJson (Join-Path $ReportRoot 'runner-result.json') $safe
    $lines=@('# Runner final report', '',('Run: '+$RunId),('Project: '+$Project),('Objective: '+$State.objective),('Status: '+$Status),('Duration seconds: '+[Math]::Round($Duration,2)),('Reason: '+$Reason),'', '## Evidence')
    foreach($name in @('tasks_completed','pending_tasks','changed_files','commits','tests','builds','linters','errors','retries','recoveries','web_queries','chatgpt_queries_used','blocks','completion_gate','cleanup')){
        $lines+=@('',('### '+$name),'', '```json',($safe[$name]|ConvertTo-Json -Depth 20),'```')
    }
    $markdown=Sanitize-StringContent ($lines -join "`n")
    [IO.File]::WriteAllText((Join-Path $ReportRoot 'FINAL.md'),$markdown,(New-Object Text.UTF8Encoding($false)))
    $special=@{FAILED='FAILURE.md';STALLED='STALLED.md';BLOCKED_REQUIRES_HUMAN='BLOCKED.md';ABORTED='ABORTED.md'}
    if($special.ContainsKey($Status)){[IO.File]::WriteAllText((Join-Path $ReportRoot $special[$Status]),$markdown,(New-Object Text.UTF8Encoding($false)))}
    return $safe
}
