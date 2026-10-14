$script:RunnerInfra=Split-Path -Parent $PSScriptRoot
Import-Module Microsoft.PowerShell.Utility -Global -ErrorAction Stop
$null=Get-Command Get-FileHash -ErrorAction Stop
. (Join-Path $script:RunnerInfra 'scripts/state-manager.ps1')
. (Join-Path $script:RunnerInfra 'scripts/security-guard.ps1')
. (Join-Path $script:RunnerInfra 'scripts/progress-guard.ps1')
. (Join-Path $script:RunnerInfra 'scripts/windows-process-job.ps1')
function Quote-RunnerArg([string]$Value){return '"'+($Value -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
function Write-RunnerJson([string]$Path,$Value){
    $temporary=$Path+'.'+[guid]::NewGuid().ToString('N')+'.tmp'
    $safe=Sanitize-ObjectDeep $Value
    [IO.File]::WriteAllText($temporary,($safe|ConvertTo-Json -Depth 24),(New-Object Text.UTF8Encoding($false)))
    for($attempt=0;$attempt -lt 6;$attempt++){
        try{
            if(Test-Path -LiteralPath $Path){[IO.File]::Replace($temporary,$Path,($Path+'.previous'))}else{[IO.File]::Move($temporary,$Path)}
            return
        }catch [IO.IOException]{if($attempt -eq 5){throw};Start-Sleep -Milliseconds 30}
    }
}
function Get-RunnerAdmission([string]$Action,[string]$Project,[string]$Digest=''){
    $argsList=@((Join-Path $script:RunnerInfra 'runner/contract.py'),$Action,'--project',$Project)
    if($Digest){$argsList+=@('--digest',$Digest)}
    $out=& C:/Python314/python.exe @argsList;$code=$LASTEXITCODE
    $result=($out -join "`n")|ConvertFrom-Json
    if($code -ne 0){throw ('ADMISSION_DENIED: '+$result.reason)}
    return $result
}
function Assert-RunnerIntegrity {
    foreach($entry in $script:Admission.hashes.PSObject.Properties){
        if((Get-FileHash -LiteralPath $entry.Name -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value){throw 'APPROVED_INPUT_CHANGED'}
    }
}
function Save-RunnerState([string]$Status,[string]$Task){
    $script:RunState.status=$Status;$script:RunState.current_phase='RUNNER';$script:RunState.current_task=$Task
    $script:RunState.updated_at=[datetimeoffset]::Now.ToString('o')
    # Coordinate with the existing per-STATE ChatGPT budget mutex. Never overwrite
    # a reservation made by the managed consultant with Runner's cached STATE.
    $statePath=Join-Path $script:Auto 'STATE.json'
    $keyBytes=[Text.Encoding]::UTF8.GetBytes([IO.Path]::GetFullPath($statePath).ToLowerInvariant())
    $keyHash=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash($keyBytes))).Replace('-','')
    $stateBudgetMutex=New-Object Threading.Mutex($false,('Local\DesarrolladorAutonomo_ChatGPTBudget_'+$keyHash));$budgetHeld=$false
    try{
        try{$budgetHeld=$stateBudgetMutex.WaitOne(10000)}catch [Threading.AbandonedMutexException]{$budgetHeld=$true}
        if(-not $budgetHeld){throw 'CHATGPT_BUDGET_LOCK_TIMEOUT'}
        if(Test-Path -LiteralPath $statePath){
            $disk=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8|ConvertFrom-Json
            if($disk.run_id -ne $script:RunId){throw 'BUDGET_STATE_RUN_ID_MISMATCH'}
            if($disk.chatgpt){
                if(-not $script:RunState.chatgpt){
                    $script:RunState|Add-Member -MemberType NoteProperty -Name chatgpt -Force -Value ([pscustomobject]@{queries_used=[int]$disk.chatgpt.queries_used;max_queries=[int]$disk.chatgpt.max_queries})
                }
                $script:RunState.chatgpt.queries_used=[Math]::Max($script:RunState.chatgpt.queries_used,$disk.chatgpt.queries_used)
                $script:RunState.chatgpt.max_queries=[Math]::Min($script:RunState.chatgpt.max_queries,$disk.chatgpt.max_queries)
            }
        }
        $null=Write-AtomicState -StateObj $script:RunState -AutopilotDir $script:Auto -ValidateTransition $false
    }finally{if($budgetHeld){$stateBudgetMutex.ReleaseMutex()};$stateBudgetMutex.Dispose()}
    Write-RunnerJson (Join-Path $script:Auto 'HEARTBEAT.json') @{run_id=$script:RunId;pid=$PID;timestamp=[datetimeoffset]::Now.ToString('o');status=$Status;current_task=$Task}
}
function Runner-Event([string]$Type,$Payload){$null=Add-AutopilotEvent -AutopilotDir $script:Auto -RunId $script:RunId -Actor 'runner' -Type $Type -Payload $Payload}
function Save-RunnerProcesses {Write-RunnerJson (Join-Path $script:Auto 'PROCESSES.json') @{run_id=$script:RunId;runner_pid=$PID;processes=@($script:Owned.Values|ForEach-Object{$_.record});external_model=$script:ExternalModel}}
function Start-RunnerProcess([string]$Name,[string]$Exe,[array]$Arguments,[string]$WorkingDir,[switch]$Guardian){
    if($Guardian -and $Name -ne 'watchdog'){throw 'ONLY_WATCHDOG_MAY_SURVIVE_PARENT_FOR_FINALIZATION'}
    $psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=$Exe;$psi.Arguments=($Arguments|ForEach-Object{Quote-RunnerArg $_}) -join ' '
    $psi.WorkingDirectory=$WorkingDir;$psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    $psi.StandardOutputEncoding=[Text.Encoding]::UTF8;$psi.StandardErrorEncoding=[Text.Encoding]::UTF8
    $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE']='1';$psi.EnvironmentVariables['PYTHONUTF8']='1'
    $proc=[Diagnostics.Process]::Start($psi)
    try{if(-not $Guardian){$script:RunJob.Assign($proc.Handle)}}catch{$proc.Kill();$proc.Dispose();throw}
    $item=@{process=$proc;stdout=$proc.StandardOutput.ReadToEndAsync();stderr=$proc.StandardError.ReadToEndAsync();record=@{name=$Name;pid=$proc.Id;start_ticks=$proc.StartTime.ToUniversalTime().Ticks;executable=$Exe;ownership='OWNED_BY_RUN'}}
    $script:Owned[$Name]=$item;Save-RunnerProcesses;Runner-Event 'PROCESS_STARTED' $item.record
    return $item
}
function Stop-RunnerProcess($Item){
    if($Item -and -not $Item.process.HasExited){
        $actual=Get-Process -Id $Item.record.pid -ErrorAction SilentlyContinue
        if($actual -and $actual.StartTime.ToUniversalTime().Ticks -eq $Item.record.start_ticks){$Item.process.Kill();$null=$Item.process.WaitForExit(5000)}
    }
}
function Test-RunnerHealth {
    try{$h=Invoke-RestMethod -Uri $script:Cfg.llama.health_endpoint -TimeoutSec 2;return $h.status -eq 'ok'}catch{return $false}
}
function Tick-Runner {
    Assert-RunnerIntegrity
    if(Test-Path -LiteralPath (Join-Path $script:Auto 'STOP')){throw 'STOP_REQUESTED'}
    if(Test-Path -LiteralPath (Join-Path $script:Auto 'WATCHDOG-SIGNAL.json')){throw 'WATCHDOG_HEARTBEAT_STALE'}
    if(([datetimeoffset]::Now-$script:Started).TotalSeconds -gt $script:GlobalSeconds){throw 'GLOBAL_TIMEOUT'}
    if($script:RunState.progress.no_progress_cycles -ge $script:Cfg.limits.max_no_progress_cycles){throw 'NO_PROGRESS_STALLED'}
    Save-RunnerState 'RUNNING' $script:CurrentTask
}
function Start-RunnerModel {
    $llama=$script:Cfg.llama
    if($llama.alias -ne 'qwen36' -or $llama.host -ne '127.0.0.1' -or $llama.ctx_size -ne 65536 -or $llama.parallel -ne 1){throw 'FROZEN_MODEL_PARAMETERS_CHANGED'}
    $listeners=@(Get-NetTCPConnection -LocalPort $llama.port -State Listen -ErrorAction SilentlyContinue)
    if($listeners.Count){
        $existing=Get-CimInstance Win32_Process -Filter ('ProcessId='+$listeners[0].OwningProcess)
        if($existing.ExecutablePath -ne $llama.executable -or $existing.CommandLine -notmatch '--ctx-size\s+65536' -or $existing.CommandLine -notmatch '--parallel\s+1' -or $existing.CommandLine -notmatch '--host\s+127.0.0.1' -or $existing.CommandLine -notmatch '--alias\s+qwen36' -or -not(Test-RunnerHealth)){throw 'EXTERNAL_MODEL_NOT_COMPATIBLE'}
        if($existing.CommandLine -notmatch ('(?:^|\s)(?:-m|--model)\s+"?'+[regex]::Escape($llama.model)+'"?(?:\s|$)')){throw 'EXTERNAL_MODEL_NOT_COMPATIBLE'}
        $models=Invoke-RestMethod -Uri ('http://'+$llama.host+':'+$llama.port+'/v1/models') -TimeoutSec 2
        if(@($models.data.id) -notcontains $llama.alias){throw 'EXTERNAL_MODEL_NOT_COMPATIBLE'}
        $script:ExternalModel=@{pid=$existing.ProcessId;start_time=$existing.CreationDate.ToString('o');ownership='PREEXISTING_EXTERNAL'};Save-RunnerProcesses
        Runner-Event 'MODEL_ADOPTED_EXTERNAL' $script:ExternalModel;return
    }
    $argsList=@('-m',$llama.model,'--alias',$llama.alias,'--host',$llama.host,'--port',[string]$llama.port,'--ctx-size',[string]$llama.ctx_size,'--parallel',[string]$llama.parallel,'--cpu-moe','--n-gpu-layers',[string]$llama.n_gpu_layers,'--flash-attn','on','--cache-type-k',$llama.cache_type_k,'--cache-type-v',$llama.cache_type_v,'--jinja')
    $item=Start-RunnerProcess 'llama' $llama.executable $argsList $script:Admission.project
    $deadline=[datetimeoffset]::Now.AddSeconds($script:Cfg.runner.llama_start_timeout_seconds)
    while([datetimeoffset]::Now -lt $deadline){Tick-Runner;if($item.process.HasExited){throw 'LLAMA_START_FAILED'};if(Test-RunnerHealth){Runner-Event 'MODEL_HEALTH_READY' @{pid=$item.record.pid};return};Start-Sleep -Milliseconds 300}
    throw 'LLAMA_HEALTH_TIMEOUT'
}
function Invoke-RunnerManaged([string]$Name,[string]$Exe,[array]$Arguments,[int]$Timeout){
    $item=Start-RunnerProcess $Name $Exe $Arguments $script:Admission.project
    $stageJob=New-Object DaOwnedProcessJob;$stageJob.Assign($item.process.Handle)
    try{
    $deadline=[datetimeoffset]::Now.AddSeconds($Timeout)
    while(-not $item.process.WaitForExit(200)){
        Tick-Runner
        if([datetimeoffset]::Now -gt $deadline){Stop-RunnerProcess $item;throw ('PHASE_TIMEOUT:'+ $Name)}
        if($script:Admission.plan.backend -ne 'probe' -and $Name -ne 'llama' -and -not(Test-RunnerHealth)){throw 'LLAMA_LOST'}
    }
    $null=[Threading.Tasks.Task]::WaitAll(@($item.stdout,$item.stderr),3000)
    $output=$item.stdout.Result;$errorText=$item.stderr.Result
    [IO.File]::WriteAllText((Join-Path $script:Auto ('logs/'+$Name+'.stdout.txt')),(Sanitize-StringContent $output),[Text.Encoding]::UTF8)
    [IO.File]::WriteAllText((Join-Path $script:Auto ('logs/'+$Name+'.stderr.txt')),(Sanitize-StringContent $errorText),[Text.Encoding]::UTF8)
    Runner-Event 'PROCESS_EXITED' @{name=$Name;exit_code=$item.process.ExitCode}
    return @{exit_code=$item.process.ExitCode;stdout=$output;stderr=$errorText;pid=$item.record.pid}
    }finally{$stageJob.Dispose();$null=$item.process.WaitForExit(5000)}
}
function Invoke-RunnerAgent([string]$Role,$Packet){
    $script:CurrentTask=$Role
    $packetPath=Join-Path $script:Auto ('packet-'+$Role+'.json');Write-RunnerJson $packetPath $Packet
    $limit=3;if($script:Admission.plan.restart_budget -ne $null){$limit=[Math]::Min($limit,$script:Admission.plan.restart_budget)}
    while($true){
        try{
            $result=Invoke-RunnerManaged $Role 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $script:RunnerInfra 'runner/agent-step.ps1'),'-PacketPath',$packetPath) ($Packet.timeout+10)
            if($result.exit_code -ne 0){throw ('AGENT_FAILED:'+ $Role)}
            return ($result.stdout|ConvertFrom-Json)
        }catch{
            $reason=$_.Exception.Message
            if($reason -notmatch 'AGENT_FAILED|LLAMA_LOST|PHASE_TIMEOUT'){throw}
            if($reason -eq 'LLAMA_LOST'){
                if($script:ExternalModel){throw 'BLOCKED_REQUIRES_HUMAN_EXTERNAL_MODEL_LOST'}
                if($script:Restarts.llama -ge $limit){throw 'LLAMA_RESTART_BUDGET_EXHAUSTED'}
                $script:Restarts.llama++;Write-RunnerJson (Join-Path $script:Auto 'RESTARTS.json') $script:Restarts
                Runner-Event 'WATCHDOG_MODEL_RESTART' @{count=$script:Restarts.llama;reason=$reason}
                Stop-RunnerProcess $script:Owned.llama;Start-RunnerModel
            }
            if($script:Restarts[$Role] -ge $limit){throw ('AGENT_RESTART_BUDGET_EXHAUSTED:'+ $Role)}
            $script:Restarts[$Role]++;Write-RunnerJson (Join-Path $script:Auto 'RESTARTS.json') $script:Restarts
            Runner-Event 'WATCHDOG_AGENT_RESTART' @{role=$Role;count=$script:Restarts[$Role];reason=$reason}
            $recovered=& (Join-Path $script:RunnerInfra 'scripts/recover-autopilot.ps1') -ProjectPath $script:Admission.project
            $script:RunState=$recovered.State;Save-RunnerState 'RUNNING' ('recovered '+$Role)
        }
    }
}
function Invoke-RunnerCommands([array]$Commands,[string]$Group){
    $results=@()
    foreach($command in $Commands){
        if($null -eq $command){continue}
        $argsList=@($command.argv);$exe=$argsList[0]
        if($exe -notin @('python','node','npm','dotnet')){throw 'CHECK_EXECUTABLE_NOT_ADMITTED'}
        $guard=Test-CommandGuard -CommandLine ($argsList -join ' ') -WorkspacePath $script:Admission.project
        if(-not $guard.Allowed){throw 'CHECK_COMMAND_DENIED'}
        if($exe -eq 'python'){$exe='C:/Python314/python.exe'}
        $seconds=60;if($command.timeout_seconds){$seconds=$command.timeout_seconds}
        $script:CurrentTask=$Group+':'+$command.id
        $result=Invoke-RunnerManaged ('check-'+$command.id) $exe @($argsList|Select-Object -Skip 1) $seconds
        $ok=$result.exit_code -eq 0 -and $result.stdout.Contains($command.marker)
        $results+=@(@{id=$command.id;status=$(if($ok){'PASS'}else{'FAIL'});exit_code=$result.exit_code;marker_present=$result.stdout.Contains($command.marker);output=(Sanitize-StringContent $result.stdout)})
    }
    return $results
}
