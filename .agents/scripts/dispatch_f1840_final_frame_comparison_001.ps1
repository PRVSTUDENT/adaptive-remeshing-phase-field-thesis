# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1840_final_frame_comparison_001.ps1
# Dispatches Task F1840: Final-Frame Remesh and Comparison for Case 2 Paper-Reproduction Reference
# (HND-F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON"
$handoffId = "HND-F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON-001"
$predecessorHandoffId = "HND-F1839-F1838-EVIDENCE-COMPLETION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1840_CASE2_FINAL_FRAME_REMESH_COMPARISON_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$commitSha = (git rev-parse HEAD).Trim()

# Read figure SHA256 hashes dynamically
$figDir = Join-Path $PSScriptRoot "..\..\results\figures"
function Get-Sha256($fpath) {
    if (Test-Path $fpath) {
        return (Get-FileHash -Path $fpath -Algorithm SHA256).Hash.ToUpper()
    }
    return "PENDING"
}

$shaFinalPng = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_final_frame_mesh.png")
$shaFinalPdf = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_final_frame_mesh.pdf")
$shaCompPng  = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_comparison.png")
$shaCompPdf  = Get-Sha256 (Join-Path $figDir "fig_f1840_case2_comparison.pdf")

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1840: Final-Frame Remesh and Comparison for Case 2 Paper-Reproduction Reference",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Does remeshing from the final converged frame (Step-2 Frame 337, t=0.655825 s) of the existing Case 2 Job-1, using identical native UNIFORM_ERROR settings (4.0%, 0.001/0.020 mm, NOT_ALLOWED), produce a mesh that is better, worse or equivalent to the Frame 300 mesh (28,165 elements, 94.62% distal coverage at h<=l0/2 in the report window, Gate 06 1.7325x FAIL), and does the final frame — the paper's last-frame rule — provide a demonstrated reason to prefer it over the discretionary Frame 300 crack-arrest selection?",
    "expected_numerical_result": "A final-frame donor ODB (Step-2 Frame 337, t=0.655825 s, 7,526,008 bytes, SHA A48C17D7...) extracted with exact 0.0 field fidelity against source companion elements and committed; one native remeshed mesh from the final frame using identical settings producing 28,160 elements (97.76% quads, min det(J)=2.46e-7 > 0, max AR 2.21, body SHA A29EB817...), confirming global element count invariance against Frame 300 (-5 elements, -0.018%); distal ligament coverage in report window achieves 100.0% <= l0 and 91.48% <= l0/2 (PASS >= 90%), and in F1812 window achieves 99.75% <= l0 and 91.35% <= l0/2 (PASS >= 90%); wake resolution in notch-to-hole channel enhanced to 1,206 elements (40.63% at <= l0/2); Gate 06 coarsening ratio is 1.8043x (FAIL against >= 2.0x, improved from 1.7325x) and Gate 07 is 28,160 (PASS); commit-pinned publication images of final-frame mesh and side-by-side comparison; plain statement of basis for preference: Frame 337 is recommended as authoritative paper-reproduction reference under published protocol with superior element shape (AR 2.21) and coarsening (1.8043x), while Frame 300 serves as crack-arrest diagnostic; 0 new PBS jobs; unit tests 7/7 PASS; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/278_f1840_final_frame_comparison/PK_F1840_CASE2_FINAL_FRAME_DONOR.odb",
      "donor_sha256": "A48C17D793077BD08D9B95177CFFB9F7C4FA39ED1E6959A37F20CD515FBA27A5",
      "donor_step": "Step-2",
      "donor_frame_index": 337,
      "indicator_frame_range": "[337, 337]",
      "held_out_later_solution": "Post-remesh crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 0.655825,
      "maximum_indicator_time": 0.655825
    },
    "image_manifest": [
      {
        "case_id": "case_2_final_frame",
        "relative_path": "results/figures/fig_f1840_case2_final_frame_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1840_case2_final_frame_mesh.png",
        "sha256": "$shaFinalPng",
        "description": "Case 2 Final-Frame (337) Native Remeshed Physical Mesh (28,160 elements, 97.76% Quads, min det(J) = 2.46e-7 > 0, max AR = 2.21, 8,759 distal elements, 91.48% <= l0/2)"
      },
      {
        "case_id": "case_2_final_frame_pdf",
        "relative_path": "results/figures/fig_f1840_case2_final_frame_mesh.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1840_case2_final_frame_mesh.pdf",
        "sha256": "$shaFinalPdf",
        "description": "Case 2 Final-Frame Native Remeshed Physical Mesh Vector PDF"
      },
      {
        "case_id": "case_2_comparison",
        "relative_path": "results/figures/fig_f1840_case2_comparison.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1840_case2_comparison.png",
        "sha256": "$shaCompPng",
        "description": "Case 2 Side-by-Side Comparison: Frame 300 (Crack-Arrest Diagnostic) vs Frame 337 (Paper-Reproduction Reference)"
      },
      {
        "case_id": "case_2_comparison_pdf",
        "relative_path": "results/figures/fig_f1840_case2_comparison.pdf",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_f1840_case2_comparison.pdf",
        "sha256": "$shaCompPdf",
        "description": "Case 2 Side-by-Side Comparison Vector PDF"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1840 executes the final-frame remesh and comparison for the Case 2 paper-reproduction reference following supervisory directive under HND-F1839-F1838-EVIDENCE-COMPLETION-001: (1) Extracted Step-2 Frame 337 (Increment 338, t=0.655825 s, d_max=0.9976) into compact standalone donor PK_F1840_CASE2_FINAL_FRAME_DONOR.odb (7,526,008 bytes, SHA A48C17D7...) with 100% field fidelity against source companion UMAT elements (exact 0.0 error across MISESERI, MISESAVG, SDV1); (2) Remeshed under identical native UNIFORM_ERROR 4.0% settings ([0.001, 0.020] mm, coarsening NOT_ALLOWED, All_elem via shared framework B0857C52...), generating physical mesh PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp (28,160 elements, 97.76% quads, min det(J)=2.46e-7 > 0, max AR 2.21, body SHA A29EB817...); (3) Proved element count invariance against Frame 300 (-5 elements, -0.018%); (4) Confirmed outer distal ligament resolution in BOTH windows (report window 8,759 el, 100.0% <= l0, 91.48% <= l0/2 PASS >= 90%; F1812 window 9,052 el, 91.35% <= l0/2 PASS >= 90%); (5) Demonstrated enhanced notch-to-hole wake resolution (1,206 vs 807 elements, +49.44%, 40.63% at <= l0/2); (6) Passed finite element quality gates: Gate 01 PASS (min det J > 0), Gate 02 PASS (97.76% quads), Gate 03 PASS (max AR 2.21, improved from 2.60), Gate 06 plainly reported as 1.8043x FAIL (improved from 1.7325x), Gate 07 PASS (28,160 < 80k/30k); (7) Articulated demonstrated basis for preference: Frame 337 is recommended as authoritative paper-reproduction reference under published protocol with superior element shape (AR 2.21) and coarsening (1.8043x), while Frame 300 serves as crack-arrest diagnostic; (8) Rendered and published publication figures with commit-pinned URLs; (9) 7/7 unit tests PASS in test_f1840_final_frame_comparison.py; (10) 0 new PBS jobs consumed (cumulative 36 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1840_CASE2_FINAL_FRAME_REMESH_COMPARISON_REPORT.md",
    "report_sha256": "$reportSha"
  }
}

---
$reportContent

---
$rulesContent
"@

if ($CheckOnly) {
    Write-Host "CheckOnly mode: Assembling prompt text and validating schema..."
    $checkResult = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId -DryRun
    Write-Host "Validation successful. Prompt length: $($header.Length) characters."
    return
}

Write-Host "Dispatching Task F1840 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
