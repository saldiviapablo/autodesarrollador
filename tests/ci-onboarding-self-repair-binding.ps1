$ErrorActionPreference='Stop'
Set-StrictMode -Version 2.0
. (Join-Path $PSScriptRoot '../scripts/onboarding-repair.ps1')
$script:infra=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$script:fixtures=Join-Path $script:infra 'sandbox/ci-self-repair-binding'
$project=Join-Path $script:fixtures 'project'
$script:callCount=0
$script:prompts=@()
$OutputEncoding=New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)

function Invoke-OnboardingHermes($Context,$Request,$Cfg){
    $script:callCount++
    $script:prompts+=@($Context.prompt)
    return [pscustomobject]@{Success=$true;Stdout='placeholder';Duration=0.1;ExitCode=0;TimedOut=$false}
}
function Read-LauncherPlannerStream([string]$Stream){
    $filename=if($script:callCount -eq 1){'first.json'}else{'second.json'}
    $content=[IO.File]::ReadAllText((Join-Path $script:fixtures $filename),[Text.Encoding]::UTF8)
    return [pscustomobject]@{text=$content;session_id=('mock-session-'+$script:callCount)}
}
function Invoke-OnboardingData($Request){
    if($Request.action -ne 'planner_proposal'){throw 'ONLY_PLANNER_PROPOSAL_PERMITTED'}
    $wire=$Request|ConvertTo-Json -Depth 50 -Compress
    $out=$wire | & python -B (Join-Path $script:infra 'scripts/project_onboarding.py')
    $statusCode=$LASTEXITCODE
    $response=($out -join "`n")|ConvertFrom-Json
    if($statusCode -ne 0 -or $response.status -ne 'PASS'){
        throw ('ONBOARDING_DENIED: '+$response.reason)
    }
    return $response
}
$context=[pscustomobject]@{prompt='Implementar React, Vite y Tailwind. Investigación multifuente y npm run build.';planner_policy=@{timeout_seconds=180}}
$request=[pscustomobject]@{project=$project;objective='Crear landing React con investigación de IA de 2026; ejecutar npm run build y tests.'}
$cfg=[pscustomobject]@{}
$before=@(Get-ChildItem -Force -LiteralPath $project)
if($before.Count -ne 0){throw 'PROJECT_NOT_EMPTY_BEFORE_PREFLIGHT'}
$repair=Invoke-OnboardingPlannerWithRepair $context $request $cfg
if($repair.attempts -ne 2 -or -not $repair.repaired){throw 'TWO_STEP_REPAIR_FAILED'}
if($script:callCount -ne 2){throw 'MODEL_RETRY_COUNT_INVALID'}
if($script:prompts[1] -notmatch 'PLANNER_CHECK_COMMAND_INCOMPLETE'){throw 'MODEL_WAS_NOT_TOLD_ABOUT_FAILURE'}
if($repair.bound.status -ne 'PASS'){throw 'BIND_PROPOSAL_FAILED'}
if($repair.bound.proposal.plan.tests[0].argv[0] -ne 'node'){throw 'TEST_EXECUTABLE_NOT_CANONICAL'}
if($repair.bound.proposal.plan.research.query -eq $null){throw 'OPEN_RESEARCH_NOT_KEPT'}
if($repair.bound.proposal.plan.builds[0].argv[0] -ne 'npm'){throw 'BUILD_NOT_PRESERVED'}
$after=@(Get-ChildItem -Force -LiteralPath $project)
if($after.Count -ne 0){throw 'PROJECT_WAS_MODIFIED_DURING_PLANNING'}
Write-Host 'REAL_BINDER_REPAIR_PASS; attempts=2; binding=PASS; project_unchanged=true; Worker=0; web=0'
