param([string]$EvidenceDir='')
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
if(-not $EvidenceDir){$EvidenceDir=Join-Path $root 'evidence/regression-7a-final'}
New-Item -ItemType Directory -Path $EvidenceDir -Force|Out-Null
. (Join-Path $root 'scripts/windows-process-job.ps1')
function Quote-Arg([string]$Value){return '"'+($Value -replace '(\\*)(")','$1$1\"' -replace '(\\+)$','$1$1')+'"'}
$script:results=[ordered]@{}
function Run-Gate([string]$Name,[string]$Exe,[array]$Arguments,[int]$Timeout=120){
    $job=New-Object DaOwnedProcessJob;$proc=$null
    try{
        $psi=New-Object Diagnostics.ProcessStartInfo;$psi.FileName=$Exe;$psi.Arguments=($Arguments|ForEach-Object{Quote-Arg $_}) -join ' ';$psi.WorkingDirectory=$root
        $psi.UseShellExecute=$false;$psi.CreateNoWindow=$true;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
        $psi.EnvironmentVariables['PYTHONDONTWRITEBYTECODE']='1'
        $proc=[Diagnostics.Process]::Start($psi);$job.Assign($proc.Handle)
        $out=$proc.StandardOutput.ReadToEndAsync();$err=$proc.StandardError.ReadToEndAsync()
        $finished=$proc.WaitForExit($Timeout*1000)
        if(-not $finished){throw ('GATE_TIMEOUT: '+$Name)}
        $null=[Threading.Tasks.Task]::WaitAll(@($out,$err),3000)
        [IO.File]::WriteAllText((Join-Path $EvidenceDir ($Name+'.stdout.txt')),$out.Result,[Text.Encoding]::UTF8)
        [IO.File]::WriteAllText((Join-Path $EvidenceDir ($Name+'.stderr.txt')),$err.Result,[Text.Encoding]::UTF8)
        $script:results[$Name]=@{status=$(if($proc.ExitCode -eq 0){'PASS'}else{'FAIL'});exit_code=$proc.ExitCode;owned_pid=$proc.Id}
        if($proc.ExitCode -ne 0){throw ('MANDATORY_TEST_FAILED: '+$Name)}
        Write-Output ($Name+': PASS')
    }finally{$job.Dispose()}
}
try{
    Run-Gate 'central-config' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'scripts/verify-config.ps1'),'-LogFile',(Join-Path $EvidenceDir 'central-config.log.txt'))
    Run-Gate 'security' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'tests/test-fase15-security.ps1'),'-SandboxDir',(Join-Path $root 'sandbox/regression7a-security'),'-EvidenceDir',(Join-Path $EvidenceDir 'security'))
    Run-Gate 'inference-lock' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'tests/test-inference-lock.ps1'),'-EvidenceDir',(Join-Path $EvidenceDir 'lock'),'-LogFile',(Join-Path $EvidenceDir 'lock.log.txt'))
    Run-Gate 'domain-node' 'node.exe' @((Join-Path $root 'tests/test-chatgpt-domain-lock.js'))
    Run-Gate 'domain-powershell' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'tests/test-chatgpt-domain-lock.ps1'))
    Run-Gate 'capability-smoke' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'scripts/verify-capability-smoke.ps1'),'-EvidencePath',(Join-Path $EvidenceDir 'capability-smoke.json'))
    Run-Gate 'prior-capabilities-smoke' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'scripts/verify-7a-prior-capabilities.ps1'),'-EvidencePath','evidence/regression-7a-final/prior-capabilities-smoke.json')
    Run-Gate 'roles-worktree-smoke' 'C:/Python314/python.exe' @((Join-Path $root 'tests/verify-later-capabilities.py'),'evidence/regression-7a-final/roles-worktree-smoke.json')
    Run-Gate 'cron-dashboard-smoke' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'scripts/verify-capabilities-7a7-7a8.ps1'),'-EvidencePath','evidence/regression-7a-final/cron-dashboard-smoke.json')
    Run-Gate 'state-schema' 'C:/Python314/python.exe' @((Join-Path $root 'tests/test-chatgpt-state-schema.py'))
    Run-Gate 'recovery-delegation' 'powershell.exe' @('-NoProfile','-NonInteractive','-File',(Join-Path $root 'tests/test-regression-recovery-delegation.ps1'),'-EvidenceDir',$EvidenceDir) 210
}finally{
    @{status=$(if($script:results.Values.status -contains 'FAIL'){'FAIL'}elseif($script:results.Count -eq 11){'PASS'}else{'INCOMPLETE'});gates=$script:results;timestamp=(Get-Date).ToString('o');full_approved_7a_suites_repeated=$false}|ConvertTo-Json -Depth 12|Set-Content -LiteralPath (Join-Path $EvidenceDir 'suite.json') -Encoding UTF8
}
