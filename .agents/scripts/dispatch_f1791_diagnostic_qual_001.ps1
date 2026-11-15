# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1791_diagnostic_qual_001.ps1
# Dispatches Task F1791 Mode-I Method C Diagnostic Observability Repair and Execution Qualification
# (HND-F1791-DIAGNOSTIC-QUAL-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1791-MODE-I-METHOD-C-DIAGNOSTIC_OBSERVABILITY_REPAIR_AND_EXECUTION_QUALIFICATION"
$handoffId = "HND-F1791-DIAGNOSTIC-QUAL-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1791_MODE1_DIAGNOSTIC_OBSERVABILITY_AND_EXECUTION_QUALIFICATION_REPORT.md"
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
  "predecessor_correlation_id": "HND-F1790-PHYSICAL-GATE-001",
  "task_id": "$taskId",
  "title": "Task F1791: Mode-I Method C Diagnostic Observability Repair and Execution Qualification",
  "reported_source_commit": "8476e4370 on PRVSTUDENT/adaptive-remeshing-phase-field-thesis",
  "report_path": "docs/validation/F1791_MODE1_DIAGNOSTIC_OBSERVABILITY_AND_EXECUTION_QUALIFICATION_REPORT.md",
  "report_sha256": "9C1C5721B6647EACCE8EFDE2C161FEABEDCDE057F6554788D0352999B253C456",
  "extractor_path": "scripts/state_transfer/extract_f1791_observables.py",
  "extractor_sha256": "BAC708DFF28B9AFDE2725E3C513FBCF2A6B4FC8800C849E710D53BDEB91ED6E3",
  "manifest_path": "models/pandey_kumar_mode1/55_f1791_method_c_diagnostic/METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json",
  "manifest_sha256": "5E89931A2430335FC96A03A6BF35561FD3A1EEDF86EAAB082463A775617ADCA8",
  "diagnostic_receipt_path": "models/pandey_kumar_mode1/PK_F1791_EXECUTION_QUALIFICATION_RECEIPT.json",
  "diagnostic_receipt_sha256": "DE5A6129CE8DF9B9A4BEB6D9C42BF3216D6491DD2A8D05C49366DA831D5FE460",
  "proposed_pbs_script_path": "models/pandey_kumar_mode1/submit_f1791_case1_diagnostic.pbs",
  "proposed_pbs_script_sha256": "0E29DF5A8C982324812D690C6E4F76DCFBFDF1BE8C63B1551BCCF09BDAA0C4AB",
  "test_suite_path": "tests/unit/test_f1791_observable_extractor.py",
  "test_suite_sha256": "5B517C95841F71D52AF44A1D27A7565FE22F6DCFC73285572A63F3FF8886692E",
  "frozen_shared_framework_sha256": "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
  "frozen_production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "cumulative_pbs_submissions": 35,
  "new_pbs_submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "preflight_verdict": "EXECUTION_ROUTE_QUALIFIED_READY_FOR_SINGLE_SOLVE_AUTHORIZATION",
  "investigation_summary": {
    "observable_extractor_repaired": "Implemented extract_f1791_observables.py with dynamic spatial crack-tip resolution identifying Node 209 at (0.500000, 0.500000) mm (0.000000 mm distance) and crack-tip cluster nodes (2844, 16591, 2914, 2915, 3032, 3156), eliminating historical hardcoded Node 14403 assumption. Authentic ODB field extraction for nodal DOF 3 damage implemented across Step 1 and Step 2 increments. Strict fail-closed error handling verified: missing files or fields emit NOT_MEASURABLE / FAIL, never PASS.",
    "warning_and_connectivity_audit": "WarnNodeBCInactiveDof2 on 98 nodes conclusively identified as N_TOP (y = 1.0 mm). In Step 1, redundant individual Dirichlet specification conflicted with *EQUATION (2, N_TOP, 2, 1.0, N_RP, 2, -1.0) which designates DOF 2 as dependent. In Step 2 (*BOUNDARY, OP=NEW), direct DOF 2 constraint on N_TOP is omitted and governed solely via N_RP, resolving the conflict. All 98 nodes verified active in Layer 2 (mechanical) and Layer 3 (companion). f42_mixed_uel.for writes uel_energy_balance.csv directly during solver iterations, guaranteeing valid energy observations despite *ELEMENT OUTPUT warnings.",
    "pbs_wrapper_guarded_execution": "submit_f1791_case1_diagnostic.pbs repaired with set +e / set -e error trap around solver call, capturing EXIT_CODE, routing to #PBS -q entry_imfdfkmq, and calling extractor on failure branch to preserve forensic failure diagnostics.",
    "execution_route_qualification": "Package staged under models/pandey_kumar_mode1/55_f1791_method_c_diagnostic/ with manifest METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json, passing Invoke-Mode1Execution.ps1 -DryRun Exit 0 with zero warnings and once-only accounting.",
    "restored_acceptance_gates": {
      "gate_c1_equilibrium_residual": "R_max / max(q_tilde, 1.0e-6) <= 1.0e-3 (Status: NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE)",
      "gate_c2_reaction_force_parity": "|Delta RF_2| / RF_2,donor <= 0.50% vs 653.0886 N (Status: NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE)",
      "gate_c3_internal_energy_continuity": "|Delta E_int| / E_int,donor <= 0.50% vs 1.663384 mJ (Status: NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE)",
      "gate_c4_pointwise_damage_irreversibility": "min(Delta d) >= -1.0e-4 across all 16,642 nodes (Status: NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE)",
      "gate_c5_artificial_crack_tip_damage_cap": "Delta d_tip <= 1.0e-3 (0.0010, strictly unrelaxed) at Node 209 (Status: NOT_YET_MEASURABLE_PENDING_PHYSICAL_SOLVE)"
    },
    "proposed_pbs_experiment": "Requests authorization for exactly ONE bounded physical diagnostic solve (Job 36 overall, F1791_C1_DIAG): 1 CPU, 8 GB, 1.0 hour, entry_imfdfkmq, submitted via Invoke-Mode1Execution.ps1 with once-only accounting. Exactly 0 jobs consumed under F1791; cumulative preserved at 35."
  }
}
"@

