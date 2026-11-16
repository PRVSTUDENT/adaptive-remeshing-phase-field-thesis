# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1805_case2_distal_sensitivity_001.ps1
# Dispatches Task F1805 Case 2 Outermost Distal Native-MISESERI Target Sensitivity
# (HND-F1805-CASE2-DISTAL-SENSITIVITY-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY"
$handoffId = "HND-F1805-CASE2-DISTAL-SENSITIVITY-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1805_CASE2_OUTERMOST_DISTAL_SENSITIVITY_REPORT.md"
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
  "predecessor_correlation_id": "HND-F1804-CASE2-DISTAL-RECOVERY-001",
  "task_id": "$taskId",
  "title": "Task F1805: Case 2 Outermost Distal Native-MISESERI Target Sensitivity",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "causal_remeshing_test",
    "numerical_uncertainty": "Can a controlled global tightening of the genuine native Abaqus MISESERI error target improve mesh resolution in the still-underresolved outermost Case 2 distal ligament x=0.90-1.00 mm, while keeping the physical mesh quality and element count acceptable, without prescribed future crack-path refinement or synthetic MISESERI?",
    "expected_numerical_result": "One fresh Case 2 physical adaptive mesh using the unchanged F1804 source donor, same causal horizon and shared engine, changing only native error_target from 2.3% to 1.9%. Independently evaluate the five distal spatial bins x=[0.75,0.80], [0.80,0.85], [0.85,0.90], [0.90,0.95] and [0.95,1.00] mm at y=[0.55,0.75] mm. Compare count-based and area-weighted h<=l0 and h<=l0/2 coverage against F1804 and F1795, especially the final two bins, while measuring retained primary h/l0, element count, quadrilateral fraction, signed Jacobians, maximum aspect ratio and consistent far-to-distal coarsening. Preserve failed outcomes if the outermost ligament remains coarse or mesh cost becomes excessive.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "post_breach_state_donor_status": "QUALIFIED_AUTHENTIC_POST_BREACH_HOLE_ARREST_RECOVERY_DONOR",
      "donor_path": "models/pandey_kumar_mode1/254_f1804_case2_distal_recovery/PK_HOLE_STATE_POSTBREACH_RECOVERY.odb",
      "donor_sha256": "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959",
      "donor_step": "RECOVERY_STEP",
      "donor_frame_index": 1,
      "indicator_frame_range": "RECOVERY_STEP frame 1 (t = 1.0 s, uy = 0.007616 mm, primary crack breached and arrested at off-axis hole, exact elementwise degraded modulus E_i = 210000.0 * [(1-d_i)^2 + 10^-7] MPa)",
      "held_out_later_solution": "Future distal crack initiation and propagation frames (uy > 0.007616 mm) strictly held out as unobserved future solution",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0,
      "physical_mesh_path": "models/pandey_kumar_mode1/255_f1805_case2_distal_sensitivity/PK_F1805_CASE_2_ADAPT_PHYS.inp",
      "physical_mesh_sha256": "4DA79E199FE7A9F8C6EBA54B2BCBD49A79573357B577F80259E3C3120D6CD8FD",
      "mesh_body_sha256": "E0F6A5C6D8DF0C879E1E9990302C6FB06E0D156CA5B9BB0236EEC0F5880980D3",
      "elements_total": 20281,
      "quad_percent": 97.35,
      "min_det_j": 1.307e-7,
      "max_aspect_ratio": 2.687,
      "median_aspect_ratio": 1.201,
      "broad_distal_corridor_mean_h": 0.002669,
      "broad_distal_corridor_min_h": 0.000500,
      "broad_distal_corridor_pct_le_l0_count": 99.81,
      "broad_distal_corridor_pct_le_l0_half_count": 86.28,
      "broad_distal_corridor_pct_le_l0_half_area": 56.35,
      "bin_x_0_90_to_0_95_pct_le_l0_half_count": 21.59,
      "bin_x_0_90_to_0_95_pct_le_l0_half_area": 11.21,
      "bin_x_0_95_to_1_00_pct_le_l0_count": 96.59,
      "bin_x_0_95_to_1_00_pct_le_l0_half_count": 0.00,
      "combined_x_0_90_to_1_00_pct_le_l0_half_count": 13.90,
      "combined_x_0_90_to_1_00_pct_le_l0_half_area": 5.65,
      "primary_corridor_pct_le_l0_half_count": 34.31,
      "far_to_distal_coarsening_ratio": 4.20,
      "scientific_gate_outer_distal": "FAIL"
    }
  },
  "report_path": "docs/validation/F1805_CASE2_OUTERMOST_DISTAL_SENSITIVITY_REPORT.md",
  "report_sha256": "75EA97EAC05B810311EB208643CDD1722B4BFF70F82FBE4674B91AF002F8A850",
  "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "framework_sha256": "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
  "cumulative_pbs_submissions": 35,
  "max_new_pbs_submissions": 0,
  "submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "review_instructions": "Review Task F1805 Case 2 Outermost Distal Native-MISESERI Target Sensitivity. Verify: (1) Reused identical verified F1804 hole-arrest recovery donor PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (35E9DC19..., 7,417,896 bytes); (2) Preserved geometry (OffAxisHoleMode1Adapter), sizing bounds h in [0.0015, 0.020] mm, refinement factor 10, indicator MISESERI, shared framework, and frozen UEL strictly invariant; (3) Tested sole numerical control error_target reduced from 2.3% to 1.9%; (4) Controlled execution of native RemeshingRule and adaptiveRemesh() pass under unchanged framework, preserving replay journal abaqus.rpy (4,770 bytes) demonstrating Exit 0; (5) Independent FE quality audit of PK_F1805_CASE_2_ADAPT_PHYS.inp (20,281 elements, 97.35% quads, positive Jacobians min det(J) = 1.307e-7 > 0, max AR 2.687 <= 4.0, median 1.201, 0 violations); (6) Broad distal corridor resolution enhancement: count-based % <= l0/2 reached 86.28% (+14.18 pts gain vs F1804), area-weighted % <= l0/2 reached 56.35% (+20.05 pts), min h dropped to 0.50 um (<< l0/2 = 3.75 um); (7) Detailed five distal spatial bins (y in [0.55, 0.75] mm): bin x=0.85-0.90 surged to 89.10% <= l0/2 (area 78.01%); bin x=0.90-0.95 achieved an 18.7x surge from 1.15% to 21.59% <= l0/2 (area from 0.36% to 11.21%, 99.58% <= l0); boundary band x=0.95-1.00 surged to 96.59% <= l0 (area 94.53%), but retained 0.00% <= l0/2 (min h = 3.789 um vs 3.75 um); combined outer ligament x=0.90-1.00 reached 13.90% <= l0/2 (area 5.65%) vs 0.71% in F1804; (8) Primary corridor partial recovery to 953 elements (34.31% <= l0/2, 96.33% <= l0); (9) Computational efficiency: 20,281 elements (< 40,000 ceiling, -43.11% smaller than F1795 baseline), far-to-distal coarsening ratio 4.20x >= 2.0x; (10) Gate outcomes: standard Gates 01-07 PASS, SCIENTIFIC_GATE_OUTER_DISTAL retained as FAIL as authentic physical proof that single-snapshot recovery cannot overcome continuum error decay near the traction-free boundary; (11) Zero new PBS jobs, cumulative preserved at 35, production UEL frozen, and MASTER_GOAL_STATUS = OPEN."
}
"@

$fullPrompt = "$header`n`n$reportContent`n`n---\n## CANONICAL BRIDGE RULES (MANDATORY INVARIANTS)\n`n$rulesContent"

Write-Host "Prepared Task F1805 Bridge Payload: $($fullPrompt.Length) characters." -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "CheckOnly switch provided. Payload validated without dispatch." -ForegroundColor Green
    return
}

# Dispatch via guarded Invoke-ChatGPTBridge
Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -TaskId $taskId
