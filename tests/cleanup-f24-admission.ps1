# Verify/release only metadata created by this admission test suite.
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$e=Join-Path $root 'evidence/f24-attempt6-preflight-20261014'
$unit=(Get-Content -LiteralPath (Join-Path $e 'completion/tests.json') -Raw -Encoding UTF8|ConvertFrom-Json).project
$unitE=Join-Path $e 'completion/cleanup';$null=New-Item -ItemType Directory -Force -Path $unitE
if(Test-Path -LiteralPath (Join-Path $unit '.autopilot/LOCK.json')){$r=& (Join-Path $root 'tests/finalize-live-test.ps1') -ProjectRoot $unit -EvidenceRoot $unitE -Failure 'UNIT_FIXTURE_ONLY_CLOSED; not native F24 execution'}
$tests=@((Get-Content -LiteralPath (Join-Path $e 'controlled-send/identity.json') -Raw -Encoding UTF8|ConvertFrom-Json).project,$unit)
$tests+=@(Get-ChildItem -LiteralPath (Join-Path $root 'sandbox') -Directory|Where-Object {$_.Name -like '7b-cleanup22-*' -and $_.CreationTime -gt (Get-Item -LiteralPath (Join-Path $e 'live-ui-precheck.json')).CreationTime}|ForEach-Object {$_.FullName})
$observed=@()
foreach($project in $tests){
    $auto=Join-Path $project '.autopilot'
    $survivors=@(Get-RunnerSurvivors $auto)
    $lockExists=$false;if(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')){$lockExists=$true}
    $observed+=@{project=$project;owned_survivors=$survivors;lock_exists=$lockExists}
}
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
try{try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}}finally{if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
$inference=Test-RunnerInferenceReleased
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)
$browser=Get-CimInstance Win32_Process -Filter 'ProcessId=16576'
$okay=$held -and $inference -eq 'FREE' -and $listeners.Count -eq 0 -and @($observed|Where-Object {$_.owned_survivors.Count -or $_.lock_exists}).Count -eq 0
$proof=@{status=$(if($okay){'PASS'}else{'FAIL'});projects=$observed;run_mutex_free=$held;inference_mutex=$inference;listeners=$listeners;browser_preexisting_preserved=($browser -and $browser.CommandLine -like '*HERMES-CHATGPT*');processes_killed_by_name=0}
Write-RunnerJson (Join-Path $e 'cleanup-final.json') $proof
$proof|ConvertTo-Json -Depth 8
if(-not $okay){exit 1}
