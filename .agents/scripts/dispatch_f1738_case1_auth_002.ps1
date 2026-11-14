# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1738_case1_auth_002.ps1
# Dispatches Task F1738 Case 1 Ligament Adaptive-Remeshing Execution Authorization Request (Round 2)
# (HND-F1738-CASE1-AUTH-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1738-CASE1-LIGAMENT-ADAPTIVE-REMESHING-QUALIFICATION"
$handoffId = "HND-F1738-CASE1-AUTH-002"

$proposalPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1738_CASE1_LIGAMENT_QUALIFICATION_PROPOSAL_R2.md"
if (-not (Test-Path $proposalPath)) {
    throw "Proposal file not found at: $proposalPath"
}
$proposalContent = Get-Content -Path $proposalPath -Raw -Encoding UTF8

$scientificReport = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: HND-F1738-CASE1-AUTH-002
PREDECESSOR_CORRELATION_ID: HND-F1738-CASE1-AUTH-001 (INSUFFICIENT_EVIDENCE; Directed point-by-point resolution of Findings F1738-R01 to F1738-R08)
TASK_ID: F1738-CASE1-LIGAMENT-ADAPTIVE-REMESHING-QUALIFICATION
TITLE: Task F1738 Case 1 Mode-I Ligament Adaptive-Remeshing Execution Authorization Request (Round 2)

========================================================================================================================
FULL ROUND 2 QUALIFICATION PROPOSAL (ADDRESSING FINDINGS F1738-R01 THROUGH F1738-R08)
========================================================================================================================

$proposalContent

========================================================================================================================
CONTROLLED EXECUTION ROUTE SPECIFICATION (FINDING F1738-R06 COMPLIANCE)
========================================================================================================================
The execution of the single bounded HPC job will strictly use the controlled PowerShell entrypoint:
`powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hpc/Submit-F1738-Case1-Ligament-Remesh.ps1`
Direct or bare `qsub` is completely eliminated.
Accounting:
- Authorized PBS allowance requested: EXACTLY 1 (max_new_pbs_submissions = 1)
- Cumulative historical submissions preserved: 13
- After submission, cumulative count will be 14.
- Zero forward phase-field fracture simulations.
- Frozen UEL f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6) bitwise preserved.
- Automatic retries strictly disabled.
"@

Write-Output "=== DISPATCHING TASK F1738 ROUND 2 EXECUTION AUTHORIZATION REQUEST TO CHATGPT (HND-F1738-CASE1-AUTH-002) ==="
$response = Invoke-ChatGPTBridge -PromptText $scientificReport -HandoffId $handoffId
Write-Output "=== CHATGPT RESPONSE RECEIVED ==="
Write-Output $response

$responseDir = Join-Path $PSScriptRoot "..\bridge_history"
if (-not (Test-Path $responseDir)) { New-Item -ItemType Directory -Path $responseDir -Force | Out-Null }
$responseFile = Join-Path $responseDir "response_${handoffId}.md"
Set-Content -Path $responseFile -Value $response -Encoding UTF8
Write-Output "Saved review response to: $responseFile"
