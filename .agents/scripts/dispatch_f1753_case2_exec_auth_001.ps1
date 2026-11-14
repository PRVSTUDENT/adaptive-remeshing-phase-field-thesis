# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1753_case2_exec_auth_001.ps1
# Dispatches Task F1753 Case 2 Method A Continuation Production Simulation Execution Authorization Packet
# (HND-F1753-CASE2-EXEC-AUTH-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION"
$handoffId = "HND-F1753-CASE2-EXEC-AUTH-001"

$payloadPath = Join-Path $PSScriptRoot "..\bridge_history\HND-F1753-CASE2-EXEC-AUTH-001_payload.md"
if (-not (Test-Path $payloadPath)) {
    throw "Payload file not found at: $payloadPath"
}
$payloadContent = Get-Content -Path $payloadPath -Raw -Encoding UTF8

$planPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1753_CASE2_CONTINUATION_EXECUTION_PLAN.md"
if (-not (Test-Path $planPath)) {
    throw "Plan file not found at: $planPath"
}
$planContent = Get-Content -Path $planPath -Raw -Encoding UTF8

$manifestPath = Join-Path $PSScriptRoot "..\..\results\validation\f1752_case2_continuation_manifest.json"
if (-not (Test-Path $manifestPath)) {
    throw "Manifest JSON not found at: $manifestPath"
}
$manifestContent = Get-Content -Path $manifestPath -Raw -Encoding UTF8

$coveragePath = Join-Path $PSScriptRoot "..\..\results\validation\f1752_output_coverage_receipt.json"
if (-not (Test-Path $coveragePath)) {
    throw "Coverage JSON not found at: $coveragePath"
}
$coverageContent = Get-Content -Path $coveragePath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1753-CASE2-EXEC-AUTH-001
PREDECESSOR_CORRELATION_ID: HND-F1752-CASE2-PREFLIGHT-002 (TECHNICAL_PREPARATION_SUBSTANTIALLY_COMPLETE; directed offline testing of cutback monitor and verification of Layer 3 SDV output coverage, then closing F1752 and registering successor execution task F1753)
TASK_ID: F1753-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION
PREDECESSOR_TASK_ID: F1752-CASE2-CONTROL-ONLY-CONTINUATION-EXECUTION-PREFLIGHT
TITLE: Task F1753 Case 2 Method A Controlled Continuation Production Simulation Execution Authorization Packet (1 Bounded PBS Job)

========================================================================================================================
1. EXECUTION AUTHORIZATION PAYLOAD AND READINESS COMPLETION SUMMARY
========================================================================================================================
$payloadContent

========================================================================================================================
2. DEFINITIVE CONTINUATION EXECUTION PLAN (docs/validation/F1753_CASE2_CONTINUATION_EXECUTION_PLAN.md)
========================================================================================================================
$planContent

========================================================================================================================
3. FIELD OUTPUT COVERAGE AND IRREVERSIBILITY AUDIT RECEIPT (results/validation/f1752_output_coverage_receipt.json)
========================================================================================================================
$coverageContent

========================================================================================================================
4. STAGED PRODUCTION MANIFEST AND DATACHECK RECEIPT (results/validation/f1752_case2_continuation_manifest.json)
========================================================================================================================
$manifestContent
"@

Write-Output "=== DISPATCHING TASK F1753 CASE 2 EXECUTION AUTHORIZATION TO CHATGPT ($handoffId) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "$($handoffId)_chatgpt_response.txt"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Response saved to: $responseFile"
