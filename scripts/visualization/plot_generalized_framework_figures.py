#!/usr/bin/env python3
"""
Generate publication-quality figures for the Generalized 2D Field-Driven Adaptive Remeshing Framework:
- FIGURE A: Full 2D adapted mesh (1.0 x 1.0 mm) with actual element edges, notch, hole, and element size field.
- FIGURE B: Zoomed adapted mesh around notch, dual indicator supports, and hole revealing mesh grading.
- FIGURE C: Authentic precritical indicator field (d >= 0.05) vs automatically selected 3*l0 support boundary.
- FIGURE D: Three-way comparison: Original native Method A (46k) vs Baseline localized (23k) vs Generalized 2D adapted mesh (54k).
- FIGURE E: Generality test suite: Case 1 (Off-axis hole), Case 2 (Shifted hole [SYNTHETIC]), Case 3 (No hole [SYNTHETIC]).

All figures rendered from actual Abaqus finite-element connectivity.
"""

import os
import sys
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Circle
from matplotlib.collections import PatchCollection

def parse_inp(inp_path):
    nodes = {}
    elems = []
    in_nodes = in_elems = False
    with open(inp_path) as f:
        for line in f:
            l = line.strip()
            if l.upper().startswith('*NODE'): in_nodes, in_elems = True, False; continue
            elif l.upper().startswith('*ELEMENT'): in_nodes, in_elems = False, True; continue
            elif l.startswith('*'): in_nodes = in_elems = False; continue
            if in_nodes:
                p = [x.strip() for x in l.split(',') if x.strip()]
                if len(p) >= 3: nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elems:
                try:
                    p = [int(x.strip()) for x in l.split(',') if x.strip()]
                    if len(p) >= 4: elems.append(p[1:])
                except ValueError: pass
    return nodes, elems

def max_edge(pts):
    dists = []
    n = len(pts)
    for i in range(n):
        dists.append(np.hypot(pts[i][0] - pts[(i+1)%n][0], pts[i][1] - pts[(i+1)%n][1]))
    return max(dists)

