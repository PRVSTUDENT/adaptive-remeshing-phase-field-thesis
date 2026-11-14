# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1752_case2_preflight_002.ps1
# Dispatches Task F1752 Case 2 Method A Continuation Preflight Re-Review Packet
# (HND-F1752-CASE2-PREFLIGHT-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT"
$handoffId = "HND-F1752-CASE2-PREFLIGHT-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1752-CASE2-PREFLIGHT-002_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1752_CASE2_CONTINUATION_PREFLIGHT_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$manifestPath = Join-Path $PSScriptRoot "..\..\results\validation\f1752_case2_continuation_manifest.json"
if (-not (Test-Path $manifestPath)) {
    throw "Manifest JSON not found at: $manifestPath"
}
$manifestContent = Get-Content -Path $manifestPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1752-CASE2-PREFLIGHT-002
PREDECESSOR_CORRELATION_ID: HND-F1752-CASE2-PREFLIGHT-001 (INSUFFICIENT_EVIDENCE; directed zero-PBS evidence reconciliation of initial-increment sign diff, COMMON-block restart audit, runtime stop enforcement, pointwise irreversibility, parity hypotheses, and node/force provenance)
TASK_ID: F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT
TITLE: Task F1752 Case 2 Method A Controlled Continuation Execution Preflight & Evidence Reconciliation Re-Review Packet

========================================================================================================================
1. RE-REVIEW PAYLOAD AND FINDINGS F1752-R01 TO R06 RESOLUTION SUMMARY
========================================================================================================================
$payloadContent

========================================================================================================================
2. DEFINITIVE PREFLIGHT & EVIDENCE RECONCILIATION REPORT (docs/validation/F1752_CASE2_CONTINUATION_PREFLIGHT_REPORT.md)
========================================================================================================================
$reportContent

========================================================================================================================
3. RECONCILED EXECUTION MANIFEST DATASET (results/validation/f1752_case2_continuation_manifest.json)
========================================================================================================================
$manifestContent
"@

Write-Output "=== DISPATCHING TASK F1752 CASE 2 PREFLIGHT RE-REVIEW TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "$($handoffId)_chatgpt_response.txt"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Response saved to: $responseFile"
