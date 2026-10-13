param([Parameter(Mandatory=$true)][string]$ProjectRoot)
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$admission=& C:/Python314/python.exe (Join-Path $PSScriptRoot 'contract.py') validate --project $ProjectRoot
if($LASTEXITCODE -ne 0){return @{status='BLOCKED_REQUIRES_HUMAN';reason='APPROVED_CONTRACT_REQUIRED'}}
$raw=& C:/Python314/python.exe (Join-Path $PSScriptRoot 'completion.py') $ProjectRoot
$gate=($raw -join "`n")|ConvertFrom-Json
[IO.File]::WriteAllText((Join-Path $ProjectRoot '.autopilot/evidence/completion-gate.json'),($gate|ConvertTo-Json -Depth 14),[Text.Encoding]::UTF8)
$gate
