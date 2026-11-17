# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1846_four_case_regression.py
==================================================
Executes the four-benchmark regression check (Cases 1, 2, 3, 5) using the
generalized framework scripts/remeshing/generalized_2d_adaptive_framework_f1846.py
from existing donors (0 new PBS jobs) and evaluates element counts and resolution
against the F1812 baselines (25,461 / 41,438 / 77,779 / 15,466).
"""

from __future__ import print_function
import os
import sys
import json
import subprocess
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

REGRESSION_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "276_f1846_generalized_framework", "regression")
SINGLE_CASE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1846_single_case.py")

CASES = [
    {
        "cid": "case_1",
        "name": "Case 1: Mode-I Edge-Cracked Plate",
        "config": os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json"),
        "donor": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb"),
        "f1812_baseline_elements": 25461,
        "error_target": 4.5,
        "l0_mm": 0.0075
    },
    {
        "cid": "case_2",
        "name": "Case 2: Mode-I Plate with Off-Axis Hole",
        "config": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
        "donor": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2", "PK_HOLE_MULTISTATE_RECOVERY.odb"),
        "f1812_baseline_elements": 41438,
        "error_target": 4.0,
        "l0_mm": 0.0075
    },
    {
        "cid": "case_3",
        "name": "Case 3: Notched Plate with Hole and Pins",
        "config": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
        "donor": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3", "SEC43_MULTISTATE_RECOVERY.odb"),
        "f1812_baseline_elements": 77779,
        "error_target": 3.0,
        "l0_mm": 0.285
    },
    {
        "cid": "case_5",
        "name": "Case 5: Plate with Seven Holes",
        "config": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
        "donor": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
        "f1812_baseline_elements": 15466,
        "error_target": 5.68,
        "l0_mm": 0.0080
    }
]

def main():
    if not os.path.exists(REGRESSION_DIR):
        os.makedirs(REGRESSION_DIR)

    results = {}
    print("=" * 80)
    print("TASK F1846: GENERALIZED FRAMEWORK FOUR-BENCHMARK REGRESSION CHECK")
    print("=" * 80)

    for c in CASES:
        cid = c["cid"]
        case_out_dir = os.path.join(REGRESSION_DIR, cid)
        if not os.path.exists(case_out_dir):
            os.makedirs(case_out_dir)

        print("\n--- Running %s ---" % c["name"])
        print("  Config: %s" % c["config"])
        print("  Donor:  %s" % c["donor"])
        print("  Error target: %.2f%%" % c["error_target"])

        cmd = [
            ABAQUS_BAT, "cae",
            "noGUI=%s" % SINGLE_CASE_SCRIPT,
            "--",
            c["config"],
            c["donor"],
            case_out_dir,
            str(c["error_target"])
        ]

        t0 = time.time()
        ret = subprocess.call(cmd, cwd=REPO_ROOT)
        t_el = time.time() - t0
        print("Finished %s in %.2f s (Exit: %d)" % (cid, t_el, ret))

        audit_json = os.path.join(case_out_dir, "PK_F1846_" + cid.upper() + "_AUDIT.json")
        if not os.path.exists(audit_json):
            raise RuntimeError("Audit JSON missing for %s at %s" % (cid, audit_json))

        with open(audit_json, "r") as f:
            audit_data = json.load(f)

        n_elem = audit_data["total_physical_elements"]
        n_base = c["f1812_baseline_elements"]
        delta_pct = 100.0 * (n_elem - n_base) / float(n_base)

        results[cid] = {
            "name": c["name"],
            "f1812_baseline": n_base,
            "f1846_elements": n_elem,
            "delta_elements": n_elem - n_base,
            "delta_pct": delta_pct,
            "quad_percent": audit_data["quad_percent"],
            "min_det_j": audit_data["min_det_j"],
            "max_aspect_ratio": audit_data["max_aspect_ratio"],
            "refinement_ratio": audit_data["refinement_ratio_far_to_core"],
            "elements_le_l0": audit_data["elements_le_l0"],
            "pct_elements_le_l0": audit_data["pct_elements_le_l0"],
            "sizing_driver": audit_data.get("sizing_driver", "UNKNOWN"),
            "sizing_provenance": audit_data.get("sizing_provenance", "UNKNOWN"),
            "audit_json": audit_json,
            "physical_mesh": os.path.join(case_out_dir, "PK_F1846_" + cid.upper() + "_ADAPT_PHYS.inp")
        }

        print("  Results for %s:" % cid)
        print("    Elements: F1812 = %d  -->  F1846 = %d (Delta: %+d, %+.2f%%)" % (n_base, n_elem, n_elem - n_base, delta_pct))
        print("    Quad Fraction: %.2f%%" % audit_data["quad_percent"])
        print("    Min det(J):    %.3e" % audit_data["min_det_j"])
        print("    Max AR:        %.2f" % audit_data["max_aspect_ratio"])
        print("    Sizing Driver: %s (%s)" % (results[cid]["sizing_driver"], results[cid]["sizing_provenance"]))

    summary_file = os.path.join(REPO_ROOT, "results", "validation", "f1846_four_benchmark_regression_summary.json")
    with open(summary_file, "w") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print("FOUR-BENCHMARK REGRESSION COMPLETE")
    print("Summary written to: %s" % summary_file)
    print("=" * 80)

if __name__ == '__main__':
    main()
