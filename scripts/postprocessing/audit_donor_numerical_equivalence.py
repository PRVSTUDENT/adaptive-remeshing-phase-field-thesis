#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Numerical Equivalence Audit: Historical Donor 1390447 vs Revised Donor 1390533
"""

import os
import sys
import json
import difflib
import numpy as np

def compare_deck_diffs():
    inp1 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp"
    inp2 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.inp"
    
    with open(inp1, "r") as fp:
        lines1 = fp.readlines()
    with open(inp2, "r") as fp:
        lines2 = fp.readlines()
        
    diff = list(difflib.unified_diff(lines1, lines2, fromfile="1390447.inp", tofile="1390533.inp", n=1))
    return diff

def load_curve_1390447(csv_path):
    with open(csv_path, "r") as fp:
        lines = fp.readlines()[1:]
    frames = []
    for l in lines:
        p = [x.strip() for x in l.strip().split(",")]
        if len(p) >= 8:
            frames.append({
                "frame": int(p[1]),
                "step_time": float(p[3]),
                "u1": float(p[5]),
                "rf1": float(p[6]),
                "d_max": float(p[7])
            })
    return frames

def load_curve_1390533(csv_path):
    with open(csv_path, "r") as fp:
        lines = fp.readlines()[1:]
    frames = []
    for l in lines:
        p = [x.strip() for x in l.strip().split(",")]
        if len(p) >= 7:
            frames.append({
                "frame": int(p[0]),
                "step_time": float(p[1]),
                "u1": float(p[2]),
                "rf1": float(p[3]),
                "d_max": float(p[6])
            })
    return frames

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL"
    
    # 1. Deck Diff
    diff = compare_deck_diffs()
    print("================================================================================")
    print("INP DECK DIFF (1390447 vs 1390533):")
    print("================================================================================")
    for d in diff:
        print(d.strip())
        
    # 2. Compare Curves
    c1_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/force_displacement_curve.csv"
    c2_path = os.path.join(base_dir, "force_displacement_curve.csv")
    
    curve1 = load_curve_1390447(c1_path)
    curve2 = load_curve_1390533(c2_path)
    
    u1_targets = [0.001, 0.002, 0.005, 0.008, 0.010, 0.01051289, 0.011, 0.012, 0.012375, 0.0125, 0.013, 0.0135, 0.014, 0.015, 0.020, 0.030, 0.040, 0.050]
    
    u1_arr1 = np.array([f["u1"] for f in curve1])
    rf1_arr1 = np.array([f["rf1"] for f in curve1])
    d1_arr = np.array([f["d_max"] for f in curve1])
    
    u1_arr2 = np.array([f["u1"] for f in curve2])
    rf1_arr2 = np.array([f["rf1"] for f in curve2])
    d2_arr = np.array([f["d_max"] for f in curve2])
    
    print("\n================================================================================")
    print("MATCHED U1 POINT-BY-POINT COMPARISON:")
    print("================================================================================")
    print("Target U1 (mm) | 1390447 RF1 (kN) | 1390533 RF1 (kN) | RF1 Diff (%) | 1390447 d_max | 1390533 d_max | d_max Diff")
    print("---------------------------------------------------------------------------------------------------------")
    
    matched_diffs = []
    for ut in u1_targets:
        idx1 = int(np.argmin(np.abs(u1_arr1 - ut)))
        idx2 = int(np.argmin(np.abs(u1_arr2 - ut)))
        
        rf1_1 = rf1_arr1[idx1]
        rf1_2 = rf1_arr2[idx2]
        diff_rf1 = (rf1_2 - rf1_1) / rf1_1 * 100.0 if rf1_1 != 0 else 0.0
        
        dm1 = d1_arr[idx1]
        dm2 = d2_arr[idx2]
        diff_dm = dm2 - dm1
        
        print("%14.6f | %16.6f | %16.6f | %+11.4f%% | %13.6f | %13.6f | %+10.6f" % (
            ut, rf1_1, rf1_2, diff_rf1, dm1, dm2, diff_dm))
            
        matched_diffs.append({
            "target_u1": ut,
            "1390447_actual_u1": float(u1_arr1[idx1]),
            "1390533_actual_u1": float(u1_arr2[idx2]),
            "1390447_rf1": float(rf1_1),
            "1390533_rf1": float(rf1_2),
            "rf1_diff_pct": float(diff_rf1),
            "1390447_d_max": float(dm1),
            "1390533_d_max": float(dm2),
            "d_max_diff": float(diff_dm)
        })
        
    audit_summary = {
        "historical_donor_job": "1390447.mmaster02",
        "revised_donor_job": "1390533.mmaster02",
        "inp_differences": [d.strip() for d in diff],
        "matched_points": matched_diffs
    }
    
    with open(os.path.join(base_dir, "donor_equivalence_audit_summary.json"), "w") as fp:
        json.dump(audit_summary, fp, indent=2)

if __name__ == "__main__":
    main()
