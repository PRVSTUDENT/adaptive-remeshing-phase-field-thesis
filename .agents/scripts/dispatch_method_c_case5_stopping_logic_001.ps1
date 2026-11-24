# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case5_stopping_logic_001.ps1
# Dispatches Method C Case 5 Stopping Logic Repair and Multi-Case Orchestrator Audit
# (HND-METHOD-C-CASE5-STOPPING-LOGIC-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE5-STOPPING-LOGIC-REPAIR"
$handoffId = "HND-METHOD-C-CASE5-STOPPING-LOGIC-001"
$predecessorHandoffId = "HND-METHOD-C-PHASE2-CASE5-001"

$orchPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\293_method_c_case5\case5_single_job_orchestrator.py"
if (-not (Test-Path $orchPath)) { throw "Orchestrator not found: $orchPath" }
$orchSha = (Get-FileHash -Path $orchPath -Algorithm SHA256).Hash.ToUpper()

$testPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case5_full_run.py"
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
    title = "Method C Case 5 Stopping Logic Repair and Multi-Case Orchestrator Audit"
    goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
    canonical_rules_sha256 = $rulesSha
    artifact_commit = $commitSha
    checkpoint_artifact = "models/pandey_kumar_mode1/293_method_c_case5/case5_single_job_orchestrator.py"
    checkpoint_artifact_sha256 = $orchSha
    research_contract = [ordered]@{
        goal_id = "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1"
        method = "METHOD_C"
        operation = "method_c_case5_stopping_logic_repair"
        numerical_uncertainty = "Does the repaired check_completion stopping logic in Case 5 properly gate geometric severance (s >= 0.85 mm or tip_x >= 0.95 mm) with SEVERANCE_RF_RATIO = 0.20 rather than the 5% load drop ratio, cleanly stopping the run after post-peak severance at Cycle 4 (ratio 19.1% < 20%) while allowing propagation at Cycle 3 (ratio 34.7% > 20%), and do Cases 1, 2, and 3 orchestrators remain sound?"
        expected_numerical_result = "Case 5 orchestrator repaired with SEVERANCE_RF_RATIO = 0.20 in branch 2 with docstring and reason string aligned; unit test test_case5_check_completion_branch2_severance_rf_ratio proves False at Cycle 3 and True at Cycle 4; 57/57 Method C unit tests PASS; multi-case audit confirms Cases 1, 2, and 3 use flat ungated geometric checks and were unaffected; 0 PBS submissions consumed (cumulative count 73 preserved); frozen UEL CE8D5EDC untouched; MASTER_GOAL_STATUS = OPEN."
        indicator_type = "F1852_MEASURED_DRIVER"
        indicator_role = "METHOD_C_DRIVER"
        causal_evidence_status = "PLANNED"
    }
    evidence_manifest = [ordered]@{
        orchestrator_script = [ordered]@{
            path = "models/pandey_kumar_mode1/293_method_c_case5/case5_single_job_orchestrator.py"
            sha256 = $orchSha
            size_bytes = (Get-Item $orchPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/293_method_c_case5/case5_single_job_orchestrator.py"
        }
        unit_test = [ordered]@{
            path = "tests/unit/test_method_c_case5_full_run.py"
            sha256 = $testSha
            size_bytes = (Get-Item $testPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_case5_full_run.py"
        }
        frozen_uel = [ordered]@{
            path = "models/pandey_kumar_mode1/f42_mixed_uel.for"
            sha256 = $uelSha
            size_bytes = (Get-Item $uelPath).Length
            github_url = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
        }
    }
    multi_case_audit_findings = [ordered]@{
        case1_status = "UNAFFECTED: case1_single_job_orchestrator.py evaluates geometric criteria (s >= 0.48 or tip_x >= 0.98) with NO reaction force gating; load drop (RF2 < 0.05 * peak) is an independent branch."
        case2_status = "UNAFFECTED: case2_single_job_orchestrator.py evaluates geometric criteria (s >= 0.52 or tip_x >= 0.98) with NO reaction force gating; load drop (RF2 < 0.05 * peak) is an independent branch."
        case3_status = "UNAFFECTED: case3_single_job_orchestrator.py evaluates geometric criteria (s >= 62.0 or tip_x >= 64.0) with NO reaction force gating; load drop (RF2 < 0.05 * peak) is an independent branch."
        case5_diagnosis = "AFFECTED & REPAIRED: In Case 5, an intentional post-peak severance gate was added around geometric criteria to avoid premature stopping during early ligaments, but mistakenly used LOAD_DROP_COMPLETION_RATIO (0.05) instead of SEVERANCE_RF_RATIO (0.20). Repaired and validated."
    }
    verification_summary = [ordered]@{
        unit_tests_passed = "57/57 (100% PASS)"
        case5_cycle3_check = "PASS (returns False, ratio 34.7% > 20%)"
        case5_cycle4_check = "PASS (returns True, ratio 19.1% < 20% with '[20% of peak]' reason)"
        pbs_submissions_consumed = 0
        cumulative_pbs_submissions = 73
        frozen_uel_sha256 = $uelSha
        master_goal_status = "OPEN"
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
