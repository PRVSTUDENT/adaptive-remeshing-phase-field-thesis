# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1847_evidence_correction_001.ps1
# Dispatches Task F1847: F1846 Evidence Correction (Donor ODB, Gate 06 Reconciliation, Pinned Links, Benchmark Images)
# (HND-F1847-F1846-EVIDENCE-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1847-F1846-EVIDENCE-CORRECTION"
$handoffId = "HND-F1847-F1846-EVIDENCE-CORRECTION-001"
$predecessorHandoffId = "HND-F1846-GENERALIZED-FRAMEWORK-FROM-F1779-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1846_GENERALIZED_FRAMEWORK_FROM_F1779_REPORT.md"
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

$shaLpanelPng = Get-Sha256 (Join-Path $figDir "fig_f1846_unfamiliar_l_panel_mesh.png")
$shaLpanelPdf = Get-Sha256 (Join-Path $figDir "fig_f1846_unfamiliar_l_panel_mesh.pdf")
$shaC1Png     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_1_mesh.png")
$shaC1Pdf     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_1_mesh.pdf")
$shaC2Png     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_2_mesh.png")
$shaC2Pdf     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_2_mesh.pdf")
$shaC3Png     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_3_mesh.png")
$shaC3Pdf     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_3_mesh.pdf")
$shaC5Png     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_5_mesh.png")
$shaC5Pdf     = Get-Sha256 (Join-Path $figDir "fig_f1847_case_5_mesh.pdf")
$shaCompPng   = Get-Sha256 (Join-Path $figDir "fig_f1847_four_benchmark_composite.png")
$shaCompPdf   = Get-Sha256 (Join-Path $figDir "fig_f1847_four_benchmark_composite.pdf")

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1847: F1846 Evidence Correction (Donor ODB, Gate 06 Reconciliation, Pinned Links, Benchmark Images)",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Can the F1846 evidence record be completed so the L-panel native-MISESERI provenance is directly verifiable from the repo and the Gate 06 values are reconciled and consistent across the report, the audit JSON and the images?",
    "expected_numerical_result": "The L-panel donor ODB committed and hash-verified; the L-panel Gate 06 stated under one named definition with the report, image and audit JSON consistent; the Case 2 Gate 06 difference and the Case 5 PASS-to-FAIL flip explained; report image URLs commit-pinned; four benchmark regression mesh images committed with pinned URLs and SHAs; Windows absolute paths replaced with repo-relative paths. No framework change, no new mesh, no new solve, 0 new PBS jobs (cumulative 36 preserved). MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/276_f1846_generalized_framework/l_panel/PK_F1846_LPANEL_COARSE.odb",
      "donor_sha256": "84FE528239F5649A185BBB5DA9752B54AC288AED8393425E676D71E449554056",
      "donor_step": "Step-1",
      "donor_frame_index": 1,
      "indicator_frame_range": "[1, 1]",
      "held_out_later_solution": "Post-yield and non-linear fracture response held out; donor is pre-initiation linear elastic solve",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    },
    "image_manifest": [
      {
        "case_id": "l_panel_png",
        "relative_path": "results/figures/fig_f1846_unfamiliar_l_panel_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1846_unfamiliar_l_panel_mesh.png",
        "sha256": "$shaLpanelPng",
        "description": "Unfamiliar L-Shaped Panel Adapted Physical Mesh (567 elements, 97.53% Quads, max AR 2.27, Gate 06: 2.58x geometric PASS / 2.33x partition PASS)"
      },
      {
        "case_id": "l_panel_pdf",
        "relative_path": "results/figures/fig_f1846_unfamiliar_l_panel_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1846_unfamiliar_l_panel_mesh.pdf",
        "sha256": "$shaLpanelPdf",
        "description": "Unfamiliar L-Shaped Panel Adapted Physical Mesh Vector PDF"
      },
      {
        "case_id": "case_1_png",
        "relative_path": "results/figures/fig_f1847_case_1_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_1_mesh.png",
        "sha256": "$shaC1Png",
        "description": "Case 1 Regenerated Adapted Mesh (25,461 elements, 97.29% Quads, min det(J) > 0, Gate 06: 2.39x PASS, 0.00% delta vs F1812)"
      },
      {
        "case_id": "case_1_pdf",
        "relative_path": "results/figures/fig_f1847_case_1_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_1_mesh.pdf",
        "sha256": "$shaC1Pdf",
        "description": "Case 1 Regenerated Adapted Mesh Vector PDF"
      },
      {
        "case_id": "case_2_png",
        "relative_path": "results/figures/fig_f1847_case_2_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_2_mesh.png",
        "sha256": "$shaC2Png",
        "description": "Case 2 Regenerated Adapted Mesh (41,438 elements, 97.57% Quads, min det(J) > 0, Gate 06: 1.81x FAIL, 100% bitwise body SHA match vs F1812)"
      },
      {
        "case_id": "case_2_pdf",
        "relative_path": "results/figures/fig_f1847_case_2_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_2_mesh.pdf",
        "sha256": "$shaC2Pdf",
        "description": "Case 2 Regenerated Adapted Mesh Vector PDF"
      },
      {
        "case_id": "case_3_png",
        "relative_path": "results/figures/fig_f1847_case_3_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_3_mesh.png",
        "sha256": "$shaC3Png",
        "description": "Case 3 Regenerated Adapted Mesh (79,260 elements, 97.32% Quads, min det(J) > 0, Gate 06: 1.60x FAIL, +1.90% delta vs F1812)"
      },
      {
        "case_id": "case_3_pdf",
        "relative_path": "results/figures/fig_f1847_case_3_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_3_mesh.pdf",
        "sha256": "$shaC3Pdf",
        "description": "Case 3 Regenerated Adapted Mesh Vector PDF"
      },
      {
        "case_id": "case_5_png",
        "relative_path": "results/figures/fig_f1847_case_5_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_5_mesh.png",
        "sha256": "$shaC5Png",
        "description": "Case 5 Regenerated Adapted Mesh (15,411 elements, 97.74% Quads, min det(J) > 0, Gate 06: 1.94x FAIL, -0.36% delta vs F1812)"
      },
      {
        "case_id": "case_5_pdf",
        "relative_path": "results/figures/fig_f1847_case_5_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_case_5_mesh.pdf",
        "sha256": "$shaC5Pdf",
        "description": "Case 5 Regenerated Adapted Mesh Vector PDF"
      },
      {
        "case_id": "composite_png",
        "relative_path": "results/figures/fig_f1847_four_benchmark_composite.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_four_benchmark_composite.png",
        "sha256": "$shaCompPng",
        "description": "Task F1847: Four-Benchmark Regression 2x2 Composite (Cases 1, 2, 3, 5)"
      },
      {
        "case_id": "composite_pdf",
        "relative_path": "results/figures/fig_f1847_four_benchmark_composite.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1847_four_benchmark_composite.pdf",
        "sha256": "$shaCompPdf",
        "description": "Task F1847: Four-Benchmark Regression 2x2 Composite Vector PDF"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1847 completes the evidence correction for Task F1846 following supervisory review directive under HND-F1846-GENERALIZED-FRAMEWORK-FROM-F1779-001: (1) Committed authentic L-panel donor ODB models/pandey_kumar_mode1/276_f1846_generalized_framework/l_panel/PK_F1846_LPANEL_COARSE.odb (365,628 bytes, SHA 84FE528239F5649A185BBB5DA9752B54AC288AED8393425E676D71E449554056) to the git repository via forced git add, directly establishing verified causal provenance; (2) Reconciled L-panel Gate 06 coarsening definitions: explicitly documented that distance-based geometric coarsening gives 2.58x (primary physical metric) while discrete audit-mask partition gives 2.33x (engine internal check), both satisfying Gate 06 (>= 2.0x), and updated image title and report text; (3) Mathematically explained Case 2 Gate 06 difference (1.8147x vs 1.9349x harmonized) for the bitwise identical mesh (body SHA 5C7DD6B5) and Case 5 Gate 06 PASS-to-FAIL flip (1.9387x vs 2.1174x) as audit-mask boundary artifacts of the preserved F1779 adapter region definitions; (4) Generated, verified, and committed standalone mesh figures for all four benchmark regression meshes (Cases 1, 2, 3, 5) and a 2x2 publication composite with commit-pinned URLs; (5) Replaced Windows absolute paths with repo-relative paths in results/validation/f1846_four_benchmark_regression_summary.json (3,100 bytes, SHA B523673F...); (6) Unit tests extended with test_08 and all 8 tests PASS (100%); (7) Exactly 0 new meshes, 0 new solves, 0 new PBS jobs consumed (cumulative 36 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1846_GENERALIZED_FRAMEWORK_FROM_F1779_REPORT.md",
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

Write-Host "Dispatching Task F1847 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
