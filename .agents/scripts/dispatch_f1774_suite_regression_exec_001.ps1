# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1774_suite_regression_exec_001.ps1
# Dispatches Task F1774 Four-Benchmark Method A Regression Batch Execution Authorization Request
# (HND-F1774-SUITE-REGRESSION-EXEC-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION"
$handoffId = "HND-F1774-SUITE-REGRESSION-EXEC-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1774-SUITE-REGRESSION-EXEC-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1773_EXECUTION_READINESS_AND_DONOR_PREFLIGHT_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1774-SUITE-REGRESSION-EXEC-001
PREDECESSOR_CORRELATION_ID: HND-F1773-SUITE-REGRESSION-AUTH-002 (Direct resolution of review findings F1773-R08 to R14)
TASK_ID: F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION
TITLE: Task F1774 Four-Benchmark Method A Adaptive Remeshing Execution & Validation Synthesis
REPORTED_SOURCE_COMMIT: 90f7756fa on PRVSTUDENT/adaptive-remeshing-phase-field-thesis

========================================================================================================
1. RECONCILED EVIDENCE PAYLOAD & RESOLUTION SUMMARY (HND-F1774-SUITE-REGRESSION-EXEC-001)
========================================================================================================
$payloadContent

========================================================================================================
2. EXECUTION READINESS & PREFLIGHT REPORT (docs/validation/F1773_EXECUTION_READINESS_AND_DONOR_PREFLIGHT_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1774 FOUR-BENCHMARK REGRESSION BATCH EXECUTION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1773-SUITE-REGRESSION-AUTH-002"
Write-Host "Scope: FOUR-BENCHMARK 3-JOB BATCH EXECUTION AUTHORIZATION (CASES 2, 3, 5)"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Host "Bridge response received for $handoffId" -ForegroundColor Green
