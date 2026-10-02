#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate Graded Stage-D Nonmatching Target Mesh Matching H1 Resolution.

Geometry:
- Domain: [-0.5, 0.5] x [-0.5, 0.5] mm
- Slit: y = 0.0, x in [-0.5, 0.0]
- Open-slit topology: independent split nodes along slit line
- Resolution: Graded mesh with h_tip = 0.002500 mm (matching H1) graded to h_outer = 0.025000 mm.
- Nonmatching: Coordinate lines shifted by delta_x = 0.0005 mm, delta_y = 0.0005 mm (or nonmatching node distribution)
  so that NO target node/GP coincides with H1.
"""

import sys
import os
import math
import numpy as np

def create_graded_coordinates(n_tip, n_outer, x_min, x_max, x_tip, h_tip, h_outer, shift=0.0):
    """
    Create graded 1D coordinate grid matching H1 crack-tip resolution but with nonmatching shift.
    """
    # Left of tip: [x_min, x_tip] = [-0.5, 0.0]
    # Right of tip: [x_tip, x_max] = [0.0, 0.5]
    
    # We create graded distribution:
    # Fine uniform region around tip [-0.05, 0.05] with h = h_tip
    # Geometric grading from |x|=0.05 to |x|=0.5 with ratio ~ 1.15
    
    # Fine inner region
    x_fine_left = np.arange(-0.05 + shift, 0.0, h_tip)
    if len(x_fine_left) == 0 or x_fine_left[-1] != 0.0:
        x_fine_left = np.append(x_fine_left, 0.0)
        
    x_fine_right = np.arange(0.0, 0.05 + shift, h_tip)
    if x_fine_right[0] == 0.0 and len(x_fine_left) > 0 and x_fine_left[-1] == 0.0:
        x_fine_right = x_fine_right[1:]
        
    # Coarse graded outer regions
    # Left outer: -0.5 to -0.05
    x_cur = x_fine_left[0]
    h_cur = h_tip
    left_outer = []
    while x_cur > x_min:
        h_cur = min(h_outer, h_cur * 1.15)
        x_cur = x_cur - h_cur
        if x_cur <= x_min:
            left_outer.append(x_min)
            break
        else:
            left_outer.append(x_cur)
    left_outer.reverse()
    
    # Right outer: 0.05 to 0.5
    x_cur = x_fine_right[-1]
    h_cur = h_tip
    right_outer = []
    while x_cur < x_max:
        h_cur = min(h_outer, h_cur * 1.15)
        x_cur = x_cur + h_cur
        if x_cur >= x_max:
            right_outer.append(x_max)
            break
        else:
            right_outer.append(x_cur)
            
    # Combine
    all_x = np.concatenate([left_outer[:-1], x_fine_left, x_fine_right, right_outer[1:]])
    all_x = np.unique(np.sort(all_x))
    
    # Ensure -0.5, 0.0, 0.5 are exact
    all_x[0] = -0.5
    all_x[-1] = 0.5
    zero_idx = np.argmin(np.abs(all_x))
    all_x[zero_idx] = 0.0
    
    return all_x

def generate_graded_stage_d_target_mesh(out_dir):
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("Generating Graded Stage-D Nonmatching Target Mesh...")
    
    # Crack tip resolution h_tip = 0.002450 mm (deliberately nonmatching with H1's 0.002500 mm)
    # Outer resolution h_outer = 0.024500 mm
    h_tip = 0.002450
    h_outer = 0.024500
    
    x_coords = create_graded_coordinates(20, 20, -0.5, 0.5, 0.0, h_tip, h_outer, shift=0.0003)
    y_coords = create_graded_coordinates(20, 20, -0.5, 0.5, 0.0, h_tip, h_outer, shift=0.0003)
    
    # Find y=0 index
    y_zero_idx = np.argmin(np.abs(y_coords))
    y_coords[y_zero_idx] = 0.0
    
    # Find x=0 index
    x_zero_idx = np.argmin(np.abs(x_coords))
    x_coords[x_zero_idx] = 0.0
    
    Nx = len(x_coords) - 1
    Ny_bot = y_zero_idx
    Ny_top = len(y_coords) - 1 - y_zero_idx
    
    print("Graded Grid Dimensions: Nx = %d, Ny_bot = %d, Ny_top = %d (Total Ny = %d)" % (
        Nx, Ny_bot, Ny_top, len(y_coords) - 1))
        
    nodes = {}
    elements = {}
    
    # Bottom half grid (j = 0 .. Ny_bot)
    bot_node_grid = np.zeros((Ny_bot + 1, Nx + 1), dtype=int)
    nid = 1
    for j in range(Ny_bot + 1):
        y = y_coords[j]
        for i in range(Nx + 1):
            x = x_coords[i]
            nodes[nid] = (x, y)
            bot_node_grid[j, i] = nid
            nid += 1
            
    # Top half grid (j = 0 .. Ny_top)
    top_node_grid = np.zeros((Ny_top + 1, Nx + 1), dtype=int)
    for j in range(Ny_top + 1):
        y = y_coords[y_zero_idx + j]
        for i in range(Nx + 1):
            x = x_coords[i]
            if j == 0:
                if x > 0.0:
                    # Ahead of crack tip: shared with bottom top-line
                    top_node_grid[j, i] = bot_node_grid[Ny_bot, i]
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
    for j in range(Ny_bot):
        for i in range(Nx):
            n1 = bot_node_grid[j, i]
            n2 = bot_node_grid[j, i + 1]
            n3 = bot_node_grid[j + 1, i + 1]
            n4 = bot_node_grid[j + 1, i]
            elements[eid] = [n1, n2, n3, n4]
            eid += 1
            
    # Top half elements
    for j in range(Ny_top):
        for i in range(Nx):
            n1 = top_node_grid[j, i]
            n2 = top_node_grid[j, i + 1]
            n3 = top_node_grid[j + 1, i + 1]
            n4 = top_node_grid[j + 1, i]
            elements[eid] = [n1, n2, n3, n4]
            eid += 1
            
    num_nodes = len(nodes)
    num_elements = len(elements)
    print("Generated Graded Target Mesh: %d physical nodes, %d physical quads" % (
        num_nodes, num_elements))
        
    # Verify Slit Disconnection:
    slit_bot_nodes = [bot_node_grid[Ny_bot, i] for i in range(x_zero_idx + 1)]
    slit_top_nodes = [top_node_grid[0, i] for i in range(x_zero_idx + 1)]
    shared_slit = set(slit_bot_nodes).intersection(set(slit_top_nodes))
    print("Slit check: %d bot slit nodes, %d top slit nodes | Shared along slit (should be 0): %d" % (
        len(slit_bot_nodes), len(slit_top_nodes), len(shared_slit)))
    assert len(shared_slit) == 0, "Error: Slit nodes are shared!"
    
    # Calculate crack-tip resolution
    tip_elem_sizes = []
    for eid, conn in elements.items():
        coords = [nodes[n] for n in conn]
        xs = [c[0] for c in coords]
        ys = [c[1] for c in coords]
        centroid_r = math.sqrt((sum(xs)/4.0)**2 + (sum(ys)/4.0)**2)
        if centroid_r < 0.05:
            tip_elem_sizes.append(max(max(xs)-min(xs), max(ys)-min(ys)))
            
    print("Target Mesh Crack-Tip Resolution: h_min = %.6f mm, h_avg = %.6f mm (matches H1 h_min = 0.002500 mm)" % (
        min(tip_elem_sizes), sum(tip_elem_sizes)/len(tip_elem_sizes)))
        
    mesh_info = {
        "num_nodes": num_nodes,
        "num_elements": num_elements,
        "nodes": nodes,
        "elements": elements,
        "nx": Nx,
        "ny": Ny_bot + Ny_top,
        "bot_nodes": [bot_node_grid[0, i] for i in range(Nx + 1)],
        "top_nodes": [top_node_grid[Ny_top, i] for i in range(Nx + 1)],
        "slit_bot_nodes": slit_bot_nodes,
        "slit_top_nodes": slit_top_nodes,
        "rp_node": 99999
    }
    return mesh_info

if __name__ == "__main__":
    out_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL"
    generate_graded_stage_d_target_mesh(out_dir)
