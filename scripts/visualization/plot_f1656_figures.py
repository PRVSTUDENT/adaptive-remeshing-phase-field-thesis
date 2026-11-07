# scripts/visualization/plot_f1656_figures.py
"""
F1656 Diagnostic Figure Generator:
- Figure A: Reconstructed Donor Stress vs F1656 Corrected Auxiliary Recovery Stress & Discrepancy
- Figure B: Damage Mapping & Smeared Crack Core Audit (Donor vs Receiver IP Field)
- Figure C: Spatially Matched Parity Scatter Plot & Reaction Force Comparison
Outputs 300 DPI PNG and vector PDF in both figure repositories.
"""
import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from scipy.interpolate import griddata

# Output directories
out_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]
for d in out_dirs:
    os.makedirs(d, exist_ok=True)

# Load extracted plot data
json_file = "f1656_plot_data.json"
if not os.path.exists(json_file):
    print("ERROR: %s not found" % json_file)
    sys.exit(1)

with open(json_file, "r") as fp:
    data = json.load(fp)

donor_c = np.array(data["donor_centroids"])
donor_s = np.array(data["donor_elem_mises"])
donor_d = np.array(data["donor_elem_d"])

rec_c = np.array(data["rec_centroids"])
rec_s = np.array(data["rec_elem_mises"])
rec_fv1 = np.array(data["rec_elem_fv1"])

miseseri = np.array(data["miseseri_vals"])
misesavg = np.array(data["misesavg_vals"])
eta = (miseseri / np.maximum(misesavg, 1e-6)) * 100.0

# Interpolate onto fine visualization grid (300 x 300)
gx = np.linspace(0.0, 1.0, 300)
gy = np.linspace(0.0, 1.0, 300)
GX, GY = np.meshgrid(gx, gy)

# Mask hole
hole_mask = (GX - 0.65)**2 + (GY - 0.65)**2 < 0.10**2
# Mask notch slit
slit_mask = (GX <= 0.50) & (np.abs(GY - 0.50) < 0.005)

grid_donor_s = griddata(donor_c, donor_s, (GX, GY), method='linear')
grid_donor_s[hole_mask] = np.nan
grid_donor_s[slit_mask] = np.nan

grid_rec_s = griddata(rec_c, rec_s, (GX, GY), method='linear')
grid_rec_s[hole_mask] = np.nan
grid_rec_s[slit_mask] = np.nan

grid_diff_s = np.abs(grid_donor_s - grid_rec_s)

# ==============================================================================
# FIGURE A: RECONSTRUCTED DONOR STRESS VS F1656 RECOVERY STRESS
# ==============================================================================
print("Plotting Figure A: Reconstructed Donor vs Recovery Stress...")
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)

s_max_vis = 2500.0 # MPa
norm_s = Normalize(vmin=0.0, vmax=s_max_vis)

# Panel 1: Donor Reconstructed Stress
im0 = axes[0].imshow(grid_donor_s, origin='lower', extent=[0, 1, 0, 1], cmap='inferno', norm=norm_s)
axes[0].set_title("(a) Authentic Donor Reconstructed Stress\n(Job 1 ODB, Step 2 Inc 337)", fontsize=12, fontweight='bold')
axes[0].set_xlabel("$x$ [mm]")
axes[0].set_ylabel("$y$ [mm]")
cbar0 = fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
cbar0.set_label("Degraded Mises Stress [MPa]")

# Panel 2: Recovery Solve Stress
im1 = axes[1].imshow(grid_rec_s, origin='lower', extent=[0, 1, 0, 1], cmap='inferno', norm=norm_s)
axes[1].set_title("(b) Corrected Auxiliary Recovery Stress\n(F1656 Node-Based Field Solve)", fontsize=12, fontweight='bold')
axes[1].set_xlabel("$x$ [mm]")
axes[1].set_ylabel("$y$ [mm]")
cbar1 = fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
cbar1.set_label("Recovered Mises Stress [MPa]")

