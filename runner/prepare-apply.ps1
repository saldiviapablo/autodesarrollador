param([string]$EncodedRequest,[switch]$ReadRequestFromStdin)
$ErrorActionPreference='Stop'
if($PSVersionTable.PSVersion.Major -le 5){$env:PSModulePath=(Join-Path $PSHOME 'Modules')}
[Console]::OutputEncoding=[Text.Encoding]::UTF8
[Console]::InputEncoding=New-Object Text.UTF8Encoding($false,$true)
if($ReadRequestFromStdin){
    if($EncodedRequest){throw 'AMBIGUOUS_PREPARE_TRANSPORT'}
    $EncodedRequest=[Console]::In.ReadToEnd()
}
if(-not $EncodedRequest -or $EncodedRequest.Length -gt 2097152){throw 'PREPARE_REQUEST_REQUIRED_OR_TOO_LARGE'}
$payload=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($EncodedRequest))|ConvertFrom-Json
$validation=$EncodedRequest | & C:/Python314/python.exe (Join-Path $PSScriptRoot 'prepare.py') --request-stdin --validate-only
if($LASTEXITCODE -ne 0){$validation;exit 2}
# Keep all initializer descendants in the existing kill-on-close ownership Job.
# The OS closes this process's Job handle on exit or parent-enforced timeout.
. (Join-Path $PSScriptRoot '../scripts/windows-process-job.ps1')
$prepareJob=New-Object DaOwnedProcessJob
$prepareJob.Assign([Diagnostics.Process]::GetCurrentProcess().Handle)
$validation=$EncodedRequest | & C:/Python314/python.exe (Join-Path $PSScriptRoot 'prepare.py') --request-stdin --validate-only
if($LASTEXITCODE -ne 0){$validation;exit 2}
# No initializer or state-manager is loaded before the shared read-only validation.
Write-Output 'PREPARE_APPLY_STARTED'
try {
    $request=$payload.request
    $null=& (Join-Path $PSScriptRoot '../scripts/init-autopilot-project.ps1') -ProjectPath $payload.binding.project -Objective $request.objective -AcceptanceCriteria @($request.criteria)
    exit 0
} catch {
    Write-Output 'PREPARE_INITIALIZER_ERROR'
    exit 2
}
