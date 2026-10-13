param([Parameter(Mandatory=$true)][string]$ProjectRoot)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
. (Join-Path $PSScriptRoot 'core.ps1')
$info=Get-RunnerAdmission inspect $ProjectRoot
$path=Join-Path $info.auto 'STOP'
Write-RunnerJson $path @{run_id=$info.contract.run_id;requested_at=[datetimeoffset]::Now.ToString('o');mode='CONTROLLED_STOP'}
@{status='STOP_REQUESTED';run_id=$info.contract.run_id;path=$path;processes_killed_by_launcher=0}|ConvertTo-Json
