# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_test_001.ps1
# Dispatches Method C Case 3 Single-Job Multi-Cycle Adaptive Remeshing Framework Execution Report
# (HND-METHOD-C-CASE3-FRAMEWORK-TEST-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-SINGLE-JOB-FRAMEWORK-BUILD-AND-TEST"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-TEST-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-PREP-001"

$executionReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md"
if (-not (Test-Path $executionReportPath)) {
    throw "Framework execution report file not found at: $executionReportPath"
}
$executionReportSha = (Get-FileHash -Path $executionReportPath -Algorithm SHA256).Hash.ToUpper()

$packageReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
$packageReportSha = (Get-FileHash -Path $packageReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$authPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_AUTHORIZATION.json"
$authSha = (Get-FileHash -Path $authPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$physMeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
$physMeshSha = (Get-FileHash -Path $physMeshPath -Algorithm SHA256).Hash.ToUpper()

$dcPath = Join-Path $caseDir "PK_METHOD_C_CASE3_COARSE_JOB1_DC.dat"
$dcSha = (Get-FileHash -Path $dcPath -Algorithm SHA256).Hash.ToUpper()

$pbsPath = Join-Path $caseDir "submit_case3_single_job_framework.pbs"
$pbsSha = (Get-FileHash -Path $pbsPath -Algorithm SHA256).Hash.ToUpper()

$notifPath = Join-Path $caseDir "job_notifications.sh"
$notifSha = (Get-FileHash -Path $notifPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$corridorPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_case3_adaptive_corridor_mesh.py"
$corridorSha = (Get-FileHash -Path $corridorPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Multi-Cycle Adaptive Remeshing Framework Execution Report (PBS 1424786)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$executionReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_single_job_framework_test_execution",
    "numerical_uncertainty": "Can the single-job multi-cycle adaptive remeshing framework for Method C Case 3 (Pandey & Kumar 2025 Section 4.3) successfully execute within a single 72-hour PBS allocation on mnode103 (16 CPUs SMP, 48 GB RAM) under PBS Job 1424786.mmaster02, parameterised with n_adaptive_steps (default 4), equal load division (0.0100 mm/cycle), no 1.5000 mm displacement cap, and dynamic crack-completion criteria (tip x >= 64.0 mm or structural RF2 < 5% of peak load), while preserving force continuity <= 5%, fracture energy integral Gamma, damage irreversibility, and bitwise frozen UEL CE8D5EDC... under strict budget accounting advancing cumulative PBS submissions from 67 to 68?",
    "expected_numerical_result": "Method C Case 3 single-job multi-cycle adaptive remeshing framework test run submitted and actively executing under PBS Job 1424786.mmaster02 on mnode103 in queue normal_imfdfkmq; all review gaps GAP-FW-01 through 03 and notes NOTE-FW-01 through 03 verified resolved; offline test suite 11/11 PASS (100%); cluster technical datacheck passed Exit 0; technical preflight passed; dual-channel notification armed; exactly 1 authorized PBS job consumed (cumulative 67 to 68); MASTER_GOAL_STATUS strictly remains OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md",
      "sha256": "$executionReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md"
    },
    "package_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md",
      "sha256": "$packageReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
    },
    "authorization_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_AUTHORIZATION.json",
      "sha256": "$authSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_AUTHORIZATION.json"
    },
    "framework_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
    },
    "adaptive_physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp",
      "sha256": "$physMeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
    },
    "datacheck_output": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_DC.dat",
      "sha256": "$dcSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1_DC.dat"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "corridor_generator_script": {
      "path": "scripts/remeshing/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "$corridorSha",
      "github_url": "$githubBase/scripts/remeshing/generate_case3_adaptive_corridor_mesh.py"
    },
    "pbs_submission_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/submit_case3_single_job_framework.pbs",
      "sha256": "$pbsSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/submit_case3_single_job_framework.pbs"
    },
    "notification_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job_notifications.sh",
      "sha256": "$notifSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job_notifications.sh"
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
      "tests_passed": 11,
      "tests_total": 11
    }
  },
  "review_resolution_matrix": {
    "GAP-FW-01": {
      "directive": "Parameterise adaptive steps & equal load division; remove 1.5000 mm cap; dynamic completion criteria",
      "status": "RESOLVED",
      "implementation": "Exposed --n-adaptive-steps N (default 4) and --load-increment-mm (default 0.0100 mm). Completely removed 1.5 mm cap. Dynamically loops until x_tip >= 64.0 mm OR RF2 < 5% peak load."
    },
    "GAP-FW-02": {
      "directive": "Implement executable in-allocation orchestrator (not dry-run only)",
      "status": "RESOLVED",
      "implementation": "Implemented execute() loop in case3_single_job_orchestrator.py executing Abaqus solve, .sta parsing, cutback floor handling (dt < 1e-14), convex_clamp state transfer, deck generation, and re-equilibration."
    },
    "GAP-FW-03": {
      "directive": "Reconcile report Section 3 against authentic records",
      "status": "RESOLVED",
      "implementation": "Reconciled Step 1 residual, node coordinates, coarse mesh 4,671 physical / 14,013 layered elements, Job 5 64,653 elements / 64,106 nodes, and element reduction 61.6% in METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md."
    },
    "NOTE-FW-01": {
      "directive": "Authentic Job-5 RF2 in unit tests",
      "status": "RESOLVED",
      "implementation": "Updated test_method_c_case3_framework_package.py with RF2 3.9063646 -> 3.8692487 kN."
    },
    "NOTE-FW-02": {
      "directive": "Generate and commit physical mesh",
      "status": "RESOLVED",
      "implementation": "Generated PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp via Abaqus CAE (24,832 physical elements, 97.41% quads, 61.59% element reduction) and committed to repo."
    },
    "NOTE-FW-03": {
      "directive": "Commit notification helper to package",
      "status": "RESOLVED",
      "implementation": "Committed canonical job_notifications.sh directly to models/pandey_kumar_mode1/290_method_c_case3/."
    }
  },
  "submission_telemetry": {
    "pbs_job_id": "1424786.mmaster02",
    "job_name": "M1_MC_C3_FRAMEWORK",
    "host": "mnode103",
    "state": "R",
    "cpus": 16,
    "memory_gb": 48,
    "walltime": "72:00:00",
    "queue": "normal_imfdfkmq",
    "active_cycle": "Cycle 0 (PK_METHOD_C_CASE3_COARSE_JOB1)",
    "solver": "Abaqus Standard 2023 with frozen UEL f42_mixed_uel.for (CE8D5EDC...)",
    "run_directory": "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job/"
  },
  "accounting": {
    "previous_cumulative_pbs_submissions": 67,
    "test_run_pbs_consumed": 1,
    "current_cumulative_pbs_submissions": 68,
    "authorized_submissions_remaining": 0,
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Output "CHECK_ONLY: Verification complete. Prompt generated with Handoff ID: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Framework Execution Report SHA: $executionReportSha"
    return
}

Write-Output "Dispatching review request $handoffId via Invoke-ChatGPTBridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
