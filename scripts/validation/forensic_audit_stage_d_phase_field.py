#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic Audit of Stage-D Phase Field Continuity, Boundary Semantics, and State Retention.
"""

import os
import sys
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def forensic_audit():
    print("================================================================================")
    print("FORENSIC AUDIT: STAGE-D PHASE-FIELD CONTINUITY & STATE RETENTION")
    print("================================================================================")
    
    staged_odb_path = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb")
    odb = openOdb(staged_odb_path, readOnly=True)
    
    print("\n--- STEP 1: STATE_INSTALL ---")
    s1 = odb.steps['STATE_INSTALL']
    f1_last = s1.frames[-1]
    u1_vals = [float(v.data[2]) for v in f1_last.fieldOutputs['U'].values if len(v.data)>=3]
    print("Step 1 (STATE_INSTALL) Frame %d: d_max = %.6f, d_min = %.6f, total nodes with U3 = %d" % (
        len(s1.frames)-1, max(u1_vals), min(u1_vals), len(u1_vals)))
        
    print("\n--- STEP 2: MECH_EQUILIBRATION ---")
    s2 = odb.steps['MECH_EQUILIBRATION']
    f2_last = s2.frames[-1]
    u2_vals = [float(v.data[2]) for v in f2_last.fieldOutputs['U'].values if len(v.data)>=3]
    print("Step 2 (MECH_EQUILIBRATION) Frame %d: d_max = %.6f, d_min = %.6f, total nodes with U3 = %d" % (
        len(s2.frames)-1, max(u2_vals), min(u2_vals), len(u2_vals)))
        
    print("\n--- STEP 3: PHASE_RELEASE ---")
    s3 = odb.steps['PHASE_RELEASE']
    f3_first = s3.frames[0]
    f3_last = s3.frames[-1]
    u3_first_vals = [float(v.data[2]) for v in f3_first.fieldOutputs['U'].values if len(v.data)>=3]
    u3_last_vals = [float(v.data[2]) for v in f3_last.fieldOutputs['U'].values if len(v.data)>=3]
    print("Step 3 (PHASE_RELEASE) Frame 0: d_max = %.6f" % max(u3_first_vals))
    print("Step 3 (PHASE_RELEASE) Frame %d: d_max = %.6f (RELAXATION / LOSS OCCURS HERE)" % (
        len(s3.frames)-1, max(u3_last_vals)))
        
    print("\n--- STEP 4: CONTINUATION ---")
    s4 = odb.steps['CONTINUATION']
    f4_first = s4.frames[0]
    f4_last = s4.frames[-1]
    u4_first_vals = [float(v.data[2]) for v in f4_first.fieldOutputs['U'].values if len(v.data)>=3]
    u4_last_vals = [float(v.data[2]) for v in f4_last.fieldOutputs['U'].values if len(v.data)>=3]
    print("Step 4 (CONTINUATION) Frame 0: d_max = %.6f" % max(u4_first_vals))
    print("Step 4 (CONTINUATION) Frame %d: d_max = %.6f" % (len(s4.frames)-1, max(u4_last_vals)))
    
    # Trace specific peak node
    # Find peak node in Step 1
    max_d_node = None
    max_val = 0.0
    for v in f1_last.fieldOutputs['U'].values:
        if len(v.data) >= 3 and float(v.data[2]) > max_val:
            max_val = float(v.data[2])
            max_d_node = v.nodeLabel
            
    print("\n--- POINTWISE TRACKING FOR PEAK NODE %d ---" % max_d_node)
    
    # Trace peak node across all steps
    history = []
    for sname in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
        step = odb.steps[sname]
        for f_idx in [0, len(step.frames)-1]:
            frame = step.frames[f_idx]
            val = None
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == max_d_node:
                    val = float(v.data[2])
                    break
            history.append({
                "step": sname,
                "frame": f_idx,
                "time": float(frame.frameValue),
                "d_val": val
            })
            print("  Step %-18s Frame %3d: d = %.6f" % (sname, f_idx, val if val is not None else -1.0))
            
    # Check SDV13 / SDV16 (History H) in overlay / UEL if available
    print("\n--- INSPECTING HISTORY FIELD H (SDV) ---")
    if 'SDV13' in f1_last.fieldOutputs:
        sdv13_vals = [float(v.data) for v in f1_last.fieldOutputs['SDV13'].values]
        print("Step 1 SDV13 max: %.6f" % max(sdv13_vals))
    else:
        print("SDV13 not in fieldOutputs directly (checking all fieldOutputs keys: %s)" % list(f1_last.fieldOutputs.keys()))
        
    odb.close()

if __name__ == "__main__":
    forensic_audit()
