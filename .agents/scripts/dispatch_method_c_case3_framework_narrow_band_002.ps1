# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_narrow_band_002.ps1
# Dispatches Method C Case 3 Narrow Damage-Following Band Re-Issue
# (HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-REPAIR-001"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$corridorGenPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_case3_adaptive_corridor_mesh.py"
$corridorGenSha = (Get-FileHash -Path $corridorGenPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$physMeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
$physMeshSha = (Get-FileHash -Path $physMeshPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_framework_package.py"
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
  "title": "Method C Case 3: Narrow Damage-Following Band Specification and Implementation (Re-Issue 2)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "Can the narrow damage-following band (H = 2.0 mm, w_half = 1.0 mm ~ 3.51 l0, 102 elements/mm advance rate) resolve all three review gaps GAP-NB-01, GAP-NB-02, GAP-NB-03: (1) correct full-severance analytic estimates using function-verified clamping (x_max = 65.0 mm, L = 56.5 mm, A = 113.0 mm2, 5,765 band elements, ~12,265 total estimate); (2) wire dynamic per-cycle receiver mesh generation (generate_cycle_adaptive_mesh) into orchestrator.execute() and align manifest corridor_box (x in [8.5, 12.0], y in [69.0, 71.0], area 7.0 mm2) and baseline mesh header; (3) excise stale 17-30 mm docstrings; and (4) verify through a dedicated unit test that receiver mesh specifications monotonically follow the crack tip across cycles (21/21 unit tests PASS, 0 new PBS jobs)?",
    "expected_numerical_result": "All review gaps GAP-NB-01 through GAP-NB-03 and TEST-NB-01 verified resolved: Table 3.2 Full-Severance corrected to 56.5 mm length, 113.0 mm2 area, 5,765 refined elements, and ~12,265 total analytic estimate (<35,000 ceiling); per-cycle receiver mesh generation wired into Case3SingleJobOrchestrator.execute(); manifest corridor_box aligned to 7.0 mm2; docstrings refreshed; 21/21 unit tests PASS; 0 new PBS consumed (cumulative count strictly 70 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "review_gaps_resolved": {
    "GAP-NB-01": "Table 3.2 Full-Severance row updated to function-verified clamped values: x_max = min(65.0, 64.0 + 2.0) = 65.0 mm, L = 56.5 mm, Area = 113.0 mm2, 5,765 refined elements, and total analytic estimate of ~12,265 elements. Explicit Alert Note added declaring all Table 3.2 counts as analytic formula estimates (6,500 + round(A/0.0196)), not physical mesh counts.",
    "GAP-NB-02": "Added generate_cycle_adaptive_mesh(self, cycle_idx, tip_x, tip_y, d_nodal) to Case3SingleJobOrchestrator and wired it into execute() before state transfer and deck assembly to provide dynamic cycle-specific receiver physical mesh (PK_METHOD_C_CASE3_CYCLE<k>_PHYS.inp) from current tip coordinates. Aligned manifest corridor_box to initial narrow band: x in [8.5, 12.0] mm, y in [69.0, 71.0] mm, width 3.5 mm, height 2.0 mm, area 7.0 mm2, and target_physical_elements_bounded: 35000. Updated PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp header to Baseline Adaptive Receiver Physical Mesh.",
    "GAP-NB-03": "Cleaned stale docstrings in scripts/remeshing/generate_case3_adaptive_corridor_mesh.py and scripts/remeshing/case3_single_job_orchestrator.py (and synchronized package copies) to describe the narrow damage-following band (H = 2.0 mm, +/-1.0 mm half-width, 102 elements/mm advance rate, <35,000 bounded mesh).",
    "TEST-NB-01": "Added test_receiver_mesh_generation_per_cycle_follows_tip to tests/unit/test_method_c_case3_framework_package.py asserting distinct narrow band specifications for Cycle 1 (x=10 mm, L=3.5 mm, A=7.0 mm2), Cycle 2 (x=15 mm, L=8.5 mm, A=17.0 mm2), Cycle 3 (x=25 mm, L=18.5 mm, A=37.0 mm2), monotonic expansion of refined region, and orchestrator receiver mesh resolution. Entire suite passes 21/21 (100%)."
  },
  "evidence_manifest": {
    "report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md"
    },
    "corridor_generator": {
      "path": "scripts/remeshing/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "$corridorGenSha",
      "github_url": "$githubBase/scripts/remeshing/generate_case3_adaptive_corridor_mesh.py"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "framework_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
    },
    "adaptive_physical_mesh_baseline": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp",
      "sha256": "$physMeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_framework_package.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_framework_package.py"
    }
  },
  "narrow_band_specification": {
    "band_half_width_mm": 1.0,
    "band_height_mm": 2.0,
    "wake_margin_mm": 1.5,
    "ahead_margin_mm": 2.0,
    "h_ref_mm": 0.140,
    "l0_mm": 0.285,
    "l0_half_mm": 0.1425,
    "elements_per_mm_advance": 102,
    "target_total_elements_bounded": 35000,
    "representative_x30_mesh_elements_analytic": 8898,
    "full_propagation_x64_mesh_elements_analytic": 12265,
    "manual_campaign_cycle4_comparison_elements": 64653
  },
  "cluster_execution_state": {
    "live_running_job_id": "1424798.mmaster02",
    "cluster_node": "mnode105",
    "state": "EXECUTED (Job completed; postprocessing/diagnostics under inspection)",
    "scratch_directory_status": "PRESERVED",
    "cumulative_pbs_submissions": 70,
    "new_pbs_submissions_in_this_step": 0
  },
  "next_step": {
    "requested_decision": "APPROVE_NARROW_BAND_BUILD",
    "proposed_action": "Review narrow band specification and gap resolutions. Following approval, inspect Job 1424798 execution observables, and proceed with production multi-cycle adaptive remeshing under the narrow band formulation.",
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Host "CHECK ONLY: Handoff validation"
    Write-Host "Handoff ID: $handoffId"
    Write-Host "Commit SHA: $commitSha"
    Write-Host "Rules SHA: $rulesSha"
    Write-Host "Report SHA: $reportSha"
    Write-Host "Orchestrator SHA: $orchSha"
    Write-Host "Corridor Gen SHA: $corridorGenSha"
    return
}

if ($DryRun) {
    Write-Host "DRY RUN: Testing bridge validation"
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun
    return
}

Write-Host "DISPATCHING: Sending $handoffId across bridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId
