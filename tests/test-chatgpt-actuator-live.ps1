# One explicitly authorized real test consultation. Never resend/reconcile on failure.
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$e=Join-Path $root 'evidence/f24-attempt6-preflight-20261014/controlled-send'
if(Test-Path -LiteralPath $e){throw 'CONTROLLED_TEST_ALREADY_PREPARED_NO_SECOND_TEST'}
$null=New-Item -ItemType Directory -Path $e
$id='test-send-actuator-'+[guid]::NewGuid().ToString('N')
$project=Join-Path $root ('sandbox/'+$id)
$question='Responde únicamente OK áéíóú ñ. Prueba única '+$id
$init=& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $project -Objective 'One controlled ChatGPT send actuator test only; not F24 E2E' -AcceptanceCriteria 'single physical action and captured response; retry no resend' -TimeBudgetMinutes 5
$auto=Join-Path $project '.autopilot';$state=Join-Path $auto 'STATE.json'
Write-RunnerJson (Join-Path $e 'identity.json') @{consultation_id=$id;project=$project;prompt=$question;historical_attempt5_touched=$false}
$passed=$false
try{
    $r=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -RawPrompt -Purpose test -ConsultationId $id -StatePath $state -TimeoutSeconds 60 -NewConversation -OutputPath (Join-Path $e 'response.json')
    if($r.Status -ne 'SUCCESS'){throw ('CONTROLLED_REAL_SEND_FAILED_NO_RETRY: '+$r.Status+' '+$r.Error)}
    $hash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($id)))).Replace('-','').ToLowerInvariant()
    $file=Join-Path $root ('runtime/chatgpt-consultations/'+$hash+'.json');$before=(Get-FileHash -LiteralPath $file).Hash
    $ledger=Get-Content -LiteralPath $file -Raw -Encoding UTF8|ConvertFrom-Json
    $x=$r.ResultObj
    if($x.physical_actions -ne 1 -or $x.user_turns_after -ne ($x.user_turns_before+1) -or $x.assistant_turns_after -ne ($x.assistant_turns_before+1) -or -not $x.composer_cleared -or $ledger.delivery_state -ne 'COMPLETED' -or -not $ledger.message_confirmed -or $ledger.send_attempts -ne 1 -or -not @($ledger.history|Where-Object {$_.to -eq 'SENT_CONFIRMED'}).Count){throw 'CONTROLLED_PROOF_FAILED_NO_RETRY'}
    $retry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -RawPrompt -Purpose test -ConsultationId $id -StatePath $state -TimeoutSeconds 15
    if($retry.Status -ne 'ALREADY_SENT' -or (Get-FileHash -LiteralPath $file).Hash -ne $before){throw 'CONTROLLED_IDEMPOTENCY_FAILED'}
    Get-ChildItem -LiteralPath (Split-Path $file) -Filter ($hash+'*')|ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $e}
    $passed=$true
    Write-RunnerJson (Join-Path $e 'RESULT.json') @{status='PASS';consultation_id=$id;send_method=$x.send_method;physical_actions=1;user_before=$x.user_turns_before;user_after=$x.user_turns_after;assistant_before=$x.assistant_turns_before;assistant_after=$x.assistant_turns_after;sent_confirmed=$true;response_captured=$true;delivery_state=$ledger.delivery_state;retry=$retry.Status;additional_actions=0;composer_empty=$x.composer_cleared}
}finally{
    $s=Get-Content -LiteralPath $state -Raw -Encoding UTF8|ConvertFrom-Json
    $s.status='ABORTED';$s.next_action='Controlled actuator test closed; no full Runner execution claimed'
    $null=Write-AtomicState -StateObj $s -AutopilotDir $auto -ValidateTransition $false
    Remove-RunnerOwnedLock $auto $s.run_id $PID
    Write-RunnerJson (Join-Path $e 'cleanup.json') @{status='PASS';lock_released=(-not(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')));browser_preexisting_preserved=$true;test_passed=$passed;inference_mutex=(Test-RunnerInferenceReleased)}
}
Get-Content -LiteralPath (Join-Path $e 'RESULT.json') -Raw
