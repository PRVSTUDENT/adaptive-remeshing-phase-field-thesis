# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_cycle3_prep_002.ps1
# Dispatches Method C Case 3: Cycle-3 Refinement Package Re-Issue
# (HND-METHOD-C-CASE3-CYCLE3-PREP-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE"
$handoffId = "HND-METHOD-C-CASE3-CYCLE3-PREP-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-CYCLE3-PREP-001"

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

$datacheckDatPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.dat"
$datacheckDatSha = (Get-FileHash -Path $datacheckDatPath -Algorithm SHA256).Hash.ToUpper()
$datacheckDatSize = (Get-Item $datacheckDatPath).Length

$datacheckMsgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.msg"
$datacheckMsgSha = (Get-FileHash -Path $datacheckMsgPath -Algorithm SHA256).Hash.ToUpper()
$datacheckMsgSize = (Get-Item $datacheckMsgPath).Length

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
  "title": "Method C Case 3: Cycle-3 Refinement Package Preparation (Re-Issue 2)",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_cycle3_refinement_package",
    "numerical_uncertainty": "Can the Cycle-3 refinement package be re-issued with the datacheck outputs committed and verifiable (Exit 0, dt_min line, completion marker), the §8 inventory corrected to the manifest values, and the damage-preservation gloss corrected to 99.69%, with 0 new PBS jobs consumed?",
    "expected_numerical_result": "Package re-issue HND-METHOD-C-CASE3-CYCLE3-PREP-002 with committed DC.dat/DC.msg matching the stated SHAs, corrected §8 sizes/SHAs, corrected 99.69% preservation figure, and a test suite that passes against the corrected tree; exactly 0 new PBS jobs consumed (cumulative 65 preserved); MASTER_GOAL_STATUS = OPEN.",
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
    "datacheck_dat": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.dat",
      "sha256": "$datacheckDatSha",
      "bytes": $datacheckDatSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.dat"
    },
    "datacheck_msg": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.msg",
      "sha256": "$datacheckMsgSha",
      "bytes": $datacheckMsgSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.msg"
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
  "review_checklist_and_gaps": {
    "gap_mc_c3c3p_01_datacheck_outputs_committed": "RESOLVED: Both technical datacheck outputs (PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_DC.dat [13,235 B, SHA F7FF2AC12B14388A40D82B1E657940B8A3FD3198BEA2138E9D7392D0F43E0360] and .msg [1,423 B, SHA BCBF5CA27E608672DBCAA29C3D3271CA50927D1F0793E4C94D72EF23283621BD]) are committed directly to models/pandey_kumar_mode1/290_method_c_case3/ via git add -f, verifying Exit 0, the dt_min=1.000E-14 line, and JOB TIME SUMMARY completion marker on a clean clone.",
    "gap_mc_c3c3p_02_report_inventory_table_corrected": "RESOLVED: §8 artifact inventory table in METHOD_C_CASE3_CYCLE3_PREPARATION_REPORT.md is corrected to manifest values: generator script 9,042 B / SHA 09767838..., audit script 7,628 B / SHA 1F2CD3BC..., transfer script 33,942 B / SHA 4B936354...; self-referential report entry omitted.",
    "gap_mc_c3c3p_03_damage_preservation_gloss_corrected": "RESOLVED: Corrected damage preservation gloss in §1.3 and §4 to 99.69% (ratio 0.99686; receiver 0.989946 vs donor 0.993061) and plainly stated the >= 0.90x gate threshold.",
    "note_mc_c3c3p_02_job3_ledger_status_updated": "RESOLVED: Updated project_coordination/HPC_JOB_LEDGER.csv for Job 3 (1424778.mmaster02) from SUBMITTED to CUTBACK_TERMINATED.",
    "accounting_audit": "Strictly 0 new PBS jobs consumed; cumulative PBS submissions remain exactly 65 (under Fix Option A 5-job allocation 62-67). Bitwise frozen UEL CE8D5EDC... maintained.",
    "master_goal_status": "OPEN"
  }
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
