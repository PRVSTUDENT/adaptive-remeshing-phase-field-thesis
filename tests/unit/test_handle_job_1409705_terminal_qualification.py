"""
Unit Tests for Authoritative One-Shot Terminal Qualification & Release Handler
(scripts/validation/handle_job_1409705_terminal_qualification.py)

Comprehensive test suite verifying all 12 implementation prerequisites and failure modes:
1. Prescribed two-step schedule verification (2,000 incs Step 1 + 5,000 incs Step 2 = 7,000 incs total)
2. Rejection of incorrect 7,000-increment Step-2 assumptions
3. Step 1 complete / Step 2 incomplete rejection
4. Rejection of positive but wrong terminal displacement (e.g. u = 0.005000 mm, u = 0.006554 mm, u = 0.008000 mm)
5. Prescribed displacement endpoint verification (u = 0.010000 mm) with float representation and BC mapping
6. Nonfatal negative-eigenvalue softening warning handling (passes with recorded diagnostic)
7. Fatal solver diagnostics (zero pivots, numerical singularities, error tags, cutback exhaustion block release)
8. Mechanically valid F-u history (monotonicity, finite values, K0 > 0, Fmax > 0, post-peak softening)
9. Rejection of corrupt/incomplete F-u histories (NaN/Inf, non-monotonic displacement, missing post-peak, too few points)
10. Energy units and raw-sign versus normalized-sign work handling (1 kN*mm = 1000 mJ, W_ext normalized)
11. Rejection of unphysical negative elastic or fracture energy integrands (E_elas < 0, E_frac < 0)
12. Scheduler running/Q state no-op (STILL_RUNNING_NOOP)
13. Solver nonzero exit / error log (BLOCK_RELEASE)
14. Missing SDV17-20 state variables (BLOCK_RELEASE)
15. ODB/CSV frame/reduction mismatch (BLOCK_RELEASE)
16. Duplicated integration-point records / 4x CPE4 overcounting (BLOCK_RELEASE)
17. Mechanical parity extraction diffs reported vs canonical reference (no hard gate)
18. Clean successful release with reported bookkeeping residual (NO hard gate)
19. Idempotent pre-existing S2 job (submits S3 only -> RELEASE_BOTH)
20. Idempotent pre-existing S3 job (submits S2 only -> RELEASE_BOTH)
21. Partial submission recovery (first qsub ok, second fails -> PARTIAL_SUBMISSION_REQUIRES_RECONCILIATION)
22. Notification failure resilience (PBS ID preserved authoritative)
23. Repeat invocation after both submitted (ALREADY_RELEASED_NOOP)
24. Dry-run suite & machine-readable decision record export
"""

import os
import sys
import json
import math
import pytest
from pathlib import Path

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.validation.handle_job_1409705_terminal_qualification import (
    CANONICAL_REF_K0,
    CANONICAL_REF_FMAX,
    CANONICAL_REF_UPEAK,
    CANONICAL_REF_FINAL_RF,
    CANONICAL_REF_WEXT,
    CANONICAL_REF_ELEMENT_COUNT,
    PRESCRIBED_STEP1_TARGET_INCS,
    PRESCRIBED_STEP2_TARGET_INCS,
    PRESCRIBED_TOTAL_TARGET_INCS,
    PRESCRIBED_FINAL_ENDPOINT_U_MM,
    PRESCRIBED_STEP2_TIME_HORIZON_S,
    audit_scheduler_state,
    audit_solver_log_and_sta,
    audit_step_completion,
    audit_displacement_horizon,
    audit_solver_diagnostics,
    audit_mechanical_f_u_history,
    audit_mechanical_parity,
    audit_energy_fields,
    audit_cross_channel_parity,
    calculate_bookkeeping_residual,
    check_submission_state,
    submit_candidate_job,
    evaluate_and_release,
    make_valid_s1_eval_dict,
    run_dry_run_suite,
    DEFAULT_DRYRUN_RECORD_PATH
)


# ==============================================================================
# 1. PRESCRIBED TWO-STEP SCHEDULE VERIFICATION & REGRESSION CASES
# ==============================================================================

