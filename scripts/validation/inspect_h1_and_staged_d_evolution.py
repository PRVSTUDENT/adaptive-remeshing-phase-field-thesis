#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic audit of d_max, nodal phase field, and reaction forces across H1 and Stage-D.
"""
from odbAccess import openOdb
import math
import sys

def audit():
    h1_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    sd_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    print("================================================================================")
    print("FORENSIC AUDIT OF D EVOLUTION IN NATIVE H1 AND STAGE-D")
    print("================================================================================")
    
    # 1. Native H1
    odb_h1 = openOdb(h1_path, readOnly=True)
    step_h1 = odb_h1.steps['ShearStep']
    print("\n--- NATIVE H1 SIMULATION (1389686.mmaster02) ---")
    print("Total frames in H1: %d" % len(step_h1.frames))
    for f_idx in range(0, len(step_h1.frames), 10):
        frame = step_h1.frames[f_idx]
        u_f = frame.fieldOutputs['U']
        max_d = 0.0
        node_max = None
        for v in u_f.values:
            if len(v.data) >= 3 and v.data[2] > max_d:
                max_d = v.data[2]
                node_max = v.nodeLabel
        print("  H1 Frame %3d (Time %.6f): max d = %.6f at Node %s" % (f_idx, frame.frameValue, max_d, node_max))
        
    last_frame_h1 = step_h1.frames[-1]
    max_d_last_h1 = 0.0
    for v in last_frame_h1.fieldOutputs['U'].values:
        if len(v.data) >= 3 and v.data[2] > max_d_last_h1:
            max_d_last_h1 = v.data[2]
    print("  H1 Last Frame %d (Time %.6f): max d = %.6f" % (len(step_h1.frames)-1, last_frame_h1.frameValue, max_d_last_h1))
    odb_h1.close()

    # 2. Stage-D
    odb_sd = openOdb(sd_path, readOnly=True)
    print("\n--- STAGE-D SIMULATION (1390192.mmaster02) ---")
    for s_name, step in odb_sd.steps.items():
        print("\nStep: %s (Total frames: %d)" % (s_name, len(step.frames)))
        for f_idx in [0, len(step.frames)//2, len(step.frames)-1]:
            if f_idx < len(step.frames):
                frame = step.frames[f_idx]
                max_d = 0.0
                node_max = None
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        if len(v.data) >= 3 and v.data[2] > max_d:
                            max_d = v.data[2]
                            node_max = v.nodeLabel
                # RF sum on RP or boundary
                rf_tot = 0.0
                if 'RF' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['RF'].values:
                        if v.data[0] > 0.0:
                            rf_tot += v.data[0]
                print("  %s Frame %3d: max d = %.6f at Node %s | Positive RF1 sum = %.6f kN" % (
                    s_name, f_idx, max_d, node_max, rf_tot))

    odb_sd.close()

if __name__ == "__main__":
    audit()
