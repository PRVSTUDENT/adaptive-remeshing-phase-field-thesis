# -*- coding: utf-8 -*-
"""
plot_f1755_feasibility.py
Task F1755: Case 2 Method A Indicator-Driven Distal Mesh Feasibility
Generates a publication-quality 4-panel diagnostic figure:
(a) Secondary ligament element sizing profile along x
(b) Elastic stress concentration Kt(x) and error indicator decay
(c) Global element count vs error target trade-off
(d) Indicator information admissibility & causality matrix
"""

import os
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def main():
    base_dir = r"D:\Master thesis\Adaptive remeshing"
    feas_json_path = os.path.join(base_dir, "results", "validation", "f1755_case2_distal_mesh_feasibility.json")
    out_png_path = os.path.join(base_dir, "results", "figures", "fig_f1755_distal_mesh_feasibility.png")
    out_pdf_path = os.path.join(base_dir, "results", "figures", "fig_f1755_distal_mesh_feasibility.pdf")
    
    with open(feas_json_path, 'r') as f:
        data = json.load(f)
        
    bins = data['secondary_ligament_spatial_bins']
    stress = data['elastic_stress_concentration_decay']
    tradeoff = data['global_over_refinement_tradeoff']
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 13))
    plt.subplots_adjust(wspace=0.28, hspace=0.32)
    
    # -------------------------------------------------------------
    # Panel (a): Secondary Ligament Sizing Profile Along x
    # -------------------------------------------------------------
    ax = axes[0, 0]
    
    x_centers = [0.5 * (b['x_range'][0] + b['x_range'][1]) for b in bins]
    h_means = [b['h_mean_um'] for b in bins]
    h_maxs = [b['h_max_um'] for b in bins]
    h_mins = [b['h_min_um'] for b in bins]
    compliances = [b['compliance_pct'] for b in bins]
    
    ax.plot(x_centers, h_means, 'b-o', lw=2.5, ms=8, label='Mean Element Size $h_{\\mathrm{mean}}$')
    ax.fill_between(x_centers, h_mins, h_maxs, color='blue', alpha=0.15, label='Min-Max Size Span $[h_{\\min}, h_{\\max}]$')
    
    # Process-zone threshold line l0/2 = 3.75 um
    ax.axhline(3.75, color='red', linestyle='--', lw=2, label=r'Reference Target $\ell_0/2 = 3.75\,\mu\mathrm{m}$')
    
    # Highlight divergence cluster zone (x in [0.90, 0.95])
    ax.axvspan(0.90, 0.95, color='salmon', alpha=0.25, label='Divergence Zone (Nodes 8056, 7317, 6972)')
    
    # Secondary axis for compliance percentage
    ax2 = ax.twinx()
    ax2.plot(x_centers, compliances, 'g--s', lw=2, ms=7, label=r'% Compliant ($h \leq \ell_0/2$)')
    ax2.set_ylabel(r'Area Compliance with $h \leq \ell_0/2$ [%]', color='green', fontsize=11)
    ax2.tick_params(axis='y', labelcolor='green')
    ax2.set_ylim([-5, 105])
    
    ax.set_title('(a) Secondary Ligament Sizing Profile along $x$', fontsize=12, fontweight='bold')
    ax.set_xlabel('Ligament Coordinate $x$ [mm] (from Hole Flank to Boundary)', fontsize=11)
    ax.set_ylabel(r'Element Sizing $h = \sqrt{A}$ [$\mu$m]', color='blue', fontsize=11)
    ax.tick_params(axis='y', labelcolor='blue')
    ax.set_xlim([0.74, 1.01])
    ax.set_ylim([0, 11])
    ax.grid(True, linestyle='--', alpha=0.5)
    
    lines_1, labels_1 = ax.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', fontsize=8.8)
    
    # -------------------------------------------------------------
    # Panel (b): Elastic Stress Concentration & Error Indicator Decay
    # -------------------------------------------------------------
    ax = axes[0, 1]
    
    x_stress = [s['x'] for s in stress]
    kt_vals = [s['stress_concentration_kt'] for s in stress]
    eta_vals = [s['relative_error_indicator_eta'] for s in stress]
    
    ax.plot(x_stress, kt_vals, 'k-o', lw=2.5, ms=8, label=r'Kirsch Stress Concentration $K_t = \sigma_{yy}/\sigma_0$')
    ax.axhline(1.0, color='gray', linestyle=':', lw=1.5, label='Uniform Far-Field Tension ($K_t = 1.0$)')
    
    ax_eta = ax.twinx()
    ax_eta.plot(x_stress, eta_vals, 'm--^', lw=2.2, ms=8, label=r'Relative Stress Error Indicator $\eta_e / \eta_{\max}$')
    ax_eta.axhline(0.02, color='crimson', linestyle='-.', lw=1.5, label='Background Far-Field Bulk Noise Threshold (~2%)')
    ax_eta.set_ylabel(r'Relative Error Indicator $\eta_e / \eta_{\max}$ [$-$]', color='purple', fontsize=11)
    ax_eta.tick_params(axis='y', labelcolor='purple')
    ax_eta.set_ylim([0, 1.1])
    
    ax.set_title('(b) Elastic Stress Concentration $K_t$ & Error Indicator Decay', fontsize=12, fontweight='bold')
    ax.set_xlabel('Coordinate $x$ [mm] along Ligament ($y = 0.65$ mm)', fontsize=11)
    ax.set_ylabel(r'Stress Concentration Factor $K_t$ [$-$]', color='black', fontsize=11)
    ax.set_xlim([0.74, 1.01])
    ax.set_ylim([0.8, 3.2])
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Annotate decay
    ax.annotate(r'Indicator drops by 98%:' + '\n' + r'Cannot distinguish distal ligament' + '\n' + r'from bulk noise at $x \geq 0.90$',
                xy=(0.91, 1.12), xytext=(0.82, 2.2),
                arrowprops=dict(arrowstyle="->", color="darkred", lw=1.5),
                fontsize=9.5, fontweight='bold', color='darkred',
                bbox=dict(boxstyle="round,pad=0.4", fc="yellow", alpha=0.3, ec="red"))
    
    lines_b1, labels_b1 = ax.get_legend_handles_labels()
    lines_b2, labels_b2 = ax_eta.get_legend_handles_labels()
    ax.legend(lines_b1 + lines_b2, labels_b1 + labels_b2, loc='upper right', fontsize=8.8)
    
    # -------------------------------------------------------------
    # Panel (c): Global Over-Refinement Trade-Off
    # -------------------------------------------------------------
    ax = axes[1, 0]
    
    targets = [t['error_target_pct'] for t in tradeoff]
    elem_counts = [t['total_physical_elements'] for t in tradeoff]
    distal_comps = [t['distal_ligament_compliance_pct'] for t in tradeoff]
    
    bar_width = 0.35
    indices = np.arange(len(tradeoff))
    
    bars1 = ax.bar(indices - bar_width/2.0, [e/1e3 for e in elem_counts], width=bar_width, color='navy', alpha=0.8, ec='black', label='Total Elements [$10^3$]')
    
    ax_comp = ax.twinx()
    bars2 = ax_comp.bar(indices + bar_width/2.0, distal_comps, width=bar_width, color='forestgreen', alpha=0.8, ec='black', label='Distal Ligament Compliance [%]')
    ax_comp.set_ylabel('Ligament Area Compliance [%]', color='forestgreen', fontsize=11)
    ax_comp.tick_params(axis='y', labelcolor='forestgreen')
    ax_comp.set_ylim([0, 115])
    
    ax.set_title('(c) Far-Field Mesh Explosion vs Error Target Trade-Off', fontsize=12, fontweight='bold')
    ax.set_xticks(indices)
    ax.set_xticklabels([r'Baseline (2.30%)' + '\n' + r'Job 1423266',
                        r'Calibrated (1.00%)' + '\n' + r'Partial Outer',
                        r'Global Outer (0.50%)' + '\n' + r'Full Compliance'], fontsize=9.5)
    ax.set_ylabel(r'Total Physical Elements [$10^3$]', color='navy', fontsize=11)
    ax.tick_params(axis='y', labelcolor='navy')
    ax.set_ylim([0, 140])
    ax.grid(True, linestyle='--', alpha=0.5, axis='y')
    
    # Add labels on bars
    for bar in bars1:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f'{int(yval)}k el', ha='center', va='bottom', fontsize=9, fontweight='bold', color='navy')
    for bar in bars2:
        yval = bar.get_height()
        ax_comp.text(bar.get_x() + bar.get_width()/2.0, yval + 2, f'{yval:.1f}%', ha='center', va='bottom', fontsize=9, fontweight='bold', color='forestgreen')
        
    # Annotate explosion
    ax.annotate(r'5x Element Explosion (~118k el):' + '\n' + r'Destroys adaptive efficiency',
                xy=(indices[2] - bar_width/2.0, 118.4), xytext=(0.8, 105),
                arrowprops=dict(arrowstyle="->", color="red", lw=1.5),
                fontsize=9.5, fontweight='bold', color='red',
                bbox=dict(boxstyle="round,pad=0.3", fc="mistyrose", ec="red"))
    
    # -------------------------------------------------------------
    # Panel (d): Information Admissibility & Causality Matrix
    # -------------------------------------------------------------
    ax = axes[1, 1]
    
    sources = [
        '1. Admissible Pre-Analysis Indicator\n(Linear-Elastic MISESERI, $u_y \\leq 0.005$ mm)',
        '2. Global Error Target Reduction\n(UNIFORM_ERROR $\\leq 0.50$%)',
        '3. Post-Breach Coupled Field (Oracle)\n(Damage $d > 0$ after hole breach)',
        '4. Geometric Corridor Override\n(Manual seed at $x \\in [0.75, 1.0]$)'
    ]
    
    y_pos = np.arange(len(sources))
    status_scores = [7.5, 3.0, 1.5, 0.5]
    colors = ['royalblue', 'darkorange', 'crimson', 'gray']
    
    evaluations = [
        'PHYSICALLY ADMISSIBLE | Fails Outer Distal Zone (Decays to Noise)',
        'DISQUALIFIED | Explodes Mesh to ~118k Elements (Loses Adaptivity)',
        'DISQUALIFIED | Violates Causality (Inadmissible Future Leakage)',
        'DISQUALIFIED | Violates Method A (Prohibited Manual Bias)'
    ]
    
    bars = ax.barh(y_pos, status_scores, align='center', color=colors, alpha=0.85, ec='black', lw=1.2)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(sources, fontsize=9.2, fontweight='bold')
    ax.invert_yaxis()
    
    for i, (bar, ev) in enumerate(zip(bars, evaluations)):
        ax.text(0.15, bar.get_y() + bar.get_height()/2.0, ev,
                va='center', ha='left', color='white', fontweight='bold', fontsize=8.8)
        
    ax.set_title('(d) Refinement Source Admissibility & Feasibility Determination', fontsize=12, fontweight='bold')
    ax.set_xlabel('Scientific Feasibility & Integrity Score (0 = Prohibited, 10 = Ideal)', fontsize=11)
    ax.set_xlim([0, 10])
    ax.grid(True, linestyle='--', alpha=0.5, axis='x')
    
    plt.tight_layout()
    plt.savefig(out_png_path, dpi=300)
    plt.savefig(out_pdf_path)
    plt.close()
    print("Saved publication figure to:")
    print("  %s" % out_png_path)
    print("  %s" % out_pdf_path)

if __name__ == '__main__':
    main()
