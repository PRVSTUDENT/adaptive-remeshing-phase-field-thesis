# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_master_closure_001.ps1
# Dispatches Method C Four-Benchmark Master Goal Closure Synthesis and Supervisor Meeting Materials
# (HND-METHOD-C-MASTER-CLOSURE-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-FOUR-BENCHMARK-CLOSURE-SYNTHESIS"
$handoffId = "HND-METHOD-C-MASTER-CLOSURE-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-CASE5-001"

$closureReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_FOUR_BENCHMARK_MASTER_GOAL_CLOSURE_REPORT.md"
if (-not (Test-Path $closureReportPath)) { throw "Report not found: $closureReportPath" }
$closureReportSha = (Get-FileHash -Path $closureReportPath -Algorithm SHA256).Hash.ToUpper()

$case5ReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE5_LOCAL_FULL_RUN_REPORT.md"
$case5ReportSha = (Get-FileHash -Path $case5ReportPath -Algorithm SHA256).Hash.ToUpper()

$meetingPath = Join-Path $PSScriptRoot "..\..\docs\meetings\2026-12-02_SUPERVISOR_MEETING_METHOD_C_SYNTHESIS_AND_SLIDES.md"
$meetingSha = (Get-FileHash -Path $meetingPath -Algorithm SHA256).Hash.ToUpper()

$closureTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_four_benchmark_closure.py"
$closureTestSha = (Get-FileHash -Path $closureTestPath -Algorithm SHA256).Hash.ToUpper()

$plotScriptPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_four_benchmark_method_c_plots.py"
$plotScriptSha = (Get-FileHash -Path $plotScriptPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$fig1Path = Join-Path $PSScriptRoot "..\..\results\figures\fig_method_c_four_benchmark_load_displacement.png"
$fig1Sha = (Get-FileHash -Path $fig1Path -Algorithm SHA256).Hash.ToUpper()

$fig2Path = Join-Path $PSScriptRoot "..\..\results\figures\fig_method_c_four_benchmark_crack_length.png"
$fig2Sha = (Get-FileHash -Path $fig2Path -Algorithm SHA256).Hash.ToUpper()

$fig3Path = Join-Path $PSScriptRoot "..\..\results\figures\fig_method_c_four_benchmark_element_counts.png"
$fig3Sha = (Get-FileHash -Path $fig3Path -Algorithm SHA256).Hash.ToUpper()

$fig4Path = Join-Path $PSScriptRoot "..\..\results\figures\fig_method_c_four_benchmark_force_continuity.png"
$fig4Sha = (Get-FileHash -Path $fig4Path -Algorithm SHA256).Hash.ToUpper()

$fig5Path = Join-Path $PSScriptRoot "..\..\results\figures\fig_method_c_four_benchmark_fracture_composite.png"
$fig5Sha = (Get-FileHash -Path $fig5Path -Algorithm SHA256).Hash.ToUpper()

$payload = [ordered]@{
    protocol = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    correlation_id = $handoffId
    predecessor_correlation_id = $predecessorHandoffId
    task_id = $taskId
    title = "Method C Four-Benchmark Master Goal Closure Synthesis and Supervisor Meeting Materials"
    goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
    canonical_rules_sha256 = $rulesSha
    artifact_commit = $commitSha
    checkpoint_artifact = "docs/validation/METHOD_C_FOUR_BENCHMARK_MASTER_GOAL_CLOSURE_REPORT.md"
    checkpoint_artifact_sha256 = $closureReportSha
    master_goal_acceptance_evidence = @(
        [ordered]@{
            benchmark = "Case 3: Mode-I Plate with Central Hole"
            status = "APPROVED"
            approval_correlation_id = "HND-METHOD-C-CASE3-FULL-RUN-COMPLETION-001"
            approval_commit = "23428fc6"
            peak_rf2_kn = 4.331822
            terminal_rf2_kn = 0.001694
            load_drop_pct = 99.96
            max_force_jump_pct = -2.63
            cycles_completed = 57
            max_elements = 30253
            severance_status = "Complete specimen severance to outer right boundary (65.0, 52.0) mm"
        },
        [ordered]@{
            benchmark = "Case 1: Pure Mode-I Edge-Notched Plate"
            status = "APPROVED"
            approval_correlation_id = "HND-METHOD-C-PHASE2-CASE1-001"
            approval_commit = "f879659b"
            peak_rf2_kn = 0.797036
            terminal_rf2_kn = 0.010952
            load_drop_pct = 98.63
            max_force_jump_pct = 2.12
            cycles_completed = 6
            max_elements = 9047
            severance_status = "Straight Mode-I horizontal cleavage to (0.9085, 0.4969) mm"
        },
        [ordered]@{
            benchmark = "Case 2: Edge-Notched Plate with Off-Axis Hole"
            status = "APPROVED"
            approval_correlation_id = "HND-METHOD-C-PHASE2-CASE2-002"
            approval_commit = "110c71fa"
            peak_rf2_kn = 0.619921
            terminal_rf2_kn = 0.008913
            load_drop_pct = 98.56
            max_force_jump_pct = -1.27
            cycles_completed = 5
            max_elements = 9876
            severance_status = "Curved trajectory into hole + distal severance to (0.9479, 0.6327) mm"
        },
        [ordered]@{
            benchmark = "Case 5: Seven-Hole Plate"
            status = "APPROVED"
            approval_correlation_id = "HND-METHOD-C-PHASE2-CASE5-001"
            approval_commit = "282913c4"
            peak_rf2_kn = 0.745825
            terminal_rf2_kn = 0.079900
            load_drop_pct = 89.30
            max_force_jump_pct = 1.82
            cycles_completed = 11
            max_elements = 15708
            severance_status = "Multi-void trajectory (h1->h4->h2->h5->h3) to far right boundary (1.0000, 0.4998) mm"
        }
    )
    research_contract = [ordered]@{
        goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
        method = "METHOD_C"
        operation = "method_c_phase2_case5_report_correction_and_master_closure_synthesis"
        numerical_uncertainty = "Can the seven Case 5 NOTE gaps be corrected in a re-issued report without changing any verified numeric, and can a master-goal closure synthesis covering all four completed cases (1, 2, 3, 5) with corrected figures and 2 Dec meeting materials be assembled for independent review?"
        expected_numerical_result = "Re-issued Case 5 report with all seven NOTE gaps corrected (51/51 suite stated or the extra 3 tests named; Cycle 3 as 52 Step 2 increments with 7 cutback retries; 88.2% and 74.6% percentages corrected; completion mechanism stated as 10-cycle cap with retrospective labelling; section 6 Case 1 row corrected to 6 cycles, 0.797036 kN peak, +2.12% max jump, EDGE_PULL, and Case 2 loading EDGE_PULL; mesh wording corrected to one canonical 15,708-element mesh), plus a master-goal closure synthesis handoff with commit-pinned evidence for all four cases and the 2 Dec meeting materials; 0 PBS submissions, cumulative 73 preserved; frozen UEL CE8D5EDC unchanged; MASTER_GOAL_STATUS = COMPLETE upon closure review approval."
        indicator_type = "F1852_MEASURED_DRIVER"
        indicator_role = "METHOD_C_DRIVER"
        causal_evidence_status = "PLANNED"
    }
    evidence_manifest = [ordered]@{
        master_closure_report = [ordered]@{
            path = "docs/validation/METHOD_C_FOUR_BENCHMARK_MASTER_GOAL_CLOSURE_REPORT.md"
            sha256 = $closureReportSha
            size_bytes = (Get-Item $closureReportPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_FOUR_BENCHMARK_MASTER_GOAL_CLOSURE_REPORT.md"
        }
        reissued_case5_report = [ordered]@{
            path = "docs/validation/METHOD_C_CASE5_LOCAL_FULL_RUN_REPORT.md"
            sha256 = $case5ReportSha
            size_bytes = (Get-Item $case5ReportPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_CASE5_LOCAL_FULL_RUN_REPORT.md"
        }
        supervisor_meeting_materials = [ordered]@{
            path = "docs/meetings/2026-12-02_SUPERVISOR_MEETING_METHOD_C_SYNTHESIS_AND_SLIDES.md"
            sha256 = $meetingSha
            size_bytes = (Get-Item $meetingPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/meetings/2026-12-02_SUPERVISOR_MEETING_METHOD_C_SYNTHESIS_AND_SLIDES.md"
        }
        closure_unit_test = [ordered]@{
            path = "tests/unit/test_method_c_four_benchmark_closure.py"
            sha256 = $closureTestSha
            size_bytes = (Get-Item $closureTestPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_four_benchmark_closure.py"
        }
        plotting_script = [ordered]@{
            path = "scripts/remeshing/generate_four_benchmark_method_c_plots.py"
            sha256 = $plotScriptSha
            size_bytes = (Get-Item $plotScriptPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/scripts/remeshing/generate_four_benchmark_method_c_plots.py"
        }
        fig_load_displacement = [ordered]@{
            path = "results/figures/fig_method_c_four_benchmark_load_displacement.png"
            sha256 = $fig1Sha
            size_bytes = (Get-Item $fig1Path).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_method_c_four_benchmark_load_displacement.png"
        }
        fig_crack_length = [ordered]@{
            path = "results/figures/fig_method_c_four_benchmark_crack_length.png"
            sha256 = $fig2Sha
            size_bytes = (Get-Item $fig2Path).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_method_c_four_benchmark_crack_length.png"
        }
        fig_element_counts = [ordered]@{
            path = "results/figures/fig_method_c_four_benchmark_element_counts.png"
            sha256 = $fig3Sha
            size_bytes = (Get-Item $fig3Path).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_method_c_four_benchmark_element_counts.png"
        }
        fig_force_continuity = [ordered]@{
            path = "results/figures/fig_method_c_four_benchmark_force_continuity.png"
            sha256 = $fig4Sha
            size_bytes = (Get-Item $fig4Path).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_method_c_four_benchmark_force_continuity.png"
        }
        fig_fracture_composite = [ordered]@{
            path = "results/figures/fig_method_c_four_benchmark_fracture_composite.png"
            sha256 = $fig5Sha
            size_bytes = (Get-Item $fig5Path).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/results/figures/fig_method_c_four_benchmark_fracture_composite.png"
        }
        frozen_uel = [ordered]@{
            path = "models/pandey_kumar_mode1/f42_mixed_uel.for"
            sha256 = $uelSha
            size_bytes = (Get-Item $uelPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
        }
    }
}

$payloadJson = $payload | ConvertTo-Json -Depth 10

$promptText = @"
INDEPENDENT_STRUCTURED_REVIEW_V1

$payloadJson
"@

if ($CheckOnly) {
    Write-Host "Validation check passed for $handoffId ($($payloadJson.Length) chars)" -ForegroundColor Green
    return
}

Invoke-ChatGPTBridge -PromptText $promptText -HandoffId $handoffId -DryRun:$DryRun -LaunchPad:(-not $DryRun) -TaskId $taskId
Write-Host "Handoff $handoffId successfully dispatched." -ForegroundColor Green
