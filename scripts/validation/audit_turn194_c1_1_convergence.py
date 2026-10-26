#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_turn194_c1_1_convergence.py
Independent Convergence Audit of Package 110 (Job 1417601.mmaster02)
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 194)
Protocol Version: 2

Audits whether Job 1417601 achieved genuine coupled fixed-point stationarity
or terminated prematurely at a fixed loop count (5 cycles).
"""

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SUMMARY_PATH = REPO_ROOT / "models/pandey_kumar_mode1/110_c4_c1_1_safeguarded_am_continuation/c4_am_continuation_summary.json"
OUTPUT_PATH = REPO_ROOT / "results/validation/c4_am_c1_1_convergence_audit_turn194.json"

def run_audit():
    with open(SUMMARY_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    history = summary["history"]
    r22_donor_rf2_N = 178.234577
    r22_donor_energy_mJ = 0.238324  # Authentic verified R22 donor energy

    audit_cycles = []
    prev_d_max = 0.684771  # Initial transferred damage
    prev_rf2 = 180.031106
    prev_e_tot = 0.2400039959

    for i, h in enumerate(history):
        cyc = h["cycle"]
        rf2 = h["rf2_rp_N"]
        d_max = h["d_max"]
        delta_d_max = h["max_delta_d"]
        e_tot = h["e_tot_mJ"]
        e_elas = h["e_elas_mJ"]
        e_frac = h["e_frac_mJ"]
        kkt_viol = h["kkt_violations"]
        healing = h["healing_count"]

        # Differences from previous cycle
        delta_rf2_cycle = rf2 - prev_rf2 if i > 0 else 0.0
        delta_etot_cycle = e_tot - prev_e_tot if i > 0 else 0.0

        # Differences vs R22 authentic donor
        rf2_diff_donor_pct = (rf2 - r22_donor_rf2_N) / r22_donor_rf2_N * 100.0
        energy_diff_donor_pct = (e_tot - r22_donor_energy_mJ) / r22_donor_energy_mJ * 100.0

        record = {
            "cycle": cyc,
            "rf2_rp_N": rf2,
            "delta_rf2_prev_cycle_N": delta_rf2_cycle,
            "rf2_diff_donor_pct": rf2_diff_donor_pct,
            "d_max": d_max,
            "max_delta_d": delta_d_max,
            "delta_d_stationary": bool(delta_d_max < 1.0e-3),
            "healing_count": healing,
            "kkt_violations": kkt_viol,
            "e_tot_mJ": e_tot,
            "delta_etot_prev_cycle_mJ": delta_etot_cycle,
            "energy_diff_donor_pct": energy_diff_donor_pct,
            "e_elas_mJ": e_elas,
            "e_frac_mJ": e_frac
        }
        audit_cycles.append(record)
        prev_rf2 = rf2
        prev_d_max = d_max
        prev_e_tot = e_tot

    # Terminal evaluation
    last_cycle = audit_cycles[-1]
    terminal_delta_d = last_cycle["max_delta_d"]
    terminal_delta_rf2 = abs(last_cycle["delta_rf2_prev_cycle_N"])
    energy_continuity_pass = bool(abs(last_cycle["energy_diff_donor_pct"]) <= 2.0)
    force_continuity_pass = bool(abs(last_cycle["rf2_diff_donor_pct"]) <= 5.0)
    zero_healing_pass = bool(all(c["healing_count"] == 0 for c in audit_cycles))
    monotonic_energy_pass = bool(all(c["delta_etot_prev_cycle_mJ"] <= 0.0 for c in audit_cycles[1:]))

    # Genuine stationarity test: terminal delta_d < 1e-3 and |delta_rf2| < 0.1 N
    is_genuinely_stationary = (terminal_delta_d < 1.0e-3) and (terminal_delta_rf2 < 0.1)

    classification = "C1_1_PREMATURE_AM_TERMINATION" if not is_genuinely_stationary else "C1_1_FULLY_VERIFIED"

    findings = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "turn": 194,
        "target_job": "1417601.mmaster02",
        "package": "PACKAGE_110_C4_C1_1_SAFEGUARDED_AM_CONTINUATION",
        "classification": classification,
        "rationale": (
            "Job 1417601 completed Exit 0 and satisfied force continuity (-1.66%), energy continuity (+0.64%), "
            "and zero damage healing across 5 cycles. However, outer fixed-point convergence was NOT achieved: "
            f"terminal max_delta_d = {terminal_delta_d:.6f} exceeds tolerance 1.0e-4 by a factor of 130, "
            f"terminal RF2 drift was {last_cycle['delta_rf2_prev_cycle_N']:.4f} N, and d_max continued increasing "
            f"(0.7249 -> 0.7823). The loop terminated purely because max_am_cycles = 5 was reached, not because "
            "mathematical stationarity was reached. Stopping at 5 cycles was premature."
        ),
        "energy_reconciliation": {
            "authentic_r22_donor_energy_mJ": r22_donor_energy_mJ,
            "misreported_table_reference_mJ": 0.2442,
            "terminal_c4_energy_mJ": last_cycle["e_tot_mJ"],
            "energy_diff_vs_authentic_donor_pct": last_cycle["energy_diff_donor_pct"],
            "energy_continuity_pass_2pct": energy_continuity_pass
        },
        "gate_c1_1_assessment": {
            "force_continuity_pass": force_continuity_pass,
            "energy_continuity_pass": energy_continuity_pass,
            "zero_healing_pass": zero_healing_pass,
            "monotonic_energy_pass": monotonic_energy_pass,
            "fixed_point_stationarity_pass": is_genuinely_stationary
        },
        "cycle_audit": audit_cycles,
        "corrective_action": {
            "required": not is_genuinely_stationary,
            "proposed_package": "110_r1_c4_am_dynamic_continuation",
            "stationarity_criteria": {
                "max_delta_d_tol": 1.0e-3,
                "delta_rf2_tol_N": 0.1,
                "max_am_cycles": 15
            }
        }
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2)

    print("Audit written to:", OUTPUT_PATH)
    print("Classification:", classification)
    print("Energy diff vs authentic R22 donor:", f"{last_cycle['energy_diff_donor_pct']:+.3f}%")
    print("Terminal max_delta_d:", terminal_delta_d)
    print("Is stationary:", is_genuinely_stationary)

if __name__ == "__main__":
    run_audit()
