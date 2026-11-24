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
[BRIDGE_HANDOFF_ID=HND-METHOD-C-FRAMEWORK-PHASE1B-002]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-FRAMEWORK-PHASE1B-002",
  "predecessor_correlation_id": "HND-METHOD-C-FRAMEWORK-PHASE1B-001",
  "task_id": "METHOD-C-FRAMEWORK-PHASE1B-WAKE-PRESERVING-REMESH-R2",
  "title": "Method C Framework Improvement Phase 1(b): Wake-Preserving Progressive Remeshing (Re-Issue 2)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "E7B62C984B2468025F9F8184BFD54D55BE0512F3FCEB78A31BF590376D48138B",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_FRAMEWORK_PHASE1B_WAKE_PRESERVING_REMESH_REPORT.md",
  "checkpoint_artifact_sha256": "027B2FAB2FE89A7ED1AF87AFF26D3ADF684FE2CFA5138BDC05B88CC608DE55F3",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_framework_phase1b_wake_preserving_remesh",
    "numerical_uncertainty": "Does the wake-preserving remesh keep terminal RF2 within defined tolerances of the approved run, clearly account for the severance boundary and crack tip lag, and ensure element-count unit tests are fully reproducible from committed repository artifacts?",
    "expected_numerical_result": "Defined explicit intermediate RF2 tolerance (<=10%) and detachment bound (<=16%); explained systematic physical stiffening (+5.0% to +5.7% in Cycles 49-51, +15.5% in Cycle 52) due to frozen background wake mesh eliminating artificial wake compliance. Corrected severance scope: Cycle 52 reaches xtip = 63.9531 mm (0.05 mm short of >= 64 mm stopping bound and 1.05 mm from plate edge), so severance was not reached in the 4-cycle validation run. Committed all 4 PHYS.inp mesh decks under phase1b_wake_preserving_validation/ and switched unit tests to repo-relative paths with 0 hardcoded paths. Corrected Cycle 52 full-run baseline to 28,710. Flagged Cycle 49 tip distance (0.91 mm) as borderline at 91% tolerance. 11/11 unit tests PASS in test_method_c_framework_phase1b.py and test_method_c_framework_phase1a.py. 0 PBS consumed, cumulative 73 preserved. HPC job 1424916 untouched. Frozen UEL CE8D5EDC... maintained. MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_FRAMEWORK_PHASE1B_WAKE_PRESERVING_REMESH_REPORT.md",
      "sha256": "027B2FAB2FE89A7ED1AF87AFF26D3ADF684FE2CFA5138BDC05B88CC608DE55F3",
      "size_bytes": 14540,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_FRAMEWORK_PHASE1B_WAKE_PRESERVING_REMESH_REPORT.md"
    },
    "unit_test": {
      "path": "tests/unit/test_method_c_framework_phase1b.py",
      "sha256": "E4648B4E9AFD30CB78089AD8F9DED7E15B213D2679C9BCBCF250A14CE8CE0807",
      "size_bytes": 8503,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_framework_phase1b.py"
    },
    "mesh_generator": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py",
      "sha256": "D9E5687BCA3F3A94639A2D0E4CFDEED85A57E4C697062E7BFC077778E4109AE4",
      "size_bytes": 24657,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py"
    },
    "orchestrator": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py",
      "sha256": "2A5D837E01D08D18321B9818888E77BD4B6FB03C1EE26A2F958E70CFA04FF22B",
      "size_bytes": 90936,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py"
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
    Write-Host "[Bridge] Publishing guarded request for HND-METHOD-C-FRAMEWORK-PHASE1B-002..." -ForegroundColor Cyan
    $res = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId 'HND-METHOD-C-FRAMEWORK-PHASE1B-002' -TaskId 'METHOD-C-FRAMEWORK-PHASE1B-WAKE-PRESERVING-REMESH-R2' -LaunchPad
    Write-Host "[Bridge] Handshake completed successfully. Response length: $($res.Length)" -ForegroundColor Green
    return $res
} else {
    Write-Host "[Bridge] DRY RUN - returning prompt..." -ForegroundColor Yellow
    return $prompt
}
