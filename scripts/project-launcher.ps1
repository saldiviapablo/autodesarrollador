[CmdletBinding()]
param([string]$ProjectRoot='', [switch]$Stop)
$ErrorActionPreference='Stop'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1'
$argsList=@('-B',(Join-Path $PSScriptRoot 'project_launcher_ui.py'))
if($ProjectRoot){$argsList+=@('--project',$ProjectRoot)}
if($Stop){$argsList+='--stop'}
& C:/Python314/python.exe @argsList
if($LASTEXITCODE -ne 0){Write-Host 'No se pudo abrir el iniciador. El detalle del error aparece arriba.'}
exit $LASTEXITCODE
