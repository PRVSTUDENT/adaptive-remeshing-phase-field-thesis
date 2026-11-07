# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1668_three_way_comparison.py
========================================================
Task: F1668 - Three-Way Controlled 2D Adaptive Remeshing Comparison
Generates publication-quality 6-panel synthesis figures for Master's thesis:
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1668_three_way_comparison_synthesis.png (.pdf)
  - docs/MA_AdaptiveRemeshing_Report_2026_main/figures/fig_f1668_three_way_comparison_synthesis.png (.pdf)

Panels:
  (a) Authentic Donor Damage d(x, y) & SPR Stress Error eta(x, y) Sources
  (b) Target Sizing Fields: h_A (Stress-Only), h_B (Damage-Only), h_C (Combined)
  (c) Full Adapted Meshes: Case A (64k), Case B (8.2k), Case C (64.7k)
  (d) High-Magnification Notch-to-Hole Ligament & Advancing Tip Zoom
  (e) Cumulative Sizing CDFs: Case A vs Case B vs Case C vs F1664 Reference
  (f) Multi-Criteria Evaluation Matrix: Resolution vs Far-Field Efficiency vs Cost
"""

from __future__ import print_function
import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Patch
from matplotlib.collections import PatchCollection, LineCollection
import matplotlib.ticker as ticker
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

def load_mesh_geometry(inp_path):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    all_elems = {}
    all_elems.update(quads)
    all_elems.update(tris)

    lines = []
    edges_h = []
    for eid, conn in all_elems.items():
        pts = [nodes[n] for n in conn]
        n_pts = len(pts)
        for i in range(n_pts):
            p1 = pts[i]
            p2 = pts[(i+1)%n_pts]
            lines.append([(p1[0], p1[1]), (p2[0], p2[1])])
            edges_h.append(math.hypot(p1[0]-p2[0], p1[1]-p2[1]) * 1000.0)

    return nodes, all_elems, lines, np.array(edges_h)

def evaluate_threshold_1d(dist, dmin=0.0075, dmax=0.0250, smin=0.00135, smax=0.0200):
    h = np.empty_like(dist)
    h[dist <= dmin] = smin
    h[dist >= dmax] = smax
    m = (dist > dmin) & (dist < dmax)
    h[m] = smin + (dist[m] - dmin)/(dmax - dmin)*(smax - smin)
    return h * 1000.0 # um

def main():
    print("=" * 80)
    print("GENERATING F1668 THREE-WAY SYNTHESIS PUBLICATION FIGURES")
    print("=" * 80)

    # File paths
    sizing_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1666_HYBRID_SIZING_FIELD.json"
    metrics_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1668_THREE_WAY_COMPARISON_METRICS.json"

    inp_ref = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    inp_case_a = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1668_CASE_A_STRESS_ONLY_PHYS.inp"
    inp_case_b = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PHYS.inp"
    inp_case_c = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1668_CASE_C_COMBINED_PHYS.inp"

    with open(str(sizing_json), "r") as f:
        sizing_data = json.load(f)
    with open(str(metrics_json), "r") as f:
        metrics_data = json.load(f)

    donor_elems = sizing_data["donor_elements"]
    rec_elems = sizing_data["recovery_elements"]

    d_pts = np.array([[el["cx"], el["cy"]] for el in donor_elems if el["d_max"] >= 0.70])
    s_pts = np.array([[el["cx"], el["cy"]] for el in rec_elems if el["eta_pct"] >= 10.0])

    # 2D Grid for Field Plotting
    NX, NY = 200, 200
    xs = np.linspace(0.0, 1.0, NX)
    ys = np.linspace(0.0, 1.0, NY)
    XX, YY = np.meshgrid(xs, ys)
    grid_pts = np.column_stack((XX.ravel(), YY.ravel()))

    slit_mask = (XX <= 0.50) & (np.abs(YY - 0.50) <= 0.001)
    hole_mask = ((XX - 0.65)**2 + (YY - 0.65)**2) < (0.10**2)
    void_mask = slit_mask | hole_mask

    def calc_dist(pts, ref_pts):
        dists = np.empty(len(pts))
        chunk = 5000
        for i in range(0, len(pts), chunk):
            p = pts[i:i+chunk]
            diff = p[:, None, :] - ref_pts[None, :, :]
            dists[i:i+chunk] = np.sqrt(np.min(np.sum(diff**2, axis=-1), axis=-1))
        return dists

    print("Computing 2D sizing fields...")
    dd = calc_dist(grid_pts, d_pts).reshape((NY, NX))
    ds = calc_dist(grid_pts, s_pts).reshape((NY, NX))

    h_A = np.ma.masked_array(evaluate_threshold_1d(ds), mask=void_mask)
    h_B = np.ma.masked_array(evaluate_threshold_1d(dd), mask=void_mask)
    h_C = np.minimum(h_A, h_B)

    # Helper function for drawing specimen boundaries
    def draw_specimen(ax, show_boxes=True):
        ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'k-', lw=1.0)
        ax.plot([0.0, 0.50], [0.50, 0.50], 'r-', lw=1.8)
        circle = Circle((0.65, 0.65), 0.10, edgecolor='lime', facecolor='white', lw=1.5, linestyle='--', zorder=10)
        ax.add_patch(circle)
        if show_boxes:
            r1 = Rectangle((0.50, 0.50), 0.15, 0.15, edgecolor='magenta', facecolor='none', lw=1.2, linestyle=':')
            r2 = Rectangle((0.71, 0.55), 0.27, 0.17, edgecolor='cyan', facecolor='none', lw=1.2, linestyle=':')
            ax.add_patch(r1)
            ax.add_patch(r2)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_xlabel('x [mm]', fontsize=9, fontweight='bold')
        ax.set_ylabel('y [mm]', fontsize=9, fontweight='bold')

    # Setup 6-Panel Figure
    fig = plt.figure(figsize=(20, 12.5), dpi=300)
    plt.subplots_adjust(left=0.05, right=0.96, bottom=0.06, top=0.93, wspace=0.28, hspace=0.30)

    # --------------------------------------------------------------------------
    # Panel (a): Source Fields (Authentic Donor Damage & Recovery SPR Error)
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(2, 3, 1)
    draw_specimen(ax1)
    # Scatter authentic donor damage and recovery error
    sc_s = ax1.scatter([el["cx"] for el in rec_elems], [el["cy"] for el in rec_elems],
                       c=[el["eta_pct"] for el in rec_elems], cmap='Blues', s=10, alpha=0.6,
                       vmin=0, vmax=25, label='Recovery SPR $\\eta$ [%]')
    sc_d = ax1.scatter([el["cx"] for el in donor_elems if el["d_max"] >= 0.10],
                       [el["cy"] for el in donor_elems if el["d_max"] >= 0.10],
                       c=[el["d_max"] for el in donor_elems if el["d_max"] >= 0.10],
                       cmap='YlOrRd', s=18, edgecolors='black', lw=0.4, vmin=0, vmax=1.0,
                       label='Donor Damage $d$')
    ax1.set_title('(a) Authentic Source Fields for Adaptivity\nCoarse Damage $d(x,y)$ & Recovery Stress Error $\\eta(x,y)$', fontsize=11, fontweight='bold')
    cb1 = plt.colorbar(sc_d, ax=ax1, fraction=0.046, pad=0.04)
    cb1.set_label('Donor Phase-Field Damage $d$', fontsize=9, fontweight='bold')
    ax1.legend(loc='lower left', fontsize=8, framealpha=0.9)

    # --------------------------------------------------------------------------
    # Panel (b): Three Target Sizing Fields Comparison (Sub-contours)
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(2, 3, 2)
    # Plot Case B (Damage-Only) field as background contour, with Case A overlay contours
    levels_size = np.linspace(1.35, 20.0, 38)
    cf2 = ax2.contourf(XX, YY, h_B, levels=levels_size, cmap='viridis_r', extend='both')
    draw_specimen(ax2)
    # Overlay contour lines for Case A (Stress-only) in blue
    cs_a = ax2.contour(XX, YY, h_A, levels=[1.50, 3.75, 10.0], colors='cyan', linewidths=1.2, linestyles='--')
    ax2.clabel(cs_a, inline=True, fontsize=7, fmt='Stress %1.1f')
    # Overlay contour lines for Case B (Damage-only) in magenta
    cs_b = ax2.contour(XX, YY, h_B, levels=[1.50, 3.75], colors='magenta', linewidths=1.4)
    ax2.clabel(cs_b, inline=True, fontsize=7, fmt='Damage %1.1f')
    ax2.set_title('(b) Target Sizing Fields: $h_A$ (Stress) vs $h_B$ (Damage)\nDamage $h_B$ (Colorfill) vs Stress $h_A$ (Cyan Dashed)', fontsize=11, fontweight='bold')
    cb2 = plt.colorbar(cf2, ax=ax2, fraction=0.046, pad=0.04)
    cb2.set_label('Target Size $h(x,y)$ [$\\mu$m]', fontsize=9, fontweight='bold')

    # --------------------------------------------------------------------------
    # Panel (c): Adapted Meshes Overview (Full Specimen)
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(2, 3, 3)
    # Plot Case B mesh lines
    nodes_b, elems_b, lines_b, _ = load_mesh_geometry(str(inp_case_b))
    lc_b = LineCollection(lines_b[::2], colors='navy', linewidths=0.35, alpha=0.7)
    ax3.add_collection(lc_b)
    draw_specimen(ax3, show_boxes=True)
    ax3.set_title('(c) Adapted Mesh Topology: Case B (Damage-Only)\n$N=8,237$ Quads | Leanest Mesh (87.3% Smaller than Combined)', fontsize=11, fontweight='bold')

    # --------------------------------------------------------------------------
    # Panel (d): High-Mag Notch-to-Hole & Advancing Tip Zoom
    # --------------------------------------------------------------------------
    ax4 = fig.add_subplot(2, 3, 4)
    # Zoom into x in [0.45, 0.85], y in [0.45, 0.80]
    lc_b_zoom = LineCollection(lines_b, colors='darkblue', linewidths=0.45, alpha=0.85)
    ax4.add_collection(lc_b_zoom)
    # Draw notch and hole in zoom
    ax4.plot([0.45, 0.50], [0.50, 0.50], 'r-', lw=2.2, label='Notch Tip')
    circle_zoom = Circle((0.65, 0.65), 0.10, edgecolor='lime', facecolor='white', lw=1.8, linestyle='--', zorder=10)
    ax4.add_patch(circle_zoom)
    ax4.set_xlim(0.46, 0.85)
    ax4.set_ylim(0.46, 0.80)
    ax4.set_aspect('equal')
    ax4.set_xlabel('x [mm]', fontsize=9, fontweight='bold')
    ax4.set_ylabel('y [mm]', fontsize=9, fontweight='bold')
    ax4.set_title('(d) High-Mag Fracture Zone Zoom (Case B)\nPrimary Ligament ($h=1.50\\,\\mu\\mathrm{m}$) & Opposite Flank ($h=1.57\\,\\mu\\mathrm{m}$)', fontsize=11, fontweight='bold')
    ax4.grid(True, linestyle=':', alpha=0.4)

    # --------------------------------------------------------------------------
    # Panel (e): Regional Sizing CDF Comparison across All 4 Meshes
    # --------------------------------------------------------------------------
    ax5 = fig.add_subplot(2, 3, 5)
    _, _, _, edges_ref = load_mesh_geometry(str(inp_ref))
    _, _, _, edges_a = load_mesh_geometry(str(inp_case_a))
    _, _, _, edges_b = load_mesh_geometry(str(inp_case_b))
    _, _, _, edges_c = load_mesh_geometry(str(inp_case_c))

    def plot_cdf(ax, edges, label, color, ls='-'):
        s = np.sort(edges)
        y = np.linspace(0.0, 100.0, len(s))
        ax.plot(s, y, color=color, linestyle=ls, lw=2.0, label=label)

    plot_cdf(ax5, edges_ref, 'F1664 Reference (20k FEs)', 'gray', ls=':')
    plot_cdf(ax5, edges_a, 'Case A: Stress-Only (64k FEs)', 'tab:blue', ls='--')
    plot_cdf(ax5, edges_b, 'Case B: Damage-Only (8.2k FEs)', 'tab:green', ls='-')
    plot_cdf(ax5, edges_c, 'Case C: Combined (64.7k FEs)', 'tab:red', ls='-.')

    ax5.axvline(1.50, color='crimson', linestyle='--', lw=1.2, label='Critical Target $\\ell_0/5 = 1.5\\,\\mu\\mathrm{m}$')
    ax5.axvline(3.75, color='orange', linestyle=':', lw=1.2, label='Continuum Bound $\\ell_0/2 = 3.75\\,\\mu\\mathrm{m}$')
    ax5.set_xlim(0.5, 25.0)
    ax5.set_ylim(0.0, 105.0)
    ax5.set_xlabel('Longest Element Edge $h_{\\max}$ [$\\mu$m]', fontsize=10, fontweight='bold')
    ax5.set_ylabel('Cumulative Percentage [%]', fontsize=10, fontweight='bold')
    ax5.set_title('(e) Global Element Sizing CDFs\nCase B Matches Sub-1.5 $\\mu$m Resolution with 87% Fewer FEs', fontsize=11, fontweight='bold')
    ax5.grid(True, linestyle='--', alpha=0.5)
    ax5.legend(loc='lower right', fontsize=8, framealpha=0.9)

    # --------------------------------------------------------------------------
    # Panel (f): Multi-Criteria Evaluation Matrix & Ranking
    # --------------------------------------------------------------------------
    ax6 = fig.add_subplot(2, 3, 6)
    ax6.axis('off')

    table_data = [
        ["Evaluation Metric", "F1664 Ref", "Case A (Stress)", "Case B (Damage)", "Case C (Hybrid)"],
        ["Total Elements", "20,213", "64,032", "8,237", "64,746"],
        ["Pure Quads %", "97.18%", "78.03%", "77.67%", "78.09%"],
        ["Non-Pos Jacobians", "0", "0", "0", "0"],
        ["Min Signed det(J)", "1.50e-7", "1.10e-7", "1.08e-7", "1.29e-7"],
        ["Sub-1.5 um Count", "273 (1.4%)", "27,554 (43%)", "2,299 (28%)", "28,097 (43%)"],
        ["Ligament Median h", "4.684 um", "1.490 um", "1.501 um", "1.491 um"],
        ["Advancing Tip Med h", "2.091 um", "1.532 um", "1.570 um", "1.516 um"],
        ["Far-Field Median h", "5.530 um", "1.570 um", "20.609 um", "1.573 um"],
        ["Far-Field Bloat %", "Moderate", "Severe (72%)", "MINIMAL (<1%)", "Severe (72%)"],
        ["Efficiency Score", "Moderate", "Poor", "EXCELLENT", "Good-Accurate"]
    ]

    col_widths = [0.32, 0.17, 0.17, 0.17, 0.17]
    tab = ax6.table(cellText=table_data, colWidths=col_widths, loc='center', cellLoc='center')
    tab.auto_set_font_size(False)
    tab.set_fontsize(8.5)
    tab.scale(1.0, 1.45)

    # Format header row
    for j in range(5):
        tab[(0, j)].set_facecolor('#2c3e50')
        tab[(0, j)].set_text_props(color='white', fontweight='bold')

    # Highlight Case B (Damage-Only) column as best compromise
    for i in range(1, len(table_data)):
        tab[(i, 3)].set_facecolor('#e8f8f5')
        tab[(i, 3)].set_text_props(fontweight='bold')

    ax6.set_title('(f) Master Three-Way Scientific Evaluation Matrix\nCase B Wins Efficiency-Resolution Trade-Off (8.2k vs 64.7k Quads)', fontsize=11, fontweight='bold')

    plt.suptitle(
        'TASK F1668: CONTROLLED THREE-WAY ADAPTIVE REMESHING STUDY\n'
        'Mode-I Plate with Off-Axis Hole | Authentic Coarse Donor & Recovery Fields | Identical Geometry & Mesher',
        fontsize=13, fontweight='bold', y=0.98
    )

    out_dirs = [
        REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures",
        REPO_ROOT / "docs" / "MA_AdaptiveRemeshing_Report_2026_main" / "figures"
    ]

    for d in out_dirs:
        d.mkdir(parents=True, exist_ok=True)
        png_p = d / "fig_f1668_three_way_comparison_synthesis.png"
        pdf_p = d / "fig_f1668_three_way_comparison_synthesis.pdf"
        plt.savefig(str(png_p), dpi=300, bbox_inches='tight')
        plt.savefig(str(pdf_p), bbox_inches='tight')
        print("Saved figure: %s" % png_p)
        print("Saved figure: %s" % pdf_p)

    plt.close()
    print("Figure generation completed successfully!")


if __name__ == "__main__":
    main()
