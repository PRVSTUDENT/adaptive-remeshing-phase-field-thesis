#!/usr/bin/env python3
"""
Check element connectivity for N_BOTTOM and N_TOP nodes in M2STATE_FRACFIX_RESTART2R5.inp.
"""
from pathlib import Path
from collections import defaultdict

def audit_boundary_connectivity():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp"
    
    nsets = defaultdict(list)
    elem_nodes = defaultdict(list)
    nodes = {}
    
    with open(inp_path, "r", errors="ignore") as f:
        current_nset = None
        in_elem = False
        in_node = False
        
        for line in f:
            if line.startswith("*NODE"):
                in_node = True
                in_elem = False
                current_nset = None
                continue
            elif in_node and line.startswith("*"):
                in_node = False
            elif in_node:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    
            if line.startswith("*NSET"):
                current_nset = line.split("NSET=")[1].split(",")[0].strip()
                in_elem = False
                continue
            elif current_nset and line.startswith("*"):
                current_nset = None
            elif current_nset:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                for p in parts:
                    nsets[current_nset].append(int(p))
                    
            if line.startswith("*ELEMENT"):
                in_elem = True
                current_nset = None
                continue
            elif in_elem and line.startswith("*"):
                in_elem = False
            elif in_elem:
                parts = [int(p.strip()) for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    eid = parts[0]
                    enodes = parts[1:]
                    for nid in enodes:
                        elem_nodes[nid].append(eid)

    print("=== BOUNDARY NODES CONNECTIVITY AUDIT ===")
    n_bottom = nsets["N_BOTTOM"]
    print(f"N_BOTTOM node count: {len(n_bottom)}")
    bottom_unconnected = [nid for nid in n_bottom if len(elem_nodes[nid]) == 0]
    print(f"N_BOTTOM unconnected nodes: {len(bottom_unconnected)}")
    if bottom_unconnected:
        print(f"  Sample unconnected: {bottom_unconnected[:10]}")
    else:
        # Check Y-coordinates of N_BOTTOM
        y_coords = [nodes[nid][1] for nid in n_bottom]
        print(f"  N_BOTTOM Y range: min={min(y_coords):.6f}, max={max(y_coords):.6f}")
        
    n_top = nsets["N_TOP"]
    print(f"\nN_TOP node count: {len(n_top)}")
    top_unconnected = [nid for nid in n_top if len(elem_nodes[nid]) == 0]
    print(f"N_TOP unconnected nodes: {len(top_unconnected)}")
    if top_unconnected:
        print(f"  Sample unconnected: {top_unconnected[:10]}")
    else:
        # Check Y-coordinates of N_TOP
        y_coords = [nodes[nid][1] for nid in n_top]
        print(f"  N_TOP Y range: min={min(y_coords):.6f}, max={max(y_coords):.6f}")
        
    # Check all 9801 nodes for orphan nodes
    all_unconnected = [nid for nid in range(1, 9802) if nid in nodes and len(elem_nodes[nid]) == 0 and nid != 99999]
    print(f"\nTotal physical orphan nodes (1..9801): {len(all_unconnected)}")

if __name__ == "__main__":
    audit_boundary_connectivity()
