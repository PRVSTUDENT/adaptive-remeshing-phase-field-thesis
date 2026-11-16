# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1827_campaign_synthesis_auth_001.ps1
# Dispatches Task F1827 Campaign Synthesis (F1812-F1826) and Harmonized Framework State
# (HND-F1827-CAMPAIGN-SYNTHESIS-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1827-CAMPAIGN-SYNTHESIS-F1812-F1826"
$handoffId = "HND-F1827-CAMPAIGN-SYNTHESIS-001"
$predecessorHandoffId = "HND-F1826-ADAPTER-HARMONIZATION-GATE06-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1827_CAMPAIGN_SYNTHESIS_F1812_F1826.md"
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
  "title": "Task F1827: Synthesis Consolidating the F1812-F1826 Campaign and the Harmonized Framework State",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "What is the consolidated, honestly disclosed state of the Method A adaptive-remeshing campaign from F1812 through F1826, including the accepted baselines, the harmonized framework revision, the Gate 06 status under the original definition, the supplementary diagnostics, and the open items?",
    "expected_numerical_result": "A single synthesis document (docs/validation/F1827_CAMPAIGN_SYNTHESIS_F1812_F1826.md) consolidating: the F1812 baselines (160,144 elements total) with all scientific gates PASS and Gate 06 plainly disclosed (Case 1 2.3867x PASS, Case 2 1.9349x FAIL, Case 3 1.4462x FAIL, Case 5 2.1174x PASS); the harmonized framework (80B41AA2...) as the current revision; the F1823-F1826 findings; the size-thresholded and corner ratios as supplementary diagnostics (not Gate 06); and the open items plainly stated (Gate 06 FAIL for Cases 2 and 3; no coupled fracture validation on the adapted meshes; the F1823 Case 3 baseline discrepancy uncorrected); 0 new PBS jobs (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
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
    "primary_question": "Does Task F1827 satisfactorily consolidate the entire Method A / A.2 adaptive remeshing campaign from F1812 through F1826 into a single transparent synthesis document, establishing the accepted baselines, documenting the harmonized framework revision, plainly disclosing original Gate 06 evaluations alongside supplementary diagnostics, and explicitly declaring all open items and limitations while maintaining all governance invariants?",
    "evaluation_criteria": [
      "1. Synthesis Document Completeness: Verification that docs/validation/F1827_CAMPAIGN_SYNTHESIS_F1812_F1826.md consolidates the accepted F1812 baselines (160,144 elements total across Cases 1, 2, 3, 5), the harmonized framework architecture (80B41AA2...), and all campaign milestones from F1816 through F1826.",
      "2. Plain Gate 06 Disclosure: Verification that Gate 06 evaluated under the un-modified geometric definition is plainly disclosed: Case 1: 2.3867x (PASS), Case 2: 1.9349x (FAIL), Case 3: 1.4462x (FAIL), and Case 5: 2.1174x (PASS), with physical explanations for Cases 2 and 3.",
      "3. Current Harmonized Framework Revision: Documentation of reusable_2d_adaptive_framework.py (SHA-256: 80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C, 2,217 lines) incorporating classify_region() corridors for Cases 2 and 3.",
      "4. Consolidated Findings: Synthesis of F1816-F1819 (narrowing & MINIMUM_MAXIMUM rejection), F1820-F1822 (genuine min/max execution with .rpy journals), F1823 (kwargs comparison, Case 3 width bug fix, donor ablation), F1824 (Job-2 preflight), F1825 (adapter inconsistency diagnosis), and F1826 (adapter harmonization & verification).",
      "5. Supplementary Diagnostics: Documentation of supplementary size-thresholded coarsening (2.74x to 4.23x, all 4 PASS) and corner coarsening (17x to 28x mean, 25x to 44x max) without redefining Gate 06.",
      "6. Plain Statement of Open Items: Explicit declaration of Gate 06 FAIL on Cases 2 & 3, unexecuted Job-2 coupled fracture validation, historical F1823 report Case 3 baseline discrepancy, and minor sampling box differences in scientific gates.",
      "7. Unit Testing: 6/6 unit tests in tests/unit/test_f1827_campaign_synthesis.py PASS in 0.40s.",
      "8. Governance Invariants: Framework 80B41AA2..., production UEL CE8D5EDC..., 0 new PBS jobs (cumulative 35 preserved), and MASTER_GOAL_STATUS = OPEN strictly maintained."
    ]
  },
  "image_manifest": [
    {
      "case_id": "fig_f1826_four_benchmark_harmonization_png",
      "image_path": "results/figures/fig_f1826_four_benchmark_harmonization.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1826_four_benchmark_harmonization.png",
      "artifact_hash": "7C2B9ED69ABEB65CAB118592A976455EC04C07666E4822EC35A63FAA49651229"
    },
    {
      "case_id": "fig_f1826_four_benchmark_harmonization_pdf",
      "image_path": "results/figures/fig_f1826_four_benchmark_harmonization.pdf",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1826_four_benchmark_harmonization.pdf",
      "artifact_hash": "A463C25FF8A1A9F7AAB4986E9C3C96E9249D91533DF6D881FDB6C9568D28B952"
    },
    {
      "case_id": "fig_f1826_case_1_mesh_png",
      "image_path": "models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_1_mesh.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_1_mesh.png",
      "artifact_hash": "391A9CFE0A7AA5CF39D91A53CC149FE0628A819B7B33A16CDBF2A24B28B4B244"
    },
    {
      "case_id": "fig_f1826_case_2_mesh_png",
      "image_path": "models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_2_mesh.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_2_mesh.png",
      "artifact_hash": "67E26A6441238F9C58D9BDDE6409D9A35EE5B1A7669413C29406153C64D04635"
    },
    {
      "case_id": "fig_f1826_case_3_mesh_png",
      "image_path": "models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_3_mesh.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_3_mesh.png",
      "artifact_hash": "966499CFB15AB59EA758070012388E604D5C5AD3EFE93F388D1B2DC7EF3CACB9"
    },
    {
      "case_id": "fig_f1826_case_5_mesh_png",
      "image_path": "models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_5_mesh.png",
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_5_mesh.png",
      "artifact_hash": "F0A70096A9787134718ADCAEBA6E1C1D980C19ED74EA0BDC98A7BC64DB5C4AF2"
    }
  ],
  "checkpoint_commit": "$commitSha",
  "governance": {
    "cumulative_pbs_submissions": 35,
    "max_new_pbs": 0,
    "submissions_consumed": 0,
    "production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "shared_framework_sha256": "80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C",
    "master_goal_status": "OPEN",
    "active_pbs_job_id": null,
    "mesh_budget_total": 160144
  }
}
"@

$fullPayload = @"
$header

# Evidentiary Report: Task F1827 Campaign Synthesis (F1812–F1826) and Harmonized Framework State
$reportContent

---

# Canonical Bridge Rules
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "=== F1827 DISPATCH CHECK ONLY ==="
    Write-Host "Handoff ID: $handoffId"
    Write-Host "Commit SHA: $commitSha"
    Write-Host "Payload Length: $($fullPayload.Length) chars"
    return
}

Write-Host "=== DISPATCHING F1827 CAMPAIGN SYNTHESIS REVIEW ACROSS OPENCLAW PAD BRIDGE ==="
Write-Host "Handoff ID: $handoffId"
Write-Host "Commit SHA: $commitSha"

Invoke-ChatGPTBridge -PromptText $fullPayload -HandoffId $handoffId

Write-Host "=== F1827 DISPATCH SUBMITTED TO BRIDGE SUCCESSFULLY ==="
