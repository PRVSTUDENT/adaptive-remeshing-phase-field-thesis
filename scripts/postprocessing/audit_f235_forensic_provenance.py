#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Forensic provenance audit of H1, H2, PK10R2, and PK10R3.
Extracts exact RP node RF1-U1 histories and element SDVs directly from original ODBs.
"""

import sys
import os
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

ODBS = {
    "H1": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"),
    "H2": os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FREEU2_FULL_U050/M2CORR_H2_FREEU2_FULL_U050.odb"),
    "PK10R2": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.odb"),
    "PK10R3": os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.odb")
}

def extract_canonical_trajectory(odb_path, model_name):
    print("Extracting canonical trajectory for %s from %s" % (model_name, odb_path))
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[0]]
    
    u1_arr = []
    rf1_arr = []
    
    # 1. Search in history regions for Node set N_RP or RP node
    found_hist = False
    for hr_name in step.historyRegions.keys():
        if "RP" in hr_name.upper() or "99999" in hr_name:
            hr = step.historyRegions[hr_name]
            if 'U1' in hr.historyOutputs and 'RF1' in hr.historyOutputs:
                u_data = hr.historyOutputs['U1'].data
                rf_data = hr.historyOutputs['RF1'].data
                for (t1, u), (t2, rf) in zip(u_data, rf_data):
                    u1_arr.append(float(u))
                    rf1_arr.append(abs(float(rf)))
                found_hist = True
                print("  Found history output in %s: %d points" % (hr_name, len(u1_arr)))
                break
                
    if not found_hist:
        # Fallback to field output on node 99999 or node 1
        print("  Extracting from fieldOutputs...")
        for frame in step.frames:
            t = frame.frameValue
            if 'U' in frame.fieldOutputs and 'RF' in frame.fieldOutputs:
                u_f = frame.fieldOutputs['U']
                rf_f = frame.fieldOutputs['RF']
                
                # Check for RP node 99999 or sum RF on bottom nodes
                for val in rf_f.values:
                    if getattr(val, 'nodeLabel', None) == 99999:
                        rf1_arr.append(abs(float(val.data[0])))
                        break
                for val in u_f.values:
                    if getattr(val, 'nodeLabel', None) == 99999:
                        u1_arr.append(abs(float(val.data[0])))
                        break
                        
    odb.close()
    
    u_np = np.array(u1_arr)
    rf_np = np.array(rf1_arr)
    
    # Compute metrics
    if len(u_np) > 1:
        mask = (u_np > 0.0001) & (u_np <= 0.003)
        if np.sum(mask) >= 2:
            p = np.polyfit(u_np[mask], rf_np[mask], 1)
            k0 = float(p[0])
        else:
            k0 = float(rf_np[1] / u_np[1])
            
        peak_idx = int(np.argmax(rf_np))
        peak_rf = float(rf_np[peak_idx])
        peak_u = float(u_np[peak_idx])
        term_rf = float(rf_np[-1])
        term_u = float(u_np[-1])
        work = float(np.trapz(rf_np, u_np))
    else:
        k0 = peak_rf = peak_u = term_rf = term_u = work = 0.0
        
    return {
        "model": model_name,
        "k0": k0,
        "peak_rf1": peak_rf,
        "peak_u1": peak_u,
        "terminal_rf1": term_rf,
        "terminal_u1": term_u,
        "work": work,
        "num_frames": len(u_np)
    }

if __name__ == "__main__":
    results = {}
    for name, path in ODBS.items():
        results[name] = extract_canonical_trajectory(path, name)
        
    print("================================================================================")
    print("CANONICAL TRAJECTORY PROVENANCE AUDIT")
    print("================================================================================")
    print(json.dumps(results, indent=2))
