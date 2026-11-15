# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1769_case1_donor_exec_001.ps1
# Dispatches Task F1769 Case 1 Advancing Coupled Donor Execution Plan & Gate Specification
# (HND-F1769-CASE1-DONOR-EXEC-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1769-CASE1-ADVANCING-COUPLED-DONOR-EXECUTION"
$handoffId = "HND-F1769-CASE1-DONOR-EXEC-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1769-CASE1-DONOR-EXEC-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1769_CASE1_DONOR_EXECUTION_PLAN.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1769-CASE1-DONOR-EXEC-001
PREDECESSOR_CORRELATION_ID: HND-F1768-CASE1-DONOR-AUTH-001 (Reviewer approved F1768 preflight and directed bounded 1-PBS successor F1769)
TASK_ID: F1769-CASE1-ADVANCING-COUPLED-DONOR-EXECUTION
TITLE: Task F1769 Case 1 Advancing Coupled Donor Execution Plan, Boundary Condition Audit & Acceptance Gate Specification

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1769-CASE1-DONOR-EXEC-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1769_CASE1_DONOR_EXECUTION_PLAN.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1769 CASE 1 DONOR EXECUTION AUTHORIZATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1768-CASE1-DONOR-AUTH-001"
Write-Host "Scope: BOUNDED ONE-PBS DONOR EXECUTION REQUEST & G1-G7 ACCEPTANCE GATES"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1769 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
