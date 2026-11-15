# -*- coding: utf-8 -*-
"""
plot_f1785_scientific_synthesis.py
Generates the publication-grade comprehensive 4-panel scientific synthesis
for Task F1785 across all four Pandey-Kumar benchmark cases (Cases 1, 2, 3, 5).
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
    
    cases = ['Case 1\n(Mode-I Edge Crack)', 'Case 2\n(Off-Axis Hole)', 'Case 3\n(Pins & Hole)', 'Case 5\n(Seven Holes)']
    
    # -------------------------------------------------------------------------
    # Panel (a): Element Count Parity & Efficiency Savings vs Baselines
    # -------------------------------------------------------------------------
    ax = axs[0, 0]
    uniform_ref = [62500, 133000, 52000, 48000] # Reference uniform fine or initial equivalent
    literature_or_initial = [20232, 28000, 12170, 15714] # Published literature / predecessor baseline
    adapted_opt = [16597, 32983, 10064, 15466] # F1780/F1784 qualified adapted meshes
    
    x = np.arange(len(cases))
    width = 0.26
    
    rects1 = ax.bar(x - width, [v / 1000.0 for v in uniform_ref], width, label='Uniform Reference (Fine)', color='#b0bec5', edgecolor='#37474f', hatch='///')
    rects2 = ax.bar(x, [v / 1000.0 for v in literature_or_initial], width, label='Literature / Baseline (P&K 2025)', color='#64b5f6', edgecolor='#0d47a1')
    rects3 = ax.bar(x + width, [v / 1000.0 for v in adapted_opt], width, label='Qualified Adapted Mesh (Method A)', color='#2e7d32', edgecolor='#1b5e20')
    
    ax.set_ylabel('Element Count ($10^3$ Elements)', fontsize=11, fontweight='bold')
    ax.set_title('(a) Discretization Efficiency vs Reference Baselines', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=9.5)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 150)
    
    # Annotate savings percentages
    for i in range(len(cases)):
        sav = (1.0 - adapted_opt[i] / uniform_ref[i]) * 100.0
        ax.annotate(f'-{sav:.1f}%\nvs unif', 
                    xy=(x[i] + width, adapted_opt[i] / 1000.0 + 3), 
                    ha='center', fontsize=8, fontweight='bold', color='#1b5e20')

    # -------------------------------------------------------------------------
    # Panel (b): Mesh Quality & Topology (Quad Dominance and Aspect Ratio)
    # -------------------------------------------------------------------------
    ax = axs[0, 1]
    quad_pcts = [97.30, 96.96, 96.40, 97.90]
    max_ars = [2.55, 2.66, 3.09, 2.37]
    min_dets = [8.23e-7, 1.04e-7, 1.25e-3, 3.92e-7]
    
    color_bar = '#1565c0'
    color_line = '#d84315'
    
    ax2 = ax.twinx()
    b1 = ax.bar(x - 0.15, quad_pcts, width=0.3, label='Quad Fraction (%)', color=color_bar, edgecolor='#0d47a1')
    l1 = ax2.plot(x + 0.15, max_ars, 'o--', color=color_line, linewidth=2.2, markersize=8, label='Max Aspect Ratio')
    
    ax.set_ylabel('Quadrilateral Element Fraction (%)', fontsize=11, fontweight='bold', color=color_bar)
    ax2.set_ylabel('Maximum Aspect Ratio (Target $\\leq 4.0$)', fontsize=11, fontweight='bold', color=color_line)
    ax.set_title('(b) Topological Quality & Aspect Ratio Bounds', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=9.5)
    ax.set_ylim(85, 102)
    ax2.set_ylim(1.5, 4.5)
    ax2.axhline(4.0, color='#b71c1c', linestyle=':', linewidth=1.5, label='AR Quality Limit (4.0)')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Combine legends
    lines, labels = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines + lines2, labels + labels2, loc='lower right', fontsize=8.5, frameon=True, facecolor='#f5f5f5')

    # -------------------------------------------------------------------------
    # Panel (c): Critical Crack Corridor Physical Resolution Compliance
    # -------------------------------------------------------------------------
    ax = axs[1, 0]
    compliance_l0 = [100.0, 100.0, 100.0, 100.0]
    compliance_l0_half = [75.0, 100.0, 100.0, 100.0]
    
    b_l0 = ax.bar(x - 0.15, compliance_l0, width=0.28, label='Corridor Resolution $h \\leq \\ell_0$ (100%)', color='#00897b', edgecolor='#004d40')
    b_l0h = ax.bar(x + 0.15, compliance_l0_half, width=0.28, label='Critical Core Resolution $h \\leq \\ell_0/2$', color='#fdd835', edgecolor='#f57f17', hatch='..')
    
    ax.set_ylabel('Corridor Resolution Compliance (%)', fontsize=11, fontweight='bold')
    ax.set_title('(c) Critical Crack Zone Physical Resolution ($h \\leq \\ell_0$ & $h \\leq \\ell_0/2$)', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases, fontsize=9.5)
    ax.set_ylim(0, 120)
    ax.axhline(100.0, color='#37474f', linestyle='--', alpha=0.6)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='lower right', fontsize=8.5, frameon=True, facecolor='#f5f5f5')
    
    for i in range(len(cases)):
        ax.annotate(f"{compliance_l0[i]:.0f}%", xy=(x[i] - 0.15, compliance_l0[i] + 2), ha='center', fontsize=8, fontweight='bold')
        ax.annotate(f"{compliance_l0_half[i]:.0f}%", xy=(x[i] + 0.15, compliance_l0_half[i] + 2), ha='center', fontsize=8, fontweight='bold')

    # -------------------------------------------------------------------------
    # Panel (d): Test B Controlled Adaptivity Proof (Element Density Migration)
    # -------------------------------------------------------------------------
    ax = axs[1, 1]
    
    windows = ['Horizontal Window\n($y \\in [0.45, 0.55]$)', 'Diagonal Window\n($y \\in [0.75, 0.90]$)']
    x_w = np.arange(len(windows))
    
    h_donor_el = [67, 90]
    d_donor_el = [59, 474]
    
    h_donor_size = [15.25, 15.90]
    d_donor_size = [15.89, 6.18]
    
    bar_w = 0.30
    rect_h = ax.bar(x_w - bar_w/2, h_donor_el, bar_w, label='Mesh 1: Horizontal Donor Indicator', color='#7e57c2', edgecolor='#4527a0')
    rect_d = ax.bar(x_w + bar_w/2, d_donor_el, bar_w, label='Mesh 2: Rising Diagonal Donor Indicator', color='#e91e63', edgecolor='#880e4f')
    
    ax.set_ylabel('Inspection Window Element Count', fontsize=11, fontweight='bold')
    ax.set_title('(d) Test B Controlled Adaptivity: Dynamic Element Migration', fontsize=12, fontweight='bold', pad=10)
    ax.set_xticks(x_w)
    ax.set_xticklabels(windows, fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 560)
    ax.legend(loc='upper left', fontsize=8.5, frameon=True, facecolor='#f5f5f5')
    
    # Annotate surge
    ax.annotate('+426.7% Density Surge\n($h$ drops: 15.90 $\\to$ 6.18 $\\mu$m)',
                xy=(x_w[1] + bar_w/2, 474), xytext=(x_w[1] + 0.05, 515),
                ha='center', fontsize=8.5, fontweight='bold', color='#880e4f',
                arrowprops=dict(facecolor='#880e4f', shrink=0.08, width=1.5, headwidth=6))
    
    ax.annotate('Coarsens\n(67 $\\to$ 59 el)',
                xy=(x_w[0] + bar_w/2, 59), xytext=(x_w[0] + 0.2, 120),
                ha='center', fontsize=8, color='#4527a0',
                arrowprops=dict(facecolor='#4527a0', shrink=0.08, width=1, headwidth=4))

    out_png = os.path.join(output_dir, 'fig_f1785_four_benchmark_scientific_synthesis.png')
    out_pdf = os.path.join(output_dir, 'fig_f1785_four_benchmark_scientific_synthesis.pdf')
    
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close()
    
    print(f"Generated: {out_png}")
    print(f"Generated: {out_pdf}")

if __name__ == '__main__':
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    out_dir = os.path.join(repo_root, 'results', 'figures')
    generate_synthesis_figure(out_dir)
