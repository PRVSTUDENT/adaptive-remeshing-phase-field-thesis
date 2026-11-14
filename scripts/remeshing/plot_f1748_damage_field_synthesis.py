# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1748_damage_field_synthesis.py
Task F1748: 4-Panel Publication-Quality Visualization of Authentic Coupled Damage Fields,
Stress-Recovery Blindspot Demonstration, and Damage-Aware Sizing Synthesis.

Generates:
- results/figures/fig_f1748_damage_field_synthesis.png
- results/figures/fig_f1748_damage_field_synthesis.pdf
"""

import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PatchCollection

def plot_f1748_synthesis():
    summary_path = "results/validation/f1748_coupled_damage_availability_summary.json"
    with open(summary_path, "r", encoding="utf-8") as f:
        summary = json.load(f)

    c3_stats = summary["case3_statistics"]
    c2_stats = summary["case2_statistics"]
    scans = c3_stats["sizing_scans"]
    prim = c3_stats["along_path_primary"]
    sec = c3_stats["along_path_secondary"]

    # Set up publication figure
    fig = plt.figure(figsize=(16, 12), dpi=300)
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 14
    })

    gs = fig.add_gridspec(2, 2, hspace=0.28, wspace=0.24)

    # -------------------------------------------------------------------------
    # Panel (a): Case 3 Base Mesh & Terminal Damage Field d(x,y)
    # -------------------------------------------------------------------------
    ax_a = fig.add_subplot(gs[0, 0])
    
    # Plate geometry
    rect = patches.Rectangle((0, 0), 65, 120, linewidth=1.5, edgecolor='black', facecolor='#f5f5f7')
    ax_a.add_patch(rect)
    # Central hole
    hole = patches.Circle((36.5, 51.0), 10.0, linewidth=1.2, edgecolor='black', facecolor='white', zorder=5)
    ax_a.add_patch(hole)
    # Pins
    pin_up = patches.Circle((20.0, 100.0), 5.0, linewidth=1.0, edgecolor='black', facecolor='white', zorder=5)
    pin_lo = patches.Circle((20.0, 20.0), 5.0, linewidth=1.0, edgecolor='black', facecolor='white', zorder=5)
    ax_a.add_patch(pin_up)
    ax_a.add_patch(pin_lo)
    # Initial notch
    ax_a.plot([0, 10], [70, 70], color='red', linewidth=2.5, label='Initial notch (10 mm)', zorder=6)

    # Plot element damage centers
    c3_prim_cx = [p['cx'] for p in prim]
    c3_prim_cy = [p['cy'] for p in prim]
    c3_prim_d = [p['damage_state_e'] for p in prim]

    c3_sec_cx = [p['cx'] for p in sec]
    c3_sec_cy = [p['cy'] for p in sec]
    c3_sec_d = [p['damage_state_e'] for p in sec]

    sc1 = ax_a.scatter(c3_prim_cx, c3_prim_cy, c=c3_prim_d, cmap='plasma', s=45, vmin=0, vmax=1.0, edgecolors='k', linewidth=0.5, zorder=7)
    sc2 = ax_a.scatter(c3_sec_cx, c3_sec_cy, c=c3_sec_d, cmap='plasma', s=45, vmin=0, vmax=1.0, edgecolors='k', linewidth=0.5, zorder=7)

    # Annotate primary and secondary fracture paths
    ax_a.annotate("Primary Crack\n(Notch -> Hole)", xy=(18, 62), xytext=(2, 85),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1.0, headwidth=5),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.8))
    ax_a.annotate("Secondary Crack\n(Hole -> Boundary)", xy=(55, 51.5), xytext=(35, 30),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1.0, headwidth=5),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='orange', alpha=0.8))

    cbar_a = plt.colorbar(sc1, ax=ax_a, fraction=0.035, pad=0.03)
    cbar_a.set_label('Authentic Phase-Field Damage $d$ [-]', fontsize=10)

    ax_a.set_xlim(-2, 67)
    ax_a.set_ylim(-2, 122)
    ax_a.set_aspect('equal')
    ax_a.set_xlabel('x [mm]')
    ax_a.set_ylabel('y [mm]')
    ax_a.set_title('(a) Case 3 Geometry & Authentic Terminal Damage Field ($d$ at State e)\nDual-Corridor Fracture Localization (3,923 Base Mesh)', fontweight='bold')
    ax_a.grid(True, linestyle=':', alpha=0.5)

    # -------------------------------------------------------------------------
    # Panel (b): Along-Path Profiles: Stress Error vs Damage Field
    # -------------------------------------------------------------------------
    ax_b = fig.add_subplot(gs[0, 1])

    s_prim = [p['s_mm'] for p in prim]
    raw_eta_prim = [p['raw_stress_eta'] for p in prim]
    d_prim = [p['damage_state_e'] for p in prim]

    # Two y-axes: left = stress error, right = damage
    color_eta = '#d95f02'
    color_d = '#1b9e77'

    ax_b.set_xlabel('Along-Path Distance $s$ [mm]\nPrimary: Notch Root -> Hole | Secondary: Hole Flank -> Right Boundary')
    ax_b.set_ylabel('Normalized Continuum Stress Error $\\hat{\\eta}$ [-]', color=color_eta, fontweight='bold')
    
    # Plot primary corridor
    line1 = ax_b.plot(s_prim, raw_eta_prim, 'o-', color=color_eta, label='Stress Error $\\hat{\\eta}$ (Primary)', linewidth=1.8, markersize=5)
    
    # Threshold line
    tau_val = 0.045744
    line_tau = ax_b.axhline(tau_val, color='red', linestyle='--', linewidth=1.5, label='Background Noise Threshold $\\tau = 0.0457$')

    # Shaded barrier region (s = 4.27 to 8.74 mm)
    ax_b.axvspan(4.27, 8.74, color='red', alpha=0.15, label='Impenetrable Coarse Barrier (Span 4.47 mm)')

    ax_b_right = ax_b.twinx()
    ax_b_right.set_ylabel('Authentic Damage $d$ [-]', color=color_d, fontweight='bold')
    line2 = ax_b_right.plot(s_prim, d_prim, 's-', color=color_d, label='Phase-Field Damage $d$ (Primary)', linewidth=2.0, markersize=5)
    line_dcut = ax_b_right.axhline(0.05, color=color_d, linestyle=':', linewidth=1.5, label='Damage Refinement Cutoff $d_{\\mathrm{cut}} = 0.05$')

    ax_b.tick_params(axis='y', labelcolor=color_eta)
    ax_b_right.tick_params(axis='y', labelcolor=color_d)
    ax_b.set_yscale('log')
    ax_b.set_ylim(0.005, 20.0)
    ax_b_right.set_ylim(-0.05, 1.05)

    # Combine legends
    lines = line1 + line2 + [line_tau, line_dcut]
    labels = [l.get_label() for l in lines]
    ax_b.legend(lines, labels, loc='upper right', framealpha=0.9)

    ax_b.set_title('(b) Primary Corridor Along-Path Profile: Method A Stress Error vs Damage\nContinuum Blindspot Creates 4.47 mm Gap, While Damage Field Resolves Full Path', fontweight='bold')
    ax_b.grid(True, linestyle=':', alpha=0.5)

    # -------------------------------------------------------------------------
    # Panel (c): Sizing Prediction Curve: Element Count vs d_cut
    # -------------------------------------------------------------------------
    ax_c = fig.add_subplot(gs[1, 0])

    d_cuts = [s['d_cut'] for s in scans]
    n_elems_core = [s['predicted_elements_l0_third'] for s in scans]
    n_elems_proc = [s['predicted_elements_l0_half'] for s in scans]
    pct_suppressed = [s['suppressed_percentage'] for s in scans]

    ax_c.plot(d_cuts, n_elems_core, 'o-', color='#7570b3', linewidth=2.0, markersize=6, label='Predicted Mesh (Core $h = \\ell_0/3$)')
    ax_c.plot(d_cuts, n_elems_proc, '^--', color='#386cb0', linewidth=1.5, markersize=6, label='Predicted Mesh (Process $h = \\ell_0/2$)')

    # Literature target line
    pub_target = 12168
    ax_c.axhline(pub_target, color='black', linestyle='-', linewidth=2.0, label='Pandey & Kumar (2025) Target: 12,168 el')
    
    # 120k probe reference
    ax_c.axhline(120554, color='gray', linestyle=':', linewidth=1.2, label='F1746 Stress-Error Probe: 120,554 el')

    # Highlight optimal d_cut = 0.05
    opt_n = 12416
    ax_c.plot(0.05, opt_n, 'r*', markersize=14, label=f'Optimal $d_{{\\mathrm{{cut}}}} = 0.05$: {opt_n:,} el (2.0% deviation)', zorder=10)

    ax_c.set_xlabel('Damage Noise Cutoff Threshold $d_{\\mathrm{cut}}$ [-]')
    ax_c.set_ylabel('Total Physical Elements in Mesh [-]')
    ax_c.set_yscale('log')
    ax_c.set_ylim(4000, 160000)
    ax_c.set_title('(c) Physics-Driven Sizing Simulation vs Published Benchmark Target\nTarget 12,168 el Matched within 2.0% with 83.0% Bulk Suppression', fontweight='bold')
    ax_c.legend(loc='center right', framealpha=0.9)
    ax_c.grid(True, linestyle=':', alpha=0.5)

    # Twin axis for suppression percentage
    ax_c_tw = ax_c.twinx()
    ax_c_tw.plot(d_cuts, pct_suppressed, 'x:', color='#66a61e', linewidth=1.5, label='Bulk Suppression [%]')
    ax_c_tw.set_ylabel('Specimen Background Suppression [%]', color='#66a61e', fontweight='bold')
    ax_c_tw.tick_params(axis='y', labelcolor='#66a61e')
    ax_c_tw.set_ylim(60, 100)

    # -------------------------------------------------------------------------
    # Panel (d): Case 2 & Case 3 Field Availability & Acceptance Synthesis
    # -------------------------------------------------------------------------
    ax_d = fig.add_subplot(gs[1, 1])
    ax_d.axis('off')

    # Create formatted synthesis summary table
    table_data = [
        ["Benchmark Metric / Feature", "Case 2 (Off-Axis Hole)", "Case 3 (Notched Hole & Pins)"],
        ["Geometry & Dimensions", "1.0 x 1.0 mm square", "65 x 120 mm plate"],
        ["Characteristic Length l0", "0.0075 mm", "0.285 mm"],
        ["Physical Elements Audited", "23,965 elements", "3,923 (coarse) / 24,718 (fine)"],
        ["Converged Solution Checkpoints", "252 frames (Steps 1 & 2)", "5 key states + 3 transient"],
        ["Available Authentic Fields", "d (SDV1), H (SDV2), u, RF", "d, H, u, S, companion MISESERI"],
        ["Layer 3 Element Offset", "eid - 47,930 = phys_id", "eid - 7,846 = phys_id"],
        ["Continuum Stress Recovery (Method A)", "PASS (Single Notch/Hole)", "DEFICIENT (4.5mm Midspan Gap)"],
        ["Method A Barrier Span", "0.0 mm (no barrier)", "4.47 mm (Primary) + 4.72 mm (Sec)"],
        ["Damage Indicator Coverage (d >= 0.05)", "100% active crack coverage", "100.0% (35/35 Primary, 21/21 Sec)"],
        ["Damage Refinement Barrier Span", "0.0 mm (barrier-free)", "0.0 mm (ZERO barriers)"],
        ["Predicted Adapted Mesh Size", "23,965 el (Pub: 23,618 el)", "12,416 el (Pub: 12,168 el)"],
        ["Deviation from Published Target", "+1.47%", "+2.04%"],
        ["HPC PBS Allowance Consumed", "0 / 0 authorized", "0 / 0 authorized (Cumul: 25)"]
    ]

    table = ax_d.table(cellText=table_data, loc='center', cellLoc='left', colWidths=[0.38, 0.31, 0.31])
    table.auto_set_font_size(False)
    table.set_fontsize(8.5)
    table.scale(1.0, 1.45)

    # Style header row
    for col in range(3):
        cell = table[0, col]
        cell.set_facecolor('#2b5c8f')
        cell.set_text_props(color='white', weight='bold')

    # Highlight key rows
    for r in [7, 8, 9, 10, 11, 12, 13]:
        for c in range(3):
            cell = table[r, c]
            if r in [7, 8]:
                cell.set_facecolor('#fee8c8') # Light orange alert for Method A deficiency
            elif r in [9, 10, 11, 12]:
                cell.set_facecolor('#e5f5e0') # Light green for damage success
            elif r == 13:
                cell.set_facecolor('#f0f0f0')

    ax_d.set_title('(d) Comprehensive Cross-Benchmark Field Availability & Indicator Synthesis\nDemonstrating Superiority of Damage-Aware Sizing Across Both 2D Benchmarks', fontweight='bold')

    # Save outputs
    out_png = "results/figures/fig_f1748_damage_field_synthesis.png"
    out_pdf = "results/figures/fig_f1748_damage_field_synthesis.pdf"
    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close()

    print(f"Figure saved to {out_png} ({os.path.getsize(out_png):,} bytes)")
    print(f"Figure saved to {out_pdf} ({os.path.getsize(out_pdf):,} bytes)")

if __name__ == "__main__":
    plot_f1748_synthesis()
