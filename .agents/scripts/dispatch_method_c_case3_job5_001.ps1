# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_job5_001.ps1
# Dispatches Method C Case 3 Cycle-4 Job-5 Refined Re-Equilibration and Forward Crack Propagation Solve
# (HND-METHOD-C-CASE3-JOB5-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-CYCLE4-JOB5-SOLVE"
$handoffId = "HND-METHOD-C-CASE3-JOB5-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-CYCLE4-PREP-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$spatialPath = Join-Path $caseDir "job5_spatial_crack.json"
$spatialSha = (Get-FileHash -Path $spatialPath -Algorithm SHA256).Hash.ToUpper()

$obsPath = Join-Path $caseDir "job5_observables.json"
$obsSha = (Get-FileHash -Path $obsPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job5_execution.py"
$testSha = (Get-FileHash -Path $testPath -Algorithm SHA256).Hash.ToUpper()

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()

$msgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.msg"
$msgSha = (Get-FileHash -Path $msgPath -Algorithm SHA256).Hash.ToUpper()

$datPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.dat"
$datSha = (Get-FileHash -Path $datPath -Algorithm SHA256).Hash.ToUpper()

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_pbs_execution.log"
$logSha = (Get-FileHash -Path $logPath -Algorithm SHA256).Hash.ToUpper()

$csvPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_uel_energy_balance.csv"
$csvSha = (Get-FileHash -Path $csvPath -Algorithm SHA256).Hash.ToUpper()

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Case 3 Cycle-4 Job-5 Refined Re-Equilibration and Forward Crack Propagation Solve Execution & Observables Verification",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_cycle4_job5_solve",
    "numerical_uncertainty": "Can the Cycle-4 adapted mesh (64,653 physical / 193,959 layered elements) with benchmark Gc = 0.00228 kN/mm preserve fixed-load re-equilibration force continuity within <= 5% vs donor Job 4 (RF2=3.9063646 kN, E_frac=0.015924724 kN*mm), maintain strict non-healing (d_max >= 0.99), demonstrate forward crack propagation past the donor tip x=13.1118 mm toward the central circular void (x=26.5 mm), and capture structural peak load with post-peak softening?",
    "expected_numerical_result": "PBS Job 1424783.mmaster02 completed 12 total converged increments (1 in Step 1, 11 in Step 2) in 678s scheduler walltime (11m 18s) / 1,893s CPU (~31m 33s) [solver wallclock 391s / CPU 1,880s] on 16 CPUs SMP. Step-1 re-equilibration force continuity passed at -0.9501% (RF2 = 3.8692487 kN vs donor 3.9063646 kN, <= 5.0% gate PASS). Initial Step-1 hold displacement u2 = 0.056835 mm converged in 1 increment and 2 Newton iterations with terminal residual -3.358e-13; crack tip during hold settled at x = 13.2105 mm (GROWTH_UNDER_HOLD). Peak structural load F_max = 3.8997762 kN captured at Inc 1 (u2 = 0.05754633 mm) followed by post-peak softening down to 3.7412223 kN at Inc 11 (-4.0657% load drop). Macroscopic crack tip (d >= 0.95) advanced forward to x = 14.1848 mm (+1.0730 mm forward advance past Job-4 donor tip x = 13.1118 mm; total crack extension from notch root Delta a_x = +4.1848 mm). Damage envelope (d >= 0.50) advanced to x = 14.748 mm, heading directly toward the central void at x = 26.5 mm (distance to hole perimeter reduced to 19.1185 mm, hole_penetrated = False). Dissipated fracture energy surged +25.78% (0.014849 -> 0.018677 kN*mm). Elastic strain energy unloaded from peak 0.112209 to 0.107739 kN*mm. Strict non-healing verified (peak damage monotonically reached d_max = 1.001932 >= 0.99). Cutbacks resolved down to dt = 6.993e-14 before hitting the 1.0e-14 floor at Inc 12. 5/5 dedicated unit tests PASS (100%). Exactly 1 new PBS job consumed (cumulative 67, concluding the Fix Option A 5-job budget 62 to 67); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md"
    },
    "solver_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_RECEIPT.json",
      "sha256": "$receiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_RECEIPT.json"
    },
    "solver_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_SUMMARY.json",
      "sha256": "$summarySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_SUMMARY.json"
    },
    "spatial_crack_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job5_spatial_crack.json",
      "sha256": "$spatialSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job5_spatial_crack.json"
    },
    "observables_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job5_observables.json",
      "sha256": "$obsSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job5_observables.json"
    },
    "refined_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp"
    },
    "physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp",
      "sha256": "$meshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
    },
    "solver_sta": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.sta",
      "sha256": "$staSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.sta"
    },
    "solver_msg": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.msg",
      "sha256": "$msgSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.msg"
    },
    "solver_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.dat",
      "sha256": "$datSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.dat"
    },
    "pbs_execution_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_pbs_execution.log",
      "sha256": "$logSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_pbs_execution.log"
    },
    "uel_energy_balance_csv": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_uel_energy_balance.csv",
      "sha256": "$csvSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_uel_energy_balance.csv"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_job5_execution.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job5_execution.py"
    }
  },
  "observables_summary": {
    "pbs_job_id": "1424783.mmaster02",
    "solver_wallclock_s": 391.0,
    "solver_cpu_time_s": 1880.0,
    "scheduler_walltime_s": 678.0,
    "step1_hold_displacement_mm": 0.056835,
    "step1_re_equilibrated_RF2_kN": 3.8692487,
    "donor_RF2_kN": 3.9063646,
    "step1_force_continuity_delta_pct": -0.950139,
    "step1_force_continuity_pass": true,
    "step1_re_equilibrated_E_frac_kNmm": 0.014849132,
    "donor_E_frac_kNmm": 0.015924724,
    "step1_energy_continuity_delta_pct": -6.754227,
    "step1_energy_continuity_pass": true,
    "step2_converged_increments": 11,
    "total_converged_increments": 12,
    "peak_structural_load_RF2_kN": 3.8997762,
    "displacement_at_peak_u2_mm": 0.05754633,
    "terminal_converged_RF2_kN": 3.7412223,
    "terminal_displacement_u2_mm": 0.057595387,
    "post_peak_softening_drop_pct": -4.065718,
    "donor_crack_tip_x_mm": 13.1118,
    "step1_hold_crack_tip_x_mm": 13.210456,
    "terminal_crack_tip_x_d095_mm": 14.184816,
    "forward_crack_advance_past_donor_mm": 1.073016,
    "forward_crack_advance_past_hold_mm": 0.974360,
    "total_crack_extension_from_notch_root_mm": 4.184816,
    "damage_envelope_tip_x_d050_mm": 14.747970,
    "distance_to_hole_perimeter_mm": 19.118543,
    "hole_penetrated": false,
    "initial_fracture_energy_kNmm": 0.014849132,
    "terminal_fracture_energy_kNmm": 0.018677283,
    "fracture_energy_growth_pct": 25.780302,
    "peak_elastic_strain_energy_kNmm": 0.11220891,
    "terminal_elastic_strain_energy_kNmm": 0.10773857,
    "terminal_peak_damage": 1.001932,
    "zero_healing_verified": true,
    "cutback_floor_dt_min": 1e-14,
    "smallest_converged_dt": 6.993e-14,
    "cumulative_pbs_submissions": 67,
    "unit_tests_passed": "5/5 (100%)",
    "budget_status": "5-job budget 62-67 100% committed (Job 5 is final job)"
  }
}
"@

if ($CheckOnly) {
    Write-Host "CHECK_ONLY: Prompt prepared successfully for $handoffId."
    Write-Host "Report SHA: $reportSha"
    Write-Host "Prompt length: $($prompt.Length) chars"
    return
}

Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
