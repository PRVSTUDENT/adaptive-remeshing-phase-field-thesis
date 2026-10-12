#!/usr/bin/env python3
"""
plot_mode1_method_b_adaptive_mesh.py
------------------------------------
Publication-quality visualization and comparative analysis of the genuine
Method B native Abaqus-adapted mesh (14,677 finite elements) for the
Pandey--Kumar Mode-I fracture benchmark.

Visualizations produced:
  1. Full-plate (1 x 1 mm) Method B adapted mesh with crack seam and BCs.
  2. Crack-tip magnified refinement corridor view (0.42 <= x,y <= 0.58 mm).
  3. Side-by-side / 2x2 comparison against the 2,906-element coarse pre-analysis mesh.
  4. Spatial element characteristic size map h = sqrt(A) and size distribution histograms.

Outputs:
  PNG (300 DPI) and vector PDF files in results/figures/mode1_method_b_mesh/
"""

import os
import sys
import math
import argparse
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# -----------------------------------------------------------------------------
# Input Deck Geometry Parsers
# -----------------------------------------------------------------------------

def parse_abaqus_mesh(inp_path):
    """
    Parses nodal coordinates and unique Layer-1 geometric finite elements
    from a multi-layer Abaqus input deck.
    
    Returns:
        nodes: dict {nid: (x, y)}
        quads: list [(eid, [n1, n2, n3, n4])]
        tris:  list [(eid, [n1, n2, n3])]
    """
    nodes = {}
    quads = []
    tris = []
    
    with open(inp_path, 'r') as f:
        sec = None
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                up = l.upper()
                if up == '*NODE' or up.startswith('*NODE,'):
                    sec = 'NODE'
                elif up.startswith('*ELEMENT, TYPE=U1') or up.startswith('*ELEMENT, TYPE=CPE4') and not quads:
                    sec = 'U1'
                elif up.startswith('*ELEMENT, TYPE=U3') or up.startswith('*ELEMENT, TYPE=CPE3') and not tris:
                    sec = 'U3'
                elif up.startswith('*STEP'):
                    break
                else:
                    sec = None
            else:
                if sec == 'NODE':
                    parts = l.split(',')
                    nid = int(parts[0].strip())
                    if nid not in (999999, 1000000):  # Skip virtual Reference Point nodes
                        nodes[nid] = (float(parts[1].strip()), float(parts[2].strip()))
                elif sec == 'U1':
                    parts = l.split(',')
                    eid = int(parts[0].strip())
                    conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                    quads.append((eid, conn))
                elif sec == 'U3':
                    parts = l.split(',')
                    eid = int(parts[0].strip())
                    conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                    tris.append((eid, conn))

    return nodes, quads, tris

def polygon_area(coords):
    """Computes polygon area using the shoelace formula."""
    n = len(coords)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += coords[i][0] * coords[j][1]
        area -= coords[j][0] * coords[i][1]
    return abs(area) / 2.0

def compute_mesh_statistics(nodes, quads, tris):
    """
    Computes element areas, characteristic lengths h = sqrt(A), centroids,
    and distances to the initial crack tip (0.5, 0.5) mm.
    """
    elements = []
    
    for eid, conn in quads:
        pts = [nodes[n] for n in conn]
        a = polygon_area(pts)
        h = math.sqrt(a)
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        d_tip = math.sqrt((cx - 0.5)**2 + (cy - 0.5)**2)
        elements.append({
            'eid': eid,
            'type': 'QUAD',
            'conn': conn,
            'pts': pts,
            'area': a,
            'h': h,
            'cx': cx,
            'cy': cy,
            'd_tip': d_tip
        })
        
    for eid, conn in tris:
        pts = [nodes[n] for n in conn]
        a = polygon_area(pts)
        h = math.sqrt(a)
        cx = sum(p[0] for p in pts) / 3.0
        cy = sum(p[1] for p in pts) / 3.0
        d_tip = math.sqrt((cx - 0.5)**2 + (cy - 0.5)**2)
        elements.append({
            'eid': eid,
            'type': 'TRI',
            'conn': conn,
            'pts': pts,
            'area': a,
            'h': h,
            'cx': cx,
            'cy': cy,
            'd_tip': d_tip
        })

    return elements

