param([Parameter(Mandatory=$true)][string]$ProjectRoot,[Parameter(Mandatory=$true)][string]$EvidenceRoot,[string]$Failure='',[double]$Duration=0)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1');. (Join-Path $root 'runner/report.ps1')
$script:Auto=Join-Path $ProjectRoot '.autopilot'
$script:RunState=Get-Content -LiteralPath (Join-Path $script:Auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
$script:RunId=$script:RunState.run_id
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
$cleanup=@{owned_survivors=@();errors=@();run_lock_removed=$false;run_mutex_released=$false;inference_mutex='NOT_CHECKED'}
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'FOREIGN_ACTIVE_RUN_PRESERVED'}
    $cleanup.owned_survivors=@(Get-RunnerSurvivors $script:Auto)
    if($cleanup.owned_survivors.Count){throw 'OWNED_PROCESS_SURVIVED'}
    $lockPath=Join-Path $script:Auto 'LOCK.json'
    if(Test-Path -LiteralPath $lockPath){
        $lock=Get-Content -LiteralPath $lockPath -Raw -Encoding UTF8|ConvertFrom-Json
        if($lock.run_id -ne $script:RunId -or [IO.Path]::GetFullPath($lock.project_root) -ne [IO.Path]::GetFullPath($ProjectRoot)){throw 'FOREIGN_LOCK_PRESERVED'}
        $owner=Get-Process -Id $lock.owner_pid -ErrorAction SilentlyContinue
        if($owner -and $owner.StartTime.ToUniversalTime() -le [datetimeoffset]::Parse($lock.started_at).UtcDateTime){throw 'LIVE_LOCK_OWNER_PRESERVED'}
        Remove-RunnerOwnedLock $script:Auto $script:RunId $lock.owner_pid
    }
    $cleanup.run_lock_removed=-not(Test-Path -LiteralPath $lockPath)
    $cleanup.inference_mutex=Test-RunnerInferenceReleased
    $cleanup.unexpected_listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object{$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)
    if($cleanup.inference_mutex -ne 'FREE' -or $cleanup.unexpected_listeners.Count){throw 'CLEANUP_FAILED'}
    if($Failure){
        $terminal='FAILED';if($Failure -match 'BLOCKED_REQUIRES_HUMAN'){$terminal='BLOCKED_REQUIRES_HUMAN'}
        Save-RunnerState $terminal $Failure
        Runner-Event 'LIVE_TEST_STOPPED' @{reason=$Failure;cleanup=$cleanup}
        $null=& (Join-Path $root 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $ProjectRoot -CheckpointId ('chk-live-stop-'+[datetime]::Now.ToString('yyyyMMddHHmmssfff')) -Reason $Failure
    }
}finally{if($held){$mutex.ReleaseMutex();$cleanup.run_mutex_released=$true};$mutex.Dispose()}
if($Failure){$null=Write-RunnerReport -Project $ProjectRoot -RunId $script:RunId -State $script:RunState -Status $terminal -Technical NOT_COMPLETED -Reason $Failure -Duration $Duration -Cleanup $cleanup}
Write-RunnerJson (Join-Path $EvidenceRoot 'cleanup-final.json') @{status='PASS';cleanup=$cleanup}
@{status='PASS';cleanup=$cleanup}|ConvertTo-Json -Depth 8
