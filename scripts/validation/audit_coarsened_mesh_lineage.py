#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Audit Coarsened Mesh Lineage & Resolution:
Compare 1390528 (original E1 coarsened) vs 1391279 (final dtmin coarsened) vs Mesh Generator
"""

import os
import sys
import hashlib
import json
import re

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def inspect_coarsened_deck(inp_path):
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    node_coords = {}
    in_node = False
    for line in lines:
        line_s = line.strip()
        if line_s.upper().startswith("*NODE"):
            in_node = True; continue
        if in_node:
            if line_s.startswith("*"): in_node = False
            elif line_s:
                parts = line_s.split(",")
                try:
                    nid = int(parts[0].strip())
                    x = float(parts[1].strip())
                    y = float(parts[2].strip())
                    node_coords[nid] = (x, y)
                except: pass
                
    # Calculate element sizes around crack tip (0, 0)
    tip_nodes = [nid for nid, (x, y) in node_coords.items() if abs(x) < 0.05 and abs(y) < 0.05]
    # Find minimum distance between adjacent nodes near crack tip
    xs = sorted(list(set([x for nid, (x, y) in node_coords.items() if abs(x) < 0.02 and abs(y) < 0.001])))
    dxs = [xs[i+1] - xs[i] for i in range(len(xs)-1)]
    min_dx = min(dxs) if dxs else 0.0
    
    return {
        "total_nodes": len(node_coords),
        "min_dx_near_tip": min_dx,
        "inp_sha256": sha256_file(inp_path)
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    inp_528 = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL/M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp")
    inp_830 = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL.inp")
    inp_279 = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    
    print("================================================================================")
    print("AUDITING COARSENED MESH LINEAGE:")
    print("================================================================================")
    for name, path in [("1390528 (Initial E1 Coarsened)", inp_528),
                       ("1390830 (Replacement Predecessor)", inp_830),
                       ("1391279 (Final dtmin Coarsened)", inp_279)]:
        if os.path.exists(path):
            res = inspect_coarsened_deck(path)
            print("\nDeck: %s" % name)
            print("  Path        : %s" % path)
            print("  SHA-256     : %s" % res["inp_sha256"])
            print("  Total Nodes : %d" % res["total_nodes"])
            print("  Min dx (tip): %.6f mm" % res["min_dx_near_tip"])
        else:
            print("\nDeck: %s NOT FOUND at %s" % (name, path))

if __name__ == "__main__":
    main()
