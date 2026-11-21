# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_cycle0_003.ps1
# Dispatches Method C Case 3 Single-Job Framework Cycle-0 Report Observables Correction Re-Issue 3
# (HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-CYCLE0-REPORT-CORRECTION-003"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-003"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-002"

$cycle0ReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md"
if (-not (Test-Path $cycle0ReportPath)) {
    throw "Cycle 0 results report file not found at: $cycle0ReportPath"
}
$cycle0ReportSha = (Get-FileHash -Path $cycle0ReportPath -Algorithm SHA256).Hash.ToUpper()

$packageReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
$packageReportSha = (Get-FileHash -Path $packageReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$orchCopyPath = Join-Path $caseDir "case3_single_job_orchestrator.py"
$orchCopySha = (Get-FileHash -Path $orchCopyPath -Algorithm SHA256).Hash.ToUpper()

$stateJsonPath = Join-Path $caseDir "PK_METHOD_C_CASE3_COARSE_JOB1_state.json"
$stateJsonSha = (Get-FileHash -Path $stateJsonPath -Algorithm SHA256).Hash.ToUpper()

$summaryJsonPath = Join-Path $caseDir "PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json"
$summaryJsonSha = (Get-FileHash -Path $summaryJsonPath -Algorithm SHA256).Hash.ToUpper()

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_COARSE_JOB1.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()

$pbsLogPath = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_CYCLE0_pbs_execution.log"
$pbsLogSha = (Get-FileHash -Path $pbsLogPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Framework Cycle-0 Report Observables Correction Re-Issue 3 (CYCLE0-003)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md",
  "checkpoint_artifact_sha256": "$cycle0ReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_single_job_framework_build",
    "numerical_uncertainty": "Can the Cycle-0 report be corrected so its equilibrium-iteration count (256 total: Step-1 160, Step-2 96) and its terminal crack tip ((10.6727, 69.9342) mm at d>=0.95, 0.676 mm extension, forward crack growth demonstrated) match the committed .sta and SUMMARY.json, with the SUMMARY.json provenance and the Step-1 vs total fracture energy stated, so the Cycle-0 results are approved and the repaired framework is ready for its next test run?",
    "expected_numerical_result": "Cycle-0 report corrected: 256 total equilibrium iterations (Step-1 160, Step-2 96); terminal tip (10.6727, 69.9342) mm at d>=0.95 with 0.676 mm extension and forward crack growth demonstrated; SUMMARY.json stated as the Job-1 summary whose values the framework run reproduced; Step-1 fracture energy 0.003456 kN*mm distinguished from total 0.005743 kN*mm; offline tests PASS; 0 new PBS consumed; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "cycle0_results_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md",
      "sha256": "$cycle0ReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md"
    },
    "framework_package_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md",
      "sha256": "$packageReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "orchestrator_copy": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py",
      "sha256": "$orchCopySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py"
    },
    "cycle0_state_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_state.json",
      "sha256": "$stateJsonSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_state.json"
    },
    "cycle0_summary_json": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json",
      "sha256": "$summaryJsonSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json"
    },
    "cycle0_sta": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.sta",
      "sha256": "$staSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.sta"
    },
    "cycle0_pbs_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_CYCLE0_pbs_execution.log",
      "sha256": "$pbsLogSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_CYCLE0_pbs_execution.log"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_framework_package.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_framework_package.py",
      "tests_passed": 16,
      "tests_total": 16
    }
  },
  "review_resolution_matrix": {
    "EQUILIBRIUM_ITERATIONS_256": {
      "directive": "State Step-1 equilibrium iterations 160 (average 3.20 per increment), Step-2 equilibrium iterations 96, total 256, as established by the committed .sta and SUMMARY.json. Remove the false '148 (average 2.96)' figure.",
      "status": "RESOLVED",
      "implementation": "Corrected Section 1 and Section 3 of METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md. Step-1 equilibrium iterations stated as 160 (average 3.20 iterations/increment across 50 increments), Step-2 equilibrium iterations stated as 96 (across 13 increments), and total analysis equilibrium iterations stated as 256, fully matching committed .sta and SUMMARY.json. The false 148 figure has been excised."
    },
    "TERMINAL_CRACK_TIP_ADVANCE": {
      "directive": "State terminal tip as (10.6727, 69.9342) mm at d>=0.95 threshold, with final crack extension 0.676 mm from notch root and forward crack growth demonstrated. Remove false 'x_tip = 10.0 mm, y_tip = 70.0 mm' terminal tip and 'zero macroscopic crack advance' claim; label (10.0, 70.0) mm as Step-1 end frame tip.",
      "status": "RESOLVED",
      "implementation": "Corrected Section 1 and Section 3 of METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md. Clarified that (10.0, 70.0) mm is the Step-1 end frame tip where no node has reached d>=0.95 (maximum nodal damage d=0.4691 at u2=0.0500 mm). At the terminal converged state (Step 2 Inc 12, u2=0.056110 mm), peak damage reaches d_max=0.9970, and macroscopic crack tip advances to (10.6727, 69.9342) mm at d>=0.95, achieving 0.675954 mm (~0.676 mm) crack extension with forward crack growth demonstrated (forward_crack_growth_demonstrated=true per SUMMARY.json propagation_history frame 6)."
    },
    "NOTE-C0-02B1_SUMMARY_PROVENANCE": {
      "directive": "State in report that committed SUMMARY.json is Job-1 summary (job_id 1424711) whose values framework run reproduced, rather than presenting it as a 1424786 output.",
      "status": "RESOLVED",
      "implementation": "Added explicit provenance disclosure in Section 1 and Section 4.2 stating that PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json carries job_id 1424711.mmaster02 (original Job-1 summary), whose physical trajectory, reaction forces, peak load, increment history, and crack advance the framework test run (PBS 1424786.mmaster02) identically reproduced on the cluster (as verified from committed 1424786 .sta and pbs_execution.log), while state.json and .sta are genuine 1424786 artifacts."
    },
    "NOTE-C0-02B2_FRACTURE_ENERGY_PARTITIONING": {
      "directive": "State that state.json e_frac 0.003456 kN*mm is Step-1 portion, while total fracture energy is 0.005743 kN*mm.",
      "status": "RESOLVED",
      "implementation": "Documented in Section 1 and Section 3 that state.json e_frac = 0.003456 kN*mm represents the Step-1 absorbed fracture energy (capturing the pre-critical linear-elastic end frame at u2=0.0500 mm), while the total accumulated fracture energy across both loading steps is E_fracture = 0.005743 kN*mm (0.0057432253 kN*mm in SUMMARY.json)."
    },
    "UNIT_TESTS_ENHANCED": {
      "directive": "Re-run offline test suite (must PASS, 16/16 or more).",
      "status": "RESOLVED",
      "implementation": "Enhanced test_cycle0_run_artifacts_and_timing_reconciliation in tests/unit/test_method_c_case3_framework_package.py to assert total_equilibrium_iterations == 256, step1_equilibrium_iterations == 160, step2_equilibrium_iterations == 96, final_crack_tip_x_mm == 10.6727, final_crack_tip_y_mm == 69.9342, final_crack_extension_mm == 0.676, forward_crack_growth_demonstrated == True, and E_fracture_kNmm == 0.005743 directly from SUMMARY.json. All 16 unit tests PASS (100%) in 1.26 seconds."
    }
  },
  "accounting": {
    "previous_cumulative_pbs_submissions": 68,
    "new_pbs_consumed_this_milestone": 0,
    "current_cumulative_pbs_submissions": 68,
    "authorized_submissions_remaining": 0,
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Output "CHECK_ONLY: Verification complete. Prompt generated with Handoff ID: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Cycle 0 Results Report SHA: $cycle0ReportSha"
    return
}

Write-Output "Dispatching review request $handoffId via Invoke-ChatGPTBridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
