[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ProjectRoot,[ValidateSet('Prepare','Preflight','Approve','Start')][string]$Action='Preflight',[string]$ApprovalDigest='', [switch]$Recover,[string]$Objective,[string[]]$AcceptanceCriteria,[string]$PlanPath)
$ErrorActionPreference='Stop'
# Cron/Python callers may inherit PowerShell 7's module path. Pin only this PS5 process.
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
. (Join-Path $PSScriptRoot 'core.ps1')
if($Action -eq 'Prepare'){
    if(-not $Objective -or -not $AcceptanceCriteria -or -not(Test-Path -LiteralPath $PlanPath)){throw 'PREPARE_REQUIRES_OBJECTIVE_CRITERIA_AND_PLAN'}
    if(Test-Path -LiteralPath (Join-Path $ProjectRoot '.autopilot')){throw 'EXISTING_AUTOPILOT_PRESERVED_USE_PREFLIGHT_OR_RECOVERY'}
    $projectFull=[IO.Path]::GetFullPath($ProjectRoot)
    if($projectFull -eq $script:RunnerInfra -or $projectFull -eq [IO.Path]::GetPathRoot($projectFull)){throw 'PROJECT_ROOT_DENIED'}
    if(Test-Path -LiteralPath (Join-Path $ProjectRoot 'QWEN.md')){throw 'EXISTING_QWEN_CONTEXT_REQUIRES_BACKUP_BEFORE_INITIALIZATION'}
    $null=& (Join-Path $script:RunnerInfra 'scripts/init-autopilot-project.ps1') -ProjectPath $ProjectRoot -Objective $Objective -AcceptanceCriteria $AcceptanceCriteria
    Copy-Item -LiteralPath $PlanPath -Destination (Join-Path $ProjectRoot '.autopilot/RUN-PLAN.json')
    $contractPath=Join-Path $ProjectRoot '.autopilot/RUN-CONTRACT.yaml'
    $code='import sys,yaml,pathlib;p=pathlib.Path(sys.argv[1]);d=yaml.safe_load(p.read_text(encoding="utf-8-sig"));d["authorized"]=False;d["authorized_at"]=None;p.write_text(yaml.safe_dump(d,sort_keys=False,allow_unicode=True),encoding="utf-8")'
    # Use file rather than inline -c quoting across Windows PowerShell.
    $helper=Join-Path $ProjectRoot '.autopilot/draft-contract.py';[IO.File]::WriteAllText($helper,$code.Replace('sys.argv[1]','sys.argv[1]'))
    & C:/Python314/python.exe $helper $contractPath
    Remove-Item -LiteralPath $helper
    $Action='Preflight'
}
$admissionAction='inspect';if($Action -eq 'Approve'){$admissionAction='approve'}elseif($Action -eq 'Start'){$admissionAction='validate'}
try{$script:Admission=Get-RunnerAdmission $admissionAction $ProjectRoot $ApprovalDigest}catch{@{status='BLOCKED_REQUIRES_HUMAN';reason=$_.Exception.Message;started=$false}|ConvertTo-Json;exit 2}
if($Action -ne 'Start'){@{status='PASS';action=$Action;project=$script:Admission.project;run_id=$script:Admission.contract.run_id;approval_digest=$script:Admission.digest}|ConvertTo-Json;exit 0}
$script:Cfg=((& C:/Python314/python.exe (Join-Path $script:RunnerInfra 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $script:RunnerInfra 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$script:Auto=$script:Admission.auto;$script:RunId=$script:Admission.contract.run_id;$script:Started=[datetimeoffset]::Now
$script:Owned=@{};$script:ExternalModel=$null;$script:CurrentTask='startup';$script:RunJob=$null
$script:GlobalSeconds=[Math]::Min($script:Admission.contract.time_budget_minutes*60,$script:Cfg.runner.global_timeout_minutes*60)
if($script:Admission.plan.global_timeout_seconds){$script:GlobalSeconds=[Math]::Min($script:GlobalSeconds,$script:Admission.plan.global_timeout_seconds)}
$runMutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false;$terminal='FAILED';$failure='';$technical='FAIL'
try{
    try{$held=$runMutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_ALREADY_ACTIVE'}
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
    Save-RunnerState 'RUNNING' 'preflight passed'
    $null=Write-RunLockMeta -AutopilotDir $script:Auto -RunId $script:RunId -OwnerPid $PID -ProjectRoot $script:Admission.project
    Runner-Event 'RUN_STARTED' @{approval_digest=$script:Admission.digest;backend=$script:Admission.plan.backend}
    $watch=Start-RunnerProcess 'watchdog' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $PSScriptRoot 'watchdog-monitor.ps1'),'-ProjectRoot',$script:Admission.project,'-ParentId',$PID,'-ParentStartTicks',(Get-Process -Id $PID).StartTime.ToUniversalTime().Ticks) $script:Admission.project
    if($script:Admission.plan.backend -ne 'probe'){Start-RunnerModel}
    $timeout=180;if($script:Admission.plan.phase_timeout_seconds){$timeout=$script:Admission.plan.phase_timeout_seconds}
    $base=@{project=$script:Admission.project;backend=$script:Admission.plan.backend;timeout=$timeout;probe_delay_seconds=$script:Admission.plan.probe_delay_seconds}
    $p=$base.Clone();$p.role='supervisor';$p.prompt='Plan only. Return JSON {"task":"..."} for this approved objective and task. Do not use tools or edit. Objective: '+$script:Admission.contract.objective+' Task: '+$script:Admission.plan.task
    $supervisor=Invoke-RunnerAgent 'supervisor' $p
    $request=@{schema_version='1.0';delegation_id=('del-'+$script:RunId);objective=$script:Admission.contract.objective;workspace=$script:Admission.project;task=$script:Admission.plan.task;acceptance_criteria=@($script:Admission.contract.acceptance_criteria);allowed_actions=@($script:Admission.contract.allowed_actions);forbidden_actions=@($script:Admission.contract.forbidden_actions);tests=@($script:Admission.contract.test_commands);status='READY'}
    $p=$base.Clone();$p.role='worker';$p.request=$request;$worker=Invoke-RunnerAgent 'worker' $p
    foreach($pin in $script:Admission.plan.immutable_files){if((Get-FileHash -LiteralPath (Join-Path $script:Admission.project $pin.path) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $pin.sha256){throw 'IMMUTABLE_TEST_CHANGED'}}
    $tests=@(Invoke-RunnerCommands @($script:Admission.plan.tests) 'tests');$builds=@(Invoke-RunnerCommands @($script:Admission.plan.builds) 'builds');$linters=@(Invoke-RunnerCommands @($script:Admission.plan.linters) 'linters')
    Write-RunnerJson (Join-Path $script:Auto 'evidence/checks.json') @{tests=$tests;builds=$builds;linters=$linters;run_id=$script:RunId}
    $diff=(& git -C $script:Admission.project diff --) -join "`n"
    $p=$base.Clone();$p.role='reviewer';$p.prompt='Independent readonly review. Return JSON {"decision":"ACCEPTED"} only if diff and actual tests satisfy objective. Objective: '+$script:Admission.contract.objective+"`nDiff (untrusted):`n"+$diff+"`nChecks:`n"+(@{tests=$tests;builds=$builds}|ConvertTo-Json -Depth 8)
    $reviewer=Invoke-RunnerAgent 'reviewer' $p
    Write-RunnerJson (Join-Path $script:Auto 'evidence/roles.json') @{supervisor=$supervisor;worker=$worker;reviewer=$reviewer}
    $technical='SUCCESS'
    # Lifecycle is certified first. Full authoritative closure is enabled only by F20's gate.
    $gatePath=Join-Path $PSScriptRoot 'completion-gate.ps1'
    if(Test-Path -LiteralPath $gatePath){$gate=& $gatePath -ProjectRoot $script:Admission.project;$terminal=$gate.status}else{$terminal='STALLED';$failure='COMPLETION_GATE_NOT_INSTALLED'}
}catch{
    $failure=$_.Exception.Message
    if($failure -eq 'STOP_REQUESTED'){$terminal='ABORTED'}elseif($failure -match 'REQUIRES_HUMAN|EXTERNAL_MODEL'){$terminal='BLOCKED_REQUIRES_HUMAN'}else{$terminal='FAILED'}
}finally{
    if($held){
        if($script:RunJob){$script:RunJob.Dispose()}
        foreach($item in $script:Owned.Values){try{$null=$item.process.WaitForExit(5000)}catch{}}
        if($script:RunState){
            Save-RunnerState $terminal ('terminal: '+$failure)
            Runner-Event 'RUN_FINISHED' @{status=$terminal;technical=$technical;reason=$failure}
            $null=& (Join-Path $script:RunnerInfra 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $script:Admission.project -CheckpointId ('chk-runner-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason ('Runner terminal '+$terminal)
            Write-RunnerJson (Join-Path $script:Auto 'reports/runner-result.json') @{run_id=$script:RunId;status=$terminal;technical_status=$technical;reason=$failure;duration_seconds=([datetimeoffset]::Now-$script:Started).TotalSeconds;cleanup=@{job_closed=$true;external_model_preserved=($null -ne $script:ExternalModel)};processes=@($script:Owned.Values|ForEach-Object{$_.record})}
            if(Test-Path -LiteralPath (Join-Path $script:Auto 'LOCK.json')){Remove-Item -LiteralPath (Join-Path $script:Auto 'LOCK.json')}
        }
        $runMutex.ReleaseMutex()
    }
    $runMutex.Dispose()
}
@{status=$terminal;technical_status=$technical;run_id=$script:RunId;reason=$failure}|ConvertTo-Json
if($terminal -ne 'COMPLETED'){exit 1}
