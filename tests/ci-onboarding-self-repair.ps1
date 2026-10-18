$ErrorActionPreference='Stop'
Set-StrictMode -Version 2
. (Join-Path $PSScriptRoot '../scripts/onboarding-repair.ps1')
$script:callCount=0
$script:mode='recover'
$script:prompts=@()
$script:actions=@()

function Invoke-OnboardingHermes($Context,$Request,$Cfg) {
    $script:callCount++
    $script:prompts+=@($Context.prompt)
    return [pscustomobject]@{Success=$true;Stdout='mock response';Duration=0.1;ExitCode=0;TimedOut=$false}
}
function Read-LauncherPlannerStream([string]$Stream){
    return [pscustomobject]@{text='model-plan-'+$script:callCount;session_id='session-'+$script:callCount}
}
function Invoke-OnboardingData($Request){
    $script:actions+=@($Request.action)
    if($Request.action -ne 'planner_proposal'){throw 'MOCK_UNEXPECTED_ACTION'}
    if($script:mode -eq 'recover' -and $script:callCount -eq 1){
        throw 'ONBOARDING_DENIED: PLANNER_CHECK_COMMAND_INCOMPLETE'
    }
    if($script:mode -eq 'security'){
        throw 'ONBOARDING_DENIED: SECRET_DETECTED_REMOVE_SECRETS_BEFORE_CONTINUING'
    }
    if($script:mode -eq 'exhaust'){
        throw 'ONBOARDING_DENIED: PLANNER_CHECK_COMMAND_INCOMPLETE'
    }
    return @{status='PASS';proposal=@{plan=@{task='plan valid'}};project_snapshot=@{}}
}
function Assert-That($Condition,[string]$Message){if(-not $Condition){throw $Message}}
$context=[pscustomobject]@{prompt='Original UTF-8: áéíóú ñ';planner_policy=@{timeout_seconds=180}}
$request=[pscustomobject]@{project='C:\Sandbox\Landing';objective='Crear React Vite con npm run build'}
$cfg=[pscustomobject]@{}
$successful=Invoke-OnboardingPlannerWithRepair $context $request $cfg
Assert-That ($successful.attempts -eq 2) 'RECOVERY_REQUIRES_TWO_ATTEMPTS'
Assert-That ($successful.repaired -eq $true) 'REPAIR_FLAG_MISSING'
Assert-That ($script:callCount -eq 2) 'INFERENCE_COUNT_WRONG'
Assert-That ($script:prompts[1].Contains('PLANNER_CHECK_COMMAND_INCOMPLETE')) 'REPAIR_ERROR_FEEDBACK_MISSING'
Assert-That ($script:prompts[1].Contains('Original UTF-8')) 'ORIGINAL_BRIEF_LOST'
Assert-That ($script:actions.Count -eq 2) 'VALIDATION_COUNT_WRONG'
$script:callCount=0;$script:prompts=@();$script:actions=@();$script:mode='security'
try{
    $null=Invoke-OnboardingPlannerWithRepair $context $request $cfg
    throw 'UNSAFE_FAILURE_MUST_BE_DENIED'
}catch{
    Assert-That ($_.Exception.Message -match 'SECRET_DETECTED_REMOVE_SECRETS') 'SECURITY_ERROR_WAS_SWALLOWED'
}
Assert-That ($script:callCount -eq 1) 'SECURITY_FAILURE_WAS_RETRIED'
$script:callCount=0;$script:prompts=@();$script:actions=@();$script:mode='exhaust'
try{
    $null=Invoke-OnboardingPlannerWithRepair $context $request $cfg
    throw 'EXHAUSTION_MUST_FAIL_CLOSED'
}catch{
    Assert-That ($_.Exception.Message -match 'PLANNER_CHECK_COMMAND_INCOMPLETE') 'EXHAUSTION_ERROR_WAS_SWALLOWED'
}
Assert-That ($script:callCount -eq 3) 'RETRY_CAP_NOT_ENFORCED'
Assert-That ((Test-OnboardingRepairableReason 'ONBOARDING_DENIED: PLANNER_CHECK_COMMAND_INCOMPLETE') -eq $true) 'EXPECTED_REPAIR_DENIED'
Assert-That ((Test-OnboardingRepairableReason 'ONBOARDING_DENIED: PATH_DENIED') -eq $false) 'UNSAFE_REASON_MARKED_REPAIRABLE'
Write-Host 'SELF_REPAIR_SIMULATION_PASS; successful recovery=2, security=1, exhaustion=3; worker_starts=0'
