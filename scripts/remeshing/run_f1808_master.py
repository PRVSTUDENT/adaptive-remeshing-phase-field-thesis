# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1808_master.py
====================================
Orchestrates fresh, isolated execution of all four canonical benchmarks:
Cases 1, 2, 3, and 5 for Task F1808.
Each benchmark runs in its own independent Abaqus CAE process via run_f1808_single_case.py.
Collects and reconciles all four case receipts into:
models/pandey_kumar_mode1/258_f1808_four_case_reproducibility/PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json
"""
from __future__ import print_function
import os
import sys
import subprocess
import json
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
BASE_OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "258_f1808_four_case_reproducibility")
SINGLE_CASE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1808_single_case.py")

ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

if not os.path.exists(BASE_OUT_DIR):
    os.makedirs(BASE_OUT_DIR)

cases = ["case_1", "case_2", "case_3", "case_5"]

def main():
    print("=" * 80)
    print("TASK F1808: FOUR-CASE NATIVE-MISESERI REPRODUCIBILITY & REGRESSION MASTER")
    print("Sequential isolated execution of Cases 1, 2, 3, 5")
    print("=" * 80)

    t_start = time.time()
    execution_receipts = {}

    for cid in cases:
        print("\n>>> Launching fresh Abaqus CAE session for %s ..." % cid)
        cmd = [ABAQUS_BAT, "cae", "noGUI=%s" % SINGLE_CASE_SCRIPT, "--", cid]
        print("    Command: %s" % " ".join(cmd))
        t0 = time.time()
        ret = subprocess.call(cmd, cwd=REPO_ROOT)
        t_el = time.time() - t0
        print("<<< %s finished in %.2f s with exit code %d" % (cid, t_el, ret))
        if ret != 0:
            raise RuntimeError("Case execution failed for %s with exit code %d" % (cid, ret))

        c_dir = cid.replace("_", "")
        receipt_path = os.path.join(BASE_OUT_DIR, c_dir, "PK_F1808_%s_RECEIPT.json" % cid.upper())
        if not os.path.exists(receipt_path):
            raise RuntimeError("Missing receipt file: %s" % receipt_path)

        with open(receipt_path, "r") as f:
            execution_receipts[cid] = json.load(f)

    # Compile master four-case receipt
    master_receipt = {
        "task_id": "F1808-FOUR-CASE-NATIVE-MISESERI-REPRODUCIBILITY-AND-REGRESSION",
        "title": "Task F1808: Four-Case Native-MISESERI Reproducibility Investigation and Regression Audit (Cases 1, 2, 3, 5)",
        "protocol": "INDEPENDENT_STRUCTURED_REVIEW_V1",
        "correlation_id": "HND-F1808-FOUR-CASE-REPRODUCIBILITY-001",
        "timestamp_iso": time.strftime("%Y-%m-%dT%H:%M:%S+01:00"),
        "total_walltime_s": time.time() - t_start,
        "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6",
        "shared_framework_sha256": "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D",
        "cumulative_pbs_submissions": 35,
        "new_pbs_submissions": 0,
        "master_goal_status": "OPEN",
        "cases": execution_receipts
    }

    master_path = os.path.join(BASE_OUT_DIR, "PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json")
    with open(master_path, "w") as f:
        json.dump(master_receipt, f, indent=2)
    print("\n" + "=" * 80)
    print("MASTER RECEIPT SAVED: %s" % master_path)
    print("=" * 80)

    # Print summary table
    print("\nFOUR-BENCHMARK QUALITY & REPRODUCIBILITY SUMMARY:")
    print("-" * 110)
    print("%-8s | %-12s | %-10s | %-10s | %-10s | %-10s | %-12s | %-10s" % (
        "Case", "Total Elem", "Quads", "Tris", "Quad %", "Max AR", "Min det(J)", "Gates"
    ))
    print("-" * 110)
    for cid in cases:
        r = execution_receipts[cid]
        aud = r["audit"]
        all_gates_pass = all(v == "PASS" for k, v in r["gates"].items() if k.startswith("GATE_"))
        print("%-8s | %-12d | %-10d | %-10d | %-9.2f%% | %-10.3f | %-12g | %-10s" % (
            cid,
            aud["total_elements"],
            aud["quad_count"],
            aud["tri_count"],
            aud["quad_percent"],
            aud["max_aspect_ratio"],
            aud["min_det_j"],
            "PASS" if all_gates_pass else "FAIL"
        ))
    print("-" * 110)


if __name__ == "__main__":
    main()
