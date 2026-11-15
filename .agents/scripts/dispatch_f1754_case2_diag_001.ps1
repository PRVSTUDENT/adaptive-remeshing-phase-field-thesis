# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1754_case2_diag_001.ps1
# Dispatches Task F1754 Case 2 Method A Discrete Phase-Field Failure Diagnosis Packet
# (HND-F1754-CASE2-DIAG-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1754-CASE2-DISCRETE-PHASE-FIELD-FAILURE-DIAGNOSIS"
$handoffId = "HND-F1754-CASE2-DIAG-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1754-CASE2-DIAG-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$diagReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1754_CASE2_DISCRETE_PHASE_FIELD_FAILURE_DIAGNOSIS_REPORT.md"
if (-not (Test-Path $diagReportPath)) {
    throw "Diagnostic report file not found at: $diagReportPath"
}
$diagReportContent = Get-Content -Path $diagReportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1754-CASE2-DIAG-001
PREDECESSOR_CORRELATION_ID: HND-F1753-CASE2-CLOSEOUT-001 (DECISION: APPROVE, PRODUCTION_EXECUTION_CLOSEOUT_AND_SUCCESSOR_DIRECTION; directed zero-PBS offline diagnosis of UEL residual/tangent formulation, COMMON-block state updates, divergence telemetry near Node 8056, and discriminative hypotheses evaluation)
TASK_ID: F1754-CASE2-DISCRETE-PHASE-FIELD-FAILURE-DIAGNOSIS
TITLE: Task F1754 Case 2 Method A Discrete Phase-Field Failure Diagnosis Report & Hypothesis Ranking

========================================================================================================================
1. DIAGNOSTIC PAYLOAD & HYPOTHESES RANKING (HND-F1754-CASE2-DIAG-001)
========================================================================================================================
$payloadContent

========================================================================================================================
2. FULL DIAGNOSTIC REPORT (docs/validation/F1754_CASE2_DISCRETE_PHASE_FIELD_FAILURE_DIAGNOSIS_REPORT.md)
========================================================================================================================
$diagReportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1754 DIAGNOSTIC PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1753-CASE2-CLOSEOUT-001"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "Response received successfully across OpenClaw PAD bridge."
Write-Host "Response length: $($response.Length) characters."

$responsePath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1754-CASE2-DIAG-001_chatgpt_response.txt"
Set-Content -Path $responsePath -Value $response -Encoding UTF8
Write-Host "Saved response to: $responsePath"
