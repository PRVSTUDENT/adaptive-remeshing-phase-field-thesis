#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_crack_front_nodes.py
Inspects the damage distribution on C5 and evaluates the phase-field residual / driving force
at each node to see which nodes are advancing and which are relaxing.
"""

import sys
import math
from pathlib import Path
import numpy as np
import csv

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

def main():
    mapped_csv = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_c5_frame7_mapped_state_table.csv"
    nodes_d = {}
    elems_h = {}
    with open(mapped_csv, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if r[0] == "NODE":
                nodes_d[int(r[1])] = float(r[4])
            elif r[0] == "ELEM_H":
                elems_h[int(r[1])] = [float(r[2]), float(r[3]), float(r[4]), float(r[5])]

    mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_crack_band_mesh_c5.inp"
    nodes = {}
    with open(mesh_inp, "r", encoding="utf-8") as f:
        reading = False
        for line in f:
            l = line.strip()
            if l.upper().startswith("*NODE"):
                reading = True
                continue
            elif l.startswith("*"):
                reading = False
                continue
            if reading:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = (float(parts[1]), float(parts[2]))

    print(f"Loaded {len(nodes)} nodes and {len(nodes_d)} damage values.")

    # Check damage distribution along crack line y = 0.050
    crack_line_nodes = []
    for nid, (x, y) in nodes.items():
        if abs(y - 0.050) < 1e-5:
            crack_line_nodes.append((x, nid, nodes_d[nid]))
    crack_line_nodes.sort()

    print("\n--- Damage Profile along y = 0.050 mm ---")
    print("x (mm)    Node ID   Damage d")
    for x, nid, d in crack_line_nodes:
        if 0.035 <= x <= 0.065:
            print(f"{x:.5f}   {nid:6d}    {d:.6f}")

    # Inspect active set nodes in Package 96:
    # (0.035 <= x <= 0.075) and (abs(y - 0.050) <= 0.008) and (0.15 <= d < 0.9990)
    free_nodes = []
    for nid, (x, y) in nodes.items():
        d = nodes_d[nid]
        dist_y = abs(y - 0.050)
        in_band = (0.035 <= x <= 0.075) and (dist_y <= 0.008)
        is_wake = (d >= 0.9990) and (x <= 0.0405)
        if in_band and (d >= 0.15) and not is_wake:
            free_nodes.append((x, y, nid, d))

    print(f"\nPackage 96 Free Nodes Count: {len(free_nodes)}")
    free_nodes.sort()
    x_coords = [p[0] for p in free_nodes]
    y_coords = [p[1] for p in free_nodes]
    d_vals = [p[3] for p in free_nodes]
    print(f"Free nodes x-range: [{min(x_coords):.5f}, {max(x_coords):.5f}] mm")
    print(f"Free nodes y-range: [{min(y_coords):.5f}, {max(y_coords):.5f}] mm")
    print(f"Free nodes d-range: [{min(d_vals):.5f}, {max(d_vals):.5f}]")

if __name__ == "__main__":
    main()
