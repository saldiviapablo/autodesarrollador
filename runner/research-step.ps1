param(
    [string]$ProjectRoot,
    [string]$Url='',
    [string]$Query='',
    [string]$DomainsJson='[]',
    [int]$MaxResults=5
)
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
[Console]::OutputEncoding=[Text.Encoding]::UTF8
if(([string]::IsNullOrWhiteSpace($Url)) -eq ([string]::IsNullOrWhiteSpace($Query))){throw 'RESEARCH_REQUIRES_EXACTLY_ONE_URL_OR_QUERY'}
if($MaxResults -lt 1 -or $MaxResults -gt 10){throw 'RESEARCH_MAX_RESULTS_INVALID'}
$wrapper=Join-Path (Split-Path -Parent $PSScriptRoot) 'scripts/web-research.ps1'
$params=@{
    TimeoutSeconds=25
    OutputPath=(Join-Path $ProjectRoot '.autopilot/evidence/WEB.json')
    MaxResults=$MaxResults
}
if(-not [string]::IsNullOrWhiteSpace($Url)){
    $params.Url=$Url
}else{
    $params.Query=$Query
    $params.FetchTop=$true
    $params.TimeoutSeconds=20
    $params.ProcessTimeoutSeconds=140
    $domains=@()
    try{$domains=@($DomainsJson|ConvertFrom-Json)}catch{throw 'RESEARCH_DOMAINS_JSON_INVALID'}
    if($domains.Count -gt 0){$params.Domains=@($domains)}
}
$r=& $wrapper @params
$r|ConvertTo-Json -Depth 12
if(-not $r.Success){exit 1}
