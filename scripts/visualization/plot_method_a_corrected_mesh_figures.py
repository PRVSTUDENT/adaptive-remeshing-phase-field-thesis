#!/usr/bin/env python3
"""
Generate publication-quality figures for the Corrected Localized Method A mesh:
1. Full-plate adapted mesh (1.0 x 1.0 mm) showing notch, hole, and both refined supports.
2. Zoomed mesh around notch tip, ligament, circular hole, and right flank.
3. Authentic precritical indicator support overlay (damage + history + 3*l0 buffer boundaries).
4. Side-by-side comparison: Old 23k baseline (with right-side omission) vs Corrected 54k mesh.

Uses authentic Abaqus node coordinates and element connectivity.
"""

import os
import sys
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Circle
from matplotlib.collections import PatchCollection, LineCollection
from shapely.geometry import Polygon as ShpPolygon

def load_inp_mesh(inp_path):
    nodes = {}
    elems = []
    in_nodes = in_elems = False
    with open(inp_path) as f:
        for line in f:
            l = line.strip()
            if l.upper().startswith('*NODE'):
                in_nodes, in_elems = True, False
                continue
            elif l.upper().startswith('*ELEMENT'):
                in_nodes, in_elems = False, True
                continue
            elif l.startswith('*'):
                in_nodes = in_elems = False
                continue
            if in_nodes:
                p = [x.strip() for x in l.split(',') if x.strip()]
                if len(p) >= 3:
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elems:
                try:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    if len(p) >= 4:
                        elems.append(p[1:])
                except ValueError:
                    pass
    return nodes, elems

