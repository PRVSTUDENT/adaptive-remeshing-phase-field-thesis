# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase2_job1_002.ps1
# Dispatches Method C Bridge Research Policy Reconciliation & HPC Outage Status
# (HND-METHOD-C-PHASE2-JOB1-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE2-JOB1-002"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-JOB1-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_BRIDGE_POLICY_RECONCILIATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 2: Bridge Research Policy Reconciliation & HPC Outage Status",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_BRIDGE_POLICY_RECONCILIATION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase2_job1_monitor",
    "numerical_uncertainty": "Can the BRIDGE_POLICY_SHA256 discrepancy (0F336675 vs CC3460C8) be definitively resolved with mathematical proof, canonical SHA C5959401 established, and the Panasas Scratch HPC outage accounted for without job submissions?",
    "expected_numerical_result": "BRIDGE_POLICY_SHA256 reconciled to canonical C5959401...; 0F336675 proved as uncommitted disk revision at 13:29 CET; Panasas scratch outage acknowledged; 0 new PBS jobs (cumulative 58 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "reconciliation_report": {
      "path": "docs/validation/METHOD_C_BRIDGE_POLICY_RECONCILIATION_REPORT.md",
      "sha256": "$reportSha"
    },
    "policy_provenance_reconciliation": {
      "claimed_sha_in_job1_handoff": "0F33667569A85735E90A6D3536B57EF6FB4265248E0CDA67C15325F9AAA22EFF",
      "claimed_sha_origin": "REAL uncommitted disk revision created at 13:29:44 CET adding method_c_phase2_job1_submit, inadvertently omitted from git add in commits 2b1798e88 and 0591548cc",
      "mathematical_proof": "Re-applying the single 13:29 CET diff to commit 2e070070c yields exact SHA 0F33667569A85735E90A6D3536B57EF6FB4265248E0CDA67C15325F9AAA22EFF",
      "canonical_policy_version": 3,
      "canonical_policy_commit": "95d58ef903b627819e44353f13a4cfef89e03e2a",
      "canonical_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
      "bit_identical_locations": [
        ".agents/scripts/bridge_research_policy.json",
        "origin/main on GitHub (commit 95d58ef90 and 3e2c14913)",
        "C:\\Users\\pruth\\OpenClawPAD\\ChatGPTBridge\\bridge_research_policy.json"
      ]
    },
    "hpc_cluster_status": {
      "outage_event": "Panasas Scratch storage outage (19 Nov ~14:34 CET)",
      "scheduler_state": "PBS server mmaster02 scheduling = False (suspended)",
      "queued_jobs": [
        "1424456.mmaster02 (F1861 Case 1 Reference)",
        "1424465.mmaster02 (F1861 Case 2 Reference)",
        "1424466.mmaster02 (F1861 Case 3 Reference)",
        "1424467.mmaster02 (F1861 Case 5 Reference)",
        "1424517.mmaster02 (Method C Demo Job-1 Baseline)"
      ],
      "actions_taken": "Zero new PBS submissions, zero job-dependent execution, non-polling suspension respected"
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
    "unit_tests": "10/10 PASS (100%)",
    "master_goal_status": "OPEN"
  }
}

---
### Full Reconciliation Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C BRIDGE POLICY RECONCILIATION HANDOFF ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
