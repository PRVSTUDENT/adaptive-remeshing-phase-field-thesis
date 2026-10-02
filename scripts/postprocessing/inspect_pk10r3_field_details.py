#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Precise Frame-by-Frame Diagnostic Field Extraction for PK10R3 (1390098) vs PK10R2 (1390056) vs H1 (1389686).
"""

import sys
import os
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def inspect_odb_fields(odb_path, label):
    print("================================================================================")
    print("INSPECTING ODB: %s (%s)" % (label, odb_path))
    print("================================================================================")
    odb = openOdb(odb_path, readOnly=True)
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    
    print("Total frames: %d" % len(step.frames))
    
    # Check available fields in last frame
    last_frame = step.frames[-1]
    print("Fields in last frame (t = %f):" % last_frame.frameValue)
    for f_name in last_frame.fieldOutputs.keys():
        print("  - %s" % f_name)
        
    # Check history regions
    for hr_name in step.historyRegions.keys():
        hr = step.historyRegions[hr_name]
        print("History region: %s (keys: %s)" % (hr_name, hr.historyOutputs.keys()))
        
    # Track max U3 (phase field) and max SDV across frames
    frame_summary = []
    target_disps = [0.005, 0.010, 0.0125, 0.020, 0.035, 0.050]
    
    for idx, frame in enumerate(step.frames):
        t = frame.frameValue
        u_rp = t * 0.05 # total prescribed displacement is 0.05
        
        max_u3 = 0.0
        max_u1 = 0.0
        max_u2 = 0.0
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if len(v.data) >= 3:
                    if v.data[2] > max_u3:
                        max_u3 = float(v.data[2])
                if abs(v.data[0]) > max_u1:
                    max_u1 = float(abs(v.data[0]))
                if len(v.data) >= 2 and abs(v.data[1]) > max_u2:
                    max_u2 = float(abs(v.data[1]))
                    
        max_sdv1 = 0.0
        for sdv_key in ['SDV_SDV1', 'SDV1', 'SDV']:
            if sdv_key in frame.fieldOutputs:
                for v in frame.fieldOutputs[sdv_key].values:
                    if hasattr(v, 'data'):
                        if isinstance(v.data, (list, tuple, np.ndarray)):
                            if len(v.data) > 0 and v.data[0] > max_sdv1:
                                max_sdv1 = float(v.data[0])
                        else:
                            if v.data > max_sdv1:
                                max_sdv1 = float(v.data)
                                
        frame_summary.append({
            "frame_index": idx,
            "step_time": float(t),
            "prescribed_u1": float(u_rp),
            "max_u3_phase": float(max_u3),
            "max_sdv1_history": float(max_sdv1),
            "max_u1": float(max_u1),
            "max_u2": float(max_u2)
        })
        
    odb.close()
    
    # Print matched summary at target displacements
    print("\n--- MATCHED DISPLACEMENT SUMMARY FOR %s ---" % label)
    for td in target_disps:
        best = min(frame_summary, key=lambda f: abs(f["prescribed_u1"] - td))
        print("Target U1 = %.4f mm | Matched Frame %3d (U1 = %.4f mm) | max(d/U3) = %.6f | max(H/SDV1) = %.6f" % (
            td, best["frame_index"], best["prescribed_u1"], best["max_u3_phase"], best["max_sdv1_history"]))
            
    return frame_summary

if __name__ == "__main__":
    p_h1 = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    p_pk10r2 = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb")
    p_pk10r3 = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb")
    
    s_h1 = inspect_odb_fields(p_h1, "H1_CANONICAL_1389686")
    s_pk10r2 = inspect_odb_fields(p_pk10r2, "PK10R2_1390056")
    s_pk10r3 = inspect_odb_fields(p_pk10r3, "PK10R3_REFINED_TIP_1390098")
    
    # Save detailed JSON
    out = {
        "H1": s_h1,
        "PK10R2": s_pk10r2,
        "PK10R3": s_pk10r3
    }
    with open(os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/field_history_comparison.json"), "w") as f:
        json.dump(out, f, indent=2)
