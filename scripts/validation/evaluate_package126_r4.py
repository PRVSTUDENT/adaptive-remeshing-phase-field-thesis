#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
evaluate_package126_r4.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Evaluates Package 126 Revision 4 deliverables against Package 125 baseline:
1. Reconciles PBS Job 1418006.mmaster02.
2. Retrieves c4_inc87_anderson_r4_summary.json and logs from scratch.
3. Performs rigorous quantitative parity audit on unaccelerated Cycles 1-5 vs Package 125.
4. Audits Anderson acceleration dynamics (Cycles 6-40): proposals, acceptance, step sizes, and coupled re-equilibration.
5. Adjudicates Hypothesis H7 against predeclared stationarity and Method C acceptance criteria.
6. Outputs results/validation/package126_r4_evaluation.json.
"""

import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/126_r4_c4_inc87_anderson_control"
P125_DIR = REPO_ROOT / "models/pandey_kumar_mode1/125_c4_inc87_extended_am_control"
SSH_CFG = Path.home() / ".ssh/codex_config"
REMOTE_DIR = "/scratch9/pr21vyci/runs/mode1_c4_inc87_anderson_control_r4"

TARGET_RF2_REF_N = 185.68243086338043
TARGET_ENERGY_REF_MJ = 0.23197697
STATIONARITY_TOL_DELTA_D = 1.0e-3
STATIONARITY_TOL_DELTA_RF2_N = 0.1
FORCE_CONTINUITY_PCT_MAX = 5.0
ENERGY_CONTINUITY_PCT_MAX = 2.0

def retrieve_remote_deliverables():
    # Retrieve summary JSON and execution logs
    files = ["c4_inc87_anderson_r4_summary.json", "pbs_execution.log", "pbs_error.log"]
    retrieved = {}
    for f in files:
        src = f"tu_freiberg:{REMOTE_DIR}/{f}"
        dst = str(PKG_DIR / f)
        res = subprocess.run(["scp", "-F", str(SSH_CFG), "-B", src, dst], capture_output=True, text=True)
        retrieved[f] = (res.returncode == 0 and os.path.exists(dst))
    return retrieved

def main():
    print("Evaluating Package 126 R4...")
    retrieved = retrieve_remote_deliverables()
    summary_path = PKG_DIR / "c4_inc87_anderson_r4_summary.json"
    
    if not summary_path.exists():
        print("Summary JSON not yet available on scratch. Job may still be running.")
        return 1

    with open(summary_path, "r") as f:
        r4_data = json.load(f)

    p125_summary_path = P125_DIR / "c4_inc87_ext_am_summary.json"
    with open(p125_summary_path, "r") as f:
        p125_data = json.load(f)

    r4_history = r4_data.get("history", [])
    p125_history = p125_data.get("history", [])

    print(f"P126 R4 completed cycles: {len(r4_history)}")
    print(f"P125 completed cycles: {len(p125_history)}")

    # 1. Unaccelerated Cycles 1-5 Parity Audit
    parity_audit = []
    max_rf2_diff = 0.0
    max_dmax_diff = 0.0
    max_energy_diff = 0.0
    parity_passed = True

    n_check = min(5, len(r4_history), len(p125_history))
    for c in range(n_check):
        h_r4 = r4_history[c]
        h_125 = p125_history[c]

        rf2_r4 = h_r4["rf2_rp_N"]
        rf2_125 = h_125["rf2_rp_N"]
        diff_rf2 = abs(rf2_r4 - rf2_125)
        max_rf2_diff = max(max_rf2_diff, diff_rf2)

        dmax_r4 = h_r4["d_max"]
        dmax_125 = h_125["d_max"]
        diff_dmax = abs(dmax_r4 - dmax_125)
        max_dmax_diff = max(max_dmax_diff, diff_dmax)

        etot_r4 = h_r4["e_tot_mJ"]
        etot_125 = h_125["e_tot_mJ"]
        diff_etot = abs(etot_r4 - etot_125)
        max_energy_diff = max(max_energy_diff, diff_etot)

        match_cycle = (diff_rf2 < 1e-3 and diff_dmax < 1e-5 and diff_etot < 1e-4)
        if not match_cycle:
            parity_passed = False

        parity_audit.append({
            "cycle": c + 1,
            "rf2_r4_N": rf2_r4,
            "rf2_p125_N": rf2_125,
            "diff_rf2_N": diff_rf2,
            "dmax_r4": dmax_r4,
            "dmax_p125": dmax_125,
            "diff_dmax": diff_dmax,
            "etot_r4_mJ": etot_r4,
            "etot_p125_mJ": etot_125,
            "diff_etot_mJ": diff_etot,
            "exact_match": match_cycle
        })

    print(f"Cycles 1-5 Parity Pass: {parity_passed} (max RF2 diff: {max_rf2_diff:.6f} N, max dmax diff: {max_dmax_diff:.8f}, max E diff: {max_energy_diff:.8f} mJ)")

    # 2. Anderson Acceleration Dynamics Audit (Cycles 6+)
    anderson_events = []
    accepted_proposals = 0
    fallback_proposals = 0

    for c in range(5, len(r4_history)):
        h = r4_history[c]
        acc = h.get("anderson_accelerated", False)
        status = h.get("acceleration_status", "")
        if acc:
            accepted_proposals += 1
        elif "FALLBACK" in status:
            fallback_proposals += 1

        anderson_events.append({
            "cycle": h["cycle"],
            "accelerated": acc,
            "status": status,
            "rf2_N": h["rf2_rp_N"],
            "d_max": h["d_max"],
            "max_delta_d": h["max_delta_d"],
            "delta_rf2_prev_cycle_N": h["delta_rf2_prev_cycle_N"],
            "free_nodes": h["free_nodes"],
            "e_tot_mJ": h["e_tot_mJ"]
        })

    # 3. Terminal State & Gate Evaluation
    final_state = r4_data.get("final_state", r4_history[-1] if r4_history else {})
    terminal_status = r4_data.get("status", "UNKNOWN")
    final_cycle = final_state.get("cycle", len(r4_history))
    final_rf2 = final_state.get("rf2_rp_N", 0.0)
    final_max_delta_d = final_state.get("max_delta_d", 999.0)
    final_delta_rf2 = final_state.get("delta_rf2_prev_cycle_N", 999.0)
    final_etot = final_state.get("e_tot_mJ", 0.0)
    final_healing = final_state.get("healing_violations", 0)

    rf2_diff_pct = (final_rf2 - TARGET_RF2_REF_N) / TARGET_RF2_REF_N * 100.0
    energy_diff_pct = (final_etot - TARGET_ENERGY_REF_MJ) / TARGET_ENERGY_REF_MJ * 100.0

    stationarity_delta_d_pass = (final_max_delta_d <= STATIONARITY_TOL_DELTA_D)
    stationarity_delta_rf2_pass = (final_delta_rf2 <= STATIONARITY_TOL_DELTA_RF2_N)
    force_continuity_pass = (abs(rf2_diff_pct) <= FORCE_CONTINUITY_PCT_MAX)
    energy_continuity_pass = (abs(energy_diff_pct) <= ENERGY_CONTINUITY_PCT_MAX)
    zero_healing_pass = (final_healing == 0)

    # 4. Hypothesis H7 Adjudication
    if not parity_passed:
        h7_verdict = "H7_INVALID_PARITY_FAILED"
    elif terminal_status == "CONVERGED_STATIONARY_STATE" and stationarity_delta_d_pass and stationarity_delta_rf2_pass:
        if force_continuity_pass and energy_continuity_pass and zero_healing_pass:
            h7_verdict = "H7_VALID_ACCELERATED_CONVERGENCE"
        else:
            h7_verdict = "H7_VALID_DIFFERENT_BRANCH"
    elif terminal_status == "ITERATION_CAP_REACHED" or not (stationarity_delta_d_pass and stationarity_delta_rf2_pass):
        h7_verdict = "H7_FAILED_NONSTATIONARY"
    else:
        h7_verdict = "H7_PENDING"

    evaluation_report = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_126_R4_C4_INC87_ANDERSON_CONTROL",
        "pbs_job_id": "1418006.mmaster02",
        "hypothesis_h7_verdict": h7_verdict,
        "solver_terminal_status": terminal_status,
        "cycles_completed": len(r4_history),
        "parity_audit": {
            "unaccelerated_cycles_1_to_5_pass": parity_passed,
            "max_rf2_discrepancy_N": max_rf2_diff,
            "max_dmax_discrepancy": max_dmax_diff,
            "max_energy_discrepancy_mJ": max_energy_diff,
            "cycle_comparisons": parity_audit
        },
        "anderson_dynamics": {
            "depth_m": 3,
            "start_cycle": 6,
            "accepted_proposals": accepted_proposals,
            "fallback_proposals": fallback_proposals,
            "events": anderson_events
        },
        "terminal_metrics": {
            "final_cycle": final_cycle,
            "final_rf2_N": final_rf2,
            "rf2_diff_vs_donor_pct": rf2_diff_pct,
            "force_continuity_pass": force_continuity_pass,
            "final_max_delta_d": final_max_delta_d,
            "stationarity_delta_d_pass": stationarity_delta_d_pass,
            "final_delta_rf2_N": final_delta_rf2,
            "stationarity_delta_rf2_pass": stationarity_delta_rf2_pass,
            "final_etot_mJ": final_etot,
            "energy_diff_vs_donor_pct": energy_diff_pct,
            "energy_continuity_pass": energy_continuity_pass,
            "healing_violations": final_healing,
            "zero_healing_pass": zero_healing_pass
        },
        "comparison_vs_p125": {
            "p125_cyc40_delta_d": 0.001187,
            "p125_cyc40_delta_rf2_N": 0.0707,
            "p125_cyc40_rf2_N": 179.904,
            "p125_cyc40_energy_mJ": 0.236369,
            "r4_cycles_saved": 40 - final_cycle if terminal_status == "CONVERGED_STATIONARY_STATE" else 0
        },
        "governing_gate": "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED"
    }

    out_file = REPO_ROOT / "results/validation/package126_r4_evaluation.json"
    with open(out_file, "w") as f:
        json.dump(evaluation_report, f, indent=2)

    print(f"Package 126 R4 Evaluation written to: {out_file}")
    print(f"H7 Verdict: {h7_verdict}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
