# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase2_job1_001.ps1
# Dispatches Method C Phase 2 Job-1 Baseline Submission & Preflight Datacheck Qualification
# (HND-METHOD-C-PHASE2-JOB1-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE2-JOB1-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-BLOCKER-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE2_JOB1_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 2: Job-1 Baseline Solve Submission and Preflight Datacheck Qualification",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE2_JOB1_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase2_job1_submit",
    "numerical_uncertainty": "Can the Job-1 baseline solve for the Method C demo case be submitted and verified via technical preflight and Abaqus 2023 datacheck, yielding authentic Step-1 baseline observables for the re-equilibration test?",
    "expected_numerical_result": "Job-1 submitted (max 1 PBS job, cumulative 57 -> 58); datacheck Exit 0 verified; PBS receipt 1424517.mmaster02 recorded; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_PHASE2_JOB1_EXECUTION_REPORT.md",
      "sha256": "$reportSha"
    },
    "pbs_job_receipt": {
      "job_id": "1424517.mmaster02",
      "job_name": "M1_MC_DEMO_JOB1",
      "scratch_dir": "/scratch9/pr21vyci/runs/mode1_289_method_c_demo_case",
      "queue": "normal_imfdfkmq",
      "resources": "16 CPUs SMP, 48 GB RAM, 72:00:00 walltime",
      "deck": "PK_METHOD_C_DEMO_COARSE_JOB1.inp (8,760 layered elements)",
      "deck_sha256": "69abff7acd1efd767046e686847f30d06f808bbec738c2fbb9bdff478a66ec9c",
      "pbs_script": "submit_demo_coarse_job1.pbs",
      "pbs_sha256": "dbb2ad8dd400c7dee5b2556941e0c5f209892755b0e5178dbb58fe346c002785",
      "submission_timestamp": "2026-11-19T12:51:20Z"
    },
    "technical_datacheck": {
      "datacheck_file": "PK_METHOD_C_DEMO_COARSE_JOB1_DC.dat",
      "datacheck_status": "ANALYSIS DATACHECK COMPLETE, 0 errors, 0 syntax violations",
      "compiler": "Intel Fortran Compiler Classic ifort 2021.13.0 (with automatic CPU dispatch)",
      "solver": "Abaqus/Standard 2023 Datacheck (pre.exe + standard.exe Exit 0)"
    },
    "accounting": {
      "authorized_submissions": 1,
      "consumed_submissions": 1,
      "pre_submission_cumulative_pbs": 57,
      "post_submission_cumulative_pbs": 58,
      "hpc_ledger_updated": true,
      "batch_submissions_updated": true,
      "active_task_updated": true
    },
    "observables_extractor": {
      "script_path": "models/pandey_kumar_mode1/289_method_c_demo_case/extract_job1_observables.py",
      "target_observables": ["U (nodal displacements)", "RF2 (reaction force)", "SDV1 (damage d)", "SDV2 (history H)", "MISESERI (stress error)", "MISESAVG"]
    }
  },
  "governance": {
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "unit_tests": "10/10 PASS (100%)",
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

Write-Output "=== DISPATCHING METHOD C PHASE 2 JOB-1 SUBMISSION HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