def run_plotting():
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

    out_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in out_dirs: os.makedirs(d, exist_ok=True)

    gen_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_GEN_PHYS.inp"
    base_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_BASELINE_PHYS.inp"
    orig_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp"
    c2_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/TEST_CASE2_SHIFTED_HOLE_PHYS.inp"
    c3_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/TEST_CASE3_NO_HOLE_PHYS.inp"
    summary_json = "results/validation/framework_generality_summary.json"
    damage_csv = "results/validation/f1642_pilot_localized_damage.csv"

    print("Loading meshes...")
    n_gen, e_gen = parse_inp(gen_inp)
    n_base, e_base = parse_inp(base_inp)
    n_orig, e_orig = parse_inp(orig_inp)
    n_c2, e_c2 = parse_inp(c2_inp)
    n_c3, e_c3 = parse_inp(c3_inp)

    with open(summary_json) as f:
        gen_data = json.load(f)
    case1_supports = gen_data["case_1_authentic_off_axis_hole"]["supports"]
    left_verts = case1_supports[0]["vertices"]
    right_verts = case1_supports[1]["vertices"]

    # -------------------------------------------------------------
    # FIGURE A: FULL 2D ADAPTED MESH WITH ELEMENT SIZE FIELD
    # -------------------------------------------------------------
    print("Plotting FIGURE A: Full 2D adapted mesh...")
    fig, ax = plt.subplots(figsize=(8.5, 8))
    patches = []
    sizes = []
    for conn in e_gen:
        pts = [n_gen[n] for n in conn if n in n_gen]
        if len(pts) >= 3:
            patches.append(MplPoly(pts, closed=True))
            sizes.append(max_edge(pts) * 1000.0) # um

    sizes = np.array(sizes)
    p_coll = PatchCollection(patches, cmap='viridis_r', edgecolor='#2f3542', linewidths=0.15, alpha=0.92)
    p_coll.set_array(sizes)
    p_coll.set_clim(1.0, 20.0)
    ax.add_collection(p_coll)

    # Starter notch and hole
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#ff4757', lw=3.0, label='Notch ($a_0 = 0.5$ mm)')
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=2.2, ls='--', label='Off-Axis Hole ($R = 0.10$ mm)')
    ax.add_patch(hole)

    cbar = plt.colorbar(p_coll, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Longest Element Edge $h_{\max}$ [$\mu$m]')

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title(r'FIGURE A: Generalized 2D Adapted Mesh ($N = 54,604$)' + '\n' + r'Dual-Support Refinement with $h_{\max} \leq 1.5\,\mu\mathrm{m}$ and Coarse Bulk ($20\,\mu\mathrm{m}$)', pad=12)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_framework_figure_a_full_adapted_mesh.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_framework_figure_a_full_adapted_mesh.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # FIGURE B: ZOOMED ADAPTED MESH AROUND NOTCH & HOLE FLANKS
    # -------------------------------------------------------------
    print("Plotting FIGURE B: Zoomed adapted mesh...")
    fig, ax = plt.subplots(figsize=(8.5, 8))
    zoom_patches = []
    zoom_sizes = []
    for conn in e_gen:
        pts = [n_gen[n] for n in conn if n in n_gen]
        if len(pts) >= 3:
            xc = np.mean([p[0] for p in pts])
            yc = np.mean([p[1] for p in pts])
            if 0.44 <= xc <= 0.86 and 0.44 <= yc <= 0.82:
                zoom_patches.append(MplPoly(pts, closed=True))
                zoom_sizes.append(max_edge(pts) * 1000.0)

    p_zoom = PatchCollection(zoom_patches, cmap='viridis_r', edgecolor='#2f3542', linewidths=0.25, alpha=0.95)
    p_zoom.set_array(np.array(zoom_sizes))
    p_zoom.set_clim(1.0, 10.0)
    ax.add_collection(p_zoom)

    # Overlays
    ax.plot([0.45, 0.50], [0.5, 0.5], color='#ff4757', lw=3.5, label='Notch Tip ($x=0.50$ mm)')
    hole_z = Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=2.2, ls='--', label='Hole ($R=0.10$ mm)')
    ax.add_patch(hole_z)

    # Support outlines
    ax.plot([v[0] for v in left_verts], [v[1] for v in left_verts], color='#00d2d3', lw=2.2, label=r'Notch-Ligament Support ($3\ell_0$ buffer)')
    ax.plot([v[0] for v in right_verts], [v[1] for v in right_verts], color='#ff9f43', lw=2.2, label=r'Opposite Flank Support ($3\ell_0$ buffer)')

    cbar = plt.colorbar(p_zoom, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Longest Element Edge $h_{\max}$ [$\mu$m]')

    ax.set_xlim(0.46, 0.84)
    ax.set_ylim(0.46, 0.78)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title(r'FIGURE B: Zoomed Adapted Mesh & Element Grading' + '\n' + r'Seamless Ligament Transition & Opposite Flank Refinement', pad=12)
    ax.legend(loc='lower left', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_framework_figure_b_zoomed_adapted_mesh.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_framework_figure_b_zoomed_adapted_mesh.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # FIGURE C: INDICATOR SUPPORT VERSUS ADAPTED MESH OVERLAY
    # -------------------------------------------------------------
    print("Plotting FIGURE C: Indicator support overlay...")
    fig, ax = plt.subplots(figsize=(9, 8))

    d_pts, d_vals = [], []
    with open(damage_csv) as f:
        for r in csv.DictReader(f):
            eid = int(r['phys_elem_id'])
            d = float(r['damage'])
            if d >= 0.05 and eid <= len(e_orig):
                conn = e_orig[eid - 1]
                pts = [n_orig[n] for n in conn if n in n_orig]
                if pts:
                    d_pts.append((np.mean([p[0] for p in pts]), np.mean([p[1] for p in pts])))
                    d_vals.append(d)

    d_pts = np.array(d_pts)
    sc = ax.scatter(d_pts[:, 0], d_pts[:, 1], c=d_vals, cmap='plasma', s=12, alpha=0.85, zorder=3, label=r'Precritical Damage ($d \geq 0.05$)')
    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Authentic Precritical Damage $d$ [-]')

    ax.plot([v[0] for v in left_verts], [v[1] for v in left_verts], color='#10ac84', lw=2.5, zorder=4, label=r'Notch-Ligament Support ($3\ell_0$ buffer)')
    ax.plot([v[0] for v in right_verts], [v[1] for v in right_verts], color='#5f27cd', lw=2.5, zorder=4, label=r'Opposite Flank Support ($3\ell_0$ buffer)')
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#00d2d3', lw=3.0, zorder=5, label='Notch ($a_0 = 0.5$ mm)')
    hole_c = Circle((0.65, 0.65), 0.10, edgecolor='#ee5253', facecolor='white', lw=2.0, ls='--', zorder=4, label='Hole ($R=0.10$ mm)')
    ax.add_patch(hole_c)

    ax.set_xlim(0.40, 0.88)
    ax.set_ylim(0.42, 0.80)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]')
    ax.set_ylabel('$y$ [mm]')
    ax.set_title(r'FIGURE C: Authentic Precritical Indicator vs Exact Support Boundaries' + '\n' + r'Full Domain Topology: Primary Ligament Band and Secondary Flank', pad=12)
    ax.legend(loc='upper right', frameon=True, framealpha=0.95)
    ax.grid(True, linestyle=':', alpha=0.4)

    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_framework_figure_c_indicator_support_overlay.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_framework_figure_c_indicator_support_overlay.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # FIGURE D: THREE-WAY MESH COMPARISON
    # -------------------------------------------------------------
    print("Plotting FIGURE D: Three-way mesh comparison...")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6))

    def make_patches(nodes, elems, xlim, ylim):
        pl = []
        for conn in elems:
            pts = [nodes[n] for n in conn if n in nodes]
            if len(pts) >= 3:
                xc = np.mean([p[0] for p in pts])
                yc = np.mean([p[1] for p in pts])
                if xlim[0] <= xc <= xlim[1] and ylim[0] <= yc <= ylim[1]:
                    pl.append(MplPoly(pts, closed=True))
        return pl

    xlim = (0.46, 0.84)
    ylim = (0.46, 0.78)

    # Panel 1: Native Method A (46k)
    p1 = make_patches(n_orig, e_orig, xlim, ylim)
    ax1.add_collection(PatchCollection(p1, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.25))
    ax1.plot([0.45, 0.50], [0.5, 0.5], color='#ff4757', lw=3.0)
    ax1.add_patch(Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=1.8, ls='--'))
    ax1.set_title(r'(a) Original Native Method A ($46,747$ elems)' + '\n' + r'Defect: Global Bulk Over-Refinement ($90.5\% \leq 10\,\mu$m)', fontsize=11)

    # Panel 2: Baseline Localized (23k)
    p2 = make_patches(n_base, e_base, xlim, ylim)
    ax2.add_collection(PatchCollection(p2, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.25))
    ax2.plot([0.45, 0.50], [0.5, 0.5], color='#ff4757', lw=3.0)
    ax2.add_patch(Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=1.8, ls='--'))
    ax2.annotate('DEFECT: Unrefined Right Flank\n(Coordinate Filter Exclusion)',
                 xy=(0.76, 0.65), xytext=(0.67, 0.73),
                 arrowprops=dict(facecolor='#d63031', shrink=0.08, width=1.5, headwidth=5),
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffeaa7', edgecolor='#d63031'),
                 fontsize=8.5, fontweight='bold', color='#d63031')
    ax2.set_title(r'(b) Baseline Localized Candidate ($23,664$ elems)' + '\n' + r'Defect: Hardcoded Filter Excluded Opposite Flank', fontsize=11)

    # Panel 3: Corrected Generalized (54k)
    p3 = make_patches(n_gen, e_gen, xlim, ylim)
    ax3.add_collection(PatchCollection(p3, facecolor='#f1f2f6', edgecolor='#2f3542', linewidths=0.25))
    ax3.plot([0.45, 0.50], [0.5, 0.5], color='#ff4757', lw=3.0)
    ax3.add_patch(Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=1.8, ls='--'))
    ax3.annotate(r'CORRECTED: Dual Supports' + '\n' + r'$h_{\max} \leq 1.5\,\mu\mathrm{m}$ Both Flanks',
                 xy=(0.76, 0.65), xytext=(0.67, 0.73),
                 arrowprops=dict(facecolor='#00b894', shrink=0.08, width=1.5, headwidth=5),
                 bbox=dict(boxstyle='round,pad=0.3', facecolor='#e8f8f5', edgecolor='#00b894'),
                 fontsize=8.5, fontweight='bold', color='#00b894')
    ax3.set_title(r'(c) Corrected Generalized Mesh ($54,604$ elems)' + '\n' + r'Resolved: Topology Support & Selective Bulk Coarsening', fontsize=11)

    for ax in [ax1, ax2, ax3]:
        ax.set_xlim(xlim); ax.set_ylim(ylim); ax.set_aspect('equal')
        ax.set_xlabel('$x$ [mm]'); ax.set_ylabel('$y$ [mm]')
        ax.grid(True, linestyle=':', alpha=0.4)

    plt.tight_layout()
    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_framework_figure_d_three_way_mesh_comparison.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_framework_figure_d_three_way_mesh_comparison.pdf'), bbox_inches='tight')
    plt.close(fig)

    # -------------------------------------------------------------
    # FIGURE E: GENERALITY TEST SUITE (3 CONFIGURATIONS)
    # -------------------------------------------------------------
    print("Plotting FIGURE E: Generality test suite...")
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6.2))

    def make_full_patches(nodes, elems):
        pl = []
        for conn in elems:
            pts = [nodes[n] for n in conn if n in nodes]
            if len(pts) >= 3: pl.append(MplPoly(pts, closed=True))
        return pl

    # Subplot 1: Case 1 (Off-Axis Hole)
    ax1.add_collection(PatchCollection(make_full_patches(n_gen, e_gen), facecolor='#f8f9fa', edgecolor='#2f3542', linewidths=0.18))
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='#ff4757', lw=2.5)
    ax1.add_patch(Circle((0.65, 0.65), 0.10, edgecolor='#2ed573', facecolor='white', lw=1.8, ls='--'))
    ax1.set_title('CASE 1: Mode-I Off-Axis Hole\n[AUTHENTIC PRECRITICAL INDICATOR]\n$N = 54,604$ elements', fontsize=11)

    # Subplot 2: Case 2 (Shifted Hole)
    ax2.add_collection(PatchCollection(make_full_patches(n_c2, e_c2), facecolor='#f8f9fa', edgecolor='#2f3542', linewidths=0.18))
    ax2.plot([0.0, 0.45], [0.5, 0.5], color='#ff4757', lw=2.5)
    ax2.add_patch(Circle((0.60, 0.40), 0.08, edgecolor='#2ed573', facecolor='white', lw=1.8, ls='--'))
    ax2.set_title('CASE 2: Shifted Hole at (0.60, 0.40)\n[SYNTHETIC TEST FIELD]\n$N = 40,940$ elements', fontsize=11)

    # Subplot 3: Case 3 (No Hole)
    ax3.add_collection(PatchCollection(make_full_patches(n_c3, e_c3), facecolor='#f8f9fa', edgecolor='#2f3542', linewidths=0.18))
    ax3.plot([0.0, 0.5], [0.5, 0.5], color='#ff4757', lw=2.5)
    ax3.set_title('CASE 3: Pure Edge Notch (No Hole)\n[SYNTHETIC TEST FIELD]\n$N = 31,675$ elements', fontsize=11)

    for ax in [ax1, ax2, ax3]:
        ax.set_xlim(-0.02, 1.02); ax.set_ylim(-0.02, 1.02); ax.set_aspect('equal')
        ax.set_xlabel('$x$ [mm]'); ax.set_ylabel('$y$ [mm]')
        ax.grid(True, linestyle=':', alpha=0.4)

    plt.tight_layout()
    for od in out_dirs:
        fig.savefig(os.path.join(od, 'fig_framework_figure_e_generality_test_suite.png'), dpi=300, bbox_inches='tight')
        fig.savefig(os.path.join(od, 'fig_framework_figure_e_generality_test_suite.pdf'), bbox_inches='tight')
    plt.close(fig)

    print("All 5 framework publication figures generated successfully!")

if __name__ == '__main__':
    run_plotting()
