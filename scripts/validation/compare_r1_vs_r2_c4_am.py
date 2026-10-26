#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compare_r1_vs_r2_c4_am.py
Compare Package 110 R1 (defective intra-step history accumulation) vs
Package 110 R2 (step-frozen committed history).
"""

from __future__ import print_function, division
import os
import sys
import json
import numpy as np

REPO_DIR = r"D:\Master thesis\Adaptive remeshing"
R1_SUMMARY = os.path.join(REPO_DIR, "results", "validation", "c4_am_dynamic_continuation_summary_1417610.json")
R2_SUMMARY = os.path.join(REPO_DIR, "results", "validation", "c4_am_step_frozen_history_summary.json")

def compare():
    with open(R1_SUMMARY, "r") as f:
        r1_data = json.load(f)
    with open(R2_SUMMARY, "r") as f:
        r2_data = json.load(f)

    r1_hist = r1_data["history"]
    r2_hist = r2_data["history"]

    print("=" * 100)
    print("COMPARISON: PACKAGE 110 R1 (ACCUMULATED HISTORY) vs PACKAGE 110 R2 (STEP-FROZEN COMMITTED HISTORY)")
    print("=" * 100)
    print("%-6s | %-16s %-16s | %-16s %-16s | %-12s %-12s" %
          ("Cyc", "R1 RF2 (N)", "R2 RF2 (N)", "R1 d_max", "R2 d_max", "R1 max_dd", "R2 max_dd"))
    print("-" * 100)

    for i in range(15):
        c1 = r1_hist[i]
        c2 = r2_hist[i]
        cyc = c1["cycle"]
        print("%-6d | %-16.4f %-16.4f | %-16.4f %-16.4f | %-12.6f %-12.6f" %
              (cyc, c1["rf2_rp_N"], c2["rf2_rp_N"], c1["d_max"], c2["d_max"], c1["max_delta_d"], c2["max_delta_d"]))

    print("\n" + "=" * 100)
    print("ENERGY EVOLUTION (R2 with step-frozen history):")
    print("=" * 100)
    print("%-6s | %-14s %-14s %-14s | %-14s %-14s %-14s" %
          ("Cyc", "E_elas (mJ)", "E_frac (mJ)", "E_tot (mJ)", "dE_tot (mJ)", "Free Res (kN/mm)", "KKT Viol"))
    print("-" * 100)
    prev_etot = None
    for i in range(15):
        c = r2_hist[i]
        detot = (c["e_tot_mJ"] - prev_etot) if prev_etot is not None else 0.0
        prev_etot = c["e_tot_mJ"]
        print("%-6d | %-14.6f %-14.6f %-14.6f | %-14.6f %-14.2e %-14d" %
              (c["cycle"], c["e_elas_mJ"], c["e_frac_mJ"], c["e_tot_mJ"], detot, c.get("free_residual_max_kN_mm", 0.0), c["kkt_violations"]))

if __name__ == "__main__":
    compare()
