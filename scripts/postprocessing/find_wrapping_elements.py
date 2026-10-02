#!/usr/bin/env python3
"""
Find all elements spanning across the specimen width (X=0.5 to X=-0.5) in M2STATE_FRACFIX_RESTART2R5.inp.
"""
from pathlib import Path
import math

def find_wrapping_elements():
    inp_path = Path("/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp")
    
    nodes = {}
    with open(inp_path, "r", errors="ignore") as f:
        in_node = False
        for line in f:
            if line.startswith("*NODE"):
                in_node = True
                continue
            elif in_node and line.startswith("*"):
                in_node = False
            elif in_node:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    
    wrapping_elements = []
    with open(inp_path, "r", errors="ignore") as f:
        in_elem = False
        for line in f:
            if line.startswith("*ELEMENT"):
                in_elem = True
                continue
            elif in_elem and line.startswith("*"):
                in_elem = False
            elif in_elem:
                parts = [int(p.strip()) for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    eid = parts[0]
                    enodes = parts[1:]
                    coords = [nodes[nid] for nid in enodes]
                    xs = [c[0] for c in coords]
                    # Check if element spans more than 0.2 mm in X
                    span_x = max(xs) - min(xs)
                    if span_x > 0.2:
                        wrapping_elements.append((eid, span_x, enodes))
                        
    print(f"Total elements with large X-span (>0.2 mm): {len(wrapping_elements)}")
    for e in wrapping_elements[:20]:
        print(f"  Element {e[0]}: span_X = {e[1]:.4f} mm, nodes = {e[2]}")

if __name__ == "__main__":
    find_wrapping_elements()
