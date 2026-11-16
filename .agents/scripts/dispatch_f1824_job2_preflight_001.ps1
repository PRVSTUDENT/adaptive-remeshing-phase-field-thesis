# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1824_job2_preflight_001.ps1
# Dispatches Task F1824 Job-2 Coupled Phase-Field Fracture Offline Preflight & Deck Audit
# (HND-F1824-JOB2-COUPLED-VALIDATION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1824-JOB2-COUPLED-FRACTURE-VALIDATION"
$handoffId = "HND-F1824-JOB2-COUPLED-VALIDATION-001"
$predecessorHandoffId = "HND-F1823-FRAMEWORK-COARSENING-DONORS-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1824_JOB2_COUPLED_FRACTURE_PREFLIGHT_REPORT.md"
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
  "title": "Task F1824: Job-2 Coupled Phase-Field Fracture Offline Preflight & Deck Audit (Holding in WAIT State)",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "job2_coupled_fracture_validation",
    "numerical_uncertainty": "Are all four production input decks, layered finite-element discretizations, kinematic tie equations, and cluster execution scripts fully qualified and ready for Job-2 coupled phase-field fracture simulations on the F1812 Pareto-optimal adapted meshes? Can all preflight requirements be satisfied strictly offline with 0 new PBS jobs consumed while holding in WAIT state for explicit user authorization to lift max_new_pbs=0?",
    "expected_numerical_result": "Authoritative 3-layer UEL + companion UMAT production input decks constructed and verified across all four benchmarks on F1812 meshes: Case 1 (25,461 phys el / 76,383 layered el), Case 2 (41,438 phys el / 124,314 layered el), Case 3 (77,779 phys el / 233,337 layered el), Case 5 (15,466 phys el / 46,398 layered el); total 160,144 physical elements / 480,432 layered elements; line-wrapping audit PASS (0 lines > 16 entries); PBS submission scripts generated with dual-channel notification traps; 5/5 unit tests PASS in test_f1824_job2_preflight.py; 0 new PBS jobs consumed (cumulative 35 preserved); bitwise frozen UEL CE8D5EDC... and framework 0578156E... maintained; holding in WAIT state awaiting explicit user confirmation of PBS budget; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/261_f1812_crack_path_refinement/case1/PK_CASE1_MULTISTATE_RECOVERY.odb",
      "donor_sha256": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
      "donor_step": "RECOVERY_STEP",
      "donor_frame_index": 2,
      "indicator_frame_range": "Four canonical benchmark donor states carried from F1812: Case 1 5-state recovery envelope; Case 2 4-state recovery envelope; Case 3 3-state recovery envelope; Case 5 single-state pre-crack",
      "held_out_later_solution": "All post-remesh coupled fracture propagation and failure fields held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Does Task F1824 satisfy all preflight criteria for Job-2 coupled phase-field fracture validation while strictly respecting the conditional execution boundary: (1) all four production input decks generated and verified on F1812 Pareto meshes via ProductionDeckBuilder; (2) total 160,144 physical elements and 480,432 layered elements verified; (3) line-wrapping audit PASS on all *NSET cards (0 lines > 16 entries); (4) PBS cluster submission scripts staged with dual-channel notification integration and atomic locks; (5) exactly 0 new PBS jobs consumed (cumulative 35 preserved); (6) project cleanly holding in WAIT state awaiting user explicit confirmation to lift max_new_pbs=0 and provide PBS job budget?",
    "evaluation_criteria": [
      "1. Production Deck Architecture: models/pandey_kumar_mode1/268_f1824_job2_preflight/ contains authoritative 3-layer UEL + companion UMAT production input decks for Cases 1, 2, 3, 5 generated via ProductionDeckBuilder matching frozen f42_mixed_uel.for.",
      "2. Discretization Parity: Case 1 (25,461 el / 76,383 layered), Case 2 (41,438 el / 124,314 layered), Case 3 (77,779 el / 233,337 layered), Case 5 (15,466 el / 46,398 layered) exactly match F1812 Pareto-optimal baseline (total 160,144 physical / 480,432 layered elements).",
      "3. Buffer Overflow Protection: 100% of *NSET cards across all 22.5 MB of production decks adhere to <= 16 entries per line.",
      "4. Cluster Staging: PBS submission scripts generated with #PBS -m abe, -M pr21vyci@mailserver.tu-freiberg.de, job_notifications.sh traps, and atomic directory locks.",
      "5. Unit Testing: 5/5 unit tests in tests/unit/test_f1824_job2_preflight.py PASS; multi-task regression tests PASS.",
      "6. Conditional Execution Discipline: Zero PBS jobs submitted; holding in WAIT state awaiting explicit user confirmation to lift max_new_pbs=0 and state PBS budget; MASTER_GOAL_STATUS = OPEN."
    ]
  },
  "image_manifest": [],
  "checkpoint_commit": "$commitSha",
  "governance": {
    "cumulative_pbs_submissions": 35,
    "max_new_pbs": 0,
    "submissions_consumed": 0,
    "production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "shared_framework_sha256": "0578156E5551173307892B8881E4BA772F099187BCF332672F39AC825023E80D",
    "master_goal_status": "OPEN",
    "holding_status": "WAIT_FOR_USER_PBS_AUTHORIZATION",
    "total_physical_elements": 160144,
    "total_layered_elements": 480432
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
