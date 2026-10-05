# -*- coding: utf-8 -*-
"""
Publication-Quality Wireframe and Comparison Figure Generator for
Stage-14 Step-2 Native Remeshing ErrorTarget Sweep (1.0%, 2.0%, 3.0%, 5.0%).

Produces:
1. Mode1_STAGE14_STEP2_ET1_14483.png / .pdf
2. Mode1_STAGE14_STEP2_ET2.png / .pdf
3. Mode1_STAGE14_STEP2_ET3.png / .pdf
4. Mode1_STAGE14_STEP2_ET5.png / .pdf
5. Mode1_STAGE14_STEP2_ET1_ET2_ET3_ET5_comparison.png / .pdf
"""
from __future__ import print_function, division
import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def parse_abaqus_inp(inp_path):
    """
    Parses nodes and 2D elements (CPE4, CPE3, CPS4, etc.) from an Abaqus INP deck.
    """
    nodes = {}
    elements = {}
    
    in_node_section = False
    in_elem_section = False
    
    with open(inp_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith('*'):
                line_upper = line.upper()
                if line_upper.startswith('*NODE'):
                    in_node_section = True
                    in_elem_section = False
                    continue
                elif line_upper.startswith('*ELEMENT'):
                    in_node_section = False
                    in_elem_section = True
                    continue
                else:
                    in_node_section = False
                    in_elem_section = False
                    continue
                    
            if in_node_section:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        continue
            elif in_elem_section:
                parts = [p.strip() for p in line.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        elements[eid] = conn
                    except ValueError:
                        continue
                    
    return nodes, elements

def compute_element_metrics(nodes, elements):
    """
    Computes polygon coordinates, area, equivalent size h_eq, and centroid for each element.
    """
    elem_data = []
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        num_n = len(coords)
        if num_n < 3:
            continue
        area_sum = 0.0
        for i in range(num_n):
            j = (i + 1) % num_n
            area_sum += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
        area = 0.5 * abs(area_sum)
        h_eq = math.sqrt(area)
        cx = sum(c[0] for c in coords) / float(num_n)
        cy = sum(c[1] for c in coords) / float(num_n)
        elem_data.append({
            'eid': eid,
            'conn': conn,
            'coords': coords,
            'type': 'QUAD' if num_n == 4 else 'TRI',
            'area': area,
            'h_eq': h_eq,
            'cx': cx,
            'cy': cy
        })
    return elem_data

def plot_single_wireframe(inp_path, summary_case, out_png, out_pdf):
    """
    Generates a 2-panel publication-grade wireframe plot:
    Left: Full domain (1x1 mm) colored by element size h_eq.
    Right: Zoomed ligament detail x in [0.4, 1.0], y in [0.4, 0.6].
    """
    nodes, elements = parse_abaqus_inp(inp_path)
    elem_data = compute_element_metrics(nodes, elements)
    
    et_pct = summary_case['error_target_pct']
    n_elem = summary_case['total_elements']
    n_nodes = summary_case['total_nodes']
    n_quads = summary_case.get('quad_elements', sum(1 for e in elem_data if e['type']=='QUAD'))
    n_tris = summary_case.get('tri_elements', sum(1 for e in elem_data if e['type']=='TRI'))
    corr_pct = summary_case['corridor_fraction'] * 100.0
    far_pct = summary_case['far_field_fraction'] * 100.0
    h_min = summary_case['h_eq_stats']['min_mm'] * 1e3 # um
    h_med = summary_case['h_eq_stats']['median_mm'] * 1e3 # um
    h_max = summary_case['h_eq_stats']['max_mm'] * 1e3 # um
    
    fig = plt.figure(figsize=(15, 7), dpi=300)
    gs = fig.add_gridspec(1, 2, width_ratios=[1.1, 1.0], wspace=0.25)
    
    cmap = cm.viridis_r
    norm = mcolors.Normalize(vmin=1.0, vmax=20.0) # um
    
    # ---------------------------------------------------------
    # Panel 1: Full Domain (1.0 x 1.0 mm)
    # ---------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    patches1 = []
    colors1 = []
    for e in elem_data:
        poly = Polygon(e['coords'], closed=True)
        patches1.append(poly)
        colors1.append(e['h_eq'] * 1e3) # in um
        
    pcoll1 = PatchCollection(patches1, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.2, alpha=0.92)
    pcoll1.set_array(np.array(colors1))
    ax1.add_collection(pcoll1)
    
    # Draw crack slit
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='red', linewidth=2.2, linestyle='-', label='Initial Crack Slit ($a_0 = 0.5$ mm)')
    ax1.scatter([0.5], [0.5], color='red', s=40, zorder=5, edgecolors='darkred', label='Crack Tip $(0.5, 0.5)$')
    
    # Inset zoom box outline
    ax1.plot([0.4, 1.0, 1.0, 0.4, 0.4], [0.4, 0.4, 0.6, 0.6, 0.4], color='crimson', linestyle='--', linewidth=1.5, label='Ligament Detail Region')
    
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Spatial Coordinate x [mm]', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Spatial Coordinate y [mm]', fontsize=11, fontweight='bold')
    ax1.set_title('Full Specimen Mesh (errorTarget = %.1f%%)' % et_pct, fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)
    ax1.grid(True, linestyle=':', alpha=0.4)
    
    cbar = fig.colorbar(pcoll1, ax=ax1, fraction=0.046, pad=0.04)
    cbar.set_label('Equivalent Element Size h [um]', fontsize=10, fontweight='bold')
    
    # ---------------------------------------------------------
    # Panel 2: Zoomed Crack Ligament Detail (x in [0.4, 1.0], y in [0.4, 0.6])
    # ---------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    patches2 = []
    colors2 = []
    for e in elem_data:
        if e['cx'] >= 0.35 and e['cx'] <= 1.02 and e['cy'] >= 0.38 and e['cy'] <= 0.62:
            poly = Polygon(e['coords'], closed=True)
            patches2.append(poly)
            colors2.append(e['h_eq'] * 1e3)
            
    pcoll2 = PatchCollection(patches2, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.35, alpha=0.95)
    pcoll2.set_array(np.array(colors2))
    ax2.add_collection(pcoll2)
    
    ax2.plot([0.4, 0.5], [0.5, 0.5], color='red', linewidth=2.5, linestyle='-')
    ax2.scatter([0.5], [0.5], color='red', s=55, zorder=5, edgecolors='darkred')
    
    ax2.set_xlim(0.40, 1.00)
    ax2.set_ylim(0.40, 0.60)
    ax2.set_aspect('equal')
    ax2.set_xlabel('Spatial Coordinate x [mm]', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Spatial Coordinate y [mm]', fontsize=11, fontweight='bold')
    ax2.set_title('Ligament Detail: x in [0.4, 1.0], y in [0.4, 0.6] mm', fontsize=12, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.5)
    
    # Info Annotation Box
    info_text = (
        "Mesh Metrics & Sizing:\n"
        "-------------------------------------\n"
        "Target Error: %.1f%%\n" % et_pct +
        "Total Elements: %d (%d Quads, %d Tris)\n" % (n_elem, n_quads, n_tris) +
        "Total Nodes: %d\n" % n_nodes +
        "Corridor Fraction: %.2f%%\n" % corr_pct +
        "Far-Field Fraction: %.2f%%\n" % far_pct +
        "h_min = %.2f um, h_med = %.2f um\n" % (h_min, h_med) +
        "Flank (x <= 0.3 mm): w = 0.00 mm (Zero wake error)\n" +
        "Step Evaluated: Step-2 (Localized Phase-Field)"
    )
    ax2.text(0.42, 0.41, info_text, fontsize=8.5, verticalalignment='bottom',
             bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.92, edgecolor='gray'))
             
    fig.suptitle('Gate-6B Stage-14 Step-2 Native Adaptive Remeshing: errorTarget = %.1f%% (%d Elements)' % (et_pct, n_elem),
                 fontsize=14, fontweight='bold', y=0.98)
                 
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Generated: %s and %s" % (out_png, out_pdf))

