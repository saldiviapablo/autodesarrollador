[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$Url,[Parameter(Mandatory=$true)][string]$ProjectPath,[double]$TimeoutSeconds=0)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts/windows-process-job.ps1')
. (Join-Path $root 'scripts/security-guard.ps1')
$cfg=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/mcp-sandbox-server.py') --dump-yaml-json (Join-Path $root 'config/system.yaml')) -join "`n") | ConvertFrom-Json
if ($TimeoutSeconds -le 0 -or $TimeoutSeconds -gt $cfg.native_browser.timeout_seconds) { $TimeoutSeconds=$cfg.native_browser.timeout_seconds }
$info=New-Object Diagnostics.ProcessStartInfo
$info.FileName=$cfg.native_browser.native_python
$values=@('-I',(Join-Path $root 'scripts/native-browser.py'),'--url',$Url,'--project',$ProjectPath.TrimEnd('\','/'))
$info.Arguments=($values | ForEach-Object {'"'+$_.Replace('"','\"')+'"'}) -join ' '
$info.UseShellExecute=$false;$info.CreateNoWindow=$true;$info.RedirectStandardOutput=$true;$info.RedirectStandardError=$true
$info.StandardOutputEncoding=[Text.Encoding]::UTF8;$info.StandardErrorEncoding=[Text.Encoding]::UTF8
$jobDir=Join-Path $root 'runtime/browser-jobs'
New-Item -ItemType Directory -Path $jobDir -Force|Out-Null
$readyFile=Join-Path $jobDir ([guid]::NewGuid().ToString('N')+'.ready')
$info.EnvironmentVariables['DA_BROWSER_JOB_READY_FILE']=$readyFile
$info.EnvironmentVariables['DA_BROWSER_NATIVE_SITE_PACKAGES']=$cfg.native_browser.native_site_packages
$job=New-Object DaOwnedProcessJob
$process=$null
$result=$null
try {
    $process=[Diagnostics.Process]::Start($info)
    $job.Assign($process.Handle)
    [IO.File]::WriteAllText($readyFile,$process.Id.ToString())
    $stdout=$process.StandardOutput.ReadToEndAsync();$stderr=$process.StandardError.ReadToEndAsync()
    if (-not $process.WaitForExit([int][Math]::Max(1,$TimeoutSeconds*1000))) {
        $null=& taskkill.exe /PID $process.Id /T /F 2>&1
        $process.WaitForExit(5000)|Out-Null
        $result=[pscustomobject]@{status='TIMEOUT';reason='NATIVE_BROWSER_TIMEOUT';child_pid=$process.Id;cleanup_ok=$process.HasExited}
    } elseif ($process.ExitCode -ne 0) {
        $lastError=($stderr.Result -split "`r?`n" | Where-Object { $_ } | Select-Object -Last 1)
        $sanitized=((& 'C:/Python314/python.exe' (Join-Path $root 'scripts/hermes-pre-tool-hook.py') --sanitize-text $lastError) -join "`n") | ConvertFrom-Json
        $result=[pscustomobject]@{status='ERROR';reason='NATIVE_BROWSER_PROCESS_FAILED';diagnostic=$sanitized.sanitized_text;cleanup_ok=$false}
    } else {
        $result=$stdout.Result | ConvertFrom-Json
    }
} finally {
    $job.Dispose()
    if($process){
        if(-not $process.HasExited){$process.WaitForExit(5000)|Out-Null}
        $tempCleanup=$true
        $projectFull=[IO.Path]::GetFullPath($ProjectPath)
        $workRoot=Join-Path $projectFull '.autopilot/native-browser'
        $guard=Test-WorkspacePathGuard -TargetFilePath $workRoot -WorkspacePath $root -Operation 'READ'
        if($guard.Allowed -and (Test-Path -LiteralPath $workRoot)){
            foreach($owned in @(Get-ChildItem -LiteralPath $workRoot -Directory -Filter ('browser-'+$process.Id+'-*'))){
                $ownedGuard=Test-WorkspacePathGuard -TargetFilePath $owned.FullName -WorkspacePath $root -Operation 'DELETE'
                if(-not $ownedGuard.Allowed -or ($owned.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){$tempCleanup=$false;continue}
                $links=@(Get-ChildItem -LiteralPath $owned.FullName -Recurse -Force|Where-Object{($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0})
                if($links.Count -gt 0){$tempCleanup=$false;continue}
                Remove-Item -LiteralPath $owned.FullName -Recurse -Force
            }
        }
        if($result){$result | Add-Member -NotePropertyName cleanup_ok -NotePropertyValue ($process.HasExited -and $tempCleanup) -Force}
        $process.Dispose()
    }
    if(Test-Path -LiteralPath $readyFile){Remove-Item -LiteralPath $readyFile}
}
return $result