def find_crack_seam_nodes(nodes):
    """
    Identifies crack slit nodes along y = 0.5 mm for x <= 0.5 mm,
    separating duplicate flank pairs and singleton tip node.
    """
    seam = []
    for nid, (x, y) in nodes.items():
        if abs(y - 0.5) < 1e-5 and x <= 0.500001:
            seam.append((nid, x, y))
            
    by_x = {}
    for nid, x, y in seam:
        by_x.setdefault(round(x, 6), []).append(nid)
        
    pairs = {x: nids for x, nids in by_x.items() if len(nids) == 2}
    singletons = {x: nids for x, nids in by_x.items() if len(nids) == 1}
    tip_nodes = singletons.get(round(0.5, 6), [])
    
    return seam, pairs, singletons, tip_nodes

# -----------------------------------------------------------------------------
# Plotting Routines
# -----------------------------------------------------------------------------

def plot_full_mesh(elements, nodes, out_dir, prefix="fig_mode1_method_b_native_full_mesh", dpi=300):
    """
    Figure 1: Full-domain (1 x 1 mm) Method B adapted mesh with crack seam,
    boundary annotations, and zoom indicator box.
    """
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=dpi)
    
    verts = [el['pts'] for el in elements]
    pc = PolyCollection(verts, edgecolors='#333333', facecolors='#F4F6F9', linewidths=0.25, alpha=0.95)
    ax.add_collection(pc)
    
    # Highlight initial crack slit (y = 0.5, 0 <= x <= 0.5)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#D90429', linewidth=2.8, zorder=5, label=r'Initial Crack Slit ($a_0 = 0.5$ mm)')
    
    # Mark crack tip (0.5, 0.5)
    ax.scatter([0.5], [0.5], s=80, color='#D90429', edgecolors='black', linewidth=1.2, zorder=6, label=r'Crack Tip $(0.5, 0.5)$ mm')
    
    # Mark expected propagation ligament (y = 0.5, 0.5 < x <= 1.0)
    ax.plot([0.5, 1.0], [0.5, 0.5], color='#2B2D42', linestyle='--', linewidth=1.5, alpha=0.7, zorder=4, label='Fracture Propagation Ligament')
    
    # Zoom corridor box [0.42, 0.58] x [0.42, 0.58]
    rect = patches.Rectangle((0.42, 0.42), 0.16, 0.16, linewidth=1.8, edgecolor='#0077B6', facecolor='none', linestyle='-', zorder=7)
    ax.add_patch(rect)
    ax.text(0.422, 0.585, 'Refinement Corridor\n(Zoom Box: 0.16 x 0.16 mm)', color='#0077B6', fontsize=9.5, fontweight='bold', va='bottom', zorder=8)
    
    # Boundary condition annotations
    # Bottom roller (uy = 0)
    ax.text(0.5, -0.035, r'Bottom Roller: $u_y = 0$ (Pinned at origin: $u_x = u_y = 0$)', ha='center', va='top', fontsize=9.5, color='#1D3557', fontweight='semibold')
    # Top displacement (uy = u_prescribed)
    ax.text(0.5, 1.035, r'Top Surface: Prescribed Displacement $u_y(t)$', ha='center', va='bottom', fontsize=9.5, color='#1D3557', fontweight='semibold')
    
    # Physical / Numerical metadata box
    n_quads = sum(1 for el in elements if el['type'] == 'QUAD')
    n_tris = sum(1 for el in elements if el['type'] == 'TRI')
    n_nodes = len(nodes)
    h_min = min(el['h'] for el in elements) * 1000.0  # um
    h_max = max(el['h'] for el in elements) * 1000.0  # um
    
    info_text = (
        r"$\mathbf{Method\ B\ Native\ Adapted\ Mesh}$" + "\n"
        f"Domain: 1.0 x 1.0 mm square\n"
        f"Unique Elements: {len(elements):,} ({n_quads:,} quads, {n_tris:,} tris)\n"
        f"Co-located Records: 44,031 (3 UEL/UMAT layers)\n"
        f"Nodal Discretization: {n_nodes:,} nodes\n"
        f"Slit Seam: 62 duplicate node pairs + 1 tip node\n"
        f"Crack-Tip Element Size: $h_{{\\mathrm{{min}}}} = {h_min:.2f}\\ \\mu\\mathrm{{m}}$\n"
        f"Far-Field Element Size: $h_{{\\mathrm{{max}}}} = {h_max:.1f}\\ \\mu\\mathrm{{m}}$\n"
        r"Regularization Scale: $l_0 = 7.5\ \mu\mathrm{m}$ ($l_0 / h \approx 3.9$)"
    )
    props = dict(boxstyle='round,pad=0.6', facecolor='#FFFFFF', edgecolor='#A8DADC', alpha=0.92, linewidth=1.2)
    ax.text(0.03, 0.97, info_text, transform=ax.transAxes, fontsize=8.8, verticalalignment='top', bbox=props, zorder=10)
    
    ax.set_xlim(-0.06, 1.06)
    ax.set_ylim(-0.06, 1.06)
    ax.set_aspect('equal')
    ax.set_xlabel('Spatial Coordinate $x$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_ylabel('Spatial Coordinate $y$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_title('Pandey--Kumar Mode-I Benchmark: Genuine Method B Native Adapted Mesh\n'
                 r'(14,677 Elements, Native Abaqus CAE Pre-Peak Elastic Error Refinement)',
                 fontsize=11.5, fontweight='bold', pad=14)
    ax.grid(True, linestyle=':', alpha=0.35, color='gray')
    ax.legend(loc='lower left', fontsize=9, framealpha=0.92, edgecolor='#A8DADC')
    
    plt.tight_layout()
    png_path = os.path.join(out_dir, f"{prefix}.png")
    pdf_path = os.path.join(out_dir, f"{prefix}.pdf")
    plt.savefig(png_path, dpi=dpi)
    plt.savefig(pdf_path)
    plt.close()
    print(f"  [Figure 1] Generated: {png_path} and {pdf_path}")

def plot_crack_tip_zoom(elements, nodes, out_dir, prefix="fig_mode1_method_b_native_crack_tip_zoom", dpi=300):
    """
    Figure 2: Magnified crack-tip refinement corridor view (0.42 <= x,y <= 0.58 mm),
    showing element density transition from h_tip = 1.91 um to far-field.
    """
    fig, ax = plt.subplots(figsize=(9, 9), dpi=dpi)
    
    # Filter elements within zoom corridor
    zoom_box = [0.42, 0.58, 0.42, 0.58]
    zoom_elems = [el for el in elements if (
        zoom_box[0] <= el['cx'] <= zoom_box[1] and
        zoom_box[2] <= el['cy'] <= zoom_box[3]
    )]
    
    # Color elements by characteristic size h [um]
    h_vals = [el['h'] * 1000.0 for el in zoom_elems]
    verts = [el['pts'] for el in zoom_elems]
    
    cmap = plt.cm.viridis_r
    norm = plt.Normalize(vmin=1.5, vmax=15.0)
    face_colors = [cmap(norm(h)) for h in h_vals]
    
    pc = PolyCollection(verts, edgecolors='#1B263B', facecolors=face_colors, linewidths=0.45, alpha=0.92)
    ax.add_collection(pc)
    
    # Highlight initial crack slit (y = 0.5, 0.42 <= x <= 0.50)
    ax.plot([0.42, 0.50], [0.50, 0.50], color='#D90429', linewidth=3.5, zorder=5, label=r'Crack Slit ($y = 0.5$ mm)')
    
    # Mark crack tip (0.5, 0.5)
    ax.scatter([0.5], [0.5], s=140, color='#D90429', edgecolors='white', linewidth=1.8, zorder=6, label=r'Crack Tip $(0.5, 0.5)$ mm')
    
    # Flank labels
    ax.text(0.45, 0.508, r'Upper Flank ($y = 0.5^+$)', fontsize=9.5, fontweight='bold', color='#D90429', zorder=7)
    ax.text(0.45, 0.492, r'Lower Flank ($y = 0.5^-$)', fontsize=9.5, fontweight='bold', color='#D90429', va='top', zorder=7)
    
    # Propagation corridor ahead of crack tip
    ax.annotate('Expected Crack Propagation\nAlong Ligament ($y = 0.5$ mm)',
                xy=(0.54, 0.50), xytext=(0.525, 0.535),
                arrowprops=dict(facecolor='#1D3557', edgecolor='#1D3557', width=1.5, headwidth=7),
                fontsize=9.5, fontweight='bold', color='#1D3557', zorder=8)
    
    # Length scale visualization bar: l0 = 7.5 um (0.0075 mm), 2*l0 = 15 um (0.015 mm)
    bar_x = 0.435
    bar_y = 0.435
    l0_mm = 0.0075
    ax.plot([bar_x, bar_x + l0_mm], [bar_y, bar_y], color='#000000', linewidth=3.0, zorder=8)
    ax.text(bar_x + l0_mm / 2.0, bar_y - 0.002, r'$l_0 = 7.5\ \mu\mathrm{m}$', ha='center', va='top', fontsize=9, fontweight='bold', zorder=8)
    
    # Scale bar for 50 um = 0.05 mm
    scale_x = 0.52
    scale_y = 0.435
    ax.plot([scale_x, scale_x + 0.05], [scale_y, scale_y], color='#333333', linewidth=3.5, zorder=8)
    ax.text(scale_x + 0.025, scale_y - 0.002, r'$50\ \mu\mathrm{m}$ Scale Bar', ha='center', va='top', fontsize=9, fontweight='bold', zorder=8)
    
    # Colorbar for element characteristic size
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Element Characteristic Size $h = \sqrt{A}\ [\mu\mathrm{m}]$', fontsize=10, fontweight='semibold')
    
    ax.set_xlim(0.42, 0.58)
    ax.set_ylim(0.42, 0.58)
    ax.set_aspect('equal')
    ax.set_xlabel('Spatial Coordinate $x$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_ylabel('Spatial Coordinate $y$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_title('Crack-Tip Refinement Corridor & Element Sizing Resolution\n'
                 r'(Tip Resolution $h_{\mathrm{tip}} \approx 1.91\ \mu\mathrm{m}$, Phase-Field Regularization $l_0 = 7.5\ \mu\mathrm{m}$)',
                 fontsize=11.5, fontweight='bold', pad=14)
    ax.grid(True, linestyle=':', alpha=0.35, color='gray')
    ax.legend(loc='upper right', fontsize=9, framealpha=0.92, edgecolor='#A8DADC')
    
    plt.tight_layout()
    png_path = os.path.join(out_dir, f"{prefix}.png")
    pdf_path = os.path.join(out_dir, f"{prefix}.pdf")
    plt.savefig(png_path, dpi=dpi)
    plt.savefig(pdf_path)
    plt.close()
    print(f"  [Figure 2] Generated: {png_path} and {pdf_path}")

def plot_mesh_comparison(elems_coarse, nodes_coarse, elems_adapt, nodes_adapt, out_dir, prefix="fig_mode1_method_b_vs_coarse_comparison", dpi=300):
    """
    Figure 3: Side-by-side comparison:
      Left column:  Coarse pre-analysis mesh (2,906 FEs) - full plate & crack-tip zoom.
      Right column: Method B adapted mesh (14,677 FEs) - full plate & crack-tip zoom.
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 14), dpi=dpi)
    
    # Subplot (a): Coarse Full Domain
    ax = axes[0, 0]
    verts_c = [el['pts'] for el in elems_coarse]
    pc = PolyCollection(verts_c, edgecolors='#444444', facecolors='#EBF2FA', linewidths=0.3)
    ax.add_collection(pc)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#D90429', linewidth=2.2, zorder=5)
    ax.scatter([0.5], [0.5], s=60, color='#D90429', edgecolors='black', linewidth=1.0, zorder=6)
    rect = patches.Rectangle((0.42, 0.42), 0.16, 0.16, linewidth=1.5, edgecolor='#0077B6', facecolor='none', linestyle='--', zorder=7)
    ax.add_patch(rect)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_title('(a) Coarse Pre-Analysis Mesh: Full Domain\n'
                 f'2,906 Elements ({len(nodes_coarse):,} Nodes)', fontsize=11, fontweight='bold')
    ax.set_xlabel('$x$ [mm]', fontsize=10)
    ax.set_ylabel('$y$ [mm]', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.3)
    
    # Subplot (b): Adapted Full Domain
    ax = axes[0, 1]
    verts_a = [el['pts'] for el in elems_adapt]
    pc = PolyCollection(verts_a, edgecolors='#333333', facecolors='#F4F6F9', linewidths=0.2)
    ax.add_collection(pc)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#D90429', linewidth=2.2, zorder=5)
    ax.scatter([0.5], [0.5], s=60, color='#D90429', edgecolors='black', linewidth=1.0, zorder=6)
    rect = patches.Rectangle((0.42, 0.42), 0.16, 0.16, linewidth=1.5, edgecolor='#0077B6', facecolor='none', linestyle='--', zorder=7)
    ax.add_patch(rect)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_title('(b) Method B Native Adapted Mesh: Full Domain\n'
                 f'14,677 Elements ({len(nodes_adapt):,} Nodes)', fontsize=11, fontweight='bold')
    ax.set_xlabel('$x$ [mm]', fontsize=10)
    ax.set_ylabel('$y$ [mm]', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.3)
    
    # Subplot (c): Coarse Crack-Tip Zoom
    ax = axes[1, 0]
    zoom_box = [0.42, 0.58, 0.42, 0.58]
    z_coarse = [el for el in elems_coarse if (zoom_box[0] <= el['cx'] <= zoom_box[1] and zoom_box[2] <= el['cy'] <= zoom_box[3])]
    verts_zc = [el['pts'] for el in z_coarse]
    pc = PolyCollection(verts_zc, edgecolors='#1B263B', facecolors='#E0AAFF', linewidths=0.7, alpha=0.85)
    ax.add_collection(pc)
    ax.plot([0.42, 0.50], [0.50, 0.50], color='#D90429', linewidth=3.2, zorder=5)
    ax.scatter([0.5], [0.5], s=120, color='#D90429', edgecolors='white', linewidth=1.5, zorder=6)
    ax.set_xlim(0.42, 0.58)
    ax.set_ylim(0.42, 0.58)
    ax.set_aspect('equal')
    h_tip_c = sorted(z_coarse, key=lambda x: x['d_tip'])[0]['h'] * 1000.0
    ax.set_title(f'(c) Coarse Mesh: Crack-Tip Region\n'
                 f'Tip Element Size: $h_{{\\mathrm{{tip}}}} \\approx {h_tip_c:.1f}\\ \\mu\\mathrm{{m}}$ ($A \\approx {h_tip_c**2:.0f}\\ \\mu\\mathrm{{m}}^2$)',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('$x$ [mm]', fontsize=10)
    ax.set_ylabel('$y$ [mm]', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.3)
    
    # Subplot (d): Adapted Crack-Tip Zoom
    ax = axes[1, 1]
    z_adapt = [el for el in elems_adapt if (zoom_box[0] <= el['cx'] <= zoom_box[1] and zoom_box[2] <= el['cy'] <= zoom_box[3])]
    verts_za = [el['pts'] for el in z_adapt]
    pc = PolyCollection(verts_za, edgecolors='#1B263B', facecolors='#90E0EF', linewidths=0.45, alpha=0.85)
    ax.add_collection(pc)
    ax.plot([0.42, 0.50], [0.50, 0.50], color='#D90429', linewidth=3.2, zorder=5)
    ax.scatter([0.5], [0.5], s=120, color='#D90429', edgecolors='white', linewidth=1.5, zorder=6)
    ax.set_xlim(0.42, 0.58)
    ax.set_ylim(0.42, 0.58)
    ax.set_aspect('equal')
    h_tip_a = sorted(z_adapt, key=lambda x: x['d_tip'])[0]['h'] * 1000.0
    ax.set_title(f'(d) Method B Adapted: Crack-Tip Region\n'
                 f'Tip Element Size: $h_{{\\mathrm{{tip}}}} \\approx {h_tip_a:.2f}\\ \\mu\\mathrm{{m}}$ ($A \\approx {h_tip_a**2:.1f}\\ \\mu\\mathrm{{m}}^2$)',
                 fontsize=11, fontweight='bold')
    ax.set_xlabel('$x$ [mm]', fontsize=10)
    ax.set_ylabel('$y$ [mm]', fontsize=10)
    ax.grid(True, linestyle=':', alpha=0.3)
    
    # Super title
    fig.suptitle('Discretization Resolution Comparison: 2,906-Element Coarse Baseline vs. 14,677-Element Method B Adapted Mesh\n'
                 f'(Local Tip Resolution Enhancement: {h_tip_c/h_tip_a:.1f}x Finer Sizing, {(h_tip_c/h_tip_a)**2:.0f}x Area Density Contrast)',
                 fontsize=13, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    png_path = os.path.join(out_dir, f"{prefix}.png")
    pdf_path = os.path.join(out_dir, f"{prefix}.pdf")
    plt.savefig(png_path, dpi=dpi)
    plt.savefig(pdf_path)
    plt.close()
    print(f"  [Figure 3] Generated: {png_path} and {pdf_path}")

def plot_element_size_distributions(elems_coarse, elems_adapt, out_dir, prefix="fig_mode1_method_b_element_size_distribution", dpi=300):
    """
    Figure 4: Spatial element characteristic size map and statistical distribution:
      Left panel:  2D spatial colormap of h(x,y) across the full domain for Method B.
      Right panel: Statistical distribution / histogram comparing Coarse vs Adapted h.
    """
    fig, axes = plt.subplots(1, 2, figsize=(15, 6.8), dpi=dpi)
    
    # Subplot (a): 2D Spatial Map of h(x,y) for Method B Adapted Mesh
    ax = axes[0]
    h_vals_adapt = [el['h'] * 1000.0 for el in elems_adapt]  # um
    verts_a = [el['pts'] for el in elems_adapt]
    
    cmap = plt.cm.plasma_r
    norm = plt.Normalize(vmin=1.5, vmax=22.0)
    face_colors = [cmap(norm(h)) for h in h_vals_adapt]
    
    pc = PolyCollection(verts_a, edgecolors='#333333', facecolors=face_colors, linewidths=0.2, alpha=0.95)
    ax.add_collection(pc)
    
    # Slit and tip
    ax.plot([0.0, 0.5], [0.5, 0.5], color='white', linewidth=2.5, zorder=5)
    ax.scatter([0.5], [0.5], s=70, color='white', edgecolors='black', linewidth=1.2, zorder=6)
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_ylabel('$y$ [mm]', fontsize=11, fontweight='semibold')
    ax.set_title('(a) Method B Adapted Mesh: Spatial Element Size Map\n'
                 r'Gradient from Tip ($h \approx 1.91\ \mu\mathrm{m}$) to Periphery ($h \approx 22\ \mu\mathrm{m}$)',
                 fontsize=11.5, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.3)
    
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Characteristic Element Size $h = \sqrt{A}\ [\mu\mathrm{m}]$', fontsize=10.5, fontweight='semibold')
    
    # Subplot (b): Element Size Distribution (Histogram / Density)
    ax = axes[1]
    h_vals_coarse = [el['h'] * 1000.0 for el in elems_coarse]  # um
    
    bins = np.linspace(0.5, 26.0, 52)
    ax.hist(h_vals_coarse, bins=bins, density=True, alpha=0.55, color='#457B9D', edgecolor='#1D3557',
            label=f'Coarse Baseline ($N = 2,906$, Median $= {np.median(h_vals_coarse):.1f}\\ \\mu\\mathrm{{m}}$)')
    ax.hist(h_vals_adapt, bins=bins, density=True, alpha=0.65, color='#E63946', edgecolor='#9B2226',
            label=f'Method B Adapted ($N = 14,677$, Median $= {np.median(h_vals_adapt):.1f}\\ \\mu\\mathrm{{m}}$)')
    
    # Phase field regularization length scale markers
    ax.axvline(7.5, color='#2B2D42', linestyle='--', linewidth=1.8, label=r'Length Scale $l_0 = 7.5\ \mu\mathrm{m}$')
    ax.axvline(3.75, color='#2B2D42', linestyle=':', linewidth=1.8, label=r'Standard Rule $h = l_0 / 2 = 3.75\ \mu\mathrm{m}$')
    ax.axvline(1.91, color='#D90429', linestyle='-', linewidth=2.0, label=r'Method B Tip Resolution $h_{\mathrm{tip}} \approx 1.91\ \mu\mathrm{m}$')
    
    ax.set_xlabel(r'Element Characteristic Size $h = \sqrt{A}\ [\mu\mathrm{m}]$', fontsize=11, fontweight='semibold')
    ax.set_ylabel(r'Probability Density $[1 / \mu\mathrm{m}]$', fontsize=11, fontweight='semibold')
    ax.set_title('(b) Discretization Size Distribution & Regularization Thresholds\n'
                 r'Comparison of Element Sizing Against Length Scale $l_0 = 7.5\ \mu\mathrm{m}$',
                 fontsize=11.5, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.35)
    ax.legend(loc='upper right', fontsize=9.2, framealpha=0.92, edgecolor='#A8DADC')
    
    plt.tight_layout()
    png_path = os.path.join(out_dir, f"{prefix}.png")
    pdf_path = os.path.join(out_dir, f"{prefix}.pdf")
    plt.savefig(png_path, dpi=dpi)
    plt.savefig(pdf_path)
    plt.close()
    print(f"  [Figure 4] Generated: {png_path} and {pdf_path}")

# -----------------------------------------------------------------------------
# Main Execution Entrypoint
# -----------------------------------------------------------------------------

def resolve_input_path(path_arg):
    """Resolves an input path from CLI argument or relative to workspace/script."""
    if os.path.isabs(path_arg) and os.path.exists(path_arg):
        return path_arg
    # Check current working directory
    cand1 = os.path.abspath(path_arg)
    if os.path.exists(cand1):
        return cand1
    # Check standard repo root locations
    repo_dirs = [
        r"D:\Master thesis\Adaptive remeshing",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    ]
    for r in repo_dirs:
        cand = os.path.join(r, path_arg)
        if os.path.exists(cand):
            return cand
    raise FileNotFoundError(f"Cannot resolve input deck: {path_arg}")

def main():
    parser = argparse.ArgumentParser(description="Plot Method B Native Adaptive Mesh for Pandey-Kumar Mode-I")
    parser.add_argument('--adapted-inp', default=r"models/pandey_kumar_mode1/38_method_b_native_final_14k/M1_MB_NATIVE_FINAL_1S.inp",
                        help="Path to Method B adapted input deck")
    parser.add_argument('--coarse-inp', default=r"models/pandey_kumar_mode1/method_b_preflight_decks/M1-MB-1S.inp",
                        help="Path to coarse pre-analysis input deck")
    parser.add_argument('--outdir', default=r"results/figures/mode1_method_b_mesh",
                        help="Output directory for generated figures")
    parser.add_argument('--dpi', type=int, default=300, help="DPI for raster output")
    args = parser.parse_args()

    adapted_path = resolve_input_path(args.adapted_inp)
    coarse_path = resolve_input_path(args.coarse_inp)
    out_dir = os.path.abspath(args.outdir)
    
    os.makedirs(out_dir, exist_ok=True)
    
    print("=" * 70)
    print("Pandey--Kumar Mode-I Method B Native Adaptive Mesh Visualization")
    print("=" * 70)
    print(f"Adapted Input Deck: {adapted_path}")
    print(f"Coarse Input Deck:  {coarse_path}")
    print(f"Output Directory:   {out_dir}")
    print("-" * 70)
    
    print("1. Parsing Method B Native adapted mesh...")
    nodes_adapt, quads_adapt, tris_adapt = parse_abaqus_mesh(adapted_path)
    elems_adapt = compute_mesh_statistics(nodes_adapt, quads_adapt, tris_adapt)
    seam_a, pairs_a, single_a, tip_a = find_crack_seam_nodes(nodes_adapt)
    print(f"   Nodes: {len(nodes_adapt):,}, Elements: {len(elems_adapt):,} ({len(quads_adapt):,} quads, {len(tris_adapt):,} tris)")
    print(f"   Crack seam: {len(seam_a)} nodes ({len(pairs_a)} duplicate pairs, tip node: {tip_a})")
    
    print("\n2. Parsing Coarse pre-analysis baseline mesh...")
    nodes_coarse, quads_coarse, tris_coarse = parse_abaqus_mesh(coarse_path)
    elems_coarse = compute_mesh_statistics(nodes_coarse, quads_coarse, tris_coarse)
    seam_c, pairs_c, single_c, tip_c = find_crack_seam_nodes(nodes_coarse)
    print(f"   Nodes: {len(nodes_coarse):,}, Elements: {len(elems_coarse):,} ({len(quads_coarse):,} quads, {len(tris_coarse):,} tris)")
    print(f"   Crack seam: {len(seam_c)} nodes ({len(pairs_c)} duplicate pairs, tip node: {tip_c})")
    
    print("\n3. Generating Figure 1: Full-plate Method B adaptive mesh...")
    plot_full_mesh(elems_adapt, nodes_adapt, out_dir, dpi=args.dpi)
    
    print("\n4. Generating Figure 2: Zoomed crack-tip refinement corridor...")
    plot_crack_tip_zoom(elems_adapt, nodes_adapt, out_dir, dpi=args.dpi)
    
    print("\n5. Generating Figure 3: Side-by-side 2x2 mesh comparison...")
    plot_mesh_comparison(elems_coarse, nodes_coarse, elems_adapt, nodes_adapt, out_dir, dpi=args.dpi)
    
    print("\n6. Generating Figure 4: Spatial element-size map and distribution...")
    plot_element_size_distributions(elems_coarse, elems_adapt, out_dir, dpi=args.dpi)
    
    print("=" * 70)
    print("All figures successfully generated and saved.")
    print("=" * 70)
    sys.stdout.flush()

if __name__ == '__main__':
    main()
