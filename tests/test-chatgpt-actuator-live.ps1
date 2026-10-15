# One explicitly authorized real test consultation. Never resend/reconcile on failure.
param([switch]$ResumePreIntent)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$admission=Join-Path $root 'evidence/f24-admission-repair-20261014'
if($env:F24_PREFLIGHT_E){$admission=$env:F24_PREFLIGHT_E}
$e=Join-Path $admission 'controlled-send'
if((Test-Path -LiteralPath $e) -and -not $ResumePreIntent){throw 'CONTROLLED_TEST_ALREADY_PREPARED_NO_SECOND_TEST'}
if($ResumePreIntent){
    $old=Get-Content -LiteralPath (Join-Path $e 'identity.json') -Raw -Encoding UTF8|ConvertFrom-Json
    $failure=Get-Content -LiteralPath (Join-Path $e 'response.json') -Raw -Encoding UTF8|ConvertFrom-Json
    if($failure.error -notlike '*NEW_CHAT_CONTROL_UNAVAILABLE_OR_AMBIGUOUS*'){throw 'PREPARATION_RETRY_NOT_ALLOWED_AFTER_NAVIGATION_OR_DELIVERY'}
    $id=$old.consultation_id;$project=$old.project
    $status=(& node.exe (Join-Path $root 'tools/chatgpt-bridge.js') --action consultation-status --consultation-id $id|Out-String)|ConvertFrom-Json
    if($status.status -ne 'NOT_SEEN'){throw 'PREPARATION_RETRY_REQUIRES_NO_LEDGER'}
    $archive=Join-Path $e 'preparation-1';if(Test-Path -LiteralPath $archive){throw 'PREPARATION_RETRY_ALREADY_USED'}
    $null=New-Item -ItemType Directory -Path $archive
    foreach($n in @('identity.json','response.json','cleanup.json')){Copy-Item -LiteralPath (Join-Path $e $n) -Destination $archive}
}else{
    $null=New-Item -ItemType Directory -Path $e
    $id='test-send-actuator-'+[guid]::NewGuid().ToString('N')
    $project=Join-Path $root ('sandbox/'+$id)
}
$question='Responde únicamente OK áéíóú ñ. Prueba única '+$id
if(-not $ResumePreIntent){$init=& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $project -Objective 'One controlled ChatGPT send actuator test only; not F24 E2E' -AcceptanceCriteria 'single physical action and captured response; retry no resend' -TimeBudgetMinutes 5}
$auto=Join-Path $project '.autopilot';$state=Join-Path $auto 'STATE.json'
if(-not $ResumePreIntent){Write-RunnerJson (Join-Path $e 'identity.json') @{consultation_id=$id;project=$project;prompt=$question;historical_attempt5_touched=$false}}
$passed=$false
try{
    $r=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -RawPrompt -Purpose test -ConsultationId $id -StatePath $state -TimeoutSeconds 60 -NewConversation -OutputPath (Join-Path $e 'response.json')
    if($r.Status -ne 'SUCCESS'){throw ('CONTROLLED_REAL_SEND_FAILED_NO_RETRY: '+$r.Status+' '+$r.Error)}
    $hash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($id)))).Replace('-','').ToLowerInvariant()
    $file=Join-Path $root ('runtime/chatgpt-consultations/'+$hash+'.json');$before=(Get-FileHash -LiteralPath $file).Hash
    $ledger=Get-Content -LiteralPath $file -Raw -Encoding UTF8|ConvertFrom-Json
    $x=$r.ResultObj
    $expectedPromptSha=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($question.Trim())))).Replace('-','').ToLowerInvariant()
    $trace=@(Get-Content -LiteralPath (Join-Path $root ('runtime/chatgpt-consultations/'+$hash+'.trace.jsonl')) -Encoding UTF8|ForEach-Object {$_|ConvertFrom-Json})
    $names=@($trace|ForEach-Object {$_.event})
    if($x.prompt_sha256 -ne $expectedPromptSha -or $x.dom_sha256 -ne $expectedPromptSha -or -not $x.utf8_valid -or -not $x.source_text_equals_dom_text -or $names.IndexOf('PREPARED') -lt 0 -or $names.IndexOf('PREPARED') -ge $names.IndexOf('DELIVERY_INTENT') -or $names.IndexOf('SENT_CONFIRMED') -ge $names.IndexOf('RESPONSE_WAIT_START')){throw 'CONTROLLED_PREPARED_SHA_TRACE_PROOF_FAILED'}
    if(-not $x.fresh_chat_ready -or $x.user_turns_before -ne 0 -or $x.assistant_turns_before -ne 0 -or $x.physical_actions -ne 1 -or $x.user_turns_after -ne 1 -or $x.assistant_turns_after -ne 1 -or -not $x.composer_cleared -or $ledger.delivery_state -ne 'COMPLETED' -or -not $ledger.message_confirmed -or $ledger.send_attempts -ne 1 -or -not @($ledger.history|Where-Object {$_.to -eq 'SENT_CONFIRMED'}).Count){throw 'CONTROLLED_PROOF_FAILED_NO_RETRY'}
    $retry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -RawPrompt -Purpose test -ConsultationId $id -StatePath $state -TimeoutSeconds 15
    if($retry.Status -ne 'ALREADY_SENT' -or (Get-FileHash -LiteralPath $file).Hash -ne $before){throw 'CONTROLLED_IDEMPOTENCY_FAILED'}
    Get-ChildItem -LiteralPath (Split-Path $file) -Filter ($hash+'*')|ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $e}
    $passed=$true
    Write-RunnerJson (Join-Path $e 'RESULT.json') @{status='PASS';consultation_id=$id;send_method=$x.send_method;physical_actions=1;prepared_before_intent=$true;prompt_sha256=$expectedPromptSha;utf8=$true;sent_before_response_wait=$true;user_before=$x.user_turns_before;user_after=$x.user_turns_after;assistant_before=$x.assistant_turns_before;assistant_after=$x.assistant_turns_after;sent_confirmed=$true;response_captured=$true;delivery_state=$ledger.delivery_state;retry=$retry.Status;additional_actions=0;composer_empty=$x.composer_cleared}
}finally{
    $s=Get-Content -LiteralPath $state -Raw -Encoding UTF8|ConvertFrom-Json
    $s.status='ABORTED';$s.next_action='Controlled actuator test closed; no full Runner execution claimed'
    $null=Write-AtomicState -StateObj $s -AutopilotDir $auto -ValidateTransition $false
    Remove-RunnerOwnedLock $auto $s.run_id $PID
    Write-RunnerJson (Join-Path $e 'cleanup.json') @{status='PASS';lock_released=(-not(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')));browser_preexisting_preserved=$true;test_passed=$passed;inference_mutex=(Test-RunnerInferenceReleased)}
}
Get-Content -LiteralPath (Join-Path $e 'RESULT.json') -Raw
