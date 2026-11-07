# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1666_figures.py
===========================================
Task: F1666 - Generalized 2D Hybrid Adaptive Remeshing
Renders the authoritative 6-panel supervisor evidence package:
  FIGURE F1666: Generalized 2D Hybrid Adaptive Remeshing Framework Synthesis:
  (a) Authentic Donor Damage d(x, y) (Job 1 1421063.mmaster02)
  (b) Authentic Recovery Relative Error eta(x, y) (PK_HOLE_F1661_RECOVERY)
  (c) Hybrid Sizing Field h_hybrid = min(h_MISESERI, h_damage)
  (d) Resulting F1666 Hybrid Adapted Mesh (42,628 elements, 96.7% quads)
  (e) High-Magnification Zoom: Primary Ligament & Advancing Secondary Crack
  (f) Regional Sizing CDF & Comparison vs F1664 Native MISESERI Baseline
"""

from __future__ import print_function
import os
import sys
import json
import math
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors
from matplotlib.patches import Circle, Rectangle

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

output_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]

for d in output_dirs:
    if not os.path.exists(d):
        os.makedirs(d)

plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 8.5,
    'figure.titlesize': 13
})

def main():
    print("======================================================================")
    print("PLOTTING FIGURE F1666: HYBRID ADAPTIVE REMESHING SYNTHESIS PACKAGE")
    print("======================================================================")

    # 1. Load Sizing Field Data
    sizing_field_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1666_HYBRID_SIZING_FIELD.json"
    with open(sizing_field_path, "r") as f:
        sizing_data = json.load(f)

    donor_nodes = {int(k): v for k, v in sizing_data["donor_nodes"].items()}
    donor_elements = sizing_data["donor_elements"]
    rec_nodes = {int(k): v for k, v in sizing_data["recovery_nodes"].items()}
    rec_elements = sizing_data["recovery_elements"]

    # 2. Parse F1664 and F1666 adapted physical meshes
    f1664_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    f1666_inp = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1666_HYBRID_ADAPT_PHYS.inp"

    nodes_1664, quads_1664, tris_1664 = MeshQualityAuditEngine.parse_physical_inp(f1664_inp)
    nodes_1666, quads_1666, tris_1666 = MeshQualityAuditEngine.parse_physical_inp(f1666_inp)

    # 3. Create 6-panel Figure (2 rows x 3 cols)
    fig, axes = plt.subplots(2, 3, figsize=(18.0, 11.5))
    plt.subplots_adjust(left=0.06, right=0.96, bottom=0.07, top=0.92, wspace=0.28, hspace=0.28)

    # --------------------------------------------------------------------------
    # Panel (a): Authentic Donor Phase-Field Damage Field d(x, y)
    # --------------------------------------------------------------------------
    ax_a = axes[0, 0]
    polys_a = [[donor_nodes[nid] for nid in el["connectivity"]] for el in donor_elements]
    d_vals = np.array([el["d_max"] for el in donor_elements])

    pc_a = PolyCollection(polys_a, array=d_vals, cmap='inferno', edgecolors='none')
    pc_a.set_clim(0.0, 1.0)
    ax_a.add_collection(pc_a)

    # Notch & Hole geometry overlay
    ax_a.plot([0.0, 0.50], [0.50, 0.50], color='cyan', lw=2.5, label='Notch ($a_0=0.5$)')
    hole_a = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=1.8, ls='--', label='Hole ($R=0.10$)')
    ax_a.add_patch(hole_a)

    ax_a.set_xlim(0.0, 1.0)
    ax_a.set_ylim(0.0, 1.0)
    ax_a.set_aspect('equal')
    ax_a.set_xlabel('X [mm]')
    ax_a.set_ylabel('Y [mm]')
    ax_a.set_title('(a) Authentic Donor Damage $d(x,y)$ (Job 1 1421063)', fontweight='bold')
    ax_a.legend(loc='lower left', framealpha=0.9)
    cb_a = plt.colorbar(pc_a, ax=ax_a, fraction=0.046, pad=0.04)
    cb_a.set_label('Damage $d$')

    # --------------------------------------------------------------------------
    # Panel (b): Authentic Recovery Relative Stress Error eta(x, y)
    # --------------------------------------------------------------------------
    ax_b = axes[0, 1]
    polys_b = [[rec_nodes[nid] for nid in el["connectivity"]] for el in rec_elements]
    eta_vals = np.array([el["eta_pct"] for el in rec_elements])

    pc_b = PolyCollection(polys_b, array=eta_vals, cmap='viridis', norm=mcolors.LogNorm(vmin=1.0, vmax=50.0), edgecolors='none')
    ax_b.add_collection(pc_b)

    ax_b.plot([0.0, 0.50], [0.50, 0.50], color='red', lw=2.5)
    hole_b = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', lw=1.8, ls='--')
    ax_b.add_patch(hole_b)

    ax_b.set_xlim(0.0, 1.0)
    ax_b.set_ylim(0.0, 1.0)
    ax_b.set_aspect('equal')
    ax_b.set_xlabel('X [mm]')
    ax_b.set_ylabel('Y [mm]')
    ax_b.set_title(r'(b) Recovery Stress Error $\eta = (\mathrm{MISESERI}/\bar{\sigma})\times 100\%$', fontweight='bold')
    cb_b = plt.colorbar(pc_b, ax=ax_b, fraction=0.046, pad=0.04)
    cb_b.set_label(r'Relative Error $\eta$ [%]')

    # --------------------------------------------------------------------------
    # Panel (c): Mathematical Hybrid Sizing Field h_hybrid = min(h_MISESERI, h_damage)
    # --------------------------------------------------------------------------
    ax_c = axes[0, 2]
    # Sizing evaluated across recovery elements
    h_hyb_vals = []
    for el in rec_elements:
        cx, cy = el["cx"], el["cy"]
        eta = el["eta_pct"]
        # Nearest donor damage
        # Find damage
        d_val = 0.0
        min_dist = 1e9
        for del_el in donor_elements:
            dist = math.hypot(cx - del_el["cx"], cy - del_el["cy"])
            if dist < min_dist:
                min_dist = dist
                d_val = del_el["d_max"]

        h_dam = 1.50 if d_val >= 0.80 else (1.50 + 2.25 * ((0.80 - d_val)/0.60)**2 if d_val >= 0.20 else 20.0)
        h_mises = 1.50 if eta >= 25.0 else (1.50 + 2.25 * ((25.0 - eta)/20.0) if eta >= 5.0 else 20.0)
        h_hyb_vals.append(min(h_dam, h_mises))

    h_hyb_vals = np.array(h_hyb_vals)
    pc_c = PolyCollection(polys_b, array=h_hyb_vals, cmap='plasma_r', norm=mcolors.LogNorm(vmin=1.0, vmax=20.0), edgecolors='none')
    ax_c.add_collection(pc_c)

    ax_c.plot([0.0, 0.50], [0.50, 0.50], color='cyan', lw=2.5)
    hole_c = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=1.8, ls='--')
    ax_c.add_patch(hole_c)

    ax_c.set_xlim(0.0, 1.0)
    ax_c.set_ylim(0.0, 1.0)
    ax_c.set_aspect('equal')
    ax_c.set_xlabel('X [mm]')
    ax_c.set_ylabel('Y [mm]')
    ax_c.set_title(r'(c) Hybrid Sizing Field $h_{\mathrm{hybrid}} = \min(h_{\mathrm{err}}, h_d)$ [$\mu$m]', fontweight='bold')
    cb_c = plt.colorbar(pc_c, ax=ax_c, fraction=0.046, pad=0.04)
    cb_c.set_label(r'Target Size $h_{\mathrm{hybrid}}$ [$\mu$m]')

    # --------------------------------------------------------------------------
    # Panel (d): Full Adapted Mesh Topology for F1666 Hybrid Off-Axis Hole
    # --------------------------------------------------------------------------
    ax_d = axes[1, 0]
    all_1666 = {}
    all_1666.update(quads_1666)
    all_1666.update(tris_1666)

    # Subsample elements for fast rendering of 42k mesh
    polys_d = []
    edges_d = []
    for eid in sorted(all_1666.keys())[::2]: # Every 2nd element
        conn = all_1666[eid]
        pts = [nodes_1666[n] for n in conn]
        polys_d.append(pts)
        e_lens = [math.hypot(pts[i][0] - pts[(i+1)%len(pts)][0], pts[i][1] - pts[(i+1)%len(pts)][1]) for i in range(len(pts))]
        edges_d.append(max(e_lens) * 1000.0)

    pc_d = PolyCollection(polys_d, array=np.array(edges_d), cmap='viridis_r', norm=mcolors.LogNorm(vmin=1.0, vmax=25.0), edgecolors='black', linewidths=0.1)
    ax_d.add_collection(pc_d)

    ax_d.plot([0.0, 0.50], [0.50, 0.50], color='red', lw=2.0)
    hole_d = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', lw=1.5, ls='--')
    ax_d.add_patch(hole_d)

    ax_d.set_xlim(0.0, 1.0)
    ax_d.set_ylim(0.0, 1.0)
    ax_d.set_aspect('equal')
    ax_d.set_xlabel('X [mm]')
    ax_d.set_ylabel('Y [mm]')
    ax_d.set_title(r'(d) F1666 Hybrid Adapted Mesh ($N=42,628$, 96.7% quads)', fontweight='bold')
    cb_d = plt.colorbar(pc_d, ax=ax_d, fraction=0.046, pad=0.04)
    cb_d.set_label(r'Element Edge $h$ [$\mu$m]')

    # --------------------------------------------------------------------------
    # Panel (e): High-Magnification Zoom: Primary Ligament & Advancing Secondary Crack
    # --------------------------------------------------------------------------
    ax_e = axes[1, 1]
    # Zoom domain: X in [0.46, 0.95], Y in [0.45, 0.80]
    zoom_polys = []
    zoom_edges = []
    for eid, conn in all_1666.items():
        pts = [nodes_1666[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        if 0.46 <= cx <= 0.98 and 0.45 <= cy <= 0.78:
            zoom_polys.append(pts)
            e_lens = [math.hypot(pts[i][0] - pts[(i+1)%len(pts)][0], pts[i][1] - pts[(i+1)%len(pts)][1]) for i in range(len(pts))]
            zoom_edges.append(max(e_lens) * 1000.0)

    pc_e = PolyCollection(zoom_polys, array=np.array(zoom_edges), cmap='plasma_r', norm=mcolors.LogNorm(vmin=0.8, vmax=8.0), edgecolors='black', linewidths=0.15)
    ax_e.add_collection(pc_e)

    hole_e = Circle((0.65, 0.65), 0.10, edgecolor='black', facecolor='white', lw=2.0, ls='--')
    ax_e.add_patch(hole_e)
    ax_e.plot([0.46, 0.50], [0.50, 0.50], color='red', lw=3.0)

    ax_e.text(0.53, 0.53, 'Primary Ligament\n$h_{\\mathrm{med}}=1.80\\,\\mu$m\n(870 el $\\leq 1.5\\,\\mu$m)', color='navy', fontweight='bold', fontsize=8.5, bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85))
    ax_e.text(0.76, 0.68, 'Advancing Tip\n$h_{\\mathrm{med}}=1.87\\,\\mu$m\n(1,471 el $\\leq 1.5\\,\\mu$m)', color='darkred', fontweight='bold', fontsize=8.5, bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85))

    ax_e.set_xlim(0.46, 0.98)
    ax_e.set_ylim(0.45, 0.78)
    ax_e.set_aspect('equal')
    ax_e.set_xlabel('X [mm]')
    ax_e.set_ylabel('Y [mm]')
    ax_e.set_title(r'(e) Zoomed FPZ: Primary Ligament & Advancing Tip', fontweight='bold')
    cb_e = plt.colorbar(pc_e, ax=ax_e, fraction=0.046, pad=0.04)
    cb_e.set_label(r'Edge $h$ [$\mu$m]')

    # --------------------------------------------------------------------------
    # Panel (f): Regional Sizing CDF & Comparison vs F1664 Native MISESERI Baseline
    # --------------------------------------------------------------------------
    ax_f = axes[1, 2]
    # Compute all edge lengths for F1664 and F1666
    all_1664 = {}
    all_1664.update(quads_1664)
    all_1664.update(tris_1664)

    h_1664_all = []
    h_1664_lig = []
    for eid, conn in all_1664.items():
        pts = [nodes_1664[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        e_lens = [math.hypot(pts[i][0] - pts[(i+1)%len(pts)][0], pts[i][1] - pts[(i+1)%len(pts)][1]) for i in range(len(pts))]
        h_max = max(e_lens) * 1000.0
        h_1664_all.append(h_max)
        if 0.50 <= cx <= 0.65 and 0.50 <= cy <= 0.65:
            h_1664_lig.append(h_max)

    h_1666_all = []
    h_1666_lig = []
    h_1666_sec = []
    for eid, conn in all_1666.items():
        pts = [nodes_1666[n] for n in conn]
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        e_lens = [math.hypot(pts[i][0] - pts[(i+1)%len(pts)][0], pts[i][1] - pts[(i+1)%len(pts)][1]) for i in range(len(pts))]
        h_max = max(e_lens) * 1000.0
        h_1666_all.append(h_max)
        if 0.50 <= cx <= 0.65 and 0.50 <= cy <= 0.65:
            h_1666_lig.append(h_max)
        elif 0.71 <= cx <= 0.98 and 0.55 <= cy <= 0.72:
            h_1666_sec.append(h_max)

    h_1664_all.sort()
    h_1664_lig.sort()
    h_1666_all.sort()
    h_1666_lig.sort()
    h_1666_sec.sort()

    y_1664_all = np.linspace(0, 1, len(h_1664_all))
    y_1664_lig = np.linspace(0, 1, len(h_1664_lig))
    y_1666_all = np.linspace(0, 1, len(h_1666_all))
    y_1666_lig = np.linspace(0, 1, len(h_1666_lig))
    y_1666_sec = np.linspace(0, 1, len(h_1666_sec))

    ax_f.plot(h_1664_all, y_1664_all, color='gray', lw=1.8, ls='--', label='F1664 Global Native ($N=20,213$)')
    ax_f.plot(h_1664_lig, y_1664_lig, color='red', lw=2.0, ls=':', label='F1664 Ligament (MISES relaxation)')
    ax_f.plot(h_1666_all, y_1666_all, color='black', lw=2.0, label='F1666 Hybrid Global ($N=42,628$)')
    ax_f.plot(h_1666_lig, y_1666_lig, color='blue', lw=2.5, label=r'F1666 Hybrid Ligament ($h_{\mathrm{med}}=1.80\,\mu$m)')
    ax_f.plot(h_1666_sec, y_1666_sec, color='green', lw=2.0, ls='-.', label=r'F1666 Hybrid Sec. Tip ($h_{\mathrm{med}}=1.87\,\mu$m)')

    # Physical thresholds
    ax_f.axvline(1.50, color='darkred', ls='--', lw=1.5, label=r'Physical target $h \leq \ell_0/5 = 1.5\,\mu$m')
    ax_f.axvline(3.75, color='orange', ls=':', lw=1.5, label=r'Continuum limit $h \leq \ell_0/2 = 3.75\,\mu$m')

    ax_f.set_xscale('log')
    ax_f.set_xlim(0.5, 35.0)
    ax_f.set_ylim(0.0, 1.05)
    ax_f.set_xlabel(r'Longest Element Edge $h_{\max}$ [$\mu$m]')
    ax_f.set_ylabel('Cumulative Distribution Function (CDF)')
    ax_f.set_title('(f) Resolution CDF: F1664 vs F1666 Hybrid', fontweight='bold')
    ax_f.legend(loc='lower right', fontsize=7.8, framealpha=0.9)
    ax_f.grid(True, which='both', ls=':', alpha=0.5)

    # Global Title
    fig.suptitle('FIGURE F1666: Generalized 2D Hybrid Adaptive Remeshing Framework Synthesis\n'
                 r'$h_{\mathrm{hybrid}}(x,y) = \min(h_{\mathrm{MISESERI}}(x,y),\, h_{\mathrm{damage}}(x,y))$ Synergistically Resolves Severed Ligament and Advancing Tip',
                 fontweight='bold', fontsize=13)

    for d in output_dirs:
        png_path = os.path.join(d, "fig_f1666_hybrid_adaptive_remesh_synthesis.png")
        pdf_path = os.path.join(d, "fig_f1666_hybrid_adaptive_remesh_synthesis.pdf")
        fig.savefig(png_path, dpi=300)
        fig.savefig(pdf_path)
        print("Exported Figure F1666 to: %s and .pdf" % png_path)

    plt.close(fig)

if __name__ == "__main__":
    main()
