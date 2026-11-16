# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1808_four_case_reproducibility_001.ps1
# Dispatches Task F1808 Four-Case Native-MISESERI Reproducibility Investigation and Regression Audit
# (HND-F1808-FOUR-CASE-REPRODUCIBILITY-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1808-FOUR-CASE-NATIVE-MISESERI-REPRODUCIBILITY-AND-REGRESSION"
$handoffId = "HND-F1808-FOUR-CASE-REPRODUCIBILITY-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1808_FOUR_CASE_NATIVE_MISESERI_REPRODUCIBILITY_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "HND-F1807-FOUR-CASE-REGRESSION-001",
  "task_id": "$taskId",
  "title": "Task F1808: Four-Case Native-MISESERI Reproducibility Investigation and Regression Audit (Cases 1, 2, 3, 5)",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "four_case_regression",
    "numerical_uncertainty": "Why did the F1807 Case 2 native-MISESERI mesh produce 22,656 elements while F1806 produced 22,924 elements under the reportedly identical post-breach donor and 1.8% target, and does the unified framework reproduce the full four-benchmark baseline deterministically under isolated execution?",
    "expected_numerical_result": "A controlled four-case reproducibility and regression experiment. Identified root cause of Case 2 element difference as an input defect in f1807_case2_native_miseseri.json (notch_length=0.4 mm vs 0.5 mm altering domain polygon); proved complete determinism by restoring notch_length=0.5 mm in f1808_case2_native_miseseri.json, reproducing EXACTLY 22,924 elements (22,346 quads, 578 tris) with 100.000% bitwise body hash parity matching F1806 (35178C924EB...); executed fresh isolated Abaqus CAE runs for all four benchmarks via run_f1808_master.py and run_f1808_single_case.py archiving journals case_1..5_abaqus.rpy; Case 1 achieves 14,087 elements (97.02% quads, tip 100% <= l0/2, coarsening 2.54x); Case 2 achieves 22,924 elements (97.48% quads, distal 89.41% <= l0/2, outer distal gate retained as FAIL 28.02%); Case 3 achieves 26,746 elements (97.39% quads, secondary corridor 58.32% <= l0, secondary gate retained as INCOMPLETE_RESOLUTION, coarsening 2.48x); Case 5 achieves 15,466 elements (97.90% quads, upper corridor 99.04% <= l0, coarsening 2.12x); all Gates 01-07 PASS across all 4 cases; generated 12 diagnostic PNGs and 4-panel publication synthesis figure; 13/13 unit tests PASS, 60/60 regression suite PASS; 0 new PBS jobs, cumulative 35 preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb",
      "donor_sha256": "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959",
      "donor_step": "AUTHENTIC_CAUSAL_DONOR_SUITE_STEP",
      "donor_frame_index": 1,
      "indicator_frame_range": "Four canonical benchmark donor states at certified causal horizons: Case 1 pre-analysis Step-1 Frame 10 (t=1.0s); Case 2 post-breach hole-arrest recovery Frame 1 (t=1.0s, physical t=0.3737s); Case 3 State-2 recovery Frame 1 (t=1.0s, physical uy=0.20mm); Case 5 pre-crack Step-2 Frame 171 (t=0.485s)",
      "held_out_later_solution": "All future fracture propagation and failure frames held out as unobserved future solutions across all four benchmarks",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0,
      "cases": {
        "case_1": {
          "benchmark": "Mode-I Edge Crack (1.0x1.0 mm, l0=7.5 um)",
          "donor_odb": "models/pandey_kumar_mode1/257_f1807_four_case_regression/case1/PK_F1807_CASE1_COARSE_DONOR.odb",
          "donor_sha256": "DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0",
          "elements_total": 14087,
          "quad_percent": 97.02,
          "min_det_j": 2.479e-7,
          "max_aspect_ratio": 2.640,
          "h_min_um": 0.706,
          "tip_pct_le_l0_half": 100.0,
          "coarsening_ratio": 2.54,
          "literature_target": 13941,
          "literature_parity_pct": 1.05
        },
        "case_2": {
          "benchmark": "Off-Axis Hole Plate (1.0x1.0 mm, l0=7.5 um)",
          "donor_odb": "models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb",
          "donor_sha256": "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959",
          "elements_total": 22924,
          "quad_percent": 97.48,
          "min_det_j": 2.870e-7,
          "max_aspect_ratio": 2.500,
          "h_min_um": 0.768,
          "distal_pct_le_l0_half": 89.41,
          "outer_boundary_band_min_h_um": 2.140,
          "combined_outer_ligament_pct_le_l0_half": 28.02,
          "coarsening_ratio": 2.10,
          "scientific_gate_outer_distal": "FAIL"
        },
        "case_3": {
          "benchmark": "Notched Plate with Pins (65x120 mm, l0=285 um)",
          "donor_odb": "models/pandey_kumar_mode1/253_f1803_case3_accurate_recovery/SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb",
          "donor_sha256": "965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB",
          "elements_total": 26746,
          "quad_percent": 97.39,
          "min_det_j": 7.650e-4,
          "max_aspect_ratio": 3.862,
          "h_min_mm": 0.0470,
          "secondary_corridor_pct_le_l0": 58.32,
          "secondary_corridor_min_h_mm": 0.0738,
          "coarsening_ratio": 2.48,
          "scientific_gate_secondary_corridor": "INCOMPLETE_RESOLUTION"
        },
        "case_5": {
          "benchmark": "Seven-Hole Plate (1.0x1.0 mm, l0=8.0 um)",
          "donor_odb": "models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb",
          "donor_sha256": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E",
          "elements_total": 15466,
          "quad_percent": 97.90,
          "min_det_j": 3.922e-7,
          "max_aspect_ratio": 2.374,
          "h_min_um": 0.979,
          "upper_corridor_pct_le_l0": 99.04,
          "lower_corridor_pct_le_l0": 94.26,
          "coarsening_ratio": 2.12,
          "literature_target": 15714,
          "literature_parity_pct": -1.58
        }
      }
    }
  },
  "report_path": "docs/validation/F1808_FOUR_CASE_NATIVE_MISESERI_REPRODUCIBILITY_REPORT.md",
  "report_sha256": "165A9BEDB8A0FFBDA3E9BF7DCEB6770F4234C5D22D77E578A7547270673C0EA3",
  "receipt_path": "models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json",
  "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "framework_sha256": "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
  "cumulative_pbs_submissions": 35,
  "max_new_pbs_submissions": 0,
  "submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "review_instructions": "Review Task F1808 Four-Case Native-MISESERI Reproducibility Investigation and Regression Audit. Verify: (1) Resolved F1806 vs F1807 Case 2 element count discrepancy by discovering input defect notch_length=0.4 mm vs 0.5 mm in f1807 config altering CAD domain polygon; (2) Proved 100.000% determinism by restoring notch_length=0.5 mm in f1808 config, reproducing EXACTLY 22,924 elements (22,346 quads, 578 tris) with 100.000% bitwise body hash parity matching F1806 (35178C924EB...); (3) Executed fresh isolated Abaqus CAE sessions for Cases 1, 2, 3, 5 via run_f1808_master.py and run_f1808_single_case.py with archived journals case_1..5_abaqus.rpy; (4) Case 1 achieves 14,087 elements (+1.05% vs literature) with 100% tip resolution <= l0/2 and 2.54x coarsening; (5) Case 2 achieves 22,924 elements with distal 89.41% <= l0/2 and combined outer ligament 28.02% <= l0/2, strictly retaining SCIENTIFIC_GATE_OUTER_DISTAL as FAIL; (6) Case 3 achieves 26,746 elements with secondary corridor 58.32% <= l0, local min h = 0.0738 mm << l0/2 distinguished from complete corridor resolution, strictly retaining SCIENTIFIC_GATE_SECONDARY_CORRIDOR as INCOMPLETE_RESOLUTION; (7) Case 5 achieves 15,466 elements (-1.58% vs literature) with upper corridor 99.04% <= l0 and 2.12x coarsening; (8) Standard Gates 01-07 PASS across all four benchmarks (all quad fractions >= 97.0%, zero nonpositive Jacobians, max AR <= 3.862 <= 4.0, coarsening >= 2.10x); (9) 12 diagnostic PNGs and 4-panel publication synthesis figure archived; (10) Active regression suite 60/60 PASS in 2.83s; zero new PBS jobs consumed, cumulative 35 preserved, and MASTER_GOAL_STATUS = OPEN."
}
"@

$fullPrompt = "$header`n`n$reportContent`n`n---\n## CANONICAL BRIDGE RULES (MANDATORY INVARIANTS)\n`n$rulesContent"

Write-Host "Prepared Task F1808 Bridge Payload: $($fullPrompt.Length) characters." -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "CheckOnly switch active. Validating canonical bridge policy..." -ForegroundColor Yellow
    Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -DryRun
    Write-Host "Pre-flight validation successful." -ForegroundColor Green
    exit 0
}

Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId
