# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1814_label_correction_auth_001.ps1
# Dispatches Task F1814 Synthesis Labeling Corrections and Four-Benchmark Framework Finalization
# (HND-F1814-LABEL-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1814-SYNTHESIS-LABEL-CORRECTION"
$handoffId = "HND-F1814-LABEL-CORRECTION-001"
$predecessorHandoffId = "HND-F1813-UNIFIED-SYNTHESIS-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1814_SYNTHESIS_LABEL_CORRECTION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = "0bab7997ee27045e1ba4add2991514990e92fede"

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1814: Synthesis Labeling Corrections and Four-Benchmark Framework Finalization",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "synthesis_label_correction",
    "numerical_uncertainty": "Can the two F1813 labeling defects be corrected without changing any scientific result: the progression summary JSON gate_status for Case 1 F1808/F1809/F1811 (reconciled to INCOMPLETE matching the report progression table and the full-ligament criterion), and the progression chart Case 1 coverage series (standardized to the full-ligament series 79.8% -> 79.8% -> 79.8% -> 97.2% with the right axis relabeled)?",
    "expected_numerical_result": "Reconciled campaign_progression_summary.json with Case 1 F1808/F1809 gate_status INCOMPLETE (full ligament 79.8% <= l0/2) and F1811 INCOMPLETE with tip-pass/distal-zero explicitly stated; updated progression chart PNG and PDF with consistent full-ligament series and relabeled axis; all four physical meshes, framework (4276A5DC...), and UEL (CE8D5EDC...) bitwise invariant; 34/34 unit tests PASS; 0 new PBS jobs consumed (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
      "donor_step": "AUTHENTIC_CAUSAL_DONOR_SUITE_STEP",
      "donor_frame_index": 5,
      "indicator_frame_range": "Four canonical benchmark donor states carried from F1812/F1813: Case 1 5-state recovery envelope (Frames 400, 420, 450, 460, 470, t=1.0s); Case 2 4-state recovery envelope (Frames 10, 190, 280, 337, t=1.0s); Case 3 3-state recovery envelope (States 1, 2, 3, t=1.0s); Case 5 pre-crack Step-2 Frame 171 (t=0.485s)",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0,
      "committed_artifacts": {
        "physical_meshes": [
          {
            "case_id": "case_1",
            "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_F1812_CASE_1_ADAPT_PHYS.inp",
            "size_bytes": 1825210,
            "whole_file_sha256": "A138FF1DDC54E7F113784980D5B9D4E3365766C95ED5AD0A8F3AA926D8C74CBE",
            "body_sha256": "50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_F1812_CASE_1_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_2",
            "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case2/PK_F1812_CASE_2_ADAPT_PHYS.inp",
            "size_bytes": 2975652,
            "whole_file_sha256": "FF6F61C307DA2202B1F798E50E42778F30B7872E680EE9232AB79DB801C47E37",
            "body_sha256": "5C7DD6B52DBBE716C823462E2EFBA37EAF3DF884862F2CAA4533F80FB7FFBFE1",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case2/PK_F1812_CASE_2_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_3",
            "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case3/PK_F1812_CASE_3_ADAPT_PHYS.inp",
            "size_bytes": 5572384,
            "whole_file_sha256": "7DB1BB4B7911D604C78DA450B93EF5E47C306FB0DD2E1FC9CF9C15876D5CF095",
            "body_sha256": "08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case3/PK_F1812_CASE_3_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_5",
            "path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case5/PK_F1812_CASE_5_ADAPT_PHYS.inp",
            "size_bytes": 1127961,
            "whole_file_sha256": "182B185B13B5EBBB2A19B8200D3CCA1344F64104EB10B2A6CFE20883ACEA3842",
            "body_sha256": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case5/PK_F1812_CASE_5_ADAPT_PHYS.inp"
          }
        ]
      }
    }
  },
  "image_manifest": {
    "commit_sha": "$commitSha",
    "images": [
      {
        "case_id": "case_1_mesh_full",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_mesh_full.png",
        "sha256": "D336E7E1BAD72F8F6DC7923A7EE76029D8E00F696B20D1A048EECEB05C832928"
      },
      {
        "case_id": "case_1_h_over_l0",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_sizing_h_l0.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_sizing_h_l0.png",
        "sha256": "0A114206FF4B4EFCB46005A0EB875CB114FFE23A76D3075B773E902A957C7334"
      },
      {
        "case_id": "case_1_mesh_closeup",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_mesh_closeup.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_1_mesh_closeup.png",
        "sha256": "F23D2DCBB4228D57AFD4D35E643ECDA50CB27CA606E9F49B5ED58CCFBDF4FF9D"
      },
      {
        "case_id": "case_2_mesh_full",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_mesh_full.png",
        "sha256": "2C5CB4AA0A25322CEEF2FF4A26FA01C71D12AB76D1E0A225A42F5EE56C7243A3"
      },
      {
        "case_id": "case_2_h_over_l0",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_sizing_h_l0.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_sizing_h_l0.png",
        "sha256": "87FE4C20A0449D2B95FC2B1A5EC03D2A5A3BE6DA51DC04A4BA0AF0CD014D0491"
      },
      {
        "case_id": "case_2_mesh_closeup",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_mesh_closeup.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_2_mesh_closeup.png",
        "sha256": "FA6560B86BDC5507B27E6BC7BF0B6821848CF3608AC5C4F4A7FD8A829C5A55EC"
      },
      {
        "case_id": "case_3_mesh_full",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_mesh_full.png",
        "sha256": "D38B5082B9E1F2DDDC4ED6C0F971DFD3D41FC8ADEEE0DEB489883F05B338F66D"
      },
      {
        "case_id": "case_3_h_over_l0",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_sizing_h_l0.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_sizing_h_l0.png",
        "sha256": "BAE4A3619B98BB65ED1C76AE2A3891474CEB4BC5CAFF964CE450E7C6A60B484B"
      },
      {
        "case_id": "case_3_mesh_closeup",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_mesh_closeup.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_3_mesh_closeup.png",
        "sha256": "FF613287E8311FDE9DA7FCD0ED9093F5C85B985DC8A4AC313C0D362FFC0AEB90"
      },
      {
        "case_id": "case_5_mesh_full",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_mesh_full.png",
        "sha256": "8DF0F864A554AFD00ABC0D825574FD645E87D7DB862F1F4FEAB4D81D95102F82"
      },
      {
        "case_id": "case_5_h_over_l0",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_sizing_h_l0.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_sizing_h_l0.png",
        "sha256": "BF2D0C318B3266DE1D852A73E69393A26D8B58D7AF1C30E59C8AFA46E490EA8B"
      },
      {
        "case_id": "case_5_mesh_closeup",
        "relative_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_mesh_closeup.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/261_f1812_crack_path_refinement/figures/case_5_mesh_closeup.png",
        "sha256": "EC0C8F3C25AF2F1E7D18F6501827BFD340EDF57D137403675D74D98E0C48CC15"
      },
      {
        "case_id": "campaign_progression_chart",
        "relative_path": "results/figures/fig_f1813_four_benchmark_progression.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1813_four_benchmark_progression.png",
        "sha256": "D416BB525E0F477C1C320026A2A87D64C8F87FF1B1DB245713C261B78AC3545B"
      },
      {
        "case_id": "unified_4panel_synthesis",
        "relative_path": "results/figures/fig_f1813_four_benchmark_unified_synthesis.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1813_four_benchmark_unified_synthesis.png",
        "sha256": "075B5384F55D58B26BF757506C5C9DB87BB54A41C787B4BB7A0FDC82F364715C"
      }
    ]
  },
  "report_path": "docs/validation/F1814_SYNTHESIS_LABEL_CORRECTION_REPORT.md",
  "report_sha256": "6765B335272E0CCFBF24AD57A9DE2BE465FE4B5262506BC5996EF0E8DAA41511",
  "receipt_path": "models/pandey_kumar_mode1/262_f1813_unified_synthesis/PK_F1813_UNIFIED_SYNTHESIS_RECEIPT.json",
  "receipt_sha256": "F4E075DA0FEEC4AC8DAB8835C38B74DFC92890D041849DAB82878BC352AC45AE",
  "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "framework_sha256": "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B",
  "cumulative_pbs_submissions": 35,
  "max_new_pbs_submissions": 0,
  "submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "review_instructions": "Review Task F1814 Synthesis Labeling Corrections and Four-Benchmark Framework Finalization. Verify: (1) Reconciled Case 1 gate_status in campaign_progression_summary.json (F1808/F1809 labeled INCOMPLETE matching full-ligament 79.8% <= l0/2, F1811 labeled INCOMPLETE with explicit tip-pass/distal-zero documentation, F1812 remains PASS); (2) Case 1 progression chart standardized to single consistent physical quantity (Full Ligament Coverage 79.8% -> 79.8% -> 79.8% -> 97.2%) with right axis relabeled to Full Ligament Coverage (%) and 95.0% gate threshold line added; (3) All four physical meshes, shared framework (4276A5DC...), and UEL (CE8D5EDC...) bitwise invariant (zero regeneration, zero code change); (4) All four scientific resolution gates PASS at F1812 baselines; (5) Note that Method A framework finalization is complete and Job-2 coupled fracture validation requires explicit user authorization to lift max_new_pbs = 0; (6) Unit tests 34/34 PASS; (7) 0 new PBS jobs consumed, cumulative 35 preserved; MASTER_GOAL_STATUS = OPEN."
}
"@

$fullPrompt = "$header`n`n$reportContent`n`n---\n## CANONICAL BRIDGE RULES (MANDATORY INVARIANTS)\n`n$rulesContent"

Write-Host "Prepared Task F1814 Bridge Payload: $($fullPrompt.Length) characters." -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "CheckOnly switch active. Validating canonical bridge policy..." -ForegroundColor Yellow
    Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -DryRun
} else {
    Write-Host "Publishing Task F1814 Bridge Payload across OpenClaw PAD Bridge..." -ForegroundColor Green
    Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId
}
