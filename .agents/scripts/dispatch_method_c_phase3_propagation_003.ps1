# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase3_propagation_003.ps1
# Dispatches Method C Phase 3: Job-3 Forward Crack Propagation Solve Execution & Observables
# (HND-METHOD-C-PHASE3-PROPAGATION-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE3-PROPAGATION-003"
$predecessorHandoffId = "HND-METHOD-C-PHASE3-PROPAGATION-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE3_FORWARD_PROPAGATION_EXECUTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$receiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_PROPAGATION_JOB3_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$extractorPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\extract_job3_observables.py"
$extractorSha = (Get-FileHash -Path $extractorPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

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
  "title": "Method C Phase 3: Step-2 Forward Crack Propagation Solve Execution & Observables Verification",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_EXECUTION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase3_forward_propagation",
    "numerical_uncertainty": "Can the Job-3 forward crack propagation solve (PK_METHOD_C_DEMO_PROPAGATION_JOB3) demonstrate continuous physical crack propagation across the 150 um ligament into the circular void ahead of the crack tip, capturing the void and producing structural load softening?",
    "expected_numerical_result": "PBS Job 1424609 solved 149 increments (24 Step 1, 125 Step 2); macroscopic crack d >= 0.95 propagated from notch tip (0.50, 0.50) across 150 um ligament, penetrated circular void perimeter at x = 0.65 mm (hole_reached = True), severed ligament into void, and extended to x_tip = 0.8957 mm; structural load reached peak F_max = 0.6487 kN at u2 = 0.006117 mm followed by post-peak softening to 0.2622 kN (-59.57% drop); physical cutback termination at u2 = 0.008756 mm (Exit 1, dt < 1e-8); 1 PBS job consumed (cumulative 60); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "execution_report": {
      "path": "docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_EXECUTION_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_PHASE3_FORWARD_PROPAGATION_EXECUTION_REPORT.md"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3_RECEIPT.json",
      "sha256": "$receiptSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3_RECEIPT.json",
      "job_id": "1424609.mmaster02",
      "exit_code": 1,
      "status": "CUTBACK_TERMINATION_AT_HOLE_CAPTURE",
      "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
      "solver_walltime_s": 2938.0,
      "solver_cpu_s": 1780.0,
      "total_increments": 149,
      "step1_increments": 24,
      "step2_increments": 125,
      "step1_end_RF2_kN": 0.548386,
      "peak_RF2_kN": 0.648681,
      "u2_at_peak_RF2_mm": 0.006117,
      "step2_end_RF2_kN": 0.262226,
      "step2_end_u2_mm": 0.008756,
      "post_peak_softening_demonstrated": true,
      "peak_damage_SDV1": 1.005501,
      "peak_history_SDV2_MPa": 4629.69,
      "final_crack_tip_x_mm": 0.895686,
      "final_crack_extension_mm": 0.395686,
      "hole_reached": true,
      "E_elastic_kNmm": 0.001148,
      "E_fracture_kNmm": 0.001593,
      "E_total_kNmm": 0.002741,
      "physical_elements": 10299,
      "layered_elements": 30897
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json",
      "sha256": "$summarySha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json"
    },
    "extractor_script": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/extract_job3_observables.py",
      "sha256": "$extractorSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/extract_job3_observables.py"
    },
    "executed_deck": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp",
      "sha256": "$deckSha",
      "github_url": "$githubBase/models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_PROPAGATION_JOB3.inp"
    },
    "unit_test_suite": {
      "path": "tests/unit/test_method_c_phase3_forward_propagation.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_phase3_forward_propagation.py",
      "pass_count": 27,
      "total_count": 27,
      "pass_percentage": 100.0
    }
  },
  "accounting_and_governance": {
    "pbs_jobs_authorized_this_turn": 1,
    "pbs_jobs_consumed_this_turn": 1,
    "max_new_pbs_for_next_turn": 0,
    "cumulative_pbs_submissions": 60,
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "canonical_bridge_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
    "unit_tests": "27/27 PASS (100%)",
    "master_goal_status": "OPEN",
    "next_recommended_milestone": "Method C Phase 4: Meeting animations, load-displacement plots, crack-extension plots, and supervisor presentation materials for the 2 December 2026 meeting."
  }
}

---
### Full Step-2 Forward Crack Propagation Solve Execution & Observables Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C PHASE 3 FORWARD PROPAGATION SOLVE VERIFICATION ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
