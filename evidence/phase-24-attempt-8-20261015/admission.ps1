$ErrorActionPreference='Stop'
$admissionRoot=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$admissionEvidence=Join-Path $admissionRoot 'evidence/phase-24-attempt-8-20261015'
$mutexProof=[ordered]@{}
foreach($mutexLabel in @('DesarrolladorAutonomo_InferenceMutex','Local\DesarrolladorAutonomo_RunMutex')){
 $probe=$null;$held=$false
 try{$probe=[Threading.Mutex]::OpenExisting($mutexLabel);try{$held=$probe.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true};$mutexProof[$mutexLabel]=if($held){'FREE'}else{'BUSY'}}catch [Threading.WaitHandleCannotBeOpenedException]{$mutexProof[$mutexLabel]='FREE'}finally{if($held){$probe.ReleaseMutex()};if($probe){$probe.Dispose()}}
}
$listeners=@(Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue|Where-Object {$_.LocalPort -in @(8080,9119)}|Select-Object LocalAddress,LocalPort,OwningProcess)
$proof=@{status=if($listeners.Count -eq 0 -and -not ($mutexProof.Values -contains 'BUSY')){'PASS'}else{'FAIL'};mutexes=$mutexProof;listeners=$listeners}
[IO.File]::WriteAllText((Join-Path $admissionEvidence 'admission-locks-ports.json'),($proof|ConvertTo-Json -Depth 7),[Text.UTF8Encoding]::new($false))
if($proof.status -ne 'PASS'){throw 'ADMISSION_LOCK_OR_PORT_BUSY'}
$proof|ConvertTo-Json -Depth 7
