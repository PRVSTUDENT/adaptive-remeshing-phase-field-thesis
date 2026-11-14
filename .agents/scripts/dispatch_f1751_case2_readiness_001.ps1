# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1751_case2_readiness_001.ps1
# Dispatches Task F1751 Case 2 Method A Damage Resolution and Continuation Readiness Report Packet
# (HND-F1751-CASE2-READINESS-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1751-CASE2-METHOD-A-DAMAGE-RESOLUTION-AND-CONTINUATION-READINESS"
$handoffId = "HND-F1751-CASE2-READINESS-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1751-CASE2-READINESS-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1751_CASE2_METHOD_A_READINESS_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$summaryPath = Join-Path $PSScriptRoot "..\..\results\validation\f1751_case2_diagnosis_summary.json"
if (-not (Test-Path $summaryPath)) {
    throw "Summary JSON not found at: $summaryPath"
}
$summaryContent = Get-Content -Path $summaryPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1751-CASE2-READINESS-001
PREDECESSOR_CORRELATION_ID: HND-F1750-SIZING-PROBE-001 (APPROVE; directed bounded zero-PBS Task F1751 Case 2 Method A damage resolution and continuation readiness diagnosis)
TASK_ID: F1751-CASE2-METHOD-A-DAMAGE-RESOLUTION-AND-CONTINUATION-READINESS
TITLE: Task F1751 Case 2 Method A Damage Resolution and Forward Continuation Readiness Report Packet

========================================================================================================================
1. REVIEW PAYLOAD AND DIRECTIVE FULFILLMENT SUMMARY
========================================================================================================================
$payloadContent

========================================================================================================================
2. COMPLETE VALIDATION REPORT (docs/validation/F1751_CASE2_METHOD_A_READINESS_REPORT.md)
========================================================================================================================
$reportContent

========================================================================================================================
3. SUMMARY JSON DATASET (results/validation/f1751_case2_diagnosis_summary.json)
========================================================================================================================
$summaryContent
"@

Write-Output "=== DISPATCHING TASK F1751 CASE 2 READINESS REVIEW TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "response_${handoffId}.md"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Saved review response to: $responseFile"
