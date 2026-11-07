# scripts/visualization/plot_f1658_figures.py
"""
Task F1658: Diagnostic Figures for Offline Integration-Point Damage & Stiffness Feasibility Test

Generates publication-quality figures:
- Figure 1: Spatial Damage Distribution: Donor (Coarse 2,906) vs Rep 1 (F1656 Nodal) vs Rep 2 (Direct IP Transfer)
- Figure 2: Constitutive Degradation Curve & Tabular Interpolation Error (Exact vs 101-pt vs 1001-pt)
- Figure 3: Notch-to-Hole Ligament Crack-Core Continuity Audit (Elements with d >= 0.80, 0.90, 0.99)
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from matplotlib.colors import LogNorm

# Load plot data
with open("f1658_plot_data.json", "r") as fp:
    plot_data = json.load(fp)

rec_gp_coords = np.array(plot_data["rec_gp_coords"])
d_rep1_nodal = np.array(plot_data["d_rep1_nodal"])
d_rep2_direct = np.array(plot_data["d_rep2_direct"])
g_rep1_exact = np.array(plot_data["g_rep1_exact"])
g_rep2_exact = np.array(plot_data["g_rep2_exact"])
g_rep2_tab101 = np.array(plot_data["g_rep2_tab101"])
donor_gp_coords = np.array(plot_data["donor_gp_coords"])
donor_gp_damage = np.array(plot_data["donor_gp_damage"])

# Target directories
output_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]

# Set publication style
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

# ==============================================================================
# FIGURE 1: SPATIAL DAMAGE COMPARISON (3 PANELS)
# ==============================================================================
print("Plotting Figure 1: Spatial Damage Comparison...")
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)

# Common zoom window around fracture domain: x in [0.4, 1.0], y in [0.3, 0.9]
zoom_mask_donor = (donor_gp_coords[:, 0] >= 0.4) & (donor_gp_coords[:, 0] <= 1.0) & \
                  (donor_gp_coords[:, 1] >= 0.3) & (donor_gp_coords[:, 1] <= 0.9)
zoom_mask_rec = (rec_gp_coords[:, 0] >= 0.4) & (rec_gp_coords[:, 0] <= 1.0) & \
                (rec_gp_coords[:, 1] >= 0.3) & (rec_gp_coords[:, 1] <= 0.9)

# (a) Donor Job 1 Authentic Damage
ax = axes[0]
sc0 = ax.scatter(donor_gp_coords[zoom_mask_donor, 0], donor_gp_coords[zoom_mask_donor, 1],
                 c=donor_gp_damage[zoom_mask_donor], cmap='inferno', vmin=0.0, vmax=1.0, s=18, edgecolors='none')
ax.plot([0.4, 0.5], [0.5, 0.5], 'c-', lw=2.5, label='Notch ($a_0=0.5$)')
hole = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=1.5, ls='--')
ax.add_patch(hole)
ax.set_title("(a) Authentic Donor Coupled Damage\n($d_{\\max} = 0.9976$, sharp crack core)", fontsize=11, fontweight='bold')
ax.set_xlabel("$x$ [mm]")
ax.set_ylabel("$y$ [mm]")
ax.set_xlim(0.4, 1.0)
ax.set_ylim(0.3, 0.9)
ax.set_aspect('equal')
ax.grid(True, ls=':', alpha=0.5)
ax.legend(loc='lower left', framealpha=0.9)

# (b) Representation 1: F1656 Nodal Interpolation (Diluted)
ax = axes[1]
sc1 = ax.scatter(rec_gp_coords[zoom_mask_rec, 0], rec_gp_coords[zoom_mask_rec, 1],
                 c=d_rep1_nodal[zoom_mask_rec], cmap='inferno', vmin=0.0, vmax=1.0, s=18, edgecolors='none')
ax.plot([0.4, 0.5], [0.5, 0.5], 'c-', lw=2.5)
hole = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=1.5, ls='--')
ax.add_patch(hole)
ax.set_title("(b) Rep 1: Nodal Interpolation (F1656)\n($d_{\\max} = 0.8842$, smeared, $2,245\\times$ stiffness surge)", fontsize=11, fontweight='bold')
ax.set_xlabel("$x$ [mm]")
ax.set_xlim(0.4, 1.0)
ax.set_ylim(0.3, 0.9)
ax.set_aspect('equal')
ax.grid(True, ls=':', alpha=0.5)

# (c) Representation 2: Direct Donor-to-Receiver-IP Transfer
ax = axes[2]
sc2 = ax.scatter(rec_gp_coords[zoom_mask_rec, 0], rec_gp_coords[zoom_mask_rec, 1],
                 c=d_rep2_direct[zoom_mask_rec], cmap='inferno', vmin=0.0, vmax=1.0, s=18, edgecolors='none')
ax.plot([0.4, 0.5], [0.5, 0.5], 'c-', lw=2.5)
hole = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=1.5, ls='--')
ax.add_patch(hole)
ax.set_title("(c) Rep 2: Direct Element-to-IP Transfer\n($d_{\\max} = 0.9976$, exact core preserved, $1.000\\times$ parity)", fontsize=11, fontweight='bold')
ax.set_xlabel("$x$ [mm]")
ax.set_xlim(0.4, 1.0)
ax.set_ylim(0.3, 0.9)
ax.set_aspect('equal')
ax.grid(True, ls=':', alpha=0.5)

cbar = fig.colorbar(sc2, ax=axes, orientation='horizontal', fraction=0.045, pad=0.12)
cbar.set_label("Phase-Field Damage $d$ [-]")

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1658_figure1_damage_field_comparison.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1658_figure1_damage_field_comparison.pdf"))
plt.close(fig)

# ==============================================================================
# FIGURE 2: CONSTITUTIVE DEGRADATION & TABULAR ERROR
# ==============================================================================
print("Plotting Figure 2: Constitutive Degradation & Tabular Error...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

# Panel (a): Exact Quadratic vs 101-pt vs 1001-pt near crack core (d in [0.95, 1.0])
d_plot = np.linspace(0.95, 1.0, 500)
k_res = 1.0e-7
g_exact_curve = (1.0 - d_plot)**2 + k_res

d_grid101 = np.linspace(0.0, 1.0, 101)
g_grid101 = (1.0 - d_grid101)**2 + k_res
g_tab101_curve = np.interp(d_plot, d_grid101, g_grid101)

d_grid1001 = np.linspace(0.0, 1.0, 1001)
g_grid1001 = (1.0 - d_grid1001)**2 + k_res
g_dense1001_curve = np.interp(d_plot, d_grid1001, g_grid1001)

ax1.plot(d_plot, g_exact_curve, 'k-', lw=2.5, label='Exact Quadratic $g(d) = (1-d)^2 + 10^{-7}$')
ax1.plot(d_plot, g_tab101_curve, 'r--', lw=2.0, label='101-Point Uniform Table (F1656 Standard)')
ax1.plot(d_plot, g_dense1001_curve, 'b:', lw=2.0, label='1001-Point Dense Table')

# Mark donor peak damage and F1656 smeared damage
d_donor = 0.997577
g_donor_exact = (1.0 - d_donor)**2 + k_res
g_donor_tab101 = float(np.interp(d_donor, d_grid101, g_grid101))

ax1.scatter([d_donor], [g_donor_exact], color='green', s=100, zorder=5, label='Donor Core Exact ($g = 5.97\\times 10^{-6}$)')
ax1.scatter([d_donor], [g_donor_tab101], color='red', marker='s', s=80, zorder=5, label='101-pt Overestimate ($g = 2.43\\times 10^{-5}$, $4.07\\times$)')

ax1.set_yscale('log')
ax1.set_xlabel("Damage $d$ [-]")
ax1.set_ylabel("Degradation Factor $g(d)$ (Log Scale)")
ax1.set_title("(a) Residual Stiffness at Crack Core ($d \\in [0.95, 1.00]$)", fontsize=11, fontweight='bold')
ax1.grid(True, which='both', ls=':', alpha=0.5)
ax1.legend(loc='upper right', framealpha=0.9, fontsize=9.5)

# Panel (b): Tabular Overestimate Factor vs Damage
ratio_101 = g_tab101_curve / g_exact_curve
ratio_1001 = g_dense1001_curve / g_exact_curve

ax2.plot(d_plot, ratio_101, 'r-', lw=2.5, label='101-Point Table Error Ratio ($g_{\\mathrm{tab101}} / g_{\\mathrm{exact}}$)')
ax2.plot(d_plot, ratio_1001, 'b--', lw=2.0, label='1001-Point Table Error Ratio ($g_{\\mathrm{dense}} / g_{\\mathrm{exact}}$)')
ax2.axhline(1.0, color='gray', ls=':', lw=1.5, label='Exact Parity (1.0)')

ax2.scatter([d_donor], [g_donor_tab101 / g_donor_exact], color='red', marker='s', s=90, zorder=5)
ax2.annotate("$4.07\\times$ Stiffness Error\nat $d=0.9976$", xy=(d_donor, g_donor_tab101 / g_donor_exact),
             xytext=(d_donor - 0.025, 3.2),
             arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
             fontweight='bold', color='darkred', fontsize=10)

ax2.set_xlabel("Damage $d$ [-]")
ax2.set_ylabel("Stiffness Overestimate Factor [-]")
ax2.set_title("(b) Piecewise Linear Tabular Error vs Damage", fontsize=11, fontweight='bold')
ax2.grid(True, ls=':', alpha=0.5)
ax2.legend(loc='upper left', framealpha=0.9)

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1658_figure2_tabular_interpolation_error.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1658_figure2_tabular_interpolation_error.pdf"))
plt.close(fig)

# ==============================================================================
# FIGURE 3: CRACK-CORE CONTINUITY & LIGAMENT ELEMENT AUDIT
# ==============================================================================
print("Plotting Figure 3: Ligament Crack-Core Continuity Audit...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), constrained_layout=True)

# High zoom on ligament: x in [0.48, 0.68], y in [0.48, 0.68]
lig_mask_rep1 = (rec_gp_coords[:, 0] >= 0.48) & (rec_gp_coords[:, 0] <= 0.68) & \
                (rec_gp_coords[:, 1] >= 0.48) & (rec_gp_coords[:, 1] <= 0.68)
lig_mask_rep2 = lig_mask_rep1

# (a) Rep 1: Smeared Nodal Field along Ligament
ax1.scatter(rec_gp_coords[lig_mask_rep1, 0], rec_gp_coords[lig_mask_rep1, 1],
            c=d_rep1_nodal[lig_mask_rep1], cmap='plasma', vmin=0.0, vmax=1.0, s=40, edgecolors='k', lw=0.3)
ax1.plot([0.48, 0.50], [0.50, 0.50], 'c-', lw=3.0, label='Notch Tip ($a_0=0.50$)')
hole = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='none', lw=2.0, ls='--', label='Hole ($R=0.10$)')
ax1.add_patch(hole)
ax1.set_title("(a) Rep 1: Nodal Smearing on Ligament\n(Max $d=0.8842$, Zero $d \\geq 0.90$ IPs, Artificial Tension)", fontsize=11, fontweight='bold')
ax1.set_xlabel("$x$ [mm]")
ax1.set_ylabel("$y$ [mm]")
ax1.set_xlim(0.48, 0.68)
ax1.set_ylim(0.48, 0.68)
ax1.set_aspect('equal')
ax1.grid(True, ls=':', alpha=0.5)
ax1.legend(loc='lower right', framealpha=0.9)

# (b) Rep 2: Direct IP Transfer along Ligament
sc = ax2.scatter(rec_gp_coords[lig_mask_rep2, 0], rec_gp_coords[lig_mask_rep2, 1],
                 c=d_rep2_direct[lig_mask_rep2], cmap='plasma', vmin=0.0, vmax=1.0, s=40, edgecolors='k', lw=0.3)
ax2.plot([0.48, 0.50], [0.50, 0.50], 'c-', lw=3.0, label='Notch Tip ($a_0=0.50$)')
hole = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='none', lw=2.0, ls='--', label='Hole ($R=0.10$)')
ax2.add_patch(hole)

# Mark broken core points (d >= 0.90) with green stars
broken_core_mask = lig_mask_rep2 & (d_rep2_direct >= 0.90)
ax2.scatter(rec_gp_coords[broken_core_mask, 0], rec_gp_coords[broken_core_mask, 1],
            color='lime', marker='*', s=90, edgecolors='black', lw=0.6, label='Broken Core ($d \\geq 0.90$, 80 IPs)', zorder=6)

ax2.set_title("(b) Rep 2: Direct IP Transfer on Ligament\n(Unbroken Crack Path, Zero Artificial Bridges, $d_{\\max}=0.9976$)", fontsize=11, fontweight='bold')
ax2.set_xlabel("$x$ [mm]")
ax2.set_xlim(0.48, 0.68)
ax2.set_ylim(0.48, 0.68)
ax2.set_aspect('equal')
ax2.grid(True, ls=':', alpha=0.5)
ax2.legend(loc='lower right', framealpha=0.9)

cbar = fig.colorbar(sc, ax=[ax1, ax2], orientation='horizontal', fraction=0.05, pad=0.14)
cbar.set_label("Phase-Field Damage $d$ [-]")

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1658_figure3_ligament_continuity_audit.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1658_figure3_ligament_continuity_audit.pdf"))
plt.close(fig)

print("All 3 figures successfully generated and saved.")
