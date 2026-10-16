param()
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8;[Console]::InputEncoding=[Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot 'project-launcher-common.ps1')
. (Join-Path $script:LauncherRoot 'runner/core.ps1')
. (Join-Path $script:LauncherRoot 'runner/cleanup.ps1')
. (Join-Path $script:LauncherRoot 'runner/report.ps1')
$request=[Console]::In.ReadToEnd()|ConvertFrom-Json
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
$result=$null;$inspection=$null
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_ALREADY_ACTIVE'}
    $env:DA_LAUNCHER_MUTEX_HELD='1'
    $inspection=Invoke-OnboardingData @{action='inspect';project=$request.project}
    if($inspection.lock){
        $owner=Get-Process -Id $inspection.lock.owner_pid -ErrorAction SilentlyContinue
        if($owner -and $owner.StartTime.ToUniversalTime() -le ([datetimeoffset]$inspection.lock.started_at).UtcDateTime.AddSeconds(1)){throw 'EXISTING_LOCK_OWNER_ALIVE_PRESERVED'}
    }
    if($request.action -eq 'approve_plan'){
        Invoke-OnboardingData $request | ConvertTo-Json -Depth 15
    }elseif($request.action -eq 'prepare'){
        foreach($c in @($request.proposal.plan.tests)+@($request.proposal.plan.builds)+@($request.proposal.plan.linters)){
            if($c -and -not (Test-CommandGuard -CommandLine ($c.argv -join ' ') -WorkspacePath $request.project).Allowed){throw 'PLANNED_CHECK_COMMAND_DENIED'}
        }
        $result=Invoke-OnboardingData $request
        $auto=Join-Path $request.project '.autopilot'
        $lock=Get-Content -LiteralPath (Join-Path $auto 'LOCK.json') -Raw -Encoding UTF8|ConvertFrom-Json
        # The canonical initializer has exited. Preserve its metadata as evidence
        # before the existing exact-run/exact-owner cleanup operation.
        Copy-Item -LiteralPath (Join-Path $auto 'LOCK.json') -Destination (Join-Path $auto 'evidence/PREPARE-LOCK.json')
        Remove-RunnerOwnedLock $auto $result.run_id $lock.owner_pid
        $null=Invoke-OnboardingData @{action='git';project=$request.project}
        # Only the already persisted, exactly bound human plan decision may reach
        # this canonical approval. Prepare never authorizes the Worker by itself.
        $info=Get-RunnerAdmission inspect $request.project
        $null=Get-RunnerAdmission approve $request.project $info.digest
        $result|ConvertTo-Json -Depth 15
    }else{throw 'UNKNOWN_LAUNCHER_MUTATION'}
}catch{
    $reason=Sanitize-StringContent $_.Exception.Message;$cleanup='NO_NEW_PREPARATION'
    $response=$_.Exception.Data['Response']
    $ownedRun=$null
    if($result -and $result.run_id){$ownedRun=$result.run_id}
    elseif($response -and $response.preparation_applied){$ownedRun=$response.run_id}
    if($held -and $ownedRun -and $ownedRun -ne $inspection.run_id){
        try{
            $current=Get-RunnerAdmission inspect $request.project
            if($current.contract.run_id -ne $ownedRun){throw 'FOREIGN_PREPARATION_PRESERVED'}
            try{Write-RunnerPrestartBlock $current ('ONBOARDING_FAILED: '+$reason)}catch{
                # The canonical helper already terminalizes/checkpoints/removes
                # initializer metadata before reporting. Git may have no HEAD.
                Write-RunnerJson (Join-Path $current.auto 'reports/ONBOARDING-FAILURE.json') @{status='BLOCKED_REQUIRES_HUMAN';run_id=$ownedRun;reason=$reason;started=$false;canonical_report_error=(Sanitize-StringContent $_.Exception.Message)}
            }
            $after=Get-Content -LiteralPath (Join-Path $current.auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
            if($after.status -ne 'BLOCKED_REQUIRES_HUMAN' -or (Test-Path -LiteralPath (Join-Path $current.auto 'LOCK.json'))){throw 'ONBOARDING_CLEANUP_INCOMPLETE'}
            $cleanup='PASS'
        }catch{$cleanup='INCOMPLETE: '+(Sanitize-StringContent $_.Exception.Message)}
    }
    @{status='DENY';reason=$reason;cleanup=$cleanup}|ConvertTo-Json
    exit 2
}finally{
    Remove-Item Env:DA_LAUNCHER_MUTEX_HELD -ErrorAction SilentlyContinue
    if($held){$mutex.ReleaseMutex()};$mutex.Dispose()
}
