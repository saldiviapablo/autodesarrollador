function Get-RunnerSurvivors([string]$Auto,[int]$ExcludePid=0){
    $alive=@()
    foreach($line in @(Get-Content -LiteralPath (Join-Path $Auto 'EVENTS.jsonl') -Encoding UTF8 -ErrorAction SilentlyContinue)){
        try{
            $evt=$line|ConvertFrom-Json
            if($evt.type -ne 'PROCESS_STARTED' -or $evt.payload.pid -eq $ExcludePid){continue}
            $record=$evt.payload;$proc=Get-Process -Id $record.pid -ErrorAction SilentlyContinue
            if($proc -and $proc.StartTime.ToUniversalTime().Ticks -eq $record.start_ticks){$alive+=@($record)}
        }catch{}
    }
    return @($alive|Sort-Object pid -Unique)
}
function Test-RunnerInferenceReleased {
    # Query the real mutex; a metadata file alone cannot establish lock ownership.
    . (Join-Path $script:RunnerInfra 'scripts/inference-lock.ps1')
    $lease=Acquire-InferenceLock -Owner 'runner-cleanup-audit' -Purpose 'verify physical mutex after owned process teardown' -TimeoutSeconds 1 -InfraPath $script:RunnerInfra
    if($lease.Acquired){$null=Release-InferenceLock -LockToken $lease;return 'FREE'}
    return 'EXTERNAL_HOLDER_PRESERVED'
}
function Remove-RunnerOwnedLock([string]$Auto,[string]$RunId,[int]$OwnerPid){
    $path=Join-Path $Auto 'LOCK.json'
    if(Test-Path -LiteralPath $path){
        $lock=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
        if($lock.run_id -ne $RunId -or $lock.owner_pid -ne $OwnerPid){throw 'FOREIGN_LOCK_PRESERVED'}
        Remove-Item -LiteralPath $path
    }
}
