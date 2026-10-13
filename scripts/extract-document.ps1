[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$InputPath,
      [Parameter(Mandatory=$true)][string]$ProjectPath,
      [double]$TimeoutSeconds=0)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts/security-guard.ps1')
$configFull=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n") | ConvertFrom-Json
$config=$configFull.document_extraction
if (-not $config -or -not $config.native_python) { throw 'DOCUMENT_CONFIG_MISSING' }
if ($TimeoutSeconds -le 0) { $TimeoutSeconds=[int]$config.timeout_seconds }
if ($TimeoutSeconds -gt [int]$config.timeout_seconds) { $TimeoutSeconds=[int]$config.timeout_seconds }
$start=New-Object System.Diagnostics.ProcessStartInfo
$start.FileName=$config.native_python
$arguments=@('-I',(Join-Path $root 'scripts/extract-document.py'),'--input',$InputPath,'--project',$ProjectPath.TrimEnd('\','/'))
$start.Arguments=($arguments | ForEach-Object { '"' + $_.Replace('"','\"') + '"' }) -join ' '
$start.UseShellExecute=$false; $start.CreateNoWindow=$true
$start.RedirectStandardOutput=$true; $start.RedirectStandardError=$true
$start.StandardOutputEncoding=[Text.Encoding]::UTF8; $start.StandardErrorEncoding=[Text.Encoding]::UTF8
$start.EnvironmentVariables['PYTHONDONTWRITEBYTECODE']='1'
$start.EnvironmentVariables['HERMES_DISABLE_LAZY_INSTALLS']='1'
$process=$null
$result=$null
try {
    $process=[Diagnostics.Process]::Start($start)
    $stdout=$process.StandardOutput.ReadToEndAsync(); $stderr=$process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit([int][Math]::Max(1,$TimeoutSeconds*1000))) {
        $null=& taskkill.exe /PID $process.Id /T /F 2>&1
        $process.WaitForExit(5000) | Out-Null
        $result=[pscustomobject]@{status='TIMEOUT';reason='DOCUMENT_EXTRACTION_TIMEOUT';cleanup_ok=$process.HasExited;child_pid=$process.Id}
    } else {
        $result=$stdout.Result | ConvertFrom-Json
        if ($process.ExitCode -ne 0) { $result=[pscustomobject]@{status='ERROR';reason='NATIVE_PROCESS_FAILED';cleanup_ok=$process.HasExited} }
    }
} finally {
    if ($process) {
        if (-not $process.HasExited) { $process.Kill(); $process.WaitForExit(5000) | Out-Null }
        # A forced timeout cannot run the child's finally. Delete only its
        # PID-prefixed private temporaries after confirming scope and no links.
        $tempCleanupOk=$true
        $projectFull=[IO.Path]::GetFullPath($ProjectPath).TrimEnd('\','/')
        $infraPrefix=$root.TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
        if ($projectFull -eq $root -or $projectFull.StartsWith($infraPrefix,[StringComparison]::OrdinalIgnoreCase)) {
            $tempRoot=Join-Path $projectFull '.autopilot/temp'
            if (Test-Path -LiteralPath $tempRoot) {
                $tempRootItem=Get-Item -LiteralPath $tempRoot
                $tempGuard=Test-WorkspacePathGuard -TargetFilePath $tempRoot -WorkspacePath $root -Operation 'READ'
                if (-not $tempGuard.Allowed -or ($tempRootItem.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { $tempCleanupOk=$false }
                else {
                    foreach ($owned in @(Get-ChildItem -LiteralPath $tempRoot -Directory -Filter ('document-'+$process.Id+'-*'))) {
                        $ownedFull=[IO.Path]::GetFullPath($owned.FullName)
                        $tempPrefix=[IO.Path]::GetFullPath($tempRoot).TrimEnd('\','/')+[IO.Path]::DirectorySeparatorChar
                        $ownedGuard=Test-WorkspacePathGuard -TargetFilePath $ownedFull -WorkspacePath $root -Operation 'DELETE'
                        if (-not $ownedGuard.Allowed -or -not $ownedFull.StartsWith($tempPrefix,[StringComparison]::OrdinalIgnoreCase) -or
                            ($owned.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { $tempCleanupOk=$false; continue }
                        $links=@(Get-ChildItem -LiteralPath $ownedFull -Recurse -Force | Where-Object { ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 })
                        if ($links.Count -gt 0) { $tempCleanupOk=$false; continue }
                        Remove-Item -LiteralPath $ownedFull -Recurse -Force
                    }
                }
            }
        }
        if ($result) { $result.cleanup_ok=($process.HasExited -and $tempCleanupOk) }
        $process.Dispose()
    }
}
return $result
