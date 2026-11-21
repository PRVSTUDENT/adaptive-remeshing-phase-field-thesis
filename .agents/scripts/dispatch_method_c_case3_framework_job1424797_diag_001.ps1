# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_job1424797_diag_001.ps1
# Dispatches Method C Case 3 Single-Job Framework Job 1424797 Failure Diagnosis & Repair
# (HND-METHOD-C-CASE3-FRAMEWORK-JOB1424797-DIAG-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-JOB1424797-FAILURE-DIAGNOSIS"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424797-DIAG-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-003"

$diagReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_JOB1424797_DIAGNOSIS_REPORT.md"
if (-not (Test-Path $diagReportPath)) {
    throw "Diagnosis report file not found at: $diagReportPath"
}
$diagReportSha = (Get-FileHash -Path $diagReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$orchCopyPath = Join-Path $caseDir "case3_single_job_orchestrator.py"
$orchCopySha = (Get-FileHash -Path $orchCopyPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Framework Job 1424797 Failure Diagnosis & Repair (Python JSON BOM Decoding Error)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424797_DIAGNOSIS_REPORT.md",
  "checkpoint_artifact_sha256": "$diagReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job1424797_failure_diagnosis",
    "numerical_uncertainty": "Can the Job 1424797 startup failure be diagnosed from verbatim solver/scheduler logs, classified by root cause (Python 3.6 JSON BOM decoding incompatibility), and demonstrated as repaired with utf-8-sig encoding, BOM-free donor state assets, passing unit test suite (16/16 PASS), and cluster dry-run (Exit 0), so the framework is qualified for an authorized retry?",
    "expected_numerical_result": "Job 1424797 diagnosed: Exit 1 after 2 s wallclock on mnode105, caused by json.decoder.JSONDecodeError due to UTF-8 BOM on scratch donor JSON; repaired in orchestrator using encoding='utf-8-sig' (SHA 221C6D13, bitwise synchronized); cluster asset sanitized; 16/16 unit tests PASS; cluster dry-run Exit 0; 1 PBS consumed (cumulative 68 to 69); 0 new PBS submitted; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "diagnosis_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424797_DIAGNOSIS_REPORT.md",
      "sha256": "$diagReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424797_DIAGNOSIS_REPORT.md"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "orchestrator_package_copy": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py",
      "sha256": "$orchCopySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py"
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
  "job_execution_evidence": {
    "pbs_job_id": "1424797.mmaster02",
    "queue": "normal_imfdfkmq",
    "node": "mnode105",
    "start_time": "2026-11-21T12:27:21+01:00",
    "walltime_s": 2,
    "cpu_time_s": 0,
    "exit_code": 1,
    "failure_classification": "ABAQUS_RUNTIME_OR_INPUT_ERROR",
    "root_cause_summary": "Python 3.6 on CentOS compute node failed in json.load(f) because PK_METHOD_C_CASE3_COARSE_JOB1_state.json on scratch contained a 3-byte UTF-8 Byte Order Mark (0xEF 0xBB 0xBF). Python 3.6 standard json.loads strictly rejects BOM unless utf-8-sig is specified.",
    "verbatim_error": "json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)",
    "fix_applied": "Updated case3_single_job_orchestrator.py to open JSON files with encoding='utf-8-sig' at lines 1031 and 1085. Uploaded clean BOM-free state.json and missing PK_METHOD_C_CASE3_COARSE_PHYS.inp to scratch. Verified with 16/16 pytest PASS and cluster dry-run Exit 0.",
    "pbs_accounting": {
      "authorized_test_runs": 1,
      "consumed_in_this_step": 1,
      "prior_cumulative_pbs": 68,
      "current_cumulative_pbs": 69,
      "unapproved_pbs_submitted": 0
    }
  },
  "next_step": {
    "requested_decision": "APPROVE_DIAGNOSIS_AND_AUTHORIZE_RETRY",
    "proposed_action": "Submit 1 authorized retry of the Method C Case 3 Single-Job Multi-Cycle Adaptive Remeshing Framework (cumulative 69 to 70) using the repaired orchestrator (SHA 221C6D13) and sanitized scratch assets.",
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Host "CHECK ONLY: Handoff validation"
    Write-Host "Handoff ID: $handoffId"
    Write-Host "Commit SHA: $commitSha"
    Write-Host "Rules SHA: $rulesSha"
    Write-Host "Report SHA: $diagReportSha"
    Write-Host "Orchestrator SHA: $orchSha"
    return
}

if ($DryRun) {
    Write-Host "DRY RUN: Testing bridge validation"
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun
    return
}

Write-Host "DISPATCHING: Sending handoff $handoffId to ChatGPT across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId

Write-Host "================ BRIDGE RESPONSE ================"
Write-Host $response
Write-Host "================================================="