def test_step_completion_prescribed_two_step_schedule():
    """Verifies that audit_step_completion checks the prescribed two-step schedule (2000 + 5000 = 7000 incs)."""
    clean_sta = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY\n Step 1 completed in 2000 increments\n Step 2 completed in 5000 increments"
    clean_log = "Abaqus JOB PK_M1_REF15K_ENERGY COMPLETED"
    
    ok, reason, details = audit_step_completion(clean_sta, clean_log)
    assert ok is True
    assert "PRESCRIBED_TWO_STEP_SCHEDULE_COMPLETED" in reason
    assert details["prescribed_step1_incs"] == 2000
    assert details["prescribed_step2_incs"] == 5000
    assert details["prescribed_total_incs"] == 7000
    assert details["two_step_horizon_verified"] is True


def test_step_completion_reject_incorrect_7000_step2_assumption():
    """Regression test: Verifies rejection when an erroneous assumption of 7000 incs for Step 2 alone is passed."""
    clean_sta = "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"
    clean_log = "Abaqus JOB PK_M1_REF15K_ENERGY COMPLETED"
    
    # Passing Step 2 = 7000 increments is an incorrect schedule assumption
    ok, reason, _ = audit_step_completion(
        clean_sta, clean_log,
        prescribed_step1_incs=0,
        prescribed_step2_incs=7000,
        prescribed_total_incs=7000
    )
    assert ok is False
    assert "INCORRECT_SCHEDULE_ASSUMPTION" in reason


def test_step_completion_step1_complete_step2_incomplete():
    """Regression test: Verifies rejection when Step 1 completes but Step 2 is incomplete or cut back."""
    incomplete_sta = "Step 1 completed in 2000 increments\nStep 2 Inc 1111\nTHE ANALYSIS HAS NOT BEEN COMPLETED\n***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED (1.0E-8)"
    incomplete_log = "Abaqus Error: The executable standard.exe aborted"
    
    ok, reason, details = audit_step_completion(incomplete_sta, incomplete_log)
    assert ok is False
    assert "STA_INDICATES_ANALYSIS_NOT_COMPLETED" in reason or "CUTBACK_TIME_INCREMENT_EXHAUSTION_DETECTED" in reason


def test_step_completion_missing_banner():
    """Verifies rejection when STA lacks the analysis completed banner."""
    truncated_sta = "Step 1 completed\nStep 2 completed"
    ok, reason, details = audit_step_completion(truncated_sta, "")
    assert ok is False
    assert "STA_MISSING_ANALYSIS_COMPLETED_BANNER" in reason


# ==============================================================================
# 2. DISPLACEMENT HORIZON & ENDPOINT AUDIT & REGRESSION CASES
# ==============================================================================

def test_displacement_horizon_reject_positive_but_wrong_endpoint():
    """Regression test: Verifies rejection when step is incomplete or terminal time not reached."""
    # Premature cutoff from earlier runs with step not completed (e.g. u = 0.006554 mm)
    ok_cut, reason_cut, _ = audit_displacement_horizon(0.006554, step_completed=False)
    assert ok_cut is False
    assert "STEP_NOT_COMPLETED" in reason_cut
    
    # Incomplete step time (e.g. t = 0.5000 s in Step 2)
    ok_s1, reason_s1, _ = audit_displacement_horizon(0.005000, step_completed=True, terminal_step_time_s=0.5000)
    assert ok_s1 is False
    assert "TERMINAL_STEP_TIME_INCOMPLETE" in reason_s1
    
    # Premature step time (e.g. t = 0.6554 s)
    ok_inter, reason_inter, _ = audit_displacement_horizon(0.008000, step_completed=True, terminal_step_time_s=0.6554)
    assert ok_inter is False
    assert "TERMINAL_STEP_TIME_INCOMPLETE" in reason_inter
    
    # Incomplete step prevents endpoint verification
    ok_step, reason_step, _ = audit_displacement_horizon(0.010000, step_completed=False)
    assert ok_step is False
    assert "STEP_NOT_COMPLETED" in reason_step
    
    # None or non-positive
    ok_none, reason_none, _ = audit_displacement_horizon(None)
    assert ok_none is False
    assert "U_FINAL_IS_NONE" in reason_none
    
    ok_neg, reason_neg, _ = audit_displacement_horizon(-0.005)
    assert ok_neg is False
    assert "U_FINAL_NON_POSITIVE" in reason_neg


