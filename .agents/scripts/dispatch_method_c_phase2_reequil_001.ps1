# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase2_reequil_001.ps1
# Dispatches Method C Phase 2: Resolving Remeshing Driver Path & Transfer Re-equilibration Package
# (HND-METHOD-C-PHASE2-REEQUIL-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE2-REEQUIL-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-JOB1-003"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE2_TRANSFER_REEQUILIBRATION_PACKAGE_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$decisionRecordPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_STEP1_REMESHING_DECISION_RECORD.md"
$decisionRecordSha = (Get-FileHash -Path $decisionRecordPath -Algorithm SHA256).Hash.ToUpper()

$meshPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$meshAuditPath = Join-Path $PSScriptRoot "..\..\results\validation\method_c_demo_refined_step1_mesh_audit.json"
$meshAuditSha = (Get-FileHash -Path $meshAuditPath -Algorithm SHA256).Hash.ToUpper()

$transferReceiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json"
$transferReceiptSha = (Get-FileHash -Path $transferReceiptPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 2: Remeshing Decision Driver Path Resolved & Transfer Re-equilibration Package Staged",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE2_TRANSFER_REEQUILIBRATION_PACKAGE_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase2_transfer_reequilibration",
    "numerical_uncertainty": "Can the remeshing-decision path be resolved for the demo Step-1 state (d_max 0.169, MISESERI 0.0) and a refined receiver mesh with a qualified transfer package be prepared for the fixed-load re-equilibration test?",
    "expected_numerical_result": "Remeshing-decision path documented for the Step-1 state; refined receiver mesh built (10,299 el, 96.84% quads, h=0.0035 mm < l0/2); transfer package prepared with the qualified isoparametric GP transfer (convex_clamp), preserving incipient tip damage d_max=0.169178 without healing (H_min >= 0, thermodynamic non-negativity verified); 3-layer production re-equilibration deck assembled (PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp, 30,897 layered elements, fixed load u2=0.0050 mm); 0 new PBS jobs submitted (cumulative 58 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "package_report": {
      "path": "docs/validation/METHOD_C_PHASE2_TRANSFER_REEQUILIBRATION_PACKAGE_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_PHASE2_TRANSFER_REEQUILIBRATION_PACKAGE_REPORT.md"
    },
    "decision_record": {
      "path": "docs/validation/METHOD_C_STEP1_REMESHING_DECISION_RECORD.md",
      "sha256": "$decisionRecordSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_STEP1_REMESHING_DECISION_RECORD.md",
      "resolves_gap": "NOTE-MC-J1B-01",
      "root_cause": "Abaqus built-in MISESERI error indicator is inactive (0.0) because Layer 3 companion elements use *USER MATERIAL (UMAT_MAT). Abaqus has no analytical elasticity tensor for general UMAT materials.",
      "decision_rule": "CONSTRUCTED_DAMAGE_ENVELOPE whenever incipient damage is present (d_max >= d_incipient = 0.10). At d_max = 0.169178, F1849 analytical damage sizing prescribes process-zone refinement h_tgt <= l0/2."
    },
    "refined_physical_mesh": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp",
      "sha256": "$meshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp",
      "element_count": 10299,
      "quad_count": 9974,
      "tri_count": 325,
      "quad_fraction": 0.968443538207593,
      "node_count": 10298,
      "min_det_j": 4.873727985449734e-07,
      "mean_aspect_ratio": 1.2885,
      "median_aspect_ratio": 1.2334,
      "process_zone_h": 0.0035,
      "l0_over_2": 0.00375
    },
    "mesh_audit_json": {
      "path": "results/validation/method_c_demo_refined_step1_mesh_audit.json",
      "sha256": "$meshAuditSha",
      "github_url": "$githubBase/results/validation/method_c_demo_refined_step1_mesh_audit.json"
    },
    "transfer_receipt": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json",
      "sha256": "$transferReceiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json",
      "resolves_gap": "NOTE-MC-J1B-02",
      "transfer_method": "isoparametric_gp_transfer.py with limiter_mode=convex_clamp",
      "receiver_gauss_points_count": 40221,
      "min_history_MPa": 0.0,
      "max_history_MPa": 0.2498721033334732,
      "peak_damage": 0.1691775918006897,
      "damage_preserved_no_healing": true,
      "negative_extrapolations_clamped": 63,
      "donor_extrema_bounded_evaluations": 10123
    },
    "production_reequilibration_deck": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp",
      "layered_element_count": 30897,
      "layer1_uel_phase_elements": 10299,
      "layer2_uel_disp_elements": 10299,
      "layer3_companion_elements": 10299,
      "total_nodes_including_rp": 10299,
      "boundary_condition_u2_RP_mm": 0.0050,
      "embedded_initial_conditions": {
        "nodal_displacements": "TYPE=DISPLACEMENT for 10298 nodes + RP",
        "phase_field_history": "TYPE=SOLUTION SVARS 1..18 for 10299 elements (SVARS 9..12 populated with transferred H0)"
      }
    },
    "accounting": {
      "authorized_submissions": 0,
      "consumed_submissions": 0,
      "cumulative_pbs": 58,
      "max_new_pbs": 0
    }
  },
  "governance": {
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "canonical_bridge_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
    "unit_tests": "18/18 PASS (100%)",
    "regression_tests": "16/16 PASS (100% in test_isoparametric_gp_transfer.py)",
    "master_goal_status": "OPEN"
  }
}

---
### Full Transfer Re-Equilibration Package Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C PHASE 2 TRANSFER RE-EQUILIBRATION PACKAGE HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
