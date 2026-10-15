[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('supervisor','reviewer','researcher')][string]$Role,
      [Parameter(Mandatory=$true)][string]$Prompt,[string]$WorkingDir='', [int]$TimeoutSeconds=180,
      [string]$SourcePromptSha256='')
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$cfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$profile=$cfg.bot_roles.($Role+'_profile')
if(-not $profile){throw 'ROLE_PROFILE_NOT_CONFIGURED'}
$profileFile=Join-Path (Split-Path -Parent $cfg.hermes.profile_dir) ($profile+'/config.yaml')
$profileCfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json $profileFile) -join "`n")|ConvertFrom-Json
if(@($profileCfg.platform_toolsets.cli).Count -ne 0 -or @($profileCfg.plugins.enabled).Count -ne 0 -or @($profileCfg.mcp_servers.PSObject.Properties).Count -ne 0 -or $profileCfg.hooks_auto_accept){throw 'ROLE_READONLY_POLICY_MISMATCH'}
$approvedProfile=Join-Path $root ('config/hermes-'+$Role+'/config.yaml')
if((Get-FileHash -LiteralPath $profileFile -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $approvedProfile -Algorithm SHA256).Hash){throw 'ROLE_PROFILE_INTEGRITY_MISMATCH'}
$contractDir=$null;$binding=$null
try{
    if($Role -eq 'reviewer'){
        if(-not $SourcePromptSha256){$SourcePromptSha256=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($Prompt)))).Replace('-','').ToLowerInvariant()}
        $contractDir=Join-Path $root ('runtime/reviewer-contract-'+[guid]::NewGuid().ToString('N'))
        $null=New-Item -ItemType Directory -Path $contractDir
        $source=Join-Path $contractDir 'source.txt';$wrapped=Join-Path $contractDir 'wrapped.txt'
        [IO.File]::WriteAllText($source,$Prompt,(New-Object Text.UTF8Encoding($false,$true)))
        $bindingRaw=& C:/Python314/python.exe (Join-Path $root 'runner/reviewer_contract.py') wrap $source --output $wrapped --expected $SourcePromptSha256
        if($LASTEXITCODE -ne 0){throw 'REVIEWER_PROMPT_INTEGRITY_FAILED'}
        $binding=($bindingRaw -join "`n")|ConvertFrom-Json
        $Prompt=[IO.File]::ReadAllText($wrapped,(New-Object Text.UTF8Encoding($false,$true)))
    }
    $result=& (Join-Path $root 'scripts/invoke-hermes.ps1') -Profile $profile -Prompt $Prompt -WorkingDir $WorkingDir -Mode chat-stream-json -MaxTurns 3 -TimeoutSeconds $TimeoutSeconds
    if($binding){$result|Add-Member -NotePropertyName ReviewerContract -NotePropertyValue $binding}
    $result
}finally{
    if($contractDir){foreach($name in @('source.txt','wrapped.txt')){$file=Join-Path $contractDir $name;if(Test-Path -LiteralPath $file){Remove-Item -LiteralPath $file}};[IO.Directory]::Delete($contractDir)}
}
