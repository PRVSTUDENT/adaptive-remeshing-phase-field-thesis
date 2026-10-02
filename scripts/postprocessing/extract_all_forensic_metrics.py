#!/usr/bin/env python3
"""
Comprehensive extraction and calculation script for all forensic metrics A through O.
Runs on cluster with Abaqus Python or Python 3.
"""
from odbAccess import openOdb
import sys
import os
import json
import math

def run_extraction():
    odb_path = "M2STATE_FRACFIX_RESTART2R6.odb"
    odb = openOdb(odb_path, readOnly=True)
    
    root = odb.rootAssembly
    instance = root.instances['PART-1-1'] if 'PART-1-1' in root.instances else list(root.instances.values())[0]
    
    # 1. Node coordinates
    node_coords = {n.label: n.coordinates for n in instance.nodes}
    
    # 2. Extract RP (Node 99999) and Field Data Across All Steps and Frames
    frames_data = []
    
    for s_name, step in odb.steps.items():
        for f_idx, frame in enumerate(step.frames):
            t_step = frame.frameValue
            desc = frame.description
            
            # Extract RP U and RF
            rp_u1 = None
            rp_rf1 = None
            
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for v in u_field.values:
                    if v.nodeLabel == 99999:
                        rp_u1 = float(v.data[0])
                        break
                        
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for v in rf_field.values:
                    if v.nodeLabel == 99999:
                        rp_rf1 = float(v.data[0])
                        break
                        
            # Extract nodal displacements U1, U2
            u1_vals = []
            u2_vals = []
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for v in u_field.values:
                    if v.nodeLabel <= 9801:
                        u1_vals.append(float(v.data[0]))
                        u2_vals.append(float(v.data[1]))
                        
            frames_data.append({
                "step_name": s_name,
                "frame_index": f_idx,
                "step_time": float(t_step),
                "description": desc,
                "rp_u1": rp_u1,
                "rp_rf1": rp_rf1,
                "u1_max": max(u1_vals) if u1_vals else None,
                "u1_min": min(u1_vals) if u1_vals else None,
                "u2_max": max(u2_vals) if u2_vals else None,
                "u2_min": min(u2_vals) if u2_vals else None
            })
            
    odb.close()
    
    # 3. Read Energies from .dat file
    dat_path = "M2STATE_FRACFIX_RESTART2R6.dat"
    energies = []
    if os.path.exists(dat_path):
        with open(dat_path, "r") as f:
            for line in f:
                if "TOTAL ENERGY" in line or "ALLKE" in line or "ALLSE" in line or "ALLWK" in line or "ALLPD" in line:
                    energies.append(line.strip())
                    
    # 4. Save extracted metrics
    out = {
        "frames_history": frames_data,
        "energy_lines": energies
    }
    
    with open("EXTRACTED_ODB_METRICS.json", "w") as f_out:
        json.dump(out, f_out, indent=2)
        
    print("Extracted ODB metrics successfully saved to EXTRACTED_ODB_METRICS.json")
    for fd in frames_data:
        print("Step %s Frame %d (t=%.4e): RP_U1 = %s mm, RP_RF1 = %s kN" % (
            fd["step_name"], fd["frame_index"], fd["step_time"],
            ("%.8f" % fd["rp_u1"]) if fd["rp_u1"] is not None else "None",
            ("%.6f" % fd["rp_rf1"]) if fd["rp_rf1"] is not None else "None"
        ))

if __name__ == "__main__":
    run_extraction()
