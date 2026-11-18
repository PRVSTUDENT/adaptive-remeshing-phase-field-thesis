# -*- coding: utf-8 -*-
# dispatch_f1859_review.ps1
param(
    [switch]$DryRun = $false
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$handoffId = "HND-F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON-001"
$taskId = "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON"
$commitSha = "ad75ffb9830066f74fab7944379add7552ffb839"
$manifestCommit = "bc76a877ed08f8f7ae3e5788f7f4c856e13ff172"

$promptJson = [ordered]@{
    protocol = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    correlation_id = $handoffId
    task_id = $taskId
    title = "Task F1859: Four-Benchmark Reference Comparison against Adaptive Framework for Supervisor Meeting"
    canonical_rules_sha256 = "7652FEC47E1F6BC5EADEAD8C3AF6C0CFB27BDAB04B09E364C7472EAB2604EE55"
    artifact_commit = $commitSha
    manifest_commit = $manifestCommit
    master_goal_status = "OPEN"
    research_contract = [ordered]@{
        goal_id = "PANDEY_KUMAR_NATIVE_MISESERI_CAUSAL_ADAPTIVITY_V1"
        method = "METHOD_A"
        operation = "unified_framework_synthesis"
        numerical_uncertainty = "Four-benchmark comparison of highly refined reference meshes against coarse Job-1 + F1852 adaptive remesh + Job-2 across Cases 1, 2, 3, and 5."
        expected_numerical_result = "Quantitative demonstration of discretization efficiency (Case 2: 30.1% walltime reduction, 27.9% element reduction) and physical peak load accuracy within 0.01% to 7.4% across all 4 benchmarks; 8/8 PBS jobs completed Exit 0."
        indicator_type = "DAMAGE_INFORMED_SIZING"
        indicator_role = "SEPARATE_COMPARISON"
        qualifies_native_miseseri = $false
        causal_evidence_status = "PLANNED"
        causal_evidence = [ordered]@{
            uses_future_frames = $false
            held_out_later_solution = "Offline comparison on committed benchmark reference meshes and F1852 adaptive meshes; no later held-out solution used."
        }
    }
    pbs_accounting = [ordered]@{
        authorized_new_submissions = 8
        submissions_consumed = 8
        predecessor_cumulative = 37
        current_cumulative = 45
    }
    deliverable = "Four-benchmark reference comparison of highly refined reference meshes against adaptive framework (coarse Job-1 + F1852 remesh + Job-2) with side-by-side cost and accuracy comparison table for supervisor meeting (19 Nov 2026)"
    report_artifact = "docs/validation/F1859_FOUR_BENCHMARK_REFERENCE_COMPARISON_REPORT.md"
    summary_artifact = "results/validation/f1859_four_benchmark_reference_comparison_summary.json"
    image_manifest_artifact = "results/validation/f1859_image_manifest.json"
    findings_synthesis = [ordered]@{
        case_1_edge_crack = "Ref: 13,960 el, F_max=0.7341 kN at u=0.00566 mm, walltime=7,024s. Adaptive Job-2: 20,193 el, F_max=0.7887 kN at u=0.00616 mm (+7.44% delta)."
        case_2_off_axis_hole = "Ref: 23,965 el, F_max=0.5717 kN at u=0.00548 mm, walltime=14,455s. Adaptive Job-2: 17,280 el (-27.9% elements), F_max=0.5980 kN at u=0.00577 mm (+4.60% delta), walltime=10,107s (1.2h / 30.1% walltime reduction, 60.3% CPU time reduction!)."
        case_3_pins_and_hole = "Ref: 12,110 el, F_max=4.3333 kN at u=0.05625 mm, walltime=605s. Adaptive Job-2: 45,009 el, F_max=4.3259 kN at u=0.05598 mm (0.17% load error, 0.48% disp error; near-exact physical parity)."
        case_5_seven_holes = "Ref: 15,708 el, F_max=0.7250 kN at u=0.00572 mm, walltime=14,467s. Adaptive Job-2: 15,411 el (-1.9% elements), F_max=0.7251 kN at u=0.00572 mm (<0.01% error at identical peak disp; walltime=22,095s)."
    }
    reviewer_gaps_resolved = [ordered]@{
        GAP_F1859_01 = "Artifact commit SHA verified directly from GitHub API/commit history: $commitSha."
        GAP_F1859_02 = "Image repository URLs corrected to PRVSTUDENT/adaptive-remeshing-phase-field-thesis at commit bc76a877 (verified HTTP 200)."
        GAP_F1859_03 = "Completed comparison table with all 8 solver results, peak loads, displacements at peak, and walltimes incorporated."
        GAP_F1859_04 = "Geometry values verified from case configs: Case 2 notch a=0.5 mm, Case 3 l0=0.285 mm, Case 5 l0=0.008 mm."
        GAP_F1859_05 = "Coarse Job-1 element counts reconciled: stated total deck elements vs evaluated damage population."
        GAP_F1859_06 = "Case 2 reference labelled as Sec 4.2 Mode-II count; Case 5 reference labelled as F1779 reference study target."
    }
} | ConvertTo-Json -Depth 6

$promptText = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1
$promptJson
"@

$bridgeScript = "C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1"
if (-not (Test-Path -LiteralPath $bridgeScript)) {
    throw "Missing bridge script: $bridgeScript"
}

. $bridgeScript

if ($DryRun) {
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId $handoffId -TaskId $taskId -DryRun
} else {
    Invoke-ChatGPTBridge -PromptText $promptText -HandoffId $handoffId -TaskId $taskId
}
