# Test-run ownership only; the nocturnal Runner remains a separate 7B deliverable.
[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$cfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
if(Get-NetTCPConnection -LocalPort $cfg.llama.port -State Listen -ErrorAction SilentlyContinue){throw 'INFERENCE_ENDPOINT_ALREADY_IN_USE: do not adopt unknown ownership'}
$argsList=@('-m',$cfg.llama.model,'--alias',$cfg.llama.alias,'--host',$cfg.llama.host,'--port',[string]$cfg.llama.port,'--ctx-size',[string]$cfg.llama.ctx_size,'--parallel',[string]$cfg.llama.parallel,'--cpu-moe','--n-gpu-layers',[string]$cfg.llama.n_gpu_layers,'--flash-attn','on','--cache-type-k',$cfg.llama.cache_type_k,'--cache-type-v',$cfg.llama.cache_type_v,'--jinja')
$arguments=($argsList|ForEach-Object{if($_ -match '\s'){'"'+$_+'"'}else{$_}})-join ' '
$logDir=Join-Path $root 'logs/macro7a-inference'
New-Item -ItemType Directory -Path $logDir -Force|Out-Null
$process=Start-Process -FilePath $cfg.llama.executable -ArgumentList $arguments -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'stdout.log') -RedirectStandardError (Join-Path $logDir 'stderr.log')
$owned=[ordered]@{run_id='macro7a-20261013';pid=$process.Id;start_time=$process.StartTime.ToString('o');executable=$cfg.llama.executable;alias=$cfg.llama.alias;ctx_size=$cfg.llama.ctx_size;parallel=$cfg.llama.parallel;host=$cfg.llama.host;port=$cfg.llama.port}
$owned|ConvertTo-Json -Depth 5|Set-Content -LiteralPath (Join-Path $root 'runtime/macro7a-llama-owner.json') -Encoding UTF8
$ready=$false
try{
    $deadline=(Get-Date).AddSeconds($cfg.runner.llama_start_timeout_seconds)
    while((Get-Date)-lt $deadline){
        if($process.HasExited){throw 'LLAMA_STARTUP_FAILED'}
        try{$health=Invoke-RestMethod -Uri $cfg.llama.health_endpoint -TimeoutSec 2;if($health.status -eq 'ok'){$ready=$true;break}}catch{}
        Start-Sleep -Milliseconds 500
    }
    if(-not $ready){throw 'LLAMA_HEALTH_TIMEOUT'}
    $owned|ConvertTo-Json -Depth 5
}catch{
    if(-not $process.HasExited){Stop-Process -Id $process.Id -Force}
    throw
}
