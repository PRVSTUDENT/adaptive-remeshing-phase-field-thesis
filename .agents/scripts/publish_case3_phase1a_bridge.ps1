param(
    [string]$CommitSha = "HEAD",
    [switch]$Publish = $false
)

. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Bridge-ResearchContract.ps1'
. 'C:\Users\pruth\OpenClawPAD\ChatGPTBridge\Invoke-ChatGPTBridge.ps1'

if ($CommitSha -eq "HEAD") {
    $commitSha = (git rev-parse HEAD).Trim()
} else {
    $commitSha = $CommitSha.Trim()
}

$prompt = @"
[BRIDGE_HANDOFF_ID=HND-METHOD-C-FRAMEWORK-PHASE1A-001]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-FRAMEWORK-PHASE1A-001",
  "predecessor_correlation_id": "HND-METHOD-C-CASE3-FULL-RUN-COMPLETION-001",
  "task_id": "METHOD-C-FRAMEWORK-PHASE1A-REPORTING-GAPS",
  "title": "Method C Framework Improvement Phase 1(a): Close Reporting Gaps",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "E7B62C984B2468025F9F8184BFD54D55BE0512F3FCEB78A31BF590376D48138B",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_FRAMEWORK_PHASE1A_REPORTING_GAPS_REPORT.md",
  "checkpoint_artifact_sha256": "AFC2C6ABFC4F26A0133887B4BCA72353B82D62F939D2983FA64563B088BAAA05",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_framework_phase1a_reporting_gaps",
    "numerical_uncertainty": "Does resolving the whitespace parsing sensitivity in parse_dat_rf2 recover accurate, independent Step 1 hold reaction forces across RIKS cycles (49-56), and do pre-severance cycles satisfy the <= 5.0% force continuity gate?",
    "expected_numerical_result": "Whitespace sensitivity (STEP    1 vs STEP  1) resolved via regex. Step 1 hold RF2 extracted independently for all RIKS cycles (step1_rf2 != terminal_rf2). All pre-severance cycles strictly pass the <= 5.0% force continuity gate: Cycle 49 (-1.05%), Cycle 50 (-2.24%), Cycle 51 (-1.56%), Cycle 52 (-3.79%). RIKS termination rule and LPF overshoot mechanism documented from Abaqus 2024 solver mechanics (increment-end evaluation). Manifest mesh-generator SHA corrected to 9524B385... 5/5 dedicated unit tests PASS in test_method_c_framework_phase1a.py. 0 PBS consumed, cumulative 73 preserved. HPC job 1424916 untouched. Frozen UEL CE8D5EDC... maintained. MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_FRAMEWORK_PHASE1A_REPORTING_GAPS_REPORT.md",
      "sha256": "AFC2C6ABFC4F26A0133887B4BCA72353B82D62F939D2983FA64563B088BAAA05",
      "size_bytes": 7436,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_FRAMEWORK_PHASE1A_REPORTING_GAPS_REPORT.md"
    },
    "unit_test": {
      "path": "tests/unit/test_method_c_framework_phase1a.py",
      "sha256": "4C3B651D79845984B95EEFC972E79CEF3D6075B796F60412A9E96D35A67E5481",
      "size_bytes": 4825,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_framework_phase1a.py"
    },
    "manifest": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json",
      "sha256": "1E431DC7FDBADF907EAF16AA2B33DE0B6AA0C044D13D067E66C9005237566676",
      "size_bytes": 4125,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
    },
    "mesh_generator": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "9524B385BC4928BC077A67C0110CDBFBE76A15AE1AC3D34F4E00996AA7B60B3C",
      "size_bytes": 24779,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "size_bytes": 29722,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
    }
  }
}
"@

if ($Publish) {
    Write-Host "[Bridge] Publishing guarded request for HND-METHOD-C-FRAMEWORK-PHASE1A-001..." -ForegroundColor Cyan
    $res = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-METHOD-C-FRAMEWORK-PHASE1A-001' -TaskId 'METHOD-C-FRAMEWORK-PHASE1A-REPORTING-GAPS' -LaunchPad
    Write-Host "[Bridge] Handshake completed successfully. Response length: $($res.Length)" -ForegroundColor Green
    return $res
} else {
    Write-Host "[Bridge] DRY RUN - returning prompt..." -ForegroundColor Yellow
    return $prompt
}
