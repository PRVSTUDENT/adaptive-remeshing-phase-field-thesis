# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1844_body_sha_correction_001.ps1
# Dispatches Task F1844: Correct the Three Scale-Invariant Mesh Body SHAs
# (HND-F1844-F1837-BODY-SHA-CORRECTION-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1844-F1837-BODY-SHA-CORRECTION"
$handoffId = "HND-F1844-F1837-BODY-SHA-CORRECTION-001"
$predecessorHandoffId = "HND-F1837-F1836-ARTIFACT-TABLE-CORRECTION-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1835_REVISED_NATIVE_REFERENCE_AND_ENVELOPE_CAUSALITY_REPORT.md"
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
$imageCommitSha = "bd71626dcdd493f2a24af92df2c80d4ac7410b44"

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Task F1844: Correct the Three Scale-Invariant Mesh Body SHAs",
  "research_contract": {
    "goal_id": "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1",
    "method": "METHOD_A",
    "operation": "shared_framework_improvement",
    "numerical_uncertainty": "Correction-only: do the Section 9 INP Body SHA-256 values for the three scale-invariant meshes (SI Cases 1, 2, 3) match the values recomputed from the committed files with the committed compute_body_sha256 function?",
    "expected_numerical_result": "A corrected F1835/F1836 report, committed as a new commit, with the Section 9 INP Body SHA-256 column for SI Case 1 = D424F2FFFCC235FF2A575B664C967F68772132A8DD71E4846B0392570A6C0CBC, SI Case 2 = 4C686A3179A0688318DED9858736758353C3A55B8392305284B7EFFCDC23FA47, and SI Case 3 = 638482BE8B64DD3C233CBA136EEF22AA86A836072F0B7E01E783D7479F21D8BE (each recomputed with the committed function); all other table entries unchanged; 0 new meshes, 0 new solves, 0 new PBS jobs; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR",
    "indicator_role": "PRIMARY_NATIVE_MISESERI",
    "qualifies_native_miseseri": true,
    "causal_evidence_status": "VERIFIED",
    "causal_evidence": {
      "donor_path": "models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb",
      "donor_sha256": "E2FE195B93A6378849E134DD3FE17EC69FFD03CCA8D446496E6D30820E7958AE",
      "donor_step": "Step-2",
      "donor_frame_index": 178,
      "indicator_frame_range": "[0, 178]",
      "held_out_later_solution": "Post-peak crack propagation frames reserved exclusively for evaluation",
      "uses_future_frames": false,
      "remesh_time": 0.7257,
      "maximum_indicator_time": 0.7257
    },
    "image_manifest": [
      {
        "case_id": "case_1",
        "relative_path": "results/figures/fig_f1835_case_1_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1835_case_1_standalone_mesh.png",
        "sha256": "FCB790BAA82433564C307F76BC1CE22C9E479A958B19BD2D61E86C465CB3223F",
        "description": "Case 1 Standalone Mesh View under Scale-Invariant Envelope (F1835: 24,949 elements, 97.10% quads, Gate 06: 2.09x PASS)"
      },
      {
        "case_id": "case_2",
        "relative_path": "results/figures/fig_f1835_case_2_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1835_case_2_standalone_mesh.png",
        "sha256": "BE6BBD987F6CE26B6FE78EF9EFEA078613BD113D1DBCBA92BC815F2300A9FE41",
        "description": "Case 2 Standalone Mesh View under Scale-Invariant Envelope (F1835: 120,088 elements, 97.49% quads, Gate 06: 1.28x FAIL, 92.3% unnecessary fine area)"
      },
      {
        "case_id": "case_3",
        "relative_path": "results/figures/fig_f1835_case_3_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1835_case_3_standalone_mesh.png",
        "sha256": "FF1A8153C46B9838FF547EE08D93E2FBCD047578161E523DA1885C96791BC5BA",
        "description": "Case 3 Standalone Mesh View under Scale-Invariant Envelope (F1835: 481,766 elements, 97.45% quads, Gate 06: 1.04x FAIL, 85.0% unnecessary fine area)"
      },
      {
        "case_id": "case_5",
        "relative_path": "results/figures/fig_f1835_case_5_standalone_mesh.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1835_case_5_standalone_mesh.png",
        "sha256": "9B27240DAB3B53F41A033957C4C49A89BCEEAE364A45867FD922A62D3722C5F0",
        "description": "Case 5 Standalone Mesh View under Scale-Invariant Envelope (Table 6 Parity Preserved: 15,466 elements, 97.90% quads, Gate 06: 2.12x PASS)"
      },
      {
        "case_id": "composite",
        "relative_path": "results/figures/fig_f1835_four_benchmark_synthesis.png",
        "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$imageCommitSha/results/figures/fig_f1835_four_benchmark_synthesis.png",
        "sha256": "05582ADA31C298C2764D178B54816E4DF880C5690EA3C1FB9EDAAD920F222D2E",
        "description": "4-Panel Publication Synthesis Composite under Scale-Invariant Envelope"
      }
    ]
  },
  "review_request": {
    "summary": "Task F1844 completes the narrow correction-only mandate following supervisory review REJECT under HND-F1837-F1836-ARTIFACT-TABLE-CORRECTION-001: (1) Corrected Section 9 INP Body SHA-256 values for the three scale-invariant meshes by recomputing each with the committed compute_body_sha256 function (skipping '**' lines, stripping whitespace, appending '\n', SHA-256 uppercase): SI Case 1 = D424F2FFFCC235FF2A575B664C967F68772132A8DD71E4846B0392570A6C0CBC, SI Case 2 = 4C686A3179A0688318DED9858736758353C3A55B8392305284B7EFFCDC23FA47, and SI Case 3 = 638482BE8B64DD3C233CBA136EEF22AA86A836072F0B7E01E783D7479F21D8BE; (2) Re-verified that all 15 file size/SHA entries and the other six body SHAs match disk and table exactly; (3) Unit test suite test_f1835_revised_diagnosis.py passes 9/9 (100%); (4) Strictly correction-only: zero new meshes, zero new solves, zero new PBS jobs (cumulative 36 preserved); bitwise frozen UEL CE8D5EDC... and framework B0857C52... maintained; MASTER_GOAL_STATUS = OPEN.",
    "commit_hash": "$commitSha",
    "report_path": "docs/validation/F1835_REVISED_NATIVE_REFERENCE_AND_ENVELOPE_CAUSALITY_REPORT.md",
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

Write-Host "Dispatching Task F1844 to Independent Scientific Supervision across OpenClaw PAD Bridge..."
$response = Invoke-ChatGPTBridge -PromptText $header -HandoffId $handoffId

Write-Host "Bridge response received successfully!"
Write-Host "Response length: $($response.Length) characters."
$response
