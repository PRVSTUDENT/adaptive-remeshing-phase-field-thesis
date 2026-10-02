#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect and Reconcile Donor Trajectory Extraction Across 5 Donor Lineage Jobs
"""

import os
import sys
import glob
from odbAccess import openOdb

def inspect_odb(odb_path, label):
    if not os.path.exists(odb_path):
        print("[NOT FOUND] %s: %s" % (label, odb_path))
        return
        
    print("================================================================================")
    print("INSPECTING: %s (%s)" % (label, odb_path))
    print("================================================================================")
    
    odb = openOdb(odb_path, readOnly=True)
    
    for s_name, step in odb.steps.items():
        num_frames = len(step.frames)
        print("Step: %s | Total Frames: %d (Frame 0 to Frame %d)" % (s_name, num_frames, num_frames - 1))
        
        # Frame 0
        f0 = step.frames[0]
        # Frame 17 (Handoff)
        f17 = step.frames[17] if len(step.frames) > 17 else None
        # Last frame
        flast = step.frames[-1]
        
        def get_rp_values(frame):
            u1, u2, u3 = 0.0, 0.0, 0.0
            rf1, rf2, rf3 = 0.0, 0.0, 0.0
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel == 99999:
                        u1 = float(v.data[0])
                        u2 = float(v.data[1])
                        if len(v.data) > 2: u3 = float(v.data[2])
                        break
            if 'RF' in frame.fieldOutputs:
                for v in frame.fieldOutputs['RF'].values:
                    if v.nodeLabel == 99999:
                        rf1 = float(v.data[0])
                        rf2 = float(v.data[1])
                        if len(v.data) > 2: rf3 = float(v.data[2])
                        break
                        
            # Also sum of RF on bottom nodes (N_BOTTOM)
            # Find bottom reaction force if present
            rf1_bottom_sum = 0.0
            if 'RF' in frame.fieldOutputs:
                for v in frame.fieldOutputs['RF'].values:
                    if v.nodeLabel != 99999:
                        rf1_bottom_sum += float(v.data[0])
                        
            return {
                "frameValue": float(frame.frameValue),
                "u1": u1, "u2": u2, "u3": u3,
                "rf1": rf1, "rf2": rf2, "rf3": rf3,
                "rf1_bottom_sum": rf1_bottom_sum
            }
            
        print("Frame  0 (Initial):", get_rp_values(f0))
        if f17:
            print("Frame 17 (Handoff):", get_rp_values(f17))
        print("Frame %d (Terminal):" % (num_frames - 1), get_rp_values(flast))
        
        # Peak RF1 across all frames
        peak_rf1 = -1e9
        peak_frame = None
        peak_u1 = None
        for idx, f in enumerate(step.frames):
            vals = get_rp_values(f)
            if vals["rf1"] > peak_rf1:
                peak_rf1 = vals["rf1"]
                peak_frame = idx
                peak_u1 = vals["u1"]
                
        print("Peak RF1: %12.8f kN at Frame %d (U1 = %10.8f mm)" % (peak_rf1, peak_frame, peak_u1))
        
    odb.close()

def main():
    candidates = [
        ("1390447.mmaster02", "models/generated/mode_ii/donor_continuation_protocol/M2CORR_STAGE_D_DONOR_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_D_DONOR_MINIMAL_CONTINUATION_VAL.odb"),
        ("1390447_alt", "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb"),
        ("1390552.mmaster02", "models/generated/mode_ii/donor_continuation_protocol/M2CORR_STAGE_E_DONOR_TARGET_BASELINES_VAL/M2CORR_STAGE_E_DONOR_TARGET_BASELINES_VAL.odb"),
        ("1390552_alt", "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_TARGET_BASELINES_VAL/M2CORR_STAGE_E_DONOR_TARGET_BASELINES_VAL.odb"),
        ("1390876.mmaster02", "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL.odb"),
        ("1391301.mmaster02", "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_IA13_ISOLATION_VAL.odb"),
        ("1391302.mmaster02", "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL/M2CORR_STAGE_E_DONOR_DTMIN5E12_ISOLATION_VAL.odb")
    ]
    
    # Also search for any other ODBs in models/generated/
    for label, path in candidates:
        inspect_odb(path, label)

if __name__ == "__main__":
    main()
