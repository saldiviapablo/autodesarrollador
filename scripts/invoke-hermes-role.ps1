[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidateSet('supervisor','reviewer','researcher')][string]$Role,
      [Parameter(Mandatory=$true)][string]$Prompt,[string]$WorkingDir='', [int]$TimeoutSeconds=180)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$cfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n")|ConvertFrom-Json
$profile=$cfg.bot_roles.($Role+'_profile')
if(-not $profile){throw 'ROLE_PROFILE_NOT_CONFIGURED'}
$profileFile=Join-Path (Split-Path -Parent $cfg.hermes.profile_dir) ($profile+'/config.yaml')
$profileCfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json $profileFile) -join "`n")|ConvertFrom-Json
if(@($profileCfg.platform_toolsets.cli).Count -ne 0 -or @($profileCfg.plugins.enabled).Count -ne 0 -or $profileCfg.hooks_auto_accept){throw 'ROLE_READONLY_POLICY_MISMATCH'}
$approvedProfile=Join-Path $root ('config/hermes-'+$Role+'/config.yaml')
if((Get-FileHash -LiteralPath $profileFile -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath $approvedProfile -Algorithm SHA256).Hash){throw 'ROLE_PROFILE_INTEGRITY_MISMATCH'}
& (Join-Path $root 'scripts/invoke-hermes.ps1') -Profile $profile -Prompt $Prompt -WorkingDir $WorkingDir -Mode chat-stream-json -MaxTurns 3 -TimeoutSeconds $TimeoutSeconds
