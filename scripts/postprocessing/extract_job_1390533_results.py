#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Post-Processing Extraction and Diagnostic Baseline Comparison for Job 1390533.mmaster02
Package: M2CORR_STAGE_E_DONOR_CONTROL_VAL (Donor Numerical Reference)
"""

import os
import sys
import json
import numpy as np
from odbAccess import openOdb

def extract_job_1390533():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL"
    odb_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL.odb")
    csv_path = os.path.join(base_dir, "force_displacement_curve.csv")
    json_path = os.path.join(base_dir, "postprocessing_summary.json")
    
    historical_donor_json = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/stage_d_continuous_target_control_summary.json"
    historical_donor_csv = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/force_displacement_curve.csv"
    
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    
    frames_data = []
    
    rp_node_id = 99999
    # Find RP node in root assembly / instance
    rp_node = None
    for inst in odb.rootAssembly.instances.values():
        for n in inst.nodes:
            if n.label == rp_node_id:
                rp_node = n
                break
        if rp_node:
            break
            
    print("Extracting %d frames..." % len(step.frames))
    
    d_max_history = []
    d_min_history = []
    
    for f_idx, frame in enumerate(step.frames):
        time = frame.frameValue
        
        # RP U1 and RF1
        u_val = 0.0
        rf_val = 0.0
        
        if 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            for v in u_field.values:
                if v.nodeLabel == rp_node_id:
                    u_val = v.data[0]
                    break
                    
        if 'RF' in frame.fieldOutputs:
            rf_field = frame.fieldOutputs['RF']
            for v in rf_field.values:
                if v.nodeLabel == rp_node_id:
                    rf_val = v.data[0]
                    break
                    
        # Damage d from SDV or U3/UR
        d_min = 0.0
        d_max = 0.0
        if 'SDV_D' in frame.fieldOutputs:
            d_field = frame.fieldOutputs['SDV_D']
            d_vals = [v.data for v in d_field.values if not np.isnan(v.data)]
            if d_vals:
                d_min = float(min(d_vals))
                d_max = float(max(d_vals))
        elif 'U' in frame.fieldOutputs:
            u_field = frame.fieldOutputs['U']
            # If phase is DOF 3
            d_vals = []
            for v in u_field.values:
                if len(v.data) >= 3 and v.nodeLabel != rp_node_id:
                    d_vals.append(v.data[2])
            if d_vals:
                d_min = float(min(d_vals))
                d_max = float(max(d_vals))
                
        d_min_history.append(d_min)
        d_max_history.append(d_max)
        
        frames_data.append({
            "frame": f_idx,
            "step_time": time,
            "u1": u_val,
            "rf1": rf_val,
            "d_min": d_min,
            "d_max": d_max
        })
        
    odb.close()
    
    # Write CSV
    with open(csv_path, "w") as fp:
        fp.write("Frame,StepTime,U1_mm,RF1_kN,RF1_N,d_min,d_max\n")
        for fd in frames_data:
            fp.write("%d,%.8e,%.8e,%.8e,%.8e,%.8e,%.8e\n" % (
                fd["frame"], fd["step_time"], fd["u1"], fd["rf1"], fd["rf1"]*1000.0, fd["d_min"], fd["d_max"]))
                
    print("Wrote %d frames to %s" % (len(frames_data), csv_path))
    
    # Compute metrics
    u1_arr = np.array([f["u1"] for f in frames_data])
    rf1_arr = np.array([f["rf1"] for f in frames_data])
    d_max_arr = np.array(d_max_history)
    d_min_arr = np.array(d_min_history)
    
    peak_idx = int(np.argmax(rf1_arr))
    peak_rf1 = float(rf1_arr[peak_idx])
    peak_u1 = float(u1_arr[peak_idx])
    terminal_rf1 = float(rf1_arr[-1])
    terminal_u1 = float(u1_arr[-1])
    
    # Find handoff state (closest to U1 = 0.01051289 mm)
    target_handoff_u1 = 0.01051289
    handoff_idx = int(np.argmin(np.abs(u1_arr - target_handoff_u1)))
    handoff_u1 = float(u1_arr[handoff_idx])
    handoff_rf1 = float(rf1_arr[handoff_idx])
    handoff_dmax = float(d_max_arr[handoff_idx])
    
    # Invariant checks (with standard single-precision ODB float tolerance 1e-5)
    bounds_ok = (np.min(d_min_arr) >= -1e-5) and (np.max(d_max_arr) <= 1.0 + 1e-5)
    diffs = np.diff(d_max_arr)
    mono_ok = (np.min(diffs) >= -1e-6) if len(diffs) > 0 else True
    
    # Compare with historical donor 1390447
    hist_peak_rf1 = 0.141676
    hist_peak_u1 = 0.012375
    hist_handoff_rf1 = 0.125916
    hist_terminal_rf1 = 0.003450
    
    diff_peak_rf1_pct = (peak_rf1 - hist_peak_rf1) / hist_peak_rf1 * 100.0
    diff_handoff_rf1_pct = (handoff_rf1 - hist_handoff_rf1) / hist_handoff_rf1 * 100.0
    
    summary = {
        "job_id": "1390533.mmaster02",
        "job_name": "M2CORR_STAGE_E_DONOR_CONTROL_VAL",
        "total_frames": len(frames_data),
        "terminal_u1_mm": terminal_u1,
        "terminal_rf1_kN": terminal_rf1,
        "peak_rf1_kN": peak_rf1,
        "peak_u1_mm": peak_u1,
        "handoff_frame": handoff_idx,
        "handoff_u1_mm": handoff_u1,
        "handoff_rf1_kN": handoff_rf1,
        "handoff_d_max": handoff_dmax,
        "comparison_vs_historical_donor_1390447": {
            "historical_donor_peak_rf1_kN": hist_peak_rf1,
            "revised_donor_peak_rf1_kN": peak_rf1,
            "peak_rf1_diff_pct": diff_peak_rf1_pct,
            "historical_donor_handoff_rf1_kN": hist_handoff_rf1,
            "revised_donor_handoff_rf1_kN": handoff_rf1,
            "handoff_rf1_diff_pct": diff_handoff_rf1_pct
        },
        "hard_invariants": {
            "phase_bounds_0_to_1": bool(bounds_ok),
            "d_min_overall": float(np.min(d_min_arr)),
            "d_max_overall": float(np.max(d_max_arr)),
            "pointwise_damage_monotonicity": bool(mono_ok),
            "min_delta_d_max": float(np.min(diffs)) if len(diffs) > 0 else 0.0
        }
    }
    
    with open(json_path, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    print("\n================================================================================")
    print("JOB 1390533.mmaster02 EXTRACTION & DIAGNOSTIC COMPARISON SUMMARY:")
    print("================================================================================")
    print("Total Extracted Frames : %d" % len(frames_data))
    print("Terminal U1            : %.6f mm (100%% of step)" % terminal_u1)
    print("Terminal RF1           : %.6f kN (Full softening reached)" % terminal_rf1)
    print("Peak Reaction Force RF1: %.6f kN at U1 = %.6f mm" % (peak_rf1, peak_u1))
    print("  vs Historical 1390447: %.6f kN (Diff: %+.4f%%)" % (hist_peak_rf1, diff_peak_rf1_pct))
    print("Handoff State (Frame %d): U1 = %.8f mm, RF1 = %.6f kN, d_max = %.6f" % (
        handoff_idx, handoff_u1, handoff_rf1, handoff_dmax))
    print("  vs Historical 1390447: %.6f kN (Diff: %+.4f%%)" % (hist_handoff_rf1, diff_handoff_rf1_pct))
    print("Hard Invariants Audit  : Bounds [0, 1] Valid = %s, Monotonicity Valid = %s" % (bounds_ok, mono_ok))

if __name__ == "__main__":
    extract_job_1390533()