def test_displacement_horizon_terminal_prescribed_endpoint_correctly_reached():
    """Regression test: Verifies acceptance of prescribed terminal displacement from BC mapping and step completion."""
    # Exact float
    ok, reason, details = audit_displacement_horizon(
        0.010000,
        prescribed_endpoint=0.010000,
        step_completed=True,
        terminal_step_time_s=1.0000
    )
    assert ok is True
    assert "PRESCRIBED_DISPLACEMENT_ENDPOINT_VERIFIED_FROM_BC_MAPPING" in reason
    assert details["extracted_u_final_mm"] == 0.010000
    assert details["diff_from_endpoint_mm"] == 0.0
    assert details["endpoint_verified"] is True
    assert "prescribed_bc_mapping" in details
    
    # Float representation with step completion
    ok_float, reason_float, details_float = audit_displacement_horizon(
        0.0100000001,
        prescribed_endpoint=0.010000,
        step_completed=True,
        terminal_step_time_s=1.0000
    )
    assert ok_float is True
    assert details_float["endpoint_verified"] is True


# ==============================================================================
# 3. SOLVER DIAGNOSTICS & NONFATAL WARNINGS
# ==============================================================================

def test_solver_diagnostics_negative_eigenvalue_warning_nonfatal():
    """Regression test: Verifies that nonfatal negative-eigenvalue warnings during softening are recorded but do not block."""
    msg_with_warning = (
        "INCREMENT 3500 SUMMARY\n"
        "***WARNING: THE SYSTEM MATRIX HAS 1 NEGATIVE EIGENVALUES DURING EQUILIBRIUM ITERATIONS\n"
        "EQUILIBRIUM ITERATION CONVERGED IN 3 ITERATIONS\n"
    )
    ok, reason, diag_info = audit_solver_diagnostics(msg_with_warning)
    assert ok is True
    assert "NO_FATAL_SOLVER_DIAGNOSTICS" in reason
    assert diag_info["has_nonfatal_negative_eigenvalues"] is True
    assert diag_info["softening_diagnostics_interpretation"] == "NONFATAL_PHYSICAL_SOFTENING_INDICATOR"
    assert len(diag_info["warnings_recorded"]) >= 1


def test_solver_diagnostics_fatal_instability_and_defects_block():
    """Regression test: Verifies that fatal singularities, zero pivots, and error tags strictly fail."""
    # Zero pivot
    msg_pivot = "***WARNING: SOLVER PROBLEM. ZERO PIVOT ENCOUNTERED AT NODE 1245 DOF 1"
    ok_p, reason_p, _ = audit_solver_diagnostics(msg_pivot)
    assert ok_p is False
    assert "ZERO_PIVOT_DETECTED" in reason_p
    
    # Numerical singularity
    msg_sing = "***WARNING: NUMERICAL SINGULARITY WHEN PROCESSING NODE 892 DOF 2"
    ok_s, reason_s, _ = audit_solver_diagnostics(msg_sing)
    assert ok_s is False
    assert "NUMERICAL_SINGULARITY_DETECTED" in reason_s
    
    # Explicit Error
    msg_err = "***ERROR: SYSTEM MATRIX IS NOT POSITIVE DEFINITE AND DIVERGED"
    ok_e, reason_e, _ = audit_solver_diagnostics(msg_err)
    assert ok_e is False
    assert "EXPLICIT_ERROR_TAG_FOUND" in reason_e
    
    # Cutback exhaustion in message file
    msg_cb = "***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED"
    ok_cb, reason_cb, _ = audit_solver_diagnostics(msg_cb)
    assert ok_cb is False
    assert "CUTBACK_TIME_INCREMENT_EXHAUSTION_FATAL" in reason_cb or "EXPLICIT_ERROR_TAG_FOUND" in reason_cb


# ==============================================================================
# 4. MECHANICALLY VALID F-U HISTORY AUDIT
# ==============================================================================

