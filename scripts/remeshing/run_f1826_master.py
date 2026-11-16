# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1826_master.py
======================================
Task F1826: Master Orchestration Script.
Executes all four benchmark cases under the harmonized adapter framework using local Abaqus CAE noGUI:
- Case 1: error_target = 4.50% -> PK_F1826_CASE_1_ADAPT_PHYS.inp
- Case 2: error_target = 4.00% -> PK_F1826_CASE_2_ADAPT_PHYS.inp
- Case 3: error_target = 3.00% -> PK_F1826_CASE_3_ADAPT_PHYS.inp
- Case 5: error_target = 5.68% -> PK_F1826_CASE_5_ADAPT_PHYS.inp

Collects individual audit receipts, aggregates results into:
- models/pandey_kumar_mode1/270_f1826_adapter_harmonization/PK_F1826_ADAPTER_HARMONIZATION_RECEIPT.json
- results/validation/f1826_adapter_harmonization_summary.json
"""
import os
import sys
import json
import subprocess
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
BASE_OUT = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "270_f1826_adapter_harmonization")
SINGLE_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1826_single_target.py")
FRAMEWORK_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

TARGETS = [
    {
        "case_id": "case_1",
        "error_target": 4.5,
        "out_dir": os.path.join(BASE_OUT, "case1"),
        "job_name": "PK_F1826_CASE_1_ADAPT"
    },
    {
        "case_id": "case_2",
        "error_target": 4.0,
        "out_dir": os.path.join(BASE_OUT, "case2"),
        "job_name": "PK_F1826_CASE_2_ADAPT"
    },
    {
        "case_id": "case_3",
        "error_target": 3.0,
        "out_dir": os.path.join(BASE_OUT, "case3"),
        "job_name": "PK_F1826_CASE_3_ADAPT"
    },
    {
        "case_id": "case_5",
        "error_target": 5.68,
        "out_dir": os.path.join(BASE_OUT, "case5"),
        "job_name": "PK_F1826_CASE_5_ADAPT"
    }
]


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    if not os.path.exists(BASE_OUT):
        os.makedirs(BASE_OUT)

    framework_sha = compute_sha256(FRAMEWORK_SCRIPT)
    print("=====================================================================")
    print("F1826 MASTER ORCHESTRATION: 4-BENCHMARK ADAPTER HARMONIZATION")
    print("Framework SHA-256: %s" % framework_sha)
    print("Output directory:  %s" % BASE_OUT)
    print("=====================================================================")

    results = {}

    for t in TARGETS:
        cid = t["case_id"]
        target = t["error_target"]
        out_dir = t["out_dir"]
        job_name = t["job_name"]

        if not os.path.exists(out_dir):
            os.makedirs(out_dir)

        print("\n>>> Launching Abaqus CAE noGUI for %s (target=%.2f%%)..." % (cid, target))
        cmd = 'abaqus cae noGUI="%s" -- %s %s "%s" %s' % (
            SINGLE_SCRIPT, cid, str(target), out_dir, job_name
        )

        ret = subprocess.call(cmd, shell=True, cwd=REPO_ROOT)
        if ret != 0:
            print("ERROR: Abaqus run failed for %s with exit code %d" % (cid, ret))
            sys.exit(ret)

        receipt_path = os.path.join(out_dir, job_name + "_RECEIPT.json")
        if not os.path.exists(receipt_path):
            print("ERROR: Expected receipt not found at %s" % receipt_path)
            sys.exit(1)

        with open(receipt_path, "r") as f:
            rec = json.load(f)
        results[cid] = rec
        print(">>> %s complete: %d elements, Gate 06: %s (%.2fx), Sci Gate: %s" % (
            cid, rec["total_elements"], rec["original_gate_06"]["status"],
            rec["original_gate_06"]["refinement_ratio"], rec["scientific_gate"]["status"]
        ))

    # Master receipt
    master_receipt = {
        "task_id": "F1826-ADAPTER-HARMONIZATION-AND-GATE06-VERIFICATION",
        "framework_sha256": framework_sha,
        "cases": results,
        "total_elements_across_four_cases": sum(r["total_elements"] for r in results.values()),
        "summary": {
            cid: {
                "total_elements": r["total_elements"],
                "quad_percent": r["quad_percent"],
                "original_gate_06_ratio": r["original_gate_06"]["refinement_ratio"],
                "original_gate_06_status": r["original_gate_06"]["status"],
                "size_thresholded_ratio": r["supplementary_diagnostics"]["size_thresholded"]["refinement_ratio"],
                "corner_mean_to_min_ratio": r["supplementary_diagnostics"]["geometric_corner"]["ratio_corner_mean_to_min"],
                "scientific_gate_name": r["scientific_gate"]["name"],
                "scientific_gate_status": r["scientific_gate"]["status"]
            }
            for cid, r in results.items()
        }
    }

    master_receipt_path = os.path.join(BASE_OUT, "PK_F1826_ADAPTER_HARMONIZATION_RECEIPT.json")
    with open(master_receipt_path, "w") as f:
        json.dump(master_receipt, f, indent=2)

    summary_dir = os.path.join(REPO_ROOT, "results", "validation")
    if not os.path.exists(summary_dir):
        os.makedirs(summary_dir)
    summary_path = os.path.join(summary_dir, "f1826_adapter_harmonization_summary.json")
    with open(summary_path, "w") as f:
        json.dump(master_receipt, f, indent=2)

    print("\n=====================================================================")
    print("F1826 ALL CASES COMPLETED SUCCESSFULLY")
    print("Master Receipt: %s" % master_receipt_path)
    print("Summary JSON:   %s" % summary_path)
    print("Total Elements: %d" % master_receipt["total_elements_across_four_cases"])
    print("=====================================================================")


if __name__ == "__main__":
    main()
