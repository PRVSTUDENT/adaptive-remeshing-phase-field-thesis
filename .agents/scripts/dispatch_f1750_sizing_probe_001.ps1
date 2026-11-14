# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1750_sizing_probe_001.ps1
# Dispatches Task F1750 Local Native Damage Sizing Probe Report Packet
# (HND-F1750-SIZING-PROBE-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1750-LOCAL-NATIVE-DAMAGE-SIZING-PROBE"
$handoffId = "HND-F1750-SIZING-PROBE-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1750-SIZING-PROBE-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1750_LOCAL_NATIVE_DAMAGE_SIZING_PROBE_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$summaryPath = Join-Path $PSScriptRoot "..\..\results\validation\f1750_local_sizing_probe_summary.json"
if (-not (Test-Path $summaryPath)) {
    throw "Summary JSON not found at: $summaryPath"
}
$summaryContent = Get-Content -Path $summaryPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1750-SIZING-PROBE-001
PREDECESSOR_CORRELATION_ID: HND-F1749-TIME-CAUSAL-002 (APPROVE; directed bounded zero-PBS Task F1750 local native Abaqus damage-derived sizing probe on Case 3 coarse base mesh)
TASK_ID: F1750-LOCAL-NATIVE-DAMAGE-SIZING-PROBE
TITLE: Task F1750 Local Native Abaqus Damage-Derived Sizing Probe on Case 3 Coarse Mesh Report Packet

========================================================================================================================
1. REVIEW PAYLOAD AND DIRECTIVE FULFILLMENT SUMMARY
========================================================================================================================
$payloadContent

========================================================================================================================
2. COMPLETE VALIDATION REPORT (docs/validation/F1750_LOCAL_NATIVE_DAMAGE_SIZING_PROBE_REPORT.md)
========================================================================================================================
$reportContent

========================================================================================================================
3. SUMMARY JSON DATASET (results/validation/f1750_local_sizing_probe_summary.json)
========================================================================================================================
$summaryContent
"@

Write-Output "=== DISPATCHING TASK F1750 SIZING PROBE REVIEW TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "response_${handoffId}.md"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Saved review response to: $responseFile"
