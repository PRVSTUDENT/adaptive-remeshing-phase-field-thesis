#!/usr/bin/env python3
import sys
from collections import defaultdict
from pathlib import Path

# Import generate_pk10r1_mesh
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "model_generation"))
from build_mode_ii_state_transfer_restart2r4_batch import generate_pk10r1_mesh

def find_boundary_nodes():
    nodes, quads, tris = generate_pk10r1_mesh()
    
    # Track edge occurrences (undirected)
    edge_count = defaultdict(int)
    edge_elems = defaultdict(list)
    
    for qid, conn in quads.items():
        edges = [
            tuple(sorted((conn[0], conn[1]))),
            tuple(sorted((conn[1], conn[2]))),
            tuple(sorted((conn[2], conn[3]))),
            tuple(sorted((conn[3], conn[0])))
        ]
        for e in edges:
            edge_count[e] += 1
            edge_elems[e].append(qid)
            
    for tid, conn in tris.items():
        edges = [
            tuple(sorted((conn[0], conn[1]))),
            tuple(sorted((conn[1], conn[2]))),
            tuple(sorted((conn[2], conn[0])))
        ]
        for e in edges:
            edge_count[e] += 1
            edge_elems[e].append(tid)
            
    boundary_edges = [e for e, count in edge_count.items() if count == 1]
    boundary_nodes = set()
    for e in boundary_edges:
        boundary_nodes.add(e[0])
        boundary_nodes.add(e[1])
        
    print(f"Total boundary edges: {len(boundary_edges)}")
    print(f"Total boundary nodes: {len(boundary_nodes)}")
    
    # Categorize boundary nodes by position
    y_vals = [nodes[n][1] for n in boundary_nodes]
    x_vals = [nodes[n][0] for n in boundary_nodes]
    y_max = max(y_vals)
    y_min = min(y_vals)
    x_max = max(x_vals)
    x_min = min(x_vals)
    
    print(f"Active domain bounds: X in [{x_min:.6f}, {x_max:.6f}], Y in [{y_min:.6f}, {y_max:.6f}]")
    
    top_boundary_nodes = sorted([n for n in boundary_nodes if abs(nodes[n][1] - y_max) < 1e-5])
    bottom_boundary_nodes = sorted([n for n in boundary_nodes if abs(nodes[n][1] - y_min) < 1e-5])
    left_boundary_nodes = sorted([n for n in boundary_nodes if abs(nodes[n][0] - x_min) < 1e-5])
    right_boundary_nodes = sorted([n for n in boundary_nodes if abs(nodes[n][0] - x_max) < 1e-5])
    
    print(f"Top boundary nodes (Y = {y_max:.6f}): {len(top_boundary_nodes)} nodes (min={min(top_boundary_nodes)}, max={max(top_boundary_nodes)})")
    print(f"Bottom boundary nodes (Y = {y_min:.6f}): {len(bottom_boundary_nodes)} nodes (min={min(bottom_boundary_nodes)}, max={max(bottom_boundary_nodes)})")
    print(f"Left boundary nodes (X = {x_min:.6f}): {len(left_boundary_nodes)} nodes")
    print(f"Right boundary nodes (X = {x_max:.6f}): {len(right_boundary_nodes)} nodes")
    
    return {
        "y_max": y_max,
        "y_min": y_min,
        "top_nodes": top_boundary_nodes,
        "bottom_nodes": bottom_boundary_nodes,
        "left_nodes": left_boundary_nodes,
        "right_nodes": right_boundary_nodes
    }

if __name__ == "__main__":
    find_boundary_nodes()
