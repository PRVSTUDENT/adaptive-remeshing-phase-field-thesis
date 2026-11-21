# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_job1424798_001.ps1
# Dispatches Method C Case 3 Single-Job Framework Job 1424798 Execution Observables Report
# (HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-JOB1424798-OBSERVABLES"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-003"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log"
$logSha = (Get-FileHash -Path $logPath -Algorithm SHA256).Hash.ToUpper()

$corridorGenPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_case3_adaptive_corridor_mesh.py"
$corridorGenSha = (Get-FileHash -Path $corridorGenPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$c1MeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE1_PHYS.inp"
$c1MeshSha = (Get-FileHash -Path $c1MeshPath -Algorithm SHA256).Hash.ToUpper()

$c2MeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_PHYS.inp"
$c2MeshSha = (Get-FileHash -Path $c2MeshPath -Algorithm SHA256).Hash.ToUpper()

$c3MeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"
$c3MeshSha = (Get-FileHash -Path $c3MeshPath -Algorithm SHA256).Hash.ToUpper()

$c4MeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
$c4MeshSha = (Get-FileHash -Path $c4MeshPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Framework Job 1424798 Execution Observables Report",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "What are the PBS 1424798 execution observables (per-cycle force/energy continuity, non-healing, crack-tip advance per cycle, receiver mesh per cycle, exit code, walltime/CPU, terminal state and completion-criterion status) for the framework adaptive-loop test run, with committed artifact SHAs, at 0 new PBS?",
    "expected_numerical_result": "A committed execution report for PBS 1424798 giving per-cycle force and energy continuity, non-healing status, crack-tip advance per cycle, the receiver mesh file and element count used per cycle (Route a fresh or Route b staged), exit code, walltime and CPU, terminal tip/RF2/u2 and completion-criterion status, with artifact SHAs; 0 new PBS (cumulative stays 70); no new submission; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "job1424798_execution_observables": {
    "pbs_job_id": "1424798.mmaster02",
    "host": "mnode105.cluster",
    "queue": "entry_imfdfkmq",
    "start_time": "Sa 21. Nov 12:27:21 CET 2026",
    "termination_time": "Sa 21. Nov 12:27:22 CET 2026",
    "elapsed_walltime_s": 1.0,
    "elapsed_cpu_s": 0.5,
    "exit_code": 1,
    "failure_classification": "CYCLE0_EXTRACTION_UTF8_BOM_DECODE_ERROR",
    "verbatim_error": "json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)",
    "failure_point": "case3_single_job_orchestrator.py line 1032 in extract_cycle_state (while loading PK_METHOD_C_CASE3_COARSE_JOB1_state.json)",
    "adaptive_cycles_completed": 0,
    "cycle_mesh_used_per_cycle": "NONE (Adaptive loop never entered)",
    "generation_route_invoked": "NEITHER (Neither Route a nor Route b was reached)",
    "force_continuity_per_cycle": "NOT_EVALUATED (Cycle 1 solve never launched)",
    "energy_continuity_per_cycle": "NOT_EVALUATED",
    "non_healing_evaluated": "NOT_EVALUATED (Remained at Cycle 0 terminal state)",
    "terminal_crack_tip_mm": [10.6727, 69.9342],
    "terminal_rf2_kN": 4.2420,
    "terminal_u2_mm": 0.056110,
    "completion_criterion_fired": false,
    "remediation_status": "utf-8-sig encoding incorporated in repository orchestrator; verified 22/22 unit tests PASS."
  },
  "evidence_manifest": {
    "report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
    },
    "pbs_execution_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log",
      "sha256": "$logSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log"
    },
    "orchestrator": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "corridor_generator": {
      "path": "scripts/remeshing/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "$corridorGenSha",
      "github_url": "$githubBase/scripts/remeshing/generate_case3_adaptive_corridor_mesh.py"
    },
    "framework_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
    },
    "cycle1_narrow_band_mesh_7172_elem": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp",
      "sha256": "$c1MeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE1_PHYS.inp"
    },
    "cycle2_narrow_band_mesh_9175_elem": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "sha256": "$c2MeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp"
    },
    "cycle3_narrow_band_mesh_11093_elem": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp",
      "sha256": "$c3MeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"
    },
    "cycle4_narrow_band_mesh_13075_elem": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp",
      "sha256": "$c4MeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
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
    "scratch_directory_status": "PRESERVED_UNMODIFIED",
    "uncapped_loop_status": "PENDING (n_adaptive_steps to high safety cap deferred pending this review)"
  },
  "next_step": {
    "requested_decision": "APPROVE_JOB1424798_OBSERVABLES",
    "proposed_action": "Approve Job 1424798 execution report and failure diagnosis. Following approval, update n_adaptive_steps to high safety cap (uncapped loop) and authorize single production multi-cycle adaptive remeshing run to complete crack propagation.",
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
    Write-Host "Log SHA: $logSha"
    return
}

if ($DryRun) {
    Write-Host "DRY RUN: Testing bridge validation"
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun
    return
}

Write-Host "DISPATCHING: Sending $handoffId across bridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId
