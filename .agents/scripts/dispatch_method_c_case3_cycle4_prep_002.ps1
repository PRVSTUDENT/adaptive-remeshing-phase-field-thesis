# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_cycle4_prep_002.ps1
# Dispatches Method C Case 3: Cycle-4 Refinement Package Preparation (Re-issue 002)
# (HND-METHOD-C-CASE3-CYCLE4-PREP-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-CYCLE4-REFINEMENT-PACKAGE"
$handoffId = "HND-METHOD-C-CASE3-CYCLE4-PREP-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-CYCLE4-PREP-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_CYCLE4_PREPARATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()
$reportSize = (Get-Item $reportPath).Length

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$donorPath = Join-Path $caseDir "donor_case3_cycle3_state.json"
$donorSha = (Get-FileHash -Path $donorPath -Algorithm SHA256).Hash.ToUpper()
$donorSize = (Get-Item $donorPath).Length

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()
$meshSize = (Get-Item $meshPath).Length

$auditPath = Join-Path $caseDir "method_c_case3_cycle4_mesh_audit.json"
$auditSha = (Get-FileHash -Path $auditPath -Algorithm SHA256).Hash.ToUpper()
$auditSize = (Get-Item $auditPath).Length

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()
$deckSize = (Get-Item $deckPath).Length

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()
$receiptSize = (Get-Item $receiptPath).Length

$datacheckDatPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat"
$datacheckDatSha = (Get-FileHash -Path $datacheckDatPath -Algorithm SHA256).Hash.ToUpper()
$datacheckDatSize = (Get-Item $datacheckDatPath).Length

$datacheckMsgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg"
$datacheckMsgSha = (Get-FileHash -Path $datacheckMsgPath -Algorithm SHA256).Hash.ToUpper()
$datacheckMsgSize = (Get-Item $datacheckMsgPath).Length

$submitPbsPath = Join-Path $caseDir "submit_case3_cycle4_job5.pbs"
$submitPbsSha = (Get-FileHash -Path $submitPbsPath -Algorithm SHA256).Hash.ToUpper()
$submitPbsSize = (Get-Item $submitPbsPath).Length

$datacheckShPath = Join-Path $caseDir "run_case3_cycle4_datacheck.sh"
$datacheckShSha = (Get-FileHash -Path $datacheckShPath -Algorithm SHA256).Hash.ToUpper()
$datacheckShSize = (Get-Item $datacheckShPath).Length

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()
$uelSize = (Get-Item $uelPath).Length

$meshGenPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_method_c_case3_cycle4_mesh.py"
$meshGenSha = (Get-FileHash -Path $meshGenPath -Algorithm SHA256).Hash.ToUpper()
$meshGenSize = (Get-Item $meshGenPath).Length

$meshAuditScriptPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\audit_method_c_case3_cycle4_mesh.py"
$meshAuditScriptSha = (Get-FileHash -Path $meshAuditScriptPath -Algorithm SHA256).Hash.ToUpper()
$meshAuditScriptSize = (Get-Item $meshAuditScriptPath).Length

$stateTransferPath = Join-Path $PSScriptRoot "..\..\scripts\state_transfer\run_case3_cycle4_state_transfer.py"
$stateTransferSha = (Get-FileHash -Path $stateTransferPath -Algorithm SHA256).Hash.ToUpper()
$stateTransferSize = (Get-Item $stateTransferPath).Length

$unitTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_cycle4_package.py"
$unitTestSha = (Get-FileHash -Path $unitTestPath -Algorithm SHA256).Hash.ToUpper()
$unitTestSize = (Get-Item $unitTestPath).Length

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Case 3: Cycle-4 Refinement Package Preparation (Re-issue 002)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_CYCLE4_PREPARATION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_cycle4_refinement_package",
    "numerical_uncertainty": "Can the Cycle-4 adaptive refinement package resolve all 5 review gaps (GAP-C4P-01..05) by hardcoding authentic Section 4.3 benchmark Gc=0.00228 kN/mm into generator and deck, disclosing the Gc timeline across Jobs 1-5, correcting Section 8 NOTE-01 citation SHAs and Section 2/8 coordinates, updating Section 9 file manifest sizes to exact committed bytes, verifying datacheck Exit 0 telemetry of 11 warnings, 0 errors, 1 distorted element, and passing 6/6 unit tests without consuming PBS jobs?",
    "expected_numerical_result": "Cycle-4 refinement package re-issued and fully verified under HND-METHOD-C-CASE3-CYCLE4-PREP-002: authentic Job-4 donor terminal state ingested; PK_METHOD_C_CASE3_CYCLE4_PHYS.inp with 64,653 elements (97.38% quads, min det(J)=6.063e-4 > 0, AR=1.263 <= 2.5, max AR=3.879 <= 4.0, all gates PASS); measured forward crack path element-size distribution median h=0.1248 mm <= l0/2=0.1425 mm; state transfer via isoparametric_gp_transfer.py with convex_clamp preserving non-negativity H_min=1.116e-11 MPa >= 0 and zero healing d_max=0.992229 (preservation ratio basis 99.53% relative to reconstructed donor max 0.996882); benchmark Gc=0.00228 kN/mm hardcoded in run_case3_cycle4_state_transfer.py and verified in *UEL PROPERTY cards; 3-layer coupled deck PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp with 193,959 elements (DF46D07B...); mitigations dt_min=1e-14 in both steps, line search data line 4, CONST_HOLD, and TYPE=SOLUTION initial conditions; cluster datacheck passed Exit 0 with exactly 11 warnings, 0 errors, 1 distorted element verified; all Section 8 NOTE-01 SHAs corrected to 64-character strings; crack tip y=69.8266 mm and node 21774 y=69.780 mm; Section 9 manifest sizes matching exact committed bytes; 6/6 dedicated unit tests PASS (100%); 0 new PBS jobs consumed, cumulative 66 strictly preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "package_report": {
      "path": "docs/validation/METHOD_C_CASE3_CYCLE4_PREPARATION_REPORT.md",
      "sha256": "$reportSha",
      "bytes": $reportSize,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_CYCLE4_PREPARATION_REPORT.md"
    },
    "donor_state": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle3_state.json",
      "sha256": "$donorSha",
      "bytes": $donorSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle3_state.json"
    },
    "adapted_physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp",
      "sha256": "$meshSha",
      "bytes": $meshSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_PHYS.inp"
    },
    "mesh_quality_audit": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle4_mesh_audit.json",
      "sha256": "$auditSha",
      "bytes": $auditSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle4_mesh_audit.json"
    },
    "state_transfer_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json",
      "sha256": "$receiptSha",
      "bytes": $receiptSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_TRANSFER_RECEIPT.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp",
      "sha256": "$deckSha",
      "bytes": $deckSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp"
    },
    "datacheck_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat",
      "sha256": "$datacheckDatSha",
      "bytes": $datacheckDatSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat"
    },
    "datacheck_msg": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg",
      "sha256": "$datacheckMsgSha",
      "bytes": $datacheckMsgSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg"
    },
    "submit_pbs": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle4_job5.pbs",
      "sha256": "$submitPbsSha",
      "bytes": $submitPbsSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle4_job5.pbs"
    },
    "datacheck_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle4_datacheck.sh",
      "sha256": "$datacheckShSha",
      "bytes": $datacheckShSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle4_datacheck.sh"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "bytes": $uelSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "mesh_generator_script": {
      "path": "scripts/remeshing/generate_method_c_case3_cycle4_mesh.py",
      "sha256": "$meshGenSha",
      "bytes": $meshGenSize,
      "github_url": "$githubBase/scripts/remeshing/generate_method_c_case3_cycle4_mesh.py"
    },
    "mesh_audit_script": {
      "path": "scripts/remeshing/audit_method_c_case3_cycle4_mesh.py",
      "sha256": "$meshAuditScriptSha",
      "bytes": $meshAuditScriptSize,
      "github_url": "$githubBase/scripts/remeshing/audit_method_c_case3_cycle4_mesh.py"
    },
    "state_transfer_script": {
      "path": "scripts/state_transfer/run_case3_cycle4_state_transfer.py",
      "sha256": "$stateTransferSha",
      "bytes": $stateTransferSize,
      "github_url": "$githubBase/scripts/state_transfer/run_case3_cycle4_state_transfer.py"
    },
    "package_unit_tests": {
      "path": "tests/unit/test_method_c_case3_cycle4_package.py",
      "sha256": "$unitTestSha",
      "bytes": $unitTestSize,
      "github_url": "$githubBase/tests/unit/test_method_c_case3_cycle4_package.py"
    }
  },
  "review_resolution_matrix": {
    "GAP-C4P-01": "RESOLVED: Hardcoded Section 4.3 benchmark Gc=0.00228 kN/mm (2.28 J/m^2) in run_case3_cycle4_state_transfer.py and regenerated production deck PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp; verified *UEL PROPERTY cards carry 0.002280; documented Gc timeline across Jobs 1-5 (0.00228, 0.00228, 0.00270, 0.00270, 0.00228) and disclosed conservative effect on crack driving force.",
    "GAP-C4P-02": "RESOLVED: Corrected Section 8 NOTE-01 SHAs to full verified 64-character hex strings: execution tests 7AA1985A875AD92622F8E6082A8B48B0A59242E178418F0E9603754B671B632D, diagnosis report 07D5759CA2B6C0B551E2EAF20CC9C5A1BCAB2A47DF318B445EF28AD2B5A13BF3, diagnosis tests B8EA0E603C210E25534FD22385B5048740E59A1EAA7DD732EE5CFD38291DB8A9.",
    "GAP-C4P-03": "RESOLVED: Corrected Section 2 terminal crack tip coordinate to exact mesh coordinate x=13.1118 mm, y=69.8266 mm.",
    "GAP-C4P-04": "RESOLVED: Corrected Section 8 failing process zone node 21774 coordinate to exact mesh coordinate x=13.284 mm, y=69.780 mm.",
    "GAP-C4P-05": "RESOLVED: Section 9 file manifest updated to exact committed byte sizes and hashes; re-ran Abaqus datacheck on cluster (Exit 0) and affirmed telemetry of exactly 11 warnings, 0 errors (including 1 distorted element); documented 99.53% damage preservation ratio basis relative to reconstructed donor maximum d_max=0.996882.",
    "NOTE-C4P-03": "RESOLVED: Strengthened unit test suite tests/unit/test_method_c_case3_cycle4_package.py with deck Gc=0.00228 assertion, datacheck warning count assertions (11 warnings, 0 errors), and report Section 9 manifest fidelity test; 6/6 tests PASS."
  },
  "requested_review_action": "INDEPENDENT_REVIEW_AND_DECISION: Review the re-issued Cycle-4 Refinement Package (HND-METHOD-C-CASE3-CYCLE4-PREP-002) resolving GAP-C4P-01 through GAP-C4P-05. Verify deck Gc=0.00228 kN/mm, Exit-0 datacheck with 11 warnings / 0 errors / 1 distorted element, verified 64-character NOTE-01 SHAs, exact coordinates, Section 9 byte manifest, and 6/6 unit tests pass. Upon approval, authorize Job-5 submission (M1_MC_C3_JOB5, cumulative 66 -> 67) as the final job of the Fix Option A 5-job budget."
}
"@

if ($CheckOnly) {
    Write-Output "HandoffId: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Report SHA: $reportSha"
    return
}

Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -DryRun:$DryRun
