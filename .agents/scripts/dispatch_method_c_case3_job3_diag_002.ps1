# -*- coding: utf-8 -*-
# .agents/scripts/dispatch_method_c_case3_job3_diag_002.ps1
# Dispatches Method C Case 3 Job-3 Diagnosis Re-Issue
# (HND-METHOD-C-CASE3-JOB3-DIAG-002) to Independent Scientific Supervision (ChatGPT) across OpenClaw PAD Bridge.

param(
    [switch]$CheckOnly,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'

. "$PSScriptRoot\Invoke-ChatGPTBridge.ps1"

$taskId = "METHOD-C-CASE3-JOB3-DIAGNOSIS"
$handoffId = "HND-METHOD-C-CASE3-JOB3-DIAG-002"
$predecessorHandoffId = "HND-METHOD-C-CASE3-JOB3-DIAG-001"

$reportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md"
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

$receiptPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json"
$receiptSha = (Get-FileHash -Path $receiptPath -Algorithm SHA256).Hash.ToUpper()
$receiptSize = (Get-Item $receiptPath).Length

$summaryPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json"
$summarySha = (Get-FileHash -Path $summaryPath -Algorithm SHA256).Hash.ToUpper()
$summarySize = (Get-Item $summaryPath).Length

$spatialPath = Join-Path $caseDir "job3_spatial_crack.json"
$spatialSha = (Get-FileHash -Path $spatialPath -Algorithm SHA256).Hash.ToUpper()
$spatialSize = (Get-Item $spatialPath).Length

$obsPath = Join-Path $caseDir "job3_observables.json"
$obsSha = (Get-FileHash -Path $obsPath -Algorithm SHA256).Hash.ToUpper()
$obsSize = (Get-Item $obsPath).Length

$deckPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp"
$deckSha = (Get-FileHash -Path $deckPath -Algorithm SHA256).Hash.ToUpper()
$deckSize = (Get-Item $deckPath).Length

$meshPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_PHYS.inp"
$meshSha = (Get-FileHash -Path $meshPath -Algorithm SHA256).Hash.ToUpper()
$meshSize = (Get-Item $meshPath).Length

$genScriptPath = Join-Path $PSScriptRoot "..\..\scripts\state_transfer\run_case3_cycle2_state_transfer.py"
$genScriptSha = (Get-FileHash -Path $genScriptPath -Algorithm SHA256).Hash.ToUpper()
$genScriptSize = (Get-Item $genScriptPath).Length

$uelPath = Join-Path $PSScriptRoot "..\..\models\pandey_kumar_mode1\f42_mixed_uel.for"
$uelSha = (Get-FileHash -Path $uelPath -Algorithm SHA256).Hash.ToUpper()
$uelSize = (Get-Item $uelPath).Length

$diagTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job3_diagnosis.py"
$diagTestSha = (Get-FileHash -Path $diagTestPath -Algorithm SHA256).Hash.ToUpper()

$execTestPath = Join-Path $PSScriptRoot "..\..\tests\unit\test_method_c_case3_job3_execution.py"
$execTestSha = (Get-FileHash -Path $execTestPath -Algorithm SHA256).Hash.ToUpper()

$execReportPath = Join-Path $PSScriptRoot "..\..\docs\validation\METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md"
$execReportSha = (Get-FileHash -Path $execReportPath -Algorithm SHA256).Hash.ToUpper()
$execReportSize = (Get-Item $execReportPath).Length

$staPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta"
$staSha = (Get-FileHash -Path $staPath -Algorithm SHA256).Hash.ToUpper()
$staSize = (Get-Item $staPath).Length

$msgPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg"
$msgSha = (Get-FileHash -Path $msgPath -Algorithm SHA256).Hash.ToUpper()
$msgSize = (Get-Item $msgPath).Length

$datPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat"
$datSha = (Get-FileHash -Path $datPath -Algorithm SHA256).Hash.ToUpper()
$datSize = (Get-Item $datPath).Length

$logPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log"
$logSha = (Get-FileHash -Path $logPath -Algorithm SHA256).Hash.ToUpper()
$logSize = (Get-Item $logPath).Length

$csvPath = Join-Path $caseDir "PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv"
$csvSha = (Get-FileHash -Path $csvPath -Algorithm SHA256).Hash.ToUpper()
$csvSize = (Get-Item $csvPath).Length

$githubBase = "https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/$commitSha"

$prompt = @"
[BRIDGE_HANDOFF_ID=$handoffId]
INDEPENDENT_STRUCTURED_REVIEW_V1

{
  "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
  "correlation_id": "$handoffId",
  "predecessor_correlation_id": "$predecessorHandoffId",
  "task_id": "$taskId",
  "title": "Method C Case 3: Job-3 Diagnosis Re-Issue (DIAG-002) with Evidenced UEL Syntax and SVAR Parity",
  "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
  "canonical_rules_sha256": "$rulesSha",
  "artifact_commit": "$commitSha",
  "checkpoint_artifact": "docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md",
  "checkpoint_artifact_sha256": "$reportSha",
  "research_contract": {
    "goal_id": "METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1",
    "method": "METHOD_C",
    "operation": "method_c_case3_job3_diagnosis",
    "numerical_uncertainty": "Can the Job-3 diagnosis be re-issued with the repaired UEL cards quoted verbatim from the executed deck (PROPERTIES=6, VARIABLES=18, UNSYMM, DOF 3 / 1, 2), the correct diff line numbers and SVAR count, the correct §3.1 total-energy absolutes (0.09956534 vs 0.099949652 kN*mm), and the regeneration mechanism attributed to evidence in the repo, with 0 new PBS jobs consumed?",
    "expected_numerical_result": "Diagnosis re-issue HND-METHOD-C-CASE3-JOB3-DIAG-002 with verbatim UEL cards, corrected line numbers and SVAR count, corrected §3.1 absolutes, and an evidenced regeneration attribution, 0 new PBS jobs consumed (cumulative 65 preserved); MASTER_GOAL_STATUS = OPEN.",
    "indicator_type": "F1852_MEASURED_DRIVER",
    "indicator_role": "METHOD_C_DRIVER",
    "causal_evidence_status": "PLANNED"
  },
  "evidence_manifest": {
    "diagnosis_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md",
      "sha256": "$reportSha",
      "size_bytes": $reportSize,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB3_DIAGNOSIS_REPORT.md"
    },
    "execution_report": {
      "path": "docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md",
      "sha256": "$execReportSha",
      "size_bytes": $execReportSize,
      "github_url": "$githubBase/docs/validation/METHOD_C_CASE3_JOB3_EXECUTION_REPORT.md"
    },
    "generating_script": {
      "path": "scripts/state_transfer/run_case3_cycle2_state_transfer.py",
      "sha256": "$genScriptSha",
      "size_bytes": $genScriptSize,
      "github_url": "$githubBase/scripts/state_transfer/run_case3_cycle2_state_transfer.py",
      "lines_writing_uel_cards": "443 (U1 quad), 449 (U3 tri), 460 (U2 quad), 466 (U4 tri)",
      "cycle1_reference_lines": "441-464 in scripts/state_transfer/run_case3_cycle1_state_transfer.py"
    },
    "completion_receipt": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json",
      "sha256": "$receiptSha",
      "size_bytes": $receiptSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_RECEIPT.json",
      "job_id": "1424778.mmaster02",
      "exit_code": 1,
      "status": "CUTBACK_TERMINATION",
      "termination_reason": "TIME_INCREMENT_LESS_THAN_MINIMUM",
      "terminal_frame_label": "Increment 28 (terminal converged state; Increment 29 attempted 3 cutbacks down to dt_min=1.0e-14 and aborted)",
      "pbs_job_span_walltime_s": 4602.0,
      "solver_wallclock_s": 4268.0,
      "solver_cpu_s": 2918.0,
      "legacy_walltime_s_removed": true,
      "timestamps_utc": "2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z",
      "timestamps_cet": "2026-11-21 00:09:47 CET to 2026-11-21 01:26:29 CET",
      "timestamp_source_notes": "Timestamps 2026-11-20 23:09:47Z to 2026-11-21 00:26:29Z (00:09:47 to 01:26:29 CET) represent the 4,602 s scheduler span; pbs_execution.log records compilation starting at 00:09:21 CET (23:09:21Z) and epilogue completion at 01:26:03 CET (00:26:03Z).",
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
        "deck_status": "REGENERATED_PREFLIGHT_SYNTAX_REPAIR",
        "generating_script": "scripts/state_transfer/run_case3_cycle2_state_transfer.py",
        "generating_script_sha256": "4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4"
      }
    },
    "observables_summary": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json",
      "sha256": "$summarySha",
      "size_bytes": $summarySize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_SUMMARY.json"
    },
    "spatial_crack_metrics": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json",
      "sha256": "$spatialSha",
      "size_bytes": $spatialSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job3_spatial_crack.json"
    },
    "frame_observables": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json",
      "sha256": "$obsSha",
      "size_bytes": $obsSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/job3_observables.json"
    },
    "production_deck": {
      "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.inp",
      "sha256": "$deckSha",
      "size_bytes": $deckSize,
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
      "size_bytes": $meshSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_PHYS.inp",
      "physical_elements": 39312,
      "quad_fraction_pct": 97.43,
      "nodes": 39034
    },
    "frozen_uel": {
      "path": "models/pandey_kumar_mode1/f42_mixed_uel.for",
      "sha256": "$uelSha",
      "size_bytes": $uelSize,
      "github_url": "$githubBase/models/pandey_kumar_mode1/f42_mixed_uel.for"
    },
    "solver_text_outputs": {
      "sta_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta",
        "sha256": "$staSha",
        "size_bytes": $staSize,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.sta"
      },
      "msg_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg",
        "sha256": "$msgSha",
        "size_bytes": $msgSize,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.msg"
      },
      "dat_file": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat",
        "sha256": "$datSha",
        "size_bytes": $datSize,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3.dat"
      },
      "pbs_execution_log": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log",
        "sha256": "$logSha",
        "size_bytes": $logSize,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_pbs_execution.log"
      },
      "uel_energy_balance_csv": {
        "path": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv",
        "sha256": "$csvSha",
        "size_bytes": $csvSize,
        "github_url": "$githubBase/models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_CYCLE2_REFINED_JOB3_uel_energy_balance.csv"
      }
    },
    "diagnosis_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job3_diagnosis.py",
      "sha256": "$diagTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job3_diagnosis.py",
      "tests_passed": 7,
      "total_tests": 7
    },
    "execution_unit_tests": {
      "path": "tests/unit/test_method_c_case3_job3_execution.py",
      "sha256": "$execTestSha",
      "github_url": "$githubBase/tests/unit/test_method_c_case3_job3_execution.py",
      "tests_passed": 5,
      "total_tests": 5,
      "case3_test_suite_passed": 37,
      "case3_test_suite_total": 37
    }
  },
  "review_checklist_and_gaps": {
    "gap_mc_c3j3d_01_verbatim_uel_syntax_and_svar_arithmetic": "RESOLVED: §2.2 quotes executed deck *USER ELEMENT cards verbatim (PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM; U1/U3 data '3', U2/U4 data '1, 2'). §2.3 documents actual diff lines: executed deck lines 39054 (U1), 77358 (U3), 78375 (U2), 116679 (U4) vs approved candidate deck lines 39052-39063 (where cards were grouped). §2.3 corrects SVAR count arithmetic: exactly 18 SVARs per physical element across 39,312 records (39,312 x 18 = 707,616 SVAR values) plus 39,312 element IDs equals 746,928 total values in *INITIAL CONDITIONS, TYPE=SOLUTION (across 117,936 lines), 100% bitwise identical.",
    "gap_mc_c3j3d_02_evidenced_generating_script": "RESOLVED: Generating script scripts/state_transfer/run_case3_cycle2_state_transfer.py (33,734 B, SHA 4C61BC4950EB7491E594F2CFD1768D187FE039521A9476B2E8ED00BAFAA10EF4) is tracked, committed, and pushed to the repository. Lines 443, 449, 460, and 466 write the exact verbatim UEL cards, matching scripts/state_transfer/run_case3_cycle1_state_transfer.py lines 441-464.",
    "gap_mc_c3j3d_03_total_energy_absolutes": "RESOLVED: Corrected §3.1 total-energy absolutes to committed CSV values: Job-2 Step-1 E_total 0.09956534 kN*mm vs Job-1 Step-1 E_total 0.099949652 kN*mm (delta = -0.3845% ~ -0.385%). Initial fracture energy 0.00172721 kN*mm vs 0.00173094 kN*mm (-0.215%).",
    "note_mc_c3j3d_01_receipt_legacy_walltime_removed": "RESOLVED: Removed legacy walltime_s from receipt solver_execution, retaining disambiguated pbs_job_span_walltime_s: 4602.0, solver_wallclock_s: 4268.0, and solver_cpu_s: 2918.0.",
    "note_mc_c3j3d_02_timestamp_source_documented": "RESOLVED: Documented timestamp source in receipt and report: timestamps 23:09:47Z to 00:26:29Z represent the 4,602 s scheduler span; pbs_execution.log records compilation starting at 00:09:21 CET (23:09:21Z) and epilogue wrap-up at 01:26:03 CET (00:26:03Z).",
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
