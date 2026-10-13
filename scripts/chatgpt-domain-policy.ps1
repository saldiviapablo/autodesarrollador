# Domain-lock autoritativo de ChatGPT: URL absoluta, HTTPS y hostname exacto.
function Test-ChatGptUrl {
    param([AllowNull()][AllowEmptyString()][string]$Url)
    $parsedUrl = $null
    if (-not [System.Uri]::TryCreate($Url, [System.UriKind]::Absolute, [ref]$parsedUrl)) {
        return $false
    }
    return ($parsedUrl.Scheme -eq 'https' -and
            $parsedUrl.Host.ToLowerInvariant() -ceq 'chatgpt.com' -and
            [string]::IsNullOrEmpty($parsedUrl.UserInfo))
}
