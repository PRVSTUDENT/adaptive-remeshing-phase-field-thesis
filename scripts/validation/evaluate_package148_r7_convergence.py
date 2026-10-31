#!/usr/bin/env python3
"""
scripts/validation/evaluate_package148_r7_convergence.py
Quantitative contraction rate, stagnation, roundoff, and iteration prediction analysis
for Package 148 Revision 7 (PBS 1418938.mmaster02) outer iterations.
"""
from __future__ import print_function, division
import json
import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

def analyze_r7_convergence(report_path=None):
    if report_path is None:
        report_path = REPO_ROOT / "results" / "validation" / "package148" / "r7_runtime_report.json"

    with open(str(report_path), "r") as f:
        data = json.load(f)

    iterations = data["iterations"]
    print("Total iterations recorded:", len(iterations))

    # Table of last 10 iterations (outer 16 to 25)
    print("\n--- LAST 10 ITERATIONS (16 to 25) ---")
    print("{:<6} {:<15} {:<15} {:<15} {:<12} {:<12} {:<6}".format(
        "Outer", "Delta_d", "Delta_u (mm)", "Delta_h (MPa)", "Free Error", "Dual Error", "Inner"
    ))
    last_10 = iterations[-10:]
    for it in last_10:
        print("{:<6d} {:<15.8e} {:<15.8e} {:<15.8e} {:<12.4e} {:<12.4e} {:<6}".format(
            it["outer"],
            it["delta_d"],
            it["delta_u"] if it["delta_u"] is not None else 0.0,
            it["delta_h"] if it["delta_h"] is not None else 0.0,
            it["free_error"],
            it["dual_error"],
            it.get("phase_iterations", 1)
        ))

    # Contraction factors
    print("\n--- CONTRACTION FACTORS (Iteration k / Iteration k-1) ---")
    print("{:<10} {:<15} {:<15} {:<15}".format("Transition", "rho(Delta_d)", "rho(Delta_u)", "rho(Delta_h)"))
    rho_d_list = []
    rho_u_list = []
    rho_h_list = []
    for i in range(len(last_10) - 1):
        prev = last_10[i]
        curr = last_10[i+1]
        trans = "%d -> %d" % (prev["outer"], curr["outer"])
        rho_d = curr["delta_d"] / prev["delta_d"]
        rho_u = curr["delta_u"] / prev["delta_u"] if prev["delta_u"] else 0.0
        rho_h = curr["delta_h"] / prev["delta_h"] if prev["delta_h"] else 0.0
        rho_d_list.append(rho_d)
        rho_u_list.append(rho_u)
        rho_h_list.append(rho_h)
        print("{:<10} {:<15.4f} {:<15.4f} {:<15.4f}".format(trans, rho_d, rho_u, rho_h))

    # Overall geometric means over last 9 transitions (outer 16 to 25)
    geom_rho_d = (last_10[-1]["delta_d"] / last_10[0]["delta_d"]) ** (1.0 / (len(last_10) - 1))
    geom_rho_u = (last_10[-1]["delta_u"] / last_10[0]["delta_u"]) ** (1.0 / (len(last_10) - 1))
    geom_rho_h = (last_10[-1]["delta_h"] / last_10[0]["delta_h"]) ** (1.0 / (len(last_10) - 1))

    # Over last 5 transitions (outer 20 to 25)
    last_5 = iterations[-5:]
    geom_rho_h_last5 = (last_5[-1]["delta_h"] / last_5[0]["delta_h"]) ** (1.0 / (len(last_5) - 1))
    max_rho_h_last5 = max(rho_h_list[-4:])
    min_rho_h_last5 = min(rho_h_list[-4:])

    print("\nGeometric mean contraction factor over outer 16..25:")
    print("  rho_geom(Delta_d): {:.4f}".format(geom_rho_d))
    print("  rho_geom(Delta_u): {:.4f}".format(geom_rho_u))
    print("  rho_geom(Delta_h): {:.4f}".format(geom_rho_h))
    print("Geometric mean contraction factor over outer 20..25 (Delta_h): {:.4f}".format(geom_rho_h_last5))
    print("Max rho(Delta_h) in last 5 iterations: {:.4f}".format(max_rho_h_last5))
    print("Min rho(Delta_h) in last 5 iterations: {:.4f}".format(min_rho_h_last5))

    # Stagnation and roundoff check
    print("\n--- STAGNATION & ROUNDOFF ANALYSIS ---")
    delta_u_24 = iterations[-2]["delta_u"]
    delta_u_25 = iterations[-1]["delta_u"]
    print("delta_u at iter 24: {:.8e} mm".format(delta_u_24))
    print("delta_u at iter 25: {:.8e} mm".format(delta_u_25))
    if delta_u_24 == delta_u_25:
        print("Note: delta_u reached 2.32830644e-10 mm (~2^-32 or single/double float limit in reporting/diff).")
        print("Displacement update is completely stagnant at ~0.23 picometers (tolerance is 1.0e-9 mm = 1 picometer).")

    # Prediction for Delta_h <= 1.0e-6 MPa
    dh_25 = iterations[-1]["delta_h"]
    target_dh = 1.0e-6
    print("\n--- PREDICTION FOR Delta_h <= 1.0e-6 MPa ---")
    print("Starting Delta_h at iter 25: {:.6e} MPa".format(dh_25))
    print("Target Delta_h: {:.6e} MPa".format(target_dh))

    # Model 1: Average geometric contraction over outer 16..25 (rho = 0.6845)
    n_geom = math.log(target_dh / dh_25) / math.log(geom_rho_h)
    print("Using 9-iteration geometric mean rho = {:.4f}: n = {:.2f} iterations (Iteration {:.1f})".format(
        geom_rho_h, n_geom, 25 + n_geom
    ))

    # Model 2: Geometric contraction over outer 20..25 (rho = 0.6980)
    n_geom5 = math.log(target_dh / dh_25) / math.log(geom_rho_h_last5)
    print("Using 5-iteration geometric mean rho = {:.4f}: n = {:.2f} iterations (Iteration {:.1f})".format(
        geom_rho_h_last5, n_geom5, 25 + n_geom5
    ))

    # Model 3: Conservative worst-case rho over last 3 transitions (rho = 0.8546 from 24->25)
    rho_conservative = rho_h_list[-1]
    n_cons = math.log(target_dh / dh_25) / math.log(rho_conservative)
    print("Using conservative last-step rho = {:.4f}: n = {:.2f} iterations (Iteration {:.1f})".format(
        rho_conservative, n_cons, 25 + n_cons
    ))

    # Step-by-step projection using both rates:
    print("\nProjected Delta_h by iteration:")
    for k in range(26, 38):
        steps = k - 25
        pred_geom = dh_25 * (geom_rho_h ** steps)
        pred_geom5 = dh_25 * (geom_rho_h_last5 ** steps)
        pred_cons = dh_25 * (rho_conservative ** steps)
        status_geom = "PASS" if pred_geom <= target_dh else "FAIL"
        status_cons = "PASS" if pred_cons <= target_dh else "FAIL"
        print("  Iter {:2d}: geom9={:.4e} ({}) | geom5={:.4e} | cons(0.85)={:.4e} ({})".format(
            k, pred_geom, status_geom, pred_geom5, pred_cons, status_cons
        ))

    # Evaluation of whether 30 outer iterations is sufficient:
    print("\n--- SUFFICIENCY OF max_outer = 30 ---")
    dh_at_30_geom = dh_25 * (geom_rho_h ** 5)
    dh_at_30_geom5 = dh_25 * (geom_rho_h_last5 ** 5)
    dh_at_30_cons = dh_25 * (rho_conservative ** 5)
    print("At iteration 30 (5 more iterations beyond 25):")
    print("  Using 9-iteration geometric rho ({:.4f}): Delta_h = {:.4e} MPa (Threshold 1.0e-6 -> {})".format(
        geom_rho_h, dh_at_30_geom, "FAIL" if dh_at_30_geom > target_dh else "PASS"
    ))
    print("  Using 5-iteration geometric rho ({:.4f}): Delta_h = {:.4e} MPa (Threshold 1.0e-6 -> {})".format(
        geom_rho_h_last5, dh_at_30_geom5, "FAIL" if dh_at_30_geom5 > target_dh else "PASS"
    ))
    print("  Using conservative rho ({:.4f}): Delta_h = {:.4e} MPa (Threshold 1.0e-6 -> {})".format(
        rho_conservative, dh_at_30_cons, "FAIL" if dh_at_30_cons > target_dh else "PASS"
    ))

    return {
        "last_10": last_10,
        "rho_h_list": rho_h_list,
        "geom_rho_h": geom_rho_h,
        "geom_rho_h_last5": geom_rho_h_last5,
        "rho_conservative": rho_conservative,
        "dh_25": dh_25,
        "target_dh": target_dh,
        "n_geom": n_geom,
        "n_geom5": n_geom5,
        "n_cons": n_cons,
        "dh_at_30_geom": dh_at_30_geom,
        "dh_at_30_geom5": dh_at_30_geom5,
        "dh_at_30_cons": dh_at_30_cons
    }

if __name__ == "__main__":
    analyze_r7_convergence()