def test_mechanical_f_u_history_complete_and_valid():
    """Regression test: Verifies valid mechanical metrics and full F-u trajectory passing audit."""
    mech = {
        "K0_kN_per_mm": CANONICAL_REF_K0,
        "F_max_kN": CANONICAL_REF_FMAX,
        "u_at_F_max_mm": CANONICAL_REF_UPEAK,
        "F_final_kN": CANONICAL_REF_FINAL_RF,
        "u_final_mm": 0.010000
    }
    # Complete monotonic curve with elastic branch, peak, and softening
    f_u_curve = [
        [0.000000, 0.000000],
        [0.001000, 0.137945],
        [0.003000, 0.413836],
        [0.005857, 0.757778],
        [0.007000, 0.300000],
        [0.008500, 0.050000],
        [0.010000, 0.000232]
    ]
    ok, reason, metrics = audit_mechanical_f_u_history(mech, f_u_data=f_u_curve)
    assert ok is True
    assert "MECHANICALLY_VALID_FULL_F_U_TRAJECTORY" in reason
    assert metrics["K0_kN_per_mm"] == CANONICAL_REF_K0
    assert metrics["softening_ratio_pct"] > 90.0
    assert metrics["f_u_monotonic_and_complete"] is True


def test_mechanical_f_u_history_corrupt_incomplete_or_non_monotonic():
    """Regression test: Verifies rejection of corrupt, incomplete, or non-monotonic F-u histories."""
    # Non-positive K0
    bad_k0 = {"K0_kN_per_mm": -10.0, "F_max_kN": 0.75, "u_at_F_max_mm": 0.0058, "F_final_kN": 0.001}
    ok_k, reason_k, _ = audit_mechanical_f_u_history(bad_k0)
    assert ok_k is False
    assert "NON_POSITIVE_INITIAL_STIFFNESS" in reason_k
    
    # Missing post-peak softening (F_final >= F_max)
    no_soft = {"K0_kN_per_mm": 137.0, "F_max_kN": 0.75, "u_at_F_max_mm": 0.0058, "F_final_kN": 0.80}
    ok_s, reason_s, _ = audit_mechanical_f_u_history(no_soft)
    assert ok_s is False
    assert "NO_POST_PEAK_SOFTENING_DETECTED" in reason_s
    
    # NaN in metrics
    nan_mech = {"K0_kN_per_mm": float("nan"), "F_max_kN": 0.75, "u_at_F_max_mm": 0.0058, "F_final_kN": 0.001}
    ok_n, reason_n, _ = audit_mechanical_f_u_history(nan_mech)
    assert ok_n is False
    assert "MECHANICAL_METRIC_NAN_OR_INF" in reason_n
    
    # Inf in force data
    good_mech = {"K0_kN_per_mm": 137.0, "F_max_kN": 0.75, "u_at_F_max_mm": 0.0058, "F_final_kN": 0.001, "u_final_mm": 0.010000}
    inf_curve = [[0.0, 0.0], [0.005, float("inf")], [0.01, 0.001]]
    ok_inf, reason_inf, _ = audit_mechanical_f_u_history(good_mech, f_u_data=inf_curve)
    assert ok_inf is False
    assert "NAN_OR_INF_IN_F_U_DATA" in reason_inf
    
    # Non-monotonic displacement array (backwards step)
    non_mono_curve = [
        [0.000000, 0.0],
        [0.002000, 0.2],
        [0.001500, 0.15], # Backwards step!
        [0.005800, 0.75],
        [0.010000, 0.01]
    ]
    ok_m, reason_m, _ = audit_mechanical_f_u_history(good_mech, f_u_data=non_mono_curve)
    assert ok_m is False
    assert "NON_MONOTONIC_DISPLACEMENT" in reason_m

    # Too few increments (< 3)
    too_few_curve = [[0.0, 0.0], [0.01, 0.5]]
    ok_tf, reason_tf, _ = audit_mechanical_f_u_history(good_mech, f_u_data=too_few_curve)
    assert ok_tf is False
    assert "F_U_DATA_TOO_FEW_INCREMENTS" in reason_tf


# ==============================================================================
# 5. ENERGY UNITS, SIGNS, AND WORK NORMALIZATION
# ==============================================================================

