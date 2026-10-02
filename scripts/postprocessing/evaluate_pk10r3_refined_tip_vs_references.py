#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Evaluate M2CORR_PK10R3_REFINED_TIP (Job 1390098) against Canonical H1 (1389686),
H2 (1389687), and PK10R2 (1390056).
"""

import sys
import os
import json
import numpy as np

# Path definitions
ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

ODB_PATHS = {
    "H1": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"),
    "H2": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb"),
    "PK10R2": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb"),
    "PK10R3": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb")
}

from odbAccess import openOdb

def extract_trajectory(odb_path):
    print("Extracting trajectory from: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    
    u1_list = []
    rf1_list = []
    
    # Try history output first
    hist_regions = step.historyRegions
    rp_key = None
    for k in hist_regions.keys():
        if "RP" in k.upper() or "99999" in k or "ASSEMBLY" in k:
            rp_key = k
            break
    if rp_key is None and len(hist_regions) > 0:
        rp_key = hist_regions.keys()[0]
        
    if rp_key and 'U1' in hist_regions[rp_key].historyOutputs and 'RF1' in hist_regions[rp_key].historyOutputs:
        u1_data = hist_regions[rp_key].historyOutputs['U1'].data
        rf1_data = hist_regions[rp_key].historyOutputs['RF1'].data
        for (t1, u), (t2, rf) in zip(u1_data, rf1_data):
            u1_list.append(float(u))
            rf1_list.append(abs(float(rf)))
    else:
        # Fallback to frame field outputs
        for frame in step.frames:
            t = frame.frameValue
            if 'U' in frame.fieldOutputs and 'RF' in frame.fieldOutputs:
                u_field = frame.fieldOutputs['U']
                rf_field = frame.fieldOutputs['RF']
                # find RP node
                for val in u_field.values:
                    if val.nodeLabel == 99999 or val.nodeLabel == 1:
                        u1_list.append(abs(float(val.data[0])))
                        break
                for val in rf_field.values:
                    if val.nodeLabel == 99999 or val.nodeLabel == 1:
                        rf1_list.append(abs(float(val.data[0])))
                        break
                        
    odb.close()
    return np.array(u1_list), np.array(rf1_list)

def extract_matched_fields(odb_path, target_u1_list):
    print("Extracting matched fields from: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    step_name = odb.steps.keys()[0]
    step = odb.steps[step_name]
    
    results = {}
    frames = step.frames
    frame_u1 = []
    for f in frames:
        t = f.frameValue
        u_rp = 0.05 * t
        frame_u1.append((u_rp, f))
        
    for target_u1 in target_u1_list:
        best_diff = 1e9
        best_frame = None
        best_u1 = 0.0
        for u_rp, f in frame_u1:
            if abs(u_rp - target_u1) < best_diff:
                best_diff = abs(u_rp - target_u1)
                best_frame = f
                best_u1 = u_rp
                
        max_d = 0.0
        max_h = 0.0
        
        if 'U' in best_frame.fieldOutputs:
            u_field = best_frame.fieldOutputs['U']
            for v in u_field.values:
                if len(v.data) >= 3:
                    d_val = float(v.data[2])
                    if d_val > max_d:
                        max_d = d_val
                        
        if 'SDV_SDV1' in best_frame.fieldOutputs:
            h_field = best_frame.fieldOutputs['SDV_SDV1']
            for v in h_field.values:
                h_val = float(v.data)
                if h_val > max_h:
                    max_h = h_val
        elif 'SDV1' in best_frame.fieldOutputs:
            h_field = best_frame.fieldOutputs['SDV1']
            for v in h_field.values:
                h_val = float(v.data)
                if h_val > max_h:
                    max_h = h_val
                    
        results[str(target_u1)] = {
            "matched_u1": float(best_u1),
            "max_d": float(max_d),
            "max_H": float(max_h)
        }
        
    odb.close()
    return results

def compute_metrics(u1, rf1):
    if len(u1) < 2:
        return {}
    mask = (u1 > 0.0001) & (u1 <= 0.003)
    if np.sum(mask) >= 2:
        p = np.polyfit(u1[mask], rf1[mask], 1)
        k0 = float(p[0])
    else:
        k0 = float(rf1[1] / u1[1]) if u1[1] > 0 else 0.0
        
    peak_idx = int(np.argmax(rf1))
    peak_rf1 = float(rf1[peak_idx])
    peak_u1 = float(u1[peak_idx])
    terminal_rf1 = float(rf1[-1])
    terminal_u1 = float(u1[-1])
    work = float(np.trapz(rf1, u1))
    
    return {
        "K0": k0,
        "peak_RF1": peak_rf1,
        "peak_U1": peak_u1,
        "terminal_RF1": terminal_rf1,
        "terminal_U1": terminal_u1,
        "total_work": work,
        "softening_ratio": float(terminal_rf1 / peak_rf1) if peak_rf1 > 0 else 1.0
    }

if __name__ == "__main__":
    targets = [0.005, 0.010, 0.0125, 0.020, 0.050]
    out = {}
    
    for case, path in ODB_PATHS.items():
        if not os.path.exists(path):
            print("WARNING: Path %s does not exist!" % path)
            continue
        u1, rf1 = extract_trajectory(path)
        metrics = compute_metrics(u1, rf1)
        fields = extract_matched_fields(path, targets)
        out[case] = {
            "metrics": metrics,
            "fields": fields,
            "trajectory_points": len(u1)
        }
        
    print("================================================================================")
    print("SCIENTIFIC EVALUATION SUMMARY: PK10R3 vs CANONICAL REFERENCES")
    print("================================================================================")
    print(json.dumps(out, indent=2))
    
    out_file = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/scientific_evaluation.json")
    with open(out_file, "w") as f:
        json.dump(out, f, indent=2)
    print("Saved evaluation to %s" % out_file)
