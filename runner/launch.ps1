param([Parameter(Mandatory=$true)][string]$ProjectRoot,[switch]$Unattended)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
. (Join-Path $PSScriptRoot 'core.ps1')
$info=Get-RunnerAdmission inspect $ProjectRoot
try{$null=Get-RunnerAdmission validate $ProjectRoot}catch{
    if($Unattended){@{status='BLOCKED_REQUIRES_HUMAN';reason='APPROVAL_REQUIRED';started=$false}|ConvertTo-Json;exit 2}
    Write-Host ('Proyecto: '+$info.project)
    Write-Host ('Objetivo: '+$info.contract.objective)
    Write-Host ('Criterios: '+($info.contract.acceptance_criteria -join '; '))
    Write-Host ('Digest de contrato/plan/policy: '+$info.digest)
    $answer=Read-Host 'Aprobar una vez este contrato y sus limites? Escriba APROBAR'
    if($answer -cne 'APROBAR'){@{status='BLOCKED_REQUIRES_HUMAN';reason='APPROVAL_NOT_GIVEN'}|ConvertTo-Json;exit 2}
    $null=Get-RunnerAdmission approve $ProjectRoot $info.digest
}
& (Join-Path $PSScriptRoot 'run.ps1') -ProjectRoot $ProjectRoot -Action Start
exit $LASTEXITCODE