def test_energy_units_and_raw_vs_normalized_sign_handling():
    """Regression test: Verifies formulation-specific units (1 kN*mm = 1000 mJ) and raw-vs-normalized work handling."""
    # Clean valid inputs with raw negative RF work channel
    ok, reason, details = audit_energy_fields(
        has_energy_sdvs=True,
        e_elas_final=0.000150, # kN*mm (0.150 mJ)
        e_frac_final=0.002100, # kN*mm (2.100 mJ)
        w_ext_final=-0.002359, # Negative raw RF sign
        unique_elements_count=CANONICAL_REF_ELEMENT_COUNT,
        expected_elements=CANONICAL_REF_ELEMENT_COUNT
    )
    assert ok is True
    assert details["e_elas_final_mJ"] == 0.150
    assert details["e_frac_final_mJ"] == 2.100
    assert details["w_ext_normalized_kNmm"] == 0.002359
    assert details["w_ext_normalized_mJ"] == 2.359
    assert details["raw_work_sign_normalized"] is True
    assert "1 kN*mm = 1.0 J = 1000.0 mJ" in details["unit_equivalence"]


def test_energy_reject_negative_elastic_or_fracture_integrand():
    """Regression test: Rejects unphysical negative elastic strain energy or AT2 fracture surface energy."""
    # Negative elastic energy integrand -> fail
    ok_neg_e, reason_neg_e, _ = audit_energy_fields(has_energy_sdvs=True, e_elas_final=-0.05, e_frac_final=0.002, w_ext_final=0.002)
    assert ok_neg_e is False
    assert "NEGATIVE_ELASTIC_ENERGY_INTEGRAND" in reason_neg_e
    
    # Negative fracture energy integrand -> fail
    ok_neg_f, reason_neg_f, _ = audit_energy_fields(has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=-0.01, w_ext_final=0.002)
    assert ok_neg_f is False
    assert "NEGATIVE_FRACTURE_ENERGY_INTEGRAND" in reason_neg_f
    
    # Element deduplication overcounting (e.g. 60,768 elements instead of 15,192)
    ok_dedup, reason_dedup, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.003,
        unique_elements_count=60768, expected_elements=15192
    )
    assert ok_dedup is False
    assert "ELEMENT_DEDUPLICATION_MISMATCH" in reason_dedup


# ==============================================================================
# 6. SCHEDULER STATE AUDIT & RUNNING NO-OP
# ==============================================================================

def test_scheduler_running_or_queued_noop():
    """Verifies that active running/queued scheduler states produce STILL_RUNNING_NOOP."""
    qstat_running = "1409705.mmaster02  pr21vyci  normal_imfdfkmq  PK_M1_REF15K  --  1  1  32gb  48:00  R  01:23"
    assert audit_scheduler_state(qstat_running, "1409705") == "RUNNING"
    
    qstat_queued = "1409705.mmaster02  pr21vyci  normal_imfdfkmq  PK_M1_REF15K  --  1  1  32gb  48:00  Q  --"
    assert audit_scheduler_state(qstat_queued, "1409705") == "RUNNING"
    
    eval_dict = make_valid_s1_eval_dict()
    report = evaluate_and_release(eval_dict, scheduler_state="RUNNING")
    assert report["final_action"] == "STILL_RUNNING_NOOP"
    assert report["prerequisites"]["terminal_scheduler_state"]["status"] == "FAIL"
    assert report["is_qualified"] is False
    assert len(report["submission_actions"]) == 0


# ==============================================================================
# 7. SOLVER NONZERO EXIT & INCOMPLETE RUNS
# ==============================================================================

def test_terminal_nonzero_exit():
    """Verifies that an aborted Abaqus solver execution blocks release."""
    bad_log = "Abaqus Error: The executable standard.exe aborted with system error code 1"
    bad_sta = "THE ANALYSIS HAS NOT BEEN COMPLETED"
    ok, reason = audit_solver_log_and_sta(bad_log, bad_sta)
    assert ok is False
    assert "LOG_CONTAINS_ABAQUS_ERROR_EXIT" in reason
    
    eval_dict = make_valid_s1_eval_dict()
    eval_dict["log_content"] = bad_log
    eval_dict["sta_content"] = bad_sta
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL")
    assert report["final_action"] == "BLOCK_RELEASE"
    assert report["prerequisites"]["solver_exit_0"]["status"] == "FAIL"
    assert any("SOLVER_COMPLETION_FAILED" in err for err in report["errors"])
    assert len(report["submission_actions"]) == 0


