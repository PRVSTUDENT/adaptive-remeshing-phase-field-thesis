#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Compare Refined Step 3 Release Physics against Donor and Matching Baseline
"""

import os
import sys
import json
import numpy as np
from odbAccess import openOdb

def extract_node_coords_and_state(odb_path):
    odb = openOdb(odb_path, readOnly=True)
    root_inst = odb.rootAssembly.instances.values()[0] if odb.rootAssembly.instances else None
    
    # Node coordinates map
    node_coords = {}
    if root_inst:
        for node in root_inst.nodes:
            node_coords[node.label] = (float(node.coordinates[0]), float(node.coordinates[1]))
            
    frames_data = []
    for s_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            rp_u1 = 0.0
            rp_rf1 = 0.0
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel == 99999: rp_u1 = float(v.data[0]); break
            if 'RF' in frame.fieldOutputs:
                for v in frame.fieldOutputs['RF'].values:
                    if v.nodeLabel == 99999: rp_rf1 = float(v.data[0]); break
                    
            d_map = {}
            if 'U' in frame.fieldOutputs:
                for v in frame.fieldOutputs['U'].values:
                    if v.nodeLabel != 99999 and len(v.data) >= 3:
                        d_map[v.nodeLabel] = float(v.data[2])
                        
            max_nid = max(d_map, key=d_map.get) if d_map else None
            max_d = d_map[max_nid] if max_nid else 0.0
            min_d = min(d_map.values()) if d_map else 0.0
            max_coord = node_coords.get(max_nid, (0.0, 0.0))
            
            # Hotspot node 16962
            d_16962 = d_map.get(16962, None)
            coord_16962 = node_coords.get(16962, (0.0, 0.0))
            
            frames_data.append({
                "step_name": s_name,
                "frame_in_step": f_idx,
                "frame_value": float(frame.frameValue),
                "rp_u1_mm": rp_u1,
                "rp_rf1_kN": rp_rf1,
                "max_d": max_d,
                "max_d_node": max_nid,
                "max_d_coord": max_coord,
                "min_d": min_d,
                "d_node_16962": d_16962,
                "coord_16962": coord_16962
            })
            
    odb.close()
    return frames_data

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    odb_1391300 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL.odb")
    odb_1391277 = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    
    data_1391300 = extract_node_coords_and_state(odb_1391300)
    data_1391277 = extract_node_coords_and_state(odb_1391277)
    
    print("================================================================================")
    print("PHYSICAL STATE EVOLUTION IN 1391300.mmaster02:")
    print("================================================================================")
    for f in data_1391300:
        print("Step %-18s Fr %d (t=%9.5f): RF1 = %9.6f kN | d_max = %8.6f at Node %5s %s | d_16962 = %s" % (
            f["step_name"], f["frame_in_step"], f["frame_value"], f["rp_rf1_kN"],
            f["max_d"], str(f["max_d_node"]), str(f["max_d_coord"]), str(f["d_node_16962"])
        ))
        
    print("\n================================================================================")
    print("MATCHING REFINED BASELINE (1391277.mmaster02) FRAMES AROUND HANDOFF:")
    print("================================================================================")
    for f in data_1391277:
        if 0.0100 <= f["rp_u1_mm"] <= 0.0110:
            print("Step %-18s Fr %d (U1=%9.6f mm): RF1 = %9.6f kN | d_max = %8.6f at Node %5s %s" % (
                f["step_name"], f["frame_in_step"], f["rp_u1_mm"], f["rp_rf1_kN"],
                f["max_d"], str(f["max_d_node"]), str(f["max_d_coord"])
            ))
            
    out_json = os.path.join(base_dir, "refined_step3_release_physics_comparison.json")
    with open(out_json, "w") as fp:
        json.dump({"1391300_frames": data_1391300, "1391277_frames": data_1391277}, fp, indent=2)
    print("\nSaved Physics Comparison to: %s" % out_json)

if __name__ == "__main__":
    main()
