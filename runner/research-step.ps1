param([string]$ProjectRoot,[string]$Url)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
$r=& (Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/web-research.ps1') -Url $Url -TimeoutSeconds 25 -OutputPath (Join-Path $ProjectRoot '.autopilot/evidence/WEB.json')
$r|ConvertTo-Json -Depth 12
if(-not $r.Success){exit 1}
