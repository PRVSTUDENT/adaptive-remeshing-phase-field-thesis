#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep GP History and State Divergence Extraction:
Historical Donor 1390447 vs Revised Donor 1390533 around Frame 19 and Frame 20
"""

import os
import sys
import json
import numpy as np
from odbAccess import openOdb

def extract_gp_details(odb_path, target_frames=[18, 19, 20, 21]):
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    
    details = {}
    
    for f_idx in target_frames:
        if f_idx >= len(step.frames): continue
        frame = step.frames[f_idx]
        time = float(frame.frameValue)
        
        # Energy
        allie = 0.0
        allse = 0.0
        alldmd = 0.0
        
        # RP U1 and RF1
        u1 = 0.0
        rf1 = 0.0
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == 99999:
                    u1 = float(v.data[0]); break
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == 99999:
                    rf1 = float(v.data[0]); break
                    
        # SDV / Damage
        d_vals = []
        if 'SDV_D' in frame.fieldOutputs:
            for v in frame.fieldOutputs['SDV_D'].values:
                if not np.isnan(v.data):
                    d_vals.append(float(v.data))
        elif 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if len(v.data) >= 3 and v.nodeLabel != 99999:
                    d_vals.append(float(v.data[2]))
                    
        # SDV_H if available
        h_vals = []
        if 'SDV_H' in frame.fieldOutputs:
            for v in frame.fieldOutputs['SDV_H'].values:
                if not np.isnan(v.data):
                    h_vals.append(float(v.data))
                    
        details[f_idx] = {
            "step_time": time,
            "u1_mm": u1,
            "rf1_kN": rf1,
            "d_max": float(max(d_vals)) if d_vals else 0.0,
            "d_min": float(min(d_vals)) if d_vals else 0.0,
            "h_max": float(max(h_vals)) if h_vals else 0.0,
            "active_upper_bound_count_d_ge_099": sum(1 for d in d_vals if d >= 0.99) if d_vals else 0
        }
        
    odb.close()
    return details

def main():
    odb1 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    odb2 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL/M2CORR_STAGE_E_DONOR_CONTROL_VAL.odb"
    
    det1 = extract_gp_details(odb1)
    det2 = extract_gp_details(odb2)
    
    print("================================================================================")
    print("HISTORICAL 1390447 GP & STATE DETAILS (FRAMES 18-21):")
    print("================================================================================")
    for f, d in sorted(det1.items()):
        print("Frame %2d: Time = %.5f, U1 = %.6f mm, RF1 = %.6f kN, d_max = %.6f, Active Upper Bound = %d" % (
            f, d["step_time"], d["u1_mm"], d["rf1_kN"], d["d_max"], d["active_upper_bound_count_d_ge_099"]))
            
    print("\n================================================================================")
    print("REVISED 1390533 GP & STATE DETAILS (FRAMES 18-21):")
    print("================================================================================")
    for f, d in sorted(det2.items()):
        print("Frame %2d: Time = %.5f, U1 = %.6f mm, RF1 = %.6f kN, d_max = %.6f, Active Upper Bound = %d" % (
            f, d["step_time"], d["u1_mm"], d["rf1_kN"], d["d_max"], d["active_upper_bound_count_d_ge_099"]))
            
    res = {
        "historical_1390447": det1,
        "revised_1390533": det2
    }
    with open("models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL/gp_divergence_details.json", "w") as fp:
        json.dump(res, fp, indent=2)

if __name__ == "__main__":
    main()
