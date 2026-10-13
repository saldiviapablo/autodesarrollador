param([Parameter(Mandatory=$true)][string]$ProjectPath,[int]$TimeoutSeconds=300,[string]$HostAddress='127.0.0.1')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if($HostAddress -ne '127.0.0.1'){return @{status='DENY';reason='NON_LOOPBACK_DENIED'}}
. (Join-Path $root 'scripts/windows-process-job.ps1')
$cfg=((& C:/Python314/python.exe (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
function Quote-Argument([string]$Value){return '"'+($Value -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
$job=New-Object DaOwnedProcessJob
$proc=$null
$directory=Join-Path $root 'runtime/dashboard-jobs';New-Item -ItemType Directory -Path $directory -Force|Out-Null
$ready=Join-Path $directory ([guid]::NewGuid().ToString('N')+'.ready');$assigned=[IO.Path]::ChangeExtension($ready,'assigned')
try{
    $psi=New-Object Diagnostics.ProcessStartInfo
    $psi.FileName=$cfg.document_extraction.native_python
    $psi.Arguments=(@('-I',(Join-Path $root 'scripts/governed-dashboard.py'),'--project',$ProjectPath,'--host',$HostAddress)|ForEach-Object{Quote-Argument $_}) -join ' '
    $psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    $psi.EnvironmentVariables['DA_DASHBOARD_JOB_READY']=$ready;$psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE']='1'
    $proc=[Diagnostics.Process]::Start($psi);$job.Assign($proc.Handle)
    $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
    $deadline=(Get-Date).AddSeconds(15)
    while(-not(Test-Path -LiteralPath $ready) -and (Get-Date) -lt $deadline -and -not $proc.HasExited){Start-Sleep -Milliseconds 30}
    if(-not(Test-Path -LiteralPath $ready)){throw 'DASHBOARD_READY_HANDSHAKE_FAILED'}
    $childPid=[int](Get-Content -LiteralPath $ready -Raw)
    $child=Get-Process -Id $childPid -ErrorAction Stop
    # The child reported itself before server imports/bind and must descend from our launcher.
    $identity=Get-CimInstance Win32_Process -Filter ('ProcessId='+$childPid)
    if($childPid -ne $proc.Id -and $identity.ParentProcessId -ne $proc.Id){throw 'DASHBOARD_CHILD_OWNERSHIP_DENIED'}
    $job.Assign($child.Handle);[IO.File]::WriteAllText($assigned,$childPid.ToString())
    $expired=-not $proc.WaitForExit($TimeoutSeconds*1000)
    $result=@{status=$(if($expired){'TIMEOUT'}else{'STOPPED'});owned_launcher_pid=$proc.Id;owned_server_pid=$childPid;timeout_seconds=$TimeoutSeconds;local_inferences=0}
}finally{
    $job.Dispose()
    foreach($path in @($ready,$assigned)){if(Test-Path -LiteralPath $path){Remove-Item -LiteralPath $path}}
}
if($proc){$null=$proc.WaitForExit(5000)}
if($child){$null=$child.WaitForExit(5000)}
$result.cleanup_ok=($child -and $child.HasExited)
$result
