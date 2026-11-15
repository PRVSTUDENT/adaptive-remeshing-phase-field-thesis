# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1774_suite_regression_exec_002.ps1
# Dispatches Task F1774 Four-Benchmark Method A Execution Package Repair & Authorization Request
# (HND-F1774-SUITE-REGRESSION-EXEC-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION"
$handoffId = "HND-F1774-SUITE-REGRESSION-EXEC-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1774-SUITE-REGRESSION-EXEC-002_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1774_EXECUTION_PACKAGE_REPAIR_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1774-SUITE-REGRESSION-EXEC-002
PREDECESSOR_CORRELATION_ID: HND-F1774-SUITE-REGRESSION-EXEC-001 (Direct resolution of review findings F1774-R01 to R06)
TASK_ID: F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION
TITLE: Task F1774 Execution Package Safety & Scientific Repair Report
REPORTED_SOURCE_COMMIT: HEAD on PRVSTUDENT/adaptive-remeshing-phase-field-thesis

========================================================================================================
1. RECONCILED EVIDENCE PAYLOAD & RESOLUTION SUMMARY (HND-F1774-SUITE-REGRESSION-EXEC-002)
========================================================================================================
$payloadContent

========================================================================================================
2. EXECUTION PACKAGE REPAIR REPORT (docs/validation/F1774_EXECUTION_PACKAGE_REPAIR_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1774 EXECUTION PACKAGE REPAIR AUTHORIZATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1774-SUITE-REGRESSION-EXEC-001"
Write-Host "Scope: FOUR-BENCHMARK EXECUTION PACKAGE REPAIR REVIEW & AUTHORIZATION"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Host "Bridge response received for $handoffId" -ForegroundColor Green
