#!/usr/bin/env python3
"""
Audit ODB nodal displacement field U for global DOF 3 (U3 / phase solution)
across all steps and frames of M2STATE_FRACFIX_RESTART1R1R5.odb.
"""

import sys
import os
import json

def audit_u3_phase(odb_path_str):
    import odbAccess
    odb = odbAccess.openOdb(odb_path_str)
    
    results = {
        "ODB_U3_phase_available": False,
        "frames": [],
        "phase_comparison": {}
    }
    
    # Check if U field exists in frames
    has_u3_data = False
    
    for step_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            if "U" not in frame.fieldOutputs:
                continue
                
            u_field = frame.fieldOutputs["U"]
            u3_vals = []
            
            for val in u_field.values:
                # Exclude reference node 99999
                if val.nodeLabel == 99999:
                    continue
                # Check component count
                if len(val.data) >= 3:
                    u3 = float(val.data[2])
                    if not (u3 != u3): # check not nan
                        u3_vals.append(u3)
            
            if u3_vals:
                has_u3_data = True
                f_min = min(u3_vals)
                f_max = max(u3_vals)
                f_mean = sum(u3_vals) / len(u3_vals)
                
                # Get prescribed displacement U1 on node 99999 if available
                u1_ref = None
                for val in u_field.values:
                    if val.nodeLabel == 99999:
                        u1_ref = float(val.data[0])
                        break
                        
                results["frames"].append({
                    "step": str(step_name),
                    "frame": f_idx,
                    "u1_prescribed": u1_ref,
                    "count": len(u3_vals),
                    "phase_min": f_min,
                    "phase_max": f_max,
                    "phase_mean": f_mean
                })
                
    results["ODB_U3_phase_available"] = has_u3_data
    odb.close()
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    odb_file = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART1R1R5.odb"
    audit_u3_phase(odb_file)
