[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ProjectRoot,[ValidateSet('Prepare','Preflight','Approve','Start')][string]$Action='Preflight',[string]$ApprovalDigest='', [switch]$Recover,[string]$Objective,[string[]]$AcceptanceCriteria,[string]$PlanPath,[string]$WorkspaceRoot)
$ErrorActionPreference='Stop'
# Cron/Python callers may inherit PowerShell 7's module path. Pin only this PS5 process.
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
if($Action -eq 'Prepare'){
    [Console]::OutputEncoding=[Text.Encoding]::UTF8
    $env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1'
    $prepareMutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$prepareHeld=$false
    try {
        try{$prepareHeld=$prepareMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$prepareHeld=$true}
        if(-not $prepareHeld){@{status='DENY';phase='PREPARE_PRE_ADMISSION';reason='RUN_ALREADY_ACTIVE';prepare_write_count=0}|ConvertTo-Json;exit 2}
        $request=@{project=$ProjectRoot;objective=$Objective;criteria=@($AcceptanceCriteria);plan=$PlanPath;workspace=$WorkspaceRoot}|ConvertTo-Json -Depth 8 -Compress
        $encoded=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($request))
        $encoded | & C:/Python314/python.exe (Join-Path $PSScriptRoot 'prepare.py') --request-stdin
        exit $LASTEXITCODE
    } finally {
        if($prepareHeld){$prepareMutex.ReleaseMutex()};$prepareMutex.Dispose()
    }
}
. (Join-Path $PSScriptRoot 'core.ps1')
. (Join-Path $PSScriptRoot 'report.ps1')
. (Join-Path $PSScriptRoot 'cleanup.ps1')
$admissionAction='inspect';if($Action -eq 'Approve'){$admissionAction='approve'}elseif($Action -eq 'Start'){$admissionAction='validate'}
try{$script:Admission=Get-RunnerAdmission $admissionAction $ProjectRoot $ApprovalDigest}catch{@{status='BLOCKED_REQUIRES_HUMAN';reason=$_.Exception.Message;started=$false}|ConvertTo-Json;exit 2}
if($Action -ne 'Start'){@{status='PASS';action=$Action;project=$script:Admission.project;run_id=$script:Admission.contract.run_id;approval_digest=$script:Admission.digest}|ConvertTo-Json;exit 0}
$script:Cfg=((& C:/Python314/python.exe (Join-Path $script:RunnerInfra 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $script:RunnerInfra 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$script:Auto=$script:Admission.auto;$script:RunId=$script:Admission.contract.run_id;$script:Started=[datetimeoffset]::Now
$script:Owned=@{};$script:ExternalModel=$null;$script:CurrentTask='startup';$script:RunJob=$null
$script:Restarts=@{llama=0;supervisor=0;worker=0;reviewer=0}
if(Test-Path -LiteralPath (Join-Path $script:Auto 'RESTARTS.json')){
    $savedRestarts=Get-Content -LiteralPath (Join-Path $script:Auto 'RESTARTS.json') -Raw -Encoding UTF8|ConvertFrom-Json
    foreach($name in @('llama','supervisor','worker','reviewer')){if($savedRestarts.$name -ne $null){$script:Restarts[$name]=[int]$savedRestarts.$name}}
}
$script:GlobalSeconds=[Math]::Min($script:Admission.contract.time_budget_minutes*60,$script:Cfg.runner.global_timeout_minutes*60)
if($script:Admission.plan.global_timeout_seconds){$script:GlobalSeconds=[Math]::Min($script:GlobalSeconds,$script:Admission.plan.global_timeout_seconds)}
$runMutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false;$terminal='FAILED';$failure='';$technical='FAIL'
try{
    try{$held=$runMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_ALREADY_ACTIVE'}
    # The approved run's wall-clock budget survives crashes and resume attempts.
    $clockDirectory=Join-Path $script:RunnerInfra 'runtime/run-clocks';$null=New-Item -ItemType Directory -Path $clockDirectory -Force
    $clockPath=Join-Path $clockDirectory (Split-Path -Leaf $script:Admission.receipt_path)
    if(Test-Path -LiteralPath $clockPath){$clock=Get-Content -LiteralPath $clockPath -Raw -Encoding UTF8|ConvertFrom-Json;if($clock.run_id -ne $script:RunId){throw 'RUN_CLOCK_ID_MISMATCH'};$script:Started=[datetimeoffset]::Parse($clock.started_at)}else{Write-RunnerJson $clockPath @{run_id=$script:RunId;started_at=$script:Started.ToString('o')}}
    if($script:Started -gt [datetimeoffset]::Now){throw 'RUN_CLOCK_INVALID'}
    $script:RunJob=New-Object DaOwnedProcessJob
    $statePath=Join-Path $script:Auto 'STATE.json'
    if($Recover -or (Test-FileSchemaValidation $statePath (Join-Path $script:RunnerInfra 'schemas/autopilot-state.schema.json')) -ne 'VALID'){
        $initialRecovery=& (Join-Path $script:RunnerInfra 'scripts/recover-autopilot.ps1') -ProjectPath $script:Admission.project
    }
    $script:RunState=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
    if($script:RunState.run_id -ne $script:RunId){throw 'STATE_RUN_ID_MISMATCH'}
    $lockPath=Join-Path $script:Auto 'LOCK.json'
    if(Test-Path -LiteralPath $lockPath){
        $old=Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8|ConvertFrom-Json
        Runner-Event 'LOCK_METADATA_RECONCILED' @{previous=$old;kernel_mutex_acquired=$held}
    }
    if($Recover -or $script:RunState.status -in @('RUNNING','RECOVERING','FAILED','STALLED')){
        $recovered=& (Join-Path $script:RunnerInfra 'scripts/recover-autopilot.ps1') -ProjectPath $script:Admission.project
        $script:RunState=$recovered.State;Runner-Event 'RUN_RECOVERED_FROM_DISK' @{status=$recovered.Status}
    }
    if($Recover){
        $archive=Join-Path $script:Auto ('recovered-signals/'+[datetime]::Now.ToString('yyyyMMddHHmmssfff'))
        foreach($name in @('WATCHDOG-SIGNAL.json','STOP')){
            $path=Join-Path $script:Auto $name
            if(Test-Path -LiteralPath $path){
                $flag=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
                $ownedFlag=($name -eq 'STOP' -and $flag.run_id -eq $script:RunId)
                if($name -eq 'WATCHDOG-SIGNAL.json'){$oldParent=Get-Process -Id $flag.parent_pid -ErrorAction SilentlyContinue;$ownedFlag=(-not $oldParent -or $oldParent.StartTime.ToUniversalTime().Ticks -ne $flag.start_ticks)}
                if(-not $ownedFlag){throw 'ACTIVE_OR_FOREIGN_SIGNAL_PRESERVED'}
                $null=New-Item -ItemType Directory -Path $archive -Force;Move-Item -LiteralPath $path -Destination (Join-Path $archive $name)
            }
        }
    }
    Save-RunnerState 'RUNNING' 'preflight passed'
    Write-RunnerJson (Join-Path $script:Auto 'RESTARTS.json') $script:Restarts
    $null=Write-RunLockMeta -AutopilotDir $script:Auto -RunId $script:RunId -OwnerPid $PID -ProjectRoot $script:Admission.project
    Runner-Event 'RUN_STARTED' @{approval_digest=$script:Admission.digest;backend=$script:Admission.plan.backend;git_head=(& git -C $script:Admission.project rev-parse HEAD).Trim()}
    $stale=120;if($script:Admission.plan.heartbeat_stale_seconds){$stale=[Math]::Min($stale,$script:Admission.plan.heartbeat_stale_seconds)}
    $watch=Start-RunnerProcess 'watchdog' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'watchdog-monitor.ps1'),'-ProjectRoot',$script:Admission.project,'-ParentId',$PID,'-ParentStartTicks',(Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks,'-StaleSeconds',$stale) $script:Admission.project -Guardian
    if($script:Admission.plan.backend -ne 'probe'){Start-RunnerModel}
    $timeout=180;if($script:Admission.plan.phase_timeout_seconds){$timeout=$script:Admission.plan.phase_timeout_seconds}
    $base=@{project=$script:Admission.project;backend=$script:Admission.plan.backend;timeout=$timeout;probe_delay_seconds=$script:Admission.plan.probe_delay_seconds}
    $tracker=@{};$feedback='';$cycleLimit=[int]$script:Cfg.limits.max_cycles
    if($script:Admission.plan.max_cycles){$cycleLimit=[Math]::Min($cycleLimit,$script:Admission.plan.max_cycles)}
    $trackerPath=Join-Path $script:Auto 'PROGRESS-TRACKER.json'
    if(Test-Path -LiteralPath $trackerPath){$savedTracker=Get-Content -LiteralPath $trackerPath -Raw -Encoding UTF8|ConvertFrom-Json;foreach($entry in $savedTracker.PSObject.Properties){$tracker[$entry.Name]=$entry.Value}}
    while($true){
    Tick-Runner
    $p=$base.Clone();$p.role='supervisor';$p.prompt='Plan only. Return JSON {"task":"..."} for this approved objective and task. Do not use tools or edit. Objective: '+$script:Admission.contract.objective+' Task: '+$script:Admission.plan.task
    $p.prompt+="`nPrevious deterministic feedback: "+$feedback
    $supervisor=Invoke-RunnerAgent 'supervisor' $p
    $request=@{schema_version='1.0';delegation_id=('del-'+$script:RunId);objective=$script:Admission.contract.objective;workspace=$script:Admission.project;task=$script:Admission.plan.task;acceptance_criteria=@($script:Admission.contract.acceptance_criteria);allowed_actions=@($script:Admission.contract.allowed_actions);forbidden_actions=@($script:Admission.contract.forbidden_actions);tests=@($script:Admission.contract.test_commands);status='READY'}
    $scopeHint=@{allowed_files=@($script:Admission.plan.allowed_files);write_scope=@($script:Admission.plan.write_scope)}|ConvertTo-Json -Compress
    $request.task+="`nApproved write scope: "+$scopeHint+"`nDo not modify files outside that scope or immutable acceptance files."
    $request.task+="`nSupervisor plan (advisory, approved scope remains binding): "+$supervisor.text+"`nPrevious checks to correct: "+$feedback
    if($script:Admission.plan.research){
        $webPath=Join-Path $script:Auto 'evidence/WEB.json'
        if(-not(Test-Path -LiteralPath $webPath)){
            if($script:Admission.plan.research.diagnose_before_fetch){
                $before=@{};foreach($name in $script:Admission.plan.allowed_files){$before[$name]=(Get-FileHash -LiteralPath (Join-Path $script:Admission.project $name) -Algorithm SHA256).Hash}
                $d=$base.Clone();$d.role='worker';$d.mode='diagnosis';$d.prompt='Diagnosis only. Run exactly this approved command once: '+($script:Admission.plan.tests[0].argv -join ' ')+'. Report the failing acceptance criteria briefly (maximum 120 words). DO NOT edit any files or solve the task. Runner will provide official research afterward.'
                $diagnosis=Invoke-RunnerAgent 'worker' $d
                foreach($name in $before.Keys){if((Get-FileHash -LiteralPath (Join-Path $script:Admission.project $name) -Algorithm SHA256).Hash -ne $before[$name]){throw 'DIAGNOSTIC_WORKER_MODIFIED_SOURCE'}}
                Write-RunnerJson (Join-Path $script:Auto 'evidence/worker-diagnosis.json') $diagnosis
                $initial=@(Invoke-RunnerCommands @($script:Admission.plan.tests) 'initial-failure')
                Write-RunnerJson (Join-Path $script:Auto 'evidence/initial-failure.json') @{tests=$initial}
                if(@($initial|Where-Object{$_.status -eq 'FAIL'}).Count -eq 0){throw 'EXPECTED_INITIAL_TEST_FAILURE_MISSING'}
                Runner-Event 'WORKER_DIAGNOSIS_CONFIRMED' @{initial_failure=$true;source_unchanged=$true}
            }
            $researchArgs=@('-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'research-step.ps1'),'-ProjectRoot',$script:Admission.project)
            if($script:Admission.plan.research.url){
                $researchArgs+=@('-Url',[string]$script:Admission.plan.research.url)
            }elseif($script:Admission.plan.research.query){
                $researchArgs+=@('-Query',[string]$script:Admission.plan.research.query)
                $maxResults=5;if($script:Admission.plan.research.max_results){$maxResults=[int]$script:Admission.plan.research.max_results}
                $researchArgs+=@('-MaxResults',[string]$maxResults)
                $domainsJson='[]';if($script:Admission.plan.research.domains){$domainsJson=@($script:Admission.plan.research.domains)|ConvertTo-Json -Compress}
                $researchArgs+=@('-DomainsJson',$domainsJson)
            }else{throw 'RESEARCH_MODE_INVALID'}
            $web=Invoke-RunnerManaged 'web-research' 'powershell.exe' $researchArgs 35
            if($web.exit_code -ne 0){throw 'REQUIRED_WEB_FETCH_FAILED'}
            Runner-Event 'WEB_FETCHED' @{source='official_web_wrapper';mode=$(if($script:Admission.plan.research.url){'url'}else{'query'})}
        }
        $handoffRaw=& C:/Python314/python.exe (Join-Path $PSScriptRoot 'research-handoff.py') provide --project $script:Admission.project
        if($LASTEXITCODE -ne 0){throw 'RESEARCH_HANDOFF_FAILED'}
        $handoff=($handoffRaw -join "`n")|ConvertFrom-Json
        $request.task+=$handoff.task_suffix
        Runner-Event 'WEB_RESULT_PROVIDED' @{source_sha256=$handoff.source_sha256}
    }
    $p=$base.Clone();$p.role='worker';$p.request=$request;$p.research_inline=[bool]$script:Admission.plan.research;$worker=Invoke-RunnerAgent 'worker' $p
    if($script:Admission.plan.research){
        $used=& C:/Python314/python.exe (Join-Path $PSScriptRoot 'research-handoff.py') verify --project $script:Admission.project
        if($LASTEXITCODE -ne 0){throw ('WEB_CONTEXT_NOT_DELIVERED: '+($used -join ' '))}
        Runner-Event 'WEB_CONTEXT_DELIVERED' @{verified=$true;binding=($used -join "`n"|ConvertFrom-Json)}
    }
    foreach($pin in $script:Admission.plan.immutable_files){if((Get-FileHash -LiteralPath (Join-Path $script:Admission.project $pin.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'IMMUTABLE_TEST_CHANGED'}}
    $tests=@(Invoke-RunnerCommands @($script:Admission.plan.tests) 'tests');$builds=@(Invoke-RunnerCommands @($script:Admission.plan.builds) 'builds');$linters=@(Invoke-RunnerCommands @($script:Admission.plan.linters) 'linters')
    Write-RunnerJson (Join-Path $script:Auto 'evidence/checks.json') @{tests=$tests;builds=$builds;linters=$linters;run_id=$script:RunId}
    if($script:Admission.plan.sandbox_crash_boundary -and -not $Recover -and @($tests+$builds|Where-Object{$_.status -ne 'PASS'}).Count -eq 0){
        $script:CurrentTask='awaiting approved sandbox controlled crash'
        Runner-Event 'CRASH_TEST_BOUNDARY_READY' @{checks_pass=$true;clock_not_paused=$true}
        while($true){Tick-Runner;Start-Sleep -Milliseconds 200}
    }
    if($script:Admission.plan.consultation -and ($Recover -or -not $script:Admission.plan.consultation.after_recovery) -and @($tests+$builds|Where-Object{$_.status -ne 'PASS'}).Count -eq 0){
        $chatPath=Join-Path $script:Auto 'evidence/CHATGPT.json'
        $existingChat=$null;if(Test-Path -LiteralPath $chatPath){$existingChat=Get-Content -LiteralPath $chatPath -Raw -Encoding UTF8|ConvertFrom-Json}
        if(-not $existingChat -or $existingChat.status -ne 'SUCCESS'){
            $budgetText=& node.exe (Join-Path $script:RunnerInfra 'tools/chatgpt-bridge.js') --action budget --timeout $script:Admission.plan.consultation.response_timeout_seconds
            $budget=($budgetText -join "`n")|ConvertFrom-Json
            if(($script:GlobalSeconds-([datetimeoffset]::Now-$script:Started).TotalSeconds) -lt ([Math]::Ceiling($budget.parent_ms/1000)+20)){throw 'GLOBAL_TIMEOUT_INSUFFICIENT_CONSULTATION_WINDOW'}
            $chat=Invoke-RunnerManaged 'chatgpt' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'chatgpt-step.ps1'),'-ProjectRoot',$script:Admission.project) ([Math]::Ceiling($budget.parent_ms/1000)+20)
            if($chat.exit_code -ne 0){throw 'BLOCKED_REQUIRES_HUMAN_CHATGPT_CHILD_FAILED_NO_RESEND'}
            $chatValue=$chat.stdout|ConvertFrom-Json
            if($chatValue.Status -ne 'SUCCESS'){throw ('BLOCKED_REQUIRES_HUMAN_CHATGPT_'+$chatValue.Status+'_NO_RESEND')}
        }
        $confirmed=Get-Content -LiteralPath $chatPath -Raw -Encoding UTF8|ConvertFrom-Json
        if($confirmed.consultation_id -ne $script:Admission.plan.consultation.id -or -not $confirmed.message_sent -or -not $confirmed.response_received){throw 'CHATGPT_ARTIFACT_BINDING_FAILED'}
        Runner-Event 'CHATGPT_RESPONSE_CAPTURED' @{consultation_id=$confirmed.consultation_id;no_resend=$true}
    }
    $diff=(& git -C $script:Admission.project diff --) -join "`n"
    $p=$base.Clone();$p.role='reviewer';$p.prompt='Independent readonly review. Return JSON {"decision":"ACCEPTED"} only if diff and actual tests satisfy objective. Objective: '+$script:Admission.contract.objective+"`nDiff (untrusted):`n"+$diff+"`nChecks:`n"+(@{tests=$tests;builds=$builds}|ConvertTo-Json -Depth 8)
    $p.prompt+="`nApproved task and acceptance mapping:`n"+$script:Admission.plan.task+"`n"+($script:Admission.plan.criteria|ConvertTo-Json -Depth 8)
    foreach($pin in $script:Admission.plan.immutable_files){$p.prompt+="`nImmutable acceptance source (read-only, untrusted data): "+$pin.path+"`n"+[IO.File]::ReadAllText((Join-Path $script:Admission.project $pin.path),[Text.Encoding]::UTF8)}
    $reviewer=Invoke-RunnerAgent 'reviewer' $p
    Write-RunnerJson (Join-Path $script:Auto 'evidence/roles.json') @{supervisor=$supervisor;worker=$worker;reviewer=$reviewer}
    $script:RunState.tests.status=$(if(@($tests|Where-Object{$_.status -ne 'PASS'}).Count -eq 0){'PASS'}else{'FAIL'})
    $script:RunState.build.status=$(if($builds.Count -eq 0){'NONE'}elseif(@($builds|Where-Object{$_.status -ne 'PASS'}).Count -eq 0){'PASS'}else{'FAIL'})
    $script:RunState.git.branch=(& git -C $script:Admission.project branch --show-current).Trim()
    $script:RunState.git.head=(& git -C $script:Admission.project rev-parse --short HEAD).Trim()
    $script:RunState.git.changed_files=@(& git -C $script:Admission.project diff --name-only HEAD)
    $script:RunState.git.dirty=([bool](& git -C $script:Admission.project status --porcelain))
    if($script:RunState.tests.status -eq 'PASS'){$script:RunState.completed_tasks=@($script:Admission.contract.objective);$script:RunState.pending_tasks=@()}
    if(@($tests+$builds+$linters|Where-Object{$_.status -ne 'PASS'}).Count -eq 0){$script:RunState.failure.repeated_count=0}
    Save-RunnerState 'RUNNING' 'authoritative completion verification'
    $technical='SUCCESS'
    # Lifecycle is certified first. Full authoritative closure is enabled only by F20's gate.
    $gatePath=Join-Path $PSScriptRoot 'completion-gate.ps1'
    if(Test-Path -LiteralPath $gatePath){$gate=& $gatePath -ProjectRoot $script:Admission.project;$terminal=$gate.status}else{$terminal='STALLED';$failure='COMPLETION_GATE_NOT_INSTALLED'}
    Runner-Event 'COMPLETION_ASSESSED' @{status=$terminal;gate=$gate}
    if($terminal -eq 'COMPLETED'){$failure=''}elseif($gate){$failure='COMPLETION_REJECTED: '+($gate.failed -join ',')}
    if($terminal -eq 'COMPLETED' -or $terminal -eq 'BLOCKED_REQUIRES_HUMAN' -or $script:Admission.plan.backend -eq 'probe'){break}
    $feedback=(@{gate=$gate;tests=$tests;builds=$builds;linters=$linters}|ConvertTo-Json -Depth 12)
    $signature=Get-NormalizedErrorSignature -ErrorText (($gate.failed|Sort-Object) -join ',')
    $fingerprint=Get-ProgressFingerprint -WorkspacePath $script:Admission.project -PassTests @($tests|Where-Object{$_.status -eq 'PASS'}).Count -FailTests @($tests|Where-Object{$_.status -ne 'PASS'}).Count -ErrorSignatureHash $signature.SignatureHash -CustomContext $diff
    $progress=Test-LoopProgress -Tracker $tracker -CurrentErrorHash $signature.SignatureHash -CurrentFingerprint $fingerprint.Fingerprint -MaxCycles $cycleLimit -MaxSameFailure $script:Cfg.limits.max_same_failure -MaxNoProgress $script:Cfg.limits.max_no_progress_cycles
    Write-RunnerJson $trackerPath $tracker
    $script:RunState.progress.no_progress_cycles=[int]$tracker.no_progress_cycles
    $script:RunState.failure.repeated_count=[int]$tracker.same_failure_count
    Save-RunnerState 'RUNNING' 'checkpoint before bounded correction cycle'
    $null=& (Join-Path $script:RunnerInfra 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $script:Admission.project -CheckpointId ('chk-cycle-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason 'Deterministic correction feedback'
    Runner-Event 'CORRECTION_CYCLE' @{progress=$progress;tracker=$tracker}
    if(-not $progress.CanContinue -or $tracker.same_failure_count -ge $script:Cfg.limits.max_same_failure -or $tracker.no_progress_cycles -ge $script:Cfg.limits.max_no_progress_cycles){$terminal='STALLED';$failure='CORRECTION_BUDGET_EXHAUSTED';break}
    }
}catch{
    $failure=$_.Exception.Message
    if($failure -eq 'STOP_REQUESTED'){$terminal='ABORTED'}elseif($failure -eq 'NO_PROGRESS_STALLED'){$terminal='STALLED'}elseif($failure -match 'REQUIRES_HUMAN|EXTERNAL_MODEL'){$terminal='BLOCKED_REQUIRES_HUMAN'}else{$terminal='FAILED'}
}finally{
    $cleanup=[ordered]@{job_closed=$false;owned_survivors=@();run_mutex_released=$false;run_lock_removed=$false;inference_mutex='NOT_CHECKED';external_model_preserved=($null -ne $script:ExternalModel);errors=@()}
    if($held){
        try{
            try{if($script:RunJob){$script:RunJob.Dispose()};$cleanup.job_closed=$true}catch{$cleanup.errors+=@('JOB_CLOSE: '+$_.Exception.Message)}
            foreach($name in @($script:Owned.Keys|Where-Object{$_ -ne 'watchdog'})){try{$null=$script:Owned[$name].process.WaitForExit(5000)}catch{$cleanup.errors+=@('PROCESS_WAIT: '+$name)}}
            if($script:RunState){
                try{Save-RunnerState $terminal ('terminal: '+$failure)}catch{$cleanup.errors+=@('STATE_SAVE: '+$_.Exception.Message)}
                try{$null=& (Join-Path $script:RunnerInfra 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $script:Admission.project -CheckpointId ('chk-runner-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason ('Runner terminal '+$terminal)}catch{$cleanup.errors+=@('CHECKPOINT: '+$_.Exception.Message)}
            }
            # Guardian exits on a terminal heartbeat; identity-checked fallback is bounded.
            if($script:Owned.watchdog){try{if(-not $script:Owned.watchdog.process.WaitForExit(2000)){Stop-RunnerProcess $script:Owned.watchdog}}catch{$cleanup.errors+=@('GUARDIAN_STOP: '+$_.Exception.Message)}}
            $cleanup.owned_survivors=@(Get-RunnerSurvivors $script:Auto)
            if($cleanup.owned_survivors.Count){$cleanup.errors+=@('OWNED_PROCESS_SURVIVED')}
            try{Remove-RunnerOwnedLock $script:Auto $script:RunId $PID;$cleanup.run_lock_removed=$true}catch{$cleanup.errors+=@('LOCK_CLEANUP: '+$_.Exception.Message)}
            try{$cleanup.inference_mutex=Test-RunnerInferenceReleased}catch{$cleanup.errors+=@('INFERENCE_CHECK: '+$_.Exception.Message)}
        }finally{
            try{$runMutex.ReleaseMutex();$cleanup.run_mutex_released=$true}catch{$cleanup.errors+=@('RUN_MUTEX_RELEASE: '+$_.Exception.Message)}
            $runMutex.Dispose()
        }
        if($cleanup.errors.Count){$terminal='FAILED';$failure='FINALIZATION_FAILED: '+($cleanup.errors -join '; ');try{Save-RunnerState $terminal $failure}catch{}}
        $reportState=$script:RunState
        if(-not $reportState){$reportState=[pscustomobject]@{objective=$script:Admission.contract.objective;completed_tasks=@();pending_tasks=@($script:Admission.contract.objective);chatgpt=@{queries_used=0}}}
        if($reportState){
            try{Runner-Event 'RUN_FINISHED' @{status=$terminal;technical=$technical;reason=$failure;cleanup=$cleanup}}catch{}
            try{$null=Write-RunnerReport -Project $script:Admission.project -RunId $script:RunId -State $reportState -Status $terminal -Technical $technical -Reason $failure -Duration ([datetimeoffset]::Now-$script:Started).TotalSeconds -Cleanup $cleanup}catch{
                $terminal='FAILED';$failure='FINAL_REPORT_WRITE_FAILED: '+$_.Exception.Message;try{Save-RunnerState $terminal $failure}catch{}
                $fallback=Join-Path $script:RunnerInfra ('runtime/emergency-reports/'+$script:RunId+'-'+$PID)
                $null=Write-RunnerReport -Project $script:Admission.project -RunId $script:RunId -State $reportState -Status $terminal -Technical $technical -Reason $failure -Duration ([datetimeoffset]::Now-$script:Started).TotalSeconds -Cleanup $cleanup -ReportRoot $fallback
            }
        }
    }else{
        $runMutex.Dispose()
    }
}
@{status=$terminal;technical_status=$technical;run_id=$script:RunId;reason=$failure}|ConvertTo-Json
if($terminal -ne 'COMPLETED'){exit 1}
