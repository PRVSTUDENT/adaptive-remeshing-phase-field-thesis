#!/usr/bin/env python3
import os
import json

run_dir = "/scratch9/pr21vyci/runs/mode1_290_method_c_case3_single_job"
state_path = os.path.join(run_dir, "PK_METHOD_C_CASE3_CYCLE6_state.json")
phys_path = os.path.join(run_dir, "PK_METHOD_C_CASE3_CYCLE6_PHYS.inp")
sta_path = os.path.join(run_dir, "PK_METHOD_C_CASE3_CYCLE6.sta")

print("Checking Cycle 6 details on scratch:")
with open(state_path, "r") as f:
    state = json.load(f)

print("Top-level keys in state.json:")
for k, v in state.items():
    if not isinstance(v, dict):
        print("  {}: {}".format(k, v))

u_nodal = state.get("u_nodal", {})
d_nodal = state.get("d_nodal", {})
h_gp = state.get("h_gp", {})

rp_u = u_nodal.get("999999") or u_nodal.get(999999)
print("Node 999999 (N_RP) displacement u:", rp_u)

max_d = max(float(v) for v in d_nodal.values()) if d_nodal else 0.0
print("Max damage d_max:", max_d)

# Find crack tip (d >= 0.95) using physical mesh node coordinates
if os.path.isfile(phys_path):
    coords = {}
    with open(phys_path, "r") as f:
        in_node = False
        for line in f:
            line = line.strip()
            if line.startswith("*NODE"):
                in_node = True
                continue
            if line.startswith("*"):
                in_node = False
                continue
            if in_node and line:
                p = [x.strip() for x in line.split(",")]
                nid = int(p[0])
                coords[nid] = (float(p[1]), float(p[2]))
                
    tip_nodes = []
    for nid_str, d_val in d_nodal.items():
        nid = int(nid_str)
        if float(d_val) >= 0.95 and nid in coords:
            tip_nodes.append((coords[nid][0], coords[nid][1], float(d_val), nid))
            
    if tip_nodes:
        tip_nodes.sort(key=lambda item: item[0], reverse=True)
        print("Calculated Crack tip (d >= 0.95) from Cycle 6 mesh:")
        print("  Leading node {}: x = {:.6f}, y = {:.6f}, d = {:.6f}".format(
            tip_nodes[0][3], tip_nodes[0][0], tip_nodes[0][1], tip_nodes[0][2]))
        print("  Top 5 tip nodes:")
        for item in tip_nodes[:5]:
            print("    Node {}: x = {:.6f}, y = {:.6f}, d = {:.6f}".format(item[3], item[0], item[1], item[2]))
    else:
        print("No nodes with d >= 0.95 found in Cycle 6 state.")

# Check .sta terminal line
if os.path.isfile(sta_path):
    print("Last 3 lines of .sta:")
    with open(sta_path, "r") as f:
        sta_lines = [l.strip() for l in f if l.strip()]
        for l in sta_lines[-5:]:
            print("  ", l)
