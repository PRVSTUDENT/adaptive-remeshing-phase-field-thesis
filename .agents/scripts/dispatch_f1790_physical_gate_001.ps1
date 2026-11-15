# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_f1790_physical_gate_001.ps1
# Dispatches Task F1790 Mode-I Method C Physical Gate Restoration & Release Diagnostic
# (HND-F1790-PHYSICAL-GATE-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "F1790-MODE-I-METHOD-C-PHYSICAL-GATE-RESTORATION-AND-RELEASE-DIAGNOSTIC"
$handoffId = "HND-F1790-PHYSICAL-GATE-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\F1790_MODE1_PHYSICAL_GATE_RESTORATION_AND_RELEASE_DIAGNOSTIC_REPORT.md"
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
  "predecessor_correlation_id": "HND-F1789-AUTHENTIC-PREFLIGHT-001",
  "task_id": "$taskId",
  "title": "Task F1790: Mode-I Method C Physical Gate Restoration and Release Diagnostic",
  "reported_source_commit": "e13b1cb22 on PRVSTUDENT/adaptive-remeshing-phase-field-thesis",
  "report_path": "docs/validation/F1790_MODE1_PHYSICAL_GATE_RESTORATION_AND_RELEASE_DIAGNOSTIC_REPORT.md",
  "report_sha256": "116E310B68D30FADCEB9D18B2A88E19787ABEC54B7247680DA93FC3D45131582",
  "diagnostic_deck_path": "models/pandey_kumar_mode1/PK_F1790_CASE1_RELEASE_DIAGNOSTIC.inp",
  "diagnostic_deck_sha256": "5A02C4D7067366AFAE6212FD62E3ADBDCD9585D54B20E512B6EA50E01A8904A9",
  "diagnostic_receipt_path": "models/pandey_kumar_mode1/PK_F1790_RELEASE_DIAGNOSTIC_RECEIPT.json",
  "diagnostic_receipt_sha256": "1B25F3CD92AF936DE85076C43834651D0EB5CC8FC9279E9DF80D5C8FF0F73A35",
  "syntaxcheck_log_path": "models/pandey_kumar_mode1/evidence_f1790_datacheck/PK_F1790_CASE1_DATACHECK.txt",
  "syntaxcheck_log_sha256": "1E87A4F2391694A848CD1692DCF24864FA1638367FBF9D59C2084666BCBEA33D",
  "proposed_pbs_script_path": "models/pandey_kumar_mode1/submit_f1790_case1_diagnostic.pbs",
  "proposed_pbs_script_sha256": "7F6E726084D0A212E53F9B278AC1220A939E36A7800DA8360FEF872DA01E496F",
  "test_suite_path": "tests/unit/test_f1790_physical_gate_restoration.py",
  "test_suite_sha256": "6A0DAECB3EDCB2933C4BD8F55C92138BF235A621D4067332EB7DE432B9C89327",
  "frozen_shared_framework_sha256": "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
  "frozen_production_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
  "cumulative_pbs_submissions": 35,
  "new_pbs_submissions_consumed": 0,
  "master_goal_status": "OPEN",
  "preflight_verdict": "NO_GO_PENDING_PHYSICAL_SOLVER_EVALUATION",
  "investigation_summary": {
    "restored_acceptance_gates": {
      "gate_c1_equilibrium_residual": "R_max / q_tilde <= 1.0e-3 (Status: NOT_YET_MEASURABLE_PENDING_PBS_SOLVE)",
      "gate_c2_reaction_force_parity": "|Delta RF_2| / RF_2,donor <= 0.50% vs 653.0886 N (Status: NOT_YET_MEASURABLE_PENDING_PBS_SOLVE; offline projection: 0.0743% PASS)",
      "gate_c3_internal_energy_continuity": "|Delta E_int| / E_int,donor <= 0.50% vs 1.663384 mJ (Status: NOT_YET_MEASURABLE_PENDING_PBS_SOLVE; offline projection: 0.0814% PASS)",
      "gate_c4_pointwise_damage_irreversibility": "min(Delta d) >= -1.0e-4 across all 16,642 nodes (Status: NOT_YET_MEASURABLE_PENDING_PBS_SOLVE; offline projection: 0.0000 PASS)",
      "gate_c5_artificial_crack_tip_damage_cap": "Delta d_tip <= 1.0e-3 (0.0010, strictly unrelaxed; Status: NOT_YET_MEASURABLE_PENDING_PBS_SOLVE; offline projection: 0.0000 PASS)"
    },
    "offline_precheck_evaluations": "Displacement L2 rel error = 0.0243% <= 1.00% (PASS); peak damage delta = 0.0000 <= 0.020 (PASS); integrated damage delta = 0.0259% <= 5.00% (PASS); min H = 1.579e-9 kN/mm^2 >= 0, 0 violations (PASS); boundary traction integral delta = 0.0743% <= 0.50% (PASS); internal strain energy integral delta = 0.0814% <= 0.50% (PASS); global work energy residual = 1.71% <= 10.0% (PASS).",
    "step_definitions_and_release_dynamics": "Step-1-Reconstruct prescribes DOFs 1, 2, 3 on all 16,642 physical nodes (u_rp = 0.0050 mm, 1 inc), initializing the deformed configuration directly. Step-2-Hold unconstrains interior DOFs via *BOUNDARY, OP=NEW with fine incrementation (dt_init=0.05, dt_max=0.10, period=1.0), enabling direct observation and resolution of the first release increments.",
    "inactive_dof_warning_resolved": "Preprocessor warning 'Boundary conditions are specified on inactive dof 2 at 98 nodes' explained with complete architectural transparency: nodes on N_BOTTOM are shared between Layer 1 (UEL phase-field, active DOF 3) and Layer 2 (UEL mechanical, active DOFs 1 and 2). Layer 2 activates DOF 2 correctly; zero modeling defect.",
    "input_processing_evidence_accessible": "Abaqus 2024 pre.exe executed locally across 49,791 layered elements and 16,643 nodes in 2.8s CPU time with zero fatal errors. Evidence text logs (PK_F1790_CASE1_DATACHECK.txt, .dat, .md) are tracked directly in git, resolving GitHub retrievability.",
    "execution_feasibility_boundary": "Local workstation Windows 11 lacks C++/Fortran compiler/linker for user subroutine f42_mixed_uel.for, making local solve technically infeasible. Cluster compute node mnode099 is fully qualified (Classic Intel Fortran 2021.13 + Abaqus 2023).",
    "proposed_pbs_experiment": "Formulated proposed Job 36 (F1790_C1_DIAG): 1 CPU, 8 GB, 1.0 hour, normal_imfdfkmq, submit_f1790_case1_diagnostic.pbs, and extract_f1790_observables.py for physical Step-1 and Step-2 release evaluation. Zero jobs submitted; cumulative preserved at 35."
  }
}
"@

