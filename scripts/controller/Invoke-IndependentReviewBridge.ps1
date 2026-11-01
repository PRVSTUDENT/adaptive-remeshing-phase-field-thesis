[CmdletBinding()]
param([Parameter(Mandatory)][string]$RequestPath,[Parameter(Mandatory)][string]$ResponsePath)
$ErrorActionPreference='Stop'
$root=Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$request=Get-Content -LiteralPath $RequestPath -Raw|ConvertFrom-Json
if($request.operation_id -notmatch '^[a-z][a-z0-9_]{5,140}$'){throw 'Invalid review operation'}
if(Test-Path -LiteralPath $ResponsePath){
    Write-Host "Preserving existing response: $ResponsePath"
    return
}

# 1. Recovery check: Look for archived response with matching correlation ID
$bridgeArchiveDir = Join-Path $env:USERPROFILE "OpenClawPAD\ChatGPTBridge\archive"
$recoveredReply = $null
if (Test-Path -LiteralPath $bridgeArchiveDir) {
    $matchedArchives = @(Get-ChildItem -Path $bridgeArchiveDir -Filter "*$($request.correlation_id)*.json" | Sort-Object LastWriteTime -Descending)
    if ($matchedArchives.Count -gt 0) {
        try {
            $archContent = Get-Content -LiteralPath $matchedArchives[0].FullName -Raw | ConvertFrom-Json
            if ($archContent.response) {
                $recoveredReply = [string]$archContent.response
                Write-Host "Recovered response for correlation $($request.correlation_id) from bridge archive: $($matchedArchives[0].Name)" -ForegroundColor Cyan
            }
        } catch {}
    }
}

# 2. Dispatch to bridge if not recovered
$reply = $recoveredReply
if (-not $reply) {
    . (Join-Path $root '.agents/scripts/Invoke-ChatGPTBridge.ps1')
    $prompt=@"
INDEPENDENT_STRUCTURED_REVIEW_V1
Review the attached exact scientific evidence. Do not infer PASS from summaries or scheduler Exit0.
Return a JSON decision with reviewer=ChatGPT-independent-review, author=gemini-antigravity,
operation_id, correlation_id, fingerprint, reviewed_hashes (exact packet values),
decision=APPROVE|REJECT|INSUFFICIENT_EVIDENCE, rationale, assistant_message_id and conversation_url.
Do not sign or invent provenance. The independently controlled bridge worker must archive
the assistant response and attest its origin in an Ed25519 envelope {decision, signature}.
If evidence is incomplete use INSUFFICIENT_EVIDENCE. No scientific jobs in this review.

$(Get-Content -LiteralPath $RequestPath -Raw)
"@
    $reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $request.correlation_id -TimeoutMinutes 2 -RequireHeartbeat
}

# 3. Attest and sign through the trusted worker boundary
$attestScript = Join-Path $PSScriptRoot 'attest_review.py'
$replyTmp = [IO.Path]::GetTempFileName()
try {
    [IO.File]::WriteAllText($replyTmp, $reply, [Text.UTF8Encoding]::new($false))
    & py -3 $attestScript --request-path $RequestPath --response-path $ResponsePath --reply-file $replyTmp
    if ($LASTEXITCODE -ne 0) {
        throw "Review attestation failed: could not generate authenticated receipt"
    }
} finally {
    if (Test-Path -LiteralPath $replyTmp) { Remove-Item -LiteralPath $replyTmp -Force -ErrorAction SilentlyContinue }
}
