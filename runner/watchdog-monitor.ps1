param([string]$ProjectRoot,[int]$ParentId,[long]$ParentStartTicks,[int]$StaleSeconds=120)
$ErrorActionPreference='Stop'
$auto=Join-Path $ProjectRoot '.autopilot';$signal=Join-Path $auto 'WATCHDOG-SIGNAL.json'
while($true){
    $parent=Get-Process -Id $ParentId -ErrorAction SilentlyContinue
    if(-not $parent -or $parent.StartTime.ToUniversalTime().Ticks -ne $ParentStartTicks){break}
    try{
        $hb=Get-Content -LiteralPath (Join-Path $auto 'HEARTBEAT.json') -Raw -Encoding UTF8|ConvertFrom-Json
        $age=([datetimeoffset]::Now-[datetimeoffset]::Parse($hb.timestamp)).TotalSeconds
        if($age -gt $StaleSeconds){@{kind='HEARTBEAT_STALE';age_seconds=$age;parent_pid=$ParentId}|ConvertTo-Json|Set-Content -LiteralPath $signal -Encoding UTF8;break}
        @{parent_pid=$ParentId;heartbeat_age=$age;monitor='WATCHDOG';timestamp=[datetimeoffset]::Now.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $auto 'WATCHDOG.json') -Encoding UTF8
    }catch{}
    Start-Sleep -Milliseconds 500
}
