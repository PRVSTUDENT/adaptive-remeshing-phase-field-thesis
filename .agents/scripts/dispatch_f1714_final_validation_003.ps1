# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1714_final_validation_003.ps1
# Dispatches Task F1714 Terminal Status, Forensic Hypothesis Verification,
# and Telemetry Staging Report across the PAD bridge under HND-F1714-FINAL-VALIDATION-003.

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1714-FIVE-HOLE-GENERALIZATION-BENCHMARK"
$handoffId = "HND-F1714-FINAL-VALIDATION-003"

$reportPath = "$PSScriptRoot\..\..\docs\validation\F1714_TERMINAL_STATUS_AND_EVIDENCE_REPORT.md"
$scientificReport = Get-Content -Path $reportPath -Raw -Encoding utf8

$promptText = @"
PROTOCOL: INDEPENDENT_STRUCTURED_REVIEW_V1
CORRELATION_ID: $handoffId
TASK_ID: $taskId
TITLE: Task F1714 Terminal Status, Forensic Hypothesis Verification, and Telemetry Staging Report ($handoffId)

$scientificReport

========================================================================================================================
REQUEST FOR INDEPENDENT SCIENTIFIC REVIEW (ROUND 3)
========================================================================================================================
In compliance with the Next Instruction of Review Round 2, the executor requests the independent reviewer to:
1. Review the empirical findings testing the reference-node reaction-force NaN hypothesis and unused-capacity buffer NaN hypothesis (including the discovery of the missing SAVE attribute in f42_amor_split_uel.for).
2. Review the verified bottom-boundary reaction force recovery formulation ($F_{tensile}(t) = -\sum_{j \in N_BOTTOM} RF_{2,j}(t)$) and volume-integrated element energy summation from ODB field variables SDV17 and SDV18.
3. Review the walltime margin model establishing +59 minutes of headroom to complete all 5,000 increments within the 8-hour PBS limit.
4. Review the staged post-processing pipeline (extract_f1714_five_hole_telemetry.py) configured to run immediately upon solver completion and .lck release.
5. Provide structured review feedback and confirm continuation of the read-only monitoring posture while Job 1422257.mmaster02 completes its forward execution.
"@

Write-Host "Dispatching Task F1714 Final Scientific Validation Round 3 Report ($handoffId)..." -ForegroundColor Cyan
$bridgeResult = Invoke-ChatGPTBridge -PromptText $promptText -HandoffId $handoffId

Write-Host "Bridge response received for $handoffId." -ForegroundColor Green
Write-Host "Response length: $($bridgeResult.Length) characters"
$bridgeResult | Out-File -FilePath "$PSScriptRoot\..\..\results\validation\f1714_final_validation_round3_review_response.json" -Encoding utf8
Write-Host "Saved response to results/validation/f1714_final_validation_round3_review_response.json"
