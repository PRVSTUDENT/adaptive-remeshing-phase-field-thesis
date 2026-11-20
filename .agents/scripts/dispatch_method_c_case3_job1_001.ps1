# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_job1_001.ps1
# Dispatches Method C Case 3 Job-1 Coarse Baseline Solve Submission & Preflight Qualification
# (HND-METHOD-C-CASE3-JOB1-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-JOB1-COARSE-SOLVE"
$handoffId = "HND-METHOD-C-CASE3-JOB1-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-PREP-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB1_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()
$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Case 3: Job-1 Coarse Baseline Solve Submission and Preflight Qualification",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB1_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job1_coarse_solve",
    "numerical_uncertainty": "Can the Case 3 Job-1 coarse baseline solve (14,013 layered elements, Step 1 precritical to 0.05 mm, Step 2 forward propagation to 0.4125 mm under PIN_HOLE_PULL) be qualified via cluster datacheck and submitted to PBS, yielding authentic execution receipts and a staged extractor for the damaged donor state?",
    "expected_numerical_result": "Job-1 submitted (max 1 PBS job, cumulative 62 -> 63); cluster datacheck Exit 0 verified; PBS receipt 1424711.mmaster02 recorded in normal_imfdfkmq with 16 CPUs SMP / 48 GB / 72 h; observables extractor staged on cluster; 51/51 unit tests PASS; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB1_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB1_EXECUTION_REPORT.md"
    },
    "authorization_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_JOB1_AUTHORIZATION.json",
      "sha256": "03B7F59919448FFC221B2FF5E622CA11A368E782E2DB25FF4536AD18E6D90D00",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_JOB1_AUTHORIZATION.json"
    },
    "pbs_job_receipt": {
      "job_id": "1424711.mmaster02",
      "job_name": "M1_MC_C3_JOB1",
      "scratch_dir": "/scratch9/pr21vyci/runs/mode1_290_method_c_case3",
      "queue": "normal_imfdfkmq",
      "resources": "16 CPUs SMP, 48 GB RAM, 72:00:00 walltime",
      "deck": "PK_METHOD_C_CASE3_COARSE_JOB1.inp (14,013 layered elements)",
      "deck_sha256": "1B3C9A62A9644E1E9FD6E8F4AD4B2DC734D69688D80E2655B0A11F8A7A7BDDC2",
      "physical_mesh": "PK_METHOD_C_CASE3_COARSE_PHYS.inp (4,671 elements, 96.85% quads)",
      "physical_mesh_sha256": "29AF8622A20C006F31B488CCED8E0C054749CB243ACB0F2B2D9CBEF35067CCDD",
      "pbs_script": "submit_case3_coarse_job1.pbs",
      "pbs_sha256": "EB53F43543DD576807642EE775628BB862D9CEC9BCC23B87143C605891F3E6D4",
      "submission_timestamp": "2026-11-20T06:39:47Z"
    },
    "technical_datacheck": {
      "datacheck_file": "PK_METHOD_C_CASE3_COARSE_JOB1_DC.dat",
      "datacheck_status": "ANALYSIS DATACHECK COMPLETE, 0 errors, 0 syntax violations",
      "compiler": "Intel Fortran Compiler Classic ifort 2021.13.0 (automatic CPU dispatch)",
      "solver": "Abaqus/Standard 2023 Datacheck (scratch=/tmp, Exit 0)"
    },
    "observables_extractor": {
      "script_path": "models/pandey_kumar_mode1/290_method_c_case3/extract_case3_job1_observables.py",
      "sha256": "F33F0AD4D723FACC97B2D3DE7626D2C37AD204F1C82FC61918E1C75B74B42441",
      "cluster_staged": true,
      "target_observables": ["U (nodal displacements)", "RF2 (reaction force on N_RP)", "SDV1 (damage d)", "SDV2 (history H)", "MISESERI", "MISESAVG", "crack tip tracking"]
    },
    "unit_tests": {
      "test_suite": "tests/unit/test_method_c_case3_job1_execution.py",
      "sha256": "F52649913A90692986D8A0186A7B67CD0078C1B134A09F1D3A4EC881DECEAB0D",
      "method_c_total_tests": "51/51 PASS (100% across all 10 suites)"
    },
    "accounting": {
      "authorized_submissions": 1,
      "consumed_submissions": 1,
      "pre_submission_cumulative_pbs": 62,
      "post_submission_cumulative_pbs": 63,
      "max_new_pbs_submissions": 0,
      "hpc_ledger_updated": true,
      "batch_submissions_updated": true,
      "active_task_updated": true
    }
  },
  "governance": {
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "dual_channel_notifications": "PASS_LOGIN_NODE",
    "master_goal_status": "OPEN"
  }
}

---
### Full Execution Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C CASE 3 JOB-1 SUBMISSION HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
