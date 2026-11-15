# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1768_case1_donor_auth_001.ps1
# Dispatches Task F1768 Case 1 Advancing Coupled Donor Preflight Qualification
# (HND-F1768-CASE1-DONOR-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1768-CASE1-ADVANCING-COUPLED-DONOR-PREPARATION"
$handoffId = "HND-F1768-CASE1-DONOR-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1768-CASE1-DONOR-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1768_CASE1_DONOR_PREPARATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1768-CASE1-DONOR-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1767-OFFLINE-QUAL-CLOSEOUT-002 (Reviewer approved F1767 closeout and directed Option B Case 1 advancing donor preflight)
TASK_ID: F1768-CASE1-ADVANCING-COUPLED-DONOR-PREPARATION
TITLE: Task F1768 Case 1 Advancing Coupled Donor Production Deck Preparation & Cluster Datacheck Qualification

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1768-CASE1-DONOR-AUTH-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1768_CASE1_DONOR_PREPARATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1768 CASE 1 DONOR PREFLIGHT ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1767-OFFLINE-QUAL-CLOSEOUT-002"
Write-Host "Scope: ZERO-PBS PREFLIGHT QUALIFICATION & ONE-JOB DONOR EXECUTION REQUEST"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1768 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
