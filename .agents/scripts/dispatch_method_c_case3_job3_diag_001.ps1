# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_job3_diag_001.ps1
# Dispatches Method C Case 3 Job-3 Diagnosis and Deck Regeneration Disclosure
# (HND-METHOD-C-CASE3-JOB3-DIAG-001) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-JOB3-DIAGNOSIS"
$handoffId = "HND-METHOD-C-CASE3-JOB3-DIAG-001"
$predecessorHandoffId = "HND-METHOD-C-CASE3-JOB3-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md"
if (-not (Test-Path $reportPath)) {
    throw "Report file not found at: $reportPath"
}
$reportContent = Get-Content -Path $reportPath -Raw -Encoding UTF8
$reportSha = (Get-FileHash -Path $reportPath -Algorithm SHA256).Hash.ToUpper()

$rulesPath = Join-Path $PSScriptRoot "bridge_rules.txt"
$rulesSha = (Get-FileHash -Path $rulesPath -Algorithm SHA256).Hash.ToUpper()

$commitSha = (git rev-parse HEAD).Trim()

$caseDir = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\290_method_c_case3"

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()

$summaryPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()

$spatialPath = Join-Path $caseDir "job3_spatial_crack.json"
$spatialSha = (Get-FileHash -Path $spatialPath -Algorithm SHA256).Hash.ToUpper()

$obsPath = Join-Path $caseDir "job3_observables.json"
$obsSha = (Get-FileHash -Path $obsPath -Algorithm SHA256).Hash.ToUpper()

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()

$diagTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job3_diagnosis.py"
$diagTestSha = (Get-FileHash -Path $diagTestPath -Algorithm SHA256).Hash.ToUpper()

$execTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job3_execution.py"
$execTestSha = (Get-FileHash -Path $execTestPath -Algorithm SHA256).Hash.ToUpper()

$execReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md"
$execReportSha = (Get-FileHash -Path $execReportPath -Algorithm SHA256).Hash.ToUpper()

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()

$msgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg"
$msgSha = (Get-FileHash -Path $msgPath -Algorithm SHA256).Hash.ToUpper()

$datPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat"
$datSha = (Get-FileHash -Path $datPath -Algorithm SHA256).Hash.ToUpper()

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log"
$logSha = (Get-FileHash -Path $logPath -Algorithm SHA256).Hash.ToUpper()

$csvPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv"
$csvSha = (Get-FileHash -Path $csvPath -Algorithm SHA256).Hash.ToUpper()

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Case 3: Job-3 Diagnosis, Deck Regeneration Disclosure, and Evidence Reconciliation",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job3_diagnosis",
    "numerical_uncertainty": "Can the preflight deck regeneration from candidate 8DDE4D8B to executed 1D72A981 be verified as strictly a 23-line syntax repair preserving 100% bitwise parity across all 746,928 transferred SVARs, and can all Job-2 comparison values, committed artifact sizes, walltime measurements, and dual forward crack advance baselines be reconciled without requiring any new PBS simulation?",
    "expected_numerical_result": "All review gaps from HND-METHOD-C-CASE3-JOB3-001 resolved with verified repository evidence. (1) Preflight deck regeneration disclosed: approved candidate 8DDE4D8B (17,373,879 B) had defective *USER ELEMENT cards (all DOFs 1, 2 with IPROPERTY=1, no UNSYMM); corrected during preflight datacheck via run_case3_cycle2_state_transfer.py to restore Job-2 working syntax (U1/U3 phase DOF 3, U2/U4 disp DOFs 1, 2, UNSYMM on all 4 cards, IPROPERTY=1 removed) and regenerated to executed deck 1D72A981 (17,373,692 B); line diff strictly 23 header lines; all 746,928 initial-condition SVAR values under *INITIAL CONDITIONS, TYPE=SOLUTION 100% bitwise identical. (2) Reconciled Job-2 comparison values: Step-1 energy continuity -0.215% fracture / -0.385% total, initial fracture energy 0.00172721 kN*mm, peak structural load 4.0498816 kN at u2=0.0524271 mm. (3) Corrected artifact sizes to exact committed disk bytes (spatial 33,824 B, observables 3,227 B, receipt 7,398 B, summary 2,643 B, UEL 29,722 B). (4) Relabeled terminal frame as Increment 28 converged state (Increment 29 aborted cutback to dt_min=1.0e-14); clarified peak load 4.101037 kN ODB vs 4.1009829 kN .dat; disambiguated PBS job span 4,602s vs solver wallclock 4,268s and CPU 2,918s with UTC/CET timestamps; harmonized dual forward advance baselines (+2.3686 mm donor vs +2.3649 mm post-hold) and classified Step-1 damage growth as GROWTH_UNDER_HOLD. Complete Case 3 unit tests 36/36 PASS (100%). Strictly 0 new PBS jobs consumed; cumulative 65 preserved; MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "diagnosis_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md",
      "sha256": "$reportSha",
      "size_bytes": 12472,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md"
    },
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md",
      "sha256": "$execReportSha",
      "size_bytes": 18952,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json",
      "sha256": "$receiptSha",
      "size_bytes": 7398,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json",
      "job_id": "1424778.mmaster02",
      "exit_code": 1,
      "status": "CUTBACK_TERMINATION",
      "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
      "terminal_frame_label": "Increment 28 (terminal converged state; Increment 29 attempted 3 cutbacks down to dt_min=1.0e-14 and aborted)",
      "pbs_job_span_walltime_s": 4602.0,
      "solver_wallclock_s": 4268.0,
      "solver_cpu_s": 2918.0,
      "timestamps_utc": "2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z",
      "timestamps_cet": "2026-11-21 00:09:47 CET to 2026-11-21 01:26:29 CET",
      "total_increments": 29,
      "step1_increments": 1,
      "step2_increments": 28,
      "step1_init_RF2_kN": 4.0484387,
      "step1_donor_RF2_kN": 4.0332960,
      "step1_init_force_continuity_delta_pct": 0.375442,
      "step1_init_force_continuity_pass": true,
      "step1_init_E_frac_kNmm": 0.0034895,
      "step1_donor_E_frac_kNmm": 0.0034562,
      "step1_init_energy_continuity_delta_pct": 0.963486,
      "step1_init_energy_continuity_pass": true,
      "step1_damage_growth_classification": "GROWTH_UNDER_HOLD",
      "peak_RF2_kN": 4.101037,
      "peak_RF2_dat_kN": 4.1009829,
      "u2_at_peak_RF2_mm": 0.053284,
      "terminal_RF2_kN": 3.947500,
      "terminal_u2_mm": 0.056073,
      "post_peak_softening_demonstrated": true,
      "load_drop_from_peak_pct": -3.743858,
      "inc11_milestone_surpassed": true,
      "smallest_converged_dt": 6.728e-14,
      "donor_tip_x_mm_d095": 10.1529,
      "step1_tip_x_mm_d095": 10.1566,
      "terminal_tip_x_mm_d095": 12.5215,
      "donor_tip_baseline_forward_advance_mm_d095": 2.3686,
      "post_hold_baseline_forward_advance_mm_d095": 2.3649,
      "step2_forward_advance_mm_d095": 2.3649,
      "final_crack_extension_mm_d095": 2.5215,
      "final_crack_tip_x_mm_d080": 12.7932,
      "final_crack_tip_x_mm_d050": 13.0767,
      "fully_damaged_elements_d095_terminal": 37,
      "process_zone_elements_d050_terminal": 170,
      "crack_propagated_spatially": true,
      "crack_heading_toward_hole": true,
      "initial_fracture_energy_kNmm": 0.0034895,
      "final_fracture_energy_kNmm": 0.013756,
      "fracture_energy_growth_pct": 294.2112,
      "peak_elastic_strain_energy_kNmm": 0.113310,
      "terminal_elastic_strain_energy_kNmm": 0.110674,
      "strain_energy_release_demonstrated": true,
      "monotonic_fracture_energy_growth": true,
      "terminal_peak_damage": 0.999750,
      "zero_healing_verified": true,
      "deck_regeneration": {
        "approved_deck_sha256": "8DDE4D8B4D441CEFFCE55979FBFB4DC5C5C0F6662446A310CE7D2791C24D338C",
        "approved_deck_size_bytes": 17373879,
        "executed_deck_sha256": "1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C",
        "executed_deck_size_bytes": 17373692,
        "deck_status": "REGENERATED_PREFLIGHT_SYNTAX_REPAIR"
      }
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json",
      "sha256": "$summarySha",
      "size_bytes": 2643,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json"
    },
    "spatial_crack_metrics": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json",
      "sha256": "$spatialSha",
      "size_bytes": 33824,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json"
    },
    "frame_observables": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json",
      "sha256": "$obsSha",
      "size_bytes": 3227,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp",
      "sha256": "$deckSha",
      "size_bytes": 17373692,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp",
      "deck_status": "REGENERATED_PREFLIGHT_SYNTAX_REPAIR",
      "approved_deck_sha256": "8DDE4D8B4D441CEFFCE55979FBFB4DC5C5C0F6662446A310CE7D2791C24D338C",
      "executed_deck_sha256": "1D72A98120AAFF2EAC657779C6F3477CDCCF3B22C3528E6CF2BB0E233EE4BC9C",
      "header_diff_lines": 23,
      "transferred_svar_records": 746928,
      "transferred_svar_parity_pct": 100.0,
      "layered_elements": 117936
    },
    "adapted_receiver_mesh": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "sha256": "$meshSha",
      "size_bytes": 3090607,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "physical_elements": 39312,
      "quad_fraction_pct": 97.43,
      "nodes": 39034
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "size_bytes": 29722,
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "solver_text_outputs": {
      "sta_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta",
        "sha256": "$staSha",
        "size_bytes": 4183,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta"
      },
      "msg_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg",
        "sha256": "$msgSha",
        "size_bytes": 250303,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg"
      },
      "dat_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat",
        "sha256": "$datSha",
        "size_bytes": 39663,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat"
      },
      "pbs_execution_log": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log",
        "sha256": "$logSha",
        "size_bytes": 2775,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log"
      },
      "uel_energy_balance_csv": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv",
        "sha256": "$csvSha",
        "size_bytes": 2891,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv"
      }
    },
    "diagnosis_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job3_diagnosis.py",
      "sha256": "$diagTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job3_diagnosis.py",
      "tests_passed": 6,
      "total_tests": 6
    },
    "execution_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job3_execution.py",
      "sha256": "$execTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job3_execution.py",
      "tests_passed": 5,
      "total_tests": 5,
      "case3_test_suite_passed": 36,
      "case3_test_suite_total": 36
    }
  },
  "review_checklist_and_gaps": {
    "gap_mc_c3j3_01_deck_regeneration_disclosure": "RESOLVED: Disclosed preflight deck regeneration from approved candidate 8DDE4D8B (17,373,879 B) to executed 1D72A981 (17,373,692 B). Explained that candidate UEL card headers had defective DOFs '1, 2' on all 4 types with IPROPERTY=1 and no UNSYMM; corrected during preflight datacheck via run_case3_cycle2_state_transfer.py to restore Job-2 working syntax (U1/U3 phase DOF 3, U2/U4 disp DOFs 1, 2, UNSYMM on all 4 cards, IPROPERTY=1 removed). Confirmed diff is strictly 23 header lines; all 746,928 initial-condition SVAR values under *INITIAL CONDITIONS, TYPE=SOLUTION are 100% bitwise identical. Formally recorded as REGENERATED_PREFLIGHT_SYNTAX_REPAIR.",
    "gap_mc_c3j3_02_job2_comparison_reconciliation": "RESOLVED: Updated Section 2 comparison table in execution report with authentic committed Job-2 values: Step-1 energy continuity -0.215% fracture / -0.385% total vs Job-1 Step 1 (replaces +0.98% placeholder); initial fracture energy 0.00172721 kN*mm (replaces 0.00342); peak structural load 4.0498816 kN at u2=0.0524271 mm (replaces 4.0441 kN at 0.05220 mm). Defined which energy each continuity figure refers to.",
    "note_mc_c3j3_01_file_size_reconciliation": "RESOLVED: Corrected all artifact sizes across execution report, diagnosis report, receipt, and summary to exact committed filesystem byte counts verified via Get-Item (spatial crack 33,824 B, observables 3,227 B, receipt 7,398 B, summary 2,643 B, UEL 29,722 B).",
    "note_mc_c3j3_02_terminal_frame_and_peak_load": "RESOLVED: Relabeled terminal frame as Increment 28 converged state (Increment 29 attempted 3 cutbacks down to dt_min=1.0e-14 and was aborted by Abaqus). Clarified that peak reaction force 4.101037 kN is ODB field output; printed summary in .dat reports 4.1009829 kN.",
    "note_mc_c3j3_04_walltime_and_timestamps": "RESOLVED: Disambiguated PBS job span (4,602s) vs Abaqus solver wallclock (4,268s) and CPU time (2,918s). Clarified UTC timestamps (2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z) and CET timestamps (2026-11-21 00:09:47 CET to 2026-11-21 01:26:29 CET).",
    "note_mc_c3j3_05_forward_advance_baselines": "RESOLVED: Defined dual forward advance baselines: +2.3686 mm past donor tip (x = 10.1529 mm) vs +2.3649 mm past post-hold tip (x = 10.1566 mm). Classified Step-1 damage growth under fixed hold (+0.0037 mm, d_max 0.976822 -> 0.977715, +0.09%) as GROWTH_UNDER_HOLD.",
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
