#!/usr/bin/env python3
"""
Check Jacobian determinant and orientation of all quads and triangles in M2STATE_FRACFIX_RESTART2R5.inp.
"""
from pathlib import Path

def audit_mesh_jacobians():
    root = Path(__file__).resolve().parent.parent.parent
    inp_path = root / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5/M2STATE_FRACFIX_RESTART2R5.inp"
    
    nodes = {}
    quads = {}
    tris = {}
    
    with open(inp_path, "r", errors="ignore") as f:
        in_node = False
        in_u1 = False
        in_u3 = False
        
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
                    
            if "*ELEMENT, TYPE=U1" in line:
                in_u1 = True
                continue
            elif in_u1 and line.startswith("*"):
                in_u1 = False
            elif in_u1:
                parts = [int(p.strip()) for p in line.split(",") if p.strip()]
                if len(parts) >= 5:
                    quads[parts[0]] = parts[1:5]
                    
            if "*ELEMENT, TYPE=U3" in line:
                in_u3 = True
                continue
            elif in_u3 and line.startswith("*"):
                in_u3 = False
            elif in_u3:
                parts = [int(p.strip()) for p in line.split(",") if p.strip()]
                if len(parts) >= 4:
                    tris[parts[0]] = parts[1:4]

    print(f"Loaded {len(nodes)} nodes, {len(quads)} quads, {len(tris)} tris")
    
    # Audit Quads
    quad_neg_detj = []
    for eid, enodes in quads.items():
        c = [nodes[nid] for nid in enodes]
        # detJ = ((x2-x1)*(y4-y1) - (x4-x1)*(y2-y1)) / 4.0
        detJ = ((c[1][0]-c[0][0])*(c[3][1]-c[0][1]) - (c[3][0]-c[0][0])*(c[1][1]-c[0][1])) / 4.0
        if detJ <= 0.0:
            quad_neg_detj.append((eid, detJ, enodes))
            
    print(f"Quads with detJ <= 0: {len(quad_neg_detj)}")
    for q in quad_neg_detj[:10]:
        print(f"  Quad {q[0]}: detJ = {q[1]:.6e}, nodes = {q[2]}")
        
    # Audit Tris
    tri_neg_detj = []
    for eid, enodes in tris.items():
        c = [nodes[nid] for nid in enodes]
        # detJ = (x2-x1)*(y3-y1) - (x3-x1)*(y2-y1)
        detJ = (c[1][0]-c[0][0])*(c[2][1]-c[0][1]) - (c[2][0]-c[0][0])*(c[1][1]-c[0][1])
        if detJ <= 0.0:
            tri_neg_detj.append((eid, detJ, enodes))
            
    print(f"Tris with detJ <= 0: {len(tri_neg_detj)}")
    for t in tri_neg_detj[:10]:
        print(f"  Tri {t[0]}: detJ = {t[1]:.6e}, nodes = {t[2]}")

if __name__ == "__main__":
    audit_mesh_jacobians()
