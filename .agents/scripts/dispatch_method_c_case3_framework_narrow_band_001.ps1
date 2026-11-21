# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_narrow_band_001.ps1
# Dispatches Method C Case 3 Narrow Damage-Following Band Specification & Implementation
# (HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-BUILD"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424797-DIAG-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$corridorGenPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_case3_adaptive_corridor_mesh.py"
$corridorGenSha = (Get-FileHash -Path $corridorGenPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\case3_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $caseDir "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Case 3: Narrow Damage-Following Band Specification and Implementation",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "Can the fixed tall corridor (17-30 mm height, >220,000 projected elements) be replaced with a narrow damage-following band (height 2.0 mm, +/-1.0 mm half-width around active crack trajectory) that adds ~102 elements per 1 mm crack advance, guaranteeing total mesh remains bounded under 15,000 elements for complete propagation, while preserving h_ref = 0.140 mm <= l0/2, frozen UEL CE8D5EDC, Gc = 0.00228 kN/mm, and 100% unit test pass rate (20/20 PASS)?",
    "expected_numerical_result": "Narrow damage-following band implemented in generate_case3_adaptive_corridor_mesh.py and case3_single_job_orchestrator.py; band dynamically tracks crack tip (x_tip, y_tip) and damage wake; height strictly 2.0 mm (half-width 1.0 mm ~ 3.51 l0); unit advance rate 102 elements/mm; representative mesh (x_tip=30 mm) has ~8,900 elements (<0.25 * 64,653 manual Cycle 4); full propagation mesh stays ~12,370 elements (<35,000 limit); 20/20 unit tests PASS; 0 new PBS jobs consumed (cumulative strictly 70); live Job 1424798 running untouched on mnode105; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md"
    },
    "corridor_generator": {
      "path": "scripts/remeshing/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "$corridorGenSha",
      "github_url": "$githubBase/scripts/remeshing/generate_case3_adaptive_corridor_mesh.py"
    },
    "orchestrator_script": {
      "path": "scripts/remeshing/case3_single_job_orchestrator.py",
      "sha256": "$orchSha",
      "github_url": "$githubBase/scripts/remeshing/case3_single_job_orchestrator.py"
    },
    "framework_manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
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
  "narrow_band_specification": {
    "band_half_width_mm": 1.0,
    "band_height_mm": 2.0,
    "wake_margin_mm": 1.5,
    "ahead_margin_mm": 2.0,
    "h_ref_mm": 0.140,
    "l0_mm": 0.285,
    "l0_half_mm": 0.1425,
    "elements_per_mm_advance": 102,
    "target_total_elements_bounded": 35000,
    "representative_x30_mesh_elements": 8900,
    "full_propagation_x64_mesh_elements": 12370,
    "manual_campaign_cycle4_comparison_elements": 64653
  },
  "cluster_execution_state": {
    "live_running_job_id": "1424798.mmaster02",
    "cluster_node": "mnode105",
    "state": "RUNNING (Cycle 1 state transfer in progress)",
    "scratch_directory_status": "UNTOUCHED (running on staged SHA 221C6D13)",
    "cumulative_pbs_submissions": 70,
    "new_pbs_submissions_in_this_step": 0
  },
  "next_step": {
    "requested_decision": "APPROVE_NARROW_BAND_BUILD",
    "proposed_action": "Review narrow band specification and implementation. Await completion of running PBS Job 1424798 retry test run (cumulative count strictly 70). Once 1424798 completes and is reviewed, deploy narrow band implementation for subsequent production multi-cycle adaptive propagation.",
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
    Write-Host "Orchestrator SHA: $orchSha"
    Write-Host "Corridor Gen SHA: $corridorGenSha"
    return
}

if ($DryRun) {
    Write-Host "DRY RUN: Testing bridge validation"
    Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun
    return
}

Write-Host "DISPATCHING: Sending $handoffId across bridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId
