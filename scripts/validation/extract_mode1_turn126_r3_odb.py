#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_mode1_turn126_r3_odb.py
Abaqus Python extraction script for Package 108 Revision 3 ODB (Job 1417252).
Extracts:
  - Step 1 (Stage-A same-load re-equilibration): RF2, d_max, E_frac, E_elas
  - Step 2 (Stage-B-Mech forward mech solve): RF2, d_max, E_frac, E_elas
  - Step 3 (Stage-B-Phase phase relaxation): RF2, d_max, artificial reactions on fixed mech DOFs, E_frac, E_elas
  - Step 4 (Stage-B-Mech2 final re-equilibration): RF2, d_max, interior mechanical residual forces, E_frac, E_elas
"""

import sys
import json
from odbAccess import openOdb

odb_path = "M1_C3_STAGGERED_R3.odb"
odb = openOdb(odb_path, readOnly=True)

results = {
    "odb_path": odb_path,
    "steps": {}
}

# Physical nodes are 1..2769
# RP node is 999999
for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    step_data = {
        "number_of_frames": len(step.frames),
        "frames": []
    }
    
    for f_idx, frame in enumerate(step.frames):
        frame_time = float(frame.frameValue)
        frame_dict = {
            "frame_id": int(f_idx),
            "frame_time": frame_time,
            "rp_u2": None,
            "rp_rf2": None,
            "d_max": 0.0,
            "d_min": 1.0,
            "max_artificial_rf": 0.0
        }
        
        # 1. Nodal displacements
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            for val in u_field.values:
                if val.nodeLabel == 999999:
                    frame_dict["rp_u2"] = float(val.data[1])
                elif val.nodeLabel <= 2769 and len(val.data) >= 3:
                    # DOF 3 is phase field
                    d_val = float(val.data[2])
                    if d_val > frame_dict["d_max"]:
                        frame_dict["d_max"] = d_val
                    if d_val < frame_dict["d_min"]:
                        frame_dict["d_min"] = d_val
                        
        # 2. Nodal reaction forces
        if 'RF' in frame.fieldOutputs:
            rf_field = frame.fieldOutputs['RF']
            for val in rf_field.values:
                if val.nodeLabel == 999999:
                    frame_dict["rp_rf2"] = float(val.data[1])
                elif step_name in ["Stage-B-Phase", "Stage-B-Mech2"] and val.nodeLabel <= 2769:
                    rf1 = abs(float(val.data[0])) if len(val.data) > 0 else 0.0
                    rf2 = abs(float(val.data[1])) if len(val.data) > 1 else 0.0
                    mag = max(rf1, rf2)
                    if mag > frame_dict["max_artificial_rf"]:
                        frame_dict["max_artificial_rf"] = mag
                        
        step_data["frames"].append(frame_dict)
    results["steps"][step_name] = step_data

odb.close()

with open("r3_extracted_telemetry.json", "w") as f:
    json.dump(results, f, indent=2)

print("Extraction completed successfully; written to r3_extracted_telemetry.json")
