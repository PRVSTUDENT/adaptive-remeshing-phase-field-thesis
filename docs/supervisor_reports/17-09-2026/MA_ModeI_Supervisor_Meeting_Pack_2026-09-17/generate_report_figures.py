#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_report_figures.py
Generates the two mandatory scientific figures for the 17-09-2026 Mode-I Supervisor Meeting Report:
1. fig1_mode1_fu_recovery.png: Clean F-u overlay with inset of initial stiffness K0
2. fig2_gate5_mesh_discrepancy_and_regions.png: Regional discretization breakdown & zone map
"""

import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge
import matplotlib.patches as mpatches

# Paths to verified curve files
BASE_DIR = r"D:\Master thesis\Adaptive remeshing"
CURVE_REF = os.path.join(BASE_DIR, r"results\pandey_kumar_mode1\master_fracture_curves\curve_standard_1398090.csv")
CURVE_NOM1 = os.path.join(BASE_DIR, r"results\pandey_kumar_mode1\master_fracture_curves\curve_1404933_extracted.csv")
CURVE_DEF = os.path.join(BASE_DIR, r"results\pandey_kumar_mode1\master_fracture_curves\curve_adaptive_1399632.csv")

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figures")
os.makedirs(OUT_DIR, exist_ok=True)

def load_csv_curve(csv_path):
    u_vals, f_vals = [], []
    if not os.path.exists(csv_path):
        print(f"Warning: {csv_path} not found.")
        return np.array([]), np.array([])
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = None
        u_col, f_col = 0, 1
        for row in reader:
            if not row or not any(c.strip() for c in row):
                continue
            if header is None:
                try:
                    float(row[0].strip())
                except ValueError:
                    header = [c.strip().lower() for c in row]
                    if 'u2_mm' in header and 'rf2_kn' in header:
                        u_col = header.index('u2_mm')
                        f_col = header.index('rf2_kn')
                    elif 'displacement_mm' in header and 'reaction_force_kn' in header:
                        u_col = header.index('displacement_mm')
                        f_col = header.index('reaction_force_kn')
                    continue
            try:
                u_vals.append(float(row[u_col]))
                f_vals.append(float(row[f_col]))
            except (ValueError, IndexError):
                continue
    paired = sorted(zip(u_vals, f_vals), key=lambda x: x[0])
    u_clean, f_clean = [], []
    for u, f in paired:
        if not u_clean or abs(u - u_clean[-1]) > 1e-12:
            u_clean.append(u)
            f_clean.append(f)
    return np.array(u_clean), np.array(f_clean)

# ==============================================================================
# FIGURE 1: Clean F-u Overlay & Stiffness Recovery
# ==============================================================================
def generate_figure_1():
    print("Generating Figure 1: Clean F-u overlay...")
    u_ref, f_ref = load_csv_curve(CURVE_REF)
    u_nom, f_nom = load_csv_curve(CURVE_NOM1)
    u_def, f_def = load_csv_curve(CURVE_DEF)

    plt.rcParams.update({
        'font.size': 11,
        'font.family': 'sans-serif',
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9.5,
        'figure.titlesize': 14
    })

    fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=300)

    # Plot lines
    # 1. Reference
    line_ref, = ax.plot(u_ref * 1000, f_ref, color='#111111', linestyle='-', linewidth=2.2,
                        label='Fixed reference (Job 1398090, 15,192 elements)\n$F_{\\max} = 0.758\\,\\mathrm{kN}$, $u = 5.86\\,\\mu\\mathrm{m}$, $K_0 = 137.95\\,\\mathrm{kN/mm}$')

    # 2. Corrected Nominal 1%
    line_nom, = ax.plot(u_nom * 1000, f_nom, color='#0066cc', linestyle='-', linewidth=2.0,
                        label='Corrected nominal 1% (Job 1404933, 71,320 elements)\n$F_{\\max} = 0.745\\,\\mathrm{kN}$, $u = 5.75\\,\\mu\\mathrm{m}$, $K_0 \\approx 137.821\\,\\mathrm{kN/mm}$')

    # 3. Defective predecessor
    line_def, = ax.plot(u_def * 1000, f_def, color='#cc2200', linestyle='--', linewidth=1.6, alpha=0.85,
                        label='DEFECTIVE N_BOTTOM PREPROCESSING (Job 1399632) -- DIAGNOSTIC ONLY\n$F_{\\max} = 0.478\\,\\mathrm{kN}$, $u = 4.15\\,\\mu\\mathrm{m}$, $K_0 \\approx 122.38\\,\\mathrm{kN/mm}$')

    # Peaks markers
    ax.plot(0.005857 * 1000, 0.757778, marker='s', color='#111111', markersize=6, zorder=5)
    ax.plot(0.005750 * 1000, 0.745325, marker='o', color='#0066cc', markersize=6, zorder=5)
    ax.plot(0.004150 * 1000, 0.478203, marker='^', color='#cc2200', markersize=6, zorder=5)

    # Annotations
    ax.annotate('Ref Peak: $F_{\\max}=0.758\\,\\mathrm{kN}$\n$u=5.86\\,\\mu\\mathrm{m}$',
                xy=(0.005857 * 1000, 0.757778), xytext=(6.5, 0.77),
                arrowprops=dict(arrowstyle='->', color='#111111', lw=1.0),
                fontsize=9.5, fontweight='bold', color='#111111',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#cccccc', alpha=0.9))

    ax.annotate('Corrected Peak: $F_{\\max}=0.745\\,\\mathrm{kN}$\n($-1.64\\%$, $u=5.75\\,\\mu\\mathrm{m}$)',
                xy=(0.005750 * 1000, 0.745325), xytext=(4.1, 0.65),
                arrowprops=dict(arrowstyle='->', color='#0066cc', lw=1.0),
                fontsize=9.5, fontweight='bold', color='#0066cc',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#99ccff', alpha=0.9))

    ax.annotate('Defective Preprocessing:\nBottom lift up to $\\approx 48.34\\%$ stroke\n$K_0 \\approx 122.38\\,\\mathrm{kN/mm}$ ($-11.3\\%$)',
                xy=(0.004150 * 1000, 0.478203), xytext=(1.8, 0.38),
                arrowprops=dict(arrowstyle='->', color='#cc2200', lw=1.0),
                fontsize=9.0, color='#cc2200',
                bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#ffcccc', alpha=0.9))

    ax.set_xlabel('Prescribed Displacement $u$ [$\\mu\\mathrm{m}$]')
    ax.set_ylabel('Total Reaction Force $F$ [kN]')
    ax.set_xlim(0.0, 7.5)
    ax.set_ylim(0.0, 0.88)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower left', framealpha=0.95, edgecolor='#cccccc')

    # INSET: Initial elastic stiffness range (u <= 1.0 um)
    ax_inset = ax.inset_axes([0.62, 0.18, 0.34, 0.34])
    mask_ref = (u_ref > 0) & (u_ref <= 0.001005)
    mask_nom = (u_nom > 0) & (u_nom <= 0.001005)
    mask_def = (u_def > 0) & (u_def <= 0.001005)

    ax_inset.plot(u_ref[mask_ref] * 1000, f_ref[mask_ref], color='#111111', lw=2.0, label='Ref ($137.95$)')
    ax_inset.plot(u_nom[mask_nom] * 1000, f_nom[mask_nom], color='#0066cc', lw=1.8, linestyle='-', label='Corr ($137.821$)')
    ax_inset.plot(u_def[mask_def] * 1000, f_def[mask_def], color='#cc2200', lw=1.5, linestyle='--', label='Def ($122.38$)')

    ax_inset.set_title(r'Elastic Range ($u \leq 1.0\,\mu\mathrm{m}$)' + '\n$K_0$ agreement: $-0.09\\%$', fontsize=9.0, fontweight='bold')
    ax_inset.set_xlabel('$u$ [$\\mu\\mathrm{m}$]', fontsize=8.0)
    ax_inset.set_ylabel('$F$ [kN]', fontsize=8.0)
    ax_inset.set_xlim(0.0, 1.0)
    ax_inset.set_ylim(0.0, 0.145)
    ax_inset.tick_params(labelsize=8)
    ax_inset.grid(True, linestyle=':', alpha=0.5)

    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, "fig1_mode1_fu_recovery.png")
    out_pdf = os.path.join(OUT_DIR, "fig1_mode1_fu_recovery.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    print(f"Saved Figure 1 to {out_png} and {out_pdf}")

# ==============================================================================
# FIGURE 2: Gate-5 Mesh Discrepancy & Regional Distribution
# ==============================================================================
def generate_figure_2():
    print("Generating Figure 2: Regional mesh breakdown & zone map...")

    plt.rcParams.update({
        'font.size': 10.5,
        'font.family': 'sans-serif',
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'figure.titlesize': 13
    })

    fig, (ax_map, ax_bar) = plt.subplots(1, 2, figsize=(11.5, 5.2), dpi=300,
                                         gridspec_kw={'width_ratios': [1.1, 1.3]})

    # -------------------------------------------------------------
    # Panel (a): 2D Spatial Schematic of the 5 Analysis Regions
    # -------------------------------------------------------------
    # Domain is [0, 1] x [0, 1] mm
    # R5 Far Field: Top (y >= 0.6) and Bottom (y <= 0.4)
    # R4 Transition: 0.4 < y < 0.6 outside corridor
    # R3 Slit Flank: x in [0, 0.5], y in [0.48, 0.52]
    # R2 Ligament: x in [0.5, 1.0], y in [0.48, 0.52]
    # R1 Crack Tip: circle r = 0.02 around (0.5, 0.5)

    # Colors
    c_r5 = '#e6f0fa'  # Light blue far field
    c_r4 = '#ffe6cc'  # Light orange transition
    c_r3 = '#e6ffcc'  # Light green slit flank
    c_r2 = '#ffcc80'  # Medium orange ligament
    c_r1 = '#d9534f'  # Red crack tip

    # Draw R5 (Far Field)
    rect_r5_top = Rectangle((0, 0.6), 1.0, 0.4, facecolor=c_r5, edgecolor='#4682b4', lw=1.0)
    rect_r5_bot = Rectangle((0, 0.0), 1.0, 0.4, facecolor=c_r5, edgecolor='#4682b4', lw=1.0)
    ax_map.add_patch(rect_r5_top)
    ax_map.add_patch(rect_r5_bot)

    # Draw R4 (Transition Zone)
    rect_r4 = Rectangle((0, 0.4), 1.0, 0.2, facecolor=c_r4, edgecolor='#e67e22', lw=1.0)
    ax_map.add_patch(rect_r4)

    # Draw R3 (Slit Flank Corridor)
    rect_r3 = Rectangle((0.0, 0.48), 0.5, 0.04, facecolor=c_r3, edgecolor='#27ae60', lw=1.0)
    ax_map.add_patch(rect_r3)

    # Draw R2 (Ligament Corridor)
    rect_r2 = Rectangle((0.5, 0.48), 0.5, 0.04, facecolor=c_r2, edgecolor='#d35400', lw=1.0)
    ax_map.add_patch(rect_r2)

    # Draw R1 (Crack Tip Zone r <= 0.02 mm)
    circ_r1 = Circle((0.5, 0.5), 0.025, facecolor=c_r1, edgecolor='#900', lw=1.5, zorder=4)
    ax_map.add_patch(circ_r1)

    # Crack slit line (a0 = 0.5 mm)
    ax_map.plot([0.0, 0.5], [0.5, 0.5], color='black', linewidth=2.8, solid_capstyle='butt', zorder=5)
    ax_map.annotate('Initial Crack Seam\n$a_0 = 0.5\\,\\mathrm{mm}$', xy=(0.25, 0.5), xytext=(0.10, 0.53),
                    fontsize=8.5, fontweight='bold', color='black',
                    arrowprops=dict(arrowstyle='->', lw=0.8, color='black'))

    # Region Labels on Map
    ax_map.text(0.5, 0.80, 'R5: Far Field Upper\n($41,986$ el in R5, $58.9\\%$)',
                ha='center', va='center', fontsize=9.0, color='#1f497d', fontweight='bold')
    ax_map.text(0.5, 0.20, 'R5: Far Field Lower',
                ha='center', va='center', fontsize=9.0, color='#1f497d', fontweight='bold')
    ax_map.text(0.5, 0.43, 'R4: Transition Zone ($20,273$ el, $28.4\\%$)',
                ha='center', va='center', fontsize=8.5, color='#b35900', fontweight='bold')
    ax_map.text(0.75, 0.50, 'R2: Ligament\n($5,318$ el)',
                ha='center', va='center', fontsize=8.0, color='#803300', fontweight='bold')
    ax_map.text(0.18, 0.46, 'R3: Flank ($3,396$ el)',
                ha='center', va='center', fontsize=8.0, color='#1e6b37')

    # Crack tip pointer
    ax_map.annotate('R1: Crack Tip\n($347$ el, $0.5\\%$)', xy=(0.5, 0.5), xytext=(0.55, 0.65),
                    arrowprops=dict(arrowstyle='->', lw=1.0, color='#900'),
                    fontsize=8.5, fontweight='bold', color='#900',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#900', alpha=0.9))

    # Boundary conditions annotations
    ax_map.text(0.5, 1.02, 'Prescribed Tension $u_y = u$, $u_x = 0$', ha='center', va='bottom', fontsize=8.5, color='black')
    ax_map.text(0.5, -0.02, 'Roller Support $u_y = 0$ (Pin at origin $u_x=0$)', ha='center', va='top', fontsize=8.5, color='black')

    ax_map.set_xlim(-0.05, 1.05)
    ax_map.set_ylim(-0.08, 1.08)
    ax_map.set_aspect('equal')
    ax_map.set_xlabel('$x$ Coordinate [mm]')
    ax_map.set_ylabel('$y$ Coordinate [mm]')
    ax_map.set_title('(a) Mode-I Regional Partition (Reconstruction Analysis)', fontweight='bold')
    ax_map.grid(True, linestyle=':', alpha=0.4)

    # -------------------------------------------------------------
    # Panel (b): Element Count Comparison & Breakdown
    # -------------------------------------------------------------
    regions = [
        (r'R1: Crack Tip ($r \leq 0.02$)', 347, c_r1, '0.49%'),
        ('R2: Ligament Corridor', 5318, c_r2, '7.46%'),
        ('R3: Slit Flank', 3396, c_r3, '4.76%'),
        ('R4: Transition Zone', 20273, c_r4, '28.42%'),
        ('R5: Far Field', 41986, c_r5, '58.87%'),
    ]

    # Stacked bar comparison:
    # Bar 1: Pandey & Kumar (2025) reported: ~13,941 elements
    # Bar 2: Verified Literal 1% Reconstruction: 71,320 elements
    bar_width = 0.55
    x_positions = [0.8, 1.8]

    # Bar 1: Published ~13,941 (Unpartitioned in literature)
    ax_bar.bar(x_positions[0], 13941, width=bar_width, color='#95a5a6', edgecolor='#555555',
               linewidth=1.2, label='Published Target (~13,941 total)')
    ax_bar.text(x_positions[0], 13941 / 2, 'Pandey & Kumar\n(2025)\n~13,941 finite elements\n(Regional split unstated)',
                ha='center', va='center', fontsize=9.0, fontweight='bold', color='#222222')
    ax_bar.text(x_positions[0], 13941 + 1200, '~13,941', ha='center', va='bottom', fontsize=10.0, fontweight='bold')

    # Bar 2: Stacked breakdown for 71,320
    bottom = 0
    legend_patches = []
    for name, count, col, pct in regions:
        b = ax_bar.bar(x_positions[1], count, bottom=bottom, width=bar_width,
                       color=col, edgecolor='#555555', linewidth=0.8)
        # Add text label if segment is large enough
        if count > 4000:
            ax_bar.text(x_positions[1], bottom + count / 2, f'{name.split(":")[0]}: {count:,}\n({pct})',
                        ha='center', va='center', fontsize=8.5, fontweight='bold',
                        color='#111111' if col != c_r1 else 'white')
        bottom += count

    ax_bar.text(x_positions[1], 71320 + 1200, '71,320', ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='#004488')

    # Annotation of regional distribution
    ax_bar.annotate('Regional Distribution (71,320 Mesh):\nFar Field (R5: $41,986$, $58.9\\%$)\n& Transition (R4: $20,273$, $28.4\\%$)\n$\\mathbf{87.3\\%}$ located outside crack corridor',
                    xy=(x_positions[1] + bar_width/2, 45000), xytext=(x_positions[1] + 0.45, 48000),
                    arrowprops=dict(arrowstyle='->', lw=1.2, color='#004488'),
                    fontsize=8.5, fontweight='bold', color='#004488',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='#f0f8ff', edgecolor='#004488', alpha=0.95))

    # Fracture zone bracket
    ax_bar.annotate('Process Zone (R1+R2+R3)\n$= 9,061$ elements ($12.7\\%$)',
                    xy=(x_positions[1] - bar_width/2, 4500), xytext=(x_positions[0] + 0.35, 3000),
                    arrowprops=dict(arrowstyle='->', lw=1.0, color='#803300'),
                    fontsize=8.5, color='#803300', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#803300', alpha=0.9))

    ax_bar.set_xticks(x_positions)
    ax_bar.set_xticklabels(['Literature\nReference', 'Literal 1% Native\nReconstruction'], fontsize=10.0, fontweight='bold')
    ax_bar.set_ylabel('Number of Finite Elements')
    ax_bar.set_ylim(0, 80000)
    ax_bar.set_xlim(0.2, 2.7)
    ax_bar.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: f'{int(x):,}'))
    ax_bar.set_title('(b) 71,320 Reconstruction Regional Distribution', fontweight='bold')
    ax_bar.grid(True, linestyle=':', alpha=0.5, axis='y')

    plt.tight_layout()
    out_png = os.path.join(OUT_DIR, "fig2_gate5_mesh_discrepancy_and_regions.png")
    out_pdf = os.path.join(OUT_DIR, "fig2_gate5_mesh_discrepancy_and_regions.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    print(f"Saved Figure 2 to {out_png} and {out_pdf}")

if __name__ == '__main__':
    generate_figure_1()
    generate_figure_2()
    print("All figures successfully generated.")
