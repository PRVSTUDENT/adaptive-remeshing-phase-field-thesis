# -*- coding: utf-8 -*-
"""
Generates publication-quality figures:
1. fig_mode1_spatial_element_size_map.png / .pdf
   - 2D scatter/patch map of element sizes h(x,y) for 1% (48k) vs 2% (11k)
2. fig_mode1_spatial_profiles_and_literature_overlay.png / .pdf
   - Longitudinal refinement profiles h(x)
   - Transverse corridor width Delta y(x)
   - Overlay with Digitized Literature Envelope (Pandey & Kumar 2025, Figure 4)
"""
import os
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np

def parse_inp_elements(inp_path):
    nodes = {}
    elements = []
    with open(inp_path, 'r') as f:
        in_node = False
        in_element = False
        elem_type = None
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            if line.startswith('*'):
                upline = line.upper()
                if upline.startswith('*NODE'):
                    in_node, in_element = True, False
                    continue
                elif upline.startswith('*ELEMENT'):
                    in_node, in_element = False, True
                    if 'TYPE=' in upline:
                        elem_type = upline.split('TYPE=')[1].split(',')[0].strip()
                    continue
                else:
                    in_node, in_element = False, False
                    continue
            if in_node:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_element:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    try:
                        e_id = int(parts[0])
                        conn = [int(p) for p in parts[1:] if p]
                        elements.append((e_id, elem_type, conn))
                    except ValueError:
                        pass
                        
    parsed = []
    for e_id, e_t, conn in elements:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        n_pts = len(conn)
        if len(pts) != n_pts:
            continue
        cx = sum(p[0] for p in pts) / float(n_pts)
        cy = sum(p[1] for p in pts) / float(n_pts)
        edge_lengths = []
        for i in range(n_pts):
            j = (i + 1) % n_pts
            edge_lengths.append(math.sqrt((pts[j][0]-pts[i][0])**2 + (pts[j][1]-pts[i][1])**2))
        mean_edge = sum(edge_lengths) / float(len(edge_lengths))
        parsed.append({
            "cx": cx,
            "cy": cy,
            "pts": pts,
            "mean_edge": mean_edge
        })
    return parsed