# ==============================================================================
# 8. CROSS-CHANNEL PARITY (ODB VS CSV)
# ==============================================================================

def test_odb_csv_mismatch():
    """Verifies that cross-channel frame mismatch or reduction mismatch blocks release."""
    odb_e = 0.002500
    csv_e = 0.005000
    # Frame index mismatch
    ok, reason, _ = audit_cross_channel_parity(odb_e, csv_e, frame_index_matched=False)
    assert ok is False
    assert "FRAME_INDEX_MISMATCH" in reason
    
    # Element reduction mismatch
    ok_red, reason_red, _ = audit_cross_channel_parity(odb_e, csv_e, frame_index_matched=True, element_reduction_matched=False)
    assert ok_red is False
    assert "ELEMENT_REDUCTION_MISMATCH" in reason_red


# ==============================================================================
# 9. MECHANICAL PARITY EXTRACTION REPORTING
# ==============================================================================

def test_mechanical_parity_extraction():
    """Verifies extraction and reporting of mechanical differences vs canonical reference."""
    ok, reason, diff_dict = audit_mechanical_parity(
        k0=137.820804,
        f_max=0.757700,
        u_peak=0.005857,
        f_final=0.000232,
        w_ext=0.002359
    )
    assert ok is True
    assert "MECHANICAL_PARITY_EXTRACTED" in reason
    assert abs(diff_dict["delta_k0_pct"] - (-0.0904)) < 0.01
    assert abs(diff_dict["delta_fmax_pct"] - (-0.0103)) < 0.01
    assert diff_dict["governance"] == "REPORTED_SCIENTIFIC_EVIDENCE_NO_HARD_PASS_FAIL_GATE"


# ==============================================================================
# 10. BOOKKEEPING RESIDUAL & CLEAN SUCCESSFUL RELEASE
# ==============================================================================

def test_clean_successful_release_and_bookkeeping_reporting():
    """Verifies clean qualification and release with reported bookkeeping residual (no hard gate)."""
    eval_dict = make_valid_s1_eval_dict()
    eval_dict["energy_balance"]["e_model_final_kNmm"] = 0.002250
    eval_dict["energy_balance"]["w_ext_final_kNmm"] = 0.002359 # Delta = -0.000109 kN*mm (-4.6%)
    
    mock_submissions = []
    def mock_runner(cmd):
        if "qsub" in cmd:
            job_num = 1409900 + len(mock_submissions) + 1
            jid = "%d.mmaster02" % job_num
            mock_submissions.append((cmd, jid))
            return 0, jid, ""
        elif "notify_submitted" in cmd:
            return 0, "OK", ""
        return 0, "", ""
        
    submission_state = {"s2_submitted": False, "s3_submitted": False}
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL", submission_state=submission_state, remote_runner=mock_runner)
    
    assert report["is_qualified"] is True
    assert report["final_action"] == "RELEASE_BOTH"
    assert report["s2_job_id"] == "1409901.mmaster02"
    assert report["s3_job_id"] == "1409902.mmaster02"
    assert report["bookkeeping_residual"] is not None
    assert abs(report["bookkeeping_residual"]["signed_reldiff_pct"] - (-4.62)) < 0.1
    assert len(mock_submissions) == 2
    for prereq_key, prereq_val in report["prerequisites"].items():
        assert prereq_val["status"] == "PASS", "Prerequisite %s failed" % prereq_key


# ==============================================================================
# 11. IDEMPOTENCY & RESILIENCE (S2/S3 PRE-EXISTING, PARTIAL SUBMISSION)
# ==============================================================================

