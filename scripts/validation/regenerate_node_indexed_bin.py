#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Regenerate STAGE_D_COMMITTED_STATE.bin with:
Record 1: SV_ELEM_NODAL_PHASE(100000, 4) - Exact nodal transferred phase for every element local node
Record 2: SV_H_COMMITTED(100000, 4) - Exact GP transferred history for every element integration point
"""

import os
import sys
import struct
import json

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

target_dir = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL")
inp_path = os.path.join(target_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp")
bc_primary_path = os.path.join(target_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp")
old_bin_path = os.path.join(target_dir, "STAGE_D_COMMITTED_STATE.bin")
new_bin_path = os.path.join(target_dir, "STAGE_D_COMMITTED_STATE.bin")

def regenerate_node_indexed_bin():
    print("================================================================================")
    print("REGENERATING NODE-INDEXED STAGE_D_COMMITTED_STATE.BIN")
    print("================================================================================")
    
    # 1. Read nodal transferred phase from STAGE_D_PRIMARY_STATE_BOUNDARY.inp
    print("1. Reading nodal phase from STAGE_D_PRIMARY_STATE_BOUNDARY.inp...")
    nodal_d = {}
    with open(bc_primary_path, "r") as fp:
        for line in fp:
            line_s = line.strip()
            if line_s.startswith("**") or not line_s:
                continue
            parts = [p.strip() for p in line_s.split(",")]
            if len(parts) == 4 and parts[1] == "3" and parts[2] == "3":
                nid = int(parts[0])
                val = float(parts[3])
                nodal_d[nid] = val
    print("  Read %d nodal phase values. Max d: %.8f" % (len(nodal_d), max(nodal_d.values())))
    
    # 2. Read element connectivity from INP deck (E_QUAD_PHASE, elements 1..8836)
    print("2. Reading element connectivity from INP deck...")
    elem_nodes = {}
    reading_conn = False
    with open(inp_path, "r") as fp:
        for line in fp:
            line_u = line.strip().upper()
            if line_u.startswith("*ELEMENT") and "TYPE=U1" in line_u:
                reading_conn = True
                continue
            elif line_u.startswith("*ELEMENT") and "TYPE=U2" in line_u:
                reading_conn = False
                break
            elif line_u.startswith("*") and reading_conn:
                reading_conn = False
                break
                
            if reading_conn:
                parts = [p.strip() for p in line.strip().split(",") if p.strip()]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    nodes = [int(p) for p in parts[1:5]]
                    elem_nodes[eid] = nodes
                    
    print("  Read connectivity for %d physical phase elements." % len(elem_nodes))
    
    # 3. Read GP committed H from old binary file
    print("3. Reading GP committed history from old binary file...")
    with open(old_bin_path, "rb") as fp:
        h1 = struct.unpack("<I", fp.read(4))[0]
        fp.seek(h1 + 4, os.SEEK_CUR) # Skip Record 1
        h2 = struct.unpack("<I", fp.read(4))[0]
        n_doubles_2 = h2 // 8
        h_flat = struct.unpack("<%dd" % n_doubles_2, fp.read(h2))
        t2 = struct.unpack("<I", fp.read(4))[0]
        
    print("  Read %d GP history floats. Max H: %.8f" % (len(h_flat), max(h_flat)))
    
    # 4. Construct SV_ELEM_NODAL_PHASE(100000, 4) in column-major order
    print("4. Constructing SV_ELEM_NODAL_PHASE(100000, 4)...")
    N_CAPACITY = 100000
    elem_nodal_phase = [[0.0 for _ in range(4)] for _ in range(N_CAPACITY)]
    
    for eid, nodes in elem_nodes.items():
        idx = eid - 1
        for local_i, nid in enumerate(nodes):
            d_val = nodal_d.get(nid, 0.0)
            elem_nodal_phase[idx][local_i] = d_val
            
    # Flatten column-major: column 0 (all GP1/Node1), column 1 (all GP2/Node2), etc.
    flat_elem_nodal_phase = []
    for local_i in range(4):
        for idx in range(N_CAPACITY):
            flat_elem_nodal_phase.append(elem_nodal_phase[idx][local_i])
            
    print("  Constructed %d element-nodal phase floats. Max: %.8f" % (
        len(flat_elem_nodal_phase), max(flat_elem_nodal_phase)))
        
    # 5. Write new binary state file
    print("5. Writing new binary state file: %s" % new_bin_path)
    rec1_bytes = len(flat_elem_nodal_phase) * 8 # 400,000 * 8 = 3,200,000 bytes
    rec2_bytes = len(h_flat) * 8               # 400,000 * 8 = 3,200,000 bytes
    
    with open(new_bin_path, "wb") as fp:
        # Record 1: SV_ELEM_NODAL_PHASE(100000, 4)
        fp.write(struct.pack("<I", rec1_bytes))
        fp.write(struct.pack("<%dd" % len(flat_elem_nodal_phase), *flat_elem_nodal_phase))
        fp.write(struct.pack("<I", rec1_bytes))
        
        # Record 2: SV_H_COMMITTED(100000, 4)
        fp.write(struct.pack("<I", rec2_bytes))
        fp.write(struct.pack("<%dd" % len(h_flat), *h_flat))
        fp.write(struct.pack("<I", rec2_bytes))
        
    print("  Successfully generated binary file of size %d bytes." % os.path.getsize(new_bin_path))
    
    # 6. Verify Target Element 4371
    print("\n--- VERIFICATION OF TARGET ELEMENT 4371 ---")
    nodes_4371 = elem_nodes[4371]
    print("Element 4371 Nodes: %s" % nodes_4371)
    d_nodes_4371 = [nodal_d[nid] for nid in nodes_4371]
    print("Nodal transferred d : %s | Max = %.8f" % (d_nodes_4371, max(d_nodes_4371)))
    h_gps_4371 = [h_flat[4370 + k*100000] for k in range(4)]
    print("GP transferred H    : %s | Max = %.8f" % (h_gps_4371, max(h_gps_4371)))

if __name__ == "__main__":
    regenerate_node_indexed_bin()
