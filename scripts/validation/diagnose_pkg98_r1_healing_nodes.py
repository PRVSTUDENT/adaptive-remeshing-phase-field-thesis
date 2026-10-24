#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import csv
import numpy as np
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot"
state_path = pkg_dir / "candidate_c5_frame7_mapped_state_table.csv"
mesh_path = pkg_dir / "candidate_crack_band_mesh_c5.inp"

# Load checkpoint state
d_ckpt = {}
with open(state_path, "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if parts and parts[0].upper() == "NODE":
            d_ckpt[int(parts[1])] = float(parts[4])

# Load mesh coordinates
coords = {}
with open(mesh_path, "r", encoding="utf-8") as f:
    reading = None
    for line in f:
        l = line.strip()
        if not l or l.startswith("**"): continue
        if l.startswith("*"):
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                reading = "NODE"
            else:
                reading = None
            continue
        if reading == "NODE":
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 3 and parts[0].isdigit():
                coords[int(parts[0])] = (float(parts[1]), float(parts[2]))

print(f"Loaded {len(d_ckpt)} checkpoint states, {len(coords)} coordinates.")

# Download iteration 14 and 15 extracted CSVs from cluster
import subprocess
rem_dir = "/scratch9/pr21vyci/runs/mode1_package98_r1_c5_pdas_repair"
ssh_cfg = Path.home() / ".ssh/codex_config"
local_dir = REPO_ROOT / "results/validation/mode1_f1597"

for it in [14, 15]:
    f = f"pdas_subproblem_iter_{it:02d}_extracted.csv"
    src = f"tu_freiberg:{rem_dir}/{f}"
    dst = str(local_dir / f"pkg98_r1_{f}")
    subprocess.run(["scp", "-F", str(ssh_cfg), "-B", src, dst], check=True)

# Parse iteration 15
d_it15 = {}
with open(local_dir / "pkg98_r1_pdas_subproblem_iter_15_extracted.csv", "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if parts and parts[0].upper() == "NODE":
            d_it15[int(parts[1])] = float(parts[4])

# Find healing nodes in iteration 15
healing_15 = []
for nid, d_val in d_it15.items():
    if nid in d_ckpt:
        diff = d_val - d_ckpt[nid]
        if diff < -1.0e-12:
            x, y = coords.get(nid, (0, 0))
            healing_15.append((nid, x, y, d_ckpt[nid], d_val, diff))

print(f"\nIteration 15 Healing Nodes: {len(healing_15)}")
for h in sorted(healing_15, key=lambda item: item[5])[:10]:
    print(f"Node {h[0]:5d} | (x={h[1]:.5f}, y={h[2]:.5f}) | d_ckpt={h[3]:.6f} | d_sol={h[4]:.6f} | delta_d={h[5]:.2e}")

# Parse iteration 14
d_it14 = {}
with open(local_dir / "pkg98_r1_pdas_subproblem_iter_14_extracted.csv", "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if parts and parts[0].upper() == "NODE":
            d_it14[int(parts[1])] = float(parts[4])

healing_14 = []
for nid, d_val in d_it14.items():
    if nid in d_ckpt:
        diff = d_val - d_ckpt[nid]
        if diff < -1.0e-12:
            x, y = coords.get(nid, (0, 0))
            healing_14.append((nid, x, y, d_ckpt[nid], d_val, diff))

print(f"\nIteration 14 Healing Nodes: {len(healing_14)}")
for h in sorted(healing_14, key=lambda item: item[5])[:10]:
    print(f"Node {h[0]:5d} | (x={h[1]:.5f}, y={h[2]:.5f}) | d_ckpt={h[3]:.6f} | d_sol={h[4]:.6f} | delta_d={h[5]:.2e}")
