#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Deep Forensic Paired Audit for Stage-E Corrected Baselines Nonconvergence
Extracts hotspot coordinates, hard invariants across accepted frames, and performs normalized deck diffs.
"""

import os
import sys
import json
import re
import numpy as np

def extract_node_coords(inp_path, target_nodes):
    coords = {}
    with open(inp_path, "r") as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith("*"):
                continue
            parts = [p.strip() for p in line_s.split(",")]
            if len(parts) == 3:
                try:
                    nid = int(parts[0])
                    if nid in target_nodes:
                        coords[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
    return coords

def check_hard_invariants(csv_path):
    # Check 0 <= d <= 1, min(Δd) >= -1e-6 from extracted curve
    with open(csv_path, "r") as fp:
        lines = fp.readlines()[1:]
        
    d_max_vals = []
    d_min_vals = []
    
    for l in lines:
        parts = l.strip().split(",")
        if len(parts) >= 7:
            d_min_vals.append(float(parts[5]))
            d_max_vals.append(float(parts[6]))
            
    d_min_arr = np.array(d_min_vals)
    d_max_arr = np.array(d_max_vals)
    
    bounds_ok = (np.min(d_min_arr) >= -1e-7) and (np.max(d_max_arr) <= 1.0 + 1e-7)
    diffs = np.diff(d_max_arr)
    mono_ok = np.min(diffs) >= -1e-6 if len(diffs) > 0 else True
    
    return {
        "d_min_overall": float(np.min(d_min_arr)),
        "d_max_overall": float(np.max(d_max_arr)),
        "bounds_satisfied": bool(bounds_ok),
        "monotonicity_satisfied": bool(mono_ok),
        "min_delta_d_max": float(np.min(diffs)) if len(diffs) > 0 else 0.0
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    # 1. Hotspots Coordinates
    ref_inp = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL", "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp")
    ref_hotspots = [16482, 16485, 16641, 16642, 16004, 16164, 15846]
    ref_coords = extract_node_coords(ref_inp, ref_hotspots)
    
    crs_inp = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL", "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp")
    crs_hotspots = [426, 506, 3531, 3775, 3859, 4018, 4100]
    crs_coords = extract_node_coords(crs_inp, crs_hotspots)
    
    print("================================================================================")
    print("REFINED 1390527 HOTSPOT NODE COORDINATES:")
    print("================================================================================")
    for nid, (x, y) in sorted(ref_coords.items()):
        print("  Node %d: x = %.6f mm, y = %.6f mm" % (nid, x, y))
        
    print("\n================================================================================")
    print("COARSENED 1390528 HOTSPOT NODE COORDINATES:")
    print("================================================================================")
    for nid, (x, y) in sorted(crs_coords.items()):
        print("  Node %d: x = %.6f mm, y = %.6f mm" % (nid, x, y))
        
    # 2. Check Hard Invariants over accepted frames
    ref_csv = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL", "force_displacement_curve.csv")
    crs_csv = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL", "force_displacement_curve.csv")
    
    ref_inv = check_hard_invariants(ref_csv)
    crs_inv = check_hard_invariants(crs_csv)
    
    print("\n================================================================================")
    print("HARD INVARIANTS AUDIT OVER ACCEPTED FRAMES:")
    print("================================================================================")
    print("Refined 1390527 : Bounds [0, 1] Valid = %s (d in [%.4e, %.4e]), Monotonicity Valid = %s (min delta = %.4e)" % (
        ref_inv["bounds_satisfied"], ref_inv["d_min_overall"], ref_inv["d_max_overall"],
        ref_inv["monotonicity_satisfied"], ref_inv["min_delta_d_max"]))
    print("Coarsened 1390528: Bounds [0, 1] Valid = %s (d in [%.4e, %.4e]), Monotonicity Valid = %s (min delta = %.4e)" % (
        crs_inv["bounds_satisfied"], crs_inv["d_min_overall"], crs_inv["d_max_overall"],
        crs_inv["monotonicity_satisfied"], crs_inv["min_delta_d_max"]))
        
if __name__ == "__main__":
    main()
