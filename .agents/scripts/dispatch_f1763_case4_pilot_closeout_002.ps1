# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1763_case4_pilot_closeout_002.ps1
# Dispatches Task F1763 Case 4 Reconciled Pilot Results & Closeout Packet
# (HND-F1763-CASE4-PILOT-CLOSEOUT-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1763-CASE4-COMMON-FRAMEWORK-PILOT-EXECUTION"
$handoffId = "HND-F1763-CASE4-PILOT-CLOSEOUT-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1763-CASE4-PILOT-CLOSEOUT-002_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1763_CASE4_PILOT_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$auditPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\236_f1763_case4_pilot\f1763_case4_spatial_audit.json"
if (-not (Test-Path $auditPath)) {
    throw "Spatial audit file not found at: $auditPath"
}
$auditContent = Get-Content -Path $auditPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1763-CASE4-PILOT-CLOSEOUT-002
PREDECESSOR_CORRELATION_ID: HND-F1763-CASE4-PILOT-CLOSEOUT-001 (Reviewer directed reconciling Gate Matrix failures G1/G5, Ligament 1 midpoint deficiency, commit provenance, and GitHub URLs)
TASK_ID: F1763-CASE4-COMMON-FRAMEWORK-PILOT-EXECUTION
TITLE: Task F1763 Reconciled Case 4 Common-Framework Pilot Results & Closeout Packet

========================================================================================================
1. EVIDENCE PAYLOAD & RESOLUTION OF REVIEWER FINDINGS (HND-F1763-CASE4-PILOT-CLOSEOUT-002)
========================================================================================================
$payloadContent

========================================================================================================
2. SPATIAL RESOLUTION & MESH QUALITY AUDIT DATA (f1763_case4_spatial_audit.json)
========================================================================================================
$auditContent

========================================================================================================
3. FULL SCIENTIFIC REPORT (docs/validation/F1763_CASE4_PILOT_EXECUTION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1763 RECONCILED CLOSEOUT PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1763-CASE4-PILOT-CLOSEOUT-001"
Write-Host "Commit SHA: 12223505 (pushed to origin/main)"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1763 RECONCILED BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
