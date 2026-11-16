# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1817_evidence_completion_auth_001.ps1
# Dispatches Task F1817 Evidence Completion for F1816 Multi-Step Narrowing (HND-F1817-EVIDENCE-COMPLETION-001)
# to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1817-EVIDENCE-COMPLETION"
$handoffId = "HND-F1817-EVIDENCE-COMPLETION-001"
$predecessorHandoffId = "HND-F1816-MULTISTEP-NARROWING-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1817_EVIDENCE_COMPLETION_REPORT.md"
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
  "title": "Task F1817: Evidence Completion for F1816 Multi-Step Narrowing",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "evidence_completion",
    "numerical_uncertainty": "Can the F1816 variant results be independently verified from committed evidence: the 12 Step 1/2 variant meshes (element counts, gate values, width metrics recomputed from the .inp files), the 6 donor ODBs (SHA-256 by download), and the framework provenance of the Step 1 min/max implementation (either a committed framework modification with a new SHA, or a corrected report stating honestly how Step 1 was executed)?",
    "expected_numerical_result": "All 12 variant meshes committed with whole-file and body SHA-256 matching the summary JSONs; element counts independently recomputed (Step 1: 63,210 / 56,300 / 87,786 / 51,598; Var 2b: 29,314 / 83,913 / 51,549 / 15,466; Var 2a: 37,511 / 82,869 / 57,464 / 15,466); gate values recomputed from the meshes (Var 2b Case 1 91.75% FAIL, Case 3 87.61% FAIL; Var 2a Case 3 86.30% FAIL); 6 donor ODBs committed with SHAs matching the report table; framework contradiction resolved and documented; artifact-table hashes recomputed from committed files; Step 2 summary paths repo-relative; run scripts committed; 0 new PBS jobs consumed (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
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
    "primary_question": "Does the completed evidence base (12 committed variant meshes, 6 committed donor ODBs, reconciled framework provenance in §2.1, normalized repo-relative paths in step2_envelope_summary.json, recomputed artifact hashes, and inspectable run scripts) definitively resolve all supervisory evidence gaps and independently prove that the F1812 baselines (total 160,144 elements) represent the true Pareto optimum?",
    "evaluation_criteria": [
      "1. 12 Variant Meshes Committed: Verify all 12 physical meshes exist at their declared paths in git, with whole-file and body SHA-256 matching the summary JSONs and report table.",
      "2. 6 Donor ODBs Committed: Verify all 6 donor ODBs exist in git under models/pandey_kumar_mode1/263_f1816_multistep_narrowing/step2_envelope/donors/, matching the report table SHAs.",
      "3. Framework Provenance Reconciled: Verify that F1816 report section 2.1 honestly explains that Step 1 evaluated min/max sizing via run_f1816_step1_minmax.py, and upon decisive rejection, the shared framework was intentionally not modified and was preserved at 4276A5DC... with UNIFORM_ERROR baseline.",
      "4. Step 2 Summary Paths Normalized: Verify that step2_envelope_summary.json contains zero Windows absolute drive prefixes (D:\\) and uses strict repo-relative forward-slash paths.",
      "5. Recomputed Artifact Hashes: Verify that step1_minmax_summary.json (7,608 B / 10E7D519...), step2_envelope_summary.json (8,397 B / A6DEFD62...), and receipt (16,034 B / FD1377F9...) match committed disk files.",
      "6. Run Scripts Inspectable: Verify run_f1816_step1_master.py, run_f1816_step1_minmax.py, run_f1816_step2_master.py, and run_f1816_step2_single.py exist and are committed in git.",
      "7. Unit Testing: Verify 52/52 unit tests PASS (test_f1813 23/23, test_f1814 11/11, test_f1816 10/10, test_f1817 8/8).",
      "8. Governance Invariants: 0 new PBS jobs consumed, cumulative 35 preserved, bitwise frozen UEL CE8D5EDC..., shared framework 4276A5DC..., MASTER_GOAL_STATUS = OPEN."
    ]
  },
  "image_manifest": [
    {
      "case_id": "all_cases_synthesis",
      "image_path": "results/figures/fig_f1816_refinement_width_comparison.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1816_refinement_width_comparison.png",
      "artifact_hash": "2B8054C994856E21B4F4826940DE3FFB34F98D6D060A0AA5332D22E7C6D3D6E5"
    },
    {
      "case_id": "all_cases_synthesis_pdf",
      "image_path": "results/figures/fig_f1816_refinement_width_comparison.pdf",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1816_refinement_width_comparison.pdf",
      "artifact_hash": "7D01DAC02126809E297615E36F10219F878A5D4BFA107C2906EF45C6776BF611"
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
# EVIDENTIARY REPORT: Task F1817 Evidence Completion
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
