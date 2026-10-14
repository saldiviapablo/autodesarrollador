$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent $PSScriptRoot;. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$p=Join-Path $root ('sandbox/budget-cache-'+[guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $p
$null=& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $p -Objective 'Budget merge deterministic test' -AcceptanceCriteria 'counter preserved'
$script:Auto=Join-Path $p '.autopilot';$path=Join-Path $script:Auto 'STATE.json'
$script:RunState=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json;$script:RunId=$script:RunState.run_id
$disk=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
$disk|Add-Member -MemberType NoteProperty -Name chatgpt -Value ([pscustomobject]@{queries_used=1;max_queries=5})
$null=Write-AtomicState -StateObj $disk -AutopilotDir $script:Auto -ValidateTransition $false
try{
    Save-RunnerState 'RUNNING' 'Deterministic stale cache merge test'
    $merged=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
    if($merged.chatgpt.queries_used -ne 1 -or $merged.chatgpt.max_queries -ne 5){throw 'RESERVATION_LOST'}
    $script:RunState.chatgpt.queries_used=2;$script:RunState.chatgpt.max_queries=3
    Save-RunnerState 'RUNNING' 'Monotonic used and conservative maximum'
    $merged=Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json
    if($merged.chatgpt.queries_used -ne 2 -or $merged.chatgpt.max_queries -ne 3){throw 'BUDGET_WEAKENED'}
    @{status='PASS';stale_cache_initially_missing_budget=$true;reservation_preserved=$true;no_credit_added=$true;inferences=0;project=$p}|ConvertTo-Json
}finally{Save-RunnerState 'FAILED' 'terminal deterministic test only';Remove-RunnerOwnedLock $script:Auto $script:RunId $PID}
