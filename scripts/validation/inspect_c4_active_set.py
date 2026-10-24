#!/usr/bin/env python3
import csv
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
C4_MESH = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp"
C4_INP = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/M1_C4_PACKAGE94_TRANSFER.inp"

nodes = {}
with open(C4_MESH, "r", encoding="utf-8") as f:
    reading = False
    for line in f:
        l = line.strip()
        if l.startswith("*Node"): reading = True; continue
        if reading:
            if l.startswith("*"): break
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = (float(parts[1]), float(parts[2]))

prescribed = set()
in_step4 = False
with open(C4_INP, "r", encoding="utf-8") as f:
    for line in f:
        l = line.strip()
        if "*Step, name=FORWARD_CONTINUATION" in l: in_step4 = True; continue
        if in_step4:
            if l.startswith("*End Step"): break
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                prescribed.add(int(parts[0]))

free_nodes = [nid for nid in nodes if nid not in prescribed]
free_pts = [nodes[nid] for nid in free_nodes]
xs = [p[0] for p in free_pts]
ys = [p[1] for p in free_pts]

print(f"C4 Free Nodes: {len(free_nodes)}")
print(f"  X range: [{min(xs):.6f}, {max(xs):.6f}] mm")
print(f"  Y range: [{min(ys):.6f}, {max(ys):.6f}] mm")
