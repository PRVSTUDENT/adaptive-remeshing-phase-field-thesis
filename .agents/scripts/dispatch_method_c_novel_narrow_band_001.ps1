# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_novel_narrow_band_001.ps1
# Dispatches Method C Novel Complex Problem Narrow Damage-Following Band Campaign Report
# (HND-METHOD-C-MODE2-LPANEL-016) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-NOVEL-INCLINED-NOTCH-HOLE"
$handoffId = "HND-METHOD-C-MODE2-LPANEL-016"
$predecessorHandoffId = "HND-METHOD-C-MODE2-LPANEL-015"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_NOVEL_NARROW_BAND_CAMPAIGN_REPORT.md"
if (-not (Test-Path $reportPath)) { throw "Report not found: $reportPath" }
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$novelResultsDir = Join-Path $PSScriptRoot "..\..\models\novel_inclined_notch_hole\campaign_results_narrow_band"
$cycle9SumPath = Join-Path $novelResultsDir "PK_METHOD_C_NOVEL_CYCLE9_SUMMARY.json"
if (-not (Test-Path $cycle9SumPath)) { throw "Cycle 9 summary not found: $cycle9SumPath" }
$cycle9SumSha = (Get-FileHash -Path $cycle9SumPath -Algorithm SHA256).Hash.ToUpper()

$cycle9ImgPath = Join-Path $novelResultsDir "PK_METHOD_C_NOVEL_CYCLE9_mesh_damage.png"
if (-not (Test-Path $cycle9ImgPath)) { throw "Cycle 9 image not found: $cycle9ImgPath" }
$cycle9ImgSha = (Get-FileHash -Path $cycle9ImgPath -Algorithm SHA256).Hash.ToUpper()

$manifestPath = Join-Path $novelResultsDir "image_manifest.json"
if (-not (Test-Path $manifestPath)) { throw "Image manifest not found: $manifestPath" }
$manifestSha = (Get-FileHash -Path $manifestPath -Algorithm SHA256).Hash.ToUpper()

