# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1816_multistep_narrowing_auth_001.ps1
# Dispatches Task F1816 Multi-Step Refinement Narrowing (HND-F1816-MULTISTEP-NARROWING-002)
# to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1816-MULTISTEP-REFINEMENT-NARROWING"
$handoffId = "HND-F1816-MULTISTEP-NARROWING-002"
$predecessorHandoffId = "HND-F1814-LABEL-CORRECTION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1816_MULTISTEP_REFINEMENT_NARROWING_REPORT.md"
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
  "title": "Task F1816: Multi-Step Refinement Narrowing Across Four Canonical Benchmarks",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "multistep_refinement_narrowing",
    "numerical_uncertainty": "The adaptive refinement band is wider than the crack path (only ~21-23% of fine elements lie within 2*l0 of the path on the five-hole geometry), and Gate 06 far-field coarsening fails for Cases 2 (1.55x) and 3 (1.65x). Can minimum/maximum sizing (eta_max=1%, eta_min=5%, bias=7) or envelope construction (overlapping native rules vs reduced 2-state envelope) narrow the refinement band while preserving all four scientific resolution gates at their F1812 thresholds?",
    "expected_numerical_result": "Step 1: MINIMUM_MAXIMUM sizing tested on all four benchmarks, producing +61.7% element ballooning (258,894 el), budget and coarsening failures, and band dilution, resulting in REJECTION. Step 2: Reduced 2-state envelope (Var 2b) and per-state overlapping rules (Var 2a) tested; Var 2b fails Case 1 (91.75% < 95%) and Case 3 (87.61% < 90%) gates and doubles Case 2 elements; Var 2a fails Case 3 (86.30% < 90%) and doubles Case 1/2 elements, resulting in REJECTION of both. Step 3: F1812 baselines (total 160,144 elements) adopted as the verified Pareto optimum with 100% scientific gate compliance. F1814 report test-file artifact table entry and test counts corrected. Zero new PBS jobs consumed (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
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
    "primary_question": "Does the systematic three-step investigation (Step 1: min/max sizing, Step 2: reduced 2-state envelope and overlapping rules, Step 3: combine and validate decision) definitively establish that the F1812 baselines represent the true Pareto optimal configuration of the Method A framework, proving that refinement width is governed by physical stress decay rather than numerical artifact?",
    "evaluation_criteria": [
      "1. Step 1 (Min/Max Sizing): Verify that eta_max=1%, eta_min=5%, bias=7 produced +61.7% mesh ballooning (258,894 el), failed element budgets on Cases 1, 3, 5, failed Gate 06 coarsening on all cases, and diluted band concentration.",
      "2. Step 2 (Envelope Construction): Verify that Variant 2b (reduced 2-state envelope) failed Case 1 full ligament gate (91.75% < 95.0%) and Case 3 secondary corridor gate (87.61% < 90.0%), and doubled Case 2 elements to 83,913.",
      "3. Step 2 (Overlapping Rules): Verify that Variant 2a failed Case 3 secondary corridor gate (86.30% < 90.0%) and ballooned elements to 37,511 in Case 1 and 82,869 in Case 2.",
      "4. Case 5 Regression Control: Verify Case 5 preserved exact parity (15,466 elements, 99.14% gate PASS, 2.12x coarsening PASS).",
      "5. Step 3 Predeclared Adoption Decision: Verify that because neither candidate narrowed the band while maintaining all four scientific gates, the F1812 baselines (total 160,144 elements) stand as the verified Pareto optimum.",
      "6. Documentation corrections: Verify that F1814 report artifact table has been corrected (test file: 5,783 bytes, SHA-256 6766E8F2...) and test suite count (11 standalone + 23 F1813 = 34) clarified.",
      "7. Governance invariants: 0 new PBS jobs consumed, cumulative 35 preserved, bitwise frozen UEL CE8D5EDC..., MASTER_GOAL_STATUS = OPEN."
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
# EVIDENTIARY REPORT: Task F1816 Multi-Step Refinement Narrowing
$reportContent

---
# CANONICAL BRIDGE RULES
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "Validation successful for Task $taskId ($handoffId)."
    Write-Host "Handoff payload preview (first 500 chars):"
    Write-Host $header.Substring(0, [Math]::Min(500, $header.Length))
    return
}

Publish-ChatGPTBridgeHandoff `
    -HandoffId $handoffId `
    -Content $header `
    -Contract @{
        goal_id = "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1"
        method = "METHOD_A"
        operation = "multistep_refinement_narrowing"
        numerical_uncertainty = "The adaptive refinement band is wider than the crack path. Can min/max sizing or envelope construction narrow the band while preserving all four scientific resolution gates?"
        expected_numerical_result = "Step 1: Min/Max sizing produces +61.7% ballooning (258,894 el) and band dilution, resulting in REJECTION. Step 2: Reduced 2-state envelope and overlapping rules fail resolution gates and double elements, resulting in REJECTION. Step 3: F1812 baselines (160,144 el) adopted as verified Pareto optimum. 0 new PBS jobs consumed, cumulative 35 preserved; MASTER_GOAL_STATUS = OPEN."
        indicator_type = "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"
        indicator_role = "PRIMARY_NATIVE_MISESERI"
        qualifies_native_miseseri = $true
        causal_evidence_status = "VERIFIED"
        causal_evidence = @{
            donor_path = "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb"
            donor_sha256 = "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117"
            donor_step = "AUTHENTIC_CAUSAL_DONOR_SUITE_STEP"
            donor_frame_index = 5
            indicator_frame_range = "Four canonical benchmark donor states carried from F1812"
            held_out_later_solution = "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions"
            uses_future_frames = $false
            remesh_time = 1.0
            maximum_indicator_time = 1.0
        }
    }
