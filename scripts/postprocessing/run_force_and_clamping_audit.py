#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to reconcile H1 handoff force provenance and audit history operator clamping
"""

import os
import sys
import struct
import numpy as np
from odbAccess import openOdb

def check_h1_odb():
    odb_paths = [
        "runs/hpc/stage_f/mode_ii_h1/evidence/1389686.mmaster02/M2REF_H1_TIGHT_BASE.odb",
        "models/generated/mode_ii/reference_convergence/M2REF_H1_TIGHT_BASE/M2REF_H1_TIGHT_BASE.odb"
    ]
    h1_odb = None
    for p in odb_paths:
        if os.path.exists(p):
            h1_odb = p
            break

    if h1_odb:
        print("Opening H1 ODB: %s" % h1_odb)
        odb = openOdb(h1_odb, readOnly=True)
        step = odb.steps['ShearStep']
        frame = step.frames[29]
        print("Frame 29 / Increment 29: FrameValue = %.10e" % frame.frameValue)

        rf_dict = {}
        for v in frame.fieldOutputs['RF'].values:
            rf_dict[v.nodeLabel] = v.data

        print("Total nodes with RF output: %d" % len(rf_dict))
        
        # Check specific node labels
        for n in [12384, 99999, 12065, 12289, 12383]:
            if n in rf_dict:
                print("Node %d RF: %s" % (n, str(rf_dict[n])))

        # Sum of positive and negative RF1
        pos_rf1 = sum(v[0] for v in rf_dict.values() if v[0] > 0)
        neg_rf1 = sum(v[0] for v in rf_dict.values() if v[0] < 0)
        print("Sum of positive RF1: %.10e kN" % pos_rf1)
        print("Sum of negative RF1: %.10e kN" % neg_rf1)

        # Check RP reaction force
        # Find the max magnitude node
        sorted_rf = sorted(rf_dict.items(), key=lambda x: abs(x[1][0]), reverse=True)
        print("Top 5 nodes by |RF1|:")
        for nid, val in sorted_rf[:5]:
            print("  Node %d: RF1 = %.10e, RF2 = %.10e" % (nid, val[0], val[1]))

        odb.close()
    else:
        print("H1 ODB not found locally.")

def check_history_clamping_detailed():
    print("\n--- Detailed Audit of History Operator Clamping across 35,344 Target GPs ---")
    bin_1390454 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL_SMOOTH_H/STAGE_D_COMMITTED_STATE.bin"
    
    with open(bin_1390454, "rb") as fp:
        buf = fp.read()

    rec1_len = struct.unpack("i", buf[:4])[0]
    rec2_len = struct.unpack("i", buf[4+rec1_len+4:4+rec1_len+4+4])[0]
    rec2_data = buf[4+rec1_len+4+4:4+rec1_len+4+4+rec2_len]
    hist_smooth = np.frombuffer(rec2_data, dtype=np.float64).reshape((100000, 4), order='F')

    n_elems = 8836
    h_s = hist_smooth[1:n_elems+1, :] # (8836, 4)

    total_gps = n_elems * 4
    print("Total Target Integration Points: %d" % total_gps)
    print("Min H = %.10e, Max H = %.10e" % (np.min(h_s), np.max(h_s)))

    # Evaluate how many points are positive, zero, etc.
    zero_gps = np.sum(h_s == 0.0)
    pos_gps = np.sum(h_s > 0.0)
    pz_gps = np.sum(h_s > 1e-4)
    print("Zero H GPs (< 1e-15)          : %d (%.2f%%)" % (zero_gps, zero_gps / float(total_gps) * 100.0))
    print("Positive H GPs (> 0)          : %d (%.2f%%)" % (pos_gps, pos_gps / float(total_gps) * 100.0))
    print("Process Zone GPs (H > 1e-4)   : %d (%.2f%%)" % (pz_gps, pz_gps / float(total_gps) * 100.0))

if __name__ == "__main__":
    check_h1_odb()
    check_history_clamping_detailed()
