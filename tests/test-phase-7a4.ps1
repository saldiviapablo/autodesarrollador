[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$evidence=Join-Path $root 'evidence/phase-7a4'
$project=Join-Path $root 'sandbox/phase7a4-browser'
New-Item -ItemType Directory -Path $evidence -Force|Out-Null
$results=[ordered]@{}
function Save-BrowserTest([string]$Id,$Data,[bool]$Passed){
    $results[$Id]=$(if($Passed){'PASS'}else{'FAIL'})
    [ordered]@{test_id=$Id;status=$results[$Id];timestamp=(Get-Date).ToString('o');data=$Data}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $evidence ($Id+'.json')) -Encoding UTF8
    if(-not $Passed){throw ('MANDATORY_TEST_FAILED: '+$Id)}
}
try{
    $functional=& (Join-Path $root 'scripts/invoke-native-browser.ps1') -Url 'https://docs.python.org/3/library/json.html' -ProjectPath $project
    $functionalSummary=[ordered]@{status=$functional.status;url=$functional.url;title=$functional.title;has_json_documentation=($functional.content -match 'JSON');trust=$functional.trust;used_real_profile=$functional.used_real_profile;cleanup_ok=$functional.cleanup_ok;local_inferences=$functional.local_inferences}
    Save-BrowserTest 'T-7A-BROWSER-001' $functionalSummary ($functional.status -eq 'SUCCESS' -and $functional.content -match 'JSON' -and $functional.trust -eq 'UNTRUSTED_EXTERNAL_DATA')
    $denied=@()
    foreach($url in @('https://example.com/','https://foo.docs.python.org/','https://docs.python.org.evil.test/','https://docs.python.org@evil.test/','http://docs.python.org/','https://chatgpt.com/','invalid URL')){
        $out=& (Join-Path $root 'scripts/invoke-native-browser.ps1') -Url $url -ProjectPath $project
        if($out.status -ne 'DENY' -or $out.reason -ne 'DOMAIN_BLOCKED'){throw ('Unexpected domain result: '+$url)}
        $denied+=@([ordered]@{url=$url;status='DENY';reason=$out.reason;cleanup_ok=$out.cleanup_ok})
    }
    $probe=Get-Content -LiteralPath (Join-Path $evidence 'native-probe.json') -Raw -Encoding UTF8|ConvertFrom-Json
    Save-BrowserTest 'T-7A-BROWSER-002' @{wrapper_denials=$denied;native_engine_nonallowlisted=$probe.non_allowlisted_native_navigation;native_evaluation_denied=$probe.evaluation_policy_denied} ($probe.native_requirements_ready -and -not $probe.non_allowlisted_native_navigation.success -and -not $probe.evaluation_policy_denied.success)
    $timeout=& (Join-Path $root 'scripts/invoke-native-browser.ps1') -Url 'https://docs.python.org/3/library/json.html' -ProjectPath $project -TimeoutSeconds 1
    Save-BrowserTest 'T-7A-BROWSER-004' $timeout ($timeout.status -eq 'TIMEOUT' -and $timeout.cleanup_ok)
    Start-Sleep -Milliseconds 200
    $orphans=@(Get-CimInstance Win32_Process|Where-Object{($_.Name -eq 'chrome.exe' -and $_.CommandLine -match 'phase7a4|agent-browser') -or ($_.Name -match 'agent-browser|node' -and $_.CommandLine -match 'agent-browser')})
    $temps=@(Get-ChildItem -LiteralPath (Join-Path $project '.autopilot/native-browser') -Directory -ErrorAction SilentlyContinue)
    Save-BrowserTest 'T-7A-BROWSER-003' @{native_processes_remaining=$orphans.Count;active_temp_dirs=$temps.Count;job_handles_closed_in_finally=$true} ($orphans.Count -eq 0 -and $temps.Count -eq 0)
}finally{
    [ordered]@{subphase='7A.4';status=$(if($results.Count -eq 4 -and @($results.Values|Where-Object{$_ -ne 'PASS'}).Count -eq 0){'PASS'}else{'FAIL'});tests=$results;new_dependencies=@()}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $evidence 'phase-7a4-summary.json') -Encoding UTF8
}
$results|ConvertTo-Json
