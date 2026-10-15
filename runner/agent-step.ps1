param([Parameter(Mandatory=$true)][string]$PacketPath)
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$packet=Get-Content -LiteralPath $PacketPath -Raw -Encoding UTF8|ConvertFrom-Json
try{
    if($packet.review_input_sha256 -and $packet.role -cne 'reviewer'){throw 'REVIEWER_ROLE_MISMATCH'}
    if($packet.backend -eq 'probe'){
        if(-not $packet.project.StartsWith((Join-Path $root 'sandbox'),[StringComparison]::OrdinalIgnoreCase)){throw 'PROBE_SCOPE_DENIED'}
        Start-Sleep -Seconds $packet.probe_delay_seconds
        $result=@{status='SUCCESS';text='{"task":"probe","decision":"ACCEPTED"}';probe=$true}
    }elseif($packet.role -eq 'worker' -and $packet.mode -eq 'diagnosis'){
        $r=& (Join-Path $root 'scripts/invoke-qwen-code.ps1') -Prompt $packet.prompt -WorkingDir $packet.project -ApprovalMode yolo -MaxWallTime ($packet.timeout.ToString()+'s') -MaxToolCalls 5 -MaxSessionTurns 3 -TimeoutSeconds ($packet.timeout+5)
        $result=@{status=$(if($r.Success){'SUCCESS'}else{'ERROR'});data=@{WorkerOutput=$r}}
    }elseif($packet.role -eq 'worker'){
        $researchProject='';if($packet.research_inline){$researchProject=$packet.project}
        $r=& (Join-Path $root 'scripts/invoke-delegation.ps1') -RequestJson ($packet.request|ConvertTo-Json -Depth 12) -MaxWallTime ($packet.timeout.ToString()+'s') -TimeoutSeconds ($packet.timeout+5) -ResearchProject $researchProject
        $result=@{status=$r.Status;data=$r}
    }elseif($packet.role -eq 'reviewer'){
        $contract=Join-Path $root 'runner/reviewer_contract.py'
        $bound=& C:/Python314/python.exe $contract validate-packet $PacketPath
        if($LASTEXITCODE -ne 0){throw 'REVIEWER_PACKET_INTEGRITY_FAILED'}
        $r=& (Join-Path $root 'scripts/invoke-hermes-role.ps1') -Role reviewer -Prompt $packet.prompt -SourcePromptSha256 $packet.review_input_sha256 -WorkingDir $packet.project -TimeoutSeconds $packet.timeout
        $stream=Join-Path $root ('runtime/reviewer-stream-'+[guid]::NewGuid().ToString('N')+'.jsonl')
        try{
            [IO.File]::WriteAllText($stream,$r.Stdout,(New-Object Text.UTF8Encoding($false,$true)))
            $timeoutText=([bool]$r.TimedOut).ToString().ToLowerInvariant()
            $parsed=& C:/Python314/python.exe $contract parse-stream $stream --exit-code $r.ExitCode --timed-out $timeoutText
            $decision=($parsed -join "`n")|ConvertFrom-Json
            if($LASTEXITCODE -ne 0 -or -not $decision.valid){
                @{status='ERROR';error_class='REVIEWER_DECISION_INVALID';error=$decision.error;text='';data=$r}|ConvertTo-Json -Depth 18
                exit 1
            }
            $result=@{status='SUCCESS';text=$decision.text;validation=$decision;data=$r}
        }finally{if(Test-Path -LiteralPath $stream){Remove-Item -LiteralPath $stream}}
    }else{
        $r=& (Join-Path $root 'scripts/invoke-hermes-role.ps1') -Role $packet.role -Prompt $packet.prompt -WorkingDir $packet.project -TimeoutSeconds $packet.timeout
        $text='';foreach($line in ($r.Stdout -split '\r?\n')){try{$event=$line|ConvertFrom-Json;if($event.type -eq 'result'){$text=$event.text}}catch{}}
        $result=@{status=$(if($r.ExitCode -eq 0){'SUCCESS'}else{'ERROR'});text=$text;data=$r}
    }
    $result|ConvertTo-Json -Depth 18
    if($result.status -ne 'SUCCESS'){exit 1}
}catch{@{status='ERROR';error=$_.Exception.Message}|ConvertTo-Json;exit 1}
