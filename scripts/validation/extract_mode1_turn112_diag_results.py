#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_mode1_turn112_diag_results.py
Abaqus Python extraction script for 4-element diagnostic patch results.
Extracts nodal displacements, reaction forces, and SDVs from VIS_QUADS.
"""
import sys
import json
from odbAccess import openOdb

odb_path = "M1_DIAG_SOLVE.odb"
odb = openOdb(odb_path, readOnly=True)

results = {
    "odb_path": odb_path,
    "steps": {}
}

for step_name in odb.steps.keys():
    step = odb.steps[step_name]
    step_data = {
        "frames": []
    }
    
    for f_idx, frame in enumerate(step.frames):
        frame_data = {
            "frame_id": int(f_idx),
            "time": float(frame.frameValue),
            "nodes": {},
            "elements": {}
        }
        
        # Nodal displacements
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            for val in u_field.values:
                nid = str(val.nodeLabel)
                data = list(val.data)
                frame_data["nodes"][nid] = {
                    "u1": float(data[0]) if len(data) > 0 else 0.0,
                    "u2": float(data[1]) if len(data) > 1 else 0.0,
                    "u3": float(data[2]) if len(data) > 2 else 0.0
                }
                
        # Nodal reactions
        if 'RF' in frame.fieldOutputs:
            rf_field = frame.fieldOutputs['RF']
            for val in rf_field.values:
                nid = str(val.nodeLabel)
                data = list(val.data)
                if nid not in frame_data["nodes"]:
                    frame_data["nodes"][nid] = {}
                frame_data["nodes"][nid]["rf1"] = float(data[0]) if len(data) > 0 else 0.0
                frame_data["nodes"][nid]["rf2"] = float(data[1]) if len(data) > 1 else 0.0
                frame_data["nodes"][nid]["rf3"] = float(data[2]) if len(data) > 2 else 0.0

        # Element SDVs from VIS_QUADS
        if 'SDV_SDV1' in frame.fieldOutputs or 'SDV1' in frame.fieldOutputs or 'SDV' in frame.fieldOutputs:
            sdv_key = 'SDV' if 'SDV' in frame.fieldOutputs else ('SDV1' if 'SDV1' in frame.fieldOutputs else 'SDV_SDV1')
            sdv_field = frame.fieldOutputs[sdv_key]
            for val in sdv_field.values:
                eid = str(val.elementLabel)
                if eid not in frame_data["elements"]:
                    frame_data["elements"][eid] = {}
                # Check data format
                if hasattr(val, 'data'):
                    try:
                        frame_data["elements"][eid]["sdv"] = [float(x) for x in list(val.data)]
                    except:
                        frame_data["elements"][eid]["sdv"] = float(val.data)
        else:
            # List all available field outputs
            frame_data["available_fields"] = list(frame.fieldOutputs.keys())
                
        step_data["frames"].append(frame_data)
        
    results["steps"][step_name] = step_data

odb.close()

out_json = "M1_DIAG_SOLVE_RESULTS.json"
with open(out_json, "w") as f:
    json.dump(results, f, indent=2)

print("SUCCESS: Extracted results to " + out_json)
