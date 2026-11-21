# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_narrow_band_003.ps1
# Dispatches Method C Case 3 Narrow Damage-Following Band Re-Issue 3
# (HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-REPAIR-002"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-003"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-002"

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
  "title": "Method C Case 3: Narrow Damage-Following Band Specification and Implementation (Re-Issue 3)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "Can the per-cycle receiver mesh generation take effect in practice under system python3 (where the PBS job runs the orchestrator) via Route (a) Abaqus CAE subprocess dynamic generation in PBS allocation plus Route (b) pre-generated authentic narrow-band cycle meshes (Cycles 1-4: 7,172, 9,175, 11,093, and 13,075 elements) committed to the repository, proving under system python3 that distinct cycles return distinct receiver mesh files with distinct element counts, while resolving manifest element counts (7,172 baseline elements), retaining corrected full-severance estimates (56.5 mm / 12,265), and passing all 21 unit tests by execution, at 0 new PBS?",
    "expected_numerical_result": "generate_cycle_adaptive_mesh under system python3 returns distinct mesh files for Cycle 1 (7,172 elements) and Cycle 3 (11,093 elements) (different paths and different mesh content); Route (a) invokes Abaqus CAE subprocess when abaqus CLI is available; Route (b) resolves committed narrow-band cycle meshes when Abaqus CAE is offline; manifest updated to 7,172 baseline elements; unit test asserts distinct mesh files; 21/21 unit tests PASS; 0 new PBS consumed (cumulative count strictly 70 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "review_gaps_resolved": {
    "GAP-NB-02_practical_runtime_resolution": "Resolved via dual-route architecture: (1) Route (a): In the PBS job, Abaqus CLI is in PATH; generate_cycle_adaptive_mesh() invokes Abaqus CAE as a subprocess ('abaqus cae noGUI=<generator> -- <mesh> <tip_x> <tip_y>') to dynamically generate narrow-band meshes directly into run_dir. (2) Route (b): Generated and committed authentic narrow-band meshes for Cycles 1-4 via Abaqus CAE: Cycle 1 (7,172 elements, 96.14% quad), Cycle 2 (9,175 elements, 97.05% quad), Cycle 3 (11,093 elements, 97.20% quad), and Cycle 4 (13,075 elements, 97.22% quad). When Abaqus CAE is offline (e.g. system python3 review sandbox), the orchestrator stages the authentic pre-generated cycle mesh from repository into run_dir.",
    "NOTE_manifest_generated_elements": "Updated manifest baseline mesh metrics: generated_physical_elements is now 7,172 (down from old 24,832 baseline), generated_physical_nodes: 7,261, and generated_quad_fraction_pct: 96.14. Cycles 1-4 are now physically generated and counted; states beyond Cycle 4 remain analytic estimates (representative x=30 mm ~8,898, full severance x=64 mm ~12,265).",
    "TEST-NB-01_proven_under_system_python3": "Updated test_receiver_mesh_generation_per_cycle_follows_tip in tests/unit/test_method_c_case3_framework_package.py: calls generate_cycle_adaptive_mesh under system python3 for Cycle 1 (tip 10.0, 70.0) and Cycle 3 (tip 20.0, 67.0); asserts distinct file paths (PK_METHOD_C_CASE3_CYCLE1_PHYS.inp vs CYCLE3_PHYS.inp), distinct element counts (7,172 vs 11,093), distinct node counts (7,261 vs 11,165), monotonic expansion along crack trajectory, and boundedness under 35,000 elements. All 21 tests pass 100% by execution."
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
  "narrow_band_physical_measurements": {
    "cycle1_elements_actual": 7172,
    "cycle2_elements_actual": 9175,
    "cycle3_elements_actual": 11093,
    "cycle4_elements_actual": 13075,
    "representative_x30_mesh_elements_analytic": 8898,
    "full_propagation_x64_mesh_elements_analytic": 12265,
    "bounded_ceiling": 35000,
    "advance_rate_elements_per_mm": 102
  },
  "cluster_execution_state": {
    "live_running_job_id": "1424798.mmaster02",
    "cluster_node": "mnode105",
    "state": "EXECUTED (Completed; scratch run directory preserved)",
    "scratch_directory_status": "PRESERVED",
    "cumulative_pbs_submissions": 70,
    "new_pbs_submissions_in_this_step": 0
  },
  "next_step": {
    "requested_decision": "APPROVE_NARROW_BAND_BUILD",
    "proposed_action": "Approve narrow band specification and verified dual-route implementation. Following approval, inspect Job 1424798 execution observables, and proceed with production multi-cycle adaptive remeshing under the narrow band formulation.",
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
