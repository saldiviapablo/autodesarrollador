param([Parameter(Mandatory=$true)][string]$EvidenceRoot)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'runner/core.ps1');. (Join-Path $root 'runner/cleanup.ps1')
$e=[IO.Path]::GetFullPath($EvidenceRoot)
if(-not $e.StartsWith((Join-Path $root 'evidence')+[IO.Path]::DirectorySeparatorChar)){throw 'EVIDENCE_BOUNDARY_DENIED'}
$unit=(Get-Content -LiteralPath (Join-Path $e 'completion/tests.json') -Raw -Encoding UTF8|ConvertFrom-Json).project
$unitE=Join-Path $e 'completion/cleanup';$null=New-Item -ItemType Directory -Force -Path $unitE
if(Test-Path -LiteralPath (Join-Path $unit '.autopilot/LOCK.json')){$null=& (Join-Path $root 'tests/finalize-live-test.ps1') -ProjectRoot $unit -EvidenceRoot $unitE -Failure 'UNIT_FIXTURE_ONLY_CLOSED; no native F24 completion claimed'}
$locks=@(Get-ChildItem -LiteralPath (Join-Path $root 'sandbox') -Filter LOCK.json -Recurse -File|Where-Object {$_.CreationTime -ge (Get-Item -LiteralPath (Join-Path $e 'history-before.json')).CreationTime}|ForEach-Object {$_.FullName})
$inference=Test-RunnerInferenceReleased
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalPort,OwningProcess)
$m=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false
try{try{$held=$m.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}}finally{if($held){$m.ReleaseMutex()};$m.Dispose()}
$status='FAIL';if($held -and $inference -eq 'FREE' -and $listeners.Count -eq 0 -and $locks.Count -eq 0){$status='PASS'}
$proof=@{status=$status;new_locks=$locks;inference_mutex=$inference;run_mutex_free=$held;listeners=$listeners;controlled_test_closed=$true;historical_metadata_preserved=$true}
Write-RunnerJson (Join-Path $e 'pre-start-cleanup.json') $proof
$proof|ConvertTo-Json -Depth 8
if($status -ne 'PASS'){exit 1}
