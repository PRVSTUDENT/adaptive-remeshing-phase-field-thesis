# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1823_framework_coarsening_auth_001.ps1
# Dispatches Task F1823 Framework Kwargs Comparison, Bounded Coarsening Sweep, and Targeted Donor Investigation
# (HND-F1823-FRAMEWORK-COARSENING-DONORS-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1823-FRAMEWORK-COMPARISON-COARSENING-AND-TARGETED-DONORS"
$handoffId = "HND-F1823-FRAMEWORK-COARSENING-DONORS-001"
$predecessorHandoffId = "HND-F1822-MINMAX-CONTROL-VERIFICATION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1823_FRAMEWORK_COARSENING_TARGETED_DONORS_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$headCommit = git rev-parse HEAD
$commitSha = $headCommit.Trim()

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1823: Framework Kwargs Comparison, Bounded Coarsening Sweep, and Targeted Donor Investigation",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Can like-for-like comparison prove that the 62,611 vs 63,210 element difference is zero code drift and purely resolved arguments? Can bounded coarsening sweeps achieve Gate 06 >= 2.0x in Cases 2 and 3? Which specific omitted donor states causally supply coverage in Cases 2 and 3?",
    "expected_numerical_result": "Zero framework code discrepancy between old 4276A5DC... and enhanced 0578156E... under UNIFORM_ERROR (identical 62,611 el at 3.0%, 25,461 el at 4.5%, 100% bitwise body SHA parity); Case 3 width bug fixed in run_f1816_step2_master.py line 76 to plate width [50-65mm] (baseline f_3l0 shifts from 0.49% to 0.55%); F1812 Case 1 eta_R=4.5% provenance verified as CLI override; Gate 06 coarsening ratio plateaus at ~1.56x for Case 2 and 1.72x for Case 3 (< 2.0x threshold), preserving F1812 baselines; Case 2 ablation proves State 1 is required for notch initiation (notch coverage collapses to 26.18%) and State 4 is required for outer boundary coverage (distal coverage collapses to 83.97%); Case 3 ablation proves State 1 is required for primary notch crack (primary coverage collapses to 3.57%) and State 3 is uniquely responsible for secondary corridor propagation (fine elements within 3*l0 drop to 0.00% and coverage drops to 50.25%); 0 new PBS jobs; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
      "donor_step": "RECOVERY_STEP",
      "donor_frame_index": 2,
      "indicator_frame_range": "Multi-state recovery donor envelopes across authentic crack propagation states",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Does Task F1823 satisfy all three sequential steps of the user goal directive: (1) Step 1: compare old vs enhanced framework kwargs, confirm zero code drift, fix Case 3 width metric bug, and document F1812 Case 1 provenance; (2) Step 2: execute bounded coarsening sweep across Cases 2 and 3 with Cases 1 & 5 controls, confirm Gate 06 plateau and preserve baselines; (3) Step 3: conduct selective targeted donor ablation across Cases 2 and 3, identify specific causal states supplying coverage, report within-3*l0 fractions alongside coverage and quality, and maintain all governance invariants?",
    "evaluation_criteria": [
      "1. Step 1 Framework Comparison: models/pandey_kumar_mode1/267_f1823_investigation/step1_comparison/ proves old 4276A5DC... and enhanced 0578156E... generate bitwise identical meshes under UNIFORM_ERROR (62,611 el / D36603D8... at 3.0%, 25,461 el / 50CB4E3C... at 4.5%), proving zero framework code discrepancy.",
      "2. Step 1 Bug Fix & Provenance: run_f1816_step2_master.py line 76 corrected to ((50.0, 60.0), (65.0, 60.0)), bounding segment within plate width (65mm); recomputed concentration percentages verified; F1812 Case 1 eta_R=4.5% proven as explicit CLI override.",
      "3. Step 2 Coarsening Sweep: models/pandey_kumar_mode1/267_f1823_investigation/step2_coarsening/ confirms Gate 06 coarsening ratio plateaus at ~1.56x for Case 2 and 1.72x for Case 3 (< 2.0x threshold); Cases 1 and 5 controls 100% bitwise identical to F1812 baselines; F1812 baselines preserved.",
      "4. Step 3 Targeted Donor Investigation: models/pandey_kumar_mode1/267_f1823_investigation/step3_donors/ proves State 1 is required for notch initiation in C2 and C3 (notch coverage collapses to 26.18% in C2, 3.57% in C3); State 4 is required for outer boundary coverage in C2 (outer coverage collapses to 83.97%); State 3 is uniquely responsible for secondary corridor propagation in C3 (fine elements within 3*l0 drop to 0.00% and coverage drops to 50.25%).",
      "5. Width Metrics Reporting: Within-3*l0 fractions reported alongside actual coverage, element counts, and mesh quality across all investigations.",
      "6. Unit Testing: 8/8 unit tests in tests/unit/test_f1823_investigation.py PASS, verifying invariants, Step 1 parity, Step 2 sweep plateau, Step 3 donor ablation, and visual figures.",
      "7. Visual Figures: results/figures/fig_f1823_coarsening_and_donor_investigation.png and .pdf synthesized across all three steps.",
      "8. Governance Invariants: Framework 0578156E..., production UEL CE8D5EDC..., 0 new PBS jobs (cumulative 35 preserved), and MASTER_GOAL_STATUS = OPEN strictly maintained."
    ]
  },
  "image_manifest": [
    {
      "case_id": "fig_f1823_coarsening_and_donor_investigation_png",
      "image_path": "results/figures/fig_f1823_coarsening_and_donor_investigation.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1823_coarsening_and_donor_investigation.png",
      "artifact_hash": "0F3830773AD09A97370BD28D142EE2E809AD348CD660C4260A5D7A86F94F7C51"
    },
    {
      "case_id": "fig_f1823_coarsening_and_donor_investigation_pdf",
      "image_path": "results/figures/fig_f1823_coarsening_and_donor_investigation.pdf",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1823_coarsening_and_donor_investigation.pdf",
      "artifact_hash": "53566DF29CFF4CB7301FAAF5D9D7C75AC75ECFCF56EF685473A51F9F4EFDA011"
    }
  ],
  "checkpoint_commit": "$commitSha",
  "governance": {
    "cumulative_pbs_submissions": 35,
    "max_new_pbs": 0,
    "submissions_consumed": 0,
    "production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "shared_framework_sha256": "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D",
    "master_goal_status": "OPEN",
    "control_case1_elements": 25461,
    "control_case5_elements": 15466
  }
}
"@

$combinedText = $header + "`n`n" + $reportContent + "`n`n" + $rulesContent

if ($CheckOnly) {
    Write-Host "=== CHECK-ONLY MODE ==="
    Write-Host "Target Handoff ID: $handoffId"
    Write-Host "Commit SHA: $commitSha"
    Write-Host "Combined text length: $($combinedText.Length) characters"
    Write-Host "Header check:"
    Write-Host ($header.Substring(0, [Math]::Min(500, $header.Length)))
    return
}

# Perform guarded publication across OpenClaw PAD Bridge
Invoke-ChatGPTBridge -PromptText $combinedText -HandoffId $handoffId
