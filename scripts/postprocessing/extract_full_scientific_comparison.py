#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract SDV field history from PK10R3 (1390098) vs PK10R2 (1390056) vs H1 (1389686).
"""

import sys
import os
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def extract_case_details(odb_path, label):
    print("================================================================================")
    print("ANALYZING: %s (%s)" % (label, odb_path))
    print("================================================================================")
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[0]]
    
    # 1. History RP Trajectory
    u1_arr = []
    rf1_arr = []
    
    # Try history output
    for hr_name in step.historyRegions.keys():
        hr = step.historyRegions[hr_name]
        if 'U1' in hr.historyOutputs and 'RF1' in hr.historyOutputs:
            u_data = hr.historyOutputs['U1'].data
            rf_data = hr.historyOutputs['RF1'].data
            for (t1, u), (t2, rf) in zip(u_data, rf_data):
                u1_arr.append(float(u))
                rf1_arr.append(abs(float(rf)))
            break
            
    # 2. Frame-by-frame SDVs
    target_disps = [0.005, 0.010, 0.0125, 0.020, 0.035, 0.050]
    matched_results = {}
    
    for td in target_disps:
        # Find closest frame by frameValue (step time t in [0, 0.050])
        best_frame = min(step.frames, key=lambda f: abs(f.frameValue - td))
        t_val = best_frame.frameValue
        
        max_d = 0.0
        max_h = 0.0
        
        # Check SDVs
        if 'SDV' in best_frame.fieldOutputs:
            sdv_f = best_frame.fieldOutputs['SDV']
            for val in sdv_f.values:
                data = val.data
                if isinstance(data, (list, tuple, np.ndarray)):
                    # SDV9 = d (index 8), SDV13 = H (index 12)
                    if len(data) >= 9:
                        if data[8] > max_d:
                            max_d = float(data[8])
                    if len(data) >= 13:
                        if data[12] > max_h:
                            max_h = float(data[12])
                else:
                    if float(data) > max_d:
                        max_d = float(data)
                        
        # Also check separate SDV components if present
        if 'SDV9' in best_frame.fieldOutputs:
            for val in best_frame.fieldOutputs['SDV9'].values:
                if float(val.data) > max_d:
                    max_d = float(val.data)
        if 'SDV13' in best_frame.fieldOutputs:
            for val in best_frame.fieldOutputs['SDV13'].values:
                if float(val.data) > max_h:
                    max_h = float(val.data)
                    
        # Check U3 if present (for continuous H1/H2 models)
        if 'U' in best_frame.fieldOutputs:
            for val in best_frame.fieldOutputs['U'].values:
                if len(val.data) >= 3:
                    if float(val.data[2]) > max_d:
                        max_d = float(val.data[2])
                        
        matched_results[str(td)] = {
            "matched_u1": float(t_val),
            "max_d": float(max_d),
            "max_H": float(max_h)
        }
        
    odb.close()
    
    # Trajectory metrics
    u1_np = np.array(u1_arr)
    rf1_np = np.array(rf1_arr)
    
    if len(u1_np) > 1:
        mask = (u1_np > 0.0001) & (u1_np <= 0.003)
        if np.sum(mask) >= 2:
            p = np.polyfit(u1_np[mask], rf1_np[mask], 1)
            k0 = float(p[0])
        else:
            k0 = float(rf1_np[1] / u1_np[1])
            
        peak_idx = int(np.argmax(rf1_np))
        peak_rf = float(rf1_np[peak_idx])
        peak_u = float(u1_np[peak_idx])
        term_rf = float(rf1_np[-1])
        term_u = float(u1_np[-1])
        work = float(np.trapz(rf1_np, u1_np))
    else:
        k0 = 0.0
        peak_rf = 0.0
        peak_u = 0.0
        term_rf = 0.0
        term_u = 0.0
        work = 0.0
        
    metrics = {
        "K0": k0,
        "peak_RF1": peak_rf,
        "peak_U1": peak_u,
        "terminal_RF1": term_rf,
        "terminal_U1": term_u,
        "total_work": work,
        "softening_ratio": float(term_rf / peak_rf) if peak_rf > 0 else 1.0,
        "num_increments": len(u1_np)
    }
    
    print("\n--- RESULTS FOR %s ---" % label)
    print("K0: %.4f kN/mm | Peak RF1: %.5f kN at U1 = %.5f mm | Terminal RF1: %.5f kN | Work: %.6f kN*mm" % (
        metrics["K0"], metrics["peak_RF1"], metrics["peak_U1"], metrics["terminal_RF1"], metrics["total_work"]))
    print("Matched Fields:")
    for td, res in matched_results.items():
        print("  U1 = %.4f mm -> max(d) = %.6f, max(H) = %.6f kN/mm^2" % (
            float(td), res["max_d"], res["max_H"]))
            
    return {
        "metrics": metrics,
        "matched_fields": matched_results,
        "trajectory": {
            "u1": u1_arr,
            "rf1": rf1_arr
        }
    }

if __name__ == "__main__":
    p_h1 = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    p_h2 = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb")
    p_pk10r2 = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb")
    p_pk10r3 = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb")
    
    res_h1 = extract_case_details(p_h1, "H1_CANONICAL_1389686")
    res_h2 = extract_case_details(p_h2, "H2_CANONICAL_1389687")
    res_pk10r2 = extract_case_details(p_pk10r2, "PK10R2_1390056")
    res_pk10r3 = extract_case_details(p_pk10r3, "PK10R3_1390098")
    
    full_eval = {
        "H1": res_h1,
        "H2": res_h2,
        "PK10R2": res_pk10r2,
        "PK10R3": res_pk10r3
    }
    
    out_file = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/scientific_comparison_full.json")
    with open(out_file, "w") as f:
        # write without huge trajectory arrays for readability
        summary_out = {
            k: {
                "metrics": v["metrics"],
                "matched_fields": v["matched_fields"]
            } for k, v in full_eval.items()
        }
        json.dump(summary_out, f, indent=2)
    print("\nSaved full scientific comparison summary to %s" % out_file)
