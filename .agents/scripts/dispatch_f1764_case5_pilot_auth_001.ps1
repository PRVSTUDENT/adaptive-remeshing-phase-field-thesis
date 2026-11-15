# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1764_case5_pilot_auth_001.ps1
# Dispatches Task F1764 Case 5 Pilot Specification & Authorization Request
# (HND-F1764-CASE5-PILOT-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1764-CASE5-COMMON-FRAMEWORK-PILOT-SPECIFICATION"
$handoffId = "HND-F1764-CASE5-PILOT-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1764-CASE5-PILOT-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1764_CASE5_PILOT_SPECIFICATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1764-CASE5-PILOT-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1763-CASE4-PILOT-CLOSEOUT-002 (Reviewer approved F1763 closeout with partial scientific qualification and authorized ONE bounded zero-PBS Case 5 specification task)
TASK_ID: F1764-CASE5-COMMON-FRAMEWORK-PILOT-SPECIFICATION
TITLE: Task F1764 Case 5 Common-Framework Single-Pass Adaptive Remeshing Pilot Specification & Pre-Execution Verification Report

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1764-CASE5-PILOT-AUTH-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1764_CASE5_PILOT_SPECIFICATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1764 CASE 5 PILOT SPECIFICATION PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1763-CASE4-PILOT-CLOSEOUT-002"
Write-Host "Scope: ZERO-PBS SPECIFICATION"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1764 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
