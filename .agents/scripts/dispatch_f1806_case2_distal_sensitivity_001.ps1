# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1806_case2_distal_sensitivity_001.ps1
# Dispatches Task F1806 Case 2 Outermost Distal Native-MISESERI Target Sensitivity at 1.8%
# (HND-F1806-CASE2-DISTAL-SENSITIVITY-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1806-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-1P8PCT"
$handoffId = "HND-F1806-CASE2-DISTAL-SENSITIVITY-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1806_CASE2_OUTERMOST_DISTAL_SENSITIVITY_REPORT.md"
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
  "predecessor_correlation_id": "HND-F1805-CASE2-DISTAL-SENSITIVITY-001",
  "task_id": "$taskId",
  "title": "Task F1806: Case 2 Outermost Distal Native-MISESERI Target Sensitivity at 1.8%",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "causal_remeshing_test",
    "numerical_uncertainty": "Can a further controlled tightening of the genuine native Abaqus MISESERI error target from 1.9% to 1.8% achieve fine-core resolution (h <= l0/2) across the outermost Case 2 distal boundary band x=0.95-1.00 mm on the verified post-breach donor, while keeping mesh cost compliant (<40,000 elements) and preserving FE quality without artificial crack prescription?",
    "expected_numerical_result": "One fresh Case 2 physical adaptive mesh generated at error_target = 1.8% on unchanged verified F1804 donor ODB. Independently audit the five distal spatial bins x=[0.75,0.80], [0.80,0.85], [0.85,0.90], [0.90,0.95] and [0.95,1.00] mm at y=[0.55,0.75] mm. Compare count-based and area-weighted h<=l0 and h<=l0/2 coverage against F1805, F1804 and F1795. Explicitly investigate h_min sizing-bound semantics and record the donor's physical versus recovery-step time mapping. Evaluate FE quality, aspect ratios, signed Jacobians, quad fraction, total elements, far-field coarsening, and canonical gates. Preserve failed SCIENTIFIC_GATE_OUTER_DISTAL if boundary resolution remains below 50% without sequential Method A.2 propagation.",
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
      "physical_mesh_path": "models/pandey_kumar_mode1/256_f1806_case2_distal_1p8pct/PK_F1806_CASE_2_ADAPT_PHYS.inp",
      "physical_mesh_sha256": "35CD501EC545F1885B129152E36E574DE0112404B458AFA86F75EFDE9186DF74",
      "mesh_body_sha256": "35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A",
      "elements_total": 22924,
      "quad_percent": 97.48,
      "min_det_j": 2.870e-7,
      "max_aspect_ratio": 2.500,
      "median_aspect_ratio": 1.210,
      "broad_distal_corridor_mean_h": 0.002551,
      "broad_distal_corridor_min_h": 0.000768,
      "broad_distal_corridor_pct_le_l0_count": 99.98,
      "broad_distal_corridor_pct_le_l0_half_count": 89.41,
      "broad_distal_corridor_pct_le_l0_half_area": 63.42,
      "bin_x_0_90_to_0_95_pct_le_l0_half_count": 41.70,
      "bin_x_0_90_to_0_95_pct_le_l0_half_area": 26.02,
      "bin_x_0_95_to_1_00_pct_le_l0_count": 99.68,
      "bin_x_0_95_to_1_00_pct_le_l0_half_count": 3.21,
      "bin_x_0_95_to_1_00_min_h": 0.002140,
      "combined_x_0_90_to_1_00_pct_le_l0_half_count": 28.02,
      "combined_x_0_90_to_1_00_pct_le_l0_half_area": 13.55,
      "primary_corridor_pct_le_l0_half_count": 35.36,
      "far_to_distal_coarsening_ratio": 4.20,
      "scientific_gate_outer_distal": "FAIL"
    }
  },
  "report_path": "docs/validation/F1806_CASE2_OUTERMOST_DISTAL_SENSITIVITY_REPORT.md",
  "report_sha256": "872618240C0D822C6A8E1838F305C9ACB4A8D23B44018B0C4C731D3CB528F30A",
  "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "framework_sha256": "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
  "cumulative_pbs_submissions": 35,
  "max_new_pbs_submissions": 0,
  "submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "review_instructions": "Review Task F1806 Case 2 Outermost Distal Native-MISESERI Target Sensitivity at 1.8%. Verify: (1) Reused identical verified F1804 hole-arrest recovery donor PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (35E9DC19..., 7,417,896 bytes); (2) Preserved geometry (OffAxisHoleMode1Adapter), sizing bounds h in [0.0015, 0.020] mm, refinement factor 10, indicator MISESERI, shared framework, and frozen UEL strictly invariant; (3) Tested sole numerical control error_target reduced from 1.9% to 1.8%; (4) Controlled execution of native RemeshingRule and adaptiveRemesh() pass under unchanged framework, preserving replay journal abaqus.rpy (5,275 bytes) demonstrating Exit 0; (5) Independent FE quality audit of PK_F1806_CASE_2_ADAPT_PHYS.inp (22,924 elements, 97.48% quads, positive Jacobians min det(J) = 2.870e-7 > 0, max AR 2.500 <= 4.0, median 1.210, 0 violations); (6) Broad distal corridor resolution enhancement: count-based % <= l0/2 reached 89.41% (+3.13 pts vs F1805), area-weighted % <= l0/2 reached 63.42% (+7.07 pts), min h dropped to 0.77 um (<< l0/2 = 3.75 um); (7) Detailed five distal spatial bins (y in [0.55, 0.75] mm): bin x=0.85-0.90 surged to 96.58% <= l0/2 (area 92.56%); bin x=0.90-0.95 surged to 41.70% <= l0/2 (area 26.02%); outermost boundary band x=0.95-1.00 achieved breakthrough with min h dropping to 2.14 um <= 3.75 um and achieving the first non-zero fine-core resolution (3.21% count, 1.05% area); combined outer ligament x=0.90-1.00 reached 28.02% <= l0/2 (area 13.55%, 246 elements); (8) Explicit investigation of h_min sizing bounds and donor time mapping: nominal edge length L_min = 0.975 um vs sqrt(area) = 0.768 um due to transition triangles and boundary-conforming paving quads; authentic donor time mapping (t_phys = 0.3737 s mapped to static recovery model Frame 1 t_local = 1.0 s); (9) Computational efficiency: 22,924 elements (< 40,000 ceiling, -35.7% smaller than F1795 baseline), far-to-distal coarsening ratio 4.20x >= 2.0x; (10) Gate outcomes: standard Gates 01-07 PASS, SCIENTIFIC_GATE_OUTER_DISTAL retained as FAIL (28.02% < 50.0%), physically demonstrating that single-snapshot recovery cannot resolve the traction-free outer boundary without sequential crack propagation (Method A.2); (11) Zero new PBS jobs, cumulative preserved at 35, production UEL frozen, and MASTER_GOAL_STATUS = OPEN."
}
"@

$fullPrompt = "$header`n`n$reportContent`n`n---\n## CANONICAL BRIDGE RULES (MANDATORY INVARIANTS)\n`n$rulesContent"

Write-Host "Prepared Task F1806 Bridge Payload: $($fullPrompt.Length) characters." -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "CheckOnly switch provided. Payload validated without dispatch." -ForegroundColor Green
    return
}

# Dispatch via guarded Invoke-ChatGPTBridge
Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -TaskId $taskId
