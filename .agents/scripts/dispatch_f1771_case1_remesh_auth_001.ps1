# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1771_case1_remesh_auth_001.ps1
# Dispatches Task F1771 Case 1 Method A Advancing Adaptive Remeshing Specification & Pilot Authorization
# (HND-F1771-CASE1-REMESH-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1771-CASE1-METHOD-A-ADVANCING-REMESHING-SPECIFICATION"
$handoffId = "HND-F1771-CASE1-REMESH-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1771-CASE1-REMESH-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1771_CASE1_REMESHING_SPECIFICATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1771-CASE1-REMESH-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1770-CASE1-DONOR-EXEC-001 (Reviewer approved replacement solve; Job 1423604.mmaster02 completed Exit 0; advancing donor ODB verified)
TASK_ID: F1771-CASE1-METHOD-A-ADVANCING-REMESHING-SPECIFICATION
TITLE: Task F1771 Case 1 Method A Advancing Adaptive Remeshing Specification & Pilot Authorization Request

========================================================================================================
1. EVIDENCE PAYLOAD & SPECIFICATION SUMMARY (HND-F1771-CASE1-REMESH-AUTH-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC SPECIFICATION REPORT (docs/validation/F1771_CASE1_REMESHING_SPECIFICATION_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1771 CASE 1 REMESHING AUTHORIZATION ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: HND-F1770-CASE1-DONOR-EXEC-001"
Write-Host "Scope: ZERO-PBS SPECIFICATION & REQUEST FOR 1-PBS MESH GENERATION PILOT"
Write-Host "================================================================================"

if ($CheckOnly) {
    Write-Host "[CheckOnly] Payload and report paths verified. Ready for dispatch."
    exit 0
}

Invoke-ChatGPTBridge -HandoffId $handoffId -ScientificReport $scientificReport -TimeoutSeconds 2400
