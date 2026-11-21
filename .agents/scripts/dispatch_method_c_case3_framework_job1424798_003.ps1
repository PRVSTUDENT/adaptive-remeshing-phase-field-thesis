# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_job1424798_003.ps1
# Dispatches Method C Case 3 Single-Job Framework Job 1424798 Execution Observables & Completion Report
# (HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-JOB1424798-COMPLETION-REPORT"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-003"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$log1424798Path = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log"
$log1424798Sha = (Get-FileHash -Path $log1424798Path -Algorithm SHA256).Hash.ToUpper()

$log1424797Path = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log"
$log1424797Sha = (Get-FileHash -Path $log1424797Path -Algorithm SHA256).Hash.ToUpper()

$energyCsvPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1_uel_energy_balance.csv"
$energyCsvSha = (Get-FileHash -Path $energyCsvPath -Algorithm SHA256).Hash.ToUpper()

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()

$msgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1.msg"
$msgSha = (Get-FileHash -Path $msgPath -Algorithm SHA256).Hash.ToUpper()

$datPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1.dat"
$datSha = (Get-FileHash -Path $datPath -Algorithm SHA256).Hash.ToUpper()

$summaryJsonPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1_SUMMARY.json"
$summaryJsonSha = (Get-FileHash -Path $summaryJsonPath -Algorithm SHA256).Hash.ToUpper()

$stateJsonPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1_state.json"
$stateJsonSha = (Get-FileHash -Path $stateJsonPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$c1MeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1_PHYS.inp"
$c1MeshSha = (Get-FileHash -Path $c1MeshPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Framework Job 1424798 Execution & Completion Observables Report (Final)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "Are all Cycle 1 observables of single-job framework PBS Job 1424798 verified against authentic committed solver outputs (force continuity <= 5%, crack tip extension, post-peak load softening, non-healing monotonic fracture energy growth), is the exit diagnostic at Cycle 2 setup fully resolved, and is the framework verified for proceeding under 0 new PBS?",
    "expected_numerical_result": "Approval of Job 1424798 final execution observables report; confirmation that Step 1 passed at -0.3912% force continuity, Step 2 converged 43 increments with +889.51% fracture energy growth and -13.17% load softening, crack tip extended +2.4246 mm into the plate heading toward the hole, exit diagnostic on OdbRepository.get() resolved with bitwise-synchronized orchestrator DF22D89B...; 24/24 unit tests PASS; 0 new PBS (cumulative stays 70); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "job1424798_execution_observables": {
    "pbs_job_id": "1424798.mmaster02",
    "execution_host": "mnode105.cluster",
    "scheduler_walltime": "03:55:19 (14,119 s)",
    "scheduler_cput": "03:54:20 (14,060 s)",
    "solver_wallclock_s": 1477.0,
    "solver_cpu_s": 1810.0,
    "step1_hold_u2_mm": 0.0500,
    "step1_re_equilibrated_rf2_kN": 3.9134287,
    "step1_donor_rf2_kN": 3.928812,
    "step1_force_discrepancy_pct": -0.3912,
    "step1_force_gate_passed": true,
    "step2_converged_increments": 43,
    "step2_peak_force_kN": 3.9085787,
    "step2_terminal_force_kN": 3.3939536,
    "step2_softening_load_drop_pct": -13.1664,
    "step2_terminal_displacement_u2_mm": 0.051056558,
    "fracture_energy_initial_kNmm": 0.0016952324,
    "fracture_energy_terminal_kNmm": 0.016774466,
    "fracture_energy_surge_pct": 889.51,
    "strict_non_healing_verified": true,
    "elastic_energy_unloading_pct": -11.71,
    "terminal_crack_tip_x_mm": 12.424576759338379,
    "terminal_crack_tip_y_mm": 69.88233947753906,
    "net_crack_extension_mm": 2.424576759338379,
    "crack_trajectory_direction": "Heading forward and deflecting downward toward circular void at (26.5, 51.0) mm",
    "max_damage": 0.9905491471290588,
    "max_history_MPa": 14.96583080291748,
    "receiver_mesh_elements": 7172,
    "receiver_mesh_quad_fraction_pct": 96.14
  },
  "forensic_diagnosis_and_remediation": {
    "exit_code": 1,
    "terminal_event": "Cycle 1 solve converged 43 increments and hit dt_min=1e-14 cutback floor as designed. During post-solve state extraction, 'abaqus python case3_single_job_orchestrator.py --extract-odb ...' crashed on line 75 with AttributeError: 'Repository' object has no attribute 'get' because Abaqus Python 2.7 OdbRepository lacks .get(). Consequently, PK_METHOD_C_CASE3_CYCLE1_state.json was not written, orchestrator fell back to coarse Job 1 donor (4,813 nodes), and Cycle 2 setup crashed with KeyError: 5617 on receiver node 5617.",
    "remediation": "Replaced .get() calls with conditional lookups ('U' in last_frame.fieldOutputs), mapped element labels for 3-layer UEL models back to physical range ((eid - 1) % num_phys + 1), derived dynamic tip coordinates from nodes with d >= 0.95, and restricted donor candidates for Cycle k >= 1 strictly to own cycle state (failing closed). Bitwise-synchronized orchestrator DF22D89B... re-deployed to scratch."
  },
  "evidence_manifest": {
    "report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
    },
    "job1424798_pbs_execution_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log",
      "sha256": "$log1424798Sha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log"
    },
    "predecessor_1424797_pbs_execution_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log",
      "sha256": "$log1424797Sha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log"
    },
    "cycle1_uel_energy_balance_csv": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_uel_energy_balance.csv",
      "sha256": "$energyCsvSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_uel_energy_balance.csv"
    },
    "cycle1_sta": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.sta",
      "sha256": "$staSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.sta"
    },
    "cycle1_msg": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.msg",
      "sha256": "$msgSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.msg"
    },
    "cycle1_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.dat",
      "sha256": "$datSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1.dat"
    },
    "cycle1_summary_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_SUMMARY.json",
      "sha256": "$summaryJsonSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_SUMMARY.json"
    },
    "cycle1_state_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_state.json",
      "sha256": "$stateJsonSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_state.json"
    },
    "orchestrator": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "cycle1_narrow_band_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp",
      "sha256": "$c1MeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp"
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
  "accounting_and_bounds": {
    "cumulative_pbs_submissions": 70,
    "new_pbs_submissions_in_this_step": 0,
    "scratch_directory_status": "BITWISE_SYNCHRONIZED_WITH_REPO",
    "job_evaluated": "1424798.mmaster02"
  },
  "next_step": {
    "requested_decision": "APPROVE_FINAL_EXECUTION_REPORT",
    "proposed_action": "Approve Job 1424798 final execution report. Proceed to update n_adaptive_steps to the user-directed high safety cap (uncapped loop) and submit the next single-job run to complete the crack propagation sequence through to the hole.",
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
    return
}

if ($DryRun) {
    Write-Host "DRY RUN: Testing bridge validation"
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun
    return
}

Write-Host "DISPATCHING: Sending $handoffId across bridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId
