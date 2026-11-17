# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1838_case2_pilot_auth_001.ps1
# Dispatches Task F1838: Bounded Native Job-1 Pilot for Case 2 & Case 1 Islands Diagnosis
# (HND-F1838-CASE2-NATIVE-JOB1-PILOT-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1838-CASE2-NATIVE-JOB1-PILOT"
$handoffId = "HND-F1838-CASE2-NATIVE-JOB1-PILOT-001"
$predecessorHandoffId = "HND-F1836-F1835-REPORT-CORRECTION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1838_CASE2_NATIVE_JOB1_PILOT_REPORT.md"
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

$shaC2Png = Get-Sha256 (Join-Path $figDir "fig_f1838_case2_pilot_mesh.png")
$shaC2Pdf = Get-Sha256 (Join-Path $figDir "fig_f1838_case2_pilot_mesh.pdf")

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1838: Bounded Native Job-1 Pilot for Case 2 and Case 1 Islands Diagnosis",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Can the candidate stress-output interface f42_native_miseseri_interface_v1.for achieve mechanical equivalence and deliver nonzero native MISESERI through full nonlinear crack evolution, and can a single authentic evolved frame (Frame 300) guide a single-pass native remesh that actively refines the outer distal ligament without artificial multi-state envelope distortion?",
    "expected_numerical_result": "Phase 1: Case 1 refinement islands diagnosed from primary ODB fields as synthesized data from multi-state max_k aggregation across terminal severance load drops (981 to 149 N), collapsing local denominators to 14-30 MPa and artificially inflating relative error to 20.7%-65.88%. Phase 2: Interface f42_native_miseseri_interface_v1.for qualified on Case 2 (PBS Job 1424198.mmaster02, exactly 1 new PBS job, cumulative 36): peak reaction force 0.731015 kN matches coarse baseline within 0.000036%, peak displacement matches within 0.002571% (both <= 0.01% threshold); incremental cutback rollback buffer verified at Increment 152; native MISESERI and MISESAVG present across all 2,906 elements in all 338 frames of Step 2. Extracted evolved Frame 300 (t=0.5937 s, d_max=0.9972) into compact 7.5 MB donor ODB. Single-pass native remesh with UNIFORM_ERROR at 4.0% error target generates 28,165 elements (97.57% Quads, min det(J) = 1.87e-7 > 0, max AR 2.60 < 4.0) with 10,280 elements actively resolving the outer distal ligament beyond the hole. Exactly 1 new PBS job consumed (cumulative 36); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/277_f1838_case2_native_pilot/PK_F1838_CASE2_FRAME300_DONOR.odb",
      "donor_sha256": "84622470D9B5DD86837030E4F7977308844B7D0B4DEF3AC444ACA609C4A4A78F",
      "donor_step": "RECOVERY_STEP",
      "donor_frame_index": 2,
      "indicator_frame_range": "[0, 2]",
      "held_out_later_solution": "Post-arrest distal crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 0.5937,
      "maximum_indicator_time": 0.5937
    },
    "image_manifest": [
      {
        "case_id": "case_2",
        "relative_path": "results/figures/fig_f1838_case2_pilot_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1838_case2_pilot_mesh.png",
        "sha256": "$shaC2Png",
        "description": "Case 2 Single-Frame Native Pilot Remeshed Physical Mesh (28,165 elements, 97.57% Quads, min det(J) = 1.87e-7 > 0, max AR = 2.60 < 4.0, 10,280 elements resolving outer distal ligament)"
      },
      {
        "case_id": "case_2_pdf",
        "relative_path": "results/figures/fig_f1838_case2_pilot_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1838_case2_pilot_mesh.pdf",
        "sha256": "$shaC2Pdf",
        "description": "Case 2 Single-Frame Native Pilot Remeshed Physical Mesh Vector PDF"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1838 completes the bounded native Job-1 pilot for Case 2 and resolves the Case 1 refinement islands: (1) Diagnosed Case 1 refinement islands as synthesized data from multi-state max_k aggregation across post-severance load drops (981 to 149 N), where denominator collapse (14-30 MPa) artificially inflated relative error to 20.7%-65.88% across boundaries while element labeling and donor topology are 100% correct; (2) Staged and executed bounded Case 2 forward coarse solve with candidate interface f42_native_miseseri_interface_v1.for as PBS Job 1424198.mmaster02, consuming exactly 1 new PBS job (cumulative 36, max_new_pbs=1 respected); (3) Verified exact mechanical equivalence against coarse baseline PK_HOLE_COARSE_JOB1.odb: peak force 0.731015 kN matches within 0.000036% and displacement matches within 0.002571% (both <= 0.01% threshold); (4) Verified cutback buffer handling at Increment 152 without divergence or stress poisoning; (5) Verified native MISESERI and MISESAVG present across all 2,906 elements in all 338 frames of Step 2; (6) Extracted authentic evolved Frame 300 (t=0.5937 s, d_max=0.9972) into compact 7.5 MB donor ODB; (7) Executed single-pass native remesh via Abaqus CAE UNIFORM_ERROR at 4.0% error target producing 28,165 elements (97.57% Quads, min det(J)=1.87e-7 > 0, max AR 2.60 < 4.0) with 10,280 elements actively resolving the outer distal ligament beyond the hole; (8) Rendered and published mesh figures with commit-pinned GitHub URLs; (9) 9/9 unit tests PASS in test_f1838_case2_native_pilot.py. Bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1838_CASE2_NATIVE_JOB1_PILOT_REPORT.md",
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

Write-Host "Dispatching Task F1838 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