$footer = @'

INSTRUCTIONS TO INDEPENDENT SCIENTIFIC REVIEWER:
Review the submitted Task F1791 Mode-I Method C Diagnostic Observability Repair and Execution Qualification report and evidence.
Evaluate whether:
1. The repaired observable extractor (extract_f1791_observables.py) with dynamic spatial crack-tip resolution (Node 209 at (0.5, 0.5) mm) and authentic ODB extraction satisfies rigorous scientific and numerical requirements.
2. The strict fail-closed error handling (emitting NOT_MEASURABLE on missing files/fields) and negative regression tests conclusively prevent false-positive gate passes.
3. The forensic audit of WarnNodeBCInactiveDof2 on N_TOP (98 nodes) and confirmation of UEL energy CSV generation resolves preprocessor warning concerns.
4. The repaired PBS wrapper (set +e error trap, #PBS -q entry_imfdfkmq) and Invoke-Mode1Execution.ps1 manifest qualification fully establish readiness for execution.
5. You AUTHORIZE the submission of exactly ONE bounded physical diagnostic experiment (Job 36: F1791_C1_DIAG) via scripts/hpc/Invoke-Mode1Execution.ps1.

RESPONSE CONTRACT: Output exactly ONE fenced JSON code block labeled 'json' containing your review verdict. No introductory prose, no markdown headings, no commentary outside the JSON block.

Required schema:
```json
{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-F1791-DIAGNOSTIC-QUAL-001",
  "task_id": "F1791-MODE-I-METHOD-C-DIAGNOSTIC_OBSERVABILITY_REPAIR_AND_EXECUTION_QUALIFICATION",
  "review_decision": "APPROVE | REJECT | CONDITIONAL_APPROVAL",
  "review_verdict": "string",
  "findings": [
    "string"
  ],
  "diagnostic_verdict": "QUALIFIED_READY_FOR_EXECUTION | UNQUALIFIED",
  "authorized_execution": {
    "job_name": "F1791_C1_DIAG",
    "manifest_path": "models/pandey_kumar_mode1/55_f1791_method_c_diagnostic/METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json",
    "max_authorized_pbs_jobs": 1,
    "submission_command": "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/hpc/Invoke-Mode1Execution.ps1 -ManifestPath models/pandey_kumar_mode1/55_f1791_method_c_diagnostic/METHOD_C_F1791_DIAGNOSTIC_AUTHORIZATION.json"
  },
  "approved_next_task": "string",
  "master_goal_status": "OPEN"
}
```
'@

$prompt = $header + "`r`n`r`n---------------- EVIDENTIARY REPORT ----------------`r`n" + $reportContent + "`r`n-------------- END EVIDENTIARY REPORT --------------`r`n`r`n---------------- BRIDGE CONTROLLER RULES ----------------`r`n" + $rulesContent + "`r`n---------------- END BRIDGE CONTROLLER RULES ----------------`r`n" + $footer

if ($CheckOnly) {
    Write-Host "[CheckOnly] Bridge prompt verified. Header: [BRIDGE_HANDOFF_ID=$handoffId]" -ForegroundColor Green
    Write-Host "[CheckOnly] Length: $($prompt.Length) characters" -ForegroundColor Cyan
    return
}

Write-Host "[Dispatch] Invoking ChatGPT Bridge for $handoffId..." -ForegroundColor Cyan
$response = Invoke-ChatGPTBridge -PromptText $prompt -HandoffId $handoffId -LaunchPad -TimeoutMinutes 40
Write-Host "[Dispatch] Response received:" -ForegroundColor Green
Write-Host $response
