# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1767_offline_qual_auth_001.ps1
# Dispatches Task F1767 Unified Method A Offline Qualification Report
# (HND-F1767-OFFLINE-QUAL-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1767-UNIFIED-METHOD-A-OFFLINE-QUALIFICATION-AND-RECONCILIATION"
$handoffId = "HND-F1767-OFFLINE-QUAL-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1767-OFFLINE-QUAL-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1767_UNIFIED_METHOD_A_OFFLINE_QUALIFICATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1767-OFFLINE-QUAL-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1766-SUITE-PLAN-AUTH-001 (Reviewer requested resolution of findings F1766-R01 to R06 before batch authorization)
TASK_ID: F1767-UNIFIED-METHOD-A-OFFLINE-QUALIFICATION-AND-RECONCILIATION
TITLE: Task F1767 Unified Method A Offline Framework Qualification, Case 3 Reconciliation & Multi-State Architecture Report

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1767-OFFLINE-QUAL-AUTH-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1767_UNIFIED_METHOD_A_OFFLINE_QUALIFICATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1767 OFFLINE QUALIFICATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1766-SUITE-PLAN-AUTH-001"
Write-Host "Scope: ZERO-PBS OFFLINE FRAMEWORK & CONFIGURATION QUALIFICATION"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1767 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
