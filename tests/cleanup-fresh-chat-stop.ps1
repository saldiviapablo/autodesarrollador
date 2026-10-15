# Read-only final ownership/lock verification after fresh-chat refusal.
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$e=Join-Path $root 'evidence/f24-admission-repair-20261014'
$id=Get-Content -LiteralPath (Join-Path $e 'controlled-send/identity.json') -Raw -Encoding UTF8|ConvertFrom-Json
$auto=Join-Path $id.project '.autopilot'
$state=Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw -Encoding UTF8|ConvertFrom-Json
$survivors=@(Get-RunnerSurvivors $auto)
$newLocks=@(Get-ChildItem -LiteralPath (Join-Path $root 'sandbox') -Filter LOCK.json -Recurse -File|Where-Object {$_.CreationTime -ge (Get-Item -LiteralPath (Join-Path $e 'history-before.json')).CreationTime}|ForEach-Object {$_.FullName})
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
try{try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}}finally{if($held){$mutex.ReleaseMutex()};$mutex.Dispose()}
$inference=Test-RunnerInferenceReleased
$browser=Get-CimInstance Win32_Process -Filter 'ProcessId=16576'
$browserPreserved=$false;if($browser -and $browser.CommandLine -like '*HERMES-CHATGPT*'){$browserPreserved=$true}
$okay=$held -and $inference -eq 'FREE' -and $survivors.Count -eq 0 -and $newLocks.Count -eq 0 -and $listeners.Count -eq 0 -and $state.status -eq 'ABORTED' -and $browserPreserved
$proof=@{status=$(if($okay){'PASS'}else{'FAIL'});owned_survivors=$survivors;new_locks=$newLocks;run_mutex_free=$held;inference_mutex=$inference;listeners=$listeners;test_state=$state.status;browser_preexisting_preserved=$browserPreserved;processes_killed=0}
Write-RunnerJson (Join-Path $e 'cleanup-final.json') $proof
$proof|ConvertTo-Json -Depth 8
if(-not $okay){exit 1}