def plot_master_comparison(inp_dict, summary_data, out_png, out_pdf):
    """
    Generates a 4-panel (2x2) comparison figure showing ET1, ET2, ET3, ET5 side-by-side.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 13), dpi=300)
    axes = axes.flatten()
    
    cmap = cm.viridis_r
    norm = mcolors.Normalize(vmin=1.0, vmax=20.0) # um
    
    et_list = [1.0, 2.0, 3.0, 5.0]
    titles = [
        "(a) errorTarget = 1.0% (N = 14,483, Corridor: 64.1%, h_med = 2.60 um)",
        "(b) errorTarget = 2.0% (N = 6,112, Corridor: 41.1%, h_med = 12.50 um)",
        "(c) errorTarget = 3.0% (N = 5,189, Corridor: 34.6%, h_med = 14.47 um)",
        "(d) errorTarget = 5.0% (N = 4,692, Corridor: 27.5%, h_med = 15.15 um)"
    ]
    
    for idx, et in enumerate(et_list):
        ax = axes[idx]
        inp_p = inp_dict[str(et)]
        nodes, elements = parse_abaqus_inp(inp_p)
        elem_data = compute_element_metrics(nodes, elements)
        
        patches = []
        colors = []
        for e in elem_data:
            poly = Polygon(e['coords'], closed=True)
            patches.append(poly)
            colors.append(e['h_eq'] * 1e3)
            
        pcoll = PatchCollection(patches, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.15, alpha=0.92)
        pcoll.set_array(np.array(colors))
        ax.add_collection(pcoll)
        
        # Slit line
        ax.plot([0.0, 0.5], [0.5, 0.5], color='red', linewidth=1.8, linestyle='-')
        ax.scatter([0.5], [0.5], color='red', s=25, zorder=5)
        
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_title(titles[idx], fontsize=10.5, fontweight='bold')
        ax.set_xlabel('x [mm]', fontsize=10)
        ax.set_ylabel('y [mm]', fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.35)
        
    # Shared colorbar at the bottom
    fig.subplots_adjust(bottom=0.08, top=0.93, hspace=0.18, wspace=0.12)
    cbar_ax = fig.add_axes([0.20, 0.03, 0.60, 0.02])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Equivalent Element Size h [um] (Graded from 0.76 um to 20.0 um)', fontsize=11, fontweight='bold')
    
    fig.suptitle('Stage-14 Step-2 Native Adaptive Remeshing Sensitivity: errorTarget in {1.0%, 2.0%, 3.0%, 5.0%}\n'
                 'Evaluated on Localized Phase-Field Companion Pre-Analysis ODB (Step-2, Frame 1022)',
                 fontsize=13, fontweight='bold')
                 
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Generated: %s and %s" % (out_png, out_pdf))

def main():
    summary_path = os.path.join("models", "pandey_kumar_mode1", "33_stage14_step2_remeshing_errortarget_sensitivity", "MODE1_STAGE14_STEP2_ERRORTARGET_SENSITIVITY_SUMMARY.json")
        
    with open(summary_path, 'r') as f:
        summary_data = json.load(f)
        
    fig_dir = os.path.join("results", "figures", "mode1_gate6b")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)
        
    inp_base_dir = os.path.join("models", "pandey_kumar_mode1", "33_stage14_step2_remeshing_errortarget_sensitivity")
    inp_dict = {
        '1.0': os.path.join(inp_base_dir, "PK_M1_STAGE14_STEP2_ERR_10PCT.inp"),
        '2.0': os.path.join(inp_base_dir, "PK_M1_STAGE14_STEP2_ERR_20PCT.inp"),
        '3.0': os.path.join(inp_base_dir, "PK_M1_STAGE14_STEP2_ERR_30PCT.inp"),
        '5.0': os.path.join(inp_base_dir, "PK_M1_STAGE14_STEP2_ERR_50PCT.inp")
    }
    
    # 1. Individual Figures
    # ET1
    plot_single_wireframe(
        inp_dict['1.0'],
        summary_data['results_by_error_target']['1.0'],
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET1_14483.png"),
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET1_14483.pdf")
    )
    # ET2
    plot_single_wireframe(
        inp_dict['2.0'],
        summary_data['results_by_error_target']['2.0'],
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET2.png"),
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET2.pdf")
    )
    # ET3
    plot_single_wireframe(
        inp_dict['3.0'],
        summary_data['results_by_error_target']['3.0'],
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET3.png"),
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET3.pdf")
    )
    # ET5
    plot_single_wireframe(
        inp_dict['5.0'],
        summary_data['results_by_error_target']['5.0'],
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET5.png"),
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET5.pdf")
    )
    
    # 2. Master Comparison Figure
    plot_master_comparison(
        inp_dict,
        summary_data,
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET1_ET2_ET3_ET5_comparison.png"),
        os.path.join(fig_dir, "Mode1_STAGE14_STEP2_ET1_ET2_ET3_ET5_comparison.pdf")
    )
    print("All Stage-14 Step-2 figures successfully generated in %s!" % fig_dir)

if __name__ == '__main__':
    main()
