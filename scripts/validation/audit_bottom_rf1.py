#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sum RF1 on bottom clamped boundary (y=0) across all steps and frames.
"""
from odbAccess import openOdb
import sys

def audit_bottom_rf1():
    sd_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    odb = openOdb(sd_path, readOnly=True)
    
    print("================================================================================")
    print("BOTTOM BOUNDARY REACTION FORCE (RF1) CONTINUITY AUDIT")
    print("================================================================================")
    
    # Bottom nodes are on y = 0
    # In Step 4, we have all nodes
    cont_step = odb.steps['CONTINUATION']
    f0 = cont_step.frames[0]
    
    bottom_nodes = set()
    # In odb, rootAssembly.instances
    inst = list(odb.rootAssembly.instances.values())[0] if len(odb.rootAssembly.instances) > 0 else None
    
    # Step 1, 2, 3 only saved NSET=N_RP, so field outputs for bottom nodes were not requested in Steps 1-3.
    # But .dat printed total reaction forces for each increment!
    
    print("Step 4 Frame 0 (t=0.0): max U1 = %.6f mm" % max(v.data[0] for v in f0.fieldOutputs['U'].values))
    
    # Calculate sum of all positive RF1 (top boundary) vs negative RF1 (bottom boundary)
    for f_idx in [0, 1, 2, 5, 10, 25, 50, 75, 100, 150, 200, 300, len(cont_step.frames)-1]:
        frame = cont_step.frames[f_idx]
        rf_pos = 0.0
        rf_neg = 0.0
        for v in frame.fieldOutputs['RF'].values:
            if v.data[0] > 0.0:
                rf_pos += v.data[0]
            elif v.data[0] < 0.0:
                rf_neg += v.data[0]
        max_u1 = max(v.data[0] for v in frame.fieldOutputs['U'].values)
        print("  Continuation Frame %3d (Time %.6f, max U1 = %.6f mm): RF1_top = %+.6f kN, RF1_bottom = %+.6f kN, Equil Err = %+.6e kN" % (
            f_idx, frame.frameValue, max_u1, rf_pos, rf_neg, rf_pos + rf_neg))
        
    odb.close()

if __name__ == "__main__":
    audit_bottom_rf1()
