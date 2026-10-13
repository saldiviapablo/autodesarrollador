param([Parameter(Mandatory=$true)][string]$EvidencePath)
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$diff=& git -C $root diff --name-only 43843bc -- scripts/governed-cron.py scripts/invoke-governed-cron.ps1 scripts/jobs/health-snapshot.py config/cron-catalog.json scripts/governed-dashboard.py scripts/invoke-native-dashboard.ps1
$cron=& (Join-Path $root 'scripts/invoke-governed-cron.ps1') -Action list -ProjectPath (Join-Path $root 'sandbox/phase7a7-cron')
$dash=Get-Content -LiteralPath (Join-Path $root 'evidence/phase-7a8/tests.json') -Raw -Encoding UTF8|ConvertFrom-Json
$currentHash=(Get-FileHash -LiteralPath (Join-Path $root 'scripts/governed-dashboard.py') -Algorithm SHA256).Hash.ToLowerInvariant()
$checks=@{cron_dashboard_components_unchanged=(-not $diff);cron_native_list_empty=($cron.success -and @($cron.jobs).Count -eq 0);dashboard_review_still_bound=($dash.ui_review.source_sha256 -eq $currentHash);dashboard_closed=(-not(Get-NetTCPConnection -LocalPort 9119 -State Listen -ErrorAction SilentlyContinue))}
$result=@{status=$(if($checks.Values -notcontains $false){'PASS'}else{'FAIL'});checks=$checks;timestamp=(Get-Date).ToString('o')}
$result|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $root $EvidencePath) -Encoding UTF8
if($result.status -ne 'PASS'){throw ($result|ConvertTo-Json)}
