# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_master_closure_002.ps1
# Dispatches Method C Four-Benchmark Master Goal Closure Synthesis Re-Issue 2
# (HND-METHOD-C-MASTER-CLOSURE-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-FOUR-BENCHMARK-CLOSURE-SYNTHESIS-R2"
$handoffId = "HND-METHOD-C-MASTER-CLOSURE-002"
$predecessorHandoffId = "HND-METHOD-C-MASTER-CLOSURE-001"

$closureReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_FOUR_BENCHMARK_MASTER_GOAL_CLOSURE_REPORT.md"
if (-not (Test-Path $closureReportPath)) { throw "Report not found: $closureReportPath" }
$closureReportSha = (Get-FileHash -Path $closureReportPath -Algorithm SHA256).Hash.ToUpper()

$case5ReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE5_LOCAL_FULL_RUN_REPORT.md"
if (-not (Test-Path $case5ReportPath)) { throw "Report not found: $case5ReportPath" }
$case5ReportSha = (Get-FileHash -Path $case5ReportPath -Algorithm SHA256).Hash.ToUpper()

$meetingPath = Join-Path $PSScriptRoot "..\..\docs\meetings\2026-12-02_SUPERVISOR_MEETING_METHOD_C_SYNTHESIS_AND_SLIDES.md"
if (-not (Test-Path $meetingPath)) { throw "Meeting materials not found: $meetingPath" }
$meetingSha = (Get-FileHash -Path $meetingPath -Algorithm SHA256).Hash.ToUpper()

$closureTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_four_benchmark_closure.py"
if (-not (Test-Path $closureTestPath)) { throw "Closure test not found: $closureTestPath" }
$closureTestSha = (Get-FileHash -Path $closureTestPath -Algorithm SHA256).Hash.ToUpper()

$case5TestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case5_full_run.py"
if (-not (Test-Path $case5TestPath)) { throw "Case 5 test not found: $case5TestPath" }
$case5TestSha = (Get-FileHash -Path $case5TestPath -Algorithm SHA256).Hash.ToUpper()

$case5OrchPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\293_method_c_case5\case5_single_job_orchestrator.py"
if (-not (Test-Path $case5OrchPath)) { throw "Case 5 orchestrator not found: $case5OrchPath" }
$case5OrchSha = (Get-FileHash -Path $case5OrchPath -Algorithm SHA256).Hash.ToUpper()

$plotScriptPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_four_benchmark_method_c_plots.py"
if (-not (Test-Path $plotScriptPath)) { throw "Plot script not found: $plotScriptPath" }
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
    title = "Method C Four-Benchmark Master Goal Closure Synthesis Re-Issue 2"
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
            max_force_jump_pct = -11.31
            subsequent_transfers_max_jump_pct = -3.79
            cycles_completed = 57
            max_elements = 30253
            severance_status = "Complete specimen severance to outer right boundary (65.0, 52.0) mm"
        },
        [ordered]@{
            benchmark = "Case 1: Pure Mode-I Edge-Notched Plate"
            status = "APPROVED"
            approval_correlation_id = "HND-METHOD-C-PHASE2-CASE1-001"
            approval_commit = "07430adb"
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
            approval_commit = "daf91780"
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
            stopping_logic_repair_commit = "0b3eeb4c"
            stopping_logic_review_correlation_id = "HND-METHOD-C-CASE5-STOPPING-LOGIC-001"
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
        numerical_uncertainty = "Can the closure synthesis be re-issued with all 8 review gaps (GAP-MC-01 through 08) resolved and the approved Case 5 stopping-logic repair (GAP-SL-01, commit 0b3eeb4c) integrated, confirming complete master goal fulfillment across all four benchmarks?"
        expected_numerical_result = "Corrected closure synthesis handoff with commit-pinned evidence: approval commits 07430adb (Case 1) and daf91780 (Case 2) verified to resolve; Case 3 maximum hold jump stated as -11.31% at Cycle 1 with Phase 1(d) stiffness-locking explanation and all subsequent transfers <= 5.0%; closure test includes Case 3 in gate check and passes; all five figures regenerated from completed Case 3 summary with real mesh counts and Euclidean arc length; meeting materials attribute 4-case expansion to owner directive (24 Nov 2026) and state ~79% distal, 0.008401 mm and 0.009395 mm; Case 5 section cites approved stopping-logic repair (0b3eeb4c, SEVERANCE_RF_RATIO = 0.20) and distinguishes historical summary label from repaired logic; full active suite 57/57 PASS; 0 PBS submissions, cumulative 73 preserved; frozen UEL CE8D5EDC unchanged; MASTER_GOAL_STATUS = COMPLETE upon closure review approval."
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
        case5_unit_test = [ordered]@{
            path = "tests/unit/test_method_c_case5_full_run.py"
            sha256 = $case5TestSha
            size_bytes = (Get-Item $case5TestPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_case5_full_run.py"
        }
        case5_orchestrator = [ordered]@{
            path = "models/pandey_kumar_mode1/293_method_c_case5/case5_single_job_orchestrator.py"
            sha256 = $case5OrchSha
            size_bytes = (Get-Item $case5OrchPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/293_method_c_case5/case5_single_job_orchestrator.py"
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
