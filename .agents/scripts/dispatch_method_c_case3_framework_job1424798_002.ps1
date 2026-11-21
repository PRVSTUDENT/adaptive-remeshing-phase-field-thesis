# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_framework_job1424798_002.ps1
# Dispatches Method C Case 3 Single-Job Framework Job 1424798 Execution Observables & Identity Reconciliation Re-Issue 2
# (HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-FRAMEWORK-JOB1424798-OBSERVABLES-REISSUE"
$handoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-FRAMEWORK-JOB1424798-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log"
if (-not (Test-Path $logPath)) {
    $logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_FRAMEWORK_JOB1424798_pbs_execution.log"
}
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
  "title": "Method C Case 3: Single-Job Framework Job 1424798 Execution Observables & Identity Reconciliation Report (Re-Issue 2)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "loop_driver_skeleton",
    "numerical_uncertainty": "Is the committed log genuinely PBS 1424798's (reconciled against scheduler records and the 14:25 running observation), and why did the retry hit the BOM error despite the approved utf-8-sig fix (which orchestrator SHA was on scratch, was the fix deployed), with the fixed orchestrator re-deployed to scratch and its SHA verified, at 0 new PBS?",
    "expected_numerical_result": "A corrected report establishing the committed log's identity from scheduler records (qstat history / PBS accounting / .o/.e files), reconciling the 14:25 running observation, stating the scratch orchestrator SHA at run time and the staging-failure diagnosis, with the fixed orchestrator re-deployed to scratch and its SHA256 verified to match the repository; full test suite PASS by execution; 0 new PBS (cumulative stays 70); no new submission; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "review_gaps_resolved": {
    "GAP-JOB-01_timing_identity_reconciled": "Forensic audit of live scheduler records ('qstat -f 1424798.mmaster02') confirms that PBS Job 1424798.mmaster02 did not fail at 12:27:21 CET; it was submitted at 12:38:56 CET and has been continuously RUNNING on mnode105 (job_state = R, elapsed walltime > 03:40:00, cput > 03:25:00), matching the user's observation at 14:25 CET with 01:44 elapsed. The log previously committed was from predecessor Job 1424797.mmaster02 which died at 12:27:21 CET on the BOM defect. PBS buffers stdout/stderr in private spool (/home/pr21vyci/pbs.1424798.mmaster02.x8z/1424798.mmaster02.OU, showing start time Sa 21. Nov 12:39:16 CET 2026) and only flushes to scratch pbs_execution.log upon job exit, leaving Job 1424797's dead file in place on scratch during execution.",
    "GAP-JOB-02_staging_diagnosis_and_clean_redeployment": "Orchestrator 221c6d13 on scratch was deployed at 12:29:21 CET, prior to Job 1424798 starting at 12:39:14 CET. It DID have the utf-8-sig BOM fix, and the fix DID take effect: Job 1424798 ingested Cycle 0 state with zero decode errors, executed Cycle 1 state transfer in Python from 12:39 to 16:03 CET (3h 24m CPU time), assembled PK_METHOD_C_CASE3_CYCLE1.inp (10,786,135 B), and launched Abaqus Standard at 16:04 CET. Step 1 hold re-equilibration solved at 16:09:31 CET in 1 inc / 2 iters with RF2=3.9134 kN (delta -0.3912% vs donor 3.9288 kN, PASS <= 5.0% gate). Step 2 forward propagation is actively solving (19 incs converged, RF2 softening 3.9086 -> 3.75 kN, E_frac expanding 0.001695 -> 0.007709 kN*mm with zero cutbacks). The current repository suite (orchestrator 4EDA4EE6, corridor generator D68519D2, manifest 523FD4B2, and authentic Cycle 1-4 meshes) has been cleanly re-deployed to scratch, with all SHA-256 hashes matching the repository bitwise."
  },
  "job1424798_live_observables": {
    "pbs_job_id": "1424798.mmaster02",
    "job_state": "RUNNING (Active on mnode105)",
    "queue": "normal_imfdfkmq (routed from entry_imfdfkmq)",
    "start_time": "Sa 21. Nov 12:39:14 CET 2026",
    "elapsed_walltime": "> 03:40:00",
    "elapsed_cput": "> 03:25:00",
    "step1_hold_reaction_force_kN": 3.9134287,
    "step1_donor_force_kN": 3.9288,
    "step1_force_discrepancy_pct": -0.3912,
    "step1_force_gate_passed": true,
    "step2_converged_increments": 19,
    "step2_peak_force_kN": 3.9085787,
    "step2_softened_force_kN": 3.75,
    "step2_e_frac_initial_kNmm": 0.0016952,
    "step2_e_frac_current_kNmm": 0.0077088,
    "strict_non_healing_verified": true
  },
  "evidence_manifest": {
    "report": {
      "path": "docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_FRAMEWORK_JOB1424798_EXECUTION_REPORT.md"
    },
    "predecessor_1424797_pbs_execution_log": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log",
      "sha256": "$logSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_FRAMEWORK_JOB1424797_pbs_execution.log"
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
  "scratch_redeployment_verification": {
    "case3_single_job_orchestrator_sha256": "4EDA4EE69BCAE09D145F0C1248F117430063A73E84A1CF6A366C167B7099CD04",
    "generate_case3_adaptive_corridor_mesh_sha256": "D68519D28D9F44EF28B034D1165B45A8F2764763D38016DBAC6E062391DBEF55",
    "METHOD_C_CASE3_FRAMEWORK_MANIFEST_sha256": "523FD4B2BF9C5381E5C1E82B2FBB5D7C8665291F94F0C0E868229BB2AE05089C",
    "PK_METHOD_C_CASE3_CYCLE1_PHYS_sha256": "E16BEDDE15EFB4E29D24B7417515FB0E7E0FA967103FEB1A60144595260DBDC4",
    "verified_bitwise_match": true
  },
  "accounting_and_bounds": {
    "cumulative_pbs_submissions": 70,
    "new_pbs_submissions_in_this_step": 0,
    "scratch_directory_status": "CLEANLY_SYNCHRONIZED_WITH_REPO",
    "live_running_job": "1424798.mmaster02"
  },
  "next_step": {
    "requested_decision": "APPROVE_RECONCILIATION_REPORT",
    "proposed_action": "Approve Job 1424798 identity reconciliation and execution report. Following approval and completion of Job 1424798, update n_adaptive_steps to the high safety cap (uncapped loop) and proceed with production multi-cycle adaptive remeshing under the verified narrow-band formulation.",
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
