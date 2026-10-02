#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Point-by-Point Parity Verification:
Historical Donor Control 1390447 vs Minimal Continuation Donor Qualification 1390552
"""

import os
import sys
import json
import numpy as np

def main():
    csv_1390447 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/force_displacement_curve.csv"
    csv_1390552 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/force_displacement_curve.csv"
    
    data1 = np.genfromtxt(csv_1390447, delimiter=',', names=True)
    data2 = np.genfromtxt(csv_1390552, delimiter=',', names=True)
    
    print("Historical 1390447 frames: %d" % len(data1))
    print("New 1390552 frames       : %d" % len(data2))
    
    u1_1 = data1['physical_u1_mm']
    rf1_1 = data1['rp_rf1_kN']
    d_1 = data1['d_max']
    
    u1_2 = data2['U1_mm']
    rf1_2 = data2['RF1_kN']
    d_2 = data2['d_max']
    
    max_u_diff = np.max(np.abs(u1_1 - u1_2))
    max_rf_diff = np.max(np.abs(rf1_1 - rf1_2))
    max_d_diff = np.max(np.abs(d_1 - d_2))
    
    print("Max U1 difference : %.8e mm" % max_u_diff)
    print("Max RF1 difference: %.8e kN" % max_rf_diff)
    print("Max d_max diff    : %.8e" % max_d_diff)
    
    res = {
        "total_frames_1390447": len(data1),
        "total_frames_1390552": len(data2),
        "exact_frame_count_match": bool(len(data1) == len(data2)),
        "max_u1_diff_mm": float(max_u_diff),
        "max_rf1_diff_kN": float(max_rf_diff),
        "max_d_max_diff": float(max_d_diff),
        "path_identical": bool(max_rf_diff < 1e-5 and max_u_diff < 1e-6 and max_d_diff < 1e-4)
    }
    
    out_json = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL/donor_parity_verification.json"
    with open(out_json, "w") as fp:
        json.dump(res, fp, indent=2)
        
    print("\nPARITY VERDICT: %s" % ("100.0000% PATH IDENTICAL" if res["path_identical"] else "DIVERGENT"))

if __name__ == "__main__":
    main()
