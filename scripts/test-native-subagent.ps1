[CmdletBinding()]
param()
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts/inference-lock.ps1')
$cfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$token=Acquire-InferenceLock -Owner 'hermes-native-subagent' -Purpose 'synchronous-native-child-policy-test' -TimeoutSeconds 360 -InfraPath $root
if(-not $token.Acquired){throw 'INFERENCE_LOCK_UNAVAILABLE'}
try{
    $env:HERMES_DISABLE_LAZY_INSTALLS='1';$env:PYTHONDONTWRITEBYTECODE='1'
    & $cfg.document_extraction.native_python (Join-Path $root 'scripts/test-native-subagent.py') $cfg.document_extraction.native_source_dir
    if($LASTEXITCODE -ne 0){throw 'Native subagent harness failed'}
}finally{$null=Release-InferenceLock -LockToken $token}
