[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
. (Join-Path $root 'scripts/chatgpt-domain-policy.ps1')
$cases = @(
    @('https://chatgpt.com/', $true),
    @('https://chatgpt.com/c/preflight?x=1#part', $true),
    @('https://openai.com/', $false),
    @('https://www.openai.com/', $false),
    @('https://foo.chatgpt.com/', $false),
    @('https://chatgpt.com.evil.test/', $false),
    @('https://chatgpt.com@evil.test/', $false),
    @('http://chatgpt.com/', $false),
    @('URL invalida', $false),
    @('about:blank', $false),
    @('', $false),
    @('https://chatgpt.com./', $false),
    @('https://user:password@chatgpt.com/', $false)
)
$results = foreach ($case in $cases) {
    $url = [string]$case[0]
    $expected = [bool]$case[1]
    if ((Test-ChatGptUrl -Url $url) -ne $expected) { throw "Domain policy mismatch: $url" }
    if (-not $expected) {
        $wrapper = & (Join-Path $root 'scripts/consultar-chatgpt.ps1') -TargetUrl $url -MockResponse 'must-not-run'
        if ($wrapper.Status -ne 'DOMAIN_BLOCKED') { throw "Wrapper accepted forbidden URL: $url" }
        $launcher = & (Join-Path $root 'scripts/start-hermes-chatgpt.ps1') -TargetUrl $url
        if ($launcher.Status -ne 'DOMAIN_BLOCKED') { throw "Launcher accepted forbidden URL: $url" }
    }
    [ordered]@{ url=$url; expected= $(if ($expected) { 'ALLOW' } else { 'DENY' }); status='PASS' }
}
[ordered]@{ test_id='PREFLIGHT-DOMAIN-POWERSHELL'; status='PASS'; cases=@($results) } | ConvertTo-Json -Depth 6
