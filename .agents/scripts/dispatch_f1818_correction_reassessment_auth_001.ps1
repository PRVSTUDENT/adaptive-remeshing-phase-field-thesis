# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1818_correction_reassessment_auth_001.ps1
# Dispatches Task F1818 Correction and Reassessment of F1816 Narrowing Conclusions (HND-F1818-CORRECTION-REASSESSMENT-001)
# to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1818-CORRECTION-AND-REASSESSMENT"
$handoffId = "HND-F1818-CORRECTION-REASSESSMENT-001"
$predecessorHandoffId = "HND-F1817-EVIDENCE-COMPLETION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1818_CORRECTION_AND_REASSESSMENT_REPORT.md"
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
  "title": "Task F1818: Correction and Reassessment of F1816 Narrowing Conclusions",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "correction_reassessment",
    "numerical_uncertainty": "Can the F1816 narrowing conclusions be corrected and restated honestly from the committed evidence: Step 1 tested UNIFORM_ERROR with errorTarget=3.0 (not MINIMUM_MAXIMUM, which the framework hardcodes away), and the Variant 2b/2a Case 3 secondary gates are 94.88% and 92.27% (both PASS, not 87.61% and 86.30% FAIL) when recomputed from the committed meshes? Does F1812 still stand as the best among the tested configurations on the corrected evidence?",
    "expected_numerical_result": "F1816 report corrected to state Step 1 used UNIFORM_ERROR errorTarget=3.0 (MINIMUM_MAXIMUM never exercised; conclusion withdrawn as a statement about that sizing method); Case 3 secondary gates corrected to Var 2b 94.88% PASS (n=12,964) and Var 2a 92.27% PASS (n=11,440) in the Step 2 summary JSON, the F1816 report and the width comparison figure panel (c) (recomputed hashes); run script hashes in the F1817 report table corrected to the committed values (0F33EFEB.../3,557 B, 3B9253DF.../15,552 B, 931E683C.../15,835 B, 95D6207C.../6,032 B); Pareto-optimum conclusion restated with the corrected evidence (F1812 best among tested configurations on element count, Case 1 gate and band concentration; MINIMUM_MAXIMUM explicitly untested); 0 new PBS jobs consumed (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
      "donor_step": "AUTHENTIC_CAUSAL_DONOR_SUITE_STEP",
      "donor_frame_index": 5,
      "indicator_frame_range": "Four canonical benchmark donor states carried from F1812: Case 1 5-state recovery envelope (Frames 400, 420, 450, 460, 470, t=1.0s); Case 2 4-state recovery envelope (Frames 10, 190, 280, 337, t=1.0s); Case 3 3-state recovery envelope (States 1, 2, 3, t=1.0s); Case 5 single-state pre-crack Step-2 Frame 171 (t=0.485s)",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Do the corrected and verified records (F1816 report honest provenance, Step 2 summary Case 3 secondary gates 94.88% and 92.27% PASS, regenerated width comparison figures, corrected run script table hashes, and restated Pareto conclusion) definitively resolve all supervisory objections and establish that F1812 represents the Pareto optimum among tested configurations while MINIMUM_MAXIMUM remains an open question?",
    "evaluation_criteria": [
      "1. Step 1 Provenance Corrected: F1816 report honestly states Step 1 ran UNIFORM_ERROR with errorTarget=3.0% (Case 1 config) because framework hardcodes UNIFORM_ERROR; prior conclusion withdrawn as a statement about MINIMUM_MAXIMUM sizing; MINIMUM_MAXIMUM noted as untested.",
      "2. Case 3 Secondary Gate Corrected: Step 2 summary JSON and F1816 report record Var 2b 94.88% PASS and Var 2a 92.27% PASS; root cause (bounding box y in [45, 75] vs [45, 65]) documented; rejection of Var 2b (Case 1 gate failure 91.75%, Case 2 ballooning to 83,913) and Var 2a (Case 1/2 ballooning, band dilution) restated.",
      "3. Width Comparison Figure Regenerated: Panel (c) reflects Case 3 Step 2b (94.9%) and Step 2a (92.3%) PASS; Panel (d) summary text updated; label overlap in panels (a) and (c) resolved; recomputed hashes match committed files (PNG 302906A7..., PDF FB62BF7D...).",
      "4. Run Script Table Hashes Corrected: F1817 report table matches committed file values (0F33EFEB.../3,557 B, 3B9253DF.../15,552 B, 931E683C.../15,835 B, 95D6207C.../6,032 B).",
      "5. Pareto Optimum Restated: F1812 stands as best among tested configurations; MINIMUM_MAXIMUM explicitly recorded as unexercised and noted as a forward roadmap item.",
      "6. Unit Testing: 60/60 unit tests PASS (test_f1813 23/23, test_f1814 11/11, test_f1816 10/10, test_f1817 8/8, test_f1818 8/8).",
      "7. Governance Invariants: 0 new PBS jobs consumed, cumulative 35 preserved, bitwise frozen UEL CE8D5EDC..., shared framework 4276A5DC..., MASTER_GOAL_STATUS = OPEN."
    ]
  },
  "image_manifest": [
    {
      "case_id": "all_cases_synthesis",
      "image_path": "results/figures/fig_f1816_refinement_width_comparison.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1816_refinement_width_comparison.png",
      "artifact_hash": "302906A7468BFD68514F61084A52F712CC72F1B681A93F0242CEF7A9BBD31802"
    },
    {
      "case_id": "all_cases_synthesis_pdf",
      "image_path": "results/figures/fig_f1816_refinement_width_comparison.pdf",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1816_refinement_width_comparison.pdf",
      "artifact_hash": "FB62BF7DD39DE330664B1913C7C0154291F238DEB5C893F1C40834E1F8007874"
    }
  ],
  "checkpoint_commit": "$commitSha",
  "governance": {
    "cumulative_pbs_submissions": 35,
    "max_new_pbs": 0,
    "submissions_consumed": 0,
    "production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "shared_framework_sha256": "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B",
    "master_goal_status": "OPEN",
    "total_adapted_mesh_elements": 160144
  }
}

---
# EVIDENTIARY REPORT: Task F1818 Correction and Reassessment
$reportContent

---
# CANONICAL BRIDGE RULES
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "Validation successful for Task $taskId ($handoffId)."
    Write-Host "Handoff payload preview (first 500 chars):"
    Write-Host $header.Substring(0, [Math]::Min(500, $header.Length))
    Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId -DryRun
    return
}

Write-Host "Publishing Task $taskId Bridge Payload across OpenClaw PAD Bridge..." -ForegroundColor Green
Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId
