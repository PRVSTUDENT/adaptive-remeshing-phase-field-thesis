#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Inspect history regions and extract RF1 vs U1 curve for H1 and Stage-D.
"""
from odbAccess import openOdb
import json

def inspect_curves():
    h1_odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    sd_odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"
    
    odb_h1 = openOdb(h1_odb_path, readOnly=True)
    odb_sd = openOdb(sd_odb_path, readOnly=True)
    
    print("--- H1 HISTORY REGIONS ---")
    step_h1 = odb_h1.steps['ShearStep']
    for k, hr in step_h1.historyRegions.items():
        print("  Key: %s | Outputs: %s" % (k, list(hr.historyOutputs.keys())))
        
    print("\n--- STAGE-D HISTORY REGIONS ---")
    for s_name, step in odb_sd.steps.items():
        print("Step: %s" % s_name)
        for k, hr in step.historyRegions.items():
            print("  Key: %s | Outputs: %s" % (k, list(hr.historyOutputs.keys())))
            
    # Extract RF1/U1 from field outputs directly across all frames of Continuation
    print("\n--- EXTRACTING FIELD RF1/U1 ACROSS CONTINUATION FRAMES ---")
    cont_step = odb_sd.steps['CONTINUATION']
    rf1_sd = []
    u1_sd = []
    for f_idx, frame in enumerate(cont_step.frames):
        # find top boundary or RP node
        rf_field = frame.fieldOutputs['RF']
        u_field = frame.fieldOutputs['U']
        
        tot_rf1 = 0.0
        # Sum reaction forces on bottom clamped boundary or top loaded boundary
        for val in rf_field.values:
            if val.data[0] > 0.0:
                tot_rf1 += val.data[0]
                
        # Get max U1 in model
        max_u1 = 0.0
        for val in u_field.values:
            if val.data[0] > max_u1:
                max_u1 = val.data[0]
                
        rf1_sd.append(tot_rf1)
        u1_sd.append(max_u1)
        if f_idx % 25 == 0 or f_idx == len(cont_step.frames)-1:
            print("  Frame %3d: max U1 = %.6f mm, positive RF1 sum = %.6f kN" % (f_idx, max_u1, tot_rf1))

    odb_h1.close()
    odb_sd.close()

if __name__ == "__main__":
    inspect_curves()
