# Canonical bridge scope/format checks; no solver, scheduler or process mutation.
function Get-BridgePolicyContext {
    param([string]$RulesPath)
    $sourceRoot = 'D:\Master thesis\Adaptive remeshing\.agents\scripts'
    if (-not (Test-Path -LiteralPath $sourceRoot)) { $sourceRoot = $PSScriptRoot }
    $canonical = Join-Path $sourceRoot 'bridge_rules.txt'
    $policyPath = Join-Path $sourceRoot 'bridge_research_policy.json'
    foreach ($path in @($canonical,$policyPath)) {
        if (-not (Test-Path -LiteralPath $path)) { throw "BRIDGE_CANONICAL_POLICY_MISSING: $path" }
    }
    $hash = (Get-FileHash -LiteralPath $canonical -Algorithm SHA256).Hash
    if ($RulesPath -and ((Get-FileHash -LiteralPath $RulesPath -Algorithm SHA256).Hash -cne $hash)) {
        throw 'BRIDGE_RULES_HASH_MISMATCH: alternate rules cannot replace canonical research policy.'
    }
    $rules = [IO.File]::ReadAllText($canonical).Trim()
    $policy = Get-Content -LiteralPath $policyPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($rules -notmatch [regex]::Escape($policy.goal_id)) { throw 'BRIDGE_RULES_POLICY_CONFLICT' }
    [pscustomobject]@{rules=$rules;rules_sha256=$hash;policy=$policy;policy_sha256=(Get-FileHash -LiteralPath $policyPath -Algorithm SHA256).Hash}
}
function ConvertFrom-BridgeJsonBlock {
    param([string]$Text)
    # Request JSON must be a standalone top-level object; report text remains immutable.
    $match = [regex]::Match($Text,'(?ms)^\{.*?^\}\s*(?=\r?$|\n)')
    if (-not $match.Success) { throw 'BRIDGE_REQUEST_JSON_REQUIRED: put a standalone JSON request after the protocol line.' }
    try { $match.Value | ConvertFrom-Json -ErrorAction Stop }
    catch { throw 'BRIDGE_REQUEST_JSON_INVALID' }
}
function Assert-BridgeResearchContract {
    param($Contract,$Policy,[string]$TaskIdentity)
    if (-not $Contract) { throw 'BRIDGE_RESEARCH_CONTRACT_REQUIRED: declare goal_id, method, operation, numerical_uncertainty, expected_numerical_result, indicator_type, indicator_role and causal_evidence_status.' }
    if ($TaskIdentity -match $Policy.paused_task_pattern) { throw 'BRIDGE_RESEARCH_SCOPE_CONFLICT: Method C, state transfer, coupled-fracture validation and thesis/presentation successors are paused.' }
    if ($Contract.goal_id -cne $Policy.goal_id -or $Contract.method -cne $Policy.method -or $Contract.operation -cnotin $Policy.allowed_operations) { throw 'BRIDGE_RESEARCH_SCOPE_CONFLICT: use the canonical Method A numerical objective.' }
    foreach ($key in @('numerical_uncertainty','expected_numerical_result')) {
        if ([string]::IsNullOrWhiteSpace([string]$Contract.$key) -or ([string]$Contract.$key).Length -lt 12) { throw "BRIDGE_NUMERICAL_PURPOSE_REQUIRED: $key" }
    }
    if ($Contract.indicator_type -ceq $Policy.native_indicator) {
        if ($Contract.indicator_role -cne 'PRIMARY_NATIVE_MISESERI') { throw 'BRIDGE_INDICATOR_PROVENANCE_CONFLICT' }
    } elseif ($Contract.indicator_type -cin @('DAMAGE_INFORMED_SIZING','SYNTHETIC_TEST')) {
        if ($Contract.indicator_role -cne 'SEPARATE_COMPARISON' -or $Contract.qualifies_native_miseseri -isnot [bool] -or $Contract.qualifies_native_miseseri) { throw 'BRIDGE_SYNTHETIC_INDICATOR_NOT_NATIVE: separate comparison only, never native MISESERI acceptance.' }
    } else { throw 'BRIDGE_INDICATOR_PROVENANCE_REQUIRED' }
    if ($Contract.causal_evidence_status -cnotin @('PLANNED','MISSING','VERIFIED')) { throw 'BRIDGE_CAUSAL_EVIDENCE_STATUS_REQUIRED' }
    if ($Contract.causal_evidence_status -ceq 'VERIFIED') {
        $c=$Contract.causal_evidence
        if (-not $c -or $c.donor_sha256 -notmatch '^[A-Fa-f0-9]{64}$' -or [string]::IsNullOrWhiteSpace([string]$c.donor_step) -or [string]::IsNullOrWhiteSpace([string]$c.indicator_frame_range) -or [string]::IsNullOrWhiteSpace([string]$c.held_out_later_solution)) { throw 'BRIDGE_CAUSAL_PROVENANCE_REQUIRED' }
        if ($c.uses_future_frames -isnot [bool] -or $c.uses_future_frames) { throw 'BRIDGE_CAUSAL_FUTURE_INFORMATION_FORBIDDEN' }
        $cutoff=0.0; $latest=0.0
        if (-not [double]::TryParse([string]$c.remesh_time,[ref]$cutoff) -or -not [double]::TryParse([string]$c.maximum_indicator_time,[ref]$latest) -or [double]::IsNaN($cutoff) -or [double]::IsInfinity($cutoff) -or [double]::IsNaN($latest) -or [double]::IsInfinity($latest) -or $cutoff -lt 0 -or $latest -lt 0 -or $latest -gt $cutoff) { throw 'BRIDGE_CAUSAL_TIME_CUTOFF_VIOLATION' }
    }
}
function New-BridgeCanonicalPrompt {
    param([string]$PromptText,[string]$HandoffId,[string]$TaskId,[string]$RulesPath)
    $ctx=Get-BridgePolicyContext -RulesPath $RulesPath
    $headers=[regex]::Matches($PromptText,'(?m)^\s*\[BRIDGE_HANDOFF_ID=(HND-[A-Za-z0-9_-]+)\]\s*$')
    if ($HandoffId -and $HandoffId -cnotmatch '^HND-[A-Za-z0-9_-]+$') { throw 'BRIDGE_INVALID_HANDOFF_ID' }
    if ($headers.Count -gt 1) { throw 'BRIDGE_DUPLICATE_HANDOFF_HEADER' }
    if (-not $HandoffId -and $headers.Count -eq 1) { $HandoffId=$headers[0].Groups[1].Value }
    if (-not $HandoffId) { throw 'BRIDGE_HANDOFF_ID_REQUIRED: preserve a durable correlation; do not generate a replacement on retry.' }
    if ($headers.Count -eq 1 -and $headers[0].Groups[1].Value -cne $HandoffId) { throw 'BRIDGE_REQUEST_CORRELATION_MISMATCH' }
    if ($PromptText -match 'BRIDGE_HANDOFF_ID=' -and $headers.Count -eq 0) { throw 'BRIDGE_MALFORMED_HANDOFF_HEADER' }
    $protocols=[regex]::Matches($PromptText,'(?m)^(INDEPENDENT_STRUCTURED_REVIEW_V1|CHATGPT_SUPERVISOR_V1)\r?$')
    if ($protocols.Count -ne 1) { throw 'BRIDGE_STRUCTURED_PROTOCOL_REQUIRED' }
    $protocol=$protocols[0].Groups[1].Value
    $req=ConvertFrom-BridgeJsonBlock -Text $PromptText
    if ($req.protocol -cne $protocol -or $req.correlation_id -cne $HandoffId) { throw 'BRIDGE_REQUEST_CORRELATION_MISMATCH' }
    if ([string]::IsNullOrWhiteSpace($req.task_id) -or ($TaskId -and $req.task_id -cne $TaskId)) { throw 'BRIDGE_REQUEST_TASK_MISMATCH' }
    Assert-BridgeResearchContract -Contract $req.research_contract -Policy $ctx.policy -TaskIdentity "$($req.task_id) $($req.title)"
    $claimed=@([regex]::Matches($PromptText,'(?mi)^BRIDGE_RULES_SHA256:\s*([A-Fa-f0-9]{64})\s*$') | ForEach-Object {$_.Groups[1].Value})
    if ($req.canonical_rules_sha256) { $claimed += [string]$req.canonical_rules_sha256 }
    foreach($hash in $claimed) { if ($hash -ine $ctx.rules_sha256) { throw 'BRIDGE_RULES_HASH_MISMATCH' } }
    $start='---------------- BRIDGE CONTROLLER RULES ----------------'
    $end='---------------- END BRIDGE CONTROLLER RULES ----------------'
    $body=$PromptText
    if ($body.Contains($start) -or $body.Contains($end)) {
        if ([regex]::Matches($body,[regex]::Escape($start)).Count -ne 1 -or [regex]::Matches($body,[regex]::Escape($end)).Count -ne 1) { throw 'BRIDGE_RULES_BLOCK_INVALID' }
        $a=$body.IndexOf($start);$b=$body.IndexOf($end)
        if ($b -le $a) { throw 'BRIDGE_RULES_BLOCK_INVALID' }
        $embedded=$body.Substring($a+$start.Length,$b-$a-$start.Length).Trim() -replace '\r\n',"`n"
        if ($embedded -cne ($ctx.rules -replace '\r\n',"`n")) { throw 'BRIDGE_EMBEDDED_PRIORITY_CONFLICT' }
        $body=$body.Remove($a,$b+$end.Length-$a)
    } elseif ($body -match '(?mi)^CANONICAL BRIDGE RULES\s*$') {
        $m=[regex]::Match($body,'(?mi)^CANONICAL BRIDGE RULES\s*$')
        $tail=$body.Substring($m.Index+$m.Length).Trim() -replace '^[=\-]+\s*',''
        if (($tail.Trim() -replace '\r\n',"`n") -cne ($ctx.rules -replace '\r\n',"`n")) { throw 'BRIDGE_EMBEDDED_PRIORITY_CONFLICT' }
        $body=$body.Substring(0,$m.Index).TrimEnd()
    }
    if ($body -match 'PROJECT / THESIS ALIGNMENT GUARD') { throw 'BRIDGE_LEGACY_PRIORITY_BLOCK: remove embedded historical guard; canonical rules are appended by the publisher.' }
    $body=[regex]::Replace($body,'(?m)^\s*\[BRIDGE_HANDOFF_ID=HND-[A-Za-z0-9_-]+\]\s*\r?\n?','',1)
    $body=[regex]::Replace($body,'(?mi)^BRIDGE_(?:RULES|POLICY)_SHA256:\s*[A-Fa-f0-9]{64}\s*\r?\n?','')
    $text="[BRIDGE_HANDOFF_ID=$HandoffId]`r`n$($body.Trim())`r`n`r`nBRIDGE_RULES_SHA256: $($ctx.rules_sha256)`r`nBRIDGE_POLICY_SHA256: $($ctx.policy_sha256)`r`n$start`r`n$($ctx.rules)`r`n$end"
    [pscustomobject]@{text=$text;handoff_id=$HandoffId;task_id=$req.task_id;protocol=$protocol;context=$ctx}
}
function Read-BridgeValidatedReply {
    param([string]$Raw,$Packet,[DateTimeOffset]$PublishedAt)
    try { $outer=$Raw | ConvertFrom-Json -ErrorAction Stop } catch { throw 'BRIDGE_RESPONSE_INVALID_TRANSPORT_JSON' }
    if ($outer.bridge_handoff_id -cne $Packet.handoff_id) { throw 'BRIDGE_RESPONSE_CORRELATION_MISMATCH' }
    if ($outer.status -cne 'OK') { throw 'BRIDGE_RESPONSE_STATUS_NOT_OK' }
    if ([string]::IsNullOrWhiteSpace([string]$outer.response) -or $outer.response_chars -ne ([string]$outer.response).Length) { throw 'BRIDGE_RESPONSE_LENGTH_MISMATCH' }
    $copied=[DateTimeOffset]::MinValue
    if (-not [DateTimeOffset]::TryParse([string]$outer.copied_at,[ref]$copied) -or $copied -lt $PublishedAt.AddSeconds(-2) -or $copied -gt [DateTimeOffset]::UtcNow.AddMinutes(2)) { throw 'BRIDGE_RESPONSE_FRESHNESS_INVALID' }
    $match=[regex]::Match(([string]$outer.response).Trim(),'(?s)^(?:```json\s*(\{.*\})\s*```|(?:(?i:json)\s*(?:Copy code\s*)?)?(\{.*\}))$')
    if (-not $match.Success) { throw 'BRIDGE_RESPONSE_JSON_ONLY_REQUIRED' }
    # Browser innerText removes markdown fences and may retain the json/Copy code label.
    $innerText=if($match.Groups[1].Success){$match.Groups[1].Value}else{$match.Groups[2].Value}
    try { $reply=$innerText | ConvertFrom-Json -ErrorAction Stop } catch { throw 'BRIDGE_RESPONSE_INNER_JSON_INVALID' }
    if ($reply.correlation_id -cne $Packet.handoff_id -or $reply.protocol -cne $Packet.protocol -or $reply.task_id -cne $Packet.task_id) { throw 'BRIDGE_RESPONSE_INNER_IDENTITY_MISMATCH' }
    $replyGoalId = if ($reply.goal_id) { [string]$reply.goal_id } else { [string]$reply.research_goal_id }
    if ($reply.canonical_rules_sha256 -ine $Packet.context.rules_sha256 -or $replyGoalId -cne $Packet.context.policy.goal_id) { throw 'BRIDGE_RESPONSE_POLICY_MISMATCH' }
    $replyDecision = if ($reply.decision) { [string]$reply.decision } else { [string]$reply.review_decision }
    if ($Packet.protocol -ceq 'INDEPENDENT_STRUCTURED_REVIEW_V1' -and $replyDecision -cnotin @('APPROVE','REJECT','INSUFFICIENT_EVIDENCE')) { throw 'BRIDGE_RESPONSE_INVALID_DECISION' }
    if ($Packet.protocol -ceq 'CHATGPT_SUPERVISOR_V1' -and $reply.action -cnotin @('DIAGNOSE','CONTINUE','WAIT','STOP')) { throw 'BRIDGE_RESPONSE_INVALID_ACTION' }
    if ($reply.master_goal_status -cnotin @('OPEN','COMPLETE')) { throw 'BRIDGE_RESPONSE_MASTER_STATUS_REQUIRED' }
    if ($reply.master_goal_status -ceq 'OPEN') {
        $nextContract = if ($reply.next_operation) { $reply.next_operation } elseif ($reply.next_instruction_to_antigravity -and $reply.next_instruction_to_antigravity.research_contract) { $reply.next_instruction_to_antigravity.research_contract } else { $null }
        $contractIdentity = if ($nextContract) { "$($nextContract.task_id) $($nextContract.title)" } else { "" }
        Assert-BridgeResearchContract -Contract $nextContract -Policy $Packet.context.policy -TaskIdentity $contractIdentity
        if ([string]::IsNullOrWhiteSpace([string]$reply.next_instruction_to_antigravity)) { throw 'BRIDGE_RESPONSE_NEXT_INSTRUCTION_REQUIRED' }
    } elseif (-not $reply.master_goal_acceptance_evidence -or @($reply.master_goal_acceptance_evidence).Count -lt 4) {
        throw 'BRIDGE_MASTER_COMPLETION_EVIDENCE_REQUIRED: independent four-case acceptance is mandatory.'
    }
    # Return inner JSON for downstream authenticated dispatcher; never grant execution here.
    $innerText
}
