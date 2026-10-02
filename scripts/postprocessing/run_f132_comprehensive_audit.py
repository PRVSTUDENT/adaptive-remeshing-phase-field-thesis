#!/usr/bin/env python3
"""
F132DIAG Comprehensive Diagnostic Audit Script
Task ID: F132DIAG-M2-CORRECTED-H2-VS-PK10R1-MODEL-EQUIVALENCE-AND-MESH-CONVERGENCE1
"""

import sys
import os
import math
import numpy as np
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

H2_INP_LOCAL = ROOT / "models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.inp"
PK10_INP_LOCAL = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.inp"

REMOTE_PYTHON_SCRIPT = """import sys
import os
import json
import math
from odbAccess import openOdb

h2_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H2_FULL_U050/M2CORR_H2_FULL_U050.odb"
pk10_odb_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_CONTINUOUS_U050/M2CORR_PK10R1_CONTINUOUS_U050.odb"

def extract_full_odb_details(odb_path, total_disp=0.050):
    odb = openOdb(path=odb_path)
    frames_data = []
    
    for step_name, step in odb.steps.items():
        for frame in step.frames:
            t = frame.frameValue
            u1 = total_disp * t
            
            # Reaction force at bottom
            rf_field = frame.fieldOutputs['RF']
            rf1_pos = 0.0
            rf1_neg = 0.0
            for val in rf_field.values:
                if val.data[0] is not None:
                    if val.data[0] > 0:
                        rf1_pos += val.data[0]
                    else:
                        rf1_neg += abs(val.data[0])
            rf1_val = max(rf1_pos, rf1_neg)
            
            # Damage stats if available in SDV or U
            d_max = 0.0
            h_max = 0.0
            d_gt_01 = 0
            d_gt_05 = 0
            d_gt_08 = 0
            
            if 'SDV_PHASE' in frame.fieldOutputs:
                d_field = frame.fieldOutputs['SDV_PHASE']
                for val in d_field.values:
                    v = val.data
                    if v > d_max: d_max = v
                    if v >= 0.1: d_gt_01 += 1
                    if v >= 0.5: d_gt_05 += 1
                    if v >= 0.8: d_gt_08 += 1
            elif 'U' in frame.fieldOutputs:
                # In 2-layer UEL, phase field d is U3 (degree of freedom 3)
                u_field = frame.fieldOutputs['U']
                for val in u_field.values:
                    if len(val.data) >= 3 and val.data[2] is not None:
                        v = val.data[2]
                        if v > d_max: d_max = v
                        if v >= 0.1: d_gt_01 += 1
                        if v >= 0.5: d_gt_05 += 1
                        if v >= 0.8: d_gt_08 += 1
                        
            frames_data.append({
                "u1": u1,
                "rf1": rf1_val,
                "d_max": d_max,
                "d_gt_01": d_gt_01,
                "d_gt_05": d_gt_05,
                "d_gt_08": d_gt_08
            })
            
    odb.close()
    return frames_data

h2_data = extract_full_odb_details(h2_odb_path)
pk10_data = extract_full_odb_details(pk10_odb_path)

out = {
    "h2_frames": h2_data,
    "pk10_frames": pk10_data
}
print("JSON_START" + json.dumps(out) + "JSON_END")
"""

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = []
    
    in_node = False
    in_elem = False
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith("**") or not line_str:
                continue
                
            if line_str.upper().startswith("*NODE"):
                in_node = True
                in_elem = False
                continue
            elif line_str.upper().startswith("*ELEMENT"):
                in_node = False
                in_elem = True
                continue
            elif line_str.startswith("*"):
                in_node = False
                in_elem = False
                continue
                
            if in_node:
                tokens = line_str.split(",")
                try:
                    nid = int(tokens[0])
                    x = float(tokens[1])
                    y = float(tokens[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
            elif in_elem:
                tokens = line_str.split(",")
                try:
                    eid = int(tokens[0])
                    nids = [int(t) for t in tokens[1:] if t.strip()]
                    elements.append((eid, nids))
                except ValueError:
                    pass
                    
    # Calculate edge lengths for 4-node quad elements
    edge_lengths = []
    notch_tip = (0.0, 0.0) # Notch tip at (0, 0)
    
    elem_edge_data = []
    
    for eid, nids in elements:
        if len(nids) == 4:
            pts = [nodes[n] for n in nids if n in nodes]
            if len(pts) == 4:
                # 4 edges
                edges = [
                    math.hypot(pts[0][0]-pts[1][0], pts[0][1]-pts[1][1]),
                    math.hypot(pts[1][0]-pts[2][0], pts[1][1]-pts[2][1]),
                    math.hypot(pts[2][0]-pts[3][0], pts[2][1]-pts[3][1]),
                    math.hypot(pts[3][0]-pts[0][0], pts[3][1]-pts[0][1])
                ]
                center_x = sum(p[0] for p in pts) / 4.0
                center_y = sum(p[1] for p in pts) / 4.0
                dist_notch = math.hypot(center_x - notch_tip[0], center_y - notch_tip[1])
                
                min_edge = min(edges)
                max_edge = max(edges)
                mean_edge = sum(edges)/4.0
                
                elem_edge_data.append({
                    "eid": eid,
                    "center": (center_x, center_y),
                    "dist_notch": dist_notch,
                    "min_edge": min_edge,
                    "max_edge": max_edge,
                    "mean_edge": mean_edge
                })
                edge_lengths.extend(edges)
                
    return nodes, elements, elem_edge_data, np.array(edge_lengths)

def main():
    print("================================================================================")
    print("F132DIAG COMPREHENSIVE DIAGNOSTIC AUDIT EXECUTION")
    print("================================================================================")

    # 1. Parse Mesh Topologies
    h2_nodes, h2_elems, h2_elem_data, h2_edges = parse_inp_mesh(H2_INP_LOCAL)
    pk10_nodes, pk10_elems, pk10_elem_data, pk10_edges = parse_inp_mesh(PK10_INP_LOCAL)

    l0 = 0.015 # mm

    print(f"\nH2 Mesh Parsed: {len(h2_nodes)} nodes, {len(h2_elems)} elements")
    print(f"H2 Edge Lengths (mm): min={np.min(h2_edges):.6f}, max={np.max(h2_edges):.6f}, median={np.median(h2_edges):.6f}")
    print(f"H2 Edge Percentiles: 5%={np.percentile(h2_edges, 5):.6f}, 25%={np.percentile(h2_edges, 25):.6f}, 50%={np.percentile(h2_edges, 50):.6f}, 75%={np.percentile(h2_edges, 75):.6f}, 95%={np.percentile(h2_edges, 95):.6f}")

    print(f"\nPK10R1 Mesh Parsed: {len(pk10_nodes)} nodes, {len(pk10_elems)} elements")
    print(f"PK10R1 Edge Lengths (mm): min={np.min(pk10_edges):.6f}, max={np.max(pk10_edges):.6f}, median={np.median(pk10_edges):.6f}")
    print(f"PK10R1 Edge Percentiles: 5%={np.percentile(pk10_edges, 5):.6f}, 25%={np.percentile(pk10_edges, 25):.6f}, 50%={np.percentile(pk10_edges, 50):.6f}, 75%={np.percentile(pk10_edges, 75):.6f}, 95%={np.percentile(pk10_edges, 95):.6f}")

    # Region-based mesh statistics
    regions = [
        ("1*l0 (r <= 0.015mm)", 1.0 * l0),
        ("2*l0 (r <= 0.030mm)", 2.0 * l0),
        ("5*l0 (r <= 0.075mm)", 5.0 * l0),
    ]

    print("\n--- MATCHED REGION MESH TABLE ---")
    print(f"{'Region':<25} | {'H2 h_min':<10} | {'H2 h_med':<10} | {'PK10 h_min':<10} | {'PK10 h_med':<10} | {'H2 Elems':<8} | {'PK10 Elems':<8}")
    print("-" * 95)

    for r_name, r_dist in regions:
        h2_in_r = [e for e in h2_elem_data if e["dist_notch"] <= r_dist]
        pk10_in_r = [e for e in pk10_elem_data if e["dist_notch"] <= r_dist]
        
        h2_min_r = min(e["min_edge"] for e in h2_in_r) if h2_in_r else 0.0
        h2_med_r = np.median([e["mean_edge"] for e in h2_in_r]) if h2_in_r else 0.0
        
        pk10_min_r = min(e["min_edge"] for e in pk10_in_r) if pk10_in_r else 0.0
        pk10_med_r = np.median([e["mean_edge"] for e in pk10_in_r]) if pk10_in_r else 0.0
        
        print(f"{r_name:<25} | {h2_min_r:<10.6f} | {h2_med_r:<10.6f} | {pk10_min_r:<10.6f} | {pk10_med_r:<10.6f} | {len(h2_in_r):<8} | {len(pk10_in_r):<8}")

    # Remote ODB Extraction
    print("\nExtracting ODB data from cluster...")
    remote_script_path = "projects/adaptive-remeshing/models/generated/mode_ii/f132_diag_abq.py"
    subprocess.run(["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_script_path}\n{REMOTE_PYTHON_SCRIPT}\nEOF"], check=True)

    run_cmd = [
        "ssh", "-i", SSH_KEY, SSH_HOST,
        "export PATH=/cluster/stages/2024.0/software/intel/2024.2/compiler/2024.2/bin:/cluster/application/abaqus/2023/Commands:$PATH; source /etc/profile.d/lmod.sh 2>/dev/null || true; module load gcc/11.4.0 intel/2024.2.0 abaqus/2023; /cluster/application/abaqus/2023/Commands/abaqus python " + remote_script_path
    ]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=300)
    
    stdout = res.stdout
    json_start = stdout.find("JSON_START")
    json_end = stdout.find("JSON_END")
    
    if json_start != -1 and json_end != -1:
        data = json.loads(stdout[json_start+10:json_end])
        h2_frames = data["h2_frames"]
        pk10_frames = data["pk10_frames"]
        
        print(f"\nExtracted {len(h2_frames)} frames for H2, {len(pk10_frames)} frames for PK10R1")
        
        # H2 Trajectory Analysis
        h2_u1 = [f["u1"] for f in h2_frames]
        h2_rf1 = [f["rf1"] for f in h2_frames]
        h2_max_rf = max(h2_rf1)
        h2_idx_max = h2_rf1.index(h2_max_rf)
        
        print("\n--- H2 TRAJECTORY METRICS ---")
        print(f"First accepted: U1={h2_u1[1]:.6f} mm, RF1={h2_rf1[1]:.6f} kN")
        print(f"Peak RF1: {h2_max_rf:.6f} kN at U1={h2_u1[h2_idx_max]:.6f} mm")
        print(f"Terminal U1: {h2_u1[-1]:.6f} mm, Terminal RF1={h2_rf1[-1]:.6f} kN across {len(h2_frames)-1} increments")
        
        # PK10R1 Trajectory Analysis
        pk10_u1 = [f["u1"] for f in pk10_frames]
        pk10_rf1 = [f["rf1"] for f in pk10_frames]
        pk10_max_rf = max(pk10_rf1)
        pk10_idx_max = pk10_rf1.index(pk10_max_rf)
        
        print("\n--- PK10R1 TRAJECTORY METRICS ---")
        print(f"First accepted: U1={pk10_u1[1]:.6f} mm, RF1={pk10_rf1[1]:.6f} kN")
        print(f"Peak RF1: {pk10_max_rf:.6f} kN at U1={pk10_u1[pk10_idx_max]:.6f} mm")
        print(f"Terminal U1: {pk10_u1[-1]:.6f} mm, Terminal RF1={pk10_rf1[-1]:.6f} kN across {len(pk10_frames)-1} increments")
        
        # Linear Elastic Stiffness Fits
        print("\n--- INITIAL LINEAR STIFFNESS FITS (K0 = RF1 / U1) ---")
        for limit_u in [0.00005, 0.00010, 0.00020]:
            h2_pts = [(u, rf) for u, rf in zip(h2_u1[1:], h2_rf1[1:]) if u <= limit_u]
            pk10_pts = [(u, rf) for u, rf in zip(pk10_u1[1:], pk10_rf1[1:]) if u <= limit_u]
            
            if h2_pts:
                # Least squares slope origin-constrained
                u_arr = np.array([p[0] for p in h2_pts])
                rf_arr = np.array([p[1] for p in h2_pts])
                k_h2 = np.sum(u_arr * rf_arr) / np.sum(u_arr**2)
            else:
                k_h2 = 0.0
                
            if pk10_pts:
                u_arr = np.array([p[0] for p in pk10_pts])
                rf_arr = np.array([p[1] for p in pk10_pts])
                k_pk10 = np.sum(u_arr * rf_arr) / np.sum(u_arr**2)
            else:
                k_pk10 = 0.0
                
            diff_rel = abs(k_pk10 - k_h2) / k_h2 if k_h2 > 0 else 0.0
            print(f"Window U1 <= {limit_u:.5f} mm: H2 K0 = {k_h2:.2f} kN/mm, PK10R1 K0 = {k_pk10:.2f} kN/mm (Diff: {diff_rel*100:.2f}%)")

        # Damage Onset Chronology
        print("\n--- DAMAGE ONSET CHRONOLOGY ---")
        for d_thresh in [0.1, 0.5, 0.8]:
            h2_onset = next((f for f in h2_frames if f["d_max"] >= d_thresh), None)
            pk10_onset = next((f for f in pk10_frames if f["d_max"] >= d_thresh), None)
            
            h2_str = f"U1={h2_onset['u1']:.6f} mm, RF1={h2_onset['rf1']:.6f} kN" if h2_onset else "N/A"
            pk10_str = f"U1={pk10_onset['u1']:.6f} mm, RF1={pk10_onset['rf1']:.6f} kN" if pk10_onset else "N/A"
            print(f"Threshold d >= {d_thresh:.1f}: H2 -> {h2_str} | PK10R1 -> {pk10_str}")

if __name__ == "__main__":
    main()