# Panel 3: Discrepancy Map
norm_diff = Normalize(vmin=0.0, vmax=1500.0)
im2 = axes[2].imshow(grid_diff_s, origin='lower', extent=[0, 1, 0, 1], cmap='magma', norm=norm_diff)
axes[2].set_title("(c) Absolute Stress Discrepancy\n$|S_{\\mathrm{donor}} - S_{\\mathrm{rec}}|$ [MPa]", fontsize=12, fontweight='bold')
axes[2].set_xlabel("$x$ [mm]")
axes[2].set_ylabel("$y$ [mm]")
cbar2 = fig.colorbar(im2, ax=axes[2], fraction=0.046, pad=0.04)
cbar2.set_label("Discrepancy [MPa]")

for d in out_dirs:
    fig.savefig(os.path.join(d, "fig_f1656_figure_a_reconstructed_vs_recovery_stress.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1656_figure_a_reconstructed_vs_recovery_stress.pdf"))
plt.close(fig)

# ==============================================================================
# FIGURE B: DAMAGE MAPPING & SMEARED CRACK CORE AUDIT
# ==============================================================================
print("Plotting Figure B: Damage Mapping & Smearing Audit...")
grid_donor_d = griddata(donor_c, donor_d, (GX, GY), method='linear')
grid_donor_d[hole_mask] = np.nan
grid_donor_d[slit_mask] = np.nan

grid_rec_d = griddata(rec_c, rec_fv1, (GX, GY), method='linear')
grid_rec_d[hole_mask] = np.nan
grid_rec_d[slit_mask] = np.nan

fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)

norm_d = Normalize(vmin=0.0, vmax=1.0)

# Panel 1: Donor Damage
im0 = axes[0].imshow(grid_donor_d, origin='lower', extent=[0, 1, 0, 1], cmap='viridis', norm=norm_d)
axes[0].set_title("(a) Authentic Donor Damage $d(\\mathbf{x})$\n($d_{\\max} = 0.9976$, sharp crack core)", fontsize=12, fontweight='bold')
axes[0].set_xlabel("$x$ [mm]")
axes[0].set_ylabel("$y$ [mm]")
cbar0 = fig.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)
cbar0.set_label("Damage $d$ [-]")

# Panel 2: Receiver IP Damage
im1 = axes[1].imshow(grid_rec_d, origin='lower', extent=[0, 1, 0, 1], cmap='viridis', norm=norm_d)
axes[1].set_title("(b) Receiver Integration-Point Field (FV1)\n($d_{\\max} = 0.8842$, smeared crack core)", fontsize=12, fontweight='bold')
axes[1].set_xlabel("$x$ [mm]")
axes[1].set_ylabel("$y$ [mm]")
cbar1 = fig.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)
cbar1.set_label("Field Variable FV1 [-]")

# Panel 3: Crack-line profile along ligament
# Sample profile along line from notch tip (0.50, 0.50) to hole entry (0.58, 0.58)
s_line = np.linspace(0.50, 0.58, 100)
pts_line = np.column_stack([s_line, s_line])
d_donor_line = griddata(donor_c, donor_d, pts_line, method='linear')
d_rec_line = griddata(rec_c, rec_fv1, pts_line, method='linear')

axes[2].plot(s_line, d_donor_line, 'r-', lw=2.5, label="Donor Job 1 ($d_{\\max} \\to 1.0$)")
axes[2].plot(s_line, d_rec_line, 'b--', lw=2.5, label="Receiver FV1 ($d_{\\max} = 0.884$)")
axes[2].axhline(0.80, color='gray', linestyle=':', label="Broken Threshold ($d=0.8$)")
axes[2].set_title("(c) Crack Ligament Profile ($x=y$)\nPeak Smearing & Stiffness Dilution", fontsize=12, fontweight='bold')
axes[2].set_xlabel("Coordinate along diagonal $x=y$ [mm]")
axes[2].set_ylabel("Damage $d$ [-]")
axes[2].set_ylim(-0.05, 1.05)
axes[2].grid(True, alpha=0.3)
axes[2].legend(loc="upper left")

for d in out_dirs:
    fig.savefig(os.path.join(d, "fig_f1656_figure_b_damage_mapping_and_smearing_audit.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1656_figure_b_damage_mapping_and_smearing_audit.pdf"))
plt.close(fig)

