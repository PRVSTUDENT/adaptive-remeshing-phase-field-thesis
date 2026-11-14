# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1749_time_causal_002.ps1
# Dispatches Task F1749 Source-Aligned Correction Re-Review Request Packet
# (HND-F1749-TIME-CAUSAL-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1749-TIME-CAUSAL-DAMAGE-INDICATOR-IMPLEMENTATION-AND-VALIDATION"
$handoffId = "HND-F1749-TIME-CAUSAL-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1749-TIME-CAUSAL-002_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1749_TIME_CAUSAL_DAMAGE_INDICATOR_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$summaryPath = Join-Path $PSScriptRoot "..\..\results\validation\f1749_time_causal_indicator_summary.json"
if (-not (Test-Path $summaryPath)) {
    throw "Summary JSON not found at: $summaryPath"
}
$summaryContent = Get-Content -Path $summaryPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1749-TIME-CAUSAL-002
PREDECESSOR_CORRELATION_ID: HND-F1749-TIME-CAUSAL-001 (INSUFFICIENT_EVIDENCE; directed source-aligned correction of Case 3 checkpoints, secondary corridor activation counts, global active element counts, primary resolution claims, Case 2 solver records, and native Abaqus interface mapping)
TASK_ID: F1749-TIME-CAUSAL-DAMAGE-INDICATOR-IMPLEMENTATION-AND-VALIDATION
TITLE: Task F1749 Source-Aligned Temporal and Sizing Correction Re-Review Packet

========================================================================================================================
1. RE-REVIEW PAYLOAD AND DIRECTIVE FULFILLMENT SUMMARY
========================================================================================================================
$payloadContent

========================================================================================================================
2. COMPLETE SOURCE-ALIGNED VALIDATION REPORT (docs/validation/F1749_TIME_CAUSAL_DAMAGE_INDICATOR_REPORT.md)
========================================================================================================================
$reportContent

========================================================================================================================
3. SOURCE-ALIGNED SUMMARY JSON DATASET (results/validation/f1749_time_causal_indicator_summary.json)
========================================================================================================================
$summaryContent
"@

Write-Output "=== DISPATCHING TASK F1749 SOURCE-ALIGNED RE-REVIEW TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "response_${handoffId}.md"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Saved review response to: $responseFile"
