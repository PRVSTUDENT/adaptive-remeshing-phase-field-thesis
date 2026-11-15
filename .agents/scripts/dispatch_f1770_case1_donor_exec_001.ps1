# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1770_case1_donor_exec_001.ps1
# Dispatches Task F1770 Case 1 Advancing Coupled Donor Replacement Execution Authorization
# (HND-F1770-CASE1-DONOR-EXEC-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION"
$handoffId = "HND-F1770-CASE1-DONOR-EXEC-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1770-CASE1-DONOR-EXEC-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1770_CASE1_DONOR_REPLACEMENT_PLAN.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1770-CASE1-DONOR-EXEC-001
PREDECESSOR_CORRELATION_ID: HND-F1769-CASE1-DONOR-R2-AUTH-001 (Reviewer approved R2 technical repair and directed registration of distinct replacement task F1770)
TASK_ID: F1770-CASE1-ADVANCING-COUPLED-DONOR-REPLACEMENT-EXECUTION
TITLE: Task F1770 Case 1 Advancing Coupled Donor Replacement Execution Plan & Gate Specification

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1770-CASE1-DONOR-EXEC-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1770_CASE1_DONOR_REPLACEMENT_PLAN.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1770 CASE 1 DONOR REPLACEMENT AUTHORIZATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1769-CASE1-DONOR-R2-AUTH-001"
Write-Host "Scope: BOUNDED ONE-PBS DONOR REPLACEMENT SOLVE & DISTINCT TASK REGISTRATION"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1770 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
