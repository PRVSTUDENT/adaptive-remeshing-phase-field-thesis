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
[BRIDGE_HANDOFF_ID=HND-METHOD-C-FRAMEWORK-PHASE1D-002]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-METHOD-C-FRAMEWORK-PHASE1D-002",
  "predecessor_correlation_id": "HND-METHOD-C-FRAMEWORK-PHASE1D-001",
  "task_id": "METHOD-C-FRAMEWORK-PHASE1D-HOLD-FORCE-DROP-INVESTIGATION-R2",
  "title": "Method C Framework Improvement Phase 1(d): Hold-Force Drop Numerical Investigation Re-Issue 2",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "E7B62C984B2468025F9F8184BFD54D55BE0512F3FCEB78A31BF590376D48138B",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_FRAMEWORK_PHASE1D_HOLD_FORCE_INVESTIGATION_REPORT.md",
  "checkpoint_artifact_sha256": "8016678A25CC4C6D27382F7662EC379D5171577262F1753D59299C8E2A77B0C6",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_framework_phase1d_hold_force_drop_investigation",
    "numerical_uncertainty": "Can the Case A/B hold-force results be independently verified from committed solver outputs, with all 22 unit tests passing from a fresh commit-pinned checkout?",
    "expected_numerical_result": "Committed all four Abaqus solver output files (CASE3_C48_SAME_MESH_PER_GP.dat [D1B72EBC...], .sta [988432EB...], CASE3_C48_SAME_MESH_ELEM_AVG.dat [31B3FD3B...], .sta [0C98AEA2...]) under models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/ with un-ignore rules in .gitignore; updated test_method_c_framework_phase1d.py to use 100% committed repo-relative paths, resolving GAP-P1D-01; corrected Section 6.2 geometry to 65 x 120 mm plate with central hole at (36.5, 51.0) mm (GAP-P1D-02); corrected Section 5.3 Phase 1(b) Cycle 49 hold jump to -0.6134% (2.3118 -> 2.2976 kN) (GAP-P1D-03); corrected Section 5.1 far-side damage to d ~ 0.48 (d_max = 0.4775) (GAP-P1D-04); reworded 'machine precision' to 'reproduces donor force to within 0.0004% (solver convergence residual)' (GAP-P1D-05); 22/22 unit tests pass across Phases 1(a)-1(d); 0 PBS consumed (cumulative 73); frozen UEL CE8D5EDC preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "validation_report": {
      "path": "docs/validation/METHOD_C_FRAMEWORK_PHASE1D_HOLD_FORCE_INVESTIGATION_REPORT.md",
      "sha256": "8016678A25CC4C6D27382F7662EC379D5171577262F1753D59299C8E2A77B0C6",
      "size_bytes": 16978,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_FRAMEWORK_PHASE1D_HOLD_FORCE_INVESTIGATION_REPORT.md"
    },
    "comparison_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/PHASE1D_HOLD_FORCE_COMPARISON_SUMMARY.json",
      "sha256": "763B78A4EDD7FF36516BB6C91298A6044B002DA20EA9D2F6E022A79186B8293B",
      "size_bytes": 3372,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/PHASE1D_HOLD_FORCE_COMPARISON_SUMMARY.json"
    },
    "physical_donor_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/PK_METHOD_C_CASE3_CYCLE48_PHYS.inp",
      "sha256": "3B56CC50DD5E34557FF8F688F9D9E5DEE77EADC9DD9EC5BC8A9D1273B37EABA8",
      "size_bytes": 1201402,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/PK_METHOD_C_CASE3_CYCLE48_PHYS.inp"
    },
    "case_a_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_PER_GP.dat",
      "sha256": "D1B72EBC51F702D2AC5614591B07EA5E811A6327E79F1290AFF1D335C6EB8AD0",
      "size_bytes": 73443,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_PER_GP.dat"
    },
    "case_a_sta": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_PER_GP.sta",
      "sha256": "988432EB7296DBAC726B2412870093EBA0AB097E388D2FE81D57A1162BAF17FE",
      "size_bytes": 7085,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_PER_GP.sta"
    },
    "case_b_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_ELEM_AVG.dat",
      "sha256": "31B3FD3BD22FBA6F7FC6D27FF87F4D655DA1C8C273A1B9DC9517C8A6FA8AAA43",
      "size_bytes": 50623,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_ELEM_AVG.dat"
    },
    "case_b_sta": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_ELEM_AVG.sta",
      "sha256": "0C98AEA233CECE30A5239709C2B85F08C524CD8B6227BDE92247D011E93B6101",
      "size_bytes": 4412,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/290_method_c_case3/phase1d_hold_force_investigation/CASE3_C48_SAME_MESH_ELEM_AVG.sta"
    },
    "unit_test": {
      "path": "tests/unit/test_method_c_framework_phase1d.py",
      "sha256": "14EF8A183CEABB18620921822A0267BA9095E0A69B9573A72FC7B68EB13E0625",
      "size_bytes": 8237,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/tests/unit/test_method_c_framework_phase1d.py"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
      "size_bytes": 29722,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "phase1c_report_corrected": {
      "path": "docs/validation/METHOD_C_FRAMEWORK_PHASE1C_ARC_LENGTH_CRACK_MEASURE_REPORT.md",
      "sha256": "3EB167C1CE80B414E23633881A9FDFB3CAF55A008901A00AD3075880A8D79D1D",
      "size_bytes": 15932,
      "github_url": "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha/docs/validation/METHOD_C_FRAMEWORK_PHASE1C_ARC_LENGTH_CRACK_MEASURE_REPORT.md"
    }
  }
}
"@

if ($Publish) {
    Write-Host "Publishing HND-METHOD-C-FRAMEWORK-PHASE1D-002 to ChatGPT Bridge..." -ForegroundColor Cyan
    Invoke-ChatGPTBridge -Prompt $prompt -CorrelationId "HND-METHOD-C-FRAMEWORK-PHASE1D-002"
} else {
    Write-Host "Dry run prompt generated for commit $commitSha." -ForegroundColor Yellow
    Write-Output $prompt
}
