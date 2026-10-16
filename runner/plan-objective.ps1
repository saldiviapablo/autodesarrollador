# Read-only preflight planning; no Worker, contract approval or project writes.
# The Runner layer owns this temporary model lifetime and always tears it down.
param()
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8;[Console]::InputEncoding=[Text.Encoding]::UTF8
. (Join-Path $PSScriptRoot '../scripts/project-launcher-common.ps1')
. (Join-Path $PSScriptRoot '../scripts/windows-process-job.ps1')
$request=[Console]::In.ReadToEnd()|ConvertFrom-Json
$mutex=New-Object Threading.Mutex($false,'Local\DesarrolladorAutonomo_RunMutex');$held=$false;$job=$null;$model=$null;$result=$null;$payload=$null;$code=0
try{
    try{$held=$mutex.WaitOne(0)}catch [Threading.AbandonedMutexException]{$held=$true}
    if(-not $held){throw 'RUN_ALREADY_ACTIVE'}
    $context=Invoke-OnboardingData @{action='planner_context';project=$request.project;objective=$request.objective}
    $cfg=((& C:/Python314/python.exe (Join-Path $script:LauncherRoot 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $script:LauncherRoot 'config/system.yaml')) -join "`n")|ConvertFrom-Json
    $l=$cfg.llama
    if($l.alias -ne 'qwen36' -or $l.host -ne '127.0.0.1' -or $l.port -ne 8080 -or $l.ctx_size -ne 65536 -or $l.parallel -ne 1){throw 'FROZEN_MODEL_PARAMETERS_CHANGED'}
    if(@(Get-NetTCPConnection -LocalPort $l.port -State Listen -ErrorAction SilentlyContinue).Count){throw 'MODEL_ENDPOINT_OWNED_PRESERVED'}
    $job=New-Object DaOwnedProcessJob
    $job.Assign([Diagnostics.Process]::GetCurrentProcess().Handle)
    $arguments=@('-m',$l.model,'--alias',$l.alias,'--host',$l.host,'--port',[string]$l.port,'--ctx-size',[string]$l.ctx_size,'--parallel',[string]$l.parallel,'--cpu-moe','--n-gpu-layers',[string]$l.n_gpu_layers,'--flash-attn','on','--cache-type-k',$l.cache_type_k,'--cache-type-v',$l.cache_type_v,'--jinja')
    $model=Start-LauncherChild $l.executable $arguments
    $deadline=[datetimeoffset]::Now.AddSeconds($cfg.runner.llama_start_timeout_seconds);$ready=$false
    while([datetimeoffset]::Now -lt $deadline){
        if($model.process.HasExited){throw 'PREFLIGHT_MODEL_START_FAILED'}
        try{$health=Invoke-RestMethod -Uri $l.health_endpoint -TimeoutSec 2;if($health.status -eq 'ok'){$ready=$true;break}}catch{}
        Start-Sleep -Milliseconds 250
    }
    if(-not $ready){throw 'PREFLIGHT_MODEL_HEALTH_TIMEOUT'}
    $result=& (Join-Path $script:LauncherRoot 'scripts/invoke-hermes-role.ps1') -Role supervisor -Prompt $context.prompt -WorkingDir $request.project -TimeoutSeconds 180
    if(-not $result.Success){throw 'PREFLIGHT_SUPERVISOR_FAILED'}
    $parsed=Read-LauncherPlannerStream $result.Stdout
    $session=$parsed.session_id
    $proposal=$parsed.text|ConvertFrom-Json
    $bound=Invoke-OnboardingData @{action='proposal';project=$request.project;objective=$request.objective;proposal=$proposal}
    # Compare the read-only input snapshot to the proposal binding before Prepare.
    if(($context.snapshot|ConvertTo-Json -Depth 10 -Compress) -cne ($bound.project_snapshot|ConvertTo-Json -Depth 10 -Compress)){throw 'PROJECT_CHANGED_DURING_PLANNING'}
    $bound|Add-Member -NotePropertyName planner -NotePropertyValue @{role='Hermes Supervisor';session_id=$session;readonly=$true;tools=0;duration=$result.Duration;inference_lock='production wrapper';hook=$result.HookIntegrity;model_pid=$model.process.Id;model_start_ticks=$model.process.StartTime.ToUniversalTime().Ticks;model_arguments=$arguments;project_snapshot_unchanged=$true}
    $payload=$bound
}catch{
    $code=2
    $payload=[pscustomobject]@{status='DENY';reason=$_.Exception.Message;diagnostic=@{hermes_timed_out=$result.TimedOut;hermes_exit=$result.ExitCode;hermes_duration=$result.Duration;response_characters=$result.Stdout.Length}}
}finally{
    $exited=$true;$modelDiagnostic=''
    if($model){
        if(-not $model.process.HasExited){$model.process.Kill()};$exited=$model.process.WaitForExit(5000)
        if($model.stderr.Wait(3000)){$lines=$model.stderr.Result -split '\r?\n';$modelDiagnostic=($lines|Where-Object{$_ -match 'prompt eval|eval time|tokens|processing|error|failed|load time'}|Select-Object -Last 12) -join "`n"}
        $model.process.Dispose()
    }
    # Do not Dispose a job containing this process while it is still returning
    # JSON. OS process exit closes the handle and any remaining descendants.
    if($held){$mutex.ReleaseMutex()};$mutex.Dispose()
    if($payload){$payload|Add-Member -NotePropertyName cleanup -NotePropertyValue @{model_exited=$exited;physical_run_mutex_released=$held;owned_job_closed_on_process_exit=$true;model_diagnostic=$modelDiagnostic}}
}
$payload|ConvertTo-Json -Depth 50
exit $code
