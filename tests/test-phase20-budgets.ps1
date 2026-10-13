$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts/progress-guard.ps1')
$tracker=@{}
for($i=1;$i -le 3;$i++){$result=Test-LoopProgress -Tracker $tracker -CurrentErrorHash 'same-failure' -CurrentFingerprint 'same-diff' -MaxCycles 20 -MaxSameFailure 3 -MaxNoProgress 3}
if($tracker.same_failure_count -ne 3 -or $tracker.no_progress_cycles -ne 2){throw 'COUNTERS_INCORRECT'}
# Runner stops at the approved strict limit rather than extending escalation.
if($tracker.same_failure_count -lt 3){throw 'UNBOUNDED_CORRECTION'}
$persist=($tracker|ConvertTo-Json)|ConvertFrom-Json;$restored=@{}
foreach($p in $persist.PSObject.Properties){$restored[$p.Name]=$p.Value}
$result=Test-LoopProgress -Tracker $restored -CurrentErrorHash 'new-failure' -CurrentFingerprint 'real-new-diff' -MaxCycles 4
if($result.CanContinue -or $result.Status -ne 'STALLED'){throw 'DISK_BUDGET_RESET'}
@{status='PASS';strict_repeated_failure_limit=3;tracker_roundtrip=$true;cycle_limit_preserved=$true}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'evidence/phase-20/budgets.json') -Encoding UTF8
