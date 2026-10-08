import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

repo_dir = r"D:\Master thesis\Adaptive remeshing"
data_dir = os.path.join(repo_dir, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
ref_dir = os.path.join(repo_dir, "references", "derived")
fig_dir = os.path.join(repo_dir, "results", "figures", "mode2")
os.makedirs(fig_dir, exist_ok=True)

# 1. Load Data
# Redigitized Fig 13a data
df_redig = pd.read_csv(os.path.join(ref_dir, "pandey_kumar_2025_fig13a_authoritative_redigitized.csv"))

# Coarse retest trajectory and RF history (Job 1411104)
df_coarse_traj = pd.read_csv(os.path.join(data_dir, "mode2_j1_coarse_retest_crack_trajectory.csv"))
df_coarse_rf = pd.read_csv(os.path.join(data_dir, "mode2_j1_coarse_retest_rf_history.csv"))
df_coarse_rf['u_um'] = df_coarse_rf['ux_mm'] * 1000.0
df_coarse_rf['rf_N'] = df_coarse_rf['rf1_kN'] * 1000.0

# MISESERI data
df_mises = pd.read_csv(os.path.join(data_dir, "mode2_miseseri_deep_audit_step1.csv"))

# Adapted retest terminal RF history & trajectory (Job 1411103)
df_adapt_rf = pd.read_csv(os.path.join(data_dir, "mode2_j2_adapted_retest_live_rf.csv"))
df_adapt_rf['u_um'] = df_adapt_rf['ux_mm'] * 1000.0
df_adapt_rf['rf_N'] = df_adapt_rf['rf1_N']
df_adapt_traj = pd.read_csv(os.path.join(data_dir, "mode2_j2_adapted_retest_crack_trajectory.csv"))

# Set publication style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
fig = plt.figure(figsize=(16, 12), dpi=300)
gs = gridspec.GridSpec(2, 2, hspace=0.28, wspace=0.24)

# -------------------------------------------------------------
# Panel A: Authoritative Redigitization of Fig. 13(a) & Correction
# -------------------------------------------------------------
axA = fig.add_subplot(gs[0, 0])
axA.plot(df_redig["displacement_um"], df_redig["proposed_pfm_N"], 'r-', linewidth=2.5,
         label=f"Proposed PFM (Pandey 2025, Peak {df_redig['proposed_pfm_N'].max():.1f} N at 8.28 $\\mu$m)")
axA.plot(df_redig["displacement_um"], df_redig["standard_pfm_N"], 'b--', linewidth=2.0,
         label=f"Standard PFM (Pandey 2025, Peak {df_redig['standard_pfm_N'].max():.1f} N at 8.08 $\\mu$m)")
axA.plot(df_redig["displacement_um"], df_redig["navidtehrani_2021_N"], 'g-.', linewidth=1.8,
         label=f"Navidtehrani (2021) [73] (Peak {df_redig['navidtehrani_2021_N'].max():.1f} N at 8.07 $\\mu$m)")

axA.axhline(145.5, color='gray', linestyle=':', linewidth=1.5)
axA.annotate("Legacy 145.5 N / 19.1 $\\mu$m Digitization Defect\n[Falsified & Formally Retracted]",
             xy=(4.0, 145.5), xytext=(2.0, 220.0),
             arrowprops=dict(arrowstyle="->", color="darkred", lw=1.5),
             bbox=dict(boxstyle="round,pad=0.3", fc="#fff0f0", ec="red", alpha=0.9),
             fontsize=8.5, color="darkred", fontweight="bold")

axA.set_xlabel("Horizontal Displacement $u_x$ [$\\mu$m]", fontsize=11, fontweight="bold")
axA.set_ylabel("Reaction Force $F_x$ [N]", fontsize=11, fontweight="bold")
axA.set_title("(a) Authoritative Redigitization of Pandey & Kumar (2025) Fig. 13(a)", fontsize=12, fontweight="bold")
axA.set_xlim(0, 16.5)
axA.set_ylim(0, 420)
axA.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
axA.grid(True, linestyle="--", alpha=0.6)

# -------------------------------------------------------------
# Panel B: Discrepancy Matrix & Provenance Summary Table
# -------------------------------------------------------------
axB = fig.add_subplot(gs[0, 1])
axB.axis('off')

matrix_data = [
    ["Parameter / Feature", "Published Paper (2025)", "Current Implementation", "Verification Finding"],
    ["Domain $\\Omega$ & Crack $a_0$", "$1.0\\times1.0\\,$mm, $a_0=0.5\\,$mm", "$1.0\\times1.0\\,$mm, $a_0=0.5\\,$mm", "Bit-for-Bit Identical"],
    ["Strain Energy Split", "Miehe Anisotropic Split", "Miehe Spectral Split", "Formulation Match"],
    ["Length Scale $l_0$", "$0.015\\,$mm ($15.0\\,\\mu$m)", "$0.015\\,$mm ($15.0\\,\\mu$m)", "Bit-for-Bit Identical"],
    ["Top Boundary $u_y$", "Constrained ($u_y=0$)", "Constrained ($u_y=0$)", "$K_0$: $47.2$ vs $45.8\\,$kN/mm ($3.1\\%$)"],
    ["Step 1 Load Increment", "Typo: $\\Delta u_1=5\\times10^{-4}$", "$\\,\\Delta u_1 = 5\\times10^{-6}\\,$mm", "Typographical error in paper"],
    ["Remeshing errorTarget", "Unpublished / Omitted", "2.0% ($22,530\\,$FEs)", "Reproduces Fig. 12b topology ($+12.9\\%$)"],
    ["Peak Force (Adapted)", "$365.74\\,$N at $8.28\\,\\mu$m", "$411.85\\,$N at $9.39\\,\\mu$m", "Agreement within $+12.6\\%$ ($h/l_0$)"],
    ["Solver Execution Status", "Complete curve", "TERMINAL_PARTIAL ($u=9.42\\,\\mu$m)", "Cutback non-convergence in softening"]
]

table = axB.table(cellText=matrix_data, loc='center', cellLoc='left', colWidths=[0.23, 0.28, 0.28, 0.21])
table.auto_set_font_size(False)
table.set_fontsize(8.0)
table.scale(1.0, 1.70)

for i in range(len(matrix_data[0])):
    table[(0, i)].set_facecolor('#1f77b4')
    table[(0, i)].set_text_props(color='white', fontweight='bold')

for r in range(1, len(matrix_data)):
    color = '#f8f9fa' if r % 2 == 1 else '#ffffff'
    for c in range(len(matrix_data[0])):
        table[(r, c)].set_facecolor(color)
        if c == 3:
            table[(r, c)].set_text_props(fontweight='bold', color='#2a6f97')

axB.set_title("(b) Literature vs. Implementation Discrepancy & Reconciliation Matrix", fontsize=12, fontweight="bold", pad=15)

# -------------------------------------------------------------
# Panel C: Pre-Analysis MISESERI Field vs Fracture Crack Path
# -------------------------------------------------------------
axC = fig.add_subplot(gs[1, 0])

# Scatter plot of MISESERI
sc = axC.scatter(df_mises["xc"], df_mises["yc"], c=df_mises["eta_e"], cmap="plasma",
                 s=18, alpha=0.7, label="Pre-Analysis $\\eta_e = \\text{MISESERI}/\\text{MISESAVG}$")
cbar = plt.colorbar(sc, ax=axC, fraction=0.046, pad=0.04)
cbar.set_label("Relative Error Indicator $\\eta_e$", fontsize=10, fontweight="bold")

# Plot initial slit
axC.plot([0.0, 0.5], [0.5, 0.5], 'k-', linewidth=3.5, label="Initial Slit ($a_0 = 0.5\\,$mm)")

# Plot actual crack trajectory from companion coarse fracture benchmark
axC.plot(df_coarse_traj["x_mm"], df_coarse_traj["y_mm"], 'ro-', linewidth=2.2, markersize=4,
         label="Coarse Crack Path (Job 1411104, $\\theta = -57.95^\\circ$)")

# Plot adapted crack trajectory
axC.plot(df_adapt_traj["x_mm"], df_adapt_traj["y_mm"], 'b.-', linewidth=1.5, markersize=3, alpha=0.8,
         label="Adapted Crack Tip Localization (Job 1411103, $d_{max}=0.960$)")

axC.set_xlabel("X Coordinate [mm]", fontsize=11, fontweight="bold")
axC.set_ylabel("Y Coordinate [mm]", fontsize=11, fontweight="bold")
axC.set_title("(c) Pre-Analysis Error Indicator ($\\,\\eta_e\\,$) vs. Fracture Crack Trajectory", fontsize=12, fontweight="bold")
axC.set_xlim(0, 1.0)
axC.set_ylim(0, 1.0)
axC.set_aspect('equal')
axC.legend(loc="upper left", fontsize=8.0, framealpha=0.95)

# -------------------------------------------------------------
# Panel D: Force-Displacement Response Comparison & Terminal Telemetry
# -------------------------------------------------------------
axD = fig.add_subplot(gs[1, 1])

# Plot Coarse Retest (Job 1411104)
axD.plot(df_coarse_rf["u_um"], df_coarse_rf["rf_N"], 'm-', linewidth=2.2,
         label=f"Coarse Benchmark (Job 1411104, 2,960 FEs, $F_{{max}}=514.5\\,$N)")

# Plot Adapted Retest (Job 1411103)
axD.plot(df_adapt_rf["u_um"], df_adapt_rf["rf_N"], 'b-', linewidth=2.5,
         label=f"Adapted Retest Terminal (Job 1411103, 22,530 FEs, $F_{{max}}=411.85\\,$N)")

# Plot Published References for comparison
axD.plot(df_redig["displacement_um"], df_redig["proposed_pfm_N"], 'r--', linewidth=2.0, alpha=0.85,
         label=f"Published Proposed PFM (Fig. 13a, 19,963 FEs, Peak {df_redig['proposed_pfm_N'].max():.1f} N)")
axD.plot(df_redig["displacement_um"], df_redig["standard_pfm_N"], 'k:', linewidth=1.8, alpha=0.85,
         label=f"Published Standard PFM (Fig. 13a, 37,155 FEs, Peak {df_redig['standard_pfm_N'].max():.1f} N)")

# Mark terminal cutback point for Job 1411103
axD.plot(df_adapt_rf["u_um"].iloc[-1], df_adapt_rf["rf_N"].iloc[-1], 'kx', markersize=10, markeredgewidth=2.5)
axD.annotate(f"Job 1411103 Non-Convergence\n(TERMINAL_PARTIAL at $u=9.42\\,\\mu$m)",
             xy=(df_adapt_rf["u_um"].iloc[-1], df_adapt_rf["rf_N"].iloc[-1]),
             xytext=(df_adapt_rf["u_um"].iloc[-1] + 1.0, df_adapt_rf["rf_N"].iloc[-1] + 30),
             arrowprops=dict(arrowstyle="->", color="navy", lw=1.5),
             bbox=dict(boxstyle="round,pad=0.3", fc="#f0f4ff", ec="navy", alpha=0.9),
             fontsize=8.5, color="navy", fontweight="bold")

axD.set_xlabel("Horizontal Displacement $u_x$ [$\\mu$m]", fontsize=11, fontweight="bold")
axD.set_ylabel("Reaction Force $F_x$ [N]", fontsize=11, fontweight="bold")
axD.set_title("(d) Force-Displacement Response & Solver Execution Benchmark", fontsize=12, fontweight="bold")
axD.set_xlim(0, 20.0)
axD.set_ylim(0, 550)
axD.legend(loc="upper right", fontsize=8.0, framealpha=0.95)
axD.grid(True, linestyle="--", alpha=0.6)

# Save figures
png_path = os.path.join(fig_dir, "fig_mode2_root_cause_and_literature_reconciliation.png")
pdf_path = os.path.join(fig_dir, "fig_mode2_root_cause_and_literature_reconciliation.pdf")
plt.savefig(png_path, dpi=300, bbox_inches='tight')
plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
plt.close()

print(f"Generated reconciliation figures successfully:")
print(f"  PNG: {png_path}")
print(f"  PDF: {pdf_path}")
