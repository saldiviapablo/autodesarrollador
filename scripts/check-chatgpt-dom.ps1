# ==============================================================================
# scripts/check-chatgpt-dom.ps1 — Auditoría Directa del DOM de ChatGPT vía CDP
# ==============================================================================
param()

$tabs = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json"
$page = $tabs | Where-Object { $_.type -eq "page" } | Select-Object -First 1

if (-not $page) {
    Write-Host "NO_PAGE_FOUND"
    exit 1
}

Write-Host "PAGE_URL:   $($page.url)"
Write-Host "PAGE_TITLE: $($page.title)"

$ws = [System.Net.WebSockets.ClientWebSocket]::new()
$cts = [System.Threading.CancellationTokenSource]::new(5000)
$ws.ConnectAsync([System.Uri]$page.webSocketDebuggerUrl, $cts.Token).Wait()

$evalJs = @'
(() => {
    const articles = document.querySelectorAll('article[data-testid^="conversation-turn-"]');
    const conversationTurns = articles.length;
    const promptText = document.querySelector('#prompt-textarea') ? document.querySelector('#prompt-textarea').innerText : '';
    const bodyText = document.body ? document.body.innerText.substring(0, 300) : '';
    return {
        url: window.location.href,
        title: document.title,
        conversationTurns: conversationTurns,
        promptText: promptText,
        articlesFound: articles.length
    };
})()
'@

$payload = @{
    id = 2001
    method = "Runtime.evaluate"
    params = @{ expression = $evalJs; returnByValue = $true }
} | ConvertTo-Json -Compress

$bytes = [System.Text.Encoding]::UTF8.GetBytes($payload)
$ws.SendAsync([System.ArraySegment[byte]]::new($bytes), [System.Net.WebSockets.WebSocketMessageType]::Text, $true, [System.Threading.CancellationToken]::None).Wait()

$buf = [byte[]]::new(65536)
$res = $ws.ReceiveAsync([System.ArraySegment[byte]]::new($buf), [System.Threading.CancellationToken]::None).Result
$resp = [System.Text.Encoding]::UTF8.GetString($buf, 0, $res.Count) | ConvertFrom-Json

$ws.CloseAsync([System.Net.WebSockets.WebSocketCloseStatus]::NormalClosure, "Done", [System.Threading.CancellationToken]::None).Wait(2000)

Write-Host "DOM_RESULT:"
$resp.result.result.value | ConvertTo-Json
