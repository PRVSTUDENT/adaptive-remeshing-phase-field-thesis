# Reconcile stale response if present
$bridgeDir = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge"
$respReady = Join-Path $bridgeDir "bridge_response.ready"
$archiveDir = Join-Path $bridgeDir "archive"
$reconciledDest = Join-Path $archiveDir "reconciled_utf16_bridge_response_20261117_234639_HND-F1850.ready"

if (Test-Path -LiteralPath $respReady) {
    Write-Host "[Dispatch] Archiving stale bridge_response.ready from F1850..." -ForegroundColor Yellow
    Move-Item -LiteralPath $respReady -Destination $reconciledDest -Force
}

# Verify clean handshake files
foreach ($f in @("bridge_request.tmp", "bridge_request.ready", "bridge_response.tmp", "bridge_response.ready")) {
    $p = Join-Path $bridgeDir $f
    if (Test-Path -LiteralPath $p) {
        throw "Found pending bridge file: $p"
    }
}

. (Join-Path $PSScriptRoot "..\..\.agents\scripts\Invoke-ChatGPTBridge.ps1")

$promptPath = "D:\Master thesis\Adaptive remeshing\.agents\bridge_history\f1857_assembled_prompt.txt"
$prompt = [System.IO.File]::ReadAllText($promptPath, [System.Text.UTF8Encoding]::new($false))

Write-Host "[Dispatch] Dispatching F1857 prompt ($($prompt.Length) chars) to ChatGPT bridge..." -ForegroundColor Cyan

$reply = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-F1857-F1856-REPORT-CORRECTION-001" -TaskId "F1857-F1856-REPORT-CORRECTION" -TimeoutMinutes 40

$outRespPath = "D:\Master thesis\Adaptive remeshing\.agents\bridge_history\f1857_bridge_response.txt"
[System.IO.File]::WriteAllText($outRespPath, $reply, [System.Text.UTF8Encoding]::new($false))
Write-Host "[Dispatch] Bridge response successfully received and saved to $outRespPath" -ForegroundColor Green
