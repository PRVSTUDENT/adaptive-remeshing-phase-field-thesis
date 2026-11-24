# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_phase2_case2_002.ps1
# Dispatches Method C Phase 2 Case 2 Full Production Run Re-Issue 2 Validation Report
# (HND-METHOD-C-PHASE2-CASE2-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-PHASE2-CASE2-FULL-RUN-R2"
$handoffId = "HND-METHOD-C-PHASE2-CASE2-002"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-CASE2-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE2_LOCAL_FULL_RUN_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case2_full_run.py"
$testSha = (Get-FileHash -Path $testPath -Algorithm SHA256).Hash.ToUpper()

$orchPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\case2_single_job_orchestrator.py"
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$genPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\generate_case2_adaptive_corridor_mesh.py"
$genSha = (Get-FileHash -Path $genPath -Algorithm SHA256).Hash.ToUpper()

$summaryJsonPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\METHOD_C_CASE2_FULL_RUN_SUMMARY.json"
$summaryJsonSha = (Get-FileHash -Path $summaryJsonPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$payload = [ordered]@{
    protocol = "INDEPENDENT_STRUCTURED_REVIEW_V1"
    correlation_id = $handoffId
    predecessor_correlation_id = $predecessorHandoffId
    task_id = $taskId
    title = "Method C Phase 2: Pandey-Kumar Mode-I Case 2 Full Benchmark Run Re-Issue 2 Complete Specimen Fracture"
    goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
    canonical_rules_sha256 = $rulesSha
    artifact_commit = $commitSha
    checkpoint_artifact = "docs/validation/METHOD_C_CASE2_LOCAL_FULL_RUN_REPORT.md"
    checkpoint_artifact_sha256 = $reportSha
    research_contract = [ordered]@{
        goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
        method = "METHOD_C"
        operation = "method_c_phase2_case2_full_run"
        numerical_uncertainty = "Can the Case 2 full run be independently verified from committed solver outputs, with all 7 Case 2 unit tests passing from a fresh commit-pinned checkout?"
        expected_numerical_result = "Five Case 2 .sta files and five .dat files committed under local_windows_full_run/ with .gitignore un-ignore rules; test_case2_per_cycle_convergence_and_status passes from a fresh checkout; full suite 44/44 pass; NOTE gaps corrected (severance wording ~79.5% distal ligament severed with tip 0.0521 mm short of outer edge, Case 5 SEVEN_HOLE_PLATE description, artifact sizes, void jump ~0.181 mm); 0 PBS; HPC job 1424916 untouched; frozen UEL CE8D5EDC preserved; MASTER_GOAL_STATUS = OPEN."
        indicator_type = "F1852_MEASURED_DRIVER"
        indicator_role = "METHOD_C_DRIVER"
        causal_evidence_status = "PLANNED"
    }
    evidence_manifest = [ordered]@{
        validation_report = [ordered]@{
            path = "docs/validation/METHOD_C_CASE2_LOCAL_FULL_RUN_REPORT.md"
            sha256 = $reportSha
            size_bytes = (Get-Item $reportPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_CASE2_LOCAL_FULL_RUN_REPORT.md"
        }
        full_run_summary_json = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/METHOD_C_CASE2_FULL_RUN_SUMMARY.json"
            sha256 = $summaryJsonSha
            size_bytes = (Get-Item $summaryJsonPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/METHOD_C_CASE2_FULL_RUN_SUMMARY.json"
        }
        unit_test_full_run = [ordered]@{
            path = "tests/unit/test_method_c_case2_full_run.py"
            sha256 = $testSha
            size_bytes = (Get-Item $testPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_case2_full_run.py"
        }
        orchestrator_script = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/case2_single_job_orchestrator.py"
            sha256 = $orchSha
            size_bytes = (Get-Item $orchPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/case2_single_job_orchestrator.py"
        }
        mesh_generator_script = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/generate_case2_adaptive_corridor_mesh.py"
            sha256 = $genSha
            size_bytes = (Get-Item $genPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/generate_case2_adaptive_corridor_mesh.py"
        }
        frozen_uel = [ordered]@{
            path = "models/pandey_kumar_mode1/f42_mixed_uel.for"
            sha256 = $uelSha
            size_bytes = (Get-Item $uelPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
        }
        coarse_sta = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_COARSE_JOB1.sta"
            sha256 = (Get-FileHash -Path (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_COARSE_JOB1.sta") -Algorithm SHA256).Hash.ToUpper()
            size_bytes = (Get-Item (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_COARSE_JOB1.sta")).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_COARSE_JOB1.sta"
        }
        cycle1_sta = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE1.sta"
            sha256 = (Get-FileHash -Path (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE1.sta") -Algorithm SHA256).Hash.ToUpper()
            size_bytes = (Get-Item (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE1.sta")).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE1.sta"
        }
        cycle2_sta = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE2.sta"
            sha256 = (Get-FileHash -Path (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE2.sta") -Algorithm SHA256).Hash.ToUpper()
            size_bytes = (Get-Item (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE2.sta")).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE2.sta"
        }
        cycle3_sta = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE3.sta"
            sha256 = (Get-FileHash -Path (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE3.sta") -Algorithm SHA256).Hash.ToUpper()
            size_bytes = (Get-Item (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE3.sta")).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE3.sta"
        }
        cycle4_sta = [ordered]@{
            path = "models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE4.sta"
            sha256 = (Get-FileHash -Path (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE4.sta") -Algorithm SHA256).Hash.ToUpper()
            size_bytes = (Get-Item (Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\292_method_c_case2\local_windows_full_run\PK_METHOD_C_CASE2_CYCLE4.sta")).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/292_method_c_case2/local_windows_full_run/PK_METHOD_C_CASE2_CYCLE4.sta"
        }
    }
}

$payloadJson = $payload | ConvertTo-Json -Depth 10

$promptText = @"
INDEPENDENT_STRUCTURED_REVIEW_V1

$payloadJson
"@

if ($CheckOnly) {
    Write-Host "Validation check passed for $handoffId" -ForegroundColor Green
    return
}

Invoke-ChatGPTBridge -PromptText $promptText -HandoffId $handoffId -DryRun:$DryRun -LaunchPad:(-not $DryRun) -TaskId $taskId
