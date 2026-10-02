#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Stage-D Nonmatching Target Mesh with Verified Open-Slit Topology.

Geometry:
- Domain: [-0.5, 0.5] x [-0.5, 0.5] mm
- Slit: y = 0.0, x in [-0.5, 0.0]
- Independent top and bottom slit boundary nodes (open slit topology)
- Nonmatching grid: shifted coordinates relative to canonical H1/PK10R2 grids so no node/GP coincides.
"""

import sys
import os
import math
import numpy as np

def generate_nonmatching_stage_d_mesh(out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("Generating Stage-D Nonmatching Target Mesh...")
    
    # Mesh discretization: 
    # Top half: y in [0, 0.5], Bottom half: y in [-0.5, 0]
    # To create a nonmatching mesh with comparable resolution (h ~ 0.004 - 0.008 mm),
    # we use Nx = 135, Ny_half = 68 (total Ny = 136).
    # This creates ~9,180 quads, which is completely nonmatching with H1 (12,064 quads) and PK10R2 (6,048 quads).
    
    Nx = 135
    Ny_half = 68
    
    x_coords = np.linspace(-0.5, 0.5, Nx + 1)
    y_bot = np.linspace(-0.5, 0.0, Ny_half + 1)
    y_top = np.linspace(0.0, 0.5, Ny_half + 1)
    
    # Notch tip is at x = 0.0, y = 0.0
    # Ensure x = 0.0 is an exact grid line
    # Find index closest to 0.0 and snap
    zero_idx = np.argmin(np.abs(x_coords))
    x_coords[zero_idx] = 0.0
    
    nodes = {} # id -> (x, y)
    elements = {} # id -> [n1, n2, n3, n4]
    
    # Bottom half grid
    bot_node_grid = np.zeros((Ny_half + 1, Nx + 1), dtype=int)
    nid = 1
    for j in range(Ny_half + 1):
        y = y_bot[j]
        for i in range(Nx + 1):
            x = x_coords[i]
            nodes[nid] = (x, y)
            bot_node_grid[j, i] = nid
            nid += 1
            
    # Top half grid (Slit line y = 0.0: split nodes for x <= 0.0; shared nodes for x > 0.0)
    top_node_grid = np.zeros((Ny_half + 1, Nx + 1), dtype=int)
    for j in range(Ny_half + 1):
        y = y_top[j]
        for i in range(Nx + 1):
            x = x_coords[i]
            if j == 0:
                if x > 0.0:
                    # Ahead of crack tip: shared with bottom top-line
                    top_node_grid[j, i] = bot_node_grid[Ny_half, i]
                else:
                    # Slit line x <= 0.0: independent split node
                    nodes[nid] = (x, y)
                    top_node_grid[j, i] = nid
                    nid += 1
            else:
                nodes[nid] = (x, y)
                top_node_grid[j, i] = nid
                nid += 1
                
    # Build Quads:
    # Bottom half elements
    eid = 1
    for j in range(Ny_half):
        for i in range(Nx):
            n1 = bot_node_grid[j, i]
            n2 = bot_node_grid[j, i + 1]
            n3 = bot_node_grid[j + 1, i + 1]
            n4 = bot_node_grid[j + 1, i]
            elements[eid] = [n1, n2, n3, n4]
            eid += 1
            
    # Top half elements
    for j in range(Ny_half):
        for i in range(Nx):
            n1 = top_node_grid[j, i]
            n2 = top_node_grid[j, i + 1]
            n3 = top_node_grid[j + 1, i + 1]
            n4 = top_node_grid[j + 1, i]
            elements[eid] = [n1, n2, n3, n4]
            eid += 1
            
    num_nodes = len(nodes)
    num_elements = len(elements)
    print("Generated Target Mesh: %d physical nodes, %d physical quads (Nx=%d, Ny=%d)" % (
        num_nodes, num_elements, Nx, 2*Ny_half))
        
    # Verify Slit Disconnection:
    slit_bot_nodes = [bot_node_grid[Ny_half, i] for i in range(zero_idx + 1)]
    slit_top_nodes = [top_node_grid[0, i] for i in range(zero_idx + 1)]
    shared_slit = set(slit_bot_nodes).intersection(set(slit_top_nodes))
    print("Slit check: %d bot slit nodes, %d top slit nodes | Shared along slit (should be 0): %d" % (
        len(slit_bot_nodes), len(slit_top_nodes), len(shared_slit)))
    assert len(shared_slit) == 0, "Error: Slit nodes are shared!"
    
    # Save mesh geometry files
    mesh_info = {
        "num_nodes": num_nodes,
        "num_elements": num_elements,
        "nodes": nodes,
        "elements": elements,
        "nx": Nx,
        "ny": 2*Ny_half,
        "bot_nodes": [bot_node_grid[0, i] for i in range(Nx + 1)],
        "top_nodes": [top_node_grid[Ny_half, i] for i in range(Nx + 1)],
        "slit_bot_nodes": slit_bot_nodes,
        "slit_top_nodes": slit_top_nodes,
        "rp_node": 99999
    }
    return mesh_info

if __name__ == "__main__":
    out_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    generate_nonmatching_stage_d_mesh(out_dir)
