[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$PayloadBase64)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if(-not(Test-Path -LiteralPath (Join-Path $root 'AGENTS.md'))){$root=Split-Path -Parent $PSScriptRoot}
. (Join-Path $root 'scripts/windows-process-job.ps1')
. (Join-Path $root 'scripts/security-guard.ps1')
$request=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($PayloadBase64))|ConvertFrom-Json
$e=[IO.Path]::GetFullPath($request.evidence);$scope=[IO.Path]::GetFullPath((Join-Path $root 'evidence'))+[IO.Path]::DirectorySeparatorChar
if(-not $e.StartsWith($scope,[StringComparison]::OrdinalIgnoreCase) -or -not(Test-Path -LiteralPath $e -PathType Container)){throw 'NEW_AUDIT_EVIDENCE_SCOPE_REQUIRED'}
$physical=Test-WorkspacePathGuard -TargetFilePath $e -WorkspacePath (Join-Path $root 'evidence') -Operation WRITE
if(-not $physical.Allowed){throw 'PHYSICAL_AUDIT_EVIDENCE_SCOPE_DENIED'}
if($request.name -notmatch '^[a-zA-Z0-9_.-]+$' -or $request.timeout -lt 1 -or $request.timeout -gt 300){throw 'AUDIT_GATE_ARGUMENT_DENIED'}
function Quote-Arg([string]$s){return '"'+($s -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
function Controller-Alive{$p=Get-Process -Id $request.controller_pid -ErrorAction SilentlyContinue;return $p -and $p.StartTime.ToUniversalTime().Ticks -eq $request.controller_birth_ticks}
$job=$null;$child=$null;$outFile=$null;$errFile=$null;$outTask=$null;$errTask=$null;$reason='';$code=$null;$started=[datetimeoffset]::Now;$identity=$null;$cleanup=$true
try{
 if(-not(Controller-Alive)){throw 'AUDIT_CONTROLLER_IDENTITY_MISMATCH'}
 $psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=$request.argv[0];$psi.Arguments=(@($request.argv|Select-Object -Skip 1)|ForEach-Object{Quote-Arg $_}) -join ' ';$psi.WorkingDirectory=$root;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
 $outPath=Join-Path $e ($request.name+'.stdout.txt');$errPath=Join-Path $e ($request.name+'.stderr.txt')
 $outFile=[IO.File]::Open($outPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read);$errFile=[IO.File]::Open($errPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::Read)
 $job=New-Object DaOwnedProcessJob;$child=[Diagnostics.Process]::Start($psi);try{$job.Assign($child.Handle)}catch{$child.Kill();throw}
 $identity=@{pid=$child.Id;start_ticks=$child.StartTime.ToUniversalTime().Ticks;executable=$psi.FileName;wrapper_pid=$PID;controller_pid=$request.controller_pid;controller_birth_ticks=$request.controller_birth_ticks}
 $outTask=$child.StandardOutput.BaseStream.CopyToAsync($outFile);$errTask=$child.StandardError.BaseStream.CopyToAsync($errFile)
 $deadline=[datetimeoffset]::Now.AddSeconds($request.timeout)
 while(-not $child.WaitForExit(100)){
  if(-not(Controller-Alive)){throw 'AUDIT_CONTROLLER_LOST'}
  if([datetimeoffset]::Now -ge $deadline){throw 'AUDIT_GATE_TIMEOUT'}
 }
 $code=$child.ExitCode
}catch{$reason=$_.Exception.Message}finally{
 if($job){$job.Dispose()}
 if($child -and -not $child.WaitForExit(5000)){$child.Kill();$cleanup=$child.WaitForExit(5000)}
 if($outTask -and -not $outTask.Wait(3000)){$cleanup=$false};if($errTask -and -not $errTask.Wait(3000)){$cleanup=$false}
 if($outFile){$outFile.Dispose()};if($errFile){$errFile.Dispose()}
 $result=@{status=$(if(-not $reason -and $code -eq 0 -and $cleanup){'PASS'}else{'FAIL'});exit_code=$code;reason=$reason;duration_seconds=([datetimeoffset]::Now-$started).TotalSeconds;owned_identity=$identity;owned_job_closed=$true;owned_process_exited=($null -eq $child -or $child.HasExited);stream_cleanup=$cleanup}
 [IO.File]::WriteAllText((Join-Path $e ($request.name+'.process.json')),($result|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false))
}
if($result.status -ne 'PASS'){exit 1}
