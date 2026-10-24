#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import csv
import numpy as np
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
pkg_dir = REPO_ROOT / "models/pandey_kumar_mode1/98_r1_c5_pdas_chatter_repair_pilot"
state_path = pkg_dir / "candidate_c5_frame7_mapped_state_table.csv"
mesh_path = pkg_dir / "candidate_crack_band_mesh_c5.inp"

# Load node list and d_ckpt
node_list = []
d_ckpt = []
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
                nid = int(parts[0])
                if nid != 999999:
                    coords[nid] = (float(parts[1]), float(parts[2]))

node_list = sorted(coords.keys())
node_to_idx = {nid: i for i, nid in enumerate(node_list)}

d_ckpt = np.zeros(len(node_list))
with open(state_path, "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if parts and parts[0].upper() == "NODE":
            nid = int(parts[1])
            if nid in node_to_idx:
                d_ckpt[node_to_idx[nid]] = float(parts[4])

# Load subproblem 15 extracted CSV
csv_15 = REPO_ROOT / "results/validation/mode1_f1597/pkg98_r1_pdas_subproblem_iter_15_extracted.csv"
d_raw_15 = np.zeros(len(node_list))
with open(csv_15, "r", encoding="utf-8") as f:
    for line in f:
        parts = [p.strip() for p in line.split(",")]
        if parts and parts[0].upper() == "NODE":
            nid = int(parts[1])
            if nid in node_to_idx:
                d_raw_15[node_to_idx[nid]] = float(parts[4])

# Check which nodes in inp 15 were free (not in *Boundary)
# Parse boundary lines from pdas_subproblem_iter_15.inp
# On cluster, download pdas_subproblem_iter_15.inp
import subprocess
rem_dir = "/scratch9/pr21vyci/runs/mode1_package98_r1_c5_pdas_repair"
ssh_cfg = Path.home() / ".ssh/codex_config"
inp_15 = REPO_ROOT / "results/validation/mode1_f1597/pdas_subproblem_iter_15.inp"
subprocess.run(["scp", "-F", str(ssh_cfg), "-B", f"tu_freiberg:{rem_dir}/pdas_subproblem_iter_15.inp", str(inp_15)], check=True)

fixed_dofs = set()
with open(inp_15, "r", encoding="utf-8") as f:
    in_bc = False
    for line in f:
        l = line.strip()
        if l.startswith("*Boundary") or l.startswith("*BOUNDARY"):
            in_bc = True
            continue
        elif l.startswith("*") and in_bc:
            in_bc = False
            continue
        if in_bc and l:
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 3 and parts[0].isdigit() and parts[1] == "3":
                fixed_dofs.add(int(parts[0]))

print(f"Fixed DOF 3 nodes in iter 15: {len(fixed_dofs)}")
print(f"Free DOF 3 nodes in iter 15: {len(node_list) - len(fixed_dofs)}")

# Now find the 5 nodes in A_15 that had d_raw < d_ckpt:
free_healing = []
for nid in node_list:
    if nid not in fixed_dofs:
        idx = node_to_idx[nid]
        diff = d_raw_15[idx] - d_ckpt[idx]
        if diff < -1.0e-12:
            x, y = coords[nid]
            free_healing.append((nid, x, y, d_ckpt[idx], d_raw_15[idx], diff))

print(f"\nExact free nodes with healing in iter 15: {len(free_healing)}")
for h in free_healing:
    print(f"Node {h[0]:5d} | (x={h[1]:.5f}, y={h[2]:.5f}) | d_ckpt={h[3]:.6f} | d_sol={h[4]:.6f} | delta_d={h[5]:.2e}")