$gridImgPath = Join-Path $novelResultsDir "fig_narrow_band_progression_grid.png"
$compImgPath = Join-Path $novelResultsDir "fig_bounding_box_vs_narrow_band.png"
$gifPath = Join-Path $novelResultsDir "inclined_notch_hole_narrow_band_cycles_0_9.gif"
$mp4Path = Join-Path $novelResultsDir "inclined_notch_hole_narrow_band_cycles_0_9.mp4"

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_novel_inclined_notch_hole.py"
if (-not (Test-Path $testPath)) { throw "Test file not found: $testPath" }
$testSha = (Get-FileHash -Path $testPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$payload = [ordered]@{
    protocol = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    correlation_id = $handoffId
    predecessor_correlation_id = $predecessorHandoffId
    task_id = $taskId
    title = "Method C Novel Complex Problem — Narrow Damage-Following Band Fix (Replace Bounding-Box Corridor, Re-Run From Cycle 0)"
    goal_id = "METHOD_C_MODE2_LPANEL_V1"
    canonical_rules_sha256 = $rulesSha
    artifact_commit = $commitSha
    checkpoint_artifact = "docs/validation/METHOD_C_NOVEL_NARROW_BAND_CAMPAIGN_REPORT.md"
    checkpoint_artifact_sha256 = $reportSha
    research_contract = [ordered]@{
        goal_id = "METHOD_C_MODE2_LPANEL_V1"
        method = "METHOD_C"
        operation = "method_c_lpanel_setup_and_validation"
        numerical_uncertainty = "Can the narrow damage-following band (< 2% domain area) accurately guide adaptive remeshing along an a priori unknown curving mixed-mode (I+II) crack path into a circular void, maintaining 100% transfer gate compliance and achieving substantial element reduction vs. the bounding-box run?"
        expected_numerical_result = "Novel inclined notch + hole benchmark demonstrated with narrow damage-following band: 68.9% element reduction at terminal hole contact (8,597 vs 27,608 elements); 100% transfer gate pass across all 9 cycles (|Delta RF2| <= 0.8238% <= 5.0%); exact hole boundary contact at r = 0.1000 mm == R_hole; all 5 mesh quality gates pass; 0 PBS (cumulative 73 preserved), bitwise frozen UEL CE8D5EDC untouched, recommending Master Goal METHOD_C_MODE2_LPANEL_V1 completion."
        indicator_type = "DAMAGE_INFORMED_SIZING"
        indicator_role = "METHOD_C_DRIVER"
        causal_evidence_status = "VERIFIED"
        causal_evidence = [ordered]@{
            donor_sha256 = "627F5304894B16E66224D7D60A64F19D8943DEAEC3EE70D53D8F4D0F428D4066"
            donor_step = "Step-2"
            indicator_frame_range = "Cycle 8 terminal increment"
            held_out_later_solution = "Held out for subsequent advance evaluation"
            uses_future_frames = $false
            remesh_time = 1.0
            maximum_indicator_time = 1.0
        }
    }
    closeout_statement = [ordered]@{
        benchmark_status = "NOVEL_COMPLEX_PROBLEM_NARROW_BAND_COMPLETE"
        terminal_cycle = 9
        terminal_tip_mm = @(0.624884784, 0.74679476)
        cumulative_arc_length_mm = 0.318054
        distance_to_hole_center_mm = 0.1000
        hole_boundary_penetration = $true
        post_peak_load_drop_pct = 28.12
        peak_reaction_force_kn = 0.8043678998947144
        terminal_reaction_force_kn = 0.5781657099723816
        transfer_gate_pass_rate = "9/9 (100%)"
        max_transfer_force_delta_pct = -0.8238
        mesh_growth_scaling = "5,678 elements scaling dynamically to 8,597 elements (Cycle 9), achieving 68.9% reduction vs bounding box (27,608 elements), with >97.4% quads and min det(J) > 0"
        damage_overshoot_disclosure = "Cycle 9 d_max = 1.0020 represents the fully-broken limit (d = 1.0) with a 0.20% numerical overshoot of the damage DOF"
        transfer_implementation_disclosure = "scipy.spatial.cKDTree nearest-neighbour nodal damage and Gauss-point history transfer"
        campaign_completion_reason = "CONNECTED_DAMAGE_REACHED_BOUNDARY"
        master_goal_status = "OPEN"
        session_status = "INACTIVE"
        recommended_verdict = "APPROVE_AND_DECLARE_MASTER_GOAL_COMPLETE"
    }
    evidence_manifest = [ordered]@{
        validation_report = [ordered]@{
            path = "docs/validation/METHOD_C_NOVEL_NARROW_BAND_CAMPAIGN_REPORT.md"
            sha256 = $reportSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_NOVEL_NARROW_BAND_CAMPAIGN_REPORT.md"
        }
        cycle9_summary = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/PK_METHOD_C_NOVEL_CYCLE9_SUMMARY.json"
            sha256 = $cycle9SumSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/64c4604de69f76091db69bb4a8f61243a26d7598/models/novel_inclined_notch_hole/campaign_results_narrow_band/PK_METHOD_C_NOVEL_CYCLE9_SUMMARY.json"
        }
        cycle9_image = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/PK_METHOD_C_NOVEL_CYCLE9_mesh_damage.png"
            sha256 = $cycle9ImgSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/64c4604de69f76091db69bb4a8f61243a26d7598/models/novel_inclined_notch_hole/campaign_results_narrow_band/PK_METHOD_C_NOVEL_CYCLE9_mesh_damage.png"
        }
        image_manifest = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/image_manifest.json"
            sha256 = $manifestSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/68dbc805ae7fddeb83dd0ff2caba784df17d24ea/models/novel_inclined_notch_hole/campaign_results_narrow_band/image_manifest.json"
        }
        fig_progression_grid = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/fig_narrow_band_progression_grid.png"
            sha256 = (Get-FileHash -Path $gridImgPath -Algorithm SHA256).Hash.ToUpper()
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/novel_inclined_notch_hole/campaign_results_narrow_band/fig_narrow_band_progression_grid.png"
        }
        fig_bounding_box_vs_narrow_band = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/fig_bounding_box_vs_narrow_band.png"
            sha256 = (Get-FileHash -Path $compImgPath -Algorithm SHA256).Hash.ToUpper()
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/novel_inclined_notch_hole/campaign_results_narrow_band/fig_bounding_box_vs_narrow_band.png"
        }
        animation_gif = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/inclined_notch_hole_narrow_band_cycles_0_9.gif"
            sha256 = (Get-FileHash -Path $gifPath -Algorithm SHA256).Hash.ToUpper()
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/novel_inclined_notch_hole/campaign_results_narrow_band/inclined_notch_hole_narrow_band_cycles_0_9.gif"
        }
        animation_mp4 = [ordered]@{
            path = "models/novel_inclined_notch_hole/campaign_results_narrow_band/inclined_notch_hole_narrow_band_cycles_0_9.mp4"
            sha256 = (Get-FileHash -Path $mp4Path -Algorithm SHA256).Hash.ToUpper()
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/novel_inclined_notch_hole/campaign_results_narrow_band/inclined_notch_hole_narrow_band_cycles_0_9.mp4"
        }
        test_suite = [ordered]@{
            path = "tests/unit/test_method_c_novel_inclined_notch_hole.py"
            sha256 = $testSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_novel_inclined_notch_hole.py"
        }
        canonical_frozen_uel = [ordered]@{
            path = "models/pandey_kumar_mode1/f42_mixed_uel.for"
            sha256 = $uelSha
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/c4d9baa342e4726bfbb49f87c336b907fe23f1b0/models/pandey_kumar_mode1/f42_mixed_uel.for"
        }
    }
    budget_declaration = [ordered]@{
        execution_mode = "LOCAL_WORKSTATION_ONLY"
        pbs_jobs_consumed_this_package = 0
        current_cumulative_submissions = 73
        hpc_job_1424916_status = "UNTOUCHED"
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
