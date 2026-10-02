#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deterministic Post-Processing and Evaluation for Corrected Stage-E Continuous Baselines
Jobs: 1390527.mmaster02 (Refined) and 1390528.mmaster02 (Coarsened)
"""

import os
import sys
import json
import numpy as np
from odbAccess import openOdb

def evaluate_odb(job_name, odb_path, out_dir):
    print("Evaluating %s from %s..." % (job_name, odb_path))
    odb = openOdb(path=odb_path, readOnly=True)
    
    step_name = "ShearStep"
    if step_name not in odb.steps:
        step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    
    num_frames = len(step.frames)
    print("  Found %d frames in step '%s'" % (num_frames, step_name))
    
    # Locate Reference Point Node 99999
    rp_node_label = 99999
    
    curve_data = []
    
    for frame_idx, frame in enumerate(step.frames):
        time_val = frame.frameValue
        u_field = frame.fieldOutputs['U'] if 'U' in frame.fieldOutputs else None
        rf_field = frame.fieldOutputs['RF'] if 'RF' in frame.fieldOutputs else None
        
        rp_u1 = 0.0
        rp_rf1 = 0.0
        
        if u_field is not None:
            for val in u_field.values:
                if val.nodeLabel == rp_node_label:
                    rp_u1 = float(val.data[0])
                    break
        if rf_field is not None:
            for val in rf_field.values:
                if val.nodeLabel == rp_node_label:
                    rp_rf1 = float(val.data[0])
                    break
                    
        # Damage field statistics if available
        d_max = 0.0
        d_min = 0.0
        if u_field is not None:
            u3_vals = [val.data[2] for val in u_field.values if len(val.data) >= 3]
            if len(u3_vals) > 0:
                d_max = float(np.max(u3_vals))
                d_min = float(np.min(u3_vals))
                
        phys_u1 = 0.050 * time_val
        
        curve_data.append({
            "frame": frame_idx,
            "step_time": float(time_val),
            "phys_u1_mm": float(phys_u1),
            "rp_u1_extracted_mm": float(rp_u1),
            "rp_rf1_kN": float(rp_rf1),
            "d_min": float(d_min),
            "d_max": float(d_max)
        })
        
    odb.close()
    
    # Save CSV
    csv_path = os.path.join(out_dir, "force_displacement_curve.csv")
    with open(csv_path, "w") as fp:
        fp.write("frame,step_time,phys_u1_mm,rp_u1_extracted_mm,rp_rf1_kN,d_min,d_max\n")
        for row in curve_data:
            fp.write("%d,%.8e,%.8e,%.8e,%.8e,%.8e,%.8e\n" % (
                row["frame"], row["step_time"], row["phys_u1_mm"],
                row["rp_u1_extracted_mm"], row["rp_rf1_kN"],
                row["d_min"], row["d_max"]
            ))
            
    # Find peak
    rf_vals = [r["rp_rf1_kN"] for r in curve_data]
    peak_idx = int(np.argmax(rf_vals))
    peak_row = curve_data[peak_idx]
    term_row = curve_data[-1]
    
    summary = {
        "job_name": job_name,
        "total_frames": num_frames,
        "peak_frame": peak_row["frame"],
        "peak_step_time": peak_row["step_time"],
        "peak_u1_mm": peak_row["phys_u1_mm"],
        "peak_rf1_kN": peak_row["rp_rf1_kN"],
        "terminal_frame": term_row["frame"],
        "terminal_step_time": term_row["step_time"],
        "terminal_u1_mm": term_row["phys_u1_mm"],
        "terminal_rf1_kN": term_row["rp_rf1_kN"],
        "terminal_d_max": term_row["d_max"],
        "terminal_d_min": term_row["d_min"]
    }
    
    json_path = os.path.join(out_dir, "postprocessing_summary.json")
    with open(json_path, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    print("  Peak RF1: %.6f kN at U1 = %.6f mm (Frame %d)" % (summary["peak_rf1_kN"], summary["peak_u1_mm"], summary["peak_frame"]))
    print("  Terminal RF1: %.6f kN at U1 = %.6f mm (Frame %d), d_max = %.6f" % (summary["terminal_rf1_kN"], summary["terminal_u1_mm"], summary["terminal_frame"], summary["terminal_d_max"]))
    return summary

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Evaluate Refined Job 1390527
    ref_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL")
    ref_odb = os.path.join(ref_dir, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.odb")
    sum_ref = evaluate_odb("M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL (1390527)", ref_odb, ref_dir)
    
    # 2. Evaluate Coarsened Job 1390528
    crs_dir = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL")
    crs_odb = os.path.join(crs_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.odb")
    sum_crs = evaluate_odb("M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL (1390528)", crs_odb, crs_dir)
    
    combined = {
        "refined_job_1390527": sum_ref,
        "coarsened_job_1390528": sum_crs
    }
    
    out_summary = os.path.join(base_dir, "corrected_e1_baselines_evaluation_summary.json")
    with open(out_summary, "w") as fp:
        json.dump(combined, fp, indent=2)
    print("\nSaved combined evaluation summary to %s" % out_summary)

if __name__ == "__main__":
    main()
