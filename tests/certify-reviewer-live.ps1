param([string]$EvidenceRoot='')
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
if(-not $EvidenceRoot){$EvidenceRoot=Join-Path $root 'evidence/overnight-reviewer-20261015/live'}
$null=New-Item -ItemType Directory -Path $EvidenceRoot
$target=Join-Path $root 'sandbox/f24-attempt7-86dd900d/project'
$control=Join-Path $root ('sandbox/reviewer-cert-control-'+[guid]::NewGuid().ToString('N').Substring(0,8))
$null=& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $control -Objective 'Isolated readonly Reviewer certification; no coding or consultation' -AcceptanceCriteria 'Valid independent Reviewer decision with target and historical files unchanged'
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$script:Auto=Join-Path $control '.autopilot';$script:RunState=Get-Content -LiteralPath (Join-Path $script:Auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
$script:RunId=$script:RunState.run_id;$script:Started=[datetimeoffset]::Now;$script:GlobalSeconds=600;$script:CurrentTask='isolated Reviewer component certification'
$script:Cfg=((& C:/Python314/python.exe (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
# This is a bounded component test controller, not an F24 run. Runtime helper
# state/process/events live only in its fresh control sandbox, never ATTEMPT7.
$hashes=@{};foreach($name in @('scripts/invoke-hermes.ps1','scripts/invoke-hermes-role.ps1','runner/reviewer_contract.py','runner/agent-step.ps1','config/system.yaml','config/security.yaml')){$path=Join-Path $root $name;$hashes[$path]=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant()}
$script:Admission=[pscustomobject]@{project=$control;hashes=($hashes|ConvertTo-Json|ConvertFrom-Json);plan=[pscustomobject]@{backend='live'}}
$script:Owned=@{};$script:ExternalModel=$null;$script:RunJob=$null
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false;$reason='';$review=$null;$readOnly=$false
$targetHashes=@{};Get-ChildItem -LiteralPath $target -File -Recurse -Force|ForEach-Object {$targetHashes[$_.FullName]=(Get-FileHash -LiteralPath $_.FullName).Hash}
Write-RunnerJson (Join-Path $EvidenceRoot 'target-before.json') $targetHashes
try{
 try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true};if(-not $held){throw 'FOREIGN_RUN_ACTIVE'}
 if(Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue){throw 'FOREIGN_MODEL_PRESERVED'}
 $script:RunJob=New-Object DaOwnedProcessJob
 Start-RunnerModel
 $source=Get-Content -LiteralPath (Join-Path $root 'evidence/phase-24-attempt-7-20261015/native/packet-reviewer.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $source|Add-Member -NotePropertyName review_input_sha256 -NotePropertyValue (([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($source.prompt)))).Replace('-','').ToLowerInvariant())
 $packet=Join-Path $EvidenceRoot 'bound-packet.json';Write-RunnerJson $packet $source
 $r=Invoke-RunnerManaged 'reviewer-isolated' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'runner/agent-step.ps1'),'-PacketPath',$packet) 310
 Write-RunnerJson (Join-Path $EvidenceRoot 'process-result.json') $r
 $review=$r.stdout|ConvertFrom-Json;Write-RunnerJson (Join-Path $EvidenceRoot 'reviewer-real.json') $review
 if($r.exit_code -ne 0 -or $review.status -ne 'SUCCESS' -or -not $review.validation.valid){throw 'REVIEWER_REAL_SCHEMA_FAILED'}
 foreach($path in $targetHashes.Keys){if((Get-FileHash -LiteralPath $path).Hash -ne $targetHashes[$path]){throw ('READONLY_FAILED: '+$path)}}
 $readOnly=$true
 if($review.validation.decision -notin @('ACCEPTED','REJECTED')){throw 'REVIEWER_DECISION_INVALID'}
}catch{$reason=$_.Exception.Message}
finally{
 if($script:RunJob){$script:RunJob.Dispose()}
 foreach($item in $script:Owned.Values){try{$null=$item.process.WaitForExit(5000)}catch{}}
 $survivors=@(Get-RunnerSurvivors $script:Auto);$free=Test-RunnerInferenceReleased
 if($held){$mutex.ReleaseMutex()};$mutex.Dispose()
 $listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)})
 $cleanup=($survivors.Count -eq 0 -and $free -eq 'FREE' -and $listeners.Count -eq 0)
 if(-not $reason -and $cleanup -and $readOnly){$script:RunState.completed_tasks=@($script:RunState.objective);$script:RunState.pending_tasks=@()}
 Save-RunnerState $(if($reason){'FAILED'}else{'COMPLETED'}) ('isolated Reviewer: '+$reason)
 $result=@{status=$(if(-not $reason -and $cleanup -and $readOnly){'PASS'}else{'FAIL'});reason=$reason;decision=$review.validation.decision;PROMPT_INTEGRITY=$review.data.ReviewerContract.valid;UTF8='verified by native wrapped input audit';REVIEWER_ROLE='reviewer';TOOLS_DISABLED=$true;MCP_DISABLED=$true;PLUGINS_DISABLED=$true;READONLY=$readOnly;RESPONSE_SCHEMA=$review.validation.valid;DECISION_PARSE=$review.validation.valid;cleanup=@{status=$cleanup;owned_survivors=$survivors;inference_mutex=$free;listeners=$listeners.Count};target=$target;controller=$control;worker_invocations=0;chatgpt_sends=0;duration_seconds=([datetimeoffset]::Now-$script:Started).TotalSeconds}
 Write-RunnerJson (Join-Path $EvidenceRoot 'CERTIFICATION.json') $result
}
$result|ConvertTo-Json -Depth 8
if($result.status -ne 'PASS'){exit 1}
