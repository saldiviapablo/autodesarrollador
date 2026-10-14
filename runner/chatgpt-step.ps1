param([string]$ProjectRoot)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot;$auto=Join-Path $ProjectRoot '.autopilot'
$plan=Get-Content -LiteralPath (Join-Path $auto 'RUN-PLAN.json') -Raw -Encoding UTF8|ConvertFrom-Json
$c=$plan.consultation
if(-not $c){throw 'CONSULTATION_PLAN_REQUIRED'}
$r=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $c.question -ConsultationId $c.id -StatePath (Join-Path $auto 'STATE.json') -TimeoutSeconds $c.response_timeout_seconds -NewConversation:$c.new_conversation -OutputPath (Join-Path $auto 'evidence/CHATGPT.json')
if($r.Status -eq 'SUCCESS'){
    $ledgerDir=Join-Path $root 'runtime/chatgpt-consultations'
    $hash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($c.id)))).Replace('-','').ToLowerInvariant()
    $ledger=Join-Path $ledgerDir ($hash+'.json')
    $before=(Get-FileHash -LiteralPath $ledger -Algorithm SHA256).Hash
    $beforeBudget=(Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json).chatgpt.queries_used
    $retry=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question $c.question -ConsultationId $c.id -StatePath (Join-Path $auto 'STATE.json') -TimeoutSeconds 15
    $unchanged=(Get-FileHash -LiteralPath $ledger -Algorithm SHA256).Hash -eq $before
    $budgetUnchanged=(Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json).chatgpt.queries_used -eq $beforeBudget
    $proof=@{status=$retry.Status;additional_physical_sends=0;ledger_unchanged=$unchanged;budget_unchanged=$budgetUnchanged}
    [IO.File]::WriteAllText((Join-Path $auto 'evidence/CHATGPT-RETRY.json'),($proof|ConvertTo-Json),[Text.Encoding]::UTF8)
    if($retry.Status -ne 'ALREADY_SENT' -or -not $unchanged -or -not $budgetUnchanged){throw 'CHATGPT_IDEMPOTENCY_FAILED'}
}
$r|ConvertTo-Json -Depth 18
