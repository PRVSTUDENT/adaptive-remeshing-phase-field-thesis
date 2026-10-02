#!/usr/bin/env python3
"""
Inspect triangles 9720 and 9840 in M2STATE_FRACFIX_RESTART2R5.inp.
"""
from pathlib import Path
import math

def inspect_sliver_triangles():
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
                    
    # Triangles: 9720 (mech 19596) and 9840 (mech 19716)
    # Let's find their node IDs from inp
    tri_nodes = {}
    with open(inp_path, "r", errors="ignore") as f:
        in_u3 = False
        for line in f:
            if "*ELEMENT, TYPE=U3" in line:
                in_u3 = True
                continue
            elif in_u3 and line.startswith("*"):
                in_u3 = False
            elif in_u3:
                parts = [int(p.strip()) for p in line.split(",") if p.strip()]
                if parts[0] in [9720, 9840]:
                    tri_nodes[parts[0]] = parts[1:]
                    
    for eid, enodes in tri_nodes.items():
        coords = [nodes[nid] for nid in enodes]
        print(f"\n--- Triangle {eid} (Nodes: {enodes}) ---")
        for i, nid in enumerate(enodes):
            print(f"  Node {nid}: ({coords[i][0]:.8f}, {coords[i][1]:.8f})")
            
        # detJ = (x2-x1)*(y3-y1) - (x3-x1)*(y2-y1)
        detJ = (coords[1][0]-coords[0][0])*(coords[2][1]-coords[0][1]) - (coords[2][0]-coords[0][0])*(coords[1][1]-coords[0][1])
        print(f"  detJ = {detJ:.10e}")
        
        # Edge lengths
        L12 = math.sqrt((coords[1][0]-coords[0][0])**2 + (coords[1][1]-coords[0][1])**2)
        L23 = math.sqrt((coords[2][0]-coords[1][0])**2 + (coords[2][1]-coords[1][1])**2)
        L31 = math.sqrt((coords[0][0]-coords[2][0])**2 + (coords[0][1]-coords[2][1])**2)
        print(f"  Edge lengths: L12={L12:.8f}, L23={L23:.8f}, L31={L31:.8f}")

if __name__ == "__main__":
    inspect_sliver_triangles()
