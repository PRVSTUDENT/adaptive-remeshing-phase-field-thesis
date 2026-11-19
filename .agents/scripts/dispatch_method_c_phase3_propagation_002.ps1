# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase3_propagation_002.ps1
# Dispatches Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh (Re-Issue with GAP-MC-P3-01 Resolved)
# (HND-METHOD-C-PHASE3-PROPAGATION-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE3-PROPAGATION-002"
$predecessorHandoffId = "HND-METHOD-C-PHASE3-PROPAGATION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$job2DeckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp"
$job2DeckSha = (Get-FileHash -Path $job2DeckPath -Algorithm SHA256).Hash.ToUpper()

$job2ReceiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json"
$job2ReceiptSha = (Get-FileHash -Path $job2ReceiptPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Phase 3: Step-2 Forward Crack Propagation Package on Refined Mesh (Re-Issue with GAP-MC-P3-01 Resolved)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_PACKAGE_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase3_forward_propagation",
    "numerical_uncertainty": "Can the executed Job-2 deck (SHA 530a0abb) be committed to the repo so the ledger hash matches a committed file, and the Job-3 forward propagation package be re-issued with the provenance gap closed?",
    "expected_numerical_result": "Executed Job-2 deck (SHA 530a0abb, without TYPE=DISPLACEMENT) committed at the Job-2 deck path in commit ccb7c1bb0 / $commitSha; ledger hash matches the committed file; Job-3 package (deck FFE25C2A) re-issued with the provenance gap closed; 0 new PBS jobs (cumulative 59 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "gap_mc_p3_01_resolution": {
      "job2_executed_deck": {
        "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp",
        "sha256": "$job2DeckSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp",
        "committed_commit": "ccb7c1bb0",
        "ledger_hash_comparison": "530a0abbdedcd298504cd28f80b6e19acbcf5a7945ea9e46981a9ee4b8ff72cb",
        "ledger_status": "MATCHES_EXACTLY"
      },
      "job2_transfer_receipt": {
        "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json",
        "sha256": "$job2ReceiptSha",
        "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_REFINED_STEP1_TRANSFER_RECEIPT.json"
      }
    },
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

Write-Output "=== DISPATCHING METHOD C PHASE 3 FORWARD PROPAGATION PACKAGE RE-ISSUE ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
