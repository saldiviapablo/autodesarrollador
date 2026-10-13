param([Parameter(Mandatory=$true)][ValidateSet('create','list','pause','resume','remove','run')][string]$Action,
      [Parameter(Mandatory=$true)][string]$ProjectPath,[string]$CatalogId,[string]$JobId)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$cfg=((& C:/Python314/python.exe (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$argsList=@('-I',(Join-Path $root 'scripts/governed-cron.py'),$Action,'--project',$ProjectPath)
if($CatalogId){$argsList+=@('--catalog-id',$CatalogId)}
if($JobId){$argsList+=@('--job-id',$JobId)}
$out=& $cfg.document_extraction.native_python @argsList
$code=$LASTEXITCODE
$result=($out -join "`n")|ConvertFrom-Json
if($code -ne 0 -and $result.decision -ne 'DENY'){throw 'CRON_NATIVE_FAILURE'}
$result
