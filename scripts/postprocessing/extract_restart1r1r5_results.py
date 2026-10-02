#!/usr/bin/env python3
"""
Abaqus Python ODB Extractor for Production Restart Job 1388886.mmaster02 (M2STATE_FRACFIX_RESTART1R1R5).
Strict Python 2.7 / 3 compatible without external dependencies.
"""

import sys
import os
import json

def extract_odb_evidence(odb_path_str):
    import odbAccess
    odb = odbAccess.openOdb(odb_path_str)
    
    results = {
        "job_id": "1388886.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART1R1R5",
        "steps": {},
        "rf1_u1_history": [],
        "energies": {}
    }
    
    ref_node_id = 99999
    
    for step_name, step in odb.steps.items():
        step_data = {
            "num_frames": len(step.frames),
            "frames": []
        }
        
        for f_idx, frame in enumerate(step.frames):
            frame_time = frame.frameValue
            
            u1_val = None
            rf1_val = None
            
            # Displacement field
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                for val in u_field.values:
                    if val.nodeLabel == ref_node_id:
                        u1_val = float(val.data[0])
                        break
            
            # Reaction force field
            if "RF" in frame.fieldOutputs:
                rf_field = frame.fieldOutputs["RF"]
                for val in rf_field.values:
                    if val.nodeLabel == ref_node_id:
                        rf1_val = float(val.data[0])
                        break
            
            frame_info = {
                "frame_index": f_idx,
                "frame_value": float(frame_time),
                "u1_mm": u1_val,
                "rf1_N": rf1_val,
                "rf1_kN": (rf1_val / 1000.0) if rf1_val is not None else None
            }
            step_data["frames"].append(frame_info)
            
            if u1_val is not None and rf1_val is not None:
                results["rf1_u1_history"].append({
                    "step": str(step_name),
                    "frame": f_idx,
                    "step_time": float(frame_time),
                    "u1_mm": u1_val,
                    "rf1_N": rf1_val,
                    "rf1_kN": rf1_val / 1000.0
                })
        
        results["steps"][str(step_name)] = step_data
        
        # Energy history extraction
        if hasattr(step, "historyRegions") and step.historyRegions:
            for h_name, h_region in step.historyRegions.items():
                if "Assembly" in h_name or "Node" in h_name or "Element" in h_name or "Whole" in h_name:
                    for e_key, e_output in h_region.historyOutputs.items():
                        e_vals = [(float(t), float(v)) for t, v in e_output.data]
                        key_name = str(step_name) + "_" + str(e_key)
                        results["energies"][key_name] = e_vals
    
    odb.close()
    return results

if __name__ == "__main__":
    odb_file = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART1R1R5.odb"
    res = extract_odb_evidence(odb_file)
    print(json.dumps(res, indent=2))
