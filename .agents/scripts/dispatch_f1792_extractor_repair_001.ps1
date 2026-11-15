# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1792_extractor_repair_001.ps1
# Dispatches Task F1792 Mode-I Method C Extractor Runtime and Release Gate Integration Repair
# (HND-F1792-EXTRACTOR-REPAIR-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1792-MODE-I-METHOD-C-EXTRACTOR_RUNTIME_AND_RELEASE_GATE_INTEGRATION_REPAIR"
$handoffId = "HND-F1792-EXTRACTOR-REPAIR-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1792_MODE1_EXTRACTOR_RUNTIME_AND_RELEASE_GATE_INTEGRATION_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesContent = ""
if (Test-Path $rulesPath) {
    $rulesContent = Get-Content -Path $rulesPath -Raw -Encoding UTF8
}

$header = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "HND-F1791-DIAGNOSTIC-QUAL-001",
  "task_id": "$taskId",
  "title": "Task F1792: Mode-I Method C Extractor Runtime and Release Gate Integration Repair",
  "reported_source_commit": "0499bc374 on PRVSTUDENT/adaptive-remeshing-phase-field-thesis",
  "report_path": "docs/validation/F1792_MODE1_EXTRACTOR_RUNTIME_AND_RELEASE_GATE_INTEGRATION_REPORT.md",
  "report_sha256": "CE7776FE7D9AF593AFFFDE5CAACF1E5084C682740B9CCF94395E50C00DF41BC0",
  "extractor_path": "scripts/state_transfer/extract_f1792_observables.py",
  "extractor_sha256": "E5F8DAB17DF38F0AE775679104DF7D0237554318852F1695B1045D665BF094DA",
  "manifest_path": "models/pandey_kumar_mode1/56_f1792_method_c_diagnostic/METHOD_C_F1792_DIAGNOSTIC_AUTHORIZATION.json",
  "manifest_sha256": "06F55C4C7DFD25033104EA86DC877D9C786E1F8478ED38622A54296C113A1121",
  "diagnostic_receipt_path": "models/pandey_kumar_mode1/PK_F1792_EXECUTION_QUALIFICATION_RECEIPT.json",
  "diagnostic_receipt_sha256": "C64F5BD7A8DD6AAE0C2895E8EDAED050D0FDB1FBF4464272DC771791060FB63A",
  "preflight_proof_path": "models/pandey_kumar_mode1/PK_F1792_TECHNICAL_PREFLIGHT_PROOF.json",
  "preflight_proof_sha256": "A4EA1FE59EB7DDAE7398049AE4CBC23E53592599066A6C17D639A56556DA95D4",
  "input_deck_path": "models/pandey_kumar_mode1/56_f1792_method_c_diagnostic/PK_F1792_CASE1_RELEASE_DIAGNOSTIC.inp",
  "input_deck_sha256": "9CCC28DA428D86827891D31C82FF6A8FA0F5605ADA8E8DDDA75280B1C25BF6F6",
  "proposed_pbs_script_path": "models/pandey_kumar_mode1/56_f1792_method_c_diagnostic/submit_f1792_case1_diagnostic.pbs",
  "proposed_pbs_script_sha256": "23BE89FA061FD30CFF25809CA2236D705FED46BEADDC1F2651D421A30CC7B591",
  "test_suite_path": "tests/unit/test_f1792_observable_extractor.py",
  "test_suite_sha256": "6CA2F60B27A43BAD1C5EDE438205C69C86D87CBCE904909DF0B6597A019B92A9",
  "frozen_shared_framework_sha256": "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
  "frozen_production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "cumulative_pbs_submissions": 35,
  "new_pbs_submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "diagnostic_verdict": "QUALIFIED_READY_FOR_EXECUTION_AUTHORIZATION",
  "repaired_components_summary": {
    "abaqus_python_runtime": "submit_f1792_case1_diagnostic.pbs explicitly invokes 'abaqus python extract_f1792_observables.py'. Cluster environment verified via guarded SSH: /cluster/application/abaqus/2023/Commands/abaqus python confirmed native odbAccess import with Exit 0.",
    "step1_dependent_dof_resolution": "In scripts/state_transfer/mode1_state_transfer_engine.py, omitted direct DOF 2 boundary cards for the 98 nodes of N_TOP in Step 1. Vertical displacement is governed identically by *EQUATION (2, N_TOP, 2, 1.0, N_RP, 2, -1.0) and N_RP = 0.0050 mm without constraint conflict. WarnNodeBCInactiveDof2 completely eliminated: local Abaqus 2024 pre.exe datacheck Exit 0 (0 errors, 49791 elements, 16643 nodes in 3.0s); cluster Intel Fortran 2021.13 + Abaqus 2023 standard datacheck Exit 0 (ANALYSIS DATACHECK COMPLETE in 10s).",
    "strict_increment_matching": "parse_energy_csv(), parse_reaction_force_dat(), and parse_residual_norm_msg() strictly require Step 2 Increment 1. All fallbacks to other increments or last row removed.",
    "reaction_force_coherent_units": "parse_reaction_force_dat() detects coherent unit scale in mm-kN-s system; converts raw force in [0.05, 10.0] kN to N (*1000.0) against donor 653.0886 N; flags unphysical forces < 50 N or > 5000 N.",
    "residual_norm_separation": "parse_residual_norm_msg() formally separates initial out-of-balance residual norm (Iteration 1 upon release) from final converged Newton residual, evaluating both against Gate C1 threshold <= 1.0e-3.",
    "complete_nodal_coverage": "extract_damage_from_odb() enforces complete 16,642-node coverage in both frames. Rejects frame-zero substitution (requires incrementNumber == 1). Explicitly labels UEL integration-point history as unavailable in ODB (offline continuous quadrature proved min H = 1.579e-9 >= 0).",
    "guarded_controller_qualification": "Staged models/pandey_kumar_mode1/56_f1792_method_c_diagnostic/ with METHOD_C_F1792_DIAGNOSTIC_AUTHORIZATION.json. Invoke-Mode1Execution.ps1 -VerifyOnly and -StopAfterPreflight passed Exit 0 with zero warnings, generating PK_F1792_TECHNICAL_PREFLIGHT_PROOF.json.",
    "automated_verification": "Standalone unit test tests/unit/test_f1792_observable_extractor.py 10/10 PASS in 0.49s; multi-task regression suite (F1780-F1792) 67/67 PASS in 20.71s."
  },
  "proposed_pbs_experiment": "Requests authorization for exactly ONE bounded physical diagnostic solve (Job 36 overall, F1792_C1_DIAG): 1 CPU, 8 GB, 1.0 hour, entry_imfdfkmq, submitted via Invoke-Mode1Execution.ps1 with once-only accounting. Exactly 0 jobs consumed under F1792; cumulative preserved at 35."
}

================================================================================
F1792 REPAIR & EXECUTION QUALIFICATION REPORT
================================================================================
"@

$prompt = $header + "`n`n" + $reportContent + "`n`n" + "================================================================================`n" + "CANONICAL BRIDGE RULES`n" + "================================================================================`n" + $rulesContent

if ($CheckOnly) {
    Write-Output "=== F1792 PROMPT INTEGRITY CHECK ==="
    Write-Output "Handoff ID: $handoffId"
    Write-Output "Task ID: $taskId"
    Write-Output "Report Path: $reportPath"
    Write-Output "Prompt Length: $($prompt.Length) characters"
    Write-Output "First 2 lines:"
    ($prompt -split "`n")[0..1] | ForEach-Object { Write-Output "  $_" }
    return
}

Write-Output "Publishing Task F1792 review request across OpenClaw PAD Bridge..."
Invoke-ChatGPTBridge -Prompt $prompt -CorrelationId $handoffId
Write-Output "Bridge request published successfully under ID: $handoffId"
