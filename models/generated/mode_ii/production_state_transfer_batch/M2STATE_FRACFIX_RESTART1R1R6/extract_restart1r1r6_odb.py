#!/usr/bin/env python3
"""
Abaqus Python ODB Extractor for Production Candidate M2STATE_FRACFIX_RESTART1R1R6.
Compatible with Python 2.7 (Abaqus internal python) and Python 3.
Extracts:
1. Physical node U3 (phase field) across all frames for nodes in N_PHYSICAL (nodes 1..4998).
2. Reference Node 99999 U1 (prescribed displacement) across all frames.
3. System energy histories (ALLSE, ALLIE, ALLWK, ALLPD, ALLCD, ALLAE, ALLVD).
"""

import sys
import os
import json

def extract_r1r6_odb(odb_path_str):
    import odbAccess
    odb = odbAccess.openOdb(odb_path_str)
    
    results = {
        "candidate": "M2STATE_FRACFIX_RESTART1R1R6",
        "physical_nodes_u3": {},
        "ref_node_99999_u1": [],
        "energies": {},
        "frame_summaries": []
    }
    
    ref_node_id = 99999
    
    for step_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            frame_time = float(frame.frameValue)
            u1_ref = None
            
            # Extract U field
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                u3_dict = {}
                
                for val in u_field.values:
                    n_id = int(val.nodeLabel)
                    if n_id == ref_node_id:
                        u1_ref = float(val.data[0])
                    elif n_id <= 4998:
                        if len(val.data) >= 3:
                            u3_val = float(val.data[2])
                            if not (u3_val != u3_val): # not nan
                                u3_dict[n_id] = u3_val
                                
                key_name = str(step_name) + "_frame_" + str(f_idx)
                results["physical_nodes_u3"][key_name] = u3_dict
                
                if u3_dict:
                    vals = list(u3_dict.values())
                    f_min = min(vals)
                    f_max = max(vals)
                    f_mean = sum(vals) / len(vals)
                    results["frame_summaries"].append({
                        "step": str(step_name),
                        "frame": f_idx,
                        "time": frame_time,
                        "u1_ref": u1_ref,
                        "phase_min": f_min,
                        "phase_max": f_max,
                        "phase_mean": f_mean,
                        "node_count": len(vals)
                    })
                    
            if u1_ref is not None:
                results["ref_node_99999_u1"].append({
                    "step": str(step_name),
                    "frame": f_idx,
                    "time": frame_time,
                    "u1_mm": u1_ref
                })

        # History region energies
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
    odb_file = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART1R1R6.odb"
    res = extract_r1r6_odb(odb_file)
    print(json.dumps(res, indent=2))
