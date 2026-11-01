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
$matchedArchive = $null
if (Test-Path -LiteralPath $bridgeArchiveDir) {
    $matchedArchives = @(Get-ChildItem -Path $bridgeArchiveDir -Filter "*$($request.correlation_id)*.json" | Sort-Object LastWriteTime -Descending)
    if ($matchedArchives.Count -gt 0) {
        $matchedArchive = $matchedArchives[0].FullName
        Write-Host "Recovered response for correlation $($request.correlation_id) from bridge archive: $($matchedArchives[0].Name)" -ForegroundColor Cyan
    }
}

# 2. Dispatch to bridge if not recovered
if (-not $matchedArchive) {
    . (Join-Path $root '.agents/scripts/Invoke-ChatGPTBridge.ps1')
    $author = if ($request.definition.author) { $request.definition.author } else { "gemini-antigravity" }
    $prompt=@"
INDEPENDENT_STRUCTURED_REVIEW_V1
Review the attached exact scientific evidence packet. Do not infer PASS from summaries or scheduler Exit0.
You must return your decision strictly as a JSON object inside a ```json ``` code block. Do NOT include any conversational preamble or text outside the code block.

Required JSON fields:
- reviewer: "ChatGPT-independent-review"
- author: "$author"
- operation_id: "$($request.operation_id)"
- correlation_id: "$($request.correlation_id)"
- fingerprint: "$($request.fingerprint)"
- reviewed_hashes: exact copy of the hashes dictionary in the request packet
- decision: "APPROVE", "REJECT", or "INSUFFICIENT_EVIDENCE"
- rationale: concise scientific justification based on the evidence
- assistant_message_id: your assistant message ID or "msg-$($request.correlation_id)"
- conversation_url: "https://chatgpt.com/c/independent-review-bridge"

Do not sign or invent provenance; the separate bridge worker verifies and signs the receipt.

$(Get-Content -LiteralPath $RequestPath -Raw)
"@
    $reply=Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $request.correlation_id -TimeoutMinutes 5 -RequireHeartbeat
    $matchedArchives = @(Get-ChildItem -Path $bridgeArchiveDir -Filter "*$($request.correlation_id)*.json" | Sort-Object LastWriteTime -Descending)
    if ($matchedArchives.Count -gt 0) {
        $matchedArchive = $matchedArchives[0].FullName
    } else {
        throw "Bridge finished but no authentic archive file found for correlation $($request.correlation_id)"
    }
}

# 3. Attest and sign through the trusted worker boundary using authentic bridge archive
$attestScript = Join-Path $PSScriptRoot 'attest_review.py'
& py -3 $attestScript --request-path $RequestPath --response-path $ResponsePath --bridge-archive $matchedArchive
if ($LASTEXITCODE -ne 0) {
    throw "Review attestation failed: authentic bridge archive could not be attested"
}