# ==============================================================================
# FIGURE C: PARITY SCATTER PLOT & REACTION FORCE COMPARISON
# ==============================================================================
print("Plotting Figure C: Stress Parity & Reaction Force Comparison...")
fig, axes = plt.subplots(1, 3, figsize=(18, 5.5), constrained_layout=True)

# Project rec stress to donor centroids for 1-to-1 comparison
# (Use simple k-NN projection matching execute script)
from scipy.spatial import cKDTree
tree = cKDTree(rec_c)
_, idxs = tree.query(donor_c, k=3)
dists = np.sqrt(np.sum((rec_c[idxs] - donor_c[:, np.newaxis, :])**2, axis=2))
weights = 1.0 / np.maximum(dists, 1e-6)
weights /= np.sum(weights, axis=1, keepdims=True)
s_rec_matched = np.sum(weights * rec_s[idxs], axis=1)

# Categorize donor elements
broken_idx = donor_d >= 0.80
fpz_idx = (donor_d >= 0.10) & (donor_d < 0.80)
elastic_idx = donor_d < 0.10

# Panel 1: Parity Scatter
axes[0].scatter(donor_s[elastic_idx], s_rec_matched[elastic_idx], c='dodgerblue', alpha=0.4, s=15, label="Elastic Far-Field ($r=0.806$)")
axes[0].scatter(donor_s[fpz_idx], s_rec_matched[fpz_idx], c='orange', alpha=0.8, s=25, label="Active FPZ ($r=0.326$)")
axes[0].scatter(donor_s[broken_idx], s_rec_matched[broken_idx], c='crimson', alpha=1.0, s=40, marker='^', label="Broken Band ($r=0.031$)")
max_val = max(donor_s.max(), s_rec_matched.max())
axes[0].plot([0, max_val], [0, max_val], 'k--', lw=1.5, label="Ideal 1:1 Parity")
axes[0].set_title("(a) Stress Parity Scatter Plot\nGlobal $r = 0.7537$, RMSE $= 396.5$ MPa (13.6% NRMSE)", fontsize=12, fontweight='bold')
axes[0].set_xlabel("Donor Reconstructed Mises Stress [MPa]")
axes[0].set_ylabel("Recovery Solve Mises Stress [MPa]")
axes[0].set_xlim(0, 3000)
axes[0].set_ylim(0, 3000)
axes[0].grid(True, alpha=0.3)
axes[0].legend(loc="upper left")

# Panel 2: Reaction Force Comparison
bars = axes[1].bar(["Donor Job 1\n(Coupled UEL)", "F1656 Recovery\n(Auxiliary Solve)"], 
                   [0.216354, 0.558936], color=['royalblue', 'coral'], width=0.45)
axes[1].set_ylabel("Reaction Force $RF_2$ [kN]")
axes[1].set_title("(b) Reaction Force Comparison\nDiscrepancy: $+158.3\\%$ ($2.58\\times$ higher)", fontsize=12, fontweight='bold')
axes[1].grid(True, axis='y', alpha=0.3)
for bar in bars:
    yval = bar.get_height()
    axes[1].text(bar.get_x() + bar.get_width()/2.0, yval + 0.02, "%.3f kN" % yval, ha='center', va='bottom', fontweight='bold')
axes[1].set_ylim(0, 0.75)

# Panel 3: SPR Error Indicator Distribution
axes[2].hist(miseseri, bins=50, color='purple', alpha=0.7, edgecolor='k')
axes[2].set_title("(c) Authentic Abaqus MISESERI Indicator\nmin=0.44 MPa, median=7.09 MPa, max=1179.9 MPa", fontsize=12, fontweight='bold')
axes[2].set_xlabel("SPR Error Indicator MISESERI [MPa]")
axes[2].set_ylabel("Element Frequency")
axes[2].grid(True, alpha=0.3)
axes[2].set_yscale('log')

for d in out_dirs:
    fig.savefig(os.path.join(d, "fig_f1656_figure_c_stress_parity_and_reaction_force.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1656_figure_c_stress_parity_and_reaction_force.pdf"))
plt.close(fig)

print("All F1656 figures successfully generated and saved.")
