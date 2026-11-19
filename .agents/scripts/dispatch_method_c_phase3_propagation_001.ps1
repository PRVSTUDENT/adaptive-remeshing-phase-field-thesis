# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase3_propagation_001.ps1
# Dispatches Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh
# (HND-METHOD-C-PHASE3-PROPAGATION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE3-PROPAGATION-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-JOB2-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$deckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$generatorPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\build_demo_propagation_job3_deck.py"
$generatorSha = (Get-FileHash -Path $generatorPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\METHOD_C_DEMO_JOB3_AUTHORIZATION.json"
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_phase3_forward_propagation.py"
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
  "title": "Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase3_forward_propagation",
    "numerical_uncertainty": "Can the Step-2 forward propagation package be prepared on the re-equilibrated refined mesh, advancing the load from u2=0.0050 to 0.0100 mm in 4-6 increments with the Job-2 state as initial condition?",
    "expected_numerical_result": "Step-2 forward crack propagation package staged; production deck PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp assembled with 30,897 layered elements (10,299 physical elements, 96.84% quads) advancing u2 from 0.0050 mm to 0.0100 mm in 4-6 increments; Job-2 re-equilibrated state carried forward via *INITIAL CONDITIONS, TYPE=SOLUTION; NOTE-MC-J2-01 formally clarified (530a0abb executed deck vs E75B82FC preflight draft); horizontal crack trajectory along y=0.50 mm into hole at (0.75, 0.50) mm documented; 24/24 Method C unit tests PASS; 0 new PBS jobs submitted (cumulative count 59 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "propagation_report": {
      "path": "docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md"
    },
    "job3_production_deck": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp",
      "physical_elements": 10299,
      "layered_elements": 30897,
      "nodes": 10299,
      "step1_schedule": "u2 = 0.0050 mm fixed-load re-equilibration (dt_init=0.01, dt_max=0.05)",
      "step2_schedule": "u2 = 0.0050 to 0.0100 mm positive forward pull (dt_init=0.10, dt_max=0.20, dt_min=1e-8, 4-6 nominal increments)",
      "boundary_modification": "*BOUNDARY, OP=MOD N_RP, 2, 2, 0.0100"
    },
    "deck_generator_script": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/build_demo_propagation_job3_deck.py",
      "sha256": "$generatorSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/build_demo_propagation_job3_deck.py"
    },
    "authorization_manifest": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB3_AUTHORIZATION.json",
      "sha256": "$manifestSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/METHOD_C_DEMO_JOB3_AUTHORIZATION.json",
      "max_new_pbs_submissions": 0,
      "cumulative_pbs_submissions": 59
    },
    "unit_test_suite": {
      "path": "tests/unit/test_method_c_phase3_forward_propagation.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_phase3_forward_propagation.py",
      "pass_count": 24,
      "total_count": 24,
      "pass_percentage": 100.0
    }
  },
  "accounting_and_governance": {
    "pbs_jobs_authorized_this_turn": 0,
    "pbs_jobs_consumed_this_turn": 0,
    "max_new_pbs_for_next_turn": 0,
    "cumulative_pbs_submissions": 59,
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "canonical_bridge_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
    "unit_tests": "24/24 PASS (100%)",
    "master_goal_status": "OPEN",
    "next_recommended_milestone": "Authorize single bounded PBS solve for Job-3 (PK_METHOD_C_DEMO_PROPAGATION_JOB3, 16 CPUs SMP, 48 GB, 72h) to simulate forward crack propagation toward the central hole."
  }
}

---
### Full Step-2 Forward Crack Propagation Package Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C PHASE 3 FORWARD PROPAGATION PACKAGE HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
