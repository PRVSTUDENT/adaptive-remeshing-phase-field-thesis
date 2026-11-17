# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1832_f1831_correction_auth_001.ps1
# Dispatches Task F1832 Report and Evidence Correction
# (HND-F1832-F1831-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1832-F1831-REPORT-CORRECTION"
$handoffId = "HND-F1832-F1831-CORRECTION-001"
$predecessorHandoffId = "HND-F1831-MATCHED-DONOR-EXPERIMENT-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1831_MATCHED_DONOR_EXPERIMENT_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = "eabb2a884ec955f3dc00ba2a67307e4419f7fa0f"

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1832: Correct the F1831 Matched Donor Experiment Report and Evidence",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Are all 8 evidentiary discrepancies and reporting defects flagged in review HND-F1831-MATCHED-DONOR-EXPERIMENT-001 rigorously corrected in place without changing the underlying physical findings or introducing new defects?",
    "expected_numerical_result": "All 8 review items corrected: (1) Section 3 table F1812 Gate 06 values restored to verified baselines: Case 1 2.3867x (PASS), Case 2 1.9349x (FAIL), Case 3 1.4462x (FAIL), Case 5 2.1174x (PASS); Cases 2 and 3 explicitly labeled FAIL; (2) Case 1 A.1 element count reconciled to 4,384 elements (staged PK_F1831_CASE_1_A1_PHYS.inp, 97.15% quads, min det(J)>0, max AR 2.26, Gate 06 1.87x FAIL, full ligament coverage 0.00% FAIL, body SHA A3FAE74F81182719DD6EFCA23010D71D08D5E278299785551CB76EC4738ACD14); (3) Case 3 A.1 Gate 06 coarsening reconciled to 1.05x (FAIL) in both report and summary JSON; (4) image manifest SHAs corrected to actual disk values: Case 1 8E0665D3..., Case 2 A5B40D10..., Case 3 9D12195B..., Case 5 3D4D0131..., Composite C3517971...; (5) aggregation inflation reported honestly: Case 1 mean -13.99% / max +150.23%; Case 2 mean +24.63% / max +36.90%; Case 3 mean -0.67% / max +198.68%; Case 5 0.00%; plainly stating only Case 2 has positive net mean inflation; (6) donor ODB path reconciled to models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb and SHA to F1829 registered 4A1A78B6C72E3BA051D9835777D4380EFE212B27A23FE835616D7FE28C3E1410; (7) Section 5 image manifest commit pinned to eabb2a884ec955f3dc00ba2a67307e4419f7fa0f and displayed meshes described accurately; (8) all A.1 mesh files committed with body SHAs recorded in Section 5.2 artifact table; 13/13 unit tests PASS (test_f1831 and test_f1832); 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework 80B41AA2... strictly maintained; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb",
      "donor_sha256": "4A1A78B6C72E3BA051D9835777D4380EFE212B27A23FE835616D7FE28C3E1410",
      "donor_step": "Step-1",
      "donor_frame_index": 12,
      "indicator_frame_range": "[0, 12]",
      "held_out_later_solution": "Step 2 post-peak crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    },
    "image_manifest": [
      {
        "case_id": "case_1",
        "relative_path": "results/figures/fig_f1831_case_1_matched_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1831_case_1_matched_mesh.png",
        "sha256": "8E0665D3A1A9ADEA0AA8F4AE91391D3951D90CD9180D58CC98BC1A74C67D89E0",
        "description": "Case 1 Standalone Mesh View (F1831 matched A.2 baseline: 25,461 elements; A.1 direct single-state: 4,384 elements)"
      },
      {
        "case_id": "case_2",
        "relative_path": "results/figures/fig_f1831_case_2_matched_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1831_case_2_matched_mesh.png",
        "sha256": "A5B40D10DA9196CFEB04BCE2C5217BA28EA1F2F708FD0863CE63C48C341DA139",
        "description": "Case 2 Standalone Mesh View (F1831 matched A.2 baseline: 41,438 elements; A.1 direct single-state: 13,651 elements)"
      },
      {
        "case_id": "case_3",
        "relative_path": "results/figures/fig_f1831_case_3_matched_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1831_case_3_matched_mesh.png",
        "sha256": "9D12195BB4FCADA4D8D4C0B31548685CA7A465F7D11E41CB091446C247D34709",
        "description": "Case 3 Standalone Mesh View (F1831 matched A.2 baseline: 77,779 elements; A.1 direct single-state: 44,534 elements)"
      },
      {
        "case_id": "case_5",
        "relative_path": "results/figures/fig_f1831_case_5_matched_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1831_case_5_matched_mesh.png",
        "sha256": "3D4D01311F0DC9A6154390BA685C2A236CA92680E8AFCC73F61CC0A558501869",
        "description": "Case 5 Standalone Mesh View (F1831 matched A.1/A.2 baseline: 15,466 elements)"
      },
      {
        "case_id": "composite",
        "relative_path": "results/figures/fig_f1831_matched_donor_synthesis.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1831_matched_donor_synthesis.png",
        "sha256": "C3517971343C9F30A46691FDF2F845B4442320999E54FB106B2350AD78163B62",
        "description": "4-Panel Publication Synthesis Composite"
      }
    ]
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Does Task F1832 rigorously and accurately correct all 8 evidentiary items from the F1831 review (HND-F1831-MATCHED-DONOR-EXPERIMENT-001): (1) restoring authentic F1812 Gate 06 baselines in Section 3 table (Case 1 2.3867x PASS, Case 2 1.9349x FAIL, Case 3 1.4462x FAIL, Case 5 2.1174x PASS) without falsely claiming PASS on Cases 2 and 3; (2) reconciling Case 1 A.1 mesh to 4,384 elements (staged, body SHA A3FAE74F..., Gate 06 1.87x FAIL, full ligament coverage 0.00% FAIL); (3) reconciling Case 3 A.1 Gate 06 coarsening to 1.05x (FAIL); (4) fixing image manifest SHAs to actual per-image values; (5) honestly stating both mean and max error inflation across the domain (noting only Case 2 has positive net mean inflation); (6) reconciling donor ODB path and SHA; (7) pinning Section 5 image manifest commit to eabb2a884ec955f3dc00ba2a67307e4419f7fa0f and describing displayed meshes accurately; (8) committing all A.1 mesh files with body SHAs in Section 5.2 artifact table; and maintaining bitwise frozen UEL CE8D5EDC... and framework 80B41AA2... with zero new PBS jobs consumed?",
    "evaluation_criteria": [
      "1. F1812 Gate 06 Baselines Reconciled: Section 3 table contains exact authentic values (Case 1 2.3867x PASS, Case 2 1.9349x FAIL, Case 3 1.4462x FAIL, Case 5 2.1174x PASS) with Cases 2 and 3 marked as FAIL.",
      "2. Case 1 A.1 Consistency: PK_F1831_CASE_1_A1_PHYS.inp staged (4,384 elements, body SHA A3FAE74F81182719DD6EFCA23010D71D08D5E278299785551CB76EC4738ACD14) with consistent counts in report and summary JSON.",
      "3. Case 3 A.1 Gate 06 Consistency: Reconciled to 1.05x (FAIL) in both report table and summary JSON.",
      "4. Image Manifest Hashes: Verified distinct per-image SHA-256 hashes matching disk files.",
      "5. Aggregation Inflation Integrity: Both mean and max error inflation reported honestly across domain, explicitly noting only Case 2 has positive mean inflation.",
      "6. Causal Donor ODB Reconciliation: Correct path models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb and registered SHA 4A1A78B6C72E3BA051D9835777D4380EFE212B27A23FE835616D7FE28C3E1410.",
      "7. Image Manifest Commit Pin: Commit pinned to eabb2a884ec955f3dc00ba2a67307e4419f7fa0f with accurate mesh descriptions.",
      "8. Mesh Artifacts Table: Section 5.2 table catalogs all 8 physical mesh INP files with body SHA-256 values.",
      "9. Unit Tests & Governance: 13/13 unit tests PASS (test_f1831 and test_f1832); 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework 80B41AA2... strictly maintained; MASTER_GOAL_STATUS = OPEN."
    ],
    "commit_sha": "$commitSha",
    "report_artifact": "docs/validation/F1831_MATCHED_DONOR_EXPERIMENT_REPORT.md",
    "receipt_artifact": "models/pandey_kumar_mode1/PK_F1832_CORRECTION_RECEIPT.json",
    "summary_json_artifact": "results/validation/f1831_matched_donor_summary.json",
    "test_suite_artifact": "tests/unit/test_f1832_f1831_corrections.py"
  }
}

---
$reportContent

---
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "CheckOnly specified. Bridge payload header validated for $handoffId."
    return
}

Write-Host "Dispatching Task F1832 Report and Evidence Correction across OpenClaw PAD Bridge ($handoffId)..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId -TimeoutMinutes 40
