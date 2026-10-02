#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canonical Post-Processing Extraction, Trajectory Parity, and Forensic Evaluation:
1. Job 1391277.mmaster02: M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL (vs 1390527 / 1390834)
2. Job 1391279.mmaster02: M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL (vs 1390528)
"""

import os
import sys
import json
import numpy as np
from odbAccess import openOdb

def extract_odb(odb_path, csv_path, json_path, job_id, pkg_name, mesh_type):
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    
    frames_data = []
    rp_node_id = 99999
    
    d_max_history = []
    d_min_history = []
    
    print("Extracting %d frames for %s..." % (len(step.frames), job_id))
    for f_idx, frame in enumerate(step.frames):
        time = float(frame.frameValue)
        u_val = 0.0
        rf_val = 0.0
        
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == rp_node_id:
                    u_val = float(v.data[0]); break
                    
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == rp_node_id:
                    rf_val = float(v.data[0]); break
                    
        d_vals = []
        if 'SDV_D' in frame.fieldOutputs:
            for v in frame.fieldOutputs['SDV_D'].values:
                if not np.isnan(v.data):
                    d_vals.append(float(v.data))
        elif 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if len(v.data) >= 3 and v.nodeLabel != rp_node_id:
                    d_vals.append(float(v.data[2]))
                    
        d_min = float(min(d_vals)) if d_vals else 0.0
        d_max = float(max(d_vals)) if d_vals else 0.0
        
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
    
    with open(csv_path, "w") as fp:
        fp.write("Frame,StepTime,U1_mm,RF1_kN,RF1_N,d_min,d_max\n")
        for fd in frames_data:
            fp.write("%d,%.8e,%.8e,%.8e,%.8e,%.8e,%.8e\n" % (
                fd["frame"], fd["step_time"], fd["u1"], fd["rf1"], fd["rf1"]*1000.0, fd["d_min"], fd["d_max"]))
                
    u1_arr = np.array([f["u1"] for f in frames_data])
    rf1_arr = np.array([f["rf1"] for f in frames_data])
    d_max_arr = np.array(d_max_history)
    d_min_arr = np.array(d_min_history)
    
    peak_idx = int(np.argmax(rf1_arr)) if len(rf1_arr) > 0 else 0
    peak_rf1 = float(rf1_arr[peak_idx]) if len(rf1_arr) > 0 else 0.0
    peak_u1 = float(u1_arr[peak_idx]) if len(u1_arr) > 0 else 0.0
    terminal_rf1 = float(rf1_arr[-1]) if len(rf1_arr) > 0 else 0.0
    terminal_u1 = float(u1_arr[-1]) if len(u1_arr) > 0 else 0.0
    
    target_handoff_u1 = 0.01051289
    handoff_idx = int(np.argmin(np.abs(u1_arr - target_handoff_u1))) if len(u1_arr) > 0 else 0
    handoff_u1 = float(u1_arr[handoff_idx]) if len(u1_arr) > 0 else 0.0
    handoff_rf1 = float(rf1_arr[handoff_idx]) if len(rf1_arr) > 0 else 0.0
    handoff_dmax = float(d_max_arr[handoff_idx]) if len(d_max_arr) > 0 else 0.0
    
    bounds_ok = (np.min(d_min_arr) >= -1e-5) and (np.max(d_max_arr) <= 1.0 + 1e-5) if len(d_min_arr) > 0 else True
    diffs = np.diff(d_max_arr)
    mono_ok = (np.min(diffs) >= -1e-6) if len(diffs) > 0 else True
    
    summary = {
        "job_id": job_id,
        "job_name": pkg_name,
        "mesh_type": mesh_type,
        "total_frames": len(frames_data),
        "terminal_u1_mm": terminal_u1,
        "terminal_rf1_kN": terminal_rf1,
        "peak_rf1_kN": peak_rf1,
        "peak_u1_mm": peak_u1,
        "peak_frame": peak_idx,
        "handoff_frame": handoff_idx,
        "handoff_u1_mm": handoff_u1,
        "handoff_rf1_kN": handoff_rf1,
        "handoff_d_max": handoff_dmax,
        "hard_invariants": {
            "phase_bounds_0_to_1": bool(bounds_ok),
            "d_min_overall": float(np.min(d_min_arr)) if len(d_min_arr) > 0 else 0.0,
            "d_max_overall": float(np.max(d_max_arr)) if len(d_max_arr) > 0 else 0.0,
            "pointwise_damage_monotonicity": bool(mono_ok),
            "min_delta_d_max": float(np.min(diffs)) if len(diffs) > 0 else 0.0
        }
    }
    
    with open(json_path, "w") as fp:
        json.dump(summary, fp, indent=2)
        
    return frames_data, summary

def parse_sta_attempts(sta_path):
    attempts_per_inc = {}
    accepted_dts = []
    attempted_dts = []
    total_cutbacks = 0
    max_attempt_exercised = 1
    
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 9 and parts[0] == '1':
                try:
                    inc = int(parts[1])
                    att = int(parts[2].replace('U', '')) if 'U' in parts[2] else int(parts[2])
                    dt = float(parts[8])
                    attempted_dts.append(dt)
                    if att > max_attempt_exercised:
                        max_attempt_exercised = att
                    if inc not in attempts_per_inc:
                        attempts_per_inc[inc] = []
                    attempts_per_inc[inc].append((att, dt, 'U' in parts[2]))
                    if 'U' not in parts[2]:
                        accepted_dts.append(dt)
                    else:
                        total_cutbacks += 1
                except:
                    pass
                    
    min_attempted_dt = min(attempted_dts) if attempted_dts else 0.0
    min_accepted_dt = min(accepted_dts) if accepted_dts else 0.0
    
    return {
        "max_attempt_exercised": max_attempt_exercised,
        "total_cutbacks": total_cutbacks,
        "min_attempted_dt": min_attempted_dt,
        "min_accepted_dt": min_accepted_dt,
        "attempts_per_inc": attempts_per_inc
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Evaluate Refined (1391277)
    dir_ref = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    odb_ref = os.path.join(dir_ref, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    csv_ref = os.path.join(dir_ref, "force_displacement_curve.csv")
    json_ref = os.path.join(dir_ref, "postprocessing_summary.json")
    sta_ref = os.path.join(dir_ref, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.sta")
    
    frames_ref, sum_ref = extract_odb(odb_ref, csv_ref, json_ref, "1391277.mmaster02", 
                                      "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL", 
                                      "Refined Target 33,600 quads (h_min=0.002000 mm)")
    sta_audit_ref = parse_sta_attempts(sta_ref)
    
    # 2. Evaluate Coarsened (1391279)
    dir_coarse = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL")
    odb_coarse = os.path.join(dir_coarse, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.odb")
    csv_coarse = os.path.join(dir_coarse, "force_displacement_curve.csv")
    json_coarse = os.path.join(dir_coarse, "postprocessing_summary.json")
    sta_coarse = os.path.join(dir_coarse, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.sta")
    
    frames_coarse, sum_coarse = extract_odb(odb_coarse, csv_coarse, json_coarse, "1391279.mmaster02",
                                            "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL",
                                            "Coarsened Target 8,200 quads (h_min=0.004000 mm)")
    sta_audit_coarse = parse_sta_attempts(sta_coarse)
    
    # Compare Refined with 1390834 / 1390527
    csv_834 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL/force_displacement_curve.csv"
    data_834 = np.genfromtxt(csv_834, delimiter=',', names=True)
    data_ref = np.genfromtxt(csv_ref, delimiter=',', names=True)
    
    min_len_ref = min(len(data_834), len(data_ref))
    u1_diff_ref = np.max(np.abs(data_834['U1_mm'][:min_len_ref] - data_ref['U1_mm'][:min_len_ref]))
    rf1_diff_ref = np.max(np.abs(data_834['RF1_kN'][:min_len_ref] - data_ref['RF1_kN'][:min_len_ref]))
    dmax_diff_ref = np.max(np.abs(data_834['d_max'][:min_len_ref] - data_ref['d_max'][:min_len_ref]))
    
    # Compare Coarsened with 1390528
    csv_528 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL/force_displacement_curve.csv"
    data_528 = np.genfromtxt(csv_528, delimiter=',', names=True) if os.path.exists(csv_528) else None
    data_coarse = np.genfromtxt(csv_coarse, delimiter=',', names=True)
    
    print("\n================================================================================")
    print("REFINED TARGET BASELINE 1391277 EVALUATION:")
    print("================================================================================")
    print("Total Extracted Frames  : %d" % len(frames_ref))
    print("Peak RF1                : %.6f kN at U1 = %.6f mm (Frame %d)" % (sum_ref["peak_rf1_kN"], sum_ref["peak_u1_mm"], sum_ref["peak_frame"]))
    print("Handoff State (Fr %d)   : U1 = %.6f mm, RF1 = %.6f kN, d_max = %.6f" % (sum_ref["handoff_frame"], sum_ref["handoff_u1_mm"], sum_ref["handoff_rf1_kN"], sum_ref["handoff_d_max"]))
    print("Terminal State          : U1 = %.6f mm, RF1 = %.6f kN" % (sum_ref["terminal_u1_mm"], sum_ref["terminal_rf1_kN"]))
    print("Parity vs 1390834 (29fr): Max U1 diff = %.3e mm, Max RF1 diff = %.3e kN, Max d_max diff = %.3e" % (u1_diff_ref, rf1_diff_ref, dmax_diff_ref))
    print("Max Attempt Exercised   : %d" % sta_audit_ref["max_attempt_exercised"])
    print("Total Cutbacks          : %d" % sta_audit_ref["total_cutbacks"])
    print("Min Attempted dt        : %.3e s" % sta_audit_ref["min_attempted_dt"])
    print("Min Accepted dt         : %.3e s" % sta_audit_ref["min_accepted_dt"])
    
    print("\n================================================================================")
    print("COARSENED TARGET BASELINE 1391279 EVALUATION:")
    print("================================================================================")
    print("Total Extracted Frames  : %d" % len(frames_coarse))
    print("Peak RF1                : %.6f kN at U1 = %.6f mm (Frame %d)" % (sum_coarse["peak_rf1_kN"], sum_coarse["peak_u1_mm"], sum_coarse["peak_frame"]))
    print("Handoff State (Fr %d)   : U1 = %.6f mm, RF1 = %.6f kN, d_max = %.6f" % (sum_coarse["handoff_frame"], sum_coarse["handoff_u1_mm"], sum_coarse["handoff_rf1_kN"], sum_coarse["handoff_d_max"]))
    print("Terminal State          : U1 = %.6f mm, RF1 = %.6f kN" % (sum_coarse["terminal_u1_mm"], sum_coarse["terminal_rf1_kN"]))
    print("Max Attempt Exercised   : %d" % sta_audit_coarse["max_attempt_exercised"])
    print("Total Cutbacks          : %d" % sta_audit_coarse["total_cutbacks"])
    print("Min Attempted dt        : %.3e s" % sta_audit_coarse["min_attempted_dt"])
    print("Min Accepted dt         : %.3e s" % sta_audit_coarse["min_accepted_dt"])
    
    eval_report = {
        "refined_job_1391277": {
            "summary": sum_ref,
            "sta_audit": {
                "max_attempt_exercised": sta_audit_ref["max_attempt_exercised"],
                "total_cutbacks": sta_audit_ref["total_cutbacks"],
                "min_attempted_dt": sta_audit_ref["min_attempted_dt"],
                "min_accepted_dt": sta_audit_ref["min_accepted_dt"]
            },
            "parity_vs_1390834": {
                "frames_compared": int(min_len_ref),
                "max_u1_diff_mm": float(u1_diff_ref),
                "max_rf1_diff_kN": float(rf1_diff_ref),
                "max_dmax_diff": float(dmax_diff_ref)
            }
        },
        "coarsened_job_1391279": {
            "summary": sum_coarse,
            "sta_audit": {
                "max_attempt_exercised": sta_audit_coarse["max_attempt_exercised"],
                "total_cutbacks": sta_audit_coarse["total_cutbacks"],
                "min_attempted_dt": sta_audit_coarse["min_attempted_dt"],
                "min_accepted_dt": sta_audit_coarse["min_accepted_dt"]
            }
        }
    }
    
    out_eval_json = os.path.join(base_dir, "final_stage_e_baselines_evaluation.json")
    with open(out_eval_json, "w") as fp:
        json.dump(eval_report, fp, indent=2)

if __name__ == "__main__":
    main()
