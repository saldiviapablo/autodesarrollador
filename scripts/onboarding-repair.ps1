# Bounded, read-only repair of model-authored onboarding proposals.
# This is NOT authorization to execute checks or modify a project.
Set-StrictMode -Version 2.0

function Test-OnboardingRepairableReason([string]$Reason) {
    if(-not $Reason.StartsWith('ONBOARDING_DENIED: ',[StringComparison]::Ordinal)){return $false}
    $code=($Reason.Substring('ONBOARDING_DENIED: '.Length) -split ':',2)[0].Trim()
    return $code -in @(
        'PLANNER_CHECK_COMMAND_INCOMPLETE',
        'PLANNER_CHECK_COMMAND_AMBIGUOUS',
        'PLANNER_CHECK_ARGV_INVALID',
        'CHECK_EXECUTABLE_NOT_ADMITTED',
        'PLANNER_SCHEMA_INVALID',
        'PLANNER_CRITERIA_BOUND',
        'PLANNER_CRITERION_BOUND',
        'COMPACT_PLANNER_LIST_BOUND',
        'BUILD_OR_EXPLICIT_NO_BUILD_REASON_REQUIRED',
        'IMMUTABLE_FILE_IN_WORKER_ALLOWLIST',
        'PLANNER_SEED_SOURCE_REQUIRED'
    )
}

function Invoke-OnboardingPlannerWithRepair($Context,$Request,$Cfg) {
    $basePrompt=[string]$Context.prompt
    $attempts=3
    $started=[Diagnostics.Stopwatch]::StartNew()
    $failures=@()
    for($attempt=1;$attempt -le $attempts;$attempt++){
        if($started.Elapsed.TotalSeconds -ge 290){
            throw 'PLANNER_REPAIR_TOTAL_BUDGET_EXCEEDED'
        }
        $current=@{};foreach($property in $Context.PSObject.Properties){$current[$property.Name]=$property.Value}
        if($attempt -gt 1){
            $last=[string]$failures[-1]
            $guidance=@'
The last proposal was rejected during strict host-only onboarding validation, NOT by the user.
Re-create the FULL compact plan from the original objective in the same envelope, not a patch/diff.
Respect every security restriction. Do not run tools. Do not execute code.
Every tests/builds/linters argv must be an ARRAY of at least TWO nonempty strings.
The first element must be python/node/npm/dotnet, and remaining args must invoke
an ACTUAL test or build script. A test cannot be only ["npm"], ["node"] or [].
Each test_id must match an actual tests entry. Each new acceptance test requires
substantive source in seed_files and an immutable_files pin to the same path.
Avoid fictitious commands; if tests refer to seed_files, use the correct exact path.
Build explicitly requested with npm run build must use ["npm","run","build"].
NEVER weaken policies, approval rules, allowed paths or acceptance requirements.
'@
            $current['prompt']=$basePrompt+"`n`nHOST VALIDATION REPAIR (attempt "+$attempt+" of "+$attempts+"): "+$last+"`n"+$guidance
        }
        $native=Invoke-OnboardingHermes ([pscustomobject]$current) $Request $Cfg
        if(-not $native.Success){throw 'PREFLIGHT_SUPERVISOR_FAILED'}
        $parsed=Read-LauncherPlannerStream $native.Stdout
        try{
            $bound=Invoke-OnboardingData @{action='planner_proposal';project=$Request.project;objective=$Request.objective;text=$parsed.text}
            return @{bound=$bound;native=$native;parsed=$parsed;attempts=$attempt;repaired=($attempt -gt 1);prior_rejections=@($failures)}
        }catch{
            $reason=[string]$_.Exception.Message
            if(-not(Test-OnboardingRepairableReason $reason) -or $attempt -eq $attempts){
                throw
            }
            $failures+=@($reason)
        }
    }
    throw 'PLANNER_REPAIR_ATTEMPTS_EXHAUSTED'
}
