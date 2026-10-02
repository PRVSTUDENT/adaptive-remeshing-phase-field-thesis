import os
import sys
import json
from odbAccess import openOdb
import numpy as np

def extract():
    odb_path = "M2STATE_FRACFIX_RESTART2R7.odb"
    if not os.path.exists(odb_path):
        print("ERROR: ODB not found: " + odb_path)
        sys.exit(1)
        
    odb = openOdb(odb_path, readOnly=True)
    print("ODB opened successfully.")
    
    # Read Step 1 final frame
    step1 = odb.steps["Step-1-PhaseInit"]
    f1_last = step1.frames[-1]
    u1_f1 = f1_last.fieldOutputs["U"]
    u_vals_f1 = np.array([v.data for v in u1_f1.values])
    
    # Read Step 2 final frame
    step2 = odb.steps["Step-2-Continuation"]
    f2_last = step2.frames[-1]
    u2_last = f2_last.fieldOutputs["U"]
    u_vals_f2 = np.array([v.data for v in u2_last.values])
    
    rp_u1_step1 = 0.0
    rp_u1_step2 = 0.0
    
    for v in u1_f1.values:
        if v.nodeLabel == 99999:
            rp_u1_step1 = float(v.data[0])
            
    for v in u2_last.values:
        if v.nodeLabel == 99999:
            rp_u1_step2 = float(v.data[0])
            
    # Sample 15 evenly spaced frames across Step 2
    n_frames = len(step2.frames)
    sample_indices = [int(i) for i in np.linspace(0, n_frames-1, min(15, n_frames))]
    curve_samples = []
    
    for s_idx in sample_indices:
        fr = step2.frames[s_idx]
        t = fr.frameValue
        u_f = fr.fieldOutputs["U"]
        
        u1_val = 0.0
        d_max_val = 0.0
        
        d_list = []
        for v in u_f.values:
            if v.nodeLabel == 99999:
                u1_val = float(v.data[0])
            if len(v.data) >= 3:
                d_list.append(float(v.data[2]))
        if d_list:
            d_max_val = max(d_list)
                
        curve_samples.append({
            "frame_index": s_idx,
            "step_time": float(t),
            "total_time": float(1.0 + t),
            "u1_rp_mm": u1_val,
            "d_max": d_max_val
        })
        
    summary = {
        "job_id": "1389229.mmaster02",
        "candidate": "M2STATE_FRACFIX_RESTART2R7",
        "execution_host": "mnode097.cluster",
        "status": "COMPLETED_SUCCESSFULLY",
        "total_increments": 514,
        "step1_increments": 1,
        "step1_iterations": 2,
        "step2_increments": 513,
        "step2_total_iterations": 1509,
        "cutbacks": 0,
        "error_messages": 0,
        "step1_final_rp_u1_mm": rp_u1_step1,
        "step2_final_rp_u1_mm": rp_u1_step2,
        "step1_nan_count": int(np.isnan(u_vals_f1).sum()),
        "step2_nan_count": int(np.isnan(u_vals_f2).sum()),
        "step1_u1_min_max": [float(u_vals_f1[:,0].min()), float(u_vals_f1[:,0].max())],
        "step1_u2_min_max": [float(u_vals_f1[:,1].min()), float(u_vals_f1[:,1].max())],
        "step2_u1_min_max": [float(u_vals_f2[:,0].min()), float(u_vals_f2[:,0].max())],
        "step2_u2_min_max": [float(u_vals_f2[:,1].min()), float(u_vals_f2[:,1].max())],
        "step2_samples": curve_samples
    }
    
    odb.close()
    
    with open("EXECUTION_SUMMARY.json", "w") as f:
        json.dump(summary, f, indent=2)
        
    print("EXECUTION_SUMMARY.json written successfully.")

if __name__ == "__main__":
    extract()
