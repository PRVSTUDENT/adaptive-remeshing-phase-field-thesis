# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1758_case1_preflight_001.ps1
# Dispatches Task F1758 Case 1 Mode-I Preflight Qualification Packet
# (HND-F1758-CASE1-PREFLIGHT-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1758-CASE1-FRACTURE-QUALIFICATION-PREFLIGHT"
$handoffId = "HND-F1758-CASE1-PREFLIGHT-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1758-CASE1-PREFLIGHT-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1758_CASE1_FRACTURE_PREFLIGHT_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1758-CASE1-PREFLIGHT-001
PREDECESSOR_CORRELATION_ID: USER-DECISION-F1757-OPTION-A (User explicitly authorized Option A: Rebalancing active research priority to Case 1 [Mode-I Single-Edge Notched Plate] and proceeding to full crack propagation to complete specimen separation under Task F1758)
TASK_ID: F1758-CASE1-FRACTURE-QUALIFICATION-PREFLIGHT
TITLE: Task F1758 Case 1 Mode-I Notched Plate Coupled Phase-Field Fracture Qualification & Production Preflight Report

========================================================================================================
1. EVIDENCE PAYLOAD & AUTHORIZATION REQUEST (HND-F1758-CASE1-PREFLIGHT-001)
========================================================================================================
$payloadContent

========================================================================================================
2. FULL SCIENTIFIC REPORT (docs/validation/F1758_CASE1_FRACTURE_PREFLIGHT_REPORT.md)
========================================================================================================
$reportContent
"@

Write-Host "================================================================================"
Write-Host "DISPATCHING TASK F1758 PREFLIGHT PACKET ($handoffId)"
Write-Host "Task ID: $taskId"
Write-Host "Correlation ID: $handoffId"
Write-Host "Predecessor ID: USER-DECISION-F1757-OPTION-A"
Write-Host "================================================================================"

$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId

Write-Host "Response received successfully across OpenClaw PAD bridge."
Write-Host "Response length: $($response.Length) characters."

$responsePath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1758-CASE1-PREFLIGHT-001_chatgpt_response.txt"
Set-Content -Path $responsePath -Value $response -Encoding UTF8
Write-Host "Saved response to: $responsePath"
