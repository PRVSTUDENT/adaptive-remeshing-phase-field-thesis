# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1839_evidence_completion_001.ps1
# Dispatches Task F1839: Complete F1838 Case 2 Native Pilot Evidence and Deliverables
# (HND-F1839-F1838-EVIDENCE-COMPLETION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1839-F1838-EVIDENCE-COMPLETION"
$handoffId = "HND-F1839-F1838-EVIDENCE-COMPLETION-001"
$predecessorHandoffId = "HND-F1838-CASE2-NATIVE-JOB1-PILOT-001"

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
  "title": "Task F1839: Complete F1838 Case 2 Native Pilot Evidence and Deliverables",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Are the F1838 Case 2 pilot evidence items (uncommitted donor ODB on GitHub, remesh receipt provenance contradiction, inaccurate artifact table sizes and SHAs, missing Gate 06/07 disclosures, un-reconciled peak MISESERI values and zone mean metrics, executive summary units error, cumulative PBS accounting caveat) completely and rigorously completed and corrected without running new solves or modifying frozen code?",
    "expected_numerical_result": "All 10 deliverables completed: (1) Frame 300 donor ODB committed to GitHub repository (7,512,588 bytes, SHA 84622470...); (2) Remesh receipt provenance contradiction resolved to NATIVE_ABAQUS_STRESS_RECOVERY_ERROR (SHA 0ADA25DC...); (3) Zone metrics recomputed from element geometry: distal ligament 10,280 elements, mean h=2.1379 um, coverage <= l0/2 is 94.62% in report window and 94.13% in F1812 window; (4) Peak MISESERI reconciled between dummy-scaled values (1.112e-13 Frame 167, 9.331e-14 Frame 300) and physical Cauchy stress errors (2,335.31 MPa and 1,959.58 MPa) via scaling factor s=4.7619e-14, with scale-invariant error ratios eta_max=82.87% and 81.38%; (5) Gate 06 (1.7325x FAIL against >= 2.0x threshold) and Gate 07 (28,165 PASS against < 80,000 threshold) plainly stated; (6) Visual mesh inspection disclosed (diffuse refinement over right half, pinned corner); (7) Executive summary units error corrected (981 N to 149 N); (8) PBS cumulative caveat noted (36 without F1828, 40 with); (9) Causal labels corrected to Step-2 Frame 300; (10) Section 7 artifact table fully updated with verified sizes and hashes; unit tests 9/9 PASS; 0 new PBS jobs consumed; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/277_f1838_case2_native_pilot/PK_F1838_CASE2_FRAME300_DONOR.odb",
      "donor_sha256": "84622470D9B5DD86837030E4F7977308844B7D0B4DEF3AC444ACA609C4A4A78F",
      "donor_step": "Step-2",
      "donor_frame_index": 300,
      "indicator_frame_range": "[300, 300]",
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
    "summary": "Task F1839 completes all 10 evidence completion and correction deliverables for the F1838 Case 2 pilot following review decision INSUFFICIENT_EVIDENCE under HND-F1838-CASE2-NATIVE-JOB1-PILOT-001: (1) Frame 300 donor ODB committed to repository (7,512,588 bytes, SHA 84622470...); (2) Remesh receipt provenance contradiction resolved to NATIVE_ABAQUS_STRESS_RECOVERY_ERROR (SHA 0ADA25DC...); (3) Zone metrics recomputed from element geometry: distal ligament 10,280 elements, mean h=2.1379 um, coverage <= l0/2 is 94.62% in report window and 94.13% in F1812 window; (4) Peak MISESERI reconciled between dummy-scaled values (1.112e-13 Frame 167, 9.331e-14 Frame 300) and physical Cauchy stress errors (2,335.31 MPa and 1,959.58 MPa) via scaling factor s=4.7619e-14, with scale-invariant error ratios eta_max=82.87% and 81.38%; (5) Gate 06 (1.7325x FAIL against >= 2.0x threshold) and Gate 07 (28,165 PASS against < 80,000 threshold) plainly stated; (6) Visual mesh inspection disclosed (diffuse refinement over right half, pinned corner); (7) Executive summary units error corrected (981 N to 149 N); (8) PBS cumulative caveat noted (36 without F1828, 40 with); (9) Causal labels corrected to Step-2 Frame 300; (10) Section 7 artifact table fully updated with verified sizes and hashes; unit tests 9/9 PASS; 0 new PBS jobs consumed; MASTER_GOAL_STATUS = OPEN.",
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

Write-Host "Dispatching Task F1839 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
