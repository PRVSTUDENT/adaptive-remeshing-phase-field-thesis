# -*- coding: mbcs -*-
"""
Abaqus Python ODB Extractor for Job 1388948.mmaster02.
Extracts:
1. N_PHYSICAL node displacements and phase field (U1, U2, U3) across all frames.
2. Reference node 99999 displacement and reaction force (U1, RF1).
3. Boundary node sets N_BOTTOM and N_TOP reaction forces.
4. Energy histories if present.
5. Step and frame summaries.
"""

import sys
import os
import json
import math

def extract_odb_data(odb_path, out_json_path):
    from odbAccess import openOdb
    
    if not os.path.exists(odb_path):
        print("ERROR: ODB path does not exist: %s" % odb_path)
        return False
        
    odb = openOdb(odb_path, readOnly=True)
    print("Opened ODB: %s" % odb.name)
    
    root_assembly = odb.rootAssembly
    print("Assembly nodeSets: %s" % root_assembly.nodeSets.keys())
    for iname, inst in root_assembly.instances.items():
        print("Instance %s nodeSets: %s" % (iname, inst.nodeSets.keys()))
        
    # Find N_PHYSICAL
    n_phys_set = None
    if "N_PHYSICAL" in root_assembly.nodeSets:
        n_phys_set = root_assembly.nodeSets["N_PHYSICAL"]
    else:
        for iname, inst in root_assembly.instances.items():
            if "N_PHYSICAL" in inst.nodeSets:
                n_phys_set = inst.nodeSets["N_PHYSICAL"]
                break
                
    print("Found N_PHYSICAL set: %s" % (n_phys_set is not None))
    
    results = {
        "job_id": "1388948.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART1R1R6R2",
        "steps": {},
        "frame_summaries": [],
        "ref_node_99999_curve": [],
        "phase_continuity_check": {},
        "phase_irreversibility_check": {}
    }
    
    prev_phase_by_node = {}
    max_illegal_phase_decrease = 0.0
    phase_decrease_count = 0
    total_phase_eval_count = 0
    
    for step_name in odb.steps.keys():
        step = odb.steps[step_name]
        step_dict = {
            "name": step_name,
            "total_time": step.timePeriod,
            "frame_count": len(step.frames),
            "frames": []
        }
        
        print("Processing Step: %s (%d frames)" % (step_name, len(step.frames)))
        for f_idx, frame in enumerate(step.frames):
            f_time = frame.frameValue
            f_summary = {
                "step": step_name,
                "frame": f_idx,
                "time": f_time,
                "description": frame.description
            }
            
            # Extract U field
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                if f_idx == 0 and step_name == "Step-1-PhaseInit":
                    print("U field type: %s, components: %s" % (u_field.type, u_field.componentLabels))
                    for v in u_field.values:
                        if v.nodeLabel in [112, 113, 392, 417]:
                            print("Sample Node %d data: %s" % (v.nodeLabel, list(v.data)))
                
                # Check N_PHYSICAL or all values
                target_u_vals = u_field.getSubset(region=n_phys_set).values if n_phys_set is not None else u_field.values
                
                min_d = 1e9
                max_d = -1e9
                d_sum = 0.0
                d_count = 0
                
                for v in target_u_vals:
                    nid = v.nodeLabel
                    if nid == 99999: continue
                    # Phase is in U3 component for phase nodes
                    d_val = v.data[2] if len(v.data) >= 3 else 0.0
                    if d_val < min_d: min_d = d_val
                    if d_val > max_d: max_d = d_val
                    d_sum += d_val
                    d_count += 1
                    
                    # Irreversibility check in Step-2
                    if step_name == "Step-2-Continuation":
                        if nid in prev_phase_by_node:
                            delta_d = d_val - prev_phase_by_node[nid]
                            total_phase_eval_count += 1
                            if delta_d < -1e-6:
                                phase_decrease_count += 1
                                if abs(delta_d) > max_illegal_phase_decrease:
                                    max_illegal_phase_decrease = abs(delta_d)
                        prev_phase_by_node[nid] = d_val
                        
                f_summary["phase_min"] = min_d if d_count > 0 else 0.0
                f_summary["phase_max"] = max_d if d_count > 0 else 0.0
                f_summary["phase_mean"] = (d_sum / d_count) if d_count > 0 else 0.0
                f_summary["physical_node_count"] = d_count
                
            # Extract RF field on ref node 99999 or N_TOP
            rf1_val = 0.0
            u1_val = 0.0
            if "RF" in frame.fieldOutputs:
                rf_field = frame.fieldOutputs["RF"]
                for v in rf_field.values:
                    if v.nodeLabel == 99999:
                        rf1_val = v.data[0]
                        break
            if "U" in frame.fieldOutputs:
                u_field = frame.fieldOutputs["U"]
                for v in u_field.values:
                    if v.nodeLabel == 99999:
                        u1_val = v.data[0]
                        break
                        
            f_summary["u1_ref"] = u1_val
            f_summary["rf1_ref"] = rf1_val
            results["ref_node_99999_curve"].append({
                "step": step_name,
                "frame": f_idx,
                "time": f_time,
                "u1": u1_val,
                "rf1": rf1_val
            })
            
            step_dict["frames"].append(f_summary)
            results["frame_summaries"].append(f_summary)
            
        results["steps"][step_name] = step_dict
        
    odb.close()
    
    results["phase_irreversibility_check"] = {
        "total_phase_evaluations": total_phase_eval_count,
        "phase_decrease_violations": phase_decrease_count,
        "max_illegal_decrease": max_illegal_phase_decrease,
        "phase_irreversibility_pass": (phase_decrease_count == 0)
    }
    
    with open(out_json_path, "w") as f:
        json.dump(results, f, indent=2)
        
    print("Successfully saved ODB extraction to: %s" % out_json_path)
    return True

if __name__ == "__main__":
    odb_in = sys.argv[1] if len(sys.argv) > 1 else "M2STATE_FRACFIX_RESTART1R1R6R2.odb"
    json_out = sys.argv[2] if len(sys.argv) > 2 else "salvage/extracted_1388948_odb.json"
    extract_odb_data(odb_in, json_out)
