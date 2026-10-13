param([string]$ProjectRoot)
$ErrorActionPreference='Stop';if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=Join-Path $PSHOME 'Modules'}
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/report.ps1')
$state=Get-Content -LiteralPath (Join-Path $ProjectRoot '.autopilot/STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
$fake='sk-'+('X'*25);$statuses=@('COMPLETED','FAILED','STALLED','BLOCKED_REQUIRES_HUMAN','ABORTED')
foreach($status in $statuses){
    $null=Write-RunnerReport -Project $ProjectRoot -RunId $state.run_id -State $state -Status $status -Technical 'UNIT_FIXTURE' -Reason ('synthetic test '+$fake) -Duration 1 -Cleanup @{job_closed=$true}
    $text=Get-Content -LiteralPath (Join-Path $ProjectRoot '.autopilot/reports/runner-result.json') -Raw -Encoding UTF8
    if($text.Contains($fake) -or -not $text.Contains('[REDACTED]')){throw 'REPORT_SECRET_LEAK'}
    $report=$text|ConvertFrom-Json
    foreach($field in @('run_id','project','objective','duration_seconds','status','tasks_completed','changed_files','commits','tests','builds','errors','retries','recoveries','web_queries','chatgpt_queries_used','blocks','completion_gate','cleanup')){if($report.PSObject.Properties.Name -notcontains $field){throw ('MISSING_REPORT_FIELD:'+ $field)}}
    if(-not (Test-Path -LiteralPath (Join-Path $ProjectRoot '.autopilot/reports/FINAL.md'))){throw 'HUMAN_REPORT_MISSING'}
}
foreach($name in @('FAILURE.md','STALLED.md','BLOCKED.md','ABORTED.md')){if(-not(Test-Path -LiteralPath (Join-Path $ProjectRoot ('.autopilot/reports/'+$name)))){throw 'TERMINAL_REPORT_MISSING'}}
@{status='PASS';terminal_statuses=$statuses;required_fields=$true;secret_sanitization='PASS';unit_fixture_only=$true}|ConvertTo-Json
