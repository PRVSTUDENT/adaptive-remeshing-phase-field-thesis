# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_cycle2_prep_001.ps1
# Dispatches Method C Cycle 2: Remesh, State Transfer, Re-Equilibration and Propagation Package Preparation
# (HND-METHOD-C-CYCLE2-PREP-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CYCLE2-REMESH-TRANSFER-PROPAGATE"
$handoffId = "HND-METHOD-C-CYCLE2-PREP-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE4-MATERIALS-003"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CYCLE2_PACKAGE_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$meshPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$auditPath = Join-Path $PSScriptRoot "..\..\results\validation\method_c_cycle2_mesh_audit.json"
$auditSha = (Get-FileHash -Path $auditPath -Algorithm SHA256).Hash.ToUpper()

$donorPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\donor_job3_state.json"
$donorSha = (Get-FileHash -Path $donorPath -Algorithm SHA256).Hash.ToUpper()

$receiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_TRANSFER_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_REFINED_JOB4.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_cycle2_package.py"
$testSha = (Get-FileHash -Path $testPath -Algorithm SHA256).Hash.ToUpper()

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Cycle 2: Remesh, State Transfer, Re-Equilibration and Propagation Package Preparation",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CYCLE2_PACKAGE_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_cycle2_remesh_transfer_propagate",
    "numerical_uncertainty": "Can an adapted physical receiver mesh (14,004 el) generated from the Job-3 ruptured end state (d_max = 1.0055) via the F1852 damage envelope driver accurately receive the transferred state and extreme history peak (4629.69 MPa) with convex_clamp limiter, preserving crack-wake damage without healing, enforcing H >= 0 everywhere, and producing an equilibrium-ready 3-layer coupled deck (PK_METHOD_C_CYCLE2_REFINED_JOB4.inp) for Step-1 re-equilibration at u2 = 0.008756 mm and Step-2 propagation toward the right edge?",
    "expected_numerical_result": "Adapted receiver physical mesh passes all 3 FE quality gates (min det(J) = 1.137e-7 > 0, quad frac 96.86% >= 85%, mean AR 1.29 <= 2.5); isoparametric GP transfer preserves peak history 4629.69 MPa and enforces H >= 0 across all 54,696 integration points; nodal damage preserves complete crack wake rupture at d_max = 0.9998 with zero healing; 3-layer production deck PK_METHOD_C_CYCLE2_REFINED_JOB4.inp (42,012 layered elements) assembled and staged for review; 37/37 unit tests PASS (100%); 0 new PBS jobs consumed, cumulative 60 strictly preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "package_report": {
      "path": "docs/validation/METHOD_C_CYCLE2_PACKAGE_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CYCLE2_PACKAGE_REPORT.md"
    },
    "adapted_physical_mesh": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp",
      "sha256": "$meshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp"
    },
    "mesh_quality_audit": {
      "path": "results/validation/method_c_cycle2_mesh_audit.json",
      "sha256": "$auditSha",
      "github_url": "$githubBase/results/validation/method_c_cycle2_mesh_audit.json"
    },
    "donor_job3_state": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/donor_job3_state.json",
      "sha256": "$donorSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/donor_job3_state.json"
    },
    "transfer_receipt": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_TRANSFER_RECEIPT.json",
      "sha256": "$receiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_TRANSFER_RECEIPT.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4.inp"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_cycle2_package.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_cycle2_package.py"
    }
  },
  "package_metrics": {
    "donor_job_id": "1424609.mmaster02",
    "donor_step2_increments": 125,
    "donor_displacement_u2_mm": 0.008756,
    "donor_final_crack_tip_x_mm": 0.895686,
    "donor_peak_damage": 0.999862,
    "donor_peak_history_MPa": 4629.688965,
    "driver_selection": "CONSTRUCTED_DAMAGE_ENVELOPE",
    "receiver_physical_elements": 14004,
    "receiver_quad_elements": 13564,
    "receiver_tri_elements": 440,
    "receiver_quad_fraction_pct": 96.86,
    "receiver_nodes": 14011,
    "receiver_layered_elements": 42012,
    "min_det_j": 1.137097e-07,
    "mean_aspect_ratio": 1.29,
    "median_aspect_ratio": 1.24,
    "max_aspect_ratio": 3.52,
    "all_fe_gates_passed": true,
    "transferred_peak_damage": 0.999775,
    "damage_preserved_no_healing": true,
    "transferred_min_history_MPa": 1.196067e-09,
    "thermodynamic_nonnegativity_verified": true,
    "transferred_peak_history_MPa": 4629.688965,
    "history_extreme_preserved": true,
    "deck_step1_re_equilibration_u2_mm": 0.008756,
    "deck_step2_propagation_u2_mm": 0.012000,
    "new_pbs_jobs_consumed": 0,
    "cumulative_pbs_jobs_consumed": 60,
    "master_goal_status": "OPEN",
    "unit_tests_pass_rate": "37/37 (100%)"
  },
  "report_markdown": "$([Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($reportContent)))"
}
"@

if ($CheckOnly) {
    Write-Host "Check-only mode requested. Prompt verified and ready for dispatch."
    Write-Host "Handoff ID: $handoffId"
    Write-Host "Task ID: $taskId"
    Write-Host "Commit: $commitSha"
    return
}

Invoke-ChatGPTBridge -Prompt $prompt -HandoffId $handoffId
