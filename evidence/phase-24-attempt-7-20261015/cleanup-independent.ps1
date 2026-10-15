$ErrorActionPreference='Stop'
$admissionRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$admissionEvidence=Join-Path $admissionRoot 'evidence/phase-24-attempt-7-20261015'
$mutexProof=[ordered]@{}
foreach($mutexLabel in @('DesarrolladorAutonomo_InferenceMutex','Local\DesarrolladorAutonomo_RunMutex')){
 $probe=$null;$held=$false
 try{$probe=[Threading.Mutex]::OpenExisting($mutexLabel);try{$held=$probe.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true};$mutexProof[$mutexLabel]=if($held){'FREE'}else{'BUSY'}}catch [Threading.WaitHandleCannotBeOpenedException]{$mutexProof[$mutexLabel]='FREE'}finally{if($held){$probe.ReleaseMutex()};if($probe){$probe.Dispose()}}
}
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalAddress,LocalPort,OwningProcess)
$auto=Join-Path $admissionRoot 'sandbox/f24-attempt7-86dd900d/project/.autopilot'
. (Join-Path $admissionRoot 'runner/core.ps1');. (Join-Path $admissionRoot 'runner/cleanup.ps1')
$survivors=@(Get-RunnerSurvivors $auto)
$aux=@(Get-CimInstance Win32_Process -Filter "Name='node.exe' OR Name='python.exe'"|Where-Object {$_.CommandLine -match 'logs[/\\]f24-attempt7[/\\](observe-browser.js|preserve-first-segment.py)|tests[/\\]test-phase24-attempt7-live.py'}|Select-Object Name,ProcessId)
$proof=@{owned_survivors=$survivors;auxiliary_survivors=$aux;run_lock_exists=(Test-Path -LiteralPath (Join-Path $auto 'LOCK.json'));preexisting_browser_preserved=[bool](Get-Process -Id 16576 -ErrorAction SilentlyContinue);state_terminal=(Get-Content -LiteralPath (Join-Path $auto 'STATE.json') -Raw|ConvertFrom-Json).status;processes_killed_by_inspection=0;status=if($survivors.Count -eq 0 -and $aux.Count -eq 0 -and -not (Test-Path -LiteralPath (Join-Path $auto 'LOCK.json')) -and $listeners.Count -eq 0 -and -not ($mutexProof.Values -contains 'BUSY')){'PASS'}else{'FAIL'};mutexes=$mutexProof;listeners=$listeners}
[IO.File]::WriteAllText((Join-Path $admissionEvidence 'cleanup-independent.json'),($proof|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
if($proof.status -ne 'PASS'){throw 'INDEPENDENT_CLEANUP_FAILED'}
$proof|ConvertTo-Json -Depth 7