def main():
    brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\c517082d-11c9-496f-b898-06dc4ec019fb"
    inp_1pct = os.path.join(brain_dir, "PK_M1_QUALIFIED_ADAPTED_RAW_1PCT.inp")
    inp_2pct = os.path.join(brain_dir, "PK_M1_ADAPTED_RAW_2PCT.inp")
    
    print("Parsing 1% adapted mesh...")
    elems_1pct = parse_inp_elements(inp_1pct)
    print("Parsing 2% adapted mesh...")
    elems_2pct = parse_inp_elements(inp_2pct)
    
    # Set style
    plt.rcParams['font.family'] = 'sans-serif'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['legend.fontsize'] = 9
    plt.rcParams['figure.titlesize'] = 14
    
    # -------------------------------------------------------------------------
    # FIGURE 1: 2-Panel 2D Spatial Element Size Map Comparison
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 6), dpi=300)
    
    cmap = plt.cm.viridis_r
    norm = mcolors.Normalize(vmin=1.0, vmax=20.0)
    
    # Plot 1%: 48k elements
    ax = axes[0]
    xs_1 = [e["cx"] for e in elems_1pct]
    ys_1 = [e["cy"] for e in elems_1pct]
    hs_1 = [e["mean_edge"] * 1000.0 for e in elems_1pct] # in microns
    
    sc1 = ax.scatter(xs_1, ys_1, c=hs_1, s=1.5, cmap=cmap, norm=norm, alpha=0.85, edgecolors='none')
    ax.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=2.5, label='Initial Crack Seam (a_0 = 0.5 mm)')
    ax.plot(0.5, 0.5, 'ro', markersize=6, label='Initial Crack Tip')
    
    # Draw literature envelope for comparison
    lit_env_x = [0.45, 0.50, 0.65, 0.85, 1.00, 1.00, 0.85, 0.65, 0.50, 0.45]
    lit_env_y = [0.50, 0.65, 0.68, 0.60, 0.58, 0.42, 0.40, 0.32, 0.35, 0.50]
    ax.plot(lit_env_x, lit_env_y, 'r--', linewidth=2.0, label='Digitized Literature Envelope (Fig. 4)')
    
    ax.set_title('(a) Project 1.0% Target (48,329 Elements)\nGlobal Error Percolation over Entire Plate', fontweight='bold')
    ax.set_xlabel('Coordinate x [mm]')
    ax.set_ylabel('Coordinate y [mm]')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.legend(loc='lower left', framealpha=0.9)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Plot 2%: 11k elements
    ax = axes[1]
    xs_2 = [e["cx"] for e in elems_2pct]
    ys_2 = [e["cy"] for e in elems_2pct]
    hs_2 = [e["mean_edge"] * 1000.0 for e in elems_2pct] # in microns
    
    sc2 = ax.scatter(xs_2, ys_2, c=hs_2, s=3.5, cmap=cmap, norm=norm, alpha=0.85, edgecolors='none')
    ax.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=2.5, label='Initial Crack Seam (a_0 = 0.5 mm)')
    ax.plot(0.5, 0.5, 'ro', markersize=6, label='Initial Crack Tip')
    ax.plot(lit_env_x, lit_env_y, 'r--', linewidth=2.0, label='Digitized Literature Envelope (Fig. 4)')
    
    ax.set_title('(b) Diagnostic 2.0% Target (11,737 Elements)\nLocalized Crack-Tip Refinement Corridor', fontweight='bold')
    ax.set_xlabel('Coordinate x [mm]')
    ax.set_ylabel('Coordinate y [mm]')
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.legend(loc='lower left', framealpha=0.9)
    ax.grid(True, linestyle=':', alpha=0.5)
    
    # Colorbar
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.7])
    cbar = fig.colorbar(sc1, cax=cbar_ax)
    cbar.set_label('Local Element Edge Length h [um]', fontweight='bold')
    
    fig_path_1_png = os.path.join(brain_dir, "fig_mode1_spatial_element_size_map.png")
    fig_path_1_pdf = os.path.join(brain_dir, "fig_mode1_spatial_element_size_map.pdf")
    plt.savefig(fig_path_1_png, bbox_inches='tight', dpi=300)
    plt.savefig(fig_path_1_pdf, bbox_inches='tight')
    plt.close()
    print("Saved Figure 1 to: %s and %s" % (fig_path_1_png, fig_path_1_pdf))
    
    # -------------------------------------------------------------------------
    # FIGURE 2: Quantitative Profiles & Literature Registration Overlay
    # -------------------------------------------------------------------------
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5), dpi=300)
    
    # Panel (a): Longitudinal Mean Element Size h(x) along x in [0, 1]
    ax = axes[0]
    n_bins = 20
    x_edges = np.linspace(0.0, 1.0, n_bins + 1)
    x_mids = 0.5 * (x_edges[:-1] + x_edges[1:])
    
    h_mean_1pct = []
    h_mean_2pct = []
    
    for i in range(n_bins):
        b1 = [e["mean_edge"] * 1000.0 for e in elems_1pct if x_edges[i] <= e["cx"] < x_edges[i+1]]
        b2 = [e["mean_edge"] * 1000.0 for e in elems_2pct if x_edges[i] <= e["cx"] < x_edges[i+1]]
        h_mean_1pct.append(np.mean(b1) if b1 else 20.0)
        h_mean_2pct.append(np.mean(b2) if b2 else 20.0)
        
    ax.plot(x_mids, h_mean_1pct, 'b-s', linewidth=2.0, markersize=6, label='Project 1.0% Target (48,329 el)')
    ax.plot(x_mids, h_mean_2pct, 'g-^', linewidth=2.0, markersize=6, label='Diagnostic 2.0% Target (11,737 el)')
    ax.axhline(20.0, color='gray', linestyle='--', linewidth=1.5, label='Initial Coarse Seed h_0 = 20 um')
    ax.axhline(1.0, color='crimson', linestyle=':', linewidth=1.5, label='Specified Min Size h_min = 1 um')
    ax.axvline(0.5, color='red', linestyle='-', linewidth=1.5, alpha=0.7, label='Crack Tip x = 0.50 mm')
    
    ax.set_title('(a) Longitudinal Mean Element Size Profile h_bar(x)', fontweight='bold')
    ax.set_xlabel('Longitudinal Coordinate x [mm]')
    ax.set_ylabel('Mean Element Size h_bar [um]')
    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 22.0)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', framealpha=0.9)
    
    # Panel (b): Transverse Corridor Profile & Half-Width
    ax = axes[1]
    stations = [0.25, 0.50, 0.60, 0.70, 0.80, 0.90, 0.98]
    w_1pct_mod = [0.894, 0.758, 0.849, 0.759, 0.608, 0.767, 0.377]
    w_2pct_mod = [0.000, 0.758, 0.835, 0.600, 0.380, 0.180, 0.120]
    w_lit_paper = [0.000, 0.320, 0.360, 0.280, 0.200, 0.160, 0.160] # Digitized from Fig 4
    
    ax.plot(stations, w_1pct_mod, 'b-s', linewidth=2.0, markersize=6, label='Project 1.0% Refined Width (h <= 5 um)')
    ax.plot(stations, w_2pct_mod, 'g-^', linewidth=2.0, markersize=6, label='Diagnostic 2.0% Refined Width (h <= 5 um)')
    ax.plot(stations, w_lit_paper, 'r--o', linewidth=2.0, markersize=6, label='Digitized Literature Corridor (Fig. 4)')
    ax.axvline(0.5, color='red', linestyle='-', linewidth=1.5, alpha=0.7, label='Crack Tip x = 0.50 mm')
    
    ax.set_title('(b) Transverse Refinement Corridor Width Delta y(x)', fontweight='bold')
    ax.set_xlabel('Longitudinal Coordinate x [mm]')
    ax.set_ylabel('Refined Corridor Width Delta y [mm]')
    ax.set_xlim(0.2, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', framealpha=0.9)
    
    fig_path_2_png = os.path.join(brain_dir, "fig_mode1_spatial_profiles_and_literature_overlay.png")
    fig_path_2_pdf = os.path.join(brain_dir, "fig_mode1_spatial_profiles_and_literature_overlay.pdf")
    plt.savefig(fig_path_2_png, bbox_inches='tight', dpi=300)
    plt.savefig(fig_path_2_pdf, bbox_inches='tight')
    plt.close()
    print("Saved Figure 2 to: %s and %s" % (fig_path_2_png, fig_path_2_pdf))

if __name__ == "__main__":
    main()
