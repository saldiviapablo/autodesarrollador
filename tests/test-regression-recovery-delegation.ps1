param([Parameter(Mandatory=$true)][string]$EvidenceDir)
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$project=Join-Path $root 'sandbox/macro7a-regression'
New-Item -ItemType Directory -Path $project,$EvidenceDir -Force|Out-Null
& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $project -Objective 'Final 7A regression gate, recovery and delegation smoke' -AcceptanceCriteria @('Mandatory 7A evidence verified','Security and lock regression PASS','Recovery and delegation smoke PASS','Protected hashes and cleanup PASS') -TestCommands @('python test_calculator.py')|Out-Null
& git -C $project init -q
& git -C $project config user.name 'DA Sandbox'
& git -C $project config user.email 'sandbox@example.invalid'
Set-Content -LiteralPath (Join-Path $project '.gitignore') -Value ".autopilot/`n__pycache__/" -Encoding UTF8
Set-Content -LiteralPath (Join-Path $project 'calculator.py') -Value "def add(a,b):`n    return a-b`n" -Encoding UTF8
Set-Content -LiteralPath (Join-Path $project 'test_calculator.py') -Value "from calculator import add`nassert add(2,3)==5`nprint('REGRESSION_GATE_DELEGATION_OK')" -Encoding UTF8
& git -C $project add -- .gitignore calculator.py test_calculator.py QWEN.md
& git -C $project commit -q -m 'sandbox regression baseline'
. (Join-Path $root 'scripts/state-manager.ps1')
$auto=Join-Path $project '.autopilot';$statePath=Join-Path $auto 'STATE.json'
$state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
$state.status='RUNNING';$state.current_phase='REGRESSION_7A';$state.tests.status='RUNNING'
$null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
$checkpoint=& (Join-Path $root 'scripts/create-autopilot-checkpoint.ps1') -ProjectPath $project -CheckpointId 'chk-regression-baseline' -Reason 'Fresh deterministic regression baseline'
# Corruption is confined to this new sandbox; prior checkpoints and STATE.previous remain intact.
Set-Content -LiteralPath $statePath -Value '{"corrupt":' -Encoding UTF8
$recovery=& (Join-Path $root 'scripts/recover-autopilot.ps1') -ProjectPath $project -CheckpointId 'chk-regression-baseline'
$integrity=Test-CheckpointIntegrity -CheckpointDir $checkpoint.Directory
$context=& (Join-Path $root 'scripts/build-recovery-context.ps1') -ProjectPath $project
$recoveryReport=@{status=$(if($recovery.Status -eq 'RECOVERED' -and $recovery.RecoveredFromBackup -and $integrity.Valid -and $recovery.State.status -eq 'RUNNING'){'PASS'}else{'FAIL'});data=$recovery;checkpoint_integrity=$integrity.Valid;context=$context}
$recoveryReport|ConvertTo-Json -Depth 14|Set-Content -LiteralPath (Join-Path $EvidenceDir 'recovery.json') -Encoding UTF8
if($recoveryReport.status -ne 'PASS'){throw 'RECOVERY_REGRESSION'}
$request=@{schema_version='1.0';delegation_id='del-final7a-smoke';objective='Fix calculator addition and pass its actual test';workspace=$project;task='Change calculator.py add(a,b) from a-b to a+b, then run python test_calculator.py';acceptance_criteria=@('add(2,3)==5','test_calculator.py prints REGRESSION_GATE_DELEGATION_OK');allowed_actions=@('edit_file','run_test');forbidden_actions=@('git push','system changes');tests=@('python test_calculator.py');status='READY'}
$requestJson=$request|ConvertTo-Json -Depth 6
$worker=& (Join-Path $root 'scripts/invoke-delegation.ps1') -RequestJson $requestJson -MaxWallTime 120s -TimeoutSeconds 150
$worker|ConvertTo-Json -Depth 16|Set-Content -LiteralPath (Join-Path $EvidenceDir 'delegation-worker.json') -Encoding UTF8
if($worker.Status -ne 'SUCCESS'){throw 'DELEGATION_REGRESSION'}
$output=& C:/Python314/python.exe (Join-Path $project 'test_calculator.py')
if($LASTEXITCODE -ne 0 -or $output -notmatch 'REGRESSION_GATE_DELEGATION_OK'){throw 'DELEGATION_FALSE_SUCCESS'}
@{status='PASS';actual_qwen_worker=$true;actual_tests='PASS';marker=$output;inference_serialized=$true;cleanup='wrapper completed'}|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $EvidenceDir 'delegation.json') -Encoding UTF8
$state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
$state.status='RUNNING';$state.current_phase='REGRESSION_7A';$state.tests.status='PASS';$state.tests.last_exit_code=0;$state.current_task='Final component integrity and cleanup';$state.next_action='Finish regression gates and report'
$null=Write-AtomicState -StateObj $state -AutopilotDir $auto -ValidateTransition $false
'RECOVERY_DELEGATION_PASS'
