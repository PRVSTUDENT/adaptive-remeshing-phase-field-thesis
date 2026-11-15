# -*- coding: utf-8 -*-
"""
plot_f1756_authentic_indicator_evidence.py
===========================================
Generates publication-quality 4-panel visualization for Task F1756:
Case 2 Method A Authentic Indicator & Sizing Evidence Evaluation.

Panels:
(a) Authentic Abaqus Donor MISESERI Spatial Profile & Kirsch Stress Gradient Decay
(b) Count-Weighted vs Area-Weighted Mesh-Size Compliance (h <= l0/2 = 3.75 um)
(c) Mesh Sizing Scenarios: Verified Generated Meshes vs Unexecuted Analytical Projections
(d) Pre-Analysis Indicator Distributions & Far-Field Bulk Noise Overlap

Outputs:
  results/figures/fig_f1756_authentic_indicator_evidence.png
  results/figures/fig_f1756_authentic_indicator_evidence.pdf
"""

from __future__ import print_function, division
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    base_dir = r"D:\Master thesis\Adaptive remeshing"
    summary_path = os.path.join(base_dir, "results", "validation", "f1756_case2_authentic_indicator_summary.json")
    donor_json = os.path.join(base_dir, "results", "validation", "f1728_case2_preanalysis_indicator.json")
    fig_png = os.path.join(base_dir, "results", "figures", "fig_f1756_authentic_indicator_evidence.png")
    fig_pdf = os.path.join(base_dir, "results", "figures", "fig_f1756_authentic_indicator_evidence.pdf")

    with open(summary_path, 'r') as f:
        data = json.load(f)

    with open(donor_json, 'r') as f:
        donor_data = json.load(f)

    records = donor_data['records']

    # Set up matplotlib style
    plt.rcParams.update({
        'font.size': 9,
        'font.family': 'sans-serif',
        'axes.labelsize': 10,
        'axes.titlesize': 10,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8,
        'figure.titlesize': 12
    })

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("F1756: Authentic Error Indicator & Sizing Evidence (Case 2 Off-Axis Hole Benchmark)\n"
                 "Empirical Verification of Pre-Analysis Indicator Blindspot and Count vs. Area Compliance",
                 fontweight='bold', y=0.98)

    # -------------------------------------------------------------
    # Panel (a): Authentic Donor MISESERI Profile vs Kirsch Decay
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    sec_records = [r for r in records if 0.75 <= r['centroid_mm'][0] <= 1.00 and 0.60 <= r['centroid_mm'][1] <= 0.70]
    x_pts = [r['centroid_mm'][0] for r in sec_records]
    y_pts = [r['miseseri_max'] for r in sec_records]

    ax_a.scatter(x_pts, y_pts, color='#1f77b4', alpha=0.6, s=35, edgecolors='none', label='Abaqus Donor Elements (N=66)', zorder=4)

    # Bin means
    bins = data['adapted_mesh_compliance_bins']
    bin_x_centers = [0.5 * (b['x_range'][0] + b['x_range'][1]) for b in bins]
    donor_reg = data['donor_indicator_regions']
    reg_keys = ['proximal_flank', 'near_flank', 'mid_ligament', 'cluster_zone', 'outer_boundary']
    bin_means = [donor_reg[k]['miseseri_mean_mpa'] for k in reg_keys]
    bin_stds = [donor_reg[k]['miseseri_std_mpa'] for k in reg_keys]

    ax_a.errorbar(bin_x_centers, bin_means, yerr=bin_stds, fmt='s-', color='#d62728', lw=2.0, ms=7,
                 capsize=4, label='Abaqus Bin Mean +/- 1 std', zorder=5)

    # Bulk noise floor band
    bulk_mean = donor_reg['bulk_far_field']['miseseri_mean_mpa']
    bulk_std = donor_reg['bulk_far_field']['miseseri_std_mpa']
    ax_a.axhspan(bulk_mean - bulk_std, bulk_mean + bulk_std, color='#2ca02c', alpha=0.15,
                 label='Bulk Noise Floor (%.1f +/- %.1f MPa)' % (bulk_mean, bulk_std), zorder=2)
    ax_a.axhline(bulk_mean, color='#2ca02c', ls='--', lw=1.2, zorder=3)

    # Twin axis for Kirsch gradient decay
    ax_a_twin = ax_a.twinx()
    kirsch_data = data['analytical_vs_fe_decay_comparison']['kirsch_profile']
    kx = [kd['x_mm'] for kd in kirsch_data]
    k_decay = [kd['kirsch_gradient_decay_pct'] for kd in kirsch_data]
    ax_a_twin.plot(kx, k_decay, 'o--', color='#9467bd', lw=1.8, ms=5, label='Kirsch Gradient Decay (%)')
    ax_a_twin.set_ylabel('Kirsch Analytical Gradient Decay (%)', color='#9467bd')
    ax_a_twin.tick_params(axis='y', labelcolor='#9467bd')
    ax_a_twin.set_ylim(-5, 105)

    ax_a.set_xlabel('Ligament Coordinate x [mm] (Hole Flank at x=0.75)')
    ax_a.set_ylabel('Abaqus Donor MISESERI [MPa]')
    ax_a.set_title('(a) Authentic Pre-Analysis MISESERI & Stress-Gradient Decay', fontweight='bold')
    ax_a.grid(True, ls=':', alpha=0.6)
    ax_a.set_xlim(0.74, 1.01)
    ax_a.set_ylim(0, 240)

    # Combine legends
    lines_1, labels_1 = ax_a.get_legend_handles_labels()
    lines_2, labels_2 = ax_a_twin.get_legend_handles_labels()
    ax_a.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right', framealpha=0.9)

    # Annotate cluster zone
    ax_a.annotate('Divergence Zone (x=0.90-0.95)\nMean: 15.2 MPa (z=1.03 in bulk)',
                  xy=(0.925, 15.18), xytext=(0.82, 90),
                  arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                  fontsize=8, bbox=dict(boxstyle='round,pad=0.3', fc='yellow', alpha=0.7))

    # -------------------------------------------------------------
    # Panel (b): Count vs Area Compliance along Secondary Ligament
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    labels_b = ['Prox. Flank\n[0.75, 0.80]', 'Near-Flank\n[0.80, 0.85]', 'Mid-Lig.\n[0.85, 0.90]',
                'Cluster Zone\n[0.90, 0.95]', 'Outer Edge\n[0.95, 1.00]', 'OVERALL\n[0.75, 1.00]']
    
    count_comp = [b['count_compliance_pct'] for b in bins] + [data['adapted_mesh_composite_compliance']['overall_secondary_ligament']['count_compliance_pct']]
    area_comp = [b['area_compliance_pct'] for b in bins] + [data['adapted_mesh_composite_compliance']['overall_secondary_ligament']['area_compliance_pct']]

    x_idx = np.arange(len(labels_b))
    width = 0.35

    rects1 = ax_b.bar(x_idx - width/2, count_comp, width, label='Count-Weighted Compliance (%)', color='#1f77b4', edgecolor='black')
    rects2 = ax_b.bar(x_idx + width/2, area_comp, width, label='Area-Weighted Compliance (%)', color='#ff7f0e', edgecolor='black')

    ax_b.axhline(85.0, color='red', ls='--', lw=1.5, label='Required Physical Gate (>=85%)')
    ax_b.set_ylabel('Mesh Compliance (h <= l0/2 = 3.75 um) [%]')
    ax_b.set_title('(b) Count-Weighted vs. Area-Weighted Mesh Compliance', fontweight='bold')
    ax_b.set_xticks(x_idx)
    ax_b.set_xticklabels(labels_b)
    ax_b.set_ylim(0, 115)
    ax_b.grid(True, ls=':', alpha=0.6, axis='y')
    ax_b.legend(loc='upper right', framealpha=0.9)

    # Bar value labels
    for rect in rects1:
        h = rect.get_height()
        ax_b.annotate('%.1f%%' % h, xy=(rect.get_x() + rect.get_width()/2, h),
                      xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7.5)
    for rect in rects2:
        h = rect.get_height()
        ax_b.annotate('%.1f%%' % h, xy=(rect.get_x() + rect.get_width()/2, h),
                      xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=7.5, color='#b25900')

    # Highlight divergence divergence
    ax_b.annotate('Overall Ligament:\nCount: 83.2%\nArea:  46.5% (FAIL)',
                  xy=(5 + width/2, 46.51), xytext=(4.2, 70),
                  arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                  fontsize=8, bbox=dict(boxstyle='round,pad=0.3', fc='lightyellow', alpha=0.8))

    # -------------------------------------------------------------
    # Panel (c): Sizing Scenarios: Generated vs Projections
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    scenarios = data['sizing_scenarios_reconciled']
    scen_labels = ['M1: Pilot\n(F1731)', 'M2: Calib.\n(F1732)', 'M3: Prod.\n(F1734/F1752)',
                   'P1: Target=1.0%\n(Projection)', 'P2: Target=0.5%\n(Projection)']
    counts = [s['total_physical_elements'] for s in scenarios]
    colors = ['#2ca02c', '#2ca02c', '#2ca02c', '#d62728', '#d62728']

    bars_c = ax_c.bar(range(len(scen_labels)), counts, color=colors, edgecolor='black', width=0.55)
    ax_c.set_ylabel('Total Physical Elements in Specimen')
    ax_c.set_title('(c) Sizing Scenarios: Verified Meshes vs. Unexecuted Projections', fontweight='bold')
    ax_c.set_xticks(range(len(scen_labels)))
    ax_c.set_xticklabels(scen_labels)
    ax_c.set_yscale('log')
    ax_c.set_ylim(1e3, 2e5)
    ax_c.grid(True, ls=':', alpha=0.6, axis='y')

    # Add labels on bars
    for i, (b, s) in enumerate(zip(bars_c, scenarios)):
        h = b.get_height()
        status_txt = "VERIFIED\nJob %s" % (s['job_id'].split('.')[0] if s['job_id'] else '') if s['classification'] == 'AUTHENTIC_GENERATED_MESH' else "UNEXECUTED\nPROJECTION"
        ax_c.annotate('%d el\n(%s)' % (h, "Generated" if "AUTHENTIC" in s['classification'] else "Projected"),
                      xy=(b.get_x() + b.get_width()/2, h), xytext=(0, 3), textcoords="offset points",
                      ha='center', va='bottom', fontsize=8, fontweight='bold')

    # Custom legend for generated vs projection
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor='#2ca02c', edgecolor='black', label='Authentic Generated Mesh (HPC Verified)'),
        Patch(facecolor='#d62728', edgecolor='black', label='Unexecuted Analytical Projection (UNIFORM_ERROR)')
    ]
    ax_c.legend(handles=legend_elements, loc='upper left', framealpha=0.9)

    # -------------------------------------------------------------
    # Panel (d): Pre-Analysis Indicator Distributions & Overlap
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    # Extract data for boxplot
    notch_vals = [r['miseseri_max'] for r in records if 0.50 <= r['centroid_mm'][0] <= 0.55 and 0.48 <= r['centroid_mm'][1] <= 0.52]
    prox_vals = [r['miseseri_max'] for r in records if 0.75 <= r['centroid_mm'][0] < 0.80 and 0.60 <= r['centroid_mm'][1] <= 0.70]
    cluster_vals = [r['miseseri_max'] for r in records if 0.90 <= r['centroid_mm'][0] < 0.95 and 0.60 <= r['centroid_mm'][1] <= 0.70]
    bulk_vals = [r['miseseri_max'] for r in records if r['centroid_mm'][1] >= 0.80 or r['centroid_mm'][1] <= 0.40]

    box_data = [notch_vals, prox_vals, cluster_vals, bulk_vals]
    box_labels = ['Notch Root\n(N=8)', 'Prox. Flank\n(N=14)', 'Cluster Zone\n(N=16)', 'Far-Field Bulk\n(N=1816)']

    bp = ax_d.boxplot(box_data, patch_artist=True, labels=box_labels, showmeans=True,
                      meanprops=dict(marker='D', markeredgecolor='black', markerfacecolor='firebrick'))

    colors_d = ['#9467bd', '#1f77b4', '#d62728', '#2ca02c']
    for patch, c in zip(bp['boxes'], colors_d):
        patch.set_facecolor(c)
        patch.set_alpha(0.6)

    ax_d.set_ylabel('Abaqus Donor MISESERI [MPa] (Log Scale)')
    ax_d.set_title('(d) Error Indicator Contrast & Bulk Noise Floor Overlap', fontweight='bold')
    ax_d.set_yscale('log')
    ax_d.set_ylim(0.3, 2000)
    ax_d.grid(True, ls=':', alpha=0.6, axis='y')

    # Annotation about overlap
    ax_d.annotate('195 Bulk Elements (10.7%)\nexceed Cluster Mean (15.2 MPa)\n-> Indistinguishable from Noise',
                  xy=(3, 15.2), xytext=(2.2, 0.8),
                  arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                  fontsize=8, bbox=dict(boxstyle='round,pad=0.3', fc='mistyrose', alpha=0.85))

    plt.tight_layout(rect=[0, 0.02, 1, 0.95])
    plt.savefig(fig_png, dpi=300)
    plt.savefig(fig_pdf)
    plt.close()

    print("Figures generated successfully:")
    print("  PNG: %s" % fig_png)
    print("  PDF: %s" % fig_pdf)

if __name__ == '__main__':
    main()
