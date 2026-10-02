#!/usr/bin/env python3
"""
Comprehensive Topology Audit: PK10R1 vs H0 vs H1 vs H2
"""

import os
import sys
import re
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

def parse_mesh(inp_path):
    nodes = {}
    quads = {}
    tris = {}
    sets = {}
    current_set = None
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    mode = None
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("**"):
            continue
        if line_clean.startswith("*"):
            l_up = line_clean.upper()
            if l_up.startswith("*NODE"):
                mode = "NODE"
            elif l_up.startswith("*ELEMENT"):
                if "TYPE=U1" in l_up or "TYPE=CPE4" in l_up or "TYPE=CPS4" in l_up or "TYPE=U2" in l_up:
                    mode = "ELEM_QUAD"
                elif "TYPE=U3" in l_up or "TYPE=CPE3" in l_up or "TYPE=CPS3" in l_up or "TYPE=U4" in l_up:
                    mode = "ELEM_TRI"
                else:
                    mode = "OTHER_ELEM"
            elif l_up.startswith("*NSET"):
                mode = "NSET"
                m = re.search(r"NSET=([A-Za-z0-9_]+)", l_up)
                current_set = m.group(1) if m else "UNKNOWN"
                if current_set not in sets:
                    sets[current_set] = []
            elif l_up.startswith("*STEP"):
                break
            else:
                mode = "OTHER"
            continue
            
        parts = [p.strip() for p in line_clean.split(",") if p.strip()]
        if mode == "NODE":
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif mode == "ELEM_QUAD":
            if len(parts) == 5:
                try:
                    eid = int(parts[0])
                    n = tuple(int(x) for x in parts[1:5])
                    quads[eid] = n
                except ValueError:
                    pass
        elif mode == "ELEM_TRI":
            if len(parts) == 4:
                try:
                    eid = int(parts[0])
                    n = tuple(int(x) for x in parts[1:4])
                    tris[eid] = n
                except ValueError:
                    pass
        elif mode == "NSET":
            for p in parts:
                try:
                    sets[current_set].append(int(p))
                except ValueError:
                    pass
                    
    return nodes, quads, tris, sets

def analyze(name, inp_path):
    if not inp_path.exists():
        print(f"MISSING: {inp_path}")
        return
    nodes, quads, tris, sets = parse_mesh(inp_path)
    xs = [coord[0] for coord in nodes.values()]
    ys = [coord[1] for coord in nodes.values()]
    
    # Slit nodes (x in [-0.5, 0.0], abs(y) < 1e-4)
    slit_nodes = [(nid, nodes[nid]) for nid in nodes if abs(nodes[nid][1]) < 1e-4 and -0.5 <= nodes[nid][0] <= 1e-4]
    
    # Top and bottom nodes
    top_nodes = [nid for nid in nodes if abs(nodes[nid][1] - max(ys)) < 1e-5]
    bot_nodes = [nid for nid in nodes if abs(nodes[nid][1] - min(ys)) < 1e-5]
    
    print(f"\n=======================================================")
    print(f"=== {name} ===")
    print(f"Path: {inp_path}")
    print(f"Nodes: {len(nodes)}")
    print(f"Quads: {len(quads)}, Tris: {len(tris)}")
    print(f"X bounds: [{min(xs):.6f}, {max(xs):.6f}]")
    print(f"Y bounds: [{min(ys):.6f}, {max(ys):.6f}]")
    print(f"Top boundary Y = {max(ys):.6f} ({len(top_nodes)} nodes)")
    print(f"Bottom boundary Y = {min(ys):.6f} ({len(bot_nodes)} nodes)")
    print(f"Notch slit region (|y| < 1e-4, x <= 0): {len(slit_nodes)} nodes")
    
    # Check if there are separate nodes at the same x along the notch
    coords_map = {}
    for nid, (x, y) in slit_nodes:
        x_round = round(x, 6)
        if x_round not in coords_map:
            coords_map[x_round] = []
        coords_map[x_round].append((nid, y))
        
    split_count = sum(1 for x_r, nlist in coords_map.items() if len(nlist) > 1)
    single_count = sum(1 for x_r, nlist in coords_map.items() if len(nlist) == 1)
    print(f"Notch slit X-stations: {len(coords_map)} total stations")
    print(f"  Split stations (flank separation): {split_count}")
    print(f"  Single stations (unsplit/continuous): {single_count}")
    if split_count > 0:
        print("  -> PHYSICAL CRACK SLIT: YES")
    else:
        print("  -> PHYSICAL CRACK SLIT: NO (SOLID UNNOTCHED MATERIAL)")

def main():
    pk10_inp = ROOT / "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6.inp"
    h0_inp = ROOT / "models/baseline_original/molnar_gravouil_2017/02_Single_Notch_Tension/SingleNotch.inp"
    h1_inp = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050/M2REF_H1_FULL_U050.inp"
    h2_inp = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050/M2REF_H2_FULL_U050.inp"
    
    for name, p in [("H0_ORIGINAL", h0_inp), ("H1_UNIFORM", h1_inp), ("H2_UNIFORM", h2_inp), ("PK10R1_CURRENT", pk10_inp)]:
        analyze(name, p)

if __name__ == "__main__":
    main()
