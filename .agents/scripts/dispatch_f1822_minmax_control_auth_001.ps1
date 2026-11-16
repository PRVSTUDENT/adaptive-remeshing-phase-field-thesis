# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1822_minmax_control_auth_001.ps1
# Dispatches Task F1822 MINIMUM_MAXIMUM Control Verification and F1821 Record Correction
# (HND-F1822-MINMAX-CONTROL-VERIFICATION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1822-MINIMUM-MAXIMUM-CONTROL-VERIFICATION"
$handoffId = "HND-F1822-MINMAX-CONTROL-VERIFICATION-001"
$predecessorHandoffId = "HND-F1821-GENUINE-MINMAX-EXECUTION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1822_MINMAX_CONTROL_VERIFICATION_REPORT.md"
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
  "title": "Task F1822: MINIMUM_MAXIMUM Control Verification and F1821 Record Correction",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Can empirical commitment of the UNIFORM_ERROR 3.0% control mesh (62,611 elements, body SHA D36603D8...) with .rpy journal, config, and receipt definitively prove that body SHA B15F948C... (63,210 elements) is the distinct deterministic signature of Abaqus CAE under MINIMUM_MAXIMUM sizing, resolving the provenance question and confirming the rejection of MINIMUM_MAXIMUM?",
    "expected_numerical_result": "Empirical execution of UNIFORM_ERROR 3.0% in models/pandey_kumar_mode1/266_f1822_uniform_error_control/ generates 62,611 elements (Body SHA D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768) with authentic .rpy journal (case_1_ue3_control_abaqus.rpy), proving that B15F948C... (63,210 elements) is distinct (+599 elements, body SHAs match = False) and is the authentic output of MINIMUM_MAXIMUM; F1821 report artifact table corrected (14,838 bytes / 1A30A82E...) and correlation_id added to F1821 receipt; MINIMUM_MAXIMUM rejected; 0 new PBS jobs; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
      "donor_step": "RECOVERY_STEP",
      "donor_frame_index": 2,
      "indicator_frame_range": "Case 1 multi-state recovery donor envelope across authentic propagation states",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Does Task F1822 satisfy all successor requirements of HND-F1821-GENUINE-MINMAX-EXECUTION-001 [REJECT] by: (1) committing the UNIFORM_ERROR 3.0% control mesh for Case 1 (62,611 elements, body SHA D36603D8...) with .rpy journal, exact config, donor ODB SHA, and framework SHA in models/pandey_kumar_mode1/266_f1822_uniform_error_control/; (2) providing full parameter specification for reproduction; (3) correcting the F1821 report artifact table entry for the F1820 report (14,838 bytes / 1A30A82E...); (4) adding correlation_id to PK_F1821_GENUINE_MINMAX_RECEIPT.json; and (5) preserving the framework enhancement (0578156E...) and committed .rpy journals?",
    "evaluation_criteria": [
      "1. UNIFORM_ERROR Control Mesh: models/pandey_kumar_mode1/266_f1822_uniform_error_control/PK_F1822_CASE1_UE3_CONTROL_PHYS.inp committed (4,480,026 bytes, whole SHA 75AAFBB0..., body SHA D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768) with 62,611 elements (60,966 quads = 97.37%, 1,645 tris), min det(J) = +1.20e-7, max AR = 2.71.",
      "2. Authentic Replay Journal: case_1_ue3_control_abaqus.rpy committed in 266_f1822_uniform_error_control/ (2,432 bytes, SHA 64EBC6C1...) proving direct execution of sizingMethod=UNIFORM_ERROR, errorTarget=3.0% producing 62,611 elements.",
      "3. Empirical Ground Truth: Direct comparison proves UNIFORM_ERROR 3.0% (62,611 elements, D36603D8...) and MINIMUM_MAXIMUM bias=7 (63,210 elements, B15F948C...) are distinct (+599 elements, body SHAs match = False), conclusively proving that B15F948C... is the authentic deterministic output of MINIMUM_MAXIMUM.",
      "4. F1821 Evidentiary Corrections: docs/validation/F1821_GENUINE_MINMAX_EXECUTION_REPORT.md Table 5 updated with actual F1820 report size/SHA (14,838 bytes / 1A30A82EECAFED41FCB4226DE5473C26FB86DC1EF7BACDC6F424E65CE3C6FF56); PK_F1821_GENUINE_MINMAX_RECEIPT.json updated with correlation_id HND-F1821-GENUINE-MINMAX-EXECUTION-001.",
      "5. Full Reproduction Specification: Complete parameters, geometry, material, donor ODB, and framework hashes tabulated in F1822 report Section 2.",
      "6. Unit Testing: 7/7 unit tests in test_f1822_control_verification.py PASS, verifying all mesh properties, journal content, config, receipts, and invariants.",
      "7. Governance Invariants: Framework enhancement (0578156E...), production UEL (CE8D5EDC...), 0 new PBS jobs (cumulative 35 preserved), and MASTER_GOAL_STATUS = OPEN strictly maintained."
    ]
  },
  "image_manifest": [
    {
      "case_id": "all_cases_genuine_minmax_comparison_png",
      "image_path": "results/figures/fig_f1821_genuine_minmax_comparison.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1821_genuine_minmax_comparison.png",
      "artifact_hash": "ECEC1FA43FEE8153FEE4815777509463340B0AF344FB19157026D43F751CBF81"
    },
    {
      "case_id": "all_cases_genuine_minmax_comparison_pdf",
      "image_path": "results/figures/fig_f1821_genuine_minmax_comparison.pdf",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1821_genuine_minmax_comparison.pdf",
      "artifact_hash": "488D99476241CB50E72FD610240C1A76A83B9E20304DE92EA09A587F09735482"
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
    "control_mesh_elements": 62611,
    "control_mesh_body_sha256": "D36603D89FF9D953395A176D8C327F097FE69E92469FA73F6CC3193426B6E768"
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
