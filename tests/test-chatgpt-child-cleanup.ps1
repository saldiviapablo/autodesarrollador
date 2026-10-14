$ErrorActionPreference='Stop'
. (Join-Path $PSScriptRoot '../scripts/wait-chatgpt-child.ps1')
$info=New-Object Diagnostics.ProcessStartInfo
$info.FileName='node.exe';$info.Arguments='-e "setInterval(()=>{},1000)"'
$info.UseShellExecute=$false;$info.CreateNoWindow=$true
$child=[Diagnostics.Process]::Start($info)
try{
    $id=$child.Id;$birth=$child.StartTime.ToUniversalTime().Ticks
    $normal=Wait-ChatGptChild $child 50
    if($normal -or -not $child.HasExited){throw 'CHILD_TIMEOUT_CLEANUP_FAILED'}
    @{status='PASS';child_pid=$id;start_ticks=$birth;timeout_exercised=$true;child_terminated=$true;browser_access=$false}|ConvertTo-Json
}finally{if(-not $child.HasExited){$child.Kill();$null=$child.WaitForExit(3000)};$child.Dispose()}