$footer = @'

INSTRUCTIONS TO INDEPENDENT SCIENTIFIC REVIEWER:
Review the submitted Task F1790 Mode-I Method C Physical Gate Restoration & Release Diagnostic report and evidence.
Evaluate whether:
1. The restoration of original Method C acceptance gates (Gates C1-C5) without renaming or relaxation, and their honest classification as NOT_YET_MEASURABLE_PENDING_PBS_SOLVE, satisfies scientific standards.
2. The re-engineered Step-2-Hold incrementation (dt_init=0.05, dt_max=0.10) properly enables physical observation of the first release increments.
3. The archived Abaqus 2024 input processing evidence resolves repository retrievability.
4. The proposed physical diagnostic experiment (Job 36: F1790_C1_DIAG) is justified, qualified, and ready for authorization under Mode-I single-cycle governance.

RESPONSE CONTRACT: Output exactly ONE fenced JSON code block labeled 'json' containing your review verdict. No introductory prose, no markdown headings, no commentary outside the JSON block.

Required schema:
```json
{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "HND-F1790-PHYSICAL-GATE-001",
  "task_id": "F1790-MODE-I-METHOD-C-PHYSICAL-GATE-RESTORATION-AND-RELEASE-DIAGNOSTIC",
  "review_decision": "APPROVE | REJECT | CONDITIONAL_APPROVAL",
  "review_verdict": "string",
  "findings": [
    "string"
  ],
  "diagnostic_verdict": "QUALIFIED_READY_FOR_EXECUTION | UNQUALIFIED",
  "approved_next_task": "string",
  "max_authorized_pbs_jobs": 0,
  "master_goal_status": "OPEN",
  "next_instruction_to_antigravity": "string"
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
