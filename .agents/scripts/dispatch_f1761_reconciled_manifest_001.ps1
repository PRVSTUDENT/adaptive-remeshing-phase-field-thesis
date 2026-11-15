# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1761_reconciled_manifest_001.ps1
# Dispatches Task F1761 Reconciled Five-Case Unified Execution Manifest Packet
# (HND-F1761-RECONCILED-MANIFEST-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1761-UNIFIED-METHOD-A-RECONCILED-EXECUTION-MANIFEST"
$handoffId = "HND-F1761-RECONCILED-MANIFEST-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1761-RECONCILED-MANIFEST-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1761_UNIFIED_METHOD_A_RECONCILED_EXECUTION_MANIFEST.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1761-RECONCILED-MANIFEST-001
PREDECESSOR_CORRELATION_ID: HND-F1760-PROVENANCE-001 (Reviewer accepted key provenance findings with INSUFFICIENT_EVIDENCE, directing manifest reconciliation and bounded pilot proposal)
TASK_ID: F1761-UNIFIED-METHOD-A-RECONCILED-EXECUTION-MANIFEST
TITLE: Task F1761 Reconciled Five-Case Unified Method A Execution Manifest & Pre-Execution Qualification Report

========================================================================================================
1. EVIDENCE PAYLOAD & MANIFEST RESOLUTION (HND-F1761-RECONCILED-MANIFEST-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL RECONCILED EXECUTION MANIFEST REPORT (docs/validation/F1761_UNIFIED_METHOD_A_RECONCILED_EXECUTION_MANIFEST.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1761 RECONCILED MANIFEST PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1760-PROVENANCE-001"
Write-Host "Commit SHA: 3a1f1f6c (pushed to origin/main)"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1761 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
