# Only preflight uses the native Hermes API's per-request structured format.
# Ordinary invoke-hermes-role.ps1 / Runner / Worker are untouched.
function Invoke-OnboardingHermes($Context,$Request,$Cfg){
    $root=$script:LauncherRoot
    $runtime=Invoke-OnboardingData @{action='planner_runtime'}
    $hook=((& (Join-Path $root 'scripts/hermes-memory-guard.ps1') -Action VerifyHookIntegrity -SecurityYamlPath (Join-Path $root 'config/security.yaml')) -join "`n")|ConvertFrom-Json
    $plugin=((& (Join-Path $root 'scripts/hermes-mcp-plugin-guard.ps1') -Action VerifyPluginIntegrity -SecurityYamlPath (Join-Path $root 'config/security.yaml')) -join "`n")|ConvertFrom-Json
    if(-not $hook.allowed -or $hook.status -ne 'PASS' -or -not $plugin.allowed -or $plugin.status -ne 'PASS'){throw 'PLANNER_HOOK_PLUGIN_INTEGRITY_FAILED'}
    . (Join-Path $root 'scripts/inference-lock.ps1')
    $lease=$null;$child=$null;$timer=[Diagnostics.Stopwatch]::StartNew()
    try{
        $lease=Acquire-InferenceLock -Owner hermes -Purpose onboarding-readonly-json -TimeoutSeconds $Context.planner_policy.timeout_seconds -InfraPath $root
        if(-not $lease.Acquired){throw 'PLANNER_INFERENCE_LOCK_FAILED'}
        $command=((& $Cfg.hermes.executable --print-runtime-command -- chat) -join "`n")|ConvertFrom-Json
        $entry="runpy.run_module('hermes_cli.main', run_name='__main__', alter_sys=True)"
        if($command.Count -lt 4 -or -not $command[3].EndsWith($entry)){throw 'UNRECOGNIZED_NATIVE_HERMES_BOOTSTRAP'}
        $path=(Join-Path $root 'scripts/onboarding_hermes.py')|ConvertTo-Json -Compress
        $command[3]=$command[3].Substring(0,$command[3].Length-$entry.Length)+"runpy.run_path($path,run_name='__main__')"
        $payload=@{project=$Request.project;prompt=$Context.prompt;policy=$Context.planner_policy;schema=$Context.planner_schema;profile_home=$runtime.profile_home;disabled_toolsets=$runtime.disabled_toolsets;model=$Cfg.llama.alias;base_url=('http://'+$Cfg.llama.host+':'+$Cfg.llama.port+'/v1')}
        $child=Start-LauncherChild $command[0] @($command[1..3]) ($payload|ConvertTo-Json -Depth 50 -Compress)
        if(-not $child.process.WaitForExit($Context.planner_policy.timeout_seconds*1000)){$child.process.Kill();throw 'PREFLIGHT_SUPERVISOR_TIMEOUT'}
        $value=$child.stdout.Result|ConvertFrom-Json
        if($child.process.ExitCode -ne 0 -or $value.status -ne 'PASS'){throw ('PREFLIGHT_SUPERVISOR_FAILED: '+$value.reason)}
        $audit=Invoke-OnboardingData @{action='planner_audit';project=$Request.project;result=$value}
        $initial=@{type='system';subtype='init';session_id=$value.session_id}|ConvertTo-Json -Compress
        $final=@{type='result';session_id=$value.session_id;text=$value.text}|ConvertTo-Json -Compress
        return @{Success=$true;Duration=$timer.Elapsed.TotalSeconds;Stdout=($initial+"`n"+$final);HookIntegrity='PASS';ExitCode=0;TimedOut=$false;Native=$value;AuditPath=$audit.path}
    }finally{
        if($child){if(-not $child.process.HasExited){$child.process.Kill()};$child.process.Dispose()}
        if($lease){$null=Release-InferenceLock -LockToken $lease}
    }
}
