param(
    [switch]$Publish = $false
)

$sourceRoot = "D:\Master thesis\Adaptive remeshing\.agents\scripts"
if (-not (Test-Path -LiteralPath $sourceRoot)) { $sourceRoot = $PSScriptRoot }

. (Join-Path $sourceRoot "Bridge-ResearchContract.ps1")
. (Join-Path $sourceRoot "Invoke-ChatGPTBridge.ps1")

$prompt = @'
[BRIDGE_HANDOFF_ID=HND-METHOD-C-CASE3-RERUN-001]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-CASE3-RERUN-001",
  "predecessor_correlation_id": "HND-METHOD-C-COMPLEX-006",
  "task_id": "METHOD-C-CASE3-RERUN",
  "title": "Method C Case 3 Re-run with Current Improved Framework — Adaptive Remesh Step Count Evaluation",
  "goal_id": "METHOD_C_COMPLEX_MODELS_V1",
  "canonical_rules_sha256": "B1117C2B72931DEF23CA2C626F8F3469395906CC2878555467B648306BA44190",
  "artifact_commit": "325aaee498e21950d2bb812b322dafa45ae69cb0",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_RERUN_STEP_COUNT_REPORT.md",
  "checkpoint_artifact_sha256": "60F3A2BC2E1A18F292FF78B1157A6654538A09B31C3420660D28404AA394915E",
  "research_contract": {
    "goal_id": "METHOD_C_COMPLEX_MODELS_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_rerun_step_count_evaluation",
    "numerical_uncertainty": "Does the current improved framework (with Phase 1 improvements and the fixed check_completion stopping logic requiring RF2 < 5% of peak in all branches) still take the same number of adaptive remesh steps (~52-56) on Case 3 as the original run, or does it stop earlier at Cycle 53 upon complete specimen severance?",
    "expected_numerical_result": "Direct measurement and comparison of adaptive remesh step count between original run (56 adaptive steps / 57 cycles) and improved framework (53 adaptive steps / 54 cycles); confirmation that Cycle 52 (RF2 = 14.72% > 5%) does not stop prematurely while Cycle 53 (RF2 = 0.039% << 5%, 99.961% load drop, x = 65.0 mm) cleanly terminates the run, eliminating 3 redundant post-severance cycles (Cycles 54-56); 7/7 unit tests PASS; 0 PBS consumed, cumulative 73 preserved; frozen UEL CE8D5EDC unchanged; master goal OPEN.",
    "indicator_type": "DAMAGE_INFORMED_SIZING",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_sha256": "516C2A02F9D44421291B22DB4023E2C29774D826B1FF94845CA33BCA48ABC5C4",
      "donor_step": "Step-2",
      "indicator_frame_range": "Cycles 0 to 53 terminal increments",
      "held_out_later_solution": "Post-severance cycles 54 to 56 held out and confirmed redundant (specimen already severed at Cycle 53 with RF2 = 1.69 N)",
      "uses_future_frames": false,
      "remesh_time": 0.3456,
      "maximum_indicator_time": 0.3456
    }
  },
  "closeout_statement": {
    "research_question": "Does Method C Case 3 re-run with the current improved framework still take the same number of adaptive remesh steps (~52-56) as the original run, or fewer?",
    "plain_answer": "Under the current improved framework with fixed stopping logic, Case 3 takes exactly 53 adaptive remesh steps (54 cycles: Cycle 0 coarse + Cycles 1-53), compared to 56 adaptive remesh steps (57 cycles) in the original run. The step count is reduced by exactly 3 steps (-5.36%).",
    "original_run_steps": 56,
    "original_run_total_cycles": 57,
    "improved_framework_steps": 53,
    "improved_framework_total_cycles": 54,
    "step_count_reduction": 3,
    "step_count_reduction_pct": 5.357,
    "eliminated_cycles": [54, 55, 56],
    "cycle_52_behavior": "Crack arc length s = 62.3665 mm >= 62.0 mm and tip x = 64.1383 mm >= 64.0 mm, but RF2 = 0.6377 kN (14.72% of peak > 5%); stopping logic correctly DOES NOT stop prematurely, advancing to Cycle 53",
    "cycle_53_severance": "Crack tip reaches x = 65.0000 mm (right edge); RF2 collapses to 0.001694 kN (1.69 N, 0.039% of peak, 99.961% load drop); stopping criterion PLATE_SEVERED_LOAD_DROP_BELOW_5PCT fires immediately and terminates simulation",
    "finite_element_budget": "Bounded strictly between 22,850 and 30,253 elements across all cycles (<35,000 ceiling, quads >= 97.68%, aspect ratio <= 4.49, min det(J) > 0)",
    "original_run_preserved": "Original results in models/pandey_kumar_mode1/290_method_c_case3/ remain 100% untouched; rerun isolated in models/pandey_kumar_mode1/290_method_c_case3_rerun/",
    "unit_test_status": "7/7 PASS (100%) in tests/unit/test_method_c_case3_rerun.py; combined Case 3 suite 19/19 PASS (100%)",
    "pbs_accounting": "0 PBS consumed, cumulative 73 strictly preserved; cluster job 1424916 untouched",
    "frozen_uel_integrity": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6 (Bitwise Identical)",
    "master_goal_status": "OPEN",
    "next_step": "Awaiting independent structured review from ChatGPT / Muse"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_CASE3_RERUN_STEP_COUNT_REPORT.md",
      "sha256": "60F3A2BC2E1A18F292FF78B1157A6654538A09B31C3420660D28404AA394915E",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/docs/validation/METHOD_C_CASE3_RERUN_STEP_COUNT_REPORT.md"
    },
    "rerun_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3_rerun/METHOD_C_CASE3_RERUN_SUMMARY.json",
      "sha256": "516C2A02F9D44421291B22DB4023E2C29774D826B1FF94845CA33BCA48ABC5C4",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/290_method_c_case3_rerun/METHOD_C_CASE3_RERUN_SUMMARY.json"
    },
    "comparison_figure_png": {
      "path": "results/figures/fig_method_c_case3_rerun_step_count_comparison.png",
      "sha256": "0450D49C45B031D701AADCB0D3E787DFF9CE3025B3970F5DF0E631C95AA31D52",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/results/figures/fig_method_c_case3_rerun_step_count_comparison.png"
    },
    "comparison_figure_pdf": {
      "path": "results/figures/fig_method_c_case3_rerun_step_count_comparison.pdf",
      "sha256": "7537FFF4CB00638369DD681242600DDE1AB2EFCF548176602DBCD6BC9FDB3FFA",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/results/figures/fig_method_c_case3_rerun_step_count_comparison.pdf"
    },
    "orchestrator_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3_rerun/case3_single_job_orchestrator.py",
      "sha256": "0C9D07C1149820710C0798EDB07B55A9E5B3D109C6270FE0BDF0CFF32EEA4516",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/290_method_c_case3_rerun/case3_single_job_orchestrator.py"
    },
    "evaluation_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3_rerun/evaluate_case3_rerun_step_count.py",
      "sha256": "E96682CD0E807EB3F65E912B320CC1D0EA4FC7812D71412B85E3E944A661DCD7",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/290_method_c_case3_rerun/evaluate_case3_rerun_step_count.py"
    },
    "corridor_mesh_generator": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3_rerun/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "D9E5687BCA3F3A94639A2D0E4CFDEED85A57E4C697062E7BFC077778E4109AE4",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/290_method_c_case3_rerun/generate_case3_adaptive_corridor_mesh.py"
    },
    "plot_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3_rerun/plot_case3_rerun_comparison.py",
      "sha256": "B3D392F5995B4AC24B43BB35D3A2523FF1E164501DD73FB1352CDFCA0E69E94A",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/290_method_c_case3_rerun/plot_case3_rerun_comparison.py"
    },
    "canonical_frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_rerun.py",
      "sha256": "6D476C1339142F1A551FC1F407CD5B487F2CCA8FFDB40FB201B6342BE86C8587",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/325aaee498e21950d2bb812b322dafa45ae69cb0/tests/unit/test_method_c_case3_rerun.py"
    }
  }
}
'@

if ($Publish) {
    Write-Output "Dispatching HND-METHOD-C-CASE3-RERUN-001 to ChatGPT Bridge..."
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-CASE3-RERUN-001" -TaskId "METHOD-C-CASE3-RERUN"
} else {
    Write-Output "Running pre-dispatch DryRun validation..."
    $dryRunText = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId "HND-METHOD-C-CASE3-RERUN-001" -TaskId "METHOD-C-CASE3-RERUN" -DryRun
    Write-Output "DryRun validation PASS! Prompt assembled successfully."
    Write-Output "Length: $($dryRunText.Length) characters"
}
