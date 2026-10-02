#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Postprocessing extraction script for Stage-E Refined Target Continuous Baseline (Job 1390489.mmaster02)
"""

import os
import sys
import json
import csv
from odbAccess import openOdb

def extract_job_1390489():
    odb_path = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.odb"
    out_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL"
    
    if not os.path.exists(odb_path):
        print("Error: ODB not found at %s" % odb_path)
        sys.exit(1)
        
    odb = openOdb(odb_path, readOnly=True)
    print("Opened ODB: %s" % odb_path)
    print("Steps in ODB: %s" % list(odb.steps.keys()))
    
    curve_data = []
    frames_extracted = 0
    
    for step_name, step in odb.steps.items():
        print("Processing Step: %s (Total Frames: %d)" % (step_name, len(step.frames)))
        for f_idx, frame in enumerate(step.frames):
            t = float(frame.frameValue)
            inc = int(frame.incrementNumber)
            
            # Extract RP (Node 99999) reaction and displacement
            u1_val = 0.0
            u2_val = 0.0
            rf1_val = 0.0
            rf2_val = 0.0
            d_max = 0.0
            
            if 'U' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if val.nodeLabel == 99999:
                        u1_val = float(val.data[0])
                        u2_val = float(val.data[1])
                    if len(val.data) > 2:
                        d_k = float(val.data[2])
                        if d_k > d_max:
                            d_max = d_k
                            
            if 'RF' in frame.fieldOutputs:
                rf_field = frame.fieldOutputs['RF']
                for val in rf_field.values:
                    if val.nodeLabel == 99999:
                        rf1_val = float(val.data[0])
                        rf2_val = float(val.data[1])
                        
            curve_data.append({
                "frame_global_index": int(frames_extracted),
                "step_name": str(step_name),
                "increment_number": int(inc),
                "step_time": float(t),
                "physical_u1_mm": float(u1_val),
                "physical_u2_mm": float(u2_val),
                "rp_rf1_kn": float(rf1_val),
                "rp_rf2_kn": float(rf2_val),
                "d_max": float(d_max)
            })
            frames_extracted += 1
            
    odb.close()
    
    # Save CSV
    csv_path = os.path.join(out_dir, "force_displacement_curve.csv")
    with open(csv_path, "w", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=[
            "frame_global_index", "step_name", "increment_number", "step_time",
            "physical_u1_mm", "physical_u2_mm", "rp_rf1_kn", "rp_rf2_kn", "d_max"
        ])
        writer.writeheader()
        for row in curve_data:
            writer.writerow(row)
            
    # Save JSON summary
    summary = {
        "job_id": "1390489.mmaster02",
        "job_name": "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL",
        "total_frames_extracted": int(frames_extracted),
        "first_frame": curve_data[0] if curve_data else None,
        "last_frame": curve_data[-1] if curve_data else None,
        "status": "EXTRACTED_COMPLETED"
    }
    json_path = os.path.join(out_dir, "postprocessing_summary.json")
    with open(json_path, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    print("\nExtraction Summary:")
    print("  Total Frames Extracted: %d" % frames_extracted)
    if curve_data:
        print("  First Frame: Inc %d, Time = %.6e, U1 = %.6e mm, RF1 = %.6e kN" % (
            curve_data[0]["increment_number"], curve_data[0]["step_time"],
            curve_data[0]["physical_u1_mm"], curve_data[0]["rp_rf1_kn"]))
        print("  Last Frame : Inc %d, Time = %.6e, U1 = %.6e mm, RF1 = %.6e kN" % (
            curve_data[-1]["increment_number"], curve_data[-1]["step_time"],
            curve_data[-1]["physical_u1_mm"], curve_data[-1]["rp_rf1_kn"]))
    print("Saved CSV: %s" % csv_path)
    print("Saved JSON: %s" % json_path)

if __name__ == "__main__":
    extract_job_1390489()
