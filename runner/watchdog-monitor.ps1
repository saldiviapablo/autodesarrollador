param([string]$ProjectRoot,[int]$ParentId,[long]$ParentStartTicks,[int]$StaleSeconds=120)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
$auto=Join-Path $ProjectRoot '.autopilot';$signal=Join-Path $auto 'WATCHDOG-SIGNAL.json'
while($true){
    $parent=Get-Process -Id $ParentId -ErrorAction SilentlyContinue
    if(-not $parent -or $parent.StartTime.ToUniversalTime().Ticks -ne $ParentStartTicks){break}
    try{
        $hb=Get-Content -LiteralPath (Join-Path $auto 'HEARTBEAT.json') -Raw -Encoding UTF8|ConvertFrom-Json
        $age=([datetimeoffset]::Now-[datetimeoffset]::Parse($hb.timestamp)).TotalSeconds
        if($age -gt $StaleSeconds){
            $diagnostic=@{kind='HEARTBEAT_STALE';age_seconds=$age;parent_pid=$ParentId;start_ticks=$ParentStartTicks}
            $diagnostic|ConvertTo-Json|Set-Content -LiteralPath $signal -Encoding UTF8
            # Independent failover: only the recorded, still-identical owned parent can be stopped.
            Start-Sleep -Milliseconds 300
            $latest=Get-Content -LiteralPath (Join-Path $auto 'HEARTBEAT.json') -Raw -Encoding UTF8|ConvertFrom-Json
            if(([datetimeoffset]::Now-[datetimeoffset]::Parse($latest.timestamp)).TotalSeconds -gt $StaleSeconds){
                $root=Split-Path -Parent $PSScriptRoot;. (Join-Path $root 'scripts/state-manager.ps1')
                $state=Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
                $state.status='FAILED';$state.current_phase='WATCHDOG_FAILOVER';$state.current_task='HEARTBEAT_STALE';$state.next_action='Recover from persisted state; no blind restart'
                $null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
                $null=Update-AutopilotHeartbeat -AutopilotDir $auto -RunId $state.run_id -ProcessId $ParentId -Status 'FAILED' -CurrentTask 'watchdog stale heartbeat'
                $diagnostic|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $auto 'reports/watchdog-failure.json') -Encoding UTF8
                $again=Get-Process -Id $ParentId -ErrorAction SilentlyContinue
                if($again -and $again.StartTime.ToUniversalTime().Ticks -eq $ParentStartTicks){
                    if(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')){Remove-Item -LiteralPath (Join-Path $auto 'LOCK.json')}
                    Stop-Process -Id $ParentId -Force
                }
            }
            break
        }
        @{parent_pid=$ParentId;heartbeat_age=$age;monitor='WATCHDOG';timestamp=[datetimeoffset]::Now.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $auto 'WATCHDOG.json') -Encoding UTF8
    }catch{}
    Start-Sleep -Milliseconds 500
}
