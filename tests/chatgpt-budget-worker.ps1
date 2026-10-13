param([string]$StatePath,[string]$Id)
$root=Split-Path -Parent $PSScriptRoot
$result=& (Join-Path $root 'scripts/consultar-chatgpt.ps1') -Question 'synthetic budget race' -ConsultationId $Id -StatePath $StatePath -MaxQueries 2 -MockResponse 'NO_NETWORK'
@{status=$result.Status}|ConvertTo-Json -Compress
