#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trace Reference Point (N_RP) RF1 and U1 exactly across Step 1, 2, 3, and 4.
"""
from odbAccess import openOdb
import sys

def trace():
    sd_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    odb = openOdb(sd_path, readOnly=True)
    
    print("================================================================================")
    print("REFERENCE POINT (N_RP) TRANSITION & CONTINUITY AUDIT")
    print("================================================================================")
    
    rp_nid = 9073 # Reference Point Node
    
    for s_name in ['STATE_INSTALL', 'MECH_EQUILIBRATION', 'PHASE_RELEASE', 'CONTINUATION']:
        step = odb.steps[s_name]
        print("\n--- STEP: %s (%d frames) ---" % (s_name, len(step.frames)))
        for f_idx in range(len(step.frames)):
            if f_idx == 0 or f_idx == len(step.frames)-1 or f_idx <= 2:
                frame = step.frames[f_idx]
                rf1 = None
                u1 = None
                if 'RF' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['RF'].values:
                        if v.nodeLabel == rp_nid:
                            rf1 = v.data[0]
                if 'U' in frame.fieldOutputs:
                    for v in frame.fieldOutputs['U'].values:
                        if v.nodeLabel == rp_nid:
                            u1 = v.data[0]
                print("  Frame %3d (Time %.6f): RP U1 = %s mm | RP RF1 = %s kN" % (
                    f_idx, frame.frameValue, ("%.6f" % u1 if u1 is not None else "None"), ("%.6f" % rf1 if rf1 is not None else "None")))
                
    odb.close()

if __name__ == "__main__":
    trace()
