[CmdletBinding()]
param([Parameter(Mandatory)][string]$RequestPath,[Parameter(Mandatory)][string]$ResponsePath,[switch]$DryRun)
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
    $contract=$request.definition.research_contract
    if (-not $contract) { throw 'Definition research_contract required for guarded bridge publication' }
    $taskId=if($request.definition.task_id){$request.definition.task_id}else{$request.operation_id}
    $rulesHash=(Get-FileHash -LiteralPath (Join-Path $root '.agents/scripts/bridge_rules.txt')).Hash
    $wire=[ordered]@{
        protocol='INDEPENDENT_STRUCTURED_REVIEW_V1'
        correlation_id=$request.correlation_id
        task_id=$taskId
        title=$request.definition.title
        goal_id=$contract.goal_id
        canonical_rules_sha256=$rulesHash
        research_contract=$contract
        master_goal_status='OPEN'
        evidence_packet=$request
    }
    $prompt=@"
INDEPENDENT_STRUCTURED_REVIEW_V1
$($wire|ConvertTo-Json -Depth 60)

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
- protocol: "INDEPENDENT_STRUCTURED_REVIEW_V1"
- task_id: "$taskId"
- goal_id: "$($contract.goal_id)"
- canonical_rules_sha256: "$rulesHash"
- master_goal_status: "OPEN"
- next_operation: a valid research_contract for your next recommended operation
- next_instruction_to_antigravity: specific scientific next instruction
- assistant_message_id and conversation_url: actual independently verified message provenance only. Never invent placeholders. If unavailable, state that in rationale; the dispatcher must not treat missing provenance as approval.

Do not sign or invent provenance; the separate bridge worker verifies and signs the receipt.

"@
    if($DryRun){
        Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $request.correlation_id -TaskId $taskId -DryRun
        return
    }
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
