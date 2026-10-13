param([Parameter(Mandatory=$true)][string]$EvidencePath)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$project=Join-Path $root 'sandbox/phase7a3-documents'
$fixture=Join-Path $project ('smoke-'+[guid]::NewGuid().ToString('N')+'.md')
try{
    Set-Content -LiteralPath $fixture -Value '# DA_PRIOR_DOCUMENT_SMOKE' -Encoding UTF8
    $doc=& (Join-Path $root 'scripts/extract-document.ps1') -InputPath $fixture -ProjectPath $project
}finally{if(Test-Path -LiteralPath $fixture){Remove-Item -LiteralPath $fixture}}
$browser=& (Join-Path $root 'scripts/invoke-native-browser.ps1') -Url 'https://docs.python.org/3/library/json.html' -ProjectPath (Join-Path $root 'sandbox/phase7a4-browser')
$checks=[ordered]@{document_extraction=($doc.status -eq 'SUCCESS');native_browser=($browser.status -eq 'SUCCESS' -and $browser.content -match 'JSON');browser_cleanup=$browser.cleanup_ok}
$result=[ordered]@{status=$(if($checks.Values -notcontains $false){'PASS'}else{'FAIL'});timestamp=(Get-Date).ToString('o');checks=$checks;local_inferences=0}
$result|ConvertTo-Json -Depth 8|Set-Content -LiteralPath (Join-Path $root $EvidencePath) -Encoding UTF8
if($result.status -ne 'PASS'){throw ($result|ConvertTo-Json -Depth 8)}
$result|ConvertTo-Json -Depth 8
