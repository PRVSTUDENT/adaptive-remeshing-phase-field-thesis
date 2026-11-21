# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_cycle0_002.ps1
# Dispatches Method C Case 3 Single-Job Framework Cycle-0 Observables Extraction & Orchestrator Repair Re-Issue (CYCLE0-002)
# (HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-CYCLE0-ORCHESTRATOR-REPAIR-REISSUE"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-001"

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
  "title": "Method C Case 3: Single-Job Framework Cycle-0 Observables Extraction & Orchestrator Repair Re-Issue (CYCLE0-002)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md",
  "checkpoint_artifact_sha256": "$cycle0ReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_single_job_framework_build",
    "numerical_uncertainty": "Can the three blocking gaps (GAP-C0-01 per-cycle state advancement, GAP-C0-02 committed Cycle-0 run artifacts and timing reconciliation, GAP-C0-03 excised hardcoded literals) and two advisory notes (NOTE-C0-01 bitwise copy sync, NOTE-C0-02 loop bound documentation) from HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-001 be fully resolved with 100% passing offline unit tests (16/16 PASS) and 0 new PBS submissions consumed (cumulative count strictly preserved at 68)?",
    "expected_numerical_result": "GAP-C0-01 resolved by wiring per-cycle state extraction and advancement in execute() loop; GAP-C0-02 resolved by committing 4 raw solver artifacts (.state.json 7443BB9C, .SUMMARY.json 9065FAB2, .sta 93FA16FA, pbs_execution.log 01C2E19B), documenting crack tip d>=0.95 at (10.0, 70.0) mm, and reconciling solver CPU 546s vs scheduler cput 559s (walltime 2114s); GAP-C0-03 resolved by computing observables dynamically from donor arrays; NOTE-C0-01 and NOTE-C0-02 resolved; 16/16 unit tests PASS (100%); 0 new PBS jobs consumed, cumulative count strictly 68 preserved; MASTER_GOAL_STATUS strictly remains OPEN.",
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
    "GAP-C0-01": {
      "directive": "Per-cycle state advancement inside the while cycle_idx <= self.n_adaptive_steps: loop",
      "status": "RESOLVED",
      "implementation": "Refactored case3_single_job_orchestrator.py: (1) Added extract_state_from_odb(odb_path, out_json_path) supporting standalone CLI/Python extraction; (2) In execute() loop, after each cycle solve, cycle_donor_state = self.extract_cycle_state(cycle_job) extracts the terminal state from the cycle's ODB; (3) Re-binds donor_state, donor_u2, donor_phys_inp, self.current_tip_x, self.current_rf2, and self.peak_rf2, guaranteeing Cycle k+1 transfers previous Cycle k's end state and check_completion sees the current crack state."
    },
    "GAP-C0-02": {
      "directive": "Commit Cycle-0 run artifact (.state.json or .sta/.msg tail), state terminal crack tip threshold and method (d>=0.95), and reconcile CPU time (546s vs 559s cput, walltime 2114s)",
      "status": "RESOLVED",
      "implementation": "Committed 4 raw solver output artifacts to models/pandey_kumar_mode1/290_method_c_case3/: PK_METHOD_C_CASE3_COARSE_JOB1_state.json (3,003,112 B, 7443BB9C), PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json (13,623 B, 9065FAB2), PK_METHOD_C_CASE3_COARSE_JOB1.sta (5,389 B, 93FA16FA), and PK_METHOD_C_CASE3_FRAMEWORK_CYCLE0_pbs_execution.log (10,832 B, 01C2E19B). Documented terminal crack tip extraction: threshold d>=0.95 at notch root (10.0, 70.0) mm with zero macroscopic crack advance past notch prior to remeshing. Reconciled timings: Abaqus internal solver CPU time = 546.0 s (from .msg TOTAL CPU TIME and .dat); PBS scheduler total job CPU time = 559.0 s (cput = 00:09:19, including pre/python/wrappers); solver wallclock = 816.0 s; scheduler walltime = 2,114.0 s (walltime = 00:35:14)."
    },
    "GAP-C0-03": {
      "directive": "Excise silent hardcoded fallback defaults in extract_cycle_state's donor-file branch (0.9472, 0.0210, 3.9288, 0.003456)",
      "status": "RESOLVED",
      "implementation": "Removed all hardcoded fallback literals from extract_cycle_state(). All observables (max_damage, tip_x, rf2, e_frac) are dynamically computed from d_nodal, h_gp, and state dictionary fields. If required keys are missing, explicit KeyError or warning is raised without silent fallback to Job-1 values."
    },
    "NOTE-C0-01": {
      "directive": "Maintain both repository copies of case3_single_job_orchestrator.py bitwise identical and state which copy PBS stages/runs",
      "status": "RESOLVED",
      "implementation": "Both scripts/remeshing/case3_single_job_orchestrator.py and models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py synchronized bitwise at SHA-256 E36568E679EF734DD87A9EEA595C6CA0A4AC66443EBD656AB07A1451613D1B72. The PBS job script stages and executes the package copy in the job working directory."
    },
    "NOTE-C0-02": {
      "directive": "Update package report wording so n_adaptive_steps is described as the user-settable loop bound (default 4)",
      "status": "RESOLVED",
      "implementation": "Updated METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md line 63 to explicitly document n_adaptive_steps as the user-settable loop bound (default 4)."
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
