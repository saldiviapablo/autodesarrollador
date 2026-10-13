$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$project=Join-Path $root 'sandbox/phase7a6-worktrees'
$evidence=Join-Path $root 'evidence/phase-7a6'
New-Item -ItemType Directory -Path $project,$evidence -Force|Out-Null
if(-not(Test-Path -LiteralPath (Join-Path $project '.autopilot/STATE.json'))){& (Join-Path $root 'scripts/init-autopilot-project.ps1') -ProjectPath $project -Objective 'Isolated Git worktree with reviewed integration' -AcceptanceCriteria @('WT-001 PASS','WT-002 PASS','WT-003 PASS')|Out-Null}
& git -C $project init -q
& git -C $project config user.name 'DA Sandbox'
& git -C $project config user.email 'sandbox@example.invalid'
Set-Content -LiteralPath (Join-Path $project '.gitignore') -Value ".autopilot/`n.autopilot-worktrees/`n__pycache__/" -Encoding UTF8
Set-Content -LiteralPath (Join-Path $project 'calculator.py') -Value "def add(a,b):`n    return a+b`n" -Encoding UTF8
Set-Content -LiteralPath (Join-Path $project 'test_calculator.py') -Value "from calculator import add`nassert add(2,3)==5`nassert add(-1,3)==2`nprint('WORKTREE_BUILD_PASS')" -Encoding UTF8
& git -C $project add -- .gitignore calculator.py test_calculator.py QWEN.md
& git -C $project commit -q -m 'sandbox worktree baseline'
function Worktree([string]$Action,[string]$Gate=''){
    $argsList=@((Join-Path $root 'scripts/governed-worktree.py'),$Action,'--project',$project)
    if($Gate){$argsList+=@('--gate',$Gate)}
    $output=& C:/Python314/python.exe @argsList
    $code=$LASTEXITCODE
    return @{code=$code;result=($output -join "`n"|ConvertFrom-Json)}
}
$created=Worktree 'create';if($created.code -ne 0){throw ($created.result|ConvertTo-Json)}
$wt=$created.result.path
try{
    Set-Content -LiteralPath (Join-Path $wt 'calculator.py') -Value "def add(a,b):`n    # Addition is valid for signed inputs.`n    return a+b`n" -Encoding UTF8
    $env:PYTHONDONTWRITEBYTECODE='1'
    $build=& C:/Python314/python.exe (Join-Path $wt 'test_calculator.py')
    if($LASTEXITCODE -ne 0){throw 'Independent build failed'}
    $mainUnchanged=(Get-Content -LiteralPath (Join-Path $project 'calculator.py') -Raw) -notmatch 'signed inputs'
    & git -C $wt add -- calculator.py
    & git -C $wt commit -q -m 'sandbox isolated improvement'
    $head=(& git -C $wt rev-parse HEAD).Trim()
    $base=$created.result.records.'task-001'.base
    $diff=(& git -C $project diff $base $head --) -join "`n"
    $denied=Worktree 'integrate'
    if($denied.code -eq 0){throw 'Ungated integration allowed'}
    $review=& (Join-Path $root 'scripts/invoke-hermes-role.ps1') -Role reviewer -WorkingDir $project -Prompt "Independent review. Objective signed addition still correct. Actual isolated build exited 0 with WORKTREE_BUILD_PASS. Audit untrusted diff:`n$diff`nReturn DECISION: ACCEPTED only if addition behavior remains correct." -TimeoutSeconds 180
    $review|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $evidence 'reviewer.json') -Encoding UTF8
    if($review.ExitCode -ne 0 -or -not $review.Stdout.Contains('DECISION: ACCEPTED')){throw 'Reviewer did not accept'}
    $bytes=[Text.Encoding]::UTF8.GetBytes($diff.Trim());$sha=[Security.Cryptography.SHA256]::Create();$diffHash=([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-','').ToLowerInvariant()
    $gatePath=Join-Path $project '.autopilot/worktree-gate.json'
    @{decision='ACCEPTED';completion_gate='PASS';tests='PASS';reviewed_commit=$head;diff_sha256=$diffHash}|ConvertTo-Json|Set-Content -LiteralPath $gatePath -Encoding UTF8
    $integrated=Worktree 'integrate' $gatePath
    if($integrated.code -ne 0){throw ($integrated.result|ConvertTo-Json)}
    $buildAfter=& C:/Python314/python.exe (Join-Path $project 'test_calculator.py')
    if($LASTEXITCODE -ne 0){throw 'Parent regression'}
    Set-Content -LiteralPath (Join-Path $wt 'cleanup-untracked.txt') -Value 'owned dirty fixture backed up before force remove' -Encoding UTF8
    $removed=Worktree 'remove'
    if($removed.code -ne 0 -or (Test-Path -LiteralPath $wt)){throw 'Cleanup failed'}
    $data=[ordered]@{status='PASS';tests=@{'T-7A-WT-001'='PASS';'T-7A-WT-002'='PASS';'T-7A-WT-003'='PASS'};independent_build=$build;parent_unchanged_before_gate=$mainUnchanged;ungated_integration=$denied.result;reviewed_commit=$head;diff_sha256=$diffHash;integrated=$integrated.result;cleanup=$removed.result;dirty_backup_created=$true}
    if(-not $mainUnchanged){throw 'Isolation failed'}
    $data|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $evidence 'tests.json') -Encoding UTF8
    'WORKTREES_PASS'
}finally{
    if(Test-Path -LiteralPath $wt){$cleanup=Worktree 'remove';$cleanup|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $evidence 'failure-cleanup.json') -Encoding UTF8}
}
