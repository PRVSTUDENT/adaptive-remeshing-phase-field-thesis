# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1835_envelope_causality_auth_001.ps1
# Dispatches Task F1835 Native-Donor Reference and Envelope-Causality Diagnosis
# (HND-F1835-ENVELOPE-CAUSALITY-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1835-SCALE-INVARIANT-ENVELOPE"
$handoffId = "HND-F1835-ENVELOPE-CAUSALITY-001"
$predecessorHandoffId = "HND-F1834-EARLY-STATE-BLOWUP-GUARD-001"

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
  "title": "Task F1835: Native-Donor Reference and Envelope-Causality Diagnosis",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Determine whether excess refinement in the multi-state envelope comes from recovery mechanics, local normalization, temporal aggregation, or field scaling without assuming the answer.",
    "expected_numerical_result": "Step 1 audit established that Cases 1, 2, 3, 5 direct evolving donors are MISSING, while Case 4 PK_F1720_COARSE_COUPLED.odb is the unique authentic evolving direct donor in the repository (Step-1 13 frames, Step-2 179 frames). Step 2 untouched-native remeshing on Step-2 terminal frame 178 produced 13,438 elements (97.51% quads, positive Jacobians, max AR 2.624, 3.53x coarsening PASS Gate 06) with only 23.15% fine area (h <= l0), proving that native single-state remeshing does NOT over-refine. Step 3 recovery mechanics isolation verified authentic physical stress bounds (0.0057-3.0809 MPa) and scale-invariant relative error ratio eta_e = MISESERI/MISESAVG (mean 3.4126%). Step 4 envelope decomposition proved that 60% of the coarse domain has eta_e >= 4% in multi-state recovery donors (1,743/2,906 elements in Case 2; 2,349/3,923 elements in Case 3) due to permanent max_k envelope accumulation across evolving crack states combined with low-load local denominator depression, which explains the 85-92% unnecessary fine area and element explosion to 120k-481k elements. Step 5 scale isolation proved that Abaqus CAE RemeshingRule sizing is invariant within +0.07% across 13 orders of magnitude (C=1.0 to C=2.1e13), ruling out field scaling as the cause. 7/7 unit tests PASS in test_f1835_revised_diagnosis.py; 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
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
    "summary": "Task F1835 completes the 5-step native-donor reference and envelope-causality diagnosis across Cases 1, 2, 3, 5 and Case 4. Track 1 verified direct evolving donors are MISSING for Cases 1, 2, 3, 5, while Case 4 PK_F1720_COARSE_COUPLED.odb is the sole authentic in-analysis evolving UEL+UMAT donor in the repository (Step-1 13 frames, Step-2 179 frames). Track 2 untouched native remeshing on Step-2 terminal frame 178 produced 13,438 elements (97.51% quads, positive Jacobians, max AR 2.624, 3.53x coarsening PASS Gate 06) with only 23.15% fine area (h <= l0), demonstrating that native single-state remeshing does NOT over-refine. Track 3 recovery mechanics isolation verified physical stress bounds (0.0057-3.0809 MPa) and scale-invariant relative error ratio eta_e = MISESERI/MISESAVG (mean 3.4126%). Track 4 envelope decomposition proved that 60% of the coarse domain has eta_e >= 4% in multi-state recovery donors (1,743/2,906 elements in Case 2; 2,349/3,923 elements in Case 3) due to permanent max_k envelope accumulation across evolving crack states combined with low-load local denominator depression, which directly drives 85-92% unnecessary fine area and element explosions to 120k-481k elements. Track 5 scale isolation proved that Abaqus CAE RemeshingRule sizing is invariant within +0.07% across 13 orders of magnitude (C=1.0 to C=2.1e13), ruling out field scaling as the cause. 7/7 unit tests PASS in test_f1835_revised_diagnosis.py; 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
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

Write-Host "Dispatching Task F1835 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
