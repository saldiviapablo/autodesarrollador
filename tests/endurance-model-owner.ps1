[CmdletBinding()]
param([Parameter(Mandatory=$true)][int]$ControllerPid,[Parameter(Mandatory=$true)][long]$ControllerBirthTicks,[Parameter(Mandatory=$true)][string]$EvidenceRoot,[Parameter(Mandatory=$true)][string]$Workspace)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
if(-not(Test-Path -LiteralPath (Join-Path $root 'AGENTS.md'))){$root=Split-Path -Parent $PSScriptRoot}
. (Join-Path $root 'scripts/windows-process-job.ps1')
function Quote-Arg([string]$v){if($v -notmatch '[\s"]'){return $v};return '"'+($v -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
function Save-Owner([string]$n,$v){[IO.File]::WriteAllText((Join-Path $EvidenceRoot $n),($v|ConvertTo-Json -Depth 12),[Text.UTF8Encoding]::new($false))}
function Parent-Alive{$p=Get-Process -Id $ControllerPid -ErrorAction SilentlyContinue;return $p -and $p.StartTime.ToUniversalTime().Ticks -eq $ControllerBirthTicks}
$proc=$null;$job=$null;$status='FAIL';$reason='';$start=[datetimeoffset]::Now
try{
 if(-not(Parent-Alive)){throw 'CONTROLLER_IDENTITY_MISMATCH'}
 $r=(& C:/Python314/python.exe (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n";$cfg=$r|ConvertFrom-Json;$l=$cfg.llama
 if($l.alias -ne 'qwen36' -or $l.host -ne '127.0.0.1' -or $l.port -ne 8080 -or $l.ctx_size -ne 65536 -or $l.parallel -ne 1){throw 'FROZEN_MODEL_CONFIGURATION_CHANGED'}
 if(@(Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue).Count){throw 'MODEL_PORT_ALREADY_OWNED_NO_ADOPTION_BY_CONTROLLER'}
 $argsList=@('-m',$l.model,'--alias',$l.alias,'--host',$l.host,'--port',[string]$l.port,'--ctx-size',[string]$l.ctx_size,'--parallel',[string]$l.parallel,'--cpu-moe','--n-gpu-layers',[string]$l.n_gpu_layers,'--flash-attn','on','--cache-type-k',$l.cache_type_k,'--cache-type-v',$l.cache_type_v,'--jinja')
 $psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=$l.executable;$psi.Arguments=($argsList|ForEach-Object{Quote-Arg $_}) -join ' ';$psi.WorkingDirectory=$Workspace;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
 $job=New-Object DaOwnedProcessJob;$proc=[Diagnostics.Process]::Start($psi);try{$job.Assign($proc.Handle)}catch{$proc.Kill();throw}
 $stdout=$proc.StandardOutput.ReadToEndAsync();$stderr=$proc.StandardError.ReadToEndAsync()
 $identity=@{pid=$proc.Id;start_ticks=$proc.StartTime.ToUniversalTime().Ticks;executable=$l.executable;arguments=$argsList;owner_pid=$PID;controller_pid=$ControllerPid;controller_birth_ticks=$ControllerBirthTicks;ownership='OWNED_BY_ENDURANCE_CONTROLLER_NOT_CHILD_RUN'}
 Save-Owner 'model-identity.json' $identity
 $deadline=[datetimeoffset]::Now.AddSeconds($cfg.runner.llama_start_timeout_seconds);$ready=$false
 while([datetimeoffset]::Now -lt $deadline){
  if(-not(Parent-Alive)){throw 'CONTROLLER_LOST'};if($proc.HasExited){throw 'MODEL_START_FAILED'}
  try{$h=Invoke-RestMethod -Uri $l.health_endpoint -TimeoutSec 2;if($h.status -eq 'ok'){$ready=$true;break}}catch{}
  Start-Sleep -Milliseconds 250
 }
 if(-not $ready){throw 'MODEL_HEALTH_TIMEOUT'}
 Save-Owner 'model-ready.json' @{status='PASS';at=[datetimeoffset]::Now.ToString('o');identity=$identity}
 while(-not(Test-Path -LiteralPath (Join-Path $EvidenceRoot 'MODEL-STOP'))){
  if(-not(Parent-Alive)){throw 'CONTROLLER_LOST'};if($proc.HasExited){throw 'MODEL_EXITED_DURING_STAGE'}
  Start-Sleep -Milliseconds 500
 }
 $status='PASS'
}catch{$reason=$_.Exception.Message}finally{
 if($job){$job.Dispose()};if($proc){
  if(-not $proc.WaitForExit(5000)){$proc.Kill();if(-not $proc.WaitForExit(5000)){$status='FAIL';$reason='OWNED_MODEL_CLEANUP_TIMEOUT'}}
  if($stdout -and $stdout.Wait(3000)){[IO.File]::WriteAllText((Join-Path $EvidenceRoot 'model.stdout.txt'),$stdout.Result,[Text.UTF8Encoding]::new($false))}
  if($stderr -and $stderr.Wait(3000)){[IO.File]::WriteAllText((Join-Path $EvidenceRoot 'model.stderr.txt'),$stderr.Result,[Text.UTF8Encoding]::new($false))}
 }
 Save-Owner 'model-cleanup.json' @{status=$status;reason=$reason;duration_seconds=([datetimeoffset]::Now-$start).TotalSeconds;model_exited=($null -eq $proc -or $proc.HasExited);owned_job_closed=$true}
}
if($status -ne 'PASS'){exit 1}
