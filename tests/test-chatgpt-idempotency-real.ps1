$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$evidence=Join-Path $root 'evidence/chatgpt-idempotency'
New-Item -ItemType Directory -Path $evidence -Force|Out-Null
$id='idemp-'+[guid]::NewGuid().ToString('N')
$unknownId='ambiguous-'+[guid]::NewGuid().ToString('N')
function Save-Bridge([string]$Name,$Value){$Value|ConvertTo-Json -Depth 10|Set-Content -LiteralPath (Join-Path $evidence ($Name+'.json')) -Encoding UTF8}
try{
    $utf8=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action unicode-roundtrip -TimeoutSeconds 30
    Save-Bridge 'real-utf8' $utf8
    if($utf8.Status -ne 'SUCCESS'){throw 'UTF8 failed'}
    $question="Prueba UTF-8: áéíóú ñ ¿Dónde? — € °. Responde solamente IDEMPOTENCY_REAL_OK. ID $id"
    $normal=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -Purpose test -RawPrompt -ConsultationId $id -TimeoutSeconds 45
    Save-Bridge 'real-first' $normal
    if($normal.Status -ne 'SUCCESS'){throw ('Real consultation failed: '+$normal.Status)}
    $retry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $question -Purpose test -RawPrompt -ConsultationId $id -TimeoutSeconds 15
    Save-Bridge 'real-retry' $retry
    if($retry.Status -ne 'ALREADY_SENT' -or -not $retry.ResultObj.no_resend){throw 'Completed ID duplicated'}
    $n=$normal.ResultObj
    if($n.user_turns_after -ne $n.user_turns_before+1 -or $n.assistant_turns_after -ne $n.assistant_turns_before+1){throw 'Normal exact turn gate failed'}
    $ambiguousQuestion="Prueba de entrega ambigua. Responde solamente AMBIGUOUS_RECONCILED_OK. ID $unknownId"
    # A 1s response deadline expires before the two stability observations required by the bridge.
    $ambiguous=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $ambiguousQuestion -Purpose test -RawPrompt -ConsultationId $unknownId -TimeoutSeconds 1
    Save-Bridge 'real-unknown-delivery' $ambiguous
    if($ambiguous.Status -ne 'UNKNOWN_DELIVERY'){throw ('Expected delivery ambiguity, got '+$ambiguous.Status)}
    $unknownRetry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $ambiguousQuestion -Purpose test -RawPrompt -ConsultationId $unknownId -TimeoutSeconds 10
    Save-Bridge 'real-unknown-retry' $unknownRetry
    if($unknownRetry.Status -ne 'UNKNOWN_DELIVERY' -or -not $unknownRetry.ResultObj.no_resend){throw 'Ambiguous ID allowed blind resend'}
    $reconciled=$null
    for($i=0;$i -lt 6;$i++){
        Start-Sleep -Seconds 2
        $reconciled=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action reconcile -ConsultationId $unknownId -TimeoutSeconds 15
        if($reconciled.Status -eq 'ALREADY_SENT'){break}
    }
    Save-Bridge 'real-reconciled' $reconciled
    if($reconciled.Status -ne 'ALREADY_SENT' -or -not $reconciled.ResultObj.no_resend -or -not $reconciled.ResultObj.reconciled){throw 'Read-only reconciliation failed'}
    $r=$reconciled.ResultObj
    if($r.user_turns_after -ne $r.user_turns_before+1 -or $r.assistant_turns_after -ne $r.assistant_turns_before+1){throw 'Ambiguous exact turn gate failed'}
    $checks=@{real_send_once=$true;completed_retry_no_resend=$true;unknown_delivery_no_blind_resend=$true;reconciled_without_send=$true;user_turns_plus_one=$true;assistant_turns_plus_one=$true;utf8=($utf8.ResultObj.unicode_roundtrip -eq 'PASS');domain_exact=($normal.ResultObj.url -match '^https://chatgpt[.]com(?:/|$)')}
    @{status='PASS';test_id='T-CHATGPT-010';checks=$checks;normal_id=$id;ambiguous_id=$unknownId;real_queries=2}|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $evidence 'real-tests.json') -Encoding UTF8
}finally{
    $cleanup=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Action close-browser -TimeoutSeconds 25
    Save-Bridge 'cleanup' $cleanup
}
