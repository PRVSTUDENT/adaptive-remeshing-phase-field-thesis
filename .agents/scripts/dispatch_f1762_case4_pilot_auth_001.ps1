# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1762_case4_pilot_auth_001.ps1
# Dispatches Task F1762 Case 4 Pilot Execution Specification Packet
# (HND-F1762-CASE4-PILOT-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1762-CASE4-COMMON-FRAMEWORK-PILOT-SPECIFICATION"
$handoffId = "HND-F1762-CASE4-PILOT-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1762-CASE4-PILOT-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1762_CASE4_PILOT_SPECIFICATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1762-CASE4-PILOT-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1761-RECONCILED-MANIFEST-001 (Reviewer directed resolving Abaqus outputFrequency frame selection, UEL config re-alignment, and canonical manifest before pilot authorization)
TASK_ID: F1762-CASE4-COMMON-FRAMEWORK-PILOT-SPECIFICATION
TITLE: Task F1762 Case 4 Common-Framework Adaptive Remeshing Pilot Specification & Pre-Execution Verification Report

========================================================================================================
1. EVIDENCE PAYLOAD & PILOT SPECIFICATION (HND-F1762-CASE4-PILOT-AUTH-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC REPORT (docs/validation/F1762_CASE4_PILOT_SPECIFICATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1762 CASE 4 PILOT PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1761-RECONCILED-MANIFEST-001"
Write-Host "Commit SHA: a45c5f20 (pushed to origin/main)"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1762 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
