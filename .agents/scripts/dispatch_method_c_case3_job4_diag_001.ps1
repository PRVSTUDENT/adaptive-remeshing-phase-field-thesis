# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_job4_diag_001.ps1
# Dispatches Method C Case 3 Job-4 Failure Diagnosis and Multi-Cycle Progression Report
# (HND-METHOD-C-CASE3-JOB4-DIAG-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-JOB4-DIAGNOSIS"
$handoffId = "HND-METHOD-C-CASE3-JOB4-DIAG-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-JOB4-001"

$diagReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md"
if (-not (Test-Path $diagReportPath)) {
    throw "Diagnosis report file not found at: $diagReportPath"
}
$diagReportSha = (Get-FileHash -Path $diagReportPath -Algorithm SHA256).Hash.ToUpper()

$execReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB4_EXECUTION_REPORT.md"
$execReportSha = (Get-FileHash -Path $execReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$spatialPath = Join-Path $caseDir "job4_spatial_crack.json"
$spatialSha = (Get-FileHash -Path $spatialPath -Algorithm SHA256).Hash.ToUpper()

$obsPath = Join-Path $caseDir "job4_observables.json"
$obsSha = (Get-FileHash -Path $obsPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$diagTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job4_diagnosis.py"
$diagTestSha = (Get-FileHash -Path $diagTestPath -Algorithm SHA256).Hash.ToUpper()

$execTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job4_execution.py"
$execTestSha = (Get-FileHash -Path $execTestPath -Algorithm SHA256).Hash.ToUpper()

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()

$msgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.msg"
$msgSha = (Get-FileHash -Path $msgPath -Algorithm SHA256).Hash.ToUpper()

$datPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.dat"
$datSha = (Get-FileHash -Path $datPath -Algorithm SHA256).Hash.ToUpper()

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_pbs_execution.log"
$logSha = (Get-FileHash -Path $logPath -Algorithm SHA256).Hash.ToUpper()

$csvPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_uel_energy_balance.csv"
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
  "title": "Method C Case 3: Job-4 Failure Diagnosis and Multi-Cycle Progression Report",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md",
  "checkpoint_artifact_sha256": "$diagReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job4_diagnosis",
    "numerical_uncertainty": "Can the Job-4 diagnosis be re-issued with the section 2 comparison table corrected from the committed Job-1/Job-2 .dat files and the Cycle-3 audit (Job-1 242 s / 290 s, Job-2 152 s / 489 s, Job-4 97.16% quads), the Step-1 terminal residual corrected to -3.125e-13 at node 11385 DOF 2, the terminal frame relabelled Increment 11 in both JSON artifacts, the Increment-12 failure mechanism diagnosed with node coordinates, and the non-healing wording corrected, with 0 new PBS jobs consumed?",
    "expected_numerical_result": "Diagnosis re-issue HND-METHOD-C-CASE3-JOB4-DIAG-001 with corrected section 2 values, corrected Step-1 residual, relabelled terminal frame, diagnosed Increment-12 mechanism (nodes 22165/21774/4275/22412/22792, 0.18-0.45 mm ahead of the terminal tip), corrected non-healing wording and manifest node count 61,106, 0 new PBS jobs consumed (cumulative 66 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "diagnosis_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md",
      "sha256": "$diagReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md"
    },
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB4_EXECUTION_REPORT.md",
      "sha256": "$execReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB4_EXECUTION_REPORT.md"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_RECEIPT.json",
      "sha256": "$receiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_RECEIPT.json",
      "job_id": "1424780.mmaster02",
      "exit_code": 1,
      "status": "CUTBACK_TERMINATION",
      "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
      "total_increments": 12,
      "step1_increments": 1,
      "step2_increments": 11,
      "step1_init_RF2_kN": 3.9360855,
      "step1_donor_RF2_kN": 3.9475231,
      "step1_init_force_continuity_delta_pct": -0.289741,
      "step1_init_force_continuity_pass": true,
      "step1_init_E_frac_kNmm": 0.01388297,
      "step1_donor_E_frac_kNmm": 0.013756,
      "step1_init_energy_continuity_delta_pct": 0.923015,
      "step1_init_energy_continuity_pass": true,
      "step1_terminal_residual": -3.125e-13,
      "step1_terminal_residual_node": 11385,
      "step1_terminal_residual_dof": 2,
      "peak_RF2_kN": 3.9760374,
      "u2_at_peak_RF2_mm": 0.056785854,
      "terminal_RF2_kN": 3.9063646,
      "terminal_u2_mm": 0.056835016,
      "terminal_frame_label": "Increment 11 (terminal converged state)",
      "initial_crack_tip_x_mm_d095": 12.5215,
      "terminal_crack_tip_x_mm_d095": 13.111840,
      "forward_crack_advance_mm_d095": 0.590340,
      "total_crack_extension_mm_d095": 3.111840,
      "terminal_peak_damage": 1.001953,
      "transferred_peak_damage": 0.989946,
      "zero_healing_verified_relative_to_donor": true
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_SUMMARY.json",
      "sha256": "$summarySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_SUMMARY.json"
    },
    "spatial_crack_metrics": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job4_spatial_crack.json",
      "sha256": "$spatialSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job4_spatial_crack.json",
      "terminal_frame_description": "Increment 11 (terminal converged state)"
    },
    "frame_observables": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job4_observables.json",
      "sha256": "$obsSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job4_observables.json",
      "terminal_frame_description": "Increment 11 (terminal converged state)"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp"
    },
    "adapted_receiver_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp",
      "sha256": "$meshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp",
      "physical_elements": 61688,
      "quad_elements": 59936,
      "tri_elements": 1752,
      "quad_fraction_pct": 97.16,
      "physical_nodes": 61106,
      "reference_nodes": 1,
      "total_nodes": 61107
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "solver_text_outputs": {
      "sta_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.sta",
        "sha256": "$staSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.sta"
      },
      "msg_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.msg",
        "sha256": "$msgSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.msg"
      },
      "dat_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.dat",
        "sha256": "$datSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.dat"
      },
      "pbs_execution_log": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_pbs_execution.log",
        "sha256": "$logSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_pbs_execution.log"
      },
      "uel_energy_balance_csv": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_uel_energy_balance.csv",
        "sha256": "$csvSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_uel_energy_balance.csv"
      }
    },
    "diagnosis_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job4_diagnosis.py",
      "sha256": "$diagTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job4_diagnosis.py",
      "tests_passed": 6,
      "total_tests": 6
    },
    "execution_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job4_execution.py",
      "sha256": "$execTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job4_execution.py",
      "tests_passed": 5,
      "total_tests": 5
    }
  },
  "review_gaps_resolution": {
    "GAP-MC-C3J4-01": "RESOLVED: Corrected report §2 comparison table cells with authentic values and exact file/SHA citations. Job-1 solver wallclock 242 s and CPU 290 s cited to committed .dat SHA C4C2D56B (lines 2183-2184); PBS span 390 s. Job-2 solver wallclock 152 s and CPU 489 s cited to committed .dat SHA 39C1A89F (lines 758-759) and PBS span 254 s from ledger. Job-4 quad fraction 97.16% (59,936/61,688) cited to committed mesh audit SHA 1620F4F6.",
    "GAP-MC-C3J4-02": "RESOLVED: Corrected Step-1 terminal residual to -3.125e-13 at node 11385 DOF 2 in sections 1.1 and 3.1 of execution report and diagnosis report (.msg line 176, THE FORCE EQUILIBRIUM EQUATIONS HAVE CONVERGED).",
    "GAP-MC-C3J4-03": "RESOLVED: In job4_observables.json and job4_spatial_crack.json Step-2 frame 3, relabelled description from 'Increment 12' to 'Increment 11 (terminal converged state)'. Both files re-committed with verified updated SHAs.",
    "GAP-MC-C3J4-04": "RESOLVED: Increment-12 cutback mechanism forensically diagnosed with failing nodes (21774, 22165, 4275, 22412, 22792) and physical coordinates in §3. All 5 nodes lie 0.17 to 0.45 mm directly ahead of the macroscopic tip (xtip = 13.1118 mm) in the active softening process zone. In Attempt 3, residual decreased across Iterations 1-3 then rebounded at Iteration 4 (+3.636e-3 DOF 2), triggering divergence and cutback to floor. Confirmed Cycle 4 proceeds as a pure adaptive remeshing cycle from the converged Increment-11 donor state with 0 new PBS jobs consumed for diagnosis and 1 PBS job for Cycle-4 solve within cumulative 67 limit.",
    "GAP-MC-C3J4-05": "RESOLVED: Corrected non-healing wording: non-healing is verified relative to the transferred state (terminal d_max = 1.001953 >= transferred 0.989946); the 0.05% shift from peak hold (1.002508 -> 1.001953) is numerical redistribution/relaxation of the overshoot above 1.0, with zero material healing. Fixed test docstring point 6.",
    "GAP-MC-C3J4-06": "RESOLVED: Corrected manifest node count to 61,106 physical nodes (61,107 with N_RP). Preserved ACTIVE_TASK last_successful_pbs_job_id at 1424778.mmaster02, noting 1424780 as cutback-terminated."
  },
  "accounting_audit": {
    "max_new_pbs_submissions": 0,
    "submissions_consumed": 0,
    "cumulative_pbs_submissions": 66,
    "budget_status": "Fix Option A 5-job allocation: cumulative 62 to 67; 1 job remaining for Cycle-4 solve",
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Output "CHECK_ONLY: Verification complete. Prompt generated with Handoff ID: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Diagnosis Report SHA: $diagReportSha"
    return
}

Write-Output "Dispatching review request $handoffId via Invoke-ChatGPTBridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
