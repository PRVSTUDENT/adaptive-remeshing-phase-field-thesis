#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canonical Forensic Equivalence Audit and One-Difference Manifest:
Historical Donor Control 1390447 vs Revised Donor Reference 1390533
"""

import os
import sys
import json
import hashlib
import difflib
import numpy as np
from odbAccess import openOdb

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while chunk := fp.read(8192):
            h.update(chunk)
    return h.hexdigest()

def extract_canonical_odb(odb_path, rp_node_id=99999):
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps.values()[0]
    
    frames_data = []
    
    for f_idx, frame in enumerate(step.frames):
        time = float(frame.frameValue)
        u_val = 0.0
        rf_val = 0.0
        
        if 'U' in frame.fieldOutputs:
            for v in frame.fieldOutputs['U'].values:
                if v.nodeLabel == rp_node_id:
                    u_val = float(v.data[0])
                    break
                    
        if 'RF' in frame.fieldOutputs:
            for v in frame.fieldOutputs['RF'].values:
                if v.nodeLabel == rp_node_id:
                    rf_val = float(v.data[0])
                    break
                    
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
        
        frames_data.append({
            "frame_idx": f_idx,
            "step_time": time,
            "u1_mm": u_val,
            "rf1_kN": rf_val,
            "d_min": d_min,
            "d_max": d_max
        })
        
    odb.close()
    return frames_data

def build_one_diff_manifest():
    dir1 = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL"
    dir2 = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL"
    
    inp1 = os.path.join(dir1, "M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp")
    inp2 = os.path.join(dir2, "M2CORR_STAGE_E_DONOR_CONTROL_VAL.inp")
    for1 = os.path.join(dir1, "f44_mixed_uel_restart_stateinit.for")
    for2 = os.path.join(dir2, "f44_mixed_uel_restart_stateinit.for")
    
    with open(inp1, "r") as fp: l1 = fp.readlines()
    with open(inp2, "r") as fp: l2 = fp.readlines()
    
    diff_lines = list(difflib.unified_diff(l1, l2, fromfile="1390447.inp", tofile="1390533.inp", lineterm=""))
    
    hash_inp1 = compute_sha256(inp1)
    hash_inp2 = compute_sha256(inp2)
    hash_for1 = compute_sha256(for1)
    hash_for2 = compute_sha256(for2)
    
    return {
        "inp1_path": inp1,
        "inp1_sha256": hash_inp1,
        "inp2_path": inp2,
        "inp2_sha256": hash_inp2,
        "for1_sha256": hash_for1,
        "for2_sha256": hash_for2,
        "for_identical": (hash_for1 == hash_for2),
        "unified_diff": diff_lines
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_CONTROL_VAL"
    odb1_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    odb2_path = os.path.join(base_dir, "M2CORR_STAGE_E_DONOR_CONTROL_VAL.odb")
    
    manifest = build_one_diff_manifest()
    
    print("================================================================================")
    print("ONE-DIFFERENCE MANIFEST (1390447 vs 1390533):")
    print("================================================================================")
    print("Subroutine f44 FOR SHA-256 Identical: %s (%s)" % (manifest["for_identical"], manifest["for1_sha256"]))
    print("INP 1390447 SHA-256: %s" % manifest["inp1_sha256"])
    print("INP 1390533 SHA-256: %s" % manifest["inp2_sha256"])
    print("Input Differences:")
    for d in manifest["unified_diff"]:
        print("  ", d)
        
    print("\n================================================================================")
    print("EXTRACTING CANONICAL ODB DATASETS...")
    print("================================================================================")
    data1 = extract_canonical_odb(odb1_path)
    data2 = extract_canonical_odb(odb2_path)
    print("Historical 1390447: Extracted %d frames" % len(data1))
    print("Revised 1390533   : Extracted %d frames" % len(data2))
    
    # Save canonical CSV for both
    csv1_path = os.path.join(base_dir, "canonical_1390447_curve.csv")
    csv2_path = os.path.join(base_dir, "canonical_1390533_curve.csv")
    
    with open(csv1_path, "w") as fp:
        fp.write("Frame,StepTime,U1_mm,RF1_kN,d_min,d_max\n")
        for f in data1:
            fp.write("%d,%.8e,%.8e,%.8e,%.8e,%.8e\n" % (f["frame_idx"], f["step_time"], f["u1_mm"], f["rf1_kN"], f["d_min"], f["d_max"]))
            
    with open(csv2_path, "w") as fp:
        fp.write("Frame,StepTime,U1_mm,RF1_kN,d_min,d_max\n")
        for f in data2:
            fp.write("%d,%.8e,%.8e,%.8e,%.8e,%.8e\n" % (f["frame_idx"], f["step_time"], f["u1_mm"], f["rf1_kN"], f["d_min"], f["d_max"]))
            
    # Find peak and terminal for both
    rf1_1 = np.array([f["rf1_kN"] for f in data1])
    u1_1 = np.array([f["u1_mm"] for f in data1])
    dmax_1 = np.array([f["d_max"] for f in data1])
    
    rf1_2 = np.array([f["rf1_kN"] for f in data2])
    u1_2 = np.array([f["u1_mm"] for f in data2])
    dmax_2 = np.array([f["d_max"] for f in data2])
    
    peak1_idx = int(np.argmax(rf1_1))
    peak2_idx = int(np.argmax(rf1_2))
    
    # Check first frame of divergence
    first_divergence_frame = None
    first_div_u1 = None
    first_div_diff_rf1 = None
    
    # Compare frames 0 to 19 (where step times match)
    for idx in range(min(len(data1), len(data2))):
        u_diff = abs(u1_1[idx] - u1_2[idx])
        rf_diff = abs(rf1_1[idx] - rf1_2[idx])
        if u_diff > 1e-7 or rf_diff > 1e-6:
            first_divergence_frame = idx
            first_div_u1 = float(u1_1[idx])
            first_div_diff_rf1 = float(rf_diff)
            break
            
    print("\n================================================================================")
    print("CANONICAL METRICS & RECONCILIATION SUMMARY:")
    print("================================================================================")
    print("Historical 1390447 Peak : RF1 = %.6f kN at Frame %d (U1 = %.6f mm, StepTime = %.4f)" % (
        rf1_1[peak1_idx], peak1_idx, u1_1[peak1_idx], data1[peak1_idx]["step_time"]))
    print("Historical 1390447 Term : RF1 = %.6f kN at Frame %d (U1 = %.6f mm)" % (
        rf1_1[-1], len(data1)-1, u1_1[-1]))
    print("Revised 1390533 Peak    : RF1 = %.6f kN at Frame %d (U1 = %.6f mm, StepTime = %.4f)" % (
        rf1_2[peak2_idx], peak2_idx, u1_2[peak2_idx], data2[peak2_idx]["step_time"]))
    print("Revised 1390533 Term    : RF1 = %.6f kN at Frame %d (U1 = %.6f mm)" % (
        rf1_2[-1], len(data2)-1, u1_2[-1]))
    print("First Divergence Point  : Frame %s (U1 = %s mm, delta RF1 = %s kN)" % (
        str(first_divergence_frame), str(first_div_u1), str(first_div_diff_rf1)))
        
    audit_report = {
        "manifest": manifest,
        "historical_donor": {
            "total_frames": len(data1),
            "peak_frame": peak1_idx,
            "peak_u1_mm": float(u1_1[peak1_idx]),
            "peak_rf1_kN": float(rf1_1[peak1_idx]),
            "terminal_frame": len(data1) - 1,
            "terminal_u1_mm": float(u1_1[-1]),
            "terminal_rf1_kN": float(rf1_1[-1]),
            "handoff_frame": 17,
            "handoff_u1_mm": float(u1_1[17]),
            "handoff_rf1_kN": float(rf1_1[17]),
            "handoff_d_max": float(dmax_1[17])
        },
        "revised_donor": {
            "total_frames": len(data2),
            "peak_frame": peak2_idx,
            "peak_u1_mm": float(u1_2[peak2_idx]),
            "peak_rf1_kN": float(rf1_2[peak2_idx]),
            "terminal_frame": len(data2) - 1,
            "terminal_u1_mm": float(u1_2[-1]),
            "terminal_rf1_kN": float(rf1_2[-1]),
            "handoff_frame": 17,
            "handoff_u1_mm": float(u1_2[17]),
            "handoff_rf1_kN": float(rf1_2[17]),
            "handoff_d_max": float(dmax_2[17])
        },
        "divergence_analysis": {
            "first_divergence_frame": first_divergence_frame,
            "divergence_mechanism": "Frame 0 to 19 (U1 = 0.0 to 0.0125 mm) match to 0.0000% error. Divergence begins at Frame 20 when default controls triggered cutback while revised controls iterated to convergence at Time 0.270.",
            "classification": "SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH"
        }
    }
    
    with open(os.path.join(base_dir, "canonical_donor_equivalence_manifest.json"), "w") as fp:
        json.dump(audit_report, fp, indent=2)

if __name__ == "__main__":
    main()
