# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1767_offline_qual_closeout_002.ps1
# Dispatches Task F1767 Source Synchronization & Closeout Payload
# (HND-F1767-OFFLINE-QUAL-CLOSEOUT-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1767-UNIFIED-METHOD-A-OFFLINE-QUALIFICATION-AND-RECONCILIATION"
$handoffId = "HND-F1767-OFFLINE-QUAL-CLOSEOUT-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1767-OFFLINE-QUAL-CLOSEOUT-002_payload.md"
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
CORRELATION_ID: HND-F1767-OFFLINE-QUAL-CLOSEOUT-002
PREDECESSOR_CORRELATION_ID: HND-F1767-OFFLINE-QUAL-AUTH-001 (Reviewer directed source synchronization to GitHub origin/main, verified blob hashes, and Method A.2 source documentation)
TASK_ID: F1767-UNIFIED-METHOD-A-OFFLINE-QUALIFICATION-AND-RECONCILIATION
TITLE: Task F1767 Source Synchronization & Closeout Report (Committed Commit SHA: 9ef2db67a9eed45c2dad5d2c95b395f76897de81)

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1767-OFFLINE-QUAL-CLOSEOUT-002)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1767_UNIFIED_METHOD_A_OFFLINE_QUALIFICATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1767 SOURCE SYNC CLOSEOUT ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1767-OFFLINE-QUAL-AUTH-001"
Write-Host "Committed HEAD: 9ef2db67a9eed45c2dad5d2c95b395f76897de81"
Write-Host "Scope: ZERO-PBS SOURCE SYNCHRONIZATION CLOSEOUT"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1767 CLOSEOUT BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
