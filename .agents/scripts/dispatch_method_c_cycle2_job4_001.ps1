# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_cycle2_job4_001.ps1
# Dispatches Method C Cycle 2: Job-4 Re-Equilibration and Forward Propagation Solve Execution & Observables
# (HND-METHOD-C-CYCLE2-JOB4-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CYCLE2-JOB4-SOLVE"
$handoffId = "HND-METHOD-C-CYCLE2-JOB4-001"
$predecessorHandoffId = "HND-METHOD-C-CYCLE2-PREP-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$receiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_REFINED_JOB4.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$meshPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_CYCLE2_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$extractorPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\extract_job4_observables.py"
$extractorSha = (Get-FileHash -Path $extractorPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_cycle2_job4_execution.py"
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
  "title": "Method C Cycle 2: Job-4 Re-Equilibration and Forward Propagation Solve Execution & Observables Verification",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_cycle2_remesh_transfer_propagate",
    "numerical_uncertainty": "Can the Job-4 solve on the adapted Cycle-2 receiver mesh (14,004 elements, 42,012 layered elements) successfully re-equilibrate the transferred state and extreme history (4629.69 MPa) at u2 = 0.008756 mm without spurious crack wake healing, and demonstrate forward crack tip propagation from the far hole boundary (x_tip = 0.8957 mm) across the second remaining ligament toward the right plate boundary?",
    "expected_numerical_result": "PBS Job 1424700.mmaster02 completed with 29 converged increments in 394s solver walltime (Exit 1 cutback termination during rapid localized dynamic crack propagation); macroscopic crack tip advances forward from x_tip = 0.895686 mm to 0.920247 mm (Delta x = +24.56 um across second ligament, total crack extension Delta a = 0.420247 mm from initial notch); pre-existing crack wake damage preserved strictly at d_max = 1.002061 (zero healing verified); transferred extreme history preserved identically at H_max = 4629.688965 MPa; structural peak load of second ligament captured at F_max = 0.167641 kN (u2 = 0.006495 mm) with post-peak softening to 0.160389 kN; dissipated fracture energy grew from 1.562855e-3 to 1.632072e-3 kN*mm (+4.43%); 41/41 unit tests PASS (100%); exactly 1 new PBS job consumed (cumulative 61); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CYCLE2_JOB4_EXECUTION_REPORT.md"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json",
      "sha256": "$receiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_RECEIPT.json",
      "job_id": "1424700.mmaster02",
      "exit_code": 1,
      "status": "CUTBACK_TERMINATION",
      "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
      "solver_walltime_s": 394.0,
      "solver_cpu_s": 473.0,
      "total_increments": 29,
      "step1_increments": 29,
      "step2_increments": 0,
      "step1_end_RF2_kN": 0.160389,
      "step1_end_u2_mm": 0.006525,
      "peak_RF2_kN": 0.167641,
      "u2_at_peak_RF2_mm": 0.006495,
      "peak_damage_SDV1": 1.002061,
      "damage_preserved_no_healing": true,
      "peak_history_SDV2_MPa": 4629.688965,
      "initial_crack_tip_x_mm": 0.895686,
      "final_crack_tip_x_mm": 0.920247,
      "crack_tip_advance_delta_x_um": 24.561,
      "final_crack_extension_mm": 0.420247,
      "hole_passed": true,
      "right_boundary_reached": false,
      "specimen_completely_severed": false,
      "E_fracture_kNmm": 0.001632072,
      "E_total_kNmm": 0.002155364
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json",
      "sha256": "$summarySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4_SUMMARY.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_REFINED_JOB4.inp"
    },
    "receiver_physical_mesh": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp",
      "sha256": "$meshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_CYCLE2_PHYS.inp"
    },
    "extractor_script": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/extract_job4_observables.py",
      "sha256": "$extractorSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/extract_job4_observables.py"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_cycle2_job4_execution.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_cycle2_job4_execution.py"
    }
  },
  "execution_metrics": {
    "pbs_job_id": "1424700.mmaster02",
    "pbs_job_name": "PK_METHOD_C_CYCLE2_REFINED_JOB4",
    "solver_exit_code": 1,
    "termination_status": "CUTBACK_TERMINATION",
    "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
    "solver_walltime_s": 394.0,
    "solver_cpu_s": 473.0,
    "physical_elements_count": 14004,
    "layered_elements_count": 42012,
    "nodes_count": 14011,
    "total_increments": 29,
    "total_cutbacks": 12,
    "total_equilibrium_iterations": 142,
    "step1_increments": 29,
    "step1_end_u2_mm": 0.006525,
    "step1_end_RF2_kN": 0.160389,
    "peak_RF2_kN": 0.167641,
    "u2_at_peak_RF2_mm": 0.006495,
    "second_ligament_peak_load_captured": true,
    "second_ligament_softening_demonstrated": true,
    "peak_damage_SDV1": 1.002061,
    "damage_preserved_no_healing": true,
    "peak_history_SDV2_MPa": 4629.688965,
    "history_extreme_preserved": true,
    "initial_crack_tip_x_mm": 0.895686,
    "final_crack_tip_x_mm": 0.920247,
    "crack_tip_advance_delta_x_um": 24.561,
    "final_crack_extension_mm": 0.420247,
    "forward_crack_growth_demonstrated": true,
    "hole_passed": true,
    "right_boundary_reached": false,
    "specimen_completely_severed": false,
    "E_elastic_kNmm": 0.000523292,
    "E_fracture_kNmm": 0.001632072,
    "E_total_kNmm": 0.002155364,
    "fracture_energy_growth_pct": 4.4288,
    "new_pbs_jobs_consumed": 1,
    "cumulative_pbs_jobs_consumed": 61,
    "master_goal_status": "OPEN",
    "unit_tests_pass_rate": "41/41 (100%)"
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
