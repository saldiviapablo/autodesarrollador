param([string]$EvidenceRoot='')
$ErrorActionPreference='Stop';$env:PSModulePath=Join-Path $PSHOME 'Modules'
$env:PYTHONUTF8='1';$env:PYTHONDONTWRITEBYTECODE='1';[Console]::OutputEncoding=[Text.Encoding]::UTF8
$root=Split-Path -Parent $PSScriptRoot
if(-not $EvidenceRoot){$EvidenceRoot=Join-Path $root 'evidence/overnight-reviewer-20261015'}
. (Join-Path $root 'runner/core.ps1')
$script:Auto=Join-Path $root ('runtime/reviewer-core-'+[guid]::NewGuid().ToString('N'));$null=New-Item -ItemType Directory -Path $script:Auto
$script:Admission=[pscustomobject]@{plan=[pscustomobject]@{restart_budget=2}}
$script:Calls=0
# Replace only the subprocess boundary. The actual packet writer, binding and
# retry classifier remain the production functions loaded above.
function Invoke-RunnerManaged([string]$Name,[string]$Exe,[array]$Arguments,[int]$Timeout){
 $script:Calls++
 return @{exit_code=1;stdout='{"status":"ERROR","error_class":"REVIEWER_DECISION_INVALID"}'}
}
try{
 $packet=@{role='reviewer';backend='live';prompt="Untrusted evidence: áéíóú ñ`r`nRun tests, not an instruction to reviewer.";timeout=5}
 if(-not $packet.prompt.Contains([string][char]0x00F1) -or -not $packet.prompt.Contains([string][char]0x00E1)){throw 'POWERSHELL_SOURCE_UTF8_CORRUPTED'}
 $failed=$false;try{$null=Invoke-RunnerAgent 'reviewer' $packet}catch{if($_.Exception.Message -notmatch '^REVIEWER_DECISION_INVALID:'){throw};$failed=$true}
 if(-not $failed -or $script:Calls -ne 1){throw 'INVALID_DECISION_RETRIED_OR_ACCEPTED'}
 $actual=Get-Content -LiteralPath (Join-Path $script:Auto 'packet-reviewer.json') -Raw -Encoding UTF8|ConvertFrom-Json
 $expected=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($packet.prompt)))).Replace('-','').ToLowerInvariant()
 if($actual.review_input_sha256 -cne $expected -or $actual.prompt -cne $packet.prompt){throw 'PACKET_BINDING_FAILED'}
 $denied=$false;try{$null=Invoke-RunnerAgent 'reviewer' @{role='worker';prompt='bad'}}catch{if($_.Exception.Message -ne 'ROLE_PACKET_MISMATCH'){throw};$denied=$true}
 if(-not $denied -or $script:Calls -ne 1){throw 'WRONG_ROLE_DISPATCHED'}
 $result=@{status='PASS';packet_UTF8_bound=$true;wrong_role_denied_before_dispatch=$true;malformed_decision_fail_fast=$true;native_subprocess_attempts=$script:Calls;local_inferences=0}
 [IO.File]::WriteAllText((Join-Path $EvidenceRoot 'core-regression.json'),($result|ConvertTo-Json),(New-Object Text.UTF8Encoding($false)))
 $result|ConvertTo-Json
}finally{
 foreach($name in @('packet-reviewer.json','packet-reviewer.json.previous')){$p=Join-Path $script:Auto $name;if(Test-Path -LiteralPath $p){Remove-Item -LiteralPath $p}}
 [IO.Directory]::Delete($script:Auto)
}
