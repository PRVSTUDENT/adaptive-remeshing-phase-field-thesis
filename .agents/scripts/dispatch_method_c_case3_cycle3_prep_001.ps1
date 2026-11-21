# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_cycle3_prep_001.ps1
# Dispatches Method C Case 3: Cycle-3 Refinement Package Preparation
# (HND-METHOD-C-CASE3-CYCLE3-PREP-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE"
$handoffId = "HND-METHOD-C-CASE3-CYCLE3-PREP-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-JOB3-DIAG-002"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md"
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

$donorPath = Join-Path $caseDir "donor_case3_cycle2_state.json"
$donorSha = (Get-FileHash -Path $donorPath -Algorithm SHA256).Hash.ToUpper()
$donorSize = (Get-Item $donorPath).Length

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()
$meshSize = (Get-Item $meshPath).Length

$auditPath = Join-Path $caseDir "method_c_case3_cycle3_mesh_audit.json"
$auditSha = (Get-FileHash -Path $auditPath -Algorithm SHA256).Hash.ToUpper()
$auditSize = (Get-Item $auditPath).Length

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()
$deckSize = (Get-Item $deckPath).Length

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_TRANSFER_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()
$receiptSize = (Get-Item $receiptPath).Length

$submitPbsPath = Join-Path $caseDir "submit_case3_cycle3_job4.pbs"
$submitPbsSha = (Get-FileHash -Path $submitPbsPath -Algorithm SHA256).Hash.ToUpper()
$submitPbsSize = (Get-Item $submitPbsPath).Length

$datacheckShPath = Join-Path $caseDir "run_case3_cycle3_datacheck.sh"
$datacheckShSha = (Get-FileHash -Path $datacheckShPath -Algorithm SHA256).Hash.ToUpper()
$datacheckShSize = (Get-Item $datacheckShPath).Length

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()
$uelSize = (Get-Item $uelPath).Length

$meshGenPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\generate_method_c_case3_cycle3_mesh.py"
$meshGenSha = (Get-FileHash -Path $meshGenPath -Algorithm SHA256).Hash.ToUpper()
$meshGenSize = (Get-Item $meshGenPath).Length

$meshAuditScriptPath = Join-Path $PSScriptRoot "..\..\scripts\remeshing\audit_method_c_case3_cycle3_mesh.py"
$meshAuditScriptSha = (Get-FileHash -Path $meshAuditScriptPath -Algorithm SHA256).Hash.ToUpper()
$meshAuditScriptSize = (Get-Item $meshAuditScriptPath).Length

$stateTransferPath = Join-Path $PSScriptRoot "..\..\scripts\state_transfer\run_case3_cycle3_state_transfer.py"
$stateTransferSha = (Get-FileHash -Path $stateTransferPath -Algorithm SHA256).Hash.ToUpper()
$stateTransferSize = (Get-Item $stateTransferPath).Length

$unitTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_cycle3_package.py"
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
  "title": "Method C Case 3: Cycle-3 Refinement Package Preparation",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_cycle3_refinement_package",
    "numerical_uncertainty": "Can the Cycle-3 adaptive refinement package transition from the Job-3 terminal state (Increment 28, u2=0.056073 mm, RF2=3.9475 kN, d_max=0.999750, crack tip x=12.5215 mm) by extending the refinement corridor to the central hole perimeter at x=26.5 mm and beyond along the crack path, preserving finite element quality gates (min det(J) > 0, quad >= 85%, AR <= 2.5), state transfer fidelity (non-negative H, zero healing), and 3-layer UEL syntax with dt_min=1e-14 and line search without consuming PBS jobs?",
    "expected_numerical_result": "Cycle-3 refinement package prepared and fully verified under HND-METHOD-C-CASE3-CYCLE3-PREP-001: authentic Job-3 donor terminal state ingested; PK_METHOD_C_CASE3_CYCLE3_PHYS.inp with 61,688 elements (97.16% quads, min det(J)=6.685e-4 > 0, AR=1.267 <= 2.5, all gates PASS); measured forward crack path element-size distribution median h=0.1240 mm <= l0/2=0.1425 mm; state transfer via isoparametric_gp_transfer.py with convex_clamp preserving non-negativity H_min=1.112e-11 MPa >= 0 and zero healing d_max=0.989946; 3-layer coupled deck PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp with 185,064 elements and verified UEL syntax from start (PROPERTIES=6, VARIABLES=18, UNSYMM; U1/U3 data 3, U2/U4 data 1, 2); mitigations dt_min=1e-14 in both steps, line search data line 4, CONST_HOLD, and TYPE=SOLUTION initial conditions; cluster datacheck passed Exit 0; stated explicit incremental remeshing snap-through strategy; 4/4 dedicated unit tests PASS (19/19 Case 3 suite PASS); 0 new PBS jobs consumed, cumulative 65 strictly preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "package_report": {
      "path": "docs/validation/METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md",
      "sha256": "$reportSha",
      "bytes": $reportSize,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md"
    },
    "donor_state": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle2_state.json",
      "sha256": "$donorSha",
      "bytes": $donorSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/donor_case3_cycle2_state.json"
    },
    "adapted_physical_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp",
      "sha256": "$meshSha",
      "bytes": $meshSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"
    },
    "mesh_quality_audit": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle3_mesh_audit.json",
      "sha256": "$auditSha",
      "bytes": $auditSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/method_c_case3_cycle3_mesh_audit.json"
    },
    "state_transfer_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_TRANSFER_RECEIPT.json",
      "sha256": "$receiptSha",
      "bytes": $receiptSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_TRANSFER_RECEIPT.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp",
      "sha256": "$deckSha",
      "bytes": $deckSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp"
    },
    "submit_pbs": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle3_job4.pbs",
      "sha256": "$submitPbsSha",
      "bytes": $submitPbsSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/submit_case3_cycle3_job4.pbs"
    },
    "datacheck_script": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle3_datacheck.sh",
      "sha256": "$datacheckShSha",
      "bytes": $datacheckShSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/run_case3_cycle3_datacheck.sh"
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "bytes": $uelSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "mesh_generator_script": {
      "path": "scripts/remeshing/generate_method_c_case3_cycle3_mesh.py",
      "sha256": "$meshGenSha",
      "bytes": $meshGenSize,
      "github_url": "$githubBase/scripts/remeshing/generate_method_c_case3_cycle3_mesh.py"
    },
    "mesh_audit_script": {
      "path": "scripts/remeshing/audit_method_c_case3_cycle3_mesh.py",
      "sha256": "$meshAuditScriptSha",
      "bytes": $meshAuditScriptSize,
      "github_url": "$githubBase/scripts/remeshing/audit_method_c_case3_cycle3_mesh.py"
    },
    "state_transfer_script": {
      "path": "scripts/state_transfer/run_case3_cycle3_state_transfer.py",
      "sha256": "$stateTransferSha",
      "bytes": $stateTransferSize,
      "github_url": "$githubBase/scripts/state_transfer/run_case3_cycle3_state_transfer.py"
    },
    "unit_tests": {
      "path": "tests/unit/test_method_c_case3_cycle3_package.py",
      "sha256": "$unitTestSha",
      "bytes": $unitTestSize,
      "github_url": "$githubBase/tests/unit/test_method_c_case3_cycle3_package.py"
    }
  },
  "review_instructions": "Verify that all 13 artifacts are present and their SHA256 hashes and sizes match this manifest at the artifact_commit; verify that the Job-3 terminal donor state is correctly extracted and preserved; verify that the Cycle-3 adapted physical mesh satisfies all 3 FE quality gates (min det(J) > 0, quad fraction >= 85%, aspect ratio <= 2.5) and that the corridor element-size distribution resolves l0/2=0.1425 mm on the forward crack path extending to the central hole perimeter at x=26.5 mm and beyond; verify that state and history transfer via isoparametric_gp_transfer.py with convex_clamp satisfies non-negativity (H >= 0), phase bounds (0 <= d <= 1), and non-healing (zero healing); verify that the 3-layer production deck PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp (185,064 elements) contains verified UEL cards from start (PROPERTIES=6, VARIABLES=18, UNSYMM; U1/U3 data 3, U2/U4 data 1, 2), dt_min=1.0E-14 in both steps, *CONTROLS, PARAMETERS=LINE SEARCH line 4, Step-1 hold u2=0.056073 mm (CONST_HOLD), and TYPE=SOLUTION initial conditions; verify that cluster technical datacheck passed Exit 0; verify that the snap-through strategy is explicitly stated (relying on incremental remeshing as adaptive transition trigger); verify that exactly 0 new PBS jobs were consumed and cumulative PBS submissions remain strictly preserved at 65; if all evidence verifies, approve the package to permit Job 4 submission (M1_MC_C3_JOB4, advancing cumulative PBS to 66); maintain MASTER_GOAL_STATUS = OPEN."
}
"@

if ($CheckOnly) {
    Write-Output "CHECK_ONLY: Verification complete. Prompt generated with Handoff ID: $handoffId"
    Write-Output "Artifact commit: $commitSha"
    Write-Output "Report SHA: $reportSha"
    return
}

Write-Output "Dispatching review request $handoffId via Invoke-ChatGPTBridge..."
Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -TaskId $taskId -DryRun:$DryRun
