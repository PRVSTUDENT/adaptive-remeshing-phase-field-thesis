# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1772_case1_remesh_exec_001.ps1
# Dispatches Task F1772 Case 1 Method A Advancing Adaptive Remeshing Execution Authorization
# (HND-F1772-CASE1-REMESH-EXEC-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1772-CASE1-METHOD-A-ADVANCING-REMESHING-EXECUTION"
$handoffId = "HND-F1772-CASE1-REMESH-EXEC-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1772-CASE1-REMESH-EXEC-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1772_CASE1_REMESHING_EXECUTION_PLAN.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1772-CASE1-REMESH-EXEC-001
PREDECESSOR_CORRELATION_ID: HND-F1771-CASE1-REMESH-AUTH-001 (Reviewer approved specification and directed registration of distinct one-submission successor F1772)
TASK_ID: F1772-CASE1-METHOD-A-ADVANCING-REMESHING-EXECUTION
TITLE: Task F1772 Case 1 Method A Advancing Adaptive Remeshing Execution Plan & Gate Specification

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1772-CASE1-REMESH-EXEC-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC EXECUTION PLAN (docs/validation/F1772_CASE1_REMESHING_EXECUTION_PLAN.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1772 CASE 1 REMESHING EXECUTION AUTHORIZATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1771-CASE1-REMESH-AUTH-001"
Write-Host "Scope: BOUNDED ONE-PBS MESH GENERATION PILOT"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "Check-only mode: Assembled scientific report verified successfully." -ForegroundColor Green
    exit 0
}

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "================================================================================"
Write-Host "TASK F1772 BRIDGE DISPATCH COMPLETE"
Write-Host "================================================================================"
