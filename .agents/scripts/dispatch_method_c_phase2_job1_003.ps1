# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase2_job1_003.ps1
# Dispatches Method C Phase 2: Job-1 Baseline Solve Verification & Observables Extraction
# (HND-METHOD-C-PHASE2-JOB1-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE2-JOB1-003"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-JOB1-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE2_JOB1_BASELINE_OBSERVABLES_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$receiptPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_COARSE_JOB1_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\289_method_c_demo_case\PK_METHOD_C_DEMO_COARSE_JOB1_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 2: Job-1 Baseline Solve Verified & Step-1 Observables Extracted",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE2_JOB1_BASELINE_OBSERVABLES_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase2_job1_extract",
    "numerical_uncertainty": "Does the Step-1 baseline solve (Increment 50, u2=0.0050 mm) provide a verified physical pre-peak state with intact bulk material, reaction force continuity (RF2=0.556024 kN), and localized crack-tip damage (d=0.169178) ready for state/history transfer?",
    "expected_numerical_result": "PBS Job 1424517 completed Exit 0 with zero errors (Walltime 1,511s, CPU 909s); Step-1 observables extracted: u2=0.0050 mm, RF2=0.556024 kN, peak damage d=0.169178 (notch tip), mean damage d=0.0086 (bulk intact), peak history H=0.249872 MPa, MISESERI=0.0 (inactive under UMAT); 0 new PBS jobs (cumulative 58 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_PHASE2_JOB1_BASELINE_OBSERVABLES_REPORT.md",
      "sha256": "$reportSha"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_COARSE_JOB1_RECEIPT.json",
      "sha256": "$receiptSha"
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_COARSE_JOB1_SUMMARY.json",
      "sha256": "$summarySha"
    },
    "solver_observables": {
      "pbs_job_id": "1424517.mmaster02",
      "job_name": "PK_METHOD_C_DEMO_COARSE_JOB1",
      "exit_code": 0,
      "status": "COMPLETED_EXIT0",
      "solver_status_sta": "THE ANALYSIS HAS COMPLETED SUCCESSFULLY",
      "solver_msg_errors": 0,
      "walltime_s": 1511.0,
      "cpu_time_s": 909.0,
      "step1_increments": 50,
      "step1_end_u2_mm": 0.0050,
      "RF2_kN": 0.5560243725776672,
      "RF2_N": 556.0243725776672,
      "peak_damage_SDV1": 0.1691775918006897,
      "mean_damage_SDV1": 0.008609119857237718,
      "bulk_damage_intact_verified": true,
      "peak_history_SDV2_MPa": 0.2498721033334732,
      "mean_history_SDV2_MPa": 0.0016202055379032697,
      "peak_miseseri": 0.0,
      "miseseri_note": "Abaqus built-in MISESERI error indicator is 0.0 because companion elements use *USER MATERIAL (UMAT_MAT); Abaqus error indicator recovery is only active for native *ELASTIC material cards.",
      "physical_elements": 2920,
      "layered_elements": 8760,
      "nodes_count": 3017
    },
    "accounting": {
      "authorized_submissions": 0,
      "consumed_submissions": 0,
      "cumulative_pbs": 58,
      "max_new_pbs": 0
    }
  },
  "governance": {
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "canonical_bridge_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
    "unit_tests": "13/13 PASS (100%)",
    "master_goal_status": "OPEN"
  }
}

---
### Full Baseline Observables Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C PHASE 2 JOB-1 OBSERVABLES HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
