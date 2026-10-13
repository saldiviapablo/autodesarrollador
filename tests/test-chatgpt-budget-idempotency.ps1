$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$project=Join-Path $root 'sandbox/chatgpt-idempotency'
if(-not(Test-Path -LiteralPath (Join-Path $project '.autopilot/STATE.json'))){
    & (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $project -Objective 'Bridge idempotency and ambiguity reconciliation' -AcceptanceCriteria @('T-CHATGPT-010 PASS','budget and domain controls PASS')|Out-Null
}
$statePath=Join-Path $project '.autopilot/STATE.json'
$state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
$state|Add-Member -MemberType NoteProperty -Name chatgpt -Value @{queries_used=1;max_queries=1} -Force
$state|ConvertTo-Json -Depth 15|Set-Content -LiteralPath $statePath -Encoding UTF8
$real=Get-Content -LiteralPath (Join-Path $root 'evidence/chatgpt-idempotency/real-tests.json') -Raw -Encoding UTF8|ConvertFrom-Json
$retry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question 'duplicate id must not send' -ConsultationId $real.normal_id -StatePath $statePath -MaxQueries 1
$blocked=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question 'budget must block before browser' -ConsultationId ('budget-'+[guid]::NewGuid().ToString('N')) -StatePath $statePath -MaxQueries 1
$after=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
$checks=@{completed_retry_at_exhausted_budget=($retry.Status -eq 'ALREADY_SENT' -and $retry.ResultObj.no_resend);new_id_budget_blocked=($blocked.status -eq 'CHATGPT_BUDGET_EXCEEDED');counter_not_incremented_by_retry=($after.chatgpt.queries_used -eq 1);browser_not_opened=(-not(Get-NetTCPConnection -LocalPort 9222 -State Listen -ErrorAction SilentlyContinue))}
$after.chatgpt.queries_used=0
$after|ConvertTo-Json -Depth 15|Set-Content -LiteralPath $statePath -Encoding UTF8
$mock=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question 'fake secret password=must-redact' -MockResponse 'SAFE_MOCK' -ConsultationId ('mock-budget-'+[guid]::NewGuid().ToString('N')) -StatePath $statePath -MaxQueries 1
$persisted=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
$checks['logical_attempt_persisted_with_strict_schema']=($mock.Status -eq 'SUCCESS' -and $persisted.chatgpt.queries_used -eq 1)
$invalidPath=Join-Path $project '.autopilot/invalid-state-fixture.json'
try{
    $persisted|Add-Member -MemberType NoteProperty -Name bypass -Value $true
    $persisted|ConvertTo-Json -Depth 15|Set-Content -LiteralPath $invalidPath -Encoding UTF8
    $invalid=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question 'must not send' -StatePath $invalidPath -ConsultationId ('invalid-'+[guid]::NewGuid().ToString('N')) -MockResponse 'FORBIDDEN'
    $checks['invalid_explicit_state_denied']=($invalid.Status -eq 'INVALID_STATE_DENY')
}finally{if(Test-Path -LiteralPath $invalidPath){Remove-Item -LiteralPath $invalidPath}}
$result=@{status=$(if($checks.Values -notcontains $false){'PASS'}else{'FAIL'});checks=$checks}
$result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $root 'evidence/chatgpt-idempotency/budget.json') -Encoding UTF8
if($result.status -ne 'PASS'){throw ($result|ConvertTo-Json)}
