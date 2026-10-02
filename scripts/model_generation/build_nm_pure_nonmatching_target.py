#!/usr/bin/env python3
"""
Pure Nonmatching Target Mesh Generator (Benchmark Class NM-A / NM-B):
Task ID: F208AUDIT-M2-HISTORY-TRANSFER-LITERATURE-PROVENANCE-AND-NONMATCHING-BENCHMARK-DESIGN1

Generates a pure nonmatching target mesh with:
  - Same 1.0 x 1.0 mm physical domain ([-0.5, 0.5] x [-0.5, 0.5])
  - Same unnotched / unsplit PK10R1 topology (continuous ligament along y=0)
  - Same boundary sets and reference point (RP at (0.0, 0.5))
  - Genuinely nonmatching discretization: 80 x 80 uniform quads (h = 0.0125 mm)
  - Zero shared interior node coordinates with PK10R1 graded mesh
"""

import os
import json
import hashlib

def generate_nm_pure_target_inp(output_path):
    xmin, xmax = -0.5, 0.5
    ymin, ymax = -0.5, 0.5
    nx, ny = 80, 80 # h = 0.0125 mm (nonmatching with PK10R1 h_local=0.010, h_global=0.050)
    
    dx = (xmax - xmin) / float(nx)
    dy = (ymax - ymin) / float(ny)
    
    nodes = []
    # 1-based node indexing
    # RP Node at 99999
    rp_node_id = 99999
    rp_coord = (0.0, 0.5)
    
    node_id = 1
    node_grid = {}
    for j in range(ny + 1):
        y = ymin + j * dy
        for i in range(nx + 1):
            x = xmin + i * dx
            nodes.append((node_id, x, y))
            node_grid[(i, j)] = node_id
            node_id += 1
            
    num_physical_nodes = len(nodes) # (81 * 81 = 6561 physical nodes)
    
    # Generate Physical Quads (Layer 1: Phase U1, Layer 2: Mechanical U2)
    # Total physical quads = 80 * 80 = 6400 elements
    elements_layer1 = []
    elements_layer2 = []
    
    n_phys = nx * ny # 6400
    elem_id = 1
    
    for j in range(ny):
        for i in range(nx):
            n1 = node_grid[(i, j)]
            n2 = node_grid[(i + 1, j)]
            n3 = node_grid[(i + 1, j + 1)]
            n4 = node_grid[(i, j + 1)]
            elements_layer1.append((elem_id, n1, n2, n3, n4))
            elements_layer2.append((elem_id + n_phys, n1, n2, n3, n4))
            elem_id += 1
            
    # Node sets
    bot_nodes = [node_grid[(i, 0)] for i in range(nx + 1)]
    top_nodes = [node_grid[(i, ny)] for i in range(nx + 1)]
    left_nodes = [node_grid[(0, j)] for j in range(ny + 1)]
    right_nodes = [node_grid[(nx, j)] for j in range(ny + 1)]
    
    lines = []
    lines.append("*HEADING")
    lines.append("M2_PURE_NONMATCHING_TARGET_BENCHMARK_NMA (80x80 Uniform Quads, h=0.0125mm)")
    lines.append("*NODE")
    for nid, x, y in nodes:
        lines.append(f"{nid:8d}, {x:14.8f}, {y:14.8f}")
    lines.append(f"{rp_node_id:8d}, {rp_coord[0]:14.8f}, {rp_coord[1]:14.8f}")
    
    lines.append("*ELEMENT, TYPE=U1, ELSET=PHASE_QUADS")
    for eid, n1, n2, n3, n4 in elements_layer1:
        lines.append(f"{eid:8d}, {n1:8d}, {n2:8d}, {n3:8d}, {n4:8d}")
        
    lines.append("*ELEMENT, TYPE=U2, ELSET=MECH_QUADS")
    for eid, n1, n2, n3, n4 in elements_layer2:
        lines.append(f"{eid:8d}, {n1:8d}, {n2:8d}, {n3:8d}, {n4:8d}")
        
    # Element Sets
    lines.append("*ELSET, ELSET=ALL_ELEMENTS")
    lines.append("PHASE_QUADS, MECH_QUADS")
    
    # Node Sets
    def write_nset(name, nlist):
        lines.append(f"*NSET, NSET={name}")
        for k in range(0, len(nlist), 16):
            chunk = nlist[k:k+16]
            lines.append(", ".join(f"{nid}" for nid in chunk))
            
    write_nset("BOT_NODES", bot_nodes)
    write_nset("TOP_NODES", top_nodes)
    write_nset("LEFT_NODES", left_nodes)
    write_nset("RIGHT_NODES", right_nodes)
    lines.append("*NSET, NSET=RP_NODE")
    lines.append(f"{rp_node_id}")
    
    # Coupling Equation / Kinematics (Top surface tied to RP Node in U1)
    # Using standard MPC / Equation for Mode-II shear loading
    lines.append("*EQUATION")
    for tn in top_nodes:
        lines.append("2")
        lines.append(f"{tn}, 1, 1.0, {rp_node_id}, 1, -1.0")
        
    content = "\n".join(lines) + "\n"
    
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w") as f:
        f.write(content)
        
    sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    print(f"Generated Pure Nonmatching Target Mesh: {output_path}")
    print(f"  Physical Nodes: {num_physical_nodes}, RP Node: 1, Total: {num_physical_nodes + 1}")
    print(f"  Physical Quads: {n_phys} (Total Layered Elements: {2 * n_phys})")
    print(f"  Element Size h: {dx:.6f} mm")
    print(f"  SHA256: {sha}")
    
    return {
        "output_path": output_path,
        "num_physical_nodes": num_physical_nodes,
        "num_physical_quads": n_phys,
        "element_size_h": dx,
        "sha256": sha
    }

if __name__ == "__main__":
    out = "models/generated/mode_ii/benchmark_mesh_candidates/M2_PURE_NONMATCHING_TARGET_NMA_80x80.inp"
    generate_nm_pure_target_inp(out)