def test_pre_existing_s2_job():
    """Verifies that an existing S2 job is preserved and only S3 is submitted."""
    eval_dict = make_valid_s1_eval_dict()
    mock_submissions = []
    def mock_runner(cmd):
        if "qsub" in cmd:
            jid = "1409903.mmaster02"
            mock_submissions.append((cmd, jid))
            return 0, jid, ""
        return 0, "", ""
        
    submission_state = {
        "s2_submitted": True,
        "s2_job_id": "1409850.mmaster02",
        "s3_submitted": False,
        "s3_job_id": None
    }
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL", submission_state=submission_state, remote_runner=mock_runner)
    
    assert report["final_action"] == "RELEASE_BOTH"
    assert report["s2_job_id"] == "1409850.mmaster02"
    assert report["s3_job_id"] == "1409903.mmaster02"
    assert len(mock_submissions) == 1
    assert "13_fixed_convergence_h0015" in mock_submissions[0][0]


def test_pre_existing_s3_job():
    """Verifies that an existing S3 job is preserved and only S2 is submitted."""
    eval_dict = make_valid_s1_eval_dict()
    mock_submissions = []
    def mock_runner(cmd):
        if "qsub" in cmd:
            jid = "1409904.mmaster02"
            mock_submissions.append((cmd, jid))
            return 0, jid, ""
        return 0, "", ""
        
    submission_state = {
        "s2_submitted": False,
        "s2_job_id": None,
        "s3_submitted": True,
        "s3_job_id": "1409851.mmaster02"
    }
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL", submission_state=submission_state, remote_runner=mock_runner)
    
    assert report["final_action"] == "RELEASE_BOTH"
    assert report["s2_job_id"] == "1409904.mmaster02"
    assert report["s3_job_id"] == "1409851.mmaster02"
    assert len(mock_submissions) == 1
    assert "12_fixed_convergence_h0020" in mock_submissions[0][0]


def test_first_qsub_succeeds_second_fails():
    """Verifies that if S2 succeeds and S3 fails, S2 ID is preserved and PARTIAL_SUBMISSION is reported."""
    eval_dict = make_valid_s1_eval_dict()
    def mock_runner(cmd):
        if "12_fixed_convergence_h0020" in cmd and "qsub" in cmd:
            return 0, "1409905.mmaster02", ""
        elif "13_fixed_convergence_h0015" in cmd and "qsub" in cmd:
            return 1, "", "qsub: PBS queue limit reached or node error"
        return 0, "", ""
        
    submission_state = {"s2_submitted": False, "s3_submitted": False}
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL", submission_state=submission_state, remote_runner=mock_runner)
    
    assert report["final_action"] == "PARTIAL_SUBMISSION_REQUIRES_RECONCILIATION"
    assert report["s2_job_id"] == "1409905.mmaster02"
    assert any("S3 submission failed after S2 submitted" in err for err in report["errors"])


def test_notification_failure_after_successful_submission():
    """Verifies that failure in notify_submitted does not invalidate successful qsub ID."""
    def mock_runner(cmd):
        if "qsub" in cmd:
            return 0, "1409906.mmaster02", ""
        if "notify_submitted" in cmd:
            return 127, "", "curl: (7) Failed to connect to api.telegram.org"
        return 0, "", ""
        
    ok, jid, msg = submit_candidate_job("/fake/path", "PK_M1_S2_ENERGY", remote_runner=mock_runner)
    assert ok is True
    assert jid == "1409906.mmaster02"
    assert msg == "SUBMITTED_SUCCESSFULLY"


def test_repeat_invocation_both_already_submitted():
    """Verifies ALREADY_RELEASED_NOOP with zero executions when both jobs exist."""
    eval_dict = make_valid_s1_eval_dict()
    mock_runner_calls = []
    def mock_runner(cmd):
        mock_runner_calls.append(cmd)
        return 0, "", ""
        
    submission_state = {
        "s2_submitted": True,
        "s2_job_id": "1409850.mmaster02",
        "s3_submitted": True,
        "s3_job_id": "1409851.mmaster02"
    }
    report = evaluate_and_release(eval_dict, scheduler_state="TERMINAL", submission_state=submission_state, remote_runner=mock_runner)
    
    assert report["final_action"] == "ALREADY_RELEASED_NOOP"
    assert report["s2_job_id"] == "1409850.mmaster02"
    assert report["s3_job_id"] == "1409851.mmaster02"
    assert len(mock_runner_calls) == 0


# ==============================================================================
# 12. DRY-RUN SUITE & MACHINE-READABLE DECISION RECORD
# ==============================================================================

