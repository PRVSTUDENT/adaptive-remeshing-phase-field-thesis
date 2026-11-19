# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase4_materials_001.ps1
# Dispatches Method C Phase 4: Meeting Materials & Demo Synthesis for 2 December 2026 Supervisor Meeting
# (HND-METHOD-C-PHASE4-MATERIALS-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE4-MATERIALS-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE3-PROPAGATION-003"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$slidesPath = Join-Path $PSScriptRoot "..\..\docs\presentations\2026-12-02_Method_C_Supervisor_Meeting_Slides.md"
$slidesSha = (Get-FileHash -Path $slidesPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$plotScriptPath = Join-Path $PSScriptRoot "..\..\scripts\postprocessing\plot_method_c_meeting_demo.py"
$plotScriptSha = (Get-FileHash -Path $plotScriptPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_phase4_meeting_materials.py"
$testSha = (Get-FileHash -Path $testPath -Algorithm SHA256).Hash.ToUpper()

# Figure hashes
$figLdPngSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_load_displacement.png") -Algorithm SHA256).Hash.ToUpper()
$figLdPdfSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_load_displacement.pdf") -Algorithm SHA256).Hash.ToUpper()
$figCePngSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_crack_extension.png") -Algorithm SHA256).Hash.ToUpper()
$figCePdfSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_crack_extension.pdf") -Algorithm SHA256).Hash.ToUpper()
$figSeqPngSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_damage_evolution_sequence.png") -Algorithm SHA256).Hash.ToUpper()
$figSeqPdfSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_damage_evolution_sequence.pdf") -Algorithm SHA256).Hash.ToUpper()
$figSynPngSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_loop_synthesis.png") -Algorithm SHA256).Hash.ToUpper()
$figSynPdfSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_loop_synthesis.pdf") -Algorithm SHA256).Hash.ToUpper()
$figGifSha = (Get-FileHash (Join-Path $PSScriptRoot "..\..\results\figures\method_c_demo\fig_method_c_damage_evolution.gif") -Algorithm SHA256).Hash.ToUpper()

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Phase 4: Meeting Materials & Demo Synthesis for 2 December 2026 Supervisor Meeting",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase4_meeting_materials",
    "numerical_uncertainty": "Can the verified multi-stage Method C simulation observables (Job 1 base solve -> state/history transfer -> Job 2 re-equilibration -> Job 3 forward crack growth and hole capture) be synthesized into publication-quality figures, animation, comprehensive report, and presentation slides for the 2 December 2026 supervisor meeting without fabricating values or masking the physical cutback termination (Exit 1) and void-compliance peak load reduction?",
    "expected_numerical_result": "Built 9 publication figures in PNG/PDF/GIF demonstrating the complete Method C loop from authentic solver observables: Figure 1 fig_method_c_load_displacement (RF2 vs u2 curve with Step 1 re-equilibration 0.5484 kN, peak load 0.6487 kN, hole capture at Inc 116, and post-peak softening to 0.2622 kN [-59.58%]); Figure 2 fig_method_c_crack_extension (crack tip x_tip vs u2 tracking 0.3957 mm extension with circular void geometry x in [0.65, 0.85] mm); Figure 3 fig_method_c_damage_evolution_sequence (6-panel high-res mesh + damage contour sequence covering all key milestones); Figure 4 fig_method_c_loop_synthesis (4-panel end-to-end Method C loop architecture); Figure 5 fig_method_c_damage_evolution.gif (smooth 28-frame damage evolution animation); authored comprehensive synthesis report docs/validation/METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md and slide deck docs/presentations/2026-12-02_Method_C_Supervisor_Meeting_Slides.md; 27/27 Method C unit tests PASS; 0 new PBS jobs consumed, cumulative 60 preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "meeting_materials_report": {
      "path": "docs/validation/METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md",
      "sha256": "$reportSha",
      "github_url": "$githubBase/docs/validation/METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md"
    },
    "supervisor_meeting_slides": {
      "path": "docs/presentations/2026-12-02_Method_C_Supervisor_Meeting_Slides.md",
      "sha256": "$slidesSha",
      "github_url": "$githubBase/docs/presentations/2026-12-02_Method_C_Supervisor_Meeting_Slides.md"
    },
    "plot_script": {
      "path": "scripts/postprocessing/plot_method_c_meeting_demo.py",
      "sha256": "$plotScriptSha",
      "github_url": "$githubBase/scripts/postprocessing/plot_method_c_meeting_demo.py"
    },
    "figure_load_displacement_png": {
      "path": "results/figures/method_c_demo/fig_method_c_load_displacement.png",
      "sha256": "$figLdPngSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_load_displacement.png"
    },
    "figure_load_displacement_pdf": {
      "path": "results/figures/method_c_demo/fig_method_c_load_displacement.pdf",
      "sha256": "$figLdPdfSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_load_displacement.pdf"
    },
    "figure_crack_extension_png": {
      "path": "results/figures/method_c_demo/fig_method_c_crack_extension.png",
      "sha256": "$figCePngSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_crack_extension.png"
    },
    "figure_crack_extension_pdf": {
      "path": "results/figures/method_c_demo/fig_method_c_crack_extension.pdf",
      "sha256": "$figCePdfSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_crack_extension.pdf"
    },
    "figure_damage_evolution_sequence_png": {
      "path": "results/figures/method_c_demo/fig_method_c_damage_evolution_sequence.png",
      "sha256": "$figSeqPngSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_damage_evolution_sequence.png"
    },
    "figure_damage_evolution_sequence_pdf": {
      "path": "results/figures/method_c_demo/fig_method_c_damage_evolution_sequence.pdf",
      "sha256": "$figSeqPdfSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_damage_evolution_sequence.pdf"
    },
    "figure_loop_synthesis_png": {
      "path": "results/figures/method_c_demo/fig_method_c_loop_synthesis.png",
      "sha256": "$figSynPngSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_loop_synthesis.png"
    },
    "figure_loop_synthesis_pdf": {
      "path": "results/figures/method_c_demo/fig_method_c_loop_synthesis.pdf",
      "sha256": "$figSynPdfSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_loop_synthesis.pdf"
    },
    "figure_damage_evolution_gif": {
      "path": "results/figures/method_c_demo/fig_method_c_damage_evolution.gif",
      "sha256": "$figGifSha",
      "github_url": "$githubBase/results/figures/method_c_demo/fig_method_c_damage_evolution.gif"
    },
    "unit_test_suite": {
      "path": "tests/unit/test_method_c_phase4_meeting_materials.py",
      "sha256": "$testSha",
      "github_url": "$githubBase/tests/unit/test_method_c_phase4_meeting_materials.py",
      "pass_count": 27,
      "total_count": 27,
      "pass_percentage": 100.0
    }
  },
  "accounting_and_governance": {
    "pbs_jobs_authorized_this_turn": 0,
    "pbs_jobs_consumed_this_turn": 0,
    "max_new_pbs_for_next_turn": 0,
    "cumulative_pbs_submissions": 60,
    "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
    "native_interface_sha256": "E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2",
    "framework_sha256": "42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A",
    "canonical_bridge_policy_sha256": "C595940130CA051A0947EC5F9382A59EF74066C1B7973EA5FA1B95B829A62EB6",
    "unit_tests": "27/27 PASS (100%)",
    "master_goal_status": "OPEN",
    "next_recommended_milestone": "2 December 2026 Supervisor Meeting presentation followed by thesis report chapter drafting (research freeze: 13 December 2026)."
  }
}

---
### Full Meeting Materials & Demo Synthesis Report Content:
$reportContent
"@

if ($CheckOnly) {
    Write-Output "=== DRY RUN / CHECK ONLY: Assembled Bridge Prompt ==="
    Write-Output $prompt
    return
}

Write-Output "=== DISPATCHING METHOD C PHASE 4 MEETING MATERIALS ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
