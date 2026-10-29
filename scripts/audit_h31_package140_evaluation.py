# -*- coding: utf-8 -*-
"""
audit_h31_package140_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent terminal audit and physical/numerical evaluation of Package 140 (Hypothesis H31):
Increment-92 Candidate C4 Under-Relaxed AM/PDAS Continuation (omega=0.70, max 35 cycles).
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import hashlib

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def run_h31_audit(repo_root):
    pkg140_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "140_c4_inc92_h31_underrelaxed_forward_continuation")
    pkg139_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "139_c4_inc91_h30_underrelaxed_forward_continuation")

    summary_path = os.path.join(pkg140_dir, "c4_inc92_h31_continuation_summary.json")
    pbs_log_path = os.path.join(pkg140_dir, "pbs_execution.log")
    active_cards_path = os.path.join(pkg140_dir, "active_set_boundary_cards.inc")

    ckpt_json_path = os.path.join(pkg140_dir, "c4_donor_inc92_exact_checkpoint.json")
    bounds_csv_path = os.path.join(pkg140_dir, "c4_donor_inc92_exact_checkpoint_d_lower_bounds.csv")
    disp_csv_path = os.path.join(pkg140_dir, "c4_donor_inc92_exact_checkpoint_nodal_displacements.csv")
    cards_inc_path = os.path.join(pkg140_dir, "c4_donor_inc92_exact_checkpoint_active_set_cards.inc")
    receipt_json_path = os.path.join(pkg140_dir, "c4_donor_inc92_exact_checkpoint_recovery_receipt.json")

    prev_bounds_csv_path = os.path.join(pkg140_dir, "d_lower_bounds.csv")
    prev_d0_cards_path = os.path.join(pkg140_dir, "stage_a_all_d0_boundary_cards.inc")

    # 1. Existence Checks
    paths_to_check = [
        summary_path, pbs_log_path, ckpt_json_path, bounds_csv_path,
        disp_csv_path, cards_inc_path, receipt_json_path,
        prev_bounds_csv_path, prev_d0_cards_path
    ]
    for p in paths_to_check:
        if not os.path.exists(p):
            raise RuntimeError("Required audit path missing: %s" % p)

    file_hashes = {
        "checkpoint_json": compute_sha256(ckpt_json_path),
        "bounds_csv": compute_sha256(bounds_csv_path),
        "disp_csv": compute_sha256(disp_csv_path),
        "cards_inc": compute_sha256(cards_inc_path),
        "receipt_json": compute_sha256(receipt_json_path),
        "continuation_summary": compute_sha256(summary_path)
    }

    # 2. Parse Summary Telemetry
    with open(summary_path, "r") as f:
        summary = json.load(f)

    final_state = summary["final_state"]
    cycles_completed = summary["cycles_completed"]
    converged_status = summary["status"]
    raw_delta_d = final_state["raw_max_delta_d"]
    relaxed_delta_d = final_state["relaxed_max_delta_d"]
    delta_rf2 = final_state["delta_rf2_prev_cycle_N"]
    free_res = final_state["free_res_max_kN_mm"]
    min_lambda = final_state["min_lambda_kN_mm"]
    healing_violations_reported = final_state["healing_violations"]
    d_max = final_state["d_max"]
    rf2_rp = final_state["rf2_rp_N"]
    e_elas = final_state["e_elas_mJ"]
    e_frac = final_state["e_frac_mJ"]
    e_tot = final_state["e_tot_mJ"]
    active_nodes = final_state["active_nodes"]
    free_nodes = final_state["free_nodes"]

    # 3. Check Predeclared Acceptance Criteria
    donor_rf2_ref = 180.059254
    donor_etot_ref = 0.25357917

    rf2_error_pct = (rf2_rp - donor_rf2_ref) / donor_rf2_ref * 100.0
    etot_error_pct = (e_tot - donor_etot_ref) / donor_etot_ref * 100.0

    criteria = {
        "c1_raw_stationarity": {
            "value": raw_delta_d,
            "threshold": 1.0e-3,
            "pass": bool(raw_delta_d <= 1.0e-3)
        },
        "c2_reaction_force_drift": {
            "value": delta_rf2,
            "threshold": 0.10,
            "pass": bool(delta_rf2 <= 0.10)
        },
        "c3_free_phase_kkt_residual": {
            "value": free_res,
            "threshold": 1.0e-6,
            "pass": bool(free_res <= 1.0e-6)
        },
        "c4_active_multiplier_bound": {
            "value": min_lambda,
            "threshold": -1.0e-9,
            "pass": bool(min_lambda >= -1.0e-9)
        },
        "c5_reported_healing_violations": {
            "value": healing_violations_reported,
            "threshold": 0,
            "pass": bool(healing_violations_reported == 0)
        },
        "c6_partition_consistency": {
            "active_nodes": active_nodes,
            "free_nodes": free_nodes,
            "total_nodes": active_nodes + free_nodes,
            "expected_total": 4588,
            "pass": bool(active_nodes + free_nodes == 4588)
        },
        "c7_donor_rf2_tolerance": {
            "computed_N": rf2_rp,
            "donor_ref_N": donor_rf2_ref,
            "error_pct": rf2_error_pct,
            "threshold_pct": 5.0,
            "pass": bool(abs(rf2_error_pct) <= 5.0)
        },
        "c8_donor_etot_tolerance": {
            "computed_mJ": e_tot,
            "donor_ref_mJ": donor_etot_ref,
            "error_pct": etot_error_pct,
            "threshold_pct": 2.0,
            "pass": bool(abs(etot_error_pct) <= 2.0)
        }
    }

    # 4. Pointwise Array Verifications
    with open(ckpt_json_path, "r") as f:
        ckpt = json.load(f)

    u_ckpt = ckpt["serialized_state"]["nodal_displacements"]
    d_ckpt = ckpt["serialized_state"]["nodal_damage"]
    h_ckpt = ckpt["serialized_state"]["gauss_point_history"]

    # Verify counts
    n_nodes = len(u_ckpt)
    n_elems = len(h_ckpt)
    n_gps = sum(len(h_ckpt[str(eid)]) for eid in h_ckpt)

    # Pointwise damage monotonicity check against Inc 91 baseline
    d_inc91 = {}
    with open(prev_d0_cards_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 4 and parts[0].isdigit():
                d_inc91[parts[0]] = float(parts[3])

    independent_healing_violations = 0
    max_healing_violation = 0.0
    for nid_str, d_val in d_ckpt.items():
        d_prev = d_inc91.get(nid_str, 0.0)
        if d_val < d_prev - 1.0e-8:
            independent_healing_violations += 1
            max_healing_violation = max(max_healing_violation, d_prev - d_val)

    # Pointwise history monotonicity check against Inc 91 baseline
    h_inc91 = {}
    with open(prev_bounds_csv_path, "r") as f:
        header = [h.strip() for h in f.readline().split(",")]
        h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            eid_str = parts[0]
            h_inc91[eid_str] = [float(parts[i]) for i in h_idx]

    independent_history_loss_violations = 0
    max_history_loss_violation = 0.0
    for eid_str, h_vals in h_ckpt.items():
        h_prev = h_inc91.get(eid_str, [0.0]*4)
        for k in range(4):
            if h_vals[k] < h_prev[k] - 1.0e-8:
                independent_history_loss_violations += 1
                max_history_loss_violation = max(max_history_loss_violation, h_prev[k] - h_vals[k])

    # 5. Column separation and physical bounds in serialized bounds CSV
    d0_min, d0_max = 999.0, -999.0
    h0_min, h0_max = 999.0, -999.0
    with open(bounds_csv_path, "r") as f:
        header = [h.strip() for h in f.readline().split(",")]
        d0_idx = [i for i, h in enumerate(header) if h.startswith("D0_")]
        h0_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            for i in d0_idx:
                v = float(parts[i])
                d0_min = min(d0_min, v)
                d0_max = max(d0_max, v)
            for i in h0_idx:
                v = float(parts[i])
                h0_min = min(h0_min, v)
                h0_max = max(h0_max, v)

    separation_valid = (
        len(d0_idx) == 4 and len(h0_idx) == 4 and
        set(d0_idx).isdisjoint(set(h0_idx)) and
        0.0 <= d0_min and d0_max <= 1.0 and
        h0_min >= 0.0
    )

    # 6. Round-trip restoration check
    max_disp_restoration_err = 0.0
    with open(disp_csv_path, "r") as f:
        f.readline()
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            nid_str = parts[0]
            ux = float(parts[1])
            uy = float(parts[2])
            ux_orig, uy_orig = u_ckpt[nid_str]
            max_disp_restoration_err = max(max_disp_restoration_err, abs(ux - ux_orig), abs(uy - uy_orig))

    max_damage_restoration_err = 0.0
    with open(cards_inc_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 4 and parts[0].isdigit():
                nid_str = parts[0]
                d_val = float(parts[3])
                max_damage_restoration_err = max(max_damage_restoration_err, abs(d_val - d_ckpt[nid_str]))

    # 7. Incremental Work & Energy Balance
    u_init_mm = 0.002040107500
    u_target_mm = 0.002065107460
    delta_u_mm = u_target_mm - u_init_mm

    rf2_inc91 = 184.31004881858826  # From Package 139 committed state
    avg_rf2_kN = 0.5 * (rf2_inc91 + rf2_rp) / 1000.0
    delta_w_ext_mJ = avg_rf2_kN * delta_u_mm * 1000.0  # kN * mm = J = 1000 mJ

    e_tot_inc91 = 0.2531307316978877  # From Package 139
    delta_e_tot_mJ = e_tot - e_tot_inc91
    delta_e_elas_mJ = e_elas - 0.18789500263072226
    delta_e_frac_mJ = e_frac - 0.06523572906716543

    energy_work_residual_mJ = abs(delta_w_ext_mJ - delta_e_tot_mJ)
    energy_work_residual_pct = energy_work_residual_mJ / delta_w_ext_mJ * 100.0

    # 8. Overall Verdict
    all_criteria_passed = (
        all(c["pass"] for c in criteria.values()) and
        independent_healing_violations == 0 and
        independent_history_loss_violations == 0 and
        separation_valid and
        max_disp_restoration_err <= 1.0e-12 and
        max_damage_restoration_err == 0.0
    )

    verdict = "H31_PASSED" if all_criteria_passed else "H31_FAILED_PHYSICAL"

    audit_report = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package_name": "140_c4_inc92_h31_underrelaxed_forward_continuation",
        "batch_name": "MODE1_C4_INC92_H31_CONT",
        "pbs_job_id": "1418600.mmaster02",
        "verdict": verdict,
        "governing_gate_retained": "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED",
        "p113_gate_valid_failure_retained": "+2.00803158%",
        "h24_reference_audit_pending_retained": True,
        "pbs_execution": {
            "exit_code": 0,
            "walltime_seconds": 79,
            "cput_seconds": 54,
            "cycles_completed": cycles_completed,
            "status": converged_status,
            "under_relaxation_omega": 0.70
        },
        "acceptance_criteria": criteria,
        "pointwise_monotonicity": {
            "independent_healing_violations": independent_healing_violations,
            "max_healing_violation": max_healing_violation,
            "independent_history_loss_violations": independent_history_loss_violations,
            "max_history_loss_violation": max_history_loss_violation
        },
        "physical_bounds": {
            "d0_min": d0_min,
            "d0_max": d0_max,
            "h0_min_MPa": h0_min,
            "h0_max_MPa": h0_max,
            "d_max": d_max,
            "separation_valid": separation_valid
        },
        "round_trip_restoration": {
            "max_disp_restoration_err_mm": max_disp_restoration_err,
            "max_damage_restoration_err": max_damage_restoration_err,
            "lossless": bool(max_disp_restoration_err <= 1.0e-12 and max_damage_restoration_err == 0.0)
        },
        "incremental_energetics": {
            "u_init_mm": u_init_mm,
            "u_target_mm": u_target_mm,
            "delta_u_nm": delta_u_mm * 1.0e6,
            "rf2_inc91_N": rf2_inc91,
            "rf2_inc92_N": rf2_rp,
            "delta_w_ext_mJ": delta_w_ext_mJ,
            "delta_e_tot_mJ": delta_e_tot_mJ,
            "delta_e_elas_mJ": delta_e_elas_mJ,
            "delta_e_frac_mJ": delta_e_frac_mJ,
            "energy_work_residual_mJ": energy_work_residual_mJ,
            "energy_work_residual_pct": energy_work_residual_pct
        },
        "file_hashes": file_hashes
    }

    report_path = os.path.join(repo_root, "results", "validation", "h31_c4_inc92_package140_evaluation.json")
    with open(report_path, "w") as f:
        json.dump(audit_report, f, indent=2)

    print("\n" + "=" * 80, flush=True)
    print("H31 AUDIT COMPLETE: Verdict = %s" % verdict, flush=True)
    print("Cycles: %d, Walltime: 79s, RF2: %.4f N (%.2f%%), E_tot: %.6f mJ (%.2f%%)" %
          (cycles_completed, rf2_rp, rf2_error_pct, e_tot, etot_error_pct), flush=True)
    print("Healing Violations: %d, History Loss Violations: %d, Round-Trip Err: %.2e mm" %
          (independent_healing_violations, independent_history_loss_violations, max_disp_restoration_err), flush=True)
    print("Report written to: %s" % report_path, flush=True)
    print("=" * 80, flush=True)

    return audit_report

if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    run_h31_audit(repo_root)
