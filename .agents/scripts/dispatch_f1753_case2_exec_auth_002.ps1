# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1753_case2_exec_auth_002.ps1
# Dispatches Task F1753 Case 2 Method A Continuation Production Simulation Execution Authorization Packet (Round 2)
# (HND-F1753-CASE2-EXEC-AUTH-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION"
$handoffId = "HND-F1753-CASE2-EXEC-AUTH-002"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1753-CASE2-EXEC-AUTH-002_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$receiptPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1753_EXECUTION_INTEGRATION_QUALIFICATION_RECEIPT.md"
if (-not (Test-Path $receiptPath)) {
    throw "Receipt file not found at: $receiptPath"
}
$receiptContent = Get-Content -Path $receiptPath -Raw -Encoding UTF8

$ipReceiptPath = Join-Path $PSScriptRoot "..\..\results\validation\f1753_case2_temporal_ip_extraction_receipt.json"
if (-not (Test-Path $ipReceiptPath)) {
    throw "IP Receipt JSON not found at: $ipReceiptPath"
}
$ipReceiptContent = Get-Content -Path $ipReceiptPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1753-CASE2-EXEC-AUTH-002
PREDECESSOR_CORRELATION_ID: HND-F1753-CASE2-EXEC-AUTH-001 (SCIENTIFIC_DESIGN: APPROVE; PRODUCTION_EXECUTION: PENDING_FINAL_INTEGRATION_QUALIFICATION; directed all-IP temporal extraction audit on authentic F1735 ODB and simulated PBS script/monitor integration test with threshold reconciliation)
TASK_ID: F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION
TITLE: Task F1753 Case 2 Method A Controlled Continuation Production Simulation Execution Authorization Packet (Round 2)

========================================================================================================================
1. EXECUTION AUTHORIZATION ROUND 2 PAYLOAD (HND-F1753-CASE2-EXEC-AUTH-002)
========================================================================================================================
$payloadContent

========================================================================================================================
2. DEFINITIVE EXECUTION-INTEGRATION QUALIFICATION RECEIPT (docs/validation/F1753_EXECUTION_INTEGRATION_QUALIFICATION_RECEIPT.md)
========================================================================================================================
$receiptContent

========================================================================================================================
3. ALL-INTEGRATION-POINT TEMPORAL EXTRACTION RECEIPT (results/validation/f1753_case2_temporal_ip_extraction_receipt.json)
========================================================================================================================
$ipReceiptContent
"@

Write-Output "=== DISPATCHING TASK F1753 CASE 2 EXECUTION AUTHORIZATION ROUND 2 TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "$($handoffId)_chatgpt_response.txt"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Response saved to: $responseFile"
