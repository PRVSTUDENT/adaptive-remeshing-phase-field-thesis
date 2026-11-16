# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1816_step1_master.py
===========================================
Master driver for Task F1816 Step 1:
Executes Cases 1, 2, 3, 5 under native Abaqus MINIMUM_MAXIMUM sizing.
Compiles step1_minmax_summary.json and prints comparison against F1812 baseline.
"""
from __future__ import print_function
import os
import sys
import subprocess
import json
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STEP1_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1816_step1_minmax.py")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "263_f1816_multistep_narrowing", "step1_minmax")
ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

CASES = ["case_1", "case_2", "case_3", "case_5"]

def main():
    print("=" * 80)
    print("TASK F1816 STEP 1: MINIMUM/MAXIMUM SIZING METHOD INVESTIGATION")
    print("  eta_max = 1%, eta_min = 5%, mesh_bias = 7 (default strong)")
    print("  Output dir:", OUT_DIR)
    print("=" * 80)

    summary = {
        "step": 1,
        "sizing_method": "MINIMUM_MAXIMUM",
        "parameters": {
            "eta_max_pct": 1.0,
            "eta_min_pct": 5.0,
            "mesh_bias": 7
        },
        "cases": {}
    }

    t0_global = time.time()

    for cid in CASES:
        print("\n>>> Launching Abaqus CAE for %s..." % cid)
        cmd = [
            ABAQUS_BAT, "cae",
            "noGUI=%s" % STEP1_SCRIPT,
            "--",
            cid,
            OUT_DIR
        ]
        t0 = time.time()
        ret = subprocess.call(cmd, cwd=REPO_ROOT)
        t_el = time.time() - t0
        print("<<< %s finished in %.2f s (Exit: %d)" % (cid, t_el, ret))
        if ret != 0:
            raise RuntimeError("Step 1 failed for %s with exit code %d" % (cid, ret))

        receipt_file = os.path.join(OUT_DIR, "step1_receipt_" + cid + ".json")
        if not os.path.exists(receipt_file):
            raise RuntimeError("Missing receipt for %s: %s" % (cid, receipt_file))

        with open(receipt_file, "r") as f:
            summary["cases"][cid] = json.load(f)

    summary_path = os.path.join(OUT_DIR, "step1_minmax_summary.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)

    total_el = sum(summary["cases"][c]["total_elements"] for c in CASES)
    total_dofs = sum(summary["cases"][c]["nominal_field_dofs"] for c in CASES)

    print("\n" + "=" * 80)
    print("STEP 1 COMPLETE ACROSS ALL FOUR BENCHMARKS (Total Time: %.2f s)" % (time.time() - t0_global))
    print("Total Elements: %d, Total DOFs: %d" % (total_el, total_dofs))
    print("=" * 80)

    # Print comparative table
    print("\n| Case | Mesh Elements | Quad % | Max AR | Gate 06 | Scientific Gate | Gate Status | Fine El (<=l0/2) | % <= 3*l0 |")
    print("| :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |")
    for cid in CASES:
        c = summary["cases"][cid]
        wm = c["width_metrics"]
        print("| %s | %d | %.2f%% | %.2f | %.2fx (%s) | %s = %.2f%% | %s | %d | %.2f%% |" % (
            cid,
            c["total_elements"],
            c["quad_fraction_pct"],
            c["max_aspect_ratio"],
            c["coarsening_ratio"],
            c["gates"]["GATE_06_FAR_FIELD_COARSENING"],
            c["scientific_gate_name"],
            c["scientific_gate_value"],
            c["scientific_gate_status"],
            wm["fine_elements_count"],
            wm["pct_within_3l0"]
        ))

if __name__ == "__main__":
    main()
