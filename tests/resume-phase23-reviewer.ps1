param([string]$ProjectRoot='', [string]$EvidenceRoot='')
$ErrorActionPreference='Stop'
$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
if(-not $ProjectRoot){$ProjectRoot=Join-Path $root 'sandbox/f23-full-feac8aea/project'}
if(-not $EvidenceRoot){$EvidenceRoot=Join-Path $root 'evidence/hermes-prompt-transport-20261014'}
. (Join-Path $root 'runner/core.ps1')
. (Join-Path $root 'runner/report.ps1')
. (Join-Path $root 'runner/cleanup.ps1')
$script:Admission=Get-RunnerAdmission 'validate' $ProjectRoot
$script:Auto=$script:Admission.auto;$script:RunId=$script:Admission.contract.run_id
$script:Cfg=((& C:/Python314/python.exe (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$script:Owned=@{};$script:ExternalModel=$null;$script:RunJob=$null
# Explicitly authorized bounded maintenance after transport repair. Historical
# run clock and exhausted automatic restart budget are preserved, never reset.
$script:Started=[datetimeoffset]::Now;$script:GlobalSeconds=600;$script:CurrentTask='F23 reviewer transport maintenance'
$script:RunState=Get-Content -LiteralPath (Join-Path $script:Auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
$terminal='FAILED';$reason='';$reviewer=$null;$gate=$null;$isolation=$false
$beforeDir=Join-Path $EvidenceRoot 'operational-before';$null=New-Item -ItemType Directory -Path $beforeDir -Force
foreach($name in @('STATE.json','STATE.md','EVENTS.jsonl','RESTARTS.json','packet-reviewer.json','evidence/checks.json','logs/supervisor.stdout.txt','logs/worker.stdout.txt','reports/runner-result.json')){
    $p=Join-Path $script:Auto $name
    if(Test-Path -LiteralPath $p){Copy-Item -LiteralPath $p -Destination (Join-Path $beforeDir ($name.Replace('/','-')))}
}
$pins=@{}
foreach($name in @('calculator.py','README.md','test_calculator.py','build.py','WEB.json','CHATGPT.json','QWEN.md','.autopilot/RESTARTS.json')){$pins[$name]=(Get-FileHash -LiteralPath (Join-Path $ProjectRoot $name)).Hash}
Write-RunnerJson (Join-Path $EvidenceRoot 'input-hashes.json') $pins
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_ALREADY_ACTIVE'}
    $script:RunJob=New-Object DaOwnedProcessJob
    Runner-Event 'F23_AUTHORIZED_REVIEWER_MAINTENANCE' @{source='explicit human request after prompt transport repair';timeout_seconds=600;automatic_restart_budget_reset=$false;historical_clock_reset=$false}
    Save-RunnerState 'RUNNING' $script:CurrentTask
    $null=Write-RunLockMeta -AutopilotDir $script:Auto -RunId $script:RunId -OwnerPid $PID -ProjectRoot $ProjectRoot
    Start-RunnerModel
    # Re-run the exact original prompt and native readonly role, with no worker edits.
    $packetPath=Join-Path $script:Auto 'packet-reviewer.json'
    $packet=Get-Content -LiteralPath $packetPath -Raw -Encoding UTF8|ConvertFrom-Json
    $r=Invoke-RunnerManaged 'reviewer-maintenance' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'runner/agent-step.ps1'),'-PacketPath',$packetPath) 310
    Write-RunnerJson (Join-Path $EvidenceRoot 'reviewer-process.json') $r
    $reviewer=$r.stdout|ConvertFrom-Json
    Write-RunnerJson (Join-Path $EvidenceRoot 'reviewer-real.json') $reviewer
    if($r.exit_code -ne 0 -or $reviewer.status -ne 'SUCCESS'){throw 'MANDATORY_TEST_FAILED: NATIVE_REVIEWER_EXECUTION'}
    $match=[regex]::Match($reviewer.text,'\{.*\}',[Text.RegularExpressions.RegexOptions]::Singleline)
    if(-not $match.Success){throw 'MANDATORY_TEST_FAILED: REVIEWER_INVALID_DECISION'}
    $decision=$match.Value|ConvertFrom-Json
    if($decision.decision -notin @('ACCEPTED','REJECTED')){throw 'MANDATORY_TEST_FAILED: REVIEWER_INVALID_DECISION'}
    foreach($name in $pins.Keys){if((Get-FileHash -LiteralPath (Join-Path $ProjectRoot $name)).Hash -ne $pins[$name]){throw ('SECURITY_REGRESSION: REVIEWER_CHANGED_FILE '+$name)}}
    $isolation=$true
    if($decision.decision -ne 'ACCEPTED'){throw ('MANDATORY_TEST_FAILED: TECHNICAL_REVIEW_REJECTED '+$reviewer.text)}
    $supervisor=Get-Content -LiteralPath (Join-Path $beforeDir 'logs-supervisor.stdout.txt') -Raw -Encoding UTF8|ConvertFrom-Json
    $worker=Get-Content -LiteralPath (Join-Path $beforeDir 'logs-worker.stdout.txt') -Raw -Encoding UTF8|ConvertFrom-Json
    if($supervisor.status -ne 'SUCCESS' -or $worker.status -ne 'SUCCESS'){throw 'MANDATORY_TEST_FAILED: HISTORICAL_ROLE_EVIDENCE'}
    # Validate freshness of checks on the same unchanged worker output; no heavy suite.
    $tests=@(Invoke-RunnerCommands @($script:Admission.plan.tests) 'tests')
    $builds=@(Invoke-RunnerCommands @($script:Admission.plan.builds) 'builds')
    Write-RunnerJson (Join-Path $script:Auto 'evidence/checks.json') @{tests=$tests;builds=$builds;linters=@();run_id=$script:RunId}
    Write-RunnerJson (Join-Path $script:Auto 'evidence/roles.json') @{supervisor=$supervisor;worker=$worker;reviewer=$reviewer}
    if(@($tests+$builds|Where-Object{$_.status -ne 'PASS'}).Count){throw 'MANDATORY_TEST_FAILED: F23_CHECK_REGRESSION'}
    $script:RunState.tests.status='PASS';$script:RunState.build.status='PASS'
    $script:RunState.completed_tasks=@($script:Admission.contract.objective);$script:RunState.pending_tasks=@()
    $script:RunState.failure.repeated_count=0
    $script:RunState.git.branch=(& git -C $ProjectRoot branch --show-current).Trim()
    $script:RunState.git.head=(& git -C $ProjectRoot rev-parse --short HEAD).Trim()
    $script:RunState.git.changed_files=@(& git -C $ProjectRoot diff --name-only HEAD)
    $script:RunState.git.dirty=[bool](& git -C $ProjectRoot status --porcelain)
    Save-RunnerState 'RUNNING' 'authoritative completion verification after authorized reviewer maintenance'
    $gate=& (Join-Path $root 'runner/completion-gate.ps1') -ProjectRoot $ProjectRoot
    Write-RunnerJson (Join-Path $EvidenceRoot 'completion-gate.json') $gate
    Runner-Event 'COMPLETION_ASSESSED' @{status=$gate.status;gate=$gate;source='authorized reviewer maintenance'}
    if($gate.status -ne 'COMPLETED'){throw ('MANDATORY_TEST_FAILED: COMPLETION_REJECTED '+($gate.failed -join ','))}
    $terminal='COMPLETED'
}catch{$reason=$_.Exception.Message}
finally{
    $cleanup=@{job_closed=$false;owned_survivors=@();run_mutex_released=$false;run_lock_removed=$false;inference_mutex='NOT_CHECKED';errors=@()}
    if($held){
        try{
            if($script:RunJob){$script:RunJob.Dispose()};$cleanup.job_closed=$true
            foreach($item in $script:Owned.Values){$null=$item.process.WaitForExit(5000)}
            Save-RunnerState $terminal ('terminal maintenance: '+$reason)
            $null=& (Join-Path $root 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $ProjectRoot -CheckpointId ('chk-reviewer-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason ('Reviewer maintenance '+$terminal)
            Remove-RunnerOwnedLock $script:Auto $script:RunId $PID;$cleanup.run_lock_removed=$true
            $cleanup.owned_survivors=@(Get-RunnerSurvivors $script:Auto)
            $cleanup.inference_mutex=Test-RunnerInferenceReleased
            if($cleanup.owned_survivors.Count -or $cleanup.inference_mutex -ne 'FREE'){throw 'CLEANUP_FAILED'}
        }catch{$cleanup.errors+=@($_.Exception.Message);$terminal='FAILED';$reason='MANDATORY_TEST_FAILED: CLEANUP '+$_.Exception.Message}
        finally{$mutex.ReleaseMutex();$mutex.Dispose();$cleanup.run_mutex_released=$true}
        Runner-Event 'F23_REVIEWER_MAINTENANCE_FINISHED' @{status=$terminal;reason=$reason;cleanup=$cleanup}
        $null=Write-RunnerReport -Project $ProjectRoot -RunId $script:RunId -State $script:RunState -Status $terminal -Technical $(if($terminal -eq 'COMPLETED'){'SUCCESS'}else{'FAIL'}) -Reason $reason -Duration ([datetimeoffset]::Now-$script:Started).TotalSeconds -Cleanup $cleanup
    }else{$mutex.Dispose()}
    $result=@{status=$(if($terminal -eq 'COMPLETED'){'PASS'}else{'FAIL'});reason=$reason;reviewer=$reviewer;reviewer_isolation=$isolation;completion_gate=$gate;cleanup=$cleanup;automatic_restart_budget_preserved=$true;historical_clock_preserved=$true;chatgpt_sends=0;worker_invocations=0}
    Write-RunnerJson (Join-Path $EvidenceRoot 'f23-reviewer-continuation.json') $result
}
$result|ConvertTo-Json -Depth 8
if($terminal -ne 'COMPLETED'){exit 1}
