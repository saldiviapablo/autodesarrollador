$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$fixture=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'fixture.json') -Raw -Encoding UTF8|ConvertFrom-Json
$auto=Join-Path $fixture.project '.autopilot';$survivors=@(Get-RunnerSurvivors $auto)
$m=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
try{try{$held=$m.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}}finally{if($held){$m.ReleaseMutex()};$m.Dispose()}
$inference=Test-RunnerInferenceReleased
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)
$lock=$false;if(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')){$lock=$true}
$chrome=Get-CimInstance Win32_Process -Filter 'ProcessId=16576';$preserved=$false;if($chrome -and $chrome.CommandLine -like '*HERMES-CHATGPT*'){$preserved=$true}
$okay=$held -and $inference -eq 'FREE' -and $survivors.Count -eq 0 -and $listeners.Count -eq 0 -and -not $lock -and $preserved
$proof=@{status=$(if($okay){'PASS'}else{'FAIL'});owned_survivors=$survivors;run_mutex_free=$held;inference_mutex=$inference;listeners=$listeners;run_lock_exists=$lock;preexisting_browser_preserved=$preserved;processes_killed_by_inspection=0}
Write-RunnerJson (Join-Path $PSScriptRoot 'cleanup-independent.json') $proof
$proof|ConvertTo-Json -Depth 8
if(-not $okay){exit 1}
