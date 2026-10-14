$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent $PSScriptRoot;$e=Join-Path $root 'evidence/f24-frontiers-20261014/regression';if($env:F24_PREFLIGHT_E){$e=Join-Path $env:F24_PREFLIGHT_E 'regression'}
$null=New-Item -ItemType Directory -Path $e -Force
$parsed=@{}
$files=@(Get-ChildItem -LiteralPath (Join-Path $root 'runner') -Filter '*.ps1')
$files+=@(Get-Item -LiteralPath (Join-Path $root 'scripts/consultar-chatgpt.ps1'),(Join-Path $root 'scripts/wait-chatgpt-child.ps1'))
foreach($file in $files){$tokens=$null;$errors=$null;$null=[Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors);if($errors.Count){throw ($errors|Out-String)};$parsed[$file.Name]='PASS'}
@{status='PASS';files=$parsed}|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $e 'syntax.json') -Encoding UTF8
. (Join-Path $root 'scripts/inference-lock.ps1')
function Child-Lock {
    $script="`$ErrorActionPreference='Stop';. '"+(Join-Path $root 'scripts/inference-lock.ps1')+"';`$t=Acquire-InferenceLock -Owner 'frontier-child' -TimeoutSeconds 1 -InfraPath '"+$root+"';`$ok=`$t.Acquired;if(`$ok){`$null=Release-InferenceLock -LockToken `$t};@{acquired=`$ok}|ConvertTo-Json -Compress"
    $info=New-Object Diagnostics.ProcessStartInfo
    $info.FileName='powershell.exe';$info.Arguments='-NoProfile -NonInteractive -EncodedCommand '+[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($script))
    $info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
    $child=[Diagnostics.Process]::Start($info);$stdout=$child.StandardOutput.ReadToEndAsync();$stderr=$child.StandardError.ReadToEndAsync()
    try{if(-not $child.WaitForExit(10000)){$child.Kill();$null=$child.WaitForExit(3000);throw 'LOCK_CHILD_TIMEOUT'};if($child.ExitCode -ne 0){throw $stderr.Result};return ($stdout.Result|ConvertFrom-Json).acquired}finally{$child.Dispose()}
}
$token=Acquire-InferenceLock -Owner 'frontier-parent' -TimeoutSeconds 1 -InfraPath $root
if(-not $token.Acquired){throw 'FOREIGN_INFERENCE_LOCK_HELD'}
try{if(Child-Lock){throw 'CONCURRENT_INFERENCE_WAS_ALLOWED'}}finally{$null=Release-InferenceLock -LockToken $token}
if(-not(Child-Lock)){throw 'INFERENCE_LOCK_NOT_RELEASED'}
@{status='PASS';cross_process_exclusion=$true;released_and_reacquired=$true;inference_requests=0}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $e 'inference-lock.json') -Encoding UTF8
@{status='PASS';syntax='PASS';inference_lock='PASS'}|ConvertTo-Json
