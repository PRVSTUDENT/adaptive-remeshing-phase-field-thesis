# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_cycle0_001.ps1
# Dispatches Method C Case 3 Single-Job Framework Cycle-0 Observables & Orchestrator Repair Report
# (HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-ORCHESTRATOR-REPAIR-AND-CYCLE0-RESULTS"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-CYCLE0-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-TEST-001"

$cycle0ReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md"
if (-not (Test-Path $cycle0ReportPath)) {
    throw "Cycle 0 results report file not found at: $cycle0ReportPath"
}
$cycle0ReportSha = (Get-FileHash -Path $cycle0ReportPath -Algorithm SHA256).Hash.ToUpper()

$execReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md"
$execReportSha = (Get-FileHash -Path $execReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$physMeshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
$physMeshSha = (Get-FileHash -Path $physMeshPath -Algorithm SHA256).Hash.ToUpper()

$pbsPath = Join-Path $caseDir "submit_case3_single_job_framework.pbs"
$pbsSha = (Get-FileHash -Path $pbsPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Framework Cycle-0 Observables Extraction & Orchestrator Repair Report",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md",
  "checkpoint_artifact_sha256": "$cycle0ReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_framework_cycle0_evaluation_and_orchestrator_repair",
    "numerical_uncertainty": "Can the Cycle-0 coarse solve observables from PBS Job 1424786 be verified and reconciled with Job-1 physical benchmarks, and can GAP-FW-02-PARTIAL in the single-job orchestrator be fully resolved by implementing production physical mesh ingestion, notch slit flank isolation at y=70 mm, gradient-preserving isoparametric GP history transfer with convex_clamp, 3-layer UEL deck assembly, and dynamic completion checks, with 100% passing unit tests and zero new PBS submissions consumed (cumulative 68 strictly preserved)?",
    "expected_numerical_result": "Cycle 0 coarse solve verified (Step 1 RF2=3.9288 kN at u2=0.0500 mm, d_max=0.9472, E_frac=0.003456 kN*mm; Step 2 peak force F_max=4.3318 kN at u2=0.05610 mm, graceful cutback floor at Inc 13, terminal RF2=4.2420 kN); GAP-FW-02-PARTIAL fully resolved in case3_single_job_orchestrator.py; 13/13 unit tests PASS (100%); 0 new PBS jobs consumed, cumulative count strictly preserved at 68; MASTER_GOAL_STATUS strictly remains OPEN.",
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
    "framework_execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md",
      "sha256": "$execReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_EXECUTION_REPORT.md"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "orchestrator_copy": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py"
    },
    "adaptive_physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp",
      "sha256": "$physMeshSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp"
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
      "tests_passed": 13,
      "tests_total": 13
    }
  },
  "review_resolution_matrix": {
    "CYCLE_0_OBSERVABLES": {
      "directive": "Extract Cycle-0 observables from PBS Job 1424786 run directory and report results",
      "status": "RESOLVED",
      "implementation": "PBS Job 1424786 completed Exit 0 on mnode103 (solver CPU 546s, walltime 2114s). Extracted Cycle-0 observables: Step 1 linear-elastic solve converged 50/50 increments to u2=0.0500 mm with RF2=3.9288 kN, d_max=0.9472, and E_frac=0.003456 kN*mm; Step 2 captured peak force F_max=4.3318 kN at u2=0.05610 mm, post-peak softening, and gracefully terminated at dt_min cutback floor (1.0e-8) at Increment 13 with residual rebound at notch root (terminal u2=0.056110 mm, terminal RF2=4.2420 kN). Fully documented in METHOD_C_CASE3_FRAMEWORK_CYCLE0_RESULTS_REPORT.md."
    },
    "GAP-FW-02-PARTIAL": {
      "directive": "Complete in-allocation orchestrator loop: physical mesh parsing, notch slit flank isolation at y=70 mm, gradient-preserving isoparametric GP history transfer with convex_clamp, 3-layer UEL deck assembly, and dynamic completion checks",
      "status": "RESOLVED",
      "implementation": "Completely refactored scripts/remeshing/case3_single_job_orchestrator.py: (1) Added parse_physical_inp parsing quads and tris; (2) Added transfer_nodal_fields with strict notch slit flank isolation at y=70.0 mm (x <= 10.0 mm) and 0 <= d <= 1 bounds; (3) Added transfer_gp_history via isoparametric bilinear reconstruction with convex_clamp limiter and thermodynamic non-negativity H >= 0; (4) Added assemble_coupled_deck creating complete 3-layer UEL deck (Phase UEL + Disp UEL + companion CPE4/CPE3) with pin-hole kinematic coupling (*EQUATION), *INITIAL CONDITIONS, TYPE=SOLUTION on SVARS 1..18, and two-step loading (Step-1-Hold + Step-2-Advance); (5) Removed hardcoded donor literals and wired dynamic observable extraction and completion checks (x_tip >= 64.0 mm or RF2 < 0.05 * peak_rf2)."
    },
    "UNIT_TEST_EXPANSION": {
      "directive": "Expand unit test suite to verify physical mesh parsing, deck assembly, and transfer routine bounds",
      "status": "RESOLVED",
      "implementation": "Added test_physical_mesh_parsing_and_deck_assembly and test_transfer_routines_bounds to tests/unit/test_method_c_case3_framework_package.py. All 13 tests PASS (100%) in 1.11 seconds."
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
