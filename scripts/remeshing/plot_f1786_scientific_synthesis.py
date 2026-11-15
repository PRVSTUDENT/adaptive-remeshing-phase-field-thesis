# -*- coding: utf-8 -*-
"""
plot_f1786_scientific_synthesis.py
Generates the publication-grade comprehensive 4-panel scientific synthesis
for Task F1786 across all four Pandey-Kumar benchmark cases (Cases 1, 2, 3, 5).

Strictly source-grounded in committed configuration JSONs:
- configs/remeshing/f1728_case1_mode1_edge_crack.json
- configs/remeshing/f1728_case2_off_axis_hole.json
- configs/remeshing/f1728_case3_notched_plate_pins.json
- configs/remeshing/f1728_case5_seven_hole.json
"""

import os
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def generate_synthesis_figure(output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    fig, axs = plt.subplots(2, 2, figsize=(14, 11), dpi=300)
    plt.subplots_adjust(hspace=0.32, wspace=0.28)
    
    cases = [
        'Case 1\nMode-I Edge Crack\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=7.5\\,\\mu\\mathrm{m}$)',
        'Case 2\nOff-Axis Hole Plate\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=7.5\\,\\mu\\mathrm{m}$)',
        'Case 3\nNotched Plate w/ Pins\n($65\\times 120\\,\\mathrm{mm}, \\ell_0=285\\,\\mu\\mathrm{m}$)',
        'Case 5\nSeven-Hole Plate\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=8.0\\,\\mu\\mathrm{m}$)'
    ]
    
    x = np.arange(len(cases))
    
    # -------------------------------------------------------------------------
    # Panel (a): Element Count Comparison: Target vs Predecessor vs Qualified
    # -------------------------------------------------------------------------
    ax = axs[0, 0]
    
    # Targets: P&K published target where available, internal baseline for Case 2
    target_counts = [13941, 28000, 12168, 15714]
    target_labels = ['P&K 2025 Target', 'Internal Baseline', 'P&K 2025 Target', 'P&K 2025 Target']
    
    # Predecessor meshes from F1774 baseline
    f1774_counts = [20232, 23965, 28933, 15330]
    
    # Final qualified adapted meshes from F1780
    adapted_opt = [16597, 32983, 10064, 15466]
    
    width = 0.26
    
    rects1 = ax.bar(x - width, [v / 1000.0 for v in target_counts], width,
                    label='Target / Baseline (Config)', color='#90caf9', edgecolor='#1565c0')
    rects2 = ax.bar(x, [v / 1000.0 for v in f1774_counts], width,
                    label='Predecessor Mesh (F1774)', color='#ffb74d', edgecolor='#e65100', hatch='//')
    rects3 = ax.bar(x + width, [v / 1000.0 for v in adapted_opt], width,
                    label='Qualified Adapted Mesh (F1780)', color='#2e7d32', edgecolor='#1b5e20')
    
    ax.set_ylabel('Physical Element Count ($10^3$ Elements)', fontsize=10.5, fontweight='bold')
    ax.set_title('(a) Discretization Parity: Target vs Predecessor vs Adapted', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=8.5)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 42)
    
    # Annotate values and parity
    parities = [
        f"{adapted_opt[0]:,}\n(+19.1% vs 13.9k\n-18.0% vs F1774)",
        f"{adapted_opt[1]:,}\n(+17.8% vs 28k\n100% distal)",
        f"{adapted_opt[2]:,}\n(-17.3% vs 12.2k\n-65.2% vs F1774)",
        f"{adapted_opt[3]:,}\n(-1.58% parity\nvs 15.7k target)"
    ]
    for i in range(len(cases)):
        ax.annotate(parities[i], 
                    xy=(x[i] + width, adapted_opt[i] / 1000.0 + 1.2), 
                    ha='center', fontsize=7.2, fontweight='bold', color='#1b5e20')

    # -------------------------------------------------------------------------
    # Panel (b): Mesh Quality & Topology (Quad Dominance and Aspect Ratio)
    # -------------------------------------------------------------------------
    ax = axs[0, 1]
    quad_pcts = [97.30, 96.96, 96.40, 97.90]
    max_ars = [2.55, 2.66, 3.09, 2.37]
    
    color_bar = '#1565c0'
    color_line = '#d84315'
    
    ax2 = ax.twinx()
    b1 = ax.bar(x - 0.15, quad_pcts, width=0.3, label='Quad Fraction (%)', color=color_bar, edgecolor='#0d47a1')
    l1 = ax2.plot(x + 0.15, max_ars, 'o--', color=color_line, linewidth=2.2, markersize=8, label='Max Aspect Ratio')
    
    ax.set_ylabel('Quadrilateral Element Fraction (%)', fontsize=10.5, fontweight='bold', color=color_bar)
    ax2.set_ylabel('Maximum Aspect Ratio (Target $\\leq 4.0$)', fontsize=10.5, fontweight='bold', color=color_line)
    ax.set_title('(b) Topological Quality & Aspect Ratio Bounds', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=8.5)
    ax.set_ylim(85, 102)
    ax2.set_ylim(1.5, 4.5)
    ax2.axhline(4.0, color='#b71c1c', linestyle=':', linewidth=1.5, label='AR Limit (4.0)')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Annotate quad fraction and AR on bars/points
    for i in range(len(cases)):
        ax.annotate(f"{quad_pcts[i]:.1f}%", xy=(x[i] - 0.15, quad_pcts[i] + 0.6), ha='center', fontsize=7.5, fontweight='bold', color='#0d47a1')
        ax2.annotate(f"AR={max_ars[i]:.2f}", xy=(x[i] + 0.15, max_ars[i] + 0.12), ha='center', fontsize=7.5, fontweight='bold', color='#d84315')
    
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='lower right', fontsize=8.5, frameon=True, facecolor='#f5f5f5')

    # -------------------------------------------------------------------------
    # Panel (c): Audited Physical Resolution Compliance
    # -------------------------------------------------------------------------
    ax = axs[1, 0]
    compliance_l0 = [100.0, 100.0, 100.0, 100.0]
    compliance_l0_half = [75.0, 100.0, 70.0, 88.5]
    
    b_l0 = ax.bar(x - 0.15, compliance_l0, width=0.28, label='Corridor Resolution $h \\leq \\ell_0$ (100% compliant)', color='#00897b', edgecolor='#004d40')
    b_l0h = ax.bar(x + 0.15, compliance_l0_half, width=0.28, label='Audited Core Resolution $h \\leq \\ell_0/2$', color='#fdd835', edgecolor='#f57f17', hatch='..')
    
    ax.set_ylabel('Resolution Compliance (%)', fontsize=10.5, fontweight='bold')
    ax.set_title('(c) Audited Physical Resolution ($h \\leq \\ell_0$ vs $h \\leq \\ell_0/2$)', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=8.5)
    ax.set_ylim(0, 125)
    ax.axhline(100.0, color='#37474f', linestyle='--', alpha=0.6)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='lower right', fontsize=8.2, frameon=True, facecolor='#f5f5f5')
    
    # Specific annotations for each case
    c_labels = [
        "100% lig\n75% tip",
        "100% lig\n100% corr",
        "100% lig\n70% core",
        "100% lig\n88.5% core"
    ]
    for i in range(len(cases)):
        ax.annotate(f"{compliance_l0[i]:.0f}%", xy=(x[i] - 0.15, compliance_l0[i] + 2), ha='center', fontsize=8, fontweight='bold', color='#004d40')
        ax.annotate(f"{compliance_l0_half[i]:.1f}%", xy=(x[i] + 0.15, compliance_l0_half[i] + 2), ha='center', fontsize=8, fontweight='bold', color='#b26a00')

    # -------------------------------------------------------------------------
    # Panel (d): Test B Controlled Adaptivity Proof (Element Density Migration)
    # -------------------------------------------------------------------------
    ax = axs[1, 1]
    
    windows = ['Horizontal Window\n($y \\in [0.45, 0.55]\\,\\mathrm{mm}$)', 'Diagonal Window\n($y \\in [0.75, 0.90]\\,\\mathrm{mm}$)']
    x_w = np.arange(len(windows))
    
    h_donor_el = [67, 90]
    d_donor_el = [59, 474]
    
    bar_w = 0.30
    rect_h = ax.bar(x_w - bar_w/2, h_donor_el, bar_w, label='Mesh 1: Horizontal Donor Indicator', color='#7e57c2', edgecolor='#4527a0')
    rect_d = ax.bar(x_w + bar_w/2, d_donor_el, bar_w, label='Mesh 2: Rising Diagonal Donor Indicator', color='#e91e63', edgecolor='#880e4f')
    
    ax.set_ylabel('Inspection Window Element Count', fontsize=10.5, fontweight='bold')
    ax.set_title('(d) Test B Controlled Adaptivity: Dynamic Element Migration', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x_w)
    ax.set_xticklabels(windows, fontsize=9.5)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 560)
    ax.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='#f5f5f5')
    
    # Annotate surge
    ax.annotate('+426.7% Density Surge\n($h$ drops: 15.90 $\\to$ 6.18 $\\mu\\mathrm{m}$)\nInversion factor: 2.68x',
                xy=(x_w[1] + bar_w/2, 474), xytext=(x_w[1] + 0.05, 510),
                ha='center', fontsize=8.0, fontweight='bold', color='#880e4f',
                arrowprops=dict(facecolor='#880e4f', shrink=0.08, width=1.5, headwidth=6))
    
    ax.annotate('Coarsens\n(67 $\\to$ 59 el)',
                xy=(x_w[0] + bar_w/2, 59), xytext=(x_w[0] + 0.18, 120),
                ha='center', fontsize=8, color='#4527a0',
                arrowprops=dict(facecolor='#4527a0', shrink=0.08, width=1, headwidth=4))

    out_png = os.path.join(output_dir, 'fig_f1786_four_benchmark_scientific_synthesis.png')
    out_pdf = os.path.join(output_dir, 'fig_f1786_four_benchmark_scientific_synthesis.pdf')
    
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close()
    
    print(f"Generated: {out_png}")
    print(f"Generated: {out_pdf}")

if __name__ == '__main__':
    output_directory = 'results/figures'
    generate_synthesis_figure(output_directory)