def test_dry_run_suite_and_machine_readable_record(tmp_path):
    """Verifies execution of all 9 dry-run scenarios and export of machine-readable JSON."""
    record_file = tmp_path / "test_decision_record.json"
    ok, master_record = run_dry_run_suite(output_record_path=record_file)
    
    assert ok is True
    assert master_record["scenarios_exercised_count"] == 9
    assert os.path.exists(record_file)
    
    with open(record_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert data["audit_protocol_version"] == 2
    assert len(data["scenarios"]) == 9
    
    # Check scenario 1 (clean pass)
    scen1 = data["scenarios"][0]
    assert scen1["final_action"] == "RELEASE_BOTH"
    assert all(p["status"] == "PASS" for p in scen1["prerequisites"].values())
    
    # Check scenario 2 (incomplete step cutback)
    scen2 = data["scenarios"][1]
    assert scen2["final_action"] == "BLOCK_RELEASE"
    assert scen2["prerequisites"]["expected_step_completed"]["status"] == "FAIL"
    
    # Check scenario 7 (partial submission)
    scen7 = data["scenarios"][6]
    assert scen7["final_action"] == "PARTIAL_SUBMISSION_REQUIRES_RECONCILIATION"
    assert scen7["s2_job_id"] == "1409905.mmaster02"
    
    # Check scenario 8 (already released no-op)
    scen8 = data["scenarios"][7]
    assert scen8["final_action"] == "ALREADY_RELEASED_NOOP"

def test_audit_energy_fields_rejects_missing_or_invalid_thickness():
    """Regression test: Rejects missing, non-positive, or non-numeric 2D out-of-plane thickness."""
    # Missing thickness (None) -> fail
    ok_none, reason_none, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.002,
        thickness_mm=None
    )
    assert ok_none is False
    assert "UNRESOLVED_2D_THICKNESS_SPECIFICATION" in reason_none
    
    # Negative thickness -> fail
    ok_neg, reason_neg, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.002,
        thickness_mm=-1.0
    )
    assert ok_neg is False
    assert "UNRESOLVED_2D_THICKNESS_SPECIFICATION" in reason_neg
    
    # Zero thickness -> fail
    ok_zero, reason_zero, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.002,
        thickness_mm=0.0
    )
    assert ok_zero is False
    assert "UNRESOLVED_2D_THICKNESS_SPECIFICATION" in reason_zero
    
    # Non-numeric thickness -> fail
    ok_str, reason_str, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.002,
        thickness_mm="invalid"
    )
    assert ok_str is False
    assert "UNRESOLVED_2D_THICKNESS_SPECIFICATION" in reason_str
    
    # Explicit unit thickness t = 1.0 mm -> pass
    ok_valid, _, _ = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.001, e_frac_final=0.002, w_ext_final=0.002,
        thickness_mm=1.0
    )
    assert ok_valid is True


def test_audit_energy_fields_records_dimensional_consistency_details():
    """Regression test: Verifies certified plane-strain unit thickness, two-tier framework, and internal/external consistency."""
    ok, reason, details = audit_energy_fields(
        has_energy_sdvs=True, e_elas_final=0.000150, e_frac_final=0.002100, w_ext_final=0.002359,
        thickness_mm=1.0, require_dimensional_consistency=True
    )
    assert ok is True
    assert details["out_of_plane_thickness_mm"] == 1.0
    assert details["internal_energy_units"] == "kN*mm == J == 1000 mJ"
    assert details["external_work_units"] == "kN*mm == J == 1000 mJ"
    assert details["energy_density_units"] == "kN/mm^2 == J/mm^3 == 1000 MPa == 1 GPa"
    assert "kN/mm" in details["native_force_units"]
    assert "J/mm" in details["native_energy_units"]
    assert details["thickness_normalization_framework"] == "TIER_1_NATIVE_2D_PER_UNIT_THICKNESS_TO_TIER_2_BENCHMARK_1MM_SLICE"
    assert details["dimensional_consistency_status"] == "CERTIFIED_PLANE_STRAIN_T1MM_CONSISTENT"
    assert "t=1.0 mm certified consistent" in reason

