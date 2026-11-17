# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1836_f1835_report_correction_001.ps1
# Dispatches Task F1836: Correct the F1835 Report and Complete the Missing Diagnosis Deliverables
# (HND-F1836-F1835-REPORT-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1836-F1835-REPORT-CORRECTION"
$handoffId = "HND-F1836-F1835-REPORT-CORRECTION-001"
$predecessorHandoffId = "HND-F1835-ENVELOPE-CAUSALITY-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1835_REVISED_NATIVE_REFERENCE_AND_ENVELOPE_CAUSALITY_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = (git rev-parse HEAD).Trim()

# Read figure SHA256 hashes dynamically
$figDir = Join-Path $PSScriptRoot "..\..\results\figures"
function Get-Sha256($fpath) {
    if (Test-Path $fpath) {
        return (Get-FileHash -Path $fpath -Algorithm SHA256).Hash.ToUpper()
    }
    return "PENDING"
}

$shaC1 = Get-Sha256 (Join-Path $figDir "fig_f1835_case_1_standalone_mesh.png")
$shaC2 = Get-Sha256 (Join-Path $figDir "fig_f1835_case_2_standalone_mesh.png")
$shaC3 = Get-Sha256 (Join-Path $figDir "fig_f1835_case_3_standalone_mesh.png")
$shaC5 = Get-Sha256 (Join-Path $figDir "fig_f1835_case_5_standalone_mesh.png")
$shaComp = Get-Sha256 (Join-Path $figDir "fig_f1835_four_benchmark_synthesis.png")

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1836: Correct the F1835 Report and Complete the Missing Diagnosis Deliverables",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Are the F1835 report defects (donor ODB SHA conflict, scale-invariance overstatement and JSON contradiction, missing per-element decomposition data, missing F1831 traceability, overstated local-denominator verdict, Section 4.4/4.5 error, task labeling mismatch) rigorously corrected in place without changing the verified numerical findings or introducing new defects?",
    "expected_numerical_result": "All defects corrected: donor ODB SHA reconciled to true local hash E2FE195B... with erroneous historical 4A1A78B6... identified as a transcription error; scale invariance reported as +0.47% max deviation for C>=1.0 with the verified=false flag explained and the C=0.001 failure stated; per-element decomposition data (driving state, MISESERI, local MISESAVG, ratio, element volume) committed in f1836_per_element_envelope_decomposition.json for Cases 2 and 3 and used to evaluate the local denominator contribution (61.68% in Case 2, 53.39% in Case 3); F1831's precomputed numbers traced to hardcoded literals in runner and classified UNVERIFIED; local denominator verdict corrected to what Step 4 measured; five-hole corrected to Section 4.5; task labeling consistent; artifact table carries SHA-256 values; 0 new PBS jobs (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb",
      "donor_sha256": "E2FE195B93A6378849E134DD3FE17EC69FFD03CCA8D446496E6D30820E7958AE",
      "donor_step": "Step-2",
      "donor_frame_index": 178,
      "indicator_frame_range": "[0, 178]",
      "held_out_later_solution": "Post-peak crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 0.7257,
      "maximum_indicator_time": 0.7257
    },
    "image_manifest": [
      {
        "case_id": "case_1",
        "relative_path": "results/figures/fig_f1835_case_1_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1835_case_1_standalone_mesh.png",
        "sha256": "$shaC1",
        "description": "Case 1 Standalone Mesh View under Scale-Invariant Envelope (F1835: 24,949 elements, 97.10% quads, Gate 06: 2.09x PASS)"
      },
      {
        "case_id": "case_2",
        "relative_path": "results/figures/fig_f1835_case_2_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1835_case_2_standalone_mesh.png",
        "sha256": "$shaC2",
        "description": "Case 2 Standalone Mesh View under Scale-Invariant Envelope (F1835: 120,088 elements, 97.49% quads, Gate 06: 1.28x FAIL, 92.3% unnecessary fine area)"
      },
      {
        "case_id": "case_3",
        "relative_path": "results/figures/fig_f1835_case_3_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1835_case_3_standalone_mesh.png",
        "sha256": "$shaC3",
        "description": "Case 3 Standalone Mesh View under Scale-Invariant Envelope (F1835: 481,766 elements, 97.45% quads, Gate 06: 1.04x FAIL, 85.0% unnecessary fine area)"
      },
      {
        "case_id": "case_5",
        "relative_path": "results/figures/fig_f1835_case_5_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1835_case_5_standalone_mesh.png",
        "sha256": "$shaC5",
        "description": "Case 5 Standalone Mesh View under Scale-Invariant Envelope (Table 6 Parity Preserved: 15,466 elements, 97.90% quads, Gate 06: 2.12x PASS)"
      },
      {
        "case_id": "composite",
        "relative_path": "results/figures/fig_f1835_four_benchmark_synthesis.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1835_four_benchmark_synthesis.png",
        "sha256": "$shaComp",
        "description": "4-Panel Publication Synthesis Composite under Scale-Invariant Envelope"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1836 completes all corrections and missing diagnosis deliverables for Task F1835: (1) Reconciled the donor ODB SHA conflict by directly hashing local PK_F1720_COARSE_COUPLED.odb (217,936,940 bytes) to E2FE195B93A6378849E134DD3FE17EC69FFD03CCA8D446496E6D30820E7958AE and explicitly identifying historical 4A1A78B6... as a transcription error; (2) Corrected scale-invariance reporting: stated max deviation across physical scales C in [1.0, 2.1e13] as +0.47% (13,501 vs 13,438 el), explained automated verified=false flag as a strict bitwise check across all scales including sub-physical C=0.001 (-25.4%), and preserved the core conclusion that scaling cannot explain the 10x explosion; (3) Delivered primary element-by-element decomposition dataset in results/validation/f1836_per_element_envelope_decomposition.json, demonstrating that depressed local denominators account for 61.68% of fine elements in Case 2 (1,075 / 1,743) and 53.39% in Case 3 (1,545 / 2,894); (4) Traced F1831 precomputed numbers to static dictionary literals in runner source and formally classified them UNVERIFIED; (5) Corrected local denominator verdict to reflect primary field measurements; (6) Corrected five-hole benchmark section number to Section 4.5; (7) Ensured consistent task labeling and added complete SHA-256 table. 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1835_REVISED_NATIVE_REFERENCE_AND_ENVELOPE_CAUSALITY_REPORT.md",
    "report_sha256": "$reportSha"
  }
}

---
$reportContent

---
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "CheckOnly mode: Assembling prompt text and validating schema..."
    $checkResult = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId -DryRun
    Write-Host "Validation successful. Prompt length: $($header.Length) characters."
    return
}

Write-Host "Dispatching Task F1836 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
