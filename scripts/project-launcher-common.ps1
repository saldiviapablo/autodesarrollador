# Shared process transport. JSON goes through strict UTF-8 stdin, never cmd parsing.
$script:LauncherRoot=Split-Path -Parent $PSScriptRoot
function Quote-LauncherArg([string]$Value){return '"'+($Value -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
function Start-LauncherChild([string]$Exe,[array]$Arguments,[string]$InputJson=''){
    $si=New-Object Diagnostics.ProcessStartInfo
    $si.FileName=$Exe;$si.Arguments=($Arguments|ForEach-Object{Quote-LauncherArg ([string]$_)}) -join ' '
    $si.WorkingDirectory=$script:LauncherRoot;$si.UseShellExecute=$false;$si.CreateNoWindow=$true
    $si.RedirectStandardOutput=$true;$si.RedirectStandardError=$true;$si.RedirectStandardInput=$true
    $si.StandardOutputEncoding=[Text.Encoding]::UTF8;$si.StandardErrorEncoding=[Text.Encoding]::UTF8
    [Console]::InputEncoding=New-Object Text.UTF8Encoding($false,$true)
    $si.EnvironmentVariables['PYTHONUTF8']='1';$si.EnvironmentVariables['PYTHONDONTWRITEBYTECODE']='1'
    $p=[Diagnostics.Process]::Start($si)
    $out=$p.StandardOutput.ReadToEndAsync();$err=$p.StandardError.ReadToEndAsync()
    if($InputJson){$bytes=(New-Object Text.UTF8Encoding($false,$true)).GetBytes($InputJson);$p.StandardInput.BaseStream.Write($bytes,0,$bytes.Length)}
    $p.StandardInput.Close()
    return @{process=$p;stdout=$out;stderr=$err}
}
function Invoke-OnboardingData($Request){
    $child=Start-LauncherChild 'C:/Python314/python.exe' @('-B',(Join-Path $script:LauncherRoot 'scripts/project_onboarding.py')) ($Request|ConvertTo-Json -Depth 50 -Compress)
    try{
        if(-not $child.process.WaitForExit(120000)){$child.process.Kill();throw 'ONBOARDING_DATA_TIMEOUT'}
        $value=$child.stdout.Result|ConvertFrom-Json
        if($child.process.ExitCode -ne 0 -or $value.status -ne 'PASS'){
            $failure=New-Object System.InvalidOperationException ('ONBOARDING_DENIED: '+$value.reason)
            $failure.Data['Response']=$value;throw $failure
        }
        return $value
    }finally{$child.process.Dispose()}
}
function Test-LauncherPid($IdValue,$Ticks){
    $p=Get-Process -Id $IdValue -ErrorAction SilentlyContinue
    return $p -and $p.StartTime.ToUniversalTime().Ticks -eq [long]$Ticks
}
function Read-LauncherPlannerStream([string]$Stream){
    $events=@();foreach($line in ($Stream -split '\r?\n')){if($line.Trim()){$events+=@($line|ConvertFrom-Json)}}
    $initial=@($events|Where-Object{$_.type -eq 'system' -and $_.subtype -eq 'init'})
    $results=@($events|Where-Object{$_.type -eq 'result'})
    if($initial.Count -ne 1 -or $results.Count -ne 1 -or -not $initial[0].session_id -or $results[0].session_id -cne $initial[0].session_id){throw 'PREFLIGHT_STREAM_SESSION_MISMATCH'}
    foreach($event in $events){
        if($event.type -in @('tool_use','tool_call','tool_result')){throw 'READONLY_PREFLIGHT_TOOL_CALL_DENIED'}
        foreach($part in @($event.message.content)){if($part.type -in @('tool_use','tool_call','tool_result')){throw 'READONLY_PREFLIGHT_TOOL_CALL_DENIED'}}
    }
    if(-not $results[0].text){throw 'PREFLIGHT_PLAN_RESULT_MISSING'}
    return @{text=$results[0].text;session_id=$initial[0].session_id;event_count=$events.Count;tools=0}
}
