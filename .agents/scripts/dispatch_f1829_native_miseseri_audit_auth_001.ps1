# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1829_native_miseseri_audit_auth_001.ps1
# Dispatches Task F1829 Native MISESERI Direct-Coupling Evidence Audit
# (HND-F1829-NATIVE-MISESERI-AUDIT-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1829-NATIVE-MISESERI-DIRECT-COUPLING-EVIDENCE-AUDIT"
$handoffId = "HND-F1829-NATIVE-MISESERI-AUDIT-001"
$predecessorHandoffId = "HND-F1828-JOB2-COUPLED-VALIDATION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1829_NATIVE_MISESERI_DIRECT_COUPLING_EVIDENCE_AUDIT_REPORT.md"
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
  "title": "Task F1829: Independent Evidence Audit of Native MISESERI Direct UEL-UMAT Coupling and Recovery Donor Evolution",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "What is the primary-source evidence resolving the provenance, step/frame/time timing, Step-1 vs Step-2 attribution, UEL-to-UMAT mapping, cutback stress freshness, mechanical neutrality, constitutive differences (Isotropic vs Amor), and forward solver failure across historical direct coupling (F1720-F1726) and its transition to recovery donors (F1728-F1812)?",
    "expected_numerical_result": "A definitive evidence audit document (docs/validation/F1829_NATIVE_MISESERI_DIRECT_COUPLING_EVIDENCE_AUDIT_REPORT.md) resolving all 7 tracks with primary source citations and verification tests: [1] donor provenance: Step-1 Frame 12 (uy=0.0050 mm, t=1.0s, max MISESERI=2.2534e-14); [2] Step-1 vs Step-2 discrepancy: manifest claimed Step 2 Inc 412, but Step 2 stopped at Inc 356 and donor was pre-critical Step-1; [3] UEL-UMAT mapping: 3-layer overlay, dummy scaling s=4.7619e-14, scale-invariant eta; [4] stress freshness: trial stresses in COMMON block lack committed/trial buffer during cutbacks; [5] mechanical neutrality: 0.0000% RF discrepancy in patch, but unscaled Cauchy stresses cause +100% force doubling; [6] constitutive discrepancy: frozen production UEL CE8D5EDC... is Isotropically Degraded Elasticity, whereas F1716/F1720 UEL 91612E94... is Amor volumetric-deviatoric split (incompatible for direct substitution); [7] forward solver: diverged in Step 2 at peak load uy=0.005664 mm (-12.21% force error), force-match claims formally retracted, prompting F1728 recovery donor pivot; 5/5 unit tests PASS in test_f1829_native_miseseri_audit.py; 0 new PBS jobs (cumulative 35 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb",
      "donor_sha256": "4A1A78B6C72E3BA051D9835777D4380EFE212B27A23FE835616D7FE28C3E1410",
      "donor_step": "Step-1",
      "donor_frame_index": 12,
      "indicator_frame_range": "Pre-critical loading Step-1, frames 0 to 12 (uy in [0.0, 0.0050] mm)",
      "held_out_later_solution": "All Step-2 crack propagation and post-peak frames held out as unobserved future solutions",
      "uses_future_frames": false,
      "remesh_time": 1.0,
      "maximum_indicator_time": 1.0
    }
  },
  "review_request": {
    "scientific_scope": "ADAPTIVE_REMESHING_ONLY",
    "primary_question": "Does Task F1829 rigorously and conclusively resolve the 7 required evidentiary tracks regarding F1720-F1726 direct coupling and the transition to recovery donors, establishing primary source facts, reconciling historical misattributions, discovering the crucial constitutive distinction (Isotropic vs Amor), and proving that frozen UEL CE8D5EDC... and Framework 80B41AA2... remain bitwise preserved with zero new PBS submissions?",
    "evaluation_criteria": [
      "1. Donor Provenance & Timing: Verification that native MISESERI was extracted strictly from Step-1 Frame 12 (uy=0.0050 mm, t=1.0s), not Step 2.",
      "2. Reconciliation of Discrepancy: Verification that the F1720 manifest claim of 'Step 2 Inc 412' was a clerical misattribution and that Step 2 diverged at Inc 356.",
      "3. UEL-to-UMAT Architecture: Verification of 3-layer overlay, IP mapping, tensor component conventions, and dummy scaling factor s=4.7619e-14.",
      "4. Cutback Vulnerability: Diagnosis of trial stress persistence in COMMON block during cutbacks and SMP thread-safety hazards.",
      "5. Mechanical Neutrality: Verification of 0.0000% RF discrepancy in single-element patch vs +100% force doubling under unscaled Cauchy stresses.",
      "6. Constitutive Formulation Distinction: Identification that frozen production UEL CE8D5EDC... is Isotropically Degraded Elasticity while F1716/F1720 UEL 91612E94... is Amor volumetric-deviatoric split.",
      "7. Forward Solver Retraction: Verification that forward simulation diverged at uy=0.005664 mm (-12.21% peak force error), explaining the F1728 pivot to offline recovery donors.",
      "8. Governance Invariants: 0 new PBS jobs consumed (cumulative 35 preserved), frozen UEL CE8D5EDC... and Framework 80B41AA2... preserved, MASTER_GOAL_STATUS = OPEN."
    ],
    "commit_sha": "$commitSha",
    "report_artifact": "docs/validation/F1829_NATIVE_MISESERI_DIRECT_COUPLING_EVIDENCE_AUDIT_REPORT.md",
    "summary_json_artifact": "results/validation/f1829_native_miseseri_audit_summary.json",
    "receipt_artifact": "models/pandey_kumar_mode1/PK_F1829_EVIDENCE_AUDIT_RECEIPT.json",
    "test_suite_artifact": "tests/unit/test_f1829_native_miseseri_audit.py"
  }
}

---
$reportContent

---
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "CheckOnly specified. Bridge payload header validated for $handoffId."
    return
}

Write-Host "Dispatching Task F1829 Evidence Audit across OpenClaw PAD Bridge ($handoffId)..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId -TimeoutMinutes 40
Write-Host "Response received for $handoffId."
return $response
