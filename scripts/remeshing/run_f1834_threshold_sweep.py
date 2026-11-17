# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1834_threshold_sweep.py
==============================================
Task F1834: Run Adaptive Remeshing Sweep across Load-Threshold Ratios:
    theta in {0.10, 0.25, 0.50, 0.80}
Across all four mandatory benchmarks:
    - Case 1: Mode-I Edge-Cracked Plate (Method A.2 Multi-State, eta_R = 4.5%)
    - Case 2: Mode-I Plate with Off-Axis Hole (Method A.2 Multi-State, eta_R = 4.0%)
    - Case 3: Notched Plate with Pins (Method A.2 Multi-State, eta_R = 3.0%)
    - Case 5: Plate with Seven Holes (Table 6 Parity, eta_R = 5.68%)

Uses run_f1834_single_target.py under Abaqus CAE noGUI mode.
"""
from __future__ import print_function
import os
import sys
import subprocess
import json
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
F1834_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "274_f1834_blowup_guard")
SINGLE_TARGET_SCRIPT = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1834_single_target.py")
ABAQUS_BAT = r"C:\SIMULIA\Commands\abaqus.bat"

TARGET_CASES = [
    {
        "cid": "case_1",
        "name": "Case 1: Mode-I Edge-Cracked Plate",
        "error_target": 4.5,
        "tag": "case1",
        "donor_fname": "PK_CASE1_MULTISTATE_RECOVERY.odb",
        "job_prefix": "PK_F1834_C1"
    },
    {
        "cid": "case_2",
        "name": "Case 2: Mode-I Plate with Off-Axis Hole",
        "error_target": 4.0,
        "tag": "case2",
        "donor_fname": "PK_HOLE_MULTISTATE_RECOVERY.odb",
        "job_prefix": "PK_F1834_C2"
    },
    {
        "cid": "case_3",
        "name": "Case 3: Notched Plate with Pins and Hole",
        "error_target": 3.0,
        "tag": "case3",
        "donor_fname": "SEC43_MULTISTATE_RECOVERY.odb",
        "job_prefix": "PK_F1834_C3"
    },
    {
        "cid": "case_5",
        "name": "Case 5: Square Plate with Seven Holes",
        "error_target": 5.68,
        "tag": "case5",
        "donor_fname": "PK_F1726_SEVEN_HOLE_COARSE.odb",
        "job_prefix": "PK_F1834_C5"
    }
]

THRESHOLDS = [
    (0.10, "thresh_010"),
    (0.25, "thresh_025"),
    (0.50, "thresh_050"),
    (0.80, "thresh_080"),
]

def run_single(cid, error_target, out_dir, job_name, donor_path):
    print("\n" + "=" * 80)
    print("LAUNCHING ABAQUS CAE: %s (Target: %.2f%%)" % (cid, error_target))
    print("  Output dir: %s" % out_dir)
    print("  Job name:   %s" % job_name)
    print("  Donor path: %s" % donor_path)
    print("=" * 80)
    cmd = [
        ABAQUS_BAT, "cae",
        "noGUI=%s" % SINGLE_TARGET_SCRIPT,
        "--",
        cid,
        str(error_target),
        out_dir,
        job_name,
        donor_path
    ]
    t0 = time.time()
    ret = subprocess.call(cmd, cwd=REPO_ROOT)
    t_el = time.time() - t0
    print("<<< Finished %s in %.2f s (Exit: %d)" % (cid, t_el, ret))
    if ret != 0:
        raise RuntimeError("Abaqus failed for %s with exit code %d" % (cid, ret))
    receipt_file = os.path.join(out_dir, job_name + "_RECEIPT.json")
    if not os.path.exists(receipt_file):
        raise RuntimeError("Missing receipt: %s" % receipt_file)
    with open(receipt_file, "r") as f:
        receipt = json.load(f)
    return receipt

def main():
    t_start = time.time()
    results = {}
    for theta, th_tag in THRESHOLDS:
        print("\n" + "#" * 80)
        print("RUNNING ADAPTIVE REMESHING SWEEP FOR THETA = %.2f (%s)" % (theta, th_tag))
        print("#" * 80)
        results[th_tag] = {"theta": theta, "cases": {}}
        for cdef in TARGET_CASES:
            cid = cdef["cid"]
            c_tag = cdef["tag"]
            out_d = os.path.join(F1834_BASE, th_tag, c_tag)
            job_n = "%s_%s" % (cdef["job_prefix"], th_tag.upper())
            donor_p = os.path.join(F1834_BASE, th_tag, c_tag, cdef["donor_fname"])
            rec = run_single(cid, cdef["error_target"], out_d, job_n, donor_p)
            results[th_tag]["cases"][cid] = {
                "elements": rec["audit_metrics"]["total_elements"],
                "quad_pct": rec["audit_metrics"]["quad_fraction_pct"],
                "min_det_j": rec["audit_metrics"]["min_det_j"],
                "max_ar": rec["audit_metrics"]["max_aspect_ratio"],
                "coarsening_ratio": rec["audit_metrics"]["coarsening_ratio"],
                "scientific_gate": rec["scientific_gate_status"],
                "gate_06": rec["gate_summary"]["gate_06_far_field_coarsening"],
                "gate_07": rec["gate_summary"]["gate_07_element_budget"],
                "corridor_fine_area": rec["band_metrics"].get("corridor_fine_area_mm2", 0.0),
                "unnecessary_fine_area": rec["band_metrics"].get("unnecessary_fine_area_mm2", 0.0),
                "unnecessary_fine_pct": rec["band_metrics"].get("unnecessary_fine_fraction_pct", 0.0),
                "band_width_mm": rec["band_metrics"].get("band_width_mm", 0.0),
                "receipt_path": os.path.relpath(os.path.join(out_d, job_n + "_RECEIPT.json"), REPO_ROOT).replace("\\", "/")
            }

    t_total = time.time() - t_start
    results["total_sweep_walltime_s"] = round(t_total, 2)
    sweep_summary_path = os.path.join(F1834_BASE, "threshold_sweep_summary.json")
    with open(sweep_summary_path, "w") as f:
        json.dump(results, f, indent=2)
    print("\n" + "=" * 80)
    print("SWEEP COMPLETE in %.2f s! Summary saved to: %s" % (t_total, sweep_summary_path))
    print("=" * 80)

if __name__ == "__main__":
    main()
