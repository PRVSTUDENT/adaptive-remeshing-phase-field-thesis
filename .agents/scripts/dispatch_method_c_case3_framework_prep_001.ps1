# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_prep_001.ps1
# Dispatches Method C Case 3 Single-Job Multi-Cycle Adaptive Remeshing Framework Package Report
# (HND-METHOD-C-CASE3-FRAMEWORK-PREP-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-SINGLE-JOB-FRAMEWORK-BUILD"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-PREP-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-001"

$frameworkReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
if (-not (Test-Path $frameworkReportPath)) {
    throw "Framework package report file not found at: $frameworkReportPath"
}
$frameworkReportSha = (Get-FileHash -Path $frameworkReportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$pbsPath = Join-Path $caseDir "submit_case3_single_job_framework.pbs"
$pbsSha = (Get-FileHash -Path $pbsPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Single-Job Multi-Cycle Adaptive Remeshing Framework Package Report",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md",
  "checkpoint_artifact_sha256": "$frameworkReportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_single_job_framework_build",
    "numerical_uncertainty": "Can the single-job multi-cycle adaptive remeshing framework for Method C Case 3 (Pandey & Kumar 2025 Section 4.3) be constructed and verified with an in-allocation orchestrator chaining Coarse solve plus 4 adaptive remesh cycles in ONE PBS allocation, a dt_min-floor (1e-14) resolution policy that remeshes from the terminal converged increment without manual dt_min reductions, a minimized refinement corridor (x in [8.5, 20], y in [60, 77] mm, area 195.5 mm^2, 77.9% reduction) targeting ~30,000 elements, quantitative force/energy/healing continuity gates, and a 16-CPU / 48-GB / 72-h PBS script, while strictly preserving 0 new PBS jobs consumed (cumulative 67 preserved) and maintaining the bitwise frozen UEL CE8D5EDC...?",
    "expected_numerical_result": "Method C Case 3 single-job multi-cycle adaptive framework package approved under HND-METHOD-C-CASE3-FRAMEWORK-PREP-001: orchestrator script case3_single_job_orchestrator.py, corridor mesh generator and audit generate_case3_adaptive_corridor_mesh.py, formal manifest METHOD_C_CASE3_FRAMEWORK_MANIFEST.json, PBS script submit_case3_single_job_framework.pbs, framework report METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md, and offline test suite 9/9 PASS; 0 new PBS submissions consumed (cumulative 67 strictly preserved); first framework run authorized for 1 PBS submission (Job 6, submission 68) only after review approval; MASTER_GOAL_STATUS strictly remains OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "framework_report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md",
      "sha256": "$frameworkReportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_PACKAGE_REPORT.md"
    },
    "framework_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
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
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_framework_package.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_framework_package.py",
      "tests_passed": 9,
      "tests_total": 9
    }
  },
  "package_specification": {
    "benchmark": "Pandey & Kumar (2025) Section 4.3 Mode-I Case 3",
    "single_job_architecture": "In-allocation chaining: Coarse solve + 4 adaptive remesh cycles in ONE PBS allocation on scratch",
    "cycle_schedule": [
      {"cycle": 0, "name": "COARSE", "u2_target_mm": 0.0500},
      {"cycle": 1, "name": "CYCLE1_ADAPT1", "u2_target_mm": 0.4125},
      {"cycle": 2, "name": "CYCLE2_ADAPT2", "u2_target_mm": 0.7750},
      {"cycle": 3, "name": "CYCLE3_ADAPT3", "u2_target_mm": 1.1375},
      {"cycle": 4, "name": "CYCLE4_ADAPT4", "u2_target_mm": 1.5000}
    ],
    "dt_min_floor_handling": {
      "floor_threshold": 1.0e-14,
      "policy": "STOP_AT_FLOOR_AND_REMESH_FROM_TERMINAL_CONVERGED_INCREMENT",
      "further_dt_min_reduction_authorized": false
    },
    "refinement_corridor_minimization": {
      "corridor_box": {"x_min_mm": 8.5, "x_max_mm": 20.0, "y_min_mm": 60.0, "y_max_mm": 77.0},
      "width_mm": 11.5,
      "height_mm": 17.0,
      "area_mm2": 195.5,
      "area_reduction_pct_vs_broad": 77.9,
      "target_physical_elements": 30000,
      "h_ref_mm": 0.140,
      "l0_half_threshold_mm": 0.1425
    },
    "continuity_gates": {
      "force_continuity_threshold_pct": 5.0,
      "energy_evaluation": "Gc_normalized_integral (Gamma = E_frac / Gc)",
      "zero_healing_enforcement": "d_max_terminal >= d_max_transferred - 1e-4",
      "terminal_frame_naming": "DYNAMIC_FROM_LAST_CONVERGED_INCREMENT"
    },
    "pbs_allocation": {
      "ncpus": 16,
      "mem_gb": 48,
      "walltime_hours": 72,
      "queue": "entry_imfdfkmq",
      "dual_channel_notifications": "MAIL_AND_TELEGRAM_TRAPS"
    }
  },
  "accounting": {
    "current_cumulative_pbs_submissions": 67,
    "framework_build_pbs_consumed": 0,
    "cumulative_pbs_submissions_preserved": 67,
    "authorized_first_run_pbs_submissions": 1,
    "first_run_pbs_execution_requires_independent_review_approval": true,
    "master_goal_status": "OPEN"
  }
}
"@

if ($CheckOnly) {
    Write-Output "CHECK_ONLY: Verification complete. Prompt generated with Handoff ID: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Framework Package Report SHA: $frameworkReportSha"
    return
}

Write-Output "Dispatching review request $handoffId via Invoke-ChatGPTBridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
