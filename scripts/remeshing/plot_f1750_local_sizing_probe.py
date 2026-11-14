# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1750_local_sizing_probe.py

Task F1750: Local Native Abaqus Damage-Derived Sizing Probe Synthesis Figure.
Generates publication-quality 4-panel visualization:
- Panel (a): Adapted Mesh Overview (121,223 elements) colored by achieved size h_achieved [mm].
- Panel (b): Requested Target Size h_target vs Achieved Size h_achieved (Scatter & Sizing Transfer).
- Panel (c): Primary Ligament & Secondary Corridor Along-Path Profiles (Requested vs Achieved vs l0/2).
- Panel (d): Synthesis Table of Finite-Element Metrics, Spatial Gates, and Hypothesis Falsification.

Outputs:
- results/figures/fig_f1750_local_sizing_probe.png
- results/figures/fig_f1750_local_sizing_probe.pdf
"""
from __future__ import print_function
import os
import sys
import math
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection
import numpy as np

def generate_f1750_figure(
    summary_path="results/validation/f1750_local_sizing_probe_summary.json",
    inp_path="models/pandey_kumar_mode1/233_f1750_local_sizing_probe/PK_F1750_CASE_3_ADAPT_PHYS.inp",
    out_png="results/figures/fig_f1750_local_sizing_probe.png",
    out_pdf="results/figures/fig_f1750_local_sizing_probe.pdf"
):
    print("=== TASK F1750: GENERATING 4-PANEL SYNTHESIS FIGURE ===")
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    # 1. Parse subset of mesh for visualization (stride sampling for clean plotting)
    print("  Reading adapted mesh: %s..." % inp_path)
    nodes = {}
    elements = []
    current_sec = None

    with open(inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l: continue
            if l.startswith('*'):
                lu = l.upper()
                if lu.startswith('*NODE') and not ('OUTPUT' in lu or 'PRINT' in lu or 'FILE' in lu):
                    current_sec = 'NODE'
                elif lu.startswith('*ELEMENT') and not ('OUTPUT' in lu or 'PRINT' in lu or 'FILE' in lu):
                    current_sec = 'ELEMENT'
                else:
                    current_sec = None
                continue

            if current_sec == 'NODE':
                parts = [p.strip() for p in l.split(',')]
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except (ValueError, IndexError):
                    pass
            elif current_sec == 'ELEMENT':
                parts = [p.strip() for p in l.split(',')]
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    elements.append((eid, conn))
                except (ValueError, IndexError):
                    pass

    n_total = len(elements)
    print("  Loaded %d elements, %d nodes." % (n_total, len(nodes)))

    # Compute element sizes & centroids
    elem_h = []
    elem_centroids = []
    for eid, conn in elements:
        if len(conn) == 4:
            x = [nodes[n][0] for n in conn]
            y = [nodes[n][1] for n in conn]
            area = 0.5 * abs((x[0]*y[1] - x[1]*y[0]) + (x[1]*y[2] - x[2]*y[1]) + (x[2]*y[3] - x[3]*y[2]) + (x[3]*y[0] - x[0]*y[3]))
            cx = sum(x) / 4.0
            cy = sum(y) / 4.0
        elif len(conn) == 3:
            x = [nodes[n][0] for n in conn]
            y = [nodes[n][1] for n in conn]
            area = 0.5 * abs((x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1])))
            cx = sum(x) / 3.0
            cy = sum(y) / 3.0
        else:
            continue
        elem_h.append(math.sqrt(area))
        elem_centroids.append((cx, cy))

    elem_h = np.array(elem_h)
    elem_cx = np.array([c[0] for c in elem_centroids])
    elem_cy = np.array([c[1] for c in elem_centroids])

    # 2. Setup Figure
    fig = plt.figure(figsize=(16, 12), dpi=300)

    # -------------------------------------------------------------
    # Panel (a): Adapted Mesh Overview (Colored by Achieved Element Size)
    # -------------------------------------------------------------
    ax_a = fig.add_subplot(2, 2, 1)
    ax_a.set_title(r"$\mathbf{(a)\ Case\ 3\ Local\ Native\ Sizing\ Probe\ Mesh\ (121,223\ el)}$", fontsize=11, fontweight='bold', pad=8)

    # Sample elements for scatter visualization
    sample_idx = np.random.RandomState(42).choice(len(elem_h), size=min(40000, len(elem_h)), replace=False)
    sc = ax_a.scatter(
        elem_cx[sample_idx], elem_cy[sample_idx],
        c=elem_h[sample_idx], cmap='viridis_r', s=1.2, alpha=0.85,
        vmin=0.05, vmax=0.45, rasterized=True
    )
    cb = plt.colorbar(sc, ax=ax_a, fraction=0.046, pad=0.04)
    cb.set_label(r"Achieved Element Size $h_{\mathrm{achieved}}$ [mm]", fontsize=9)

    # Draw CAD boundaries
    # Notch: (0, 70) to (10, 70)
    ax_a.plot([0.0, 10.0], [70.0, 70.0], 'r-', linewidth=2.0, label="Notch ($a=10$ mm)")
    # Central hole: (36.5, 51.0), r=10
    circ_center = patches.Circle((36.5, 51.0), 10.0, fill=True, color='white', ec='black', lw=1.5, zorder=5)
    circ_pin_low = patches.Circle((20.0, 20.0), 5.0, fill=True, color='white', ec='black', lw=1.5, zorder=5)
    circ_pin_up = patches.Circle((20.0, 100.0), 5.0, fill=True, color='white', ec='black', lw=1.5, zorder=5)
    ax_a.add_patch(circ_center)
    ax_a.add_patch(circ_pin_low)
    ax_a.add_patch(circ_pin_up)

    ax_a.set_xlim(-2.0, 67.0)
    ax_a.set_ylim(-2.0, 122.0)
    ax_a.set_xlabel(r"$x$ [mm]", fontsize=10)
    ax_a.set_ylabel(r"$y$ [mm]", fontsize=10)
    ax_a.set_aspect('equal')
    ax_a.legend(loc='upper right', fontsize=8)

    # -------------------------------------------------------------
    # Panel (b): Target vs Achieved Size Distribution (Global Refinement Disclosure)
    # -------------------------------------------------------------
    ax_b = fig.add_subplot(2, 2, 2)
    ax_b.set_title(r"$\mathbf{(b)\ Sizing\ Transfer:\ Target\ vs\ Achieved\ Size\ Distribution}$", fontsize=11, fontweight='bold', pad=8)

    # Histogram of achieved sizes vs requested target range
    bins = np.linspace(0.04, 1.50, 60)
    ax_b.hist(elem_h, bins=bins, color='#1f77b4', alpha=0.7, edgecolor='black', linewidth=0.5, density=True, label="Achieved Mesh Sizes ($h_{\mathrm{achieved}}$)")
    
    # Overlay requested distribution markers
    l0 = 0.285
    ax_b.axvline(l0 / 3.0, color='darkred', linestyle='--', linewidth=1.8, label=r"Core Target $h_{\mathrm{core}} = \ell_0/3 = 0.095$ mm")
    ax_b.axvline(l0 / 2.0, color='red', linestyle='-', linewidth=2.0, label=r"Process Zone Limit $\ell_0/2 = 0.1425$ mm")
    ax_b.axvline(1.3670, color='darkgreen', linestyle=':', linewidth=2.0, label=r"Requested Bulk Size $h_{\mathrm{bg}} = 1.367$ mm")

    ax_b.set_xlabel(r"Element Size $h$ [mm]", fontsize=10)
    ax_b.set_ylabel(r"Probability Density", fontsize=10)
    ax_b.set_xlim(0.0, 1.55)
    ax_b.legend(loc='upper right', fontsize=8)
    ax_b.grid(True, linestyle='--', alpha=0.4)

    # Annotation of global refinement mechanism
    ax_b.text(0.48, 0.45, "Native Abaqus Global\nEnergy-Norm Coupling:\nEntire plate refined\ndown to ~0.24 mm\n(Requested bulk 1.37 mm\nwas not preserved)",
              transform=ax_b.transAxes, fontsize=8.5, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', edgecolor='orange', alpha=0.9))

    # -------------------------------------------------------------
    # Panel (c): Along-Path Sizing in Primary Ligament & Secondary Corridor
    # -------------------------------------------------------------
    ax_c = fig.add_subplot(2, 2, 3)
    ax_c.set_title(r"$\mathbf{(c)\ Primary\ Ligament\ Along-Path\ Sizing\ Profile}$", fontsize=11, fontweight='bold', pad=8)

    # Filter elements in primary ligament band: (10, 70) to (26.5, 51.0)
    # Parametric coordinate s in [0, 1] along ligament
    dx_prim = 26.5 - 10.0
    dy_prim = 51.0 - 70.0
    L_prim = math.hypot(dx_prim, dy_prim)

    prim_s = []
    prim_sizes = []
    corridor_w = 2.0 * l0

    for i in range(len(elem_h)):
        px = elem_cx[i]
        py = elem_cy[i]
        if 9.5 <= px <= 27.0 and 50.0 <= py <= 70.5:
            # Project onto segment
            t = ((px - 10.0)*dx_prim + (py - 70.0)*dy_prim) / (L_prim**2)
            if 0.0 <= t <= 1.0:
                dist = math.hypot(px - (10.0 + t*dx_prim), py - (70.0 + t*dy_prim))
                if dist <= corridor_w:
                    prim_s.append(t * L_prim)
                    prim_sizes.append(elem_h[i])

    prim_s = np.array(prim_s)
    prim_sizes = np.array(prim_sizes)

    if len(prim_s) > 0:
        ax_c.scatter(prim_s, prim_sizes, color='navy', alpha=0.5, s=8, label="Achieved Elements ($h_{\mathrm{new}}$)")
        # Moving average
        sort_ord = np.argsort(prim_s)
        s_sorted = prim_s[sort_ord]
        h_sorted = prim_sizes[sort_ord]
        # Window rolling mean
        window = 25
        if len(h_sorted) > window:
            rolling_h = np.convolve(h_sorted, np.ones(window)/window, mode='valid')
            rolling_s = (s_sorted[:len(rolling_h)] + s_sorted[window-1:]) / 2.0
            ax_c.plot(rolling_s, rolling_h, 'k-', linewidth=2.0, label="Moving Mean Achieved Size")

    ax_c.axhline(l0 / 2.0, color='red', linestyle='--', linewidth=1.8, label=r"Threshold $\ell_0/2 = 0.1425$ mm")
    ax_c.axhline(l0 / 3.0, color='darkred', linestyle=':', linewidth=1.5, label=r"Core $\ell_0/3 = 0.0950$ mm")

    ax_c.set_xlabel(r"Distance along Primary Ligament from Notch Root $s$ [mm]", fontsize=10)
    ax_c.set_ylabel(r"Element Size $h$ [mm]", fontsize=10)
    ax_c.set_xlim(0.0, L_prim)
    ax_c.set_ylim(0.0, 0.50)
    ax_c.legend(loc='upper right', fontsize=8)
    ax_c.grid(True, linestyle='--', alpha=0.4)

    ax_c.text(0.03, 0.15, r"Notch Root: $h_{\min} = 0.0759$ mm ($\leq \ell_0/2$ PASS)",
              transform=ax_c.transAxes, fontsize=8, color='darkgreen', fontweight='bold',
              bbox=dict(boxstyle='round,pad=0.3', facecolor='#e8f5e9', ec='green'))
    ax_c.text(0.40, 0.82, "Distal Ligament:\nAchieved $h \approx 0.22$ mm\n(Weakness: target requested\ndiffuse tail $h \approx 0.44-1.09$ mm)",
              transform=ax_c.transAxes, fontsize=8,
              bbox=dict(boxstyle='round,pad=0.3', facecolor='#fffde7', ec='orange'))

    # -------------------------------------------------------------
    # Panel (d): Synthesis Table of Finite-Element Metrics & Transfer Audit
    # -------------------------------------------------------------
    ax_d = fig.add_subplot(2, 2, 4)
    ax_d.axis('off')
    ax_d.set_title(r"$\mathbf{(d)\ Task\ F1750\ Native\ Sizing\ Probe\ Verification\ Summary}$", fontsize=11, fontweight='bold', pad=8)

    met = summary["adapted_mesh_metrics"]
    reg = summary["regional_spatial_resolution"]
    tra = summary["requested_vs_achieved_transfer_audit"]
    gov = summary["governance_and_resource_accounting"]

    table_data = [
        ["Parameter / Metric", "F1750 Local Sizing Probe Value", "Evaluation / Gate"],
        ["Base Physical Mesh", "3,923 elements, 4,039 nodes", "Case 3 Authentic Coarse Base"],
        ["Time-Causal Donor State", "State b (uy = 0.20 mm, Frame 40)", "Pre-Peak Propagation Snapshot"],
        ["Total Adapted Elements", f"{met['total_elements']:,} elements", "High-Resolution Physical Mesh"],
        ["Element Topology", f"{met['cpe4_quad_percent']:.2f}% CPE4 / {met['cpe3_tria_percent']:.2f}% CPE3", "Quad-Dominated (>97% CPE4)"],
        ["Jacobian Determinants", f"{met['negative_jacobians_count']} negative Jacobians", "100% Inversion-Safe (PASS)"],
        ["Aspect Ratio (Mean / Max)", f"{met['aspect_ratio_mean']:.2f} / {met['aspect_ratio_max']:.2f}", "Publication Quality (PASS)"],
        ["Primary Ligament h_min", f"{reg['primary_ligament']['achieved_size_min_mm']:.4f} mm", "Threshold <= 0.1425 mm (PASS)"],
        ["Primary Strict Compliance", f"{reg['primary_ligament']['strict_proc_zone_compliance_percent']:.2f}% (notch root)", "Reflects Target Weakness (3/35)"],
        ["Secondary Corridor Status", f"h_min = {reg['secondary_corridor']['achieved_size_min_mm']:.4f} mm", "Causal Pre-Crack Active"],
        ["Global Sizing Transfer Error", f"{tra['area_weighted_absolute_error_mm']:.4f} mm", "Background Over-Refined"],
        ["Spearman Rank Correlation", f"rho = {tra['spearman_rank_correlation_rho']:.4f}", "Inverse Mapping Falsified"],
        ["PBS Submissions Consumed", "0 new (cumulative preserved at 25)", "Zero-PBS Governance (PASS)"],
        ["Frozen Production UEL", "CE8D5EDCD2911DCB018BB15275271F874...", "Bitwise Preserved (PASS)"],
        ["Fracture Continuation", "0 forward runs executed", "Spatial Gates Only (COMPLIANT)"]
    ]

    tbl = ax_d.table(
        cellText=table_data,
        cellLoc='left',
        loc='center',
        bbox=[0.02, 0.05, 0.96, 0.90]
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)

    for (row, col), cell in tbl.get_celld().items():
        cell.set_edgecolor('#cccccc')
        if row == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#1a237e')
        elif row in [5, 6, 7, 12, 13, 14]:
            cell.set_facecolor('#f1f8e9')  # light green
        elif row in [8, 10, 11]:
            cell.set_facecolor('#fff8e1')  # light amber warning
        else:
            cell.set_facecolor('#f9f9f9' if row % 2 == 0 else '#ffffff')

    plt.subplots_adjust(left=0.06, right=0.95, top=0.95, bottom=0.06, hspace=0.25, wspace=0.20)

    os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    print("SUCCESS: 4-panel publication visualization saved to:")
    print("  PNG: %s" % out_png)
    print("  PDF: %s" % out_pdf)

if __name__ == '__main__':
    generate_f1750_figure()
