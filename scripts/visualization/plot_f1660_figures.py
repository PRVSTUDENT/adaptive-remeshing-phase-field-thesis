# scripts/visualization/plot_f1660_figures.py
"""
Task F1660: Diagnostic Figure for Recovery Provenance & IP Qualification

Generates publication-quality figure:
- Figure 1: Integration-Point Coordinate Precision & Regime-Specific Stress Agreement
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Load audit data
audit_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1660_PROVENANCE_AUDIT.json"
with open(audit_path, "r") as fp:
    audit = json.load(fp)

# Load plot data from F1659
with open("f1659_plot_data.json", "r") as fp:
    pdata = json.load(fp)

rec_mises = np.array(pdata["rec_elem_mises"])
donor_mises = np.array(pdata["matched_donor_mises"])
donor_d = np.array(pdata["matched_donor_d"])

output_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]

plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

# Panel (a): Coordinate Precision Telemetry
categories = ['Min Error', 'Median Error', 'Mean Error', '95th % Error', 'Max Error']
values = [
    audit['integration_point_coordinate_audit']['min_error_mm'],
    audit['integration_point_coordinate_audit']['median_error_mm'],
    audit['integration_point_coordinate_audit']['mean_error_mm'],
    audit['integration_point_coordinate_audit']['p95_error_mm'],
    audit['integration_point_coordinate_audit']['max_error_mm']
]

bars = ax1.bar(categories, values, color='royalblue', width=0.55, edgecolor='black', lw=1.2)
ax1.set_yscale('log')
ax1.set_ylabel("Coordinate Distance $\\Delta r$ [mm] (Log Scale)")
ax1.set_title("(a) Integration-Point Coordinate Precision Audit\n(11,452 IPs: Max Error = $7.00\\times 10^{-10}$ mm $\\equiv$ Machine Precision)",
              fontsize=11, fontweight='bold')
ax1.axhline(1.0e-3, color='red', ls='--', lw=1.5, label='USDFLD Fail-Closed Threshold ($1.0\\times 10^{-2}$ mm)')
ax1.grid(True, which='both', ls=':', alpha=0.5)
ax1.legend(loc='upper left', framealpha=0.9)

for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval * 1.5,
             f"{yval:.2e} mm", ha='center', va='bottom', fontsize=9.5, fontweight='bold')

# Panel (b): Regime Breakdown MAE & RMSE
regimes = ['Far-Field\n($d < 0.10$)\n[94.1%]', 'Softening Zone\n($0.10 \\leq d < 0.80$)\n[4.9%]', 'Broken Band\n($d \\geq 0.80$)\n[0.9%]', 'Global Domain\n(All Elements)\n[100%]']
rmse_vals = [
    audit['stress_parity_recalculation']['far_field']['rmse_MPa'],
    audit['stress_parity_recalculation']['softened']['rmse_MPa'],
    audit['stress_parity_recalculation']['broken_band']['rmse_MPa'],
    audit['stress_parity_recalculation']['global']['rmse_MPa']
]
mae_vals = [
    audit['stress_parity_recalculation']['far_field']['mae_MPa'],
    audit['stress_parity_recalculation']['softened']['mae_MPa'],
    audit['stress_parity_recalculation']['broken_band']['mae_MPa'],
    audit['stress_parity_recalculation']['global']['mae_MPa']
]

x = np.arange(len(regimes))
width = 0.35

ax2.bar(x - width/2, rmse_vals, width, label='RMSE [MPa]', color='crimson', edgecolor='black', lw=1.2)
ax2.bar(x + width/2, mae_vals, width, label='MAE [MPa]', color='darkorange', edgecolor='black', lw=1.2)

ax2.set_xticks(x)
ax2.set_xticklabels(regimes)
ax2.set_ylabel("Stress Error [MPa]")
ax2.set_title("(b) Stress Discrepancy Breakdown by Damage Regime\n(Global $r=0.9575$, Far-Field $r=0.9724$, NRMSE = 4.05%)",
              fontsize=11, fontweight='bold')
ax2.grid(True, axis='y', ls=':', alpha=0.5)
ax2.legend(loc='upper left', framealpha=0.9)

for i in range(len(regimes)):
    ax2.text(x[i] - width/2, rmse_vals[i] + 10, f"{rmse_vals[i]:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold')
    ax2.text(x[i] + width/2, mae_vals[i] + 10, f"{mae_vals[i]:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold')

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1660_provenance_and_precision_audit.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1660_provenance_and_precision_audit.pdf"))
plt.close(fig)

print("Figure F1660 successfully generated and saved.")
