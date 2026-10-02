"""
Script to extract exact Gauss-point coordinates, element coordinates, strain components,
strain energy density (psi_+), history (H), and damage (d) around the notch tip (0,0)
for H1 (1389686) and PK10R2 (1390056) at matched displacements.
"""

import sys
import os
import math
import json

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {} # el_label -> [n1, n2, n3, n4]
    with open(inp_path) as f:
        in_nodes = False
        in_disp = False
        for line in f:
            line = line.strip()
            if line.startswith('*Node') or line.startswith('*NODE'):
                in_nodes = True
                in_disp = False
                continue
            elif line.startswith('*Element') or line.startswith('*ELEMENT'):
                in_nodes = False
                if 'DISP_QUAD' in line:
                    in_disp = True
                else:
                    in_disp = False
                continue
            elif line.startswith('*'):
                in_nodes = False
                in_disp = False
                continue

            if in_nodes and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except: pass
            elif in_disp and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 5:
                    try:
                        elements[int(parts[0])] = [int(parts[i]) for i in range(1, 5)]
                    except: pass
    return nodes, elements

def get_gauss_points(node_coords):
    # 2x2 Gauss quadrature points in physical coords
    # xi, eta in [-1/sqrt(3), 1/sqrt(3)]
    g_local = [-0.577350269189626, 0.577350269189626]
    pts = []
    for eta in g_local:
        for xi in g_local:
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
            gx = n1 * node_coords[0][0] + n2 * node_coords[1][0] + n3 * node_coords[2][0] + n4 * node_coords[3][0]
            gy = n1 * node_coords[0][1] + n2 * node_coords[1][1] + n3 * node_coords[2][1] + n4 * node_coords[3][1]
            pts.append((gx, gy))
    return pts

def audit_model_crack_tip(name, inp_path):
    nodes, elements = parse_inp_mesh(inp_path)
    
    # Find elements within 0.02 mm of notch tip (0,0)
    tip_elements = []
    for el_id, conn in elements.items():
        coords = [nodes[n] for n in conn if n in nodes]
        if len(coords) == 4:
            cx = sum([c[0] for c in coords]) / 4.0
            cy = sum([c[1] for c in coords]) / 4.0
            dist = math.sqrt(cx**2 + cy**2)
            if dist < 0.025:
                # compute edge lengths
                edges = [math.sqrt((coords[i][0]-coords[(i+1)%4][0])**2 + (coords[i][1]-coords[(i+1)%4][1])**2) for i in range(4)]
                g_pts = get_gauss_points(coords)
                min_g_dist = min([math.sqrt(gx**2 + gy**2) for gx, gy in g_pts])
                tip_elements.append({
                    "el_id": el_id,
                    "conn": conn,
                    "center": (cx, cy),
                    "dist_center": dist,
                    "min_edge_h": min(edges),
                    "max_edge_h": max(edges),
                    "gauss_points": g_pts,
                    "min_gauss_dist_to_tip": min_g_dist
                })

    tip_elements.sort(key=lambda x: x["min_gauss_dist_to_tip"])
    
    print("================================================================================")
    print("CRACK TIP MESH & GAUSS QUADRATURE AUDIT: " + name)
    print("INP: " + inp_path)
    print("Elements in tip neighborhood (< 0.025 mm): " + str(len(tip_elements)))
    print("Closest 4 elements to notch tip (0,0):")
    for el in tip_elements[:4]:
        print("  Element {0}: Center=({1:.5f}, {2:.5f}), h_edge={3:.5f} mm".format(
            el["el_id"], el["center"][0], el["center"][1], el["min_edge_h"]))
        print("    Nodes: " + str(el["conn"]))
        print("    Gauss Points (physical coords):")
        for g_idx, (gx, gy) in enumerate(el["gauss_points"]):
            g_dist = math.sqrt(gx**2 + gy**2)
            print("      GP {0}: ({1:.6f}, {2:.6f}) -> dist to tip = {3:.6f} mm".format(g_idx+1, gx, gy, g_dist))
    return tip_elements

def main():
    h1_tip = audit_model_crack_tip("H1_UNIFORM_FINE", "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    pk10r2_tip = audit_model_crack_tip("PK10R2_TOPOLOGY_CORRECTED", "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED/M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp")

    # Compare nearest Gauss point to tip
    h1_nearest_gp = h1_tip[0]["min_gauss_dist_to_tip"]
    pk10r2_nearest_gp = pk10r2_tip[0]["min_gauss_dist_to_tip"]
    
    print("================================================================================")
    print("GAUSS POINT PROXIMITY COMPARISON:")
    print("  H1 nearest Gauss point to tip (0,0):      {0:.6f} mm".format(h1_nearest_gp))
    print("  PK10R2 nearest Gauss point to tip (0,0):  {0:.6f} mm".format(pk10r2_nearest_gp))
    print("  Proximity ratio (r_PK10R2 / r_H1):        {0:.2f}x further from singular tip".format(pk10r2_nearest_gp / h1_nearest_gp))
    print("  Theoretical elastic strain energy scale (1/r): ~{0:.2f}x reduction at nearest GP".format(pk10r2_nearest_gp / h1_nearest_gp))
    print("  Element volume ratio (h_PK10R2^2 / h_H1^2):    {0:.2f}x volume averaging".format((pk10r2_tip[0]["min_edge_h"] / h1_tip[0]["min_edge_h"])**2))
    print("================================================================================")

if __name__ == "__main__":
    main()
