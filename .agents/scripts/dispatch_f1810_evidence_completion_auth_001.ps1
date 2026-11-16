# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1810_evidence_completion_auth_001.ps1
# Dispatches Task F1810 Method A.2 Evidence Completion, Git Tracking, and Verification Freeze
# (HND-F1810-EVIDENCE-COMPLETION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1810-EVIDENCE-COMPLETION-AND-REVERIFICATION"
$handoffId = "HND-F1810-EVIDENCE-COMPLETION-001"
$predecessorHandoffId = "HND-F1809-METHOD-A2-MULTISTATE-SEQUENTIAL-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1810_EVIDENCE_COMPLETION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = "78b4a32f54245be5a210633b4d2c88f98c603a1d"

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1810: Commit Missing F1809 Evidence and Correct the Report and Manifest",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "evidence_completion",
    "numerical_uncertainty": "The F1809 headline results (Case 2 118,640 elements with 100.00% outer-ligament coverage <= l0/2; Case 3 77,779 elements with 93.84% secondary-corridor coverage <= l0) cannot be independently verified because the physical mesh .inp files and the multi-state donor ODBs are not in the repo, the image manifest hashes do not match the committed images, and the report's F1808 baseline columns contain errors. Can the missing artifacts be committed and the report corrected so the F1809 results become independently verifiable?",
    "expected_numerical_result": "All missing F1809 artifacts committed to GitHub at the claimed paths: the four physical mesh .inp files (Case 1 PK_F1809_CASE_1_ADAPT_PHYS.inp, Case 2 PK_F1809_CASE_2_ADAPT_PHYS.inp, Case 3 PK_F1809_CASE_3_ADAPT_PHYS.inp, Case 5 PK_F1809_CASE_5_ADAPT_PHYS.inp) under models/pandey_kumar_mode1/259_f1809_multistate_recovery/case<N>/, and the two multi-state donor ODBs (PK_HOLE_MULTISTATE_RECOVERY.odb, SEC43_MULTISTATE_RECOVERY.odb) in their case directories, with whole-file and normalized body SHA-256 values recomputed from the committed files and matching the receipt. The image manifest hashes recomputed from the committed image files (the current manifest values are wrong). The F1809 report's F1808 baseline columns corrected to the verified F1808 values: Case 2 Bins 1-4 (100.00% / 0.768 um; 99.03% / 0.784 um; 96.58% / 0.936 um; 41.70% / 1.717 um), Case 3 secondary corridor element count 4,410 and <= l0/2 2.38%, and the Case 3 primary corridor region stated explicitly with its F1808 baseline recomputed under that same region. The Case 2 minimum-element-size warning (21 elements) addressed in the corrected report. No change to the frozen UEL or framework, no new PBS jobs (cumulative 35 preserved), MASTER_GOAL_STATUS = OPEN. After this task is approved, the efficiency calibration (error-target tuning for Cases 2 and 3) proceeds as the next scientific task.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
      "donor_step": "AUTHENTIC_CAUSAL_DONOR_SUITE_STEP",
      "donor_frame_index": 2,
      "indicator_frame_range": "Four canonical benchmark donor states: Case 1 pre-analysis Step-1 Frame 10 (t=1.0s); Case 2 4-state recovery envelope (Frames 10, 190, 280, 337, t=1.0s); Case 3 3-state recovery envelope (States 1, 2, 3, t=1.0s); Case 5 pre-crack Step-2 Frame 171 (t=0.485s)",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0,
      "committed_artifacts": {
        "physical_meshes": [
          {
            "case_id": "case_1",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case1/PK_F1809_CASE_1_ADAPT_PHYS.inp",
            "size_bytes": 1011306,
            "whole_file_sha256": "B18339EA2B4D69932851CAE66483779D258711CB9961D752598D2155A72C57A3",
            "body_sha256": "EAA671FBECC8E1AE759BF3EE5A54AC8BE90F354B087483CD8B513A85DF85F277",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case1/PK_F1809_CASE_1_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_2",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_F1809_CASE_2_ADAPT_PHYS.inp",
            "size_bytes": 9082011,
            "whole_file_sha256": "DFC5F4DA3026BFCF0F17F09A958A30481E3AEB1F57ADBF7311DD387E1BC6DA7A",
            "body_sha256": "C1378B714BAD1E8B47701DE5CEC6FB607B04BCAF13F96B3975962ECFEA8A6527",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_F1809_CASE_2_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_3",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/PK_F1809_CASE_3_ADAPT_PHYS.inp",
            "size_bytes": 5572384,
            "whole_file_sha256": "4B1E5F42BA7899D33473DB6960AA0C1FBEF86742233629B00BA3BC5AE5AAA6DD",
            "body_sha256": "08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/PK_F1809_CASE_3_ADAPT_PHYS.inp"
          },
          {
            "case_id": "case_5",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case5/PK_F1809_CASE_5_ADAPT_PHYS.inp",
            "size_bytes": 1127961,
            "whole_file_sha256": "686A61C21ABBC97B550236A6A6ACA7FFCC2DE6B4E1BC66B7CF3F68DEB8345D5A",
            "body_sha256": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case5/PK_F1809_CASE_5_ADAPT_PHYS.inp"
          }
        ],
        "donor_odbs": [
          {
            "case_id": "case_2",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb",
            "size_bytes": 7499592,
            "sha256": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case2/PK_HOLE_MULTISTATE_RECOVERY.odb"
          },
          {
            "case_id": "case_3",
            "path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb",
            "size_bytes": 10043772,
            "sha256": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
            "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/case3/SEC43_MULTISTATE_RECOVERY.odb"
          }
        ]
      }
    }
  },
  "image_manifest": {
    "commit_sha": "$commitSha",
    "images": [
      {
        "case_id": "case_1",
        "relative_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_1_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_1_mesh_full.png",
        "sha256": "F3776225878985899E60B1E2D2BB4C6714899279D71210B27091C1D63B32BB72"
      },
      {
        "case_id": "case_2",
        "relative_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_2_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_2_mesh_full.png",
        "sha256": "CCC416E9DF25DF6B6E1C5DBDF2A3F446C76B0B87A1F380C96B6B03B589F76CA1"
      },
      {
        "case_id": "case_3",
        "relative_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_3_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_3_mesh_full.png",
        "sha256": "EEDA01A3BCB9812078840B9133BCA98A146DF706673E69839BAE234EBD6AB031"
      },
      {
        "case_id": "case_5",
        "relative_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_5_mesh_full.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/259_f1809_multistate_recovery/figures/case_5_mesh_full.png",
        "sha256": "EA9DD53FF38ED3EB2E98E6966503E7FFB55B08C9170DD141328961E57B69683E"
      },
      {
        "case_id": "composite_4panel",
        "relative_path": "results/figures/fig_f1809_four_benchmark_multistate_synthesis.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1809_four_benchmark_multistate_synthesis.png",
        "sha256": "1B837E8C71B9B0F1E4A2EB5BCFE00222F368A44A0AAABECB5A0E953541344877"
      }
    ]
  },
  "report_path": "docs/validation/F1810_EVIDENCE_COMPLETION_REPORT.md",
  "report_sha256": "D29FFCAF9A8C85E6A196AB898AD95FA5F46B056966340A5213AA42A1E76DF38D",
  "receipt_path": "models/pandey_kumar_mode1/259_f1809_multistate_recovery/PK_F1809_MULTISTATE_SEQUENTIAL_RECEIPT.json",
  "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "framework_sha256": "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
  "cumulative_pbs_submissions": 35,
  "max_new_pbs_submissions": 0,
  "submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "review_instructions": "Review Task F1810 Evidence Completion and Reverification. Verify: (1) All four physical mesh INP files (Cases 1, 2, 3, 5) and both multi-state donor ODBs (Cases 2 and 3) are now fully tracked in the thesis GitHub repository under models/pandey_kumar_mode1/259_f1809_multistate_recovery/ and verified by SHA-256 against the receipt; (2) All published image manifest SHA-256 hashes are verified directly from disk files; (3) Report baseline errata reconciled against verified F1808 values (Case 2 Bins 1-4, Case 3 secondary corridor, explicit Case 3 primary corridor region); (4) Case 2 21 minimum-element-size clamped elements audited, confirming clamp to 0.0015 mm = l0/5 keeps all elements far below l0/2 and outer ligament achieves 100.00% <= l0/2 with max size 2.713 um; (5) Unit tests 25/25 PASS in test_f1810_evidence_completion.py; (6) 0 new PBS jobs consumed, cumulative 35 preserved; MASTER_GOAL_STATUS = OPEN."
}
"@

$fullPrompt = "$header`n`n$reportContent`n`n---\n## CANONICAL BRIDGE RULES (MANDATORY INVARIANTS)\n`n$rulesContent"

Write-Host "Prepared Task F1810 Bridge Payload: $($fullPrompt.Length) characters." -ForegroundColor Cyan

if ($CheckOnly) {
    Write-Host "CheckOnly switch active. Validating canonical bridge policy..." -ForegroundColor Yellow
    Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId -DryRun
} else {
    Write-Host "Publishing Task F1810 Bridge Payload across OpenClaw PAD Bridge..." -ForegroundColor Green
    Invoke-ChatGPTBridge -PromptText $fullPrompt -HandoffId $handoffId
}
