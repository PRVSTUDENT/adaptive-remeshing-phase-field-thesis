# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase4_materials_003.ps1
# Dispatches Method C Phase 4: Meeting Materials & Demo Synthesis Re-Issue 2 for 2 December 2026 Supervisor Meeting
# (HND-METHOD-C-PHASE4-MATERIALS-003) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON"
$handoffId = "HND-METHOD-C-PHASE4-MATERIALS-003"
$predecessorHandoffId = "HND-METHOD-C-PHASE4-MATERIALS-002"

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
  "title": "Method C Phase 4: Meeting Materials & Demo Synthesis Re-Issue 2 for 2 December 2026 Supervisor Meeting",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_PHASE4_MEETING_MATERIALS_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_phase4_meeting_materials",
    "numerical_uncertainty": "Can the load-displacement Peak Load annotation be repositioned to the upper-right clear of the upper-left legend (GAP-MC-P4-04R), and crack-extension void annotations shifted clear of the right boundary (NOTE-MC-P4-06R), completing the Phase 4 meeting-materials figures without affecting underlying observables or introducing regressions?",
    "expected_numerical_result": "Load-displacement figure regenerated with Peak Load callout relocated to (u2 + 0.8, 0.67) [u2 = 6.917 um, F = 0.67 kN], completely clear of the upper-left legend box and softening curve; crack-extension figure regenerated with annotations shifted leftward into the open void band and x-axis expanded to 9.8 um, guaranteeing generous right-edge margins; GIF terminal frame confirmed displaying x_tip = 0.896 mm; all 32 unit tests PASS (100%); meeting report updated with Section 6.2; 0 new PBS jobs consumed, cumulative 60 strictly preserved; MASTER_GOAL_STATUS = OPEN.",
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
      "pass_count": 32,
      "total_count": 32,
      "pass_percentage": 100.0,
      "suite_breakdown": "10 kickoff + 3 Job-1 observables + 3 Job-2 re-equilibration + 5 transfer re-equilibration + 6 Phase-3 propagation + 5 Phase-4 meeting materials = 32"
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
    "unit_tests": "32/32 PASS (100%)",
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

Write-Output "=== DISPATCHING METHOD C PHASE 4 MEETING MATERIALS RE-ISSUE 2 ($handoffId) ==="
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TimeoutMinutes 40
