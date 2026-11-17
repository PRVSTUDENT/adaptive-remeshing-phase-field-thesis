# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1842_final_report_correction_001.ps1
# Dispatches Task F1842: Final Report and Remesh Script Correction for Case 2 Paper-Reproduction Reference
# (HND-F1842-F1840-FINAL-REPORT-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1842-F1840-FINAL-REPORT-CORRECTION"
$handoffId = "HND-F1842-F1840-FINAL-REPORT-CORRECTION-001"
$predecessorHandoffId = "HND-F1841-F1840-ARTIFACT-TABLE-CORRECTION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1840_CASE2_FINAL_FRAME_REMESH_COMPARISON_REPORT.md"
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
$imageCommitSha = "458e6a9d8cb36fae18f357e11577989adac4617e"

# Read figure SHA256 hashes dynamically
$figDir = Join-Path $PSScriptRoot "..\..\results\figures"
function Get-Sha256($fpath) {
    if (Test-Path $fpath) {
        return (Get-FileHash -Path $fpath -Algorithm SHA256).Hash.ToUpper()
    }
    return "PENDING"
}

$shaFinalPng = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_final_frame_mesh.png")
$shaFinalPdf = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_final_frame_mesh.pdf")
$shaCompPng  = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_comparison.png")
$shaCompPdf  = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_comparison.pdf")

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1842: Final Report and Remesh Script Correction for Case 2 Paper-Reproduction Reference",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Narrow correction-only reconciliation: does correcting Section 3 line 83 INP body SHA to 26FBE773..., correcting Table 7.2 checkpoint 458e6a9d baseline rows for extract script (10,102 B, SHA 12790D104F66...) and remesh script (16,093 B, SHA FFF34BFD0963...), and restoring standard body SHA function in run_f1840_case2_final_frame_remesh.py (reproducing 26FBE773... directly) resolve all remaining defects while preserving the verified core science of F1840?",
    "expected_numerical_result": "100% internal and external consistency across the F1840 report and codebase: Section 3 line 83 body SHA 26FBE77367FB71EE2DE300A2E7B9B7EC26E82E0FF333BC37F807A1BE0F647AC6 matching Table 7.1, remesh receipt, and committed mesh; Table 7.2 baseline rows matching independent downloads at 458e6a9d; run_f1840_case2_final_frame_remesh.py compute_body_sha256 directly reproducing 26FBE773... verified by unit test; Table 7.1 updated with exact live disk values for remesh script (16,077 B, SHA 8104BA8DD3A2...) and test file (7,839 B, SHA 56811A26D314...); 9/9 unit tests in test_f1840_final_frame_comparison.py PASS; exactly 0 new meshes, 0 new solves, 0 new PBS jobs (cumulative 36 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/278_f1840_final_frame_comparison/PK_F1840_CASE2_FINAL_FRAME_DONOR.odb",
      "donor_sha256": "A48C17D793077BD08D9B95177CFFB9F7C4FA39ED1E6959A37F20CD515FBA27A5",
      "donor_step": "Step-2",
      "donor_frame_index": 337,
      "indicator_frame_range": "[337, 337]",
      "held_out_later_solution": "Post-remesh crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 0.655825,
      "maximum_indicator_time": 0.655825
    },
    "image_manifest": [
      {
        "case_id": "case_2_final_frame",
        "relative_path": "results/figures/fig_f1840_case2_final_frame_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1840_case2_final_frame_mesh.png",
        "sha256": "$shaFinalPng",
        "description": "Case 2 Final-Frame (337) Native Remeshed Physical Mesh (28,160 elements, 97.76% Quads, min det(J) = 2.46e-7 > 0, max AR = 2.21, 8,759 distal elements, 91.48% <= l0/2)"
      },
      {
        "case_id": "case_2_final_frame_pdf",
        "relative_path": "results/figures/fig_f1840_case2_final_frame_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1840_case2_final_frame_mesh.pdf",
        "sha256": "$shaFinalPdf",
        "description": "Case 2 Final-Frame Native Remeshed Physical Mesh Vector PDF"
      },
      {
        "case_id": "case_2_comparison",
        "relative_path": "results/figures/fig_f1840_case2_comparison.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1840_case2_comparison.png",
        "sha256": "$shaCompPng",
        "description": "Case 2 Side-by-Side Comparison: Frame 300 (Crack-Arrest Diagnostic) vs Frame 337 (Paper-Reproduction Reference)"
      },
      {
        "case_id": "case_2_comparison_pdf",
        "relative_path": "results/figures/fig_f1840_case2_comparison.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1840_case2_comparison.pdf",
        "sha256": "$shaCompPdf",
        "description": "Case 2 Side-by-Side Comparison Vector PDF"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1842 completes the final narrow correction-only mandate following supervisory review REJECT under HND-F1841-F1840-ARTIFACT-TABLE-CORRECTION-001: (1) Corrected Section 3 line 83 INP body SHA to 26FBE77367FB71EE2DE300A2E7B9B7EC26E82E0FF333BC37F807A1BE0F647AC6, resolving internal inconsistency with Table 7.1 and the remesh receipt; (2) Corrected Table 7.2 checkpoint 458e6a9d baseline rows for the extract script (10,102 B, SHA 12790D104F667015382DE31E4712154480F7E87B7A09B633518A77EF7AE7D045) and remesh script (16,093 B, SHA FFF34BFD096379DC1C8F49E4E575AD6602053BB7F356FEF5ABFF2A9895109DA2), matching independent downloads; (3) Restored standard repository body-SHA function in scripts/remeshing/run_f1840_case2_final_frame_remesh.py by removing *HEADING filter, directly reproducing 26FBE773...; (4) Added test_remesh_script_body_sha_reproduction to test_f1840_final_frame_comparison.py, verifying that remesh script function reproduces the exact registry body SHA; all 9 unit tests PASS; test_f1838_case2_native_pilot.py 9/9 PASS; (5) Table 7.1 updated with exact live disk values for remesh script (16,077 B, SHA 8104BA8DD3A2...) and test file (7,839 B, SHA 56811A26D314...); (6) Strictly correction-only: zero new meshes, zero new solves, zero new PBS jobs (cumulative 36 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1840_CASE2_FINAL_FRAME_REMESH_COMPARISON_REPORT.md",
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

Write-Host "Dispatching Task F1842 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
