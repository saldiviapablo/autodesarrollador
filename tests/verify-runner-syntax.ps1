$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot;$checks=@{}
foreach($file in @(Get-ChildItem -LiteralPath (Join-Path $root 'runner') -Filter '*.ps1')){
    $tokens=$null;$parseErrors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$parseErrors)
    if($parseErrors.Count){throw ($file.Name+': '+($parseErrors|Out-String))}
    $checks[$file.Name]='PASS'
}
@{status='PASS';powershell_ast=$checks}|ConvertTo-Json -Depth 4|Set-Content -LiteralPath (Join-Path $root 'evidence/regression-7b-final/runner-syntax.json') -Encoding UTF8