def plot_all_figures():
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 14,
        'font.family': 'sans-serif'
    })

    corr_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_CORR_PHYS.inp"
    base_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_BASELINE_PHYS.inp"
    supports_json = "results/validation/faithful_indicator_supports.json"
    damage_csv = "results/validation/f1642_pilot_localized_damage.csv"

    out_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)

    print("Loading corrected mesh:", corr_inp)
    corr_nodes, corr_elems = load_inp_mesh(corr_inp)
    print("Loading baseline mesh:", base_inp)
    base_nodes, base_elems = load_inp_mesh(base_inp)

    with open(supports_json) as f:
        sup_data = json.load(f)
    left_verts = sup_data["supports"]["notch_ligament_fpz"]["vertices"]
    right_verts = sup_data["supports"]["hole_right_flank_fpz"]["vertices"]

    # -------------------------------------------------------------
    # Figure 1: Full-Plate Corrected Mesh
    # -------------------------------------------------------------
    print("Generating Figure 1: Full-Plate Corrected Mesh...")
    fig, ax = plt.subplots(figsize=(8, 8))
    patches = []
    for conn in corr_elems:
        pts = [corr_nodes[n] for n in conn if n in corr_nodes]
        if len(pts) >= 3:
            patches.append(MplPolygon(pts, closed=True))
    p_coll = PatchCollection(patches, facecolor='#f8f9fa', edgecolor='#212529', linewidths=0.2, alpha=0.9)
    ax.add_collection(p_coll)

    # Highlight notch and hole
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#00d2d3', lw=3.0, label='Starter Notch ($a_0 = 0.5$ mm)')
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.0, ls='--', label='Off-Axis Hole ($R = 0.10$ mm)')
    ax.add_patch(hole)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title('Corrected Damage-Informed Method A Adapted Mesh ($N = 54,563$)\nFull Domain Support: Notch-Ligament & Opposite Hole Flank', pad=12)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_full_mesh.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_full_mesh.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 2: Zoomed Corrected Mesh (Notch Tip, Ligament, Hole, Flanks)
    # -------------------------------------------------------------
    print("Generating Figure 2: Zoomed Corrected Mesh...")
    fig, ax = plt.subplots(figsize=(8, 8))
    zoom_patches = []
    for conn in corr_elems:
        pts = [corr_nodes[n] for n in conn if n in corr_nodes]
        if len(pts) >= 3:
            xc = np.mean([p[0] for p in pts])
            yc = np.mean([p[1] for p in pts])
            if 0.44 <= xc <= 0.86 and 0.44 <= yc <= 0.82:
                zoom_patches.append(MplPolygon(pts, closed=True))

    p_zoom = PatchCollection(zoom_patches, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.3, alpha=0.95)
    ax.add_collection(p_zoom)

    # Draw notch root and hole
    ax.plot([0.45, 0.50], [0.5, 0.5], color='#00d2d3', lw=3.5, label='Notch Tip ($x=0.5$ mm)')
    hole_zoom = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.2, ls='--', label='Off-Axis Hole ($R=0.10$ mm)')
    ax.add_patch(hole_zoom)

    # Outline support boundaries
    poly_left_patch = MplPolygon(left_verts, closed=True, edgecolor='#10ac84', facecolor='none', lw=2.0, ls='-', label='Notch-Ligament Support ($3\\ell_0$ buffer)')
    poly_right_patch = MplPolygon(right_verts, closed=True, edgecolor='#5f27cd', facecolor='none', lw=2.0, ls='-', label='Opposite Flank Support ($3\\ell_0$ buffer)')
    ax.add_patch(poly_left_patch)
    ax.add_patch(poly_right_patch)

    ax.set_xlim(0.46, 0.84)
    ax.set_ylim(0.46, 0.78)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title(r'Zoomed Fracture Domain & Opposite Flank Refinement' + '\n' + r'Longest Edge $h_{\max} \leq 1.5\,\mu\mathrm{m}$ in Both Process Zones', pad=12)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_zoom_mesh.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_zoom_mesh.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 3: Authentic Indicator Support Overlay
    # -------------------------------------------------------------
    print("Generating Figure 3: Indicator Support Overlay...")
    fig, ax = plt.subplots(figsize=(9, 8))

    # Load authentic precritical damage field
    d_pts = []
    d_vals = []
    with open(damage_csv) as f:
        for r in csv.DictReader(f):
            eid = int(r['phys_elem_id'])
            d = float(r['damage'])
            if d >= 0.05:
                # find centroid from base mesh
                if eid <= len(base_elems):
                    conn = base_elems[eid - 1]
                    pts = [base_nodes[n] for n in conn if n in base_nodes]
                    if pts:
                        d_pts.append((np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])))
                        d_vals.append(d)

    d_pts = np.array(d_pts)
    d_vals = np.array(d_vals)

    sc = ax.scatter(d_pts[:, 0], d_pts[:, 1], c=d_vals, cmap='plasma', s=12, alpha=0.85, zorder=3, label='Precritical Damage ($d \\geq 0.05$)')
    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Authentic Precritical Damage $d$ [-]')

    # Add support outlines
    ax.plot([v[0] for v in left_verts], [v[1] for v in left_verts], color='#10ac84', lw=2.5, zorder=4, label='Left FPZ Support ($3\\ell_0$ buffer)')
    ax.plot([v[0] for v in right_verts], [v[1] for v in right_verts], color='#5f27cd', lw=2.5, zorder=4, label='Right Flank Support ($3\\ell_0$ buffer)')

    # Add notch and hole
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#00d2d3', lw=3.0, zorder=5, label='Notch ($a_0=0.5$ mm)')
    hole_ov = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.0, ls='--', zorder=4, label='Hole ($R=0.10$ mm)')
    ax.add_patch(hole_ov)

    ax.set_xlim(0.40, 0.88)
    ax.set_ylim(0.42, 0.80)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title('Authentic Precritical Indicator Support & $3\\ell_0$ Buffers\nFull Domain Evaluation: Primary Ligament and Secondary Flank', pad=12)
    ax.legend(loc='upper right', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_support_overlay.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_method_a_corrected_support_overlay.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 4: Side-by-Side Old 23k Baseline vs Corrected 54k Mesh
    # -------------------------------------------------------------
    print("Generating Figure 4: Side-by-Side Comparison...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5))

    # Panel (a): Old Baseline (23k)
    base_patches = []
    for conn in base_elems:
        pts = [base_nodes[n] for n in conn if n in base_nodes]
        if len(pts) >= 3:
            xc = np.mean([p[0] for p in pts])
            yc = np.mean([p[1] for p in pts])
            if 0.44 <= xc <= 0.86 and 0.44 <= yc <= 0.82:
                base_patches.append(MplPolygon(pts, closed=True))
    p_b = PatchCollection(base_patches, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.3, alpha=0.95)
    ax1.add_collection(p_b)
    ax1.plot([0.45, 0.50], [0.5, 0.5], color='#00d2d3', lw=3.0)
    h1 = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.0, ls='--')
    ax1.add_patch(h1)
    # Annotate defect: right flank left unrefined
    ax1.annotate('DEFECT: Unrefined Right Flank\n(Excluded by Coordinate Filter)\n$h \\approx 10-20\\,\\mu$m',
                 xy=(0.76, 0.65), xytext=(0.72, 0.74),
                 arrowprops=dict(facecolor='#d63031', edgecolor='#d63031', shrink=0.08, width=1.5, headwidth=6),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#ffeaa7', edgecolor='#d63031', lw=1.5),
                 fontsize=9, fontweight='bold', color='#d63031')
    ax1.set_xlim(0.46, 0.84)
    ax1.set_ylim(0.46, 0.78)
    ax1.set_aspect('equal')
    ax1.set_xlabel('$x$ [mm]')
    ax1.set_ylabel('$y$ [mm]')
    ax1.set_title('(a) Baseline Candidate ($N = 23,664$)\nDefect: Hardcoded Filter Excluded Opposite Flank', pad=10)
    ax1.grid(True, linestyle=':', alpha=0.4)

    # Panel (b): Corrected Candidate (54k)
    corr_zoom_patches = []
    for conn in corr_elems:
        pts = [corr_nodes[n] for n in conn if n in corr_nodes]
        if len(pts) >= 3:
            xc = np.mean([p[0] for p in pts])
            yc = np.mean([p[1] for p in pts])
            if 0.44 <= xc <= 0.86 and 0.44 <= yc <= 0.82:
                corr_zoom_patches.append(MplPolygon(pts, closed=True))
    p_c = PatchCollection(corr_zoom_patches, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.3, alpha=0.95)
    ax2.add_collection(p_c)
    ax2.plot([0.45, 0.50], [0.5, 0.5], color='#00d2d3', lw=3.0)
    h2 = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.0, ls='--')
    ax2.add_patch(h2)
    # Annotate correction: right flank refined
    ax2.annotate('CORRECTED: Refined Right Flank\n(Dual Indicator Supports)\n$h_{\\max} \\leq 1.5\\,\\mu$m',
                 xy=(0.76, 0.65), xytext=(0.72, 0.74),
                 arrowprops=dict(facecolor='#00b894', edgecolor='#00b894', shrink=0.08, width=1.5, headwidth=6),
                 bbox=dict(boxstyle='round,pad=0.4', facecolor='#e8f8f5', edgecolor='#00b894', lw=1.5),
                 fontsize=9, fontweight='bold', color='#00b894')
    ax2.set_xlim(0.46, 0.84)
    ax2.set_ylim(0.46, 0.78)
    ax2.set_aspect('equal')
    ax2.set_xlabel('$x$ [mm]')
    ax2.set_ylabel('$y$ [mm]')
    ax2.set_title('(b) Corrected Candidate ($N = 54,563$)\nFull Domain Support: Notch-Ligament & Opposite Flank', pad=10)
    ax2.grid(True, linestyle=':', alpha=0.4)

    plt.tight_layout()
    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_method_a_baseline_vs_corrected_comparison.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_method_a_baseline_vs_corrected_comparison.pdf'), bbox_inches='tight')
    plt.close(fig)

    print("All 4 publication figures generated successfully!")

if __name__ == '__main__':
    plot_all_figures()
