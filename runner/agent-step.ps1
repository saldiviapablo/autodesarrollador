param([Parameter(Mandatory=$true)][string]$PacketPath)
$ErrorActionPreference='Stop';$root=Split-Path -Parent $PSScriptRoot
$packet=Get-Content -LiteralPath $PacketPath -Raw -Encoding UTF8|ConvertFrom-Json
try{
    if($packet.backend -eq 'probe'){
        if(-not $packet.project.StartsWith((Join-Path $root 'sandbox'),[StringComparison]::OrdinalIgnoreCase)){throw 'PROBE_SCOPE_DENIED'}
        Start-Sleep -Seconds $packet.probe_delay_seconds
        $result=@{status='SUCCESS';text='{"task":"probe","decision":"ACCEPTED"}';probe=$true}
    }elseif($packet.role -eq 'worker'){
        $r=& (Join-Path $root 'scripts/invoke-delegation.ps1') -RequestJson ($packet.request|ConvertTo-Json -Depth 12) -MaxWallTime ($packet.timeout.ToString()+'s') -TimeoutSeconds ($packet.timeout+5)
        $result=@{status=$r.Status;data=$r}
    }else{
        $r=& (Join-Path $root 'scripts/invoke-hermes-role.ps1') -Role $packet.role -Prompt $packet.prompt -WorkingDir $packet.project -TimeoutSeconds $packet.timeout
        $text='';foreach($line in ($r.Stdout -split '\r?\n')){try{$event=$line|ConvertFrom-Json;if($event.type -eq 'result'){$text=$event.text}}catch{}}
        $result=@{status=$(if($r.ExitCode -eq 0){'SUCCESS'}else{'ERROR'});text=$text;data=$r}
    }
    $result|ConvertTo-Json -Depth 18
    if($result.status -ne 'SUCCESS'){exit 1}
}catch{@{status='ERROR';error=$_.Exception.Message}|ConvertTo-Json;exit 1}
