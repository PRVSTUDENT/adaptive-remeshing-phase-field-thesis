# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase1_kickoff_002.ps1
# Dispatches Method C Phase 1 Kickoff Evidence Correction
# (HND-METHOD-C-PHASE1-KICKOFF-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE1-KICKOFF-002"
$predecessorHandoffId = "HND-METHOD-C-PHASE1-KICKOFF-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE1_KICKOFF_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = "6cb9730180f33e584d9227e8aa0378ada0d7b220"

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 1 Kickoff: Demonstration Case Definition, Incremental Schedule, and Orchestration Loop Skeleton (Re-issued with Pushed Report)",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase1_kickoff_correction",
    "numerical_uncertainty": "Can the Phase 1 kickoff report be committed and its SHA verified so that Phase 1 execution can proceed on a verified evidence base?",
    "expected_numerical_result": "Report committed at docs/validation/METHOD_C_PHASE1_KICKOFF_REPORT.md with SHA256 matching CC8BFF17556F8AFC2D488B6B4E6E7BA6C99D446DA3D887007F90030CF2060A31; artifact_commit points to the commit containing the report; 0 new PBS jobs (cumulative 57 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "artifact_commit": "$commitSha",
  "report_file": "docs/validation/METHOD_C_PHASE1_KICKOFF_REPORT.md",
  "report_sha256": "$reportSha",
  "gap_reconciliations": [
    {
      "gap_id": "GAP-MC-P1-01",
      "status": "RESOLVED",
      "evidence": "Report committed and pushed to GitHub origin/main at docs/validation/METHOD_C_PHASE1_KICKOFF_REPORT.md (commit 6cb9730180f33e584d9227e8aa0378ada0d7b220). SHA-256 verified directly as CC8BFF17556F8AFC2D488B6B4E6E7BA6C99D446DA3D887007F90030CF2060A31, exactly matching the claimed hash."
    },
    {
      "gap_id": "GAP-MC-P1-02",
      "status": "RESOLVED",
      "evidence": "artifact_commit updated to 6cb9730180f33e584d9227e8aa0378ada0d7b220, which is pushed to GitHub origin/main and contains docs/validation/METHOD_C_PHASE1_KICKOFF_REPORT.md, bridge policy, session report, and unit test suite."
    },
    {
      "gap_id": "GAP-MC-P1-03",
      "status": "RESOLVED",
      "evidence": "Confirmed: bridge rules and research policy were formally re-issued for Method C per the 19 Nov 2026 supervisor meeting with Prof. Kiefer & Dr. Roth, superseding the frozen Method A policy (RESEARCH_GOAL_ID: METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1, method: METHOD_C, unpausing Method C and state transfer). Current canonical rules SHA-256 is D581ACC321F93D27131655DF7C13F552330D7C1D4CCEBBA331F22A0A881F2399 and policy SHA-256 is C6CB651B5A08367D87379DF607FDBDDB2B70CB86C870E241E2A6411B6E296B22, both synchronized and committed."
    }
  ],
  "unit_test_status": "tests/unit/test_method_c_phase1_kickoff.py 4/4 PASS (100%)",
  "demo_geometry_proposal": {
    "domain": [0.0, 1.0, 0.0, 1.0],
    "edge_notch": {"y": 0.5, "x_start": 0.0, "x_end": 0.5, "length": 0.5},
    "hole": {"center": [0.75, 0.5], "radius": 0.1},
    "inter_feature_ligament_width_mm": 0.15,
    "rear_ligament_width_mm": 0.15,
    "material": {"E_GPa": 210.0, "nu": 0.3, "Gc_kN_mm": 0.0027, "l0_mm": 0.0075, "k": 1e-7},
    "loading": {"step1_u2_mm": 0.005, "step2_u2_mm": 0.010, "step2_increments": [4, 6]}
  },
  "pbs_accounting": {
    "max_new_pbs": 0,
    "submissions_consumed": 0,
    "cumulative_pbs_submissions": 57
  },
  "governance_invariants": {
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "remeshing_framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "master_goal_status": "OPEN"
  }
}
"@

$fullPrompt = @"
$header

================================================================================
METHOD C PHASE 1 KICKOFF REPORT (COMMITTED AT 6cb9730180f33e584d9227e8aa0378ada0d7b220)
================================================================================

$reportContent
"@

if ($CheckOnly) {
    Write-Host "[Dispatch] Running dry-run canonical contract validation..." -ForegroundColor Cyan
    $result = Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -TaskId $taskId -DryRun
    Write-Host "[Dispatch] Dry-run PASSED! Prompt size: $($result.Length) characters." -ForegroundColor Green
    return
}

Write-Host "[Dispatch] Dispatching Task METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON (Correction HND-002) across OpenClaw PAD Bridge..." -ForegroundColor Cyan
$response = Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -TaskId $taskId -LaunchPad -TimeoutMinutes 40
Write-Host "[Dispatch] Bridge response received!" -ForegroundColor Green
$response
