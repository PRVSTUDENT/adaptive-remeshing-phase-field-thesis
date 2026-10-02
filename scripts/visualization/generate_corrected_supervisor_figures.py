#!/usr/bin/env python3
"""
generate_corrected_supervisor_figures.py

Regenerates corrected figures for the 01-October-2026 Mode-I Supervisor Meeting Report:
1. fig_mode1_spatial_fu_convergence (and FIGURE_M1_SPATIAL_CONVERGENCE):
   - Title: Mode-I Tensile Force-Displacement Response (Spatial Series S1--S4 + Historical Fine Mesh)
   - Legend for 69k mesh: "Historical fine mesh (h=1.00 um, 69k, Cutback u=9.58 um)"
2. fig_mode1_s1_energy_balance (and FIGURE_M1_S1_ENERGY_EVOLUTION):
   - Title: Global Energy Component Evolution (Baseline S1 / T2 Series)
   - Regenerated from authoritative S1/T2 mechanical & energy balance evidence
   - Proper displacement scaling in microns (u in [0, 10.0] um)
   - Two-term bookkeeping difference R_bookkeeping = W_trap - (E_elas + E_frac) [mJ]
"""
import os
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Base paths
base_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\batch_mode1_energy_convergence"
meeting_pack_fig_dir = r"D:\Master thesis\Adaptive remeshing\docs\supervisor_reports\01-10-2026\MA_ModeI_Supervisor_Meeting_Pack_2026-10-01\figures"
report_fig_dir = r"D:\Master thesis\Adaptive remeshing\docs\MA_AdaptiveRemeshing_Report_2026_main\figures"
repro_fig_dir = r"D:\Master thesis\Adaptive remeshing\ModeI_Supervisor_Report_Reproduction_Package\images"

output_dirs = [d for d in [meeting_pack_fig_dir, base_dir, report_fig_dir, repro_fig_dir] if os.path.exists(d)]

plt.rcParams.update({
    'font.size': 11,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9.5,
    'figure.titlesize': 14,
    'lines.linewidth': 1.8,
    'grid.linestyle': '--',
    'grid.alpha': 0.6
})

def parse_fu(csv_path):
    u_list, rf_list = [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        u_idx, rf_idx = 0, 1
        for i, h in enumerate(header):
            hl = h.lower()
            if "u" in hl or "disp" in hl: u_idx = i
            elif "rf" in hl or "force" in hl: rf_idx = i
        for row in reader:
            if len(row) > max(u_idx, rf_idx):
                try:
                    u_list.append(float(row[u_idx]))
                    rf_list.append(float(row[rf_idx]))
                except ValueError:
                    pass
    return np.array(u_list), np.array(rf_list)

def save_fig(fig, base_name):
    for d in output_dirs:
        p_png = os.path.join(d, base_name + ".png")
        p_pdf = os.path.join(d, base_name + ".pdf")
        fig.savefig(p_png, dpi=300, bbox_inches='tight')
        fig.savefig(p_pdf, bbox_inches='tight')
        print(f"Saved {p_png} and {p_pdf}")

# ==============================================================================
# 1. REGENERATE FIGURE 10: SPATIAL F-U CONVERGENCE (S1-S4 + HISTORICAL FINE MESH)
# ==============================================================================
print("\n--- Generating Spatial F-u Convergence Figure ---")
s1_u, s1_rf = parse_fu(os.path.join(base_dir, "S1_h0030_15k_MECHANICAL_FU_AUDITED.csv"))
s2_u, s2_rf = parse_fu(os.path.join(base_dir, "S2_h0020_32k_MECHANICAL_FU_AUDITED.csv"))
s3_u, s3_rf = parse_fu(os.path.join(base_dir, "S3_h0015_42k_MECHANICAL_FU_AUDITED.csv"))
s4_u, s4_rf = parse_fu(os.path.join(base_dir, "S4_h00125_51k_MECHANICAL_FU_AUDITED.csv"))
s5_u, s5_rf = parse_fu(os.path.join(base_dir, "S5_h00100_69k_MECHANICAL_FU_AUDITED.csv"))

fig, ax = plt.subplots(figsize=(8.5, 6))
ax.plot(s1_u * 1000, s1_rf, 'k-', label=r"$S_1$ ($h=3.00\,\mu\mathrm{m}$, 15k, Full to $10\,\mu\mathrm{m}$)", linewidth=2.0)
ax.plot(s2_u * 1000, s2_rf, 'b--', label=r"$S_2$ ($h=2.00\,\mu\mathrm{m}$, 32k, Cutback $u=6.82\,\mu\mathrm{m}$)")
ax.plot(s3_u * 1000, s3_rf, 'g-.', label=r"$S_3$ ($h=1.50\,\mu\mathrm{m}$, 42k, Cutback $u=7.84\,\mu\mathrm{m}$)")
ax.plot(s4_u * 1000, s4_rf, 'm:', label=r"$S_4$ ($h=1.25\,\mu\mathrm{m}$, 51k, Cutback $u=7.21\,\mu\mathrm{m}$)", linewidth=2.0)
ax.plot(s5_u * 1000, s5_rf, color='darkorange', linestyle='-', label=r"Historical fine mesh ($h=1.00\,\mu\mathrm{m}$, 69k, Cutback $u=9.58\,\mu\mathrm{m}$)", alpha=0.9)

ax.scatter([s2_u[-1]*1000], [s2_rf[-1]], color='blue', s=45, zorder=5, marker='o')
ax.scatter([s3_u[-1]*1000], [s3_rf[-1]], color='green', s=45, zorder=5, marker='s')
ax.scatter([s4_u[-1]*1000], [s4_rf[-1]], color='magenta', s=45, zorder=5, marker='^')
ax.scatter([s5_u[-1]*1000], [s5_rf[-1]], color='darkorange', s=45, zorder=5, marker='D')

ax.set_xlabel(r"Prescribed Displacement $u$ [$\mu\mathrm{m}$]")
ax.set_ylabel(r"Reaction Force $F$ [$\mathrm{kN}$]")
ax.set_title("Mode-I Tensile Force-Displacement Response (Spatial Series S1--S4 + Historical Fine Mesh)")
ax.set_xlim([0.0, 10.2])
ax.set_ylim([-0.02, 0.82])
ax.grid(True)
ax.legend(loc='upper right')

# Inset peak region
ax_ins = ax.inset_axes([0.10, 0.18, 0.38, 0.38])
ax_ins.plot(s1_u * 1000, s1_rf, 'k-', linewidth=1.5)
ax_ins.plot(s2_u * 1000, s2_rf, 'b--', linewidth=1.5)
ax_ins.plot(s3_u * 1000, s3_rf, 'g-.', linewidth=1.5)
ax_ins.plot(s4_u * 1000, s4_rf, 'm:', linewidth=1.8)
ax_ins.plot(s5_u * 1000, s5_rf, color='darkorange', linestyle='-', linewidth=1.5)
ax_ins.set_xlim([5.2, 6.0])
ax_ins.set_ylim([0.65, 0.77])
ax_ins.set_title("Peak Region", fontsize=9)
ax_ins.grid(True, alpha=0.4)

save_fig(fig, "fig_mode1_spatial_fu_convergence")
save_fig(fig, "FIGURE_M1_SPATIAL_CONVERGENCE")
plt.close(fig)

# ==============================================================================
# 2. REGENERATE FIGURE 18: AUTHORITATIVE S1/T2 ENERGY EVOLUTION AND BALANCE
# ==============================================================================
print("\n--- Generating Authoritative S1/T2 Energy Balance Figure ---")

# Step A: Compute cumulative external work W_trap from S1/T2 mechanical response
# S1 (Job 1406015 / T2 Job 1406021) has u in mm, rf in kN
w_trap_cum = np.zeros_like(s1_u)
for i in range(1, len(s1_u)):
    du = s1_u[i] - s1_u[i-1]
    f_avg = 0.5 * (s1_rf[i] + s1_rf[i-1])
    w_trap_cum[i] = w_trap_cum[i-1] + f_avg * du # in kN*mm = J
w_trap_mJ = w_trap_cum * 1000.0 # in mJ

# Step B: Parse UEL energy components from uel_energy_balance.csv
eb_csv = os.path.join(base_dir, "S1_h0030_15k_diagnostic_r2", "uel_energy_balance.csv")
eb_u_um = []
eb_eelas_mJ = []
eb_efrac_mJ = []
eb_etot_mJ = []

with open(eb_csv, "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    header = next(reader)
    # Header: Step, Increment, TotalTime, StepTime, E_elastic_kNmm, E_fracture_kNmm, E_total_kNmm
    for row in reader:
        if len(row) >= 7:
            try:
                step = int(row[0].strip())
                inc = int(row[1].strip())
                step_time = float(row[3].strip())
                e_elas_knmm = float(row[4].strip())
                e_frac_knmm = float(row[5].strip())
                e_tot_knmm = float(row[6].strip())

                # Exact physical displacement u in mm:
                # Step 1: linear ramp from 0 to 0.005 mm (stroke 0.005 mm)
                # Step 2: linear ramp from 0.005 to 0.010 mm (stroke 0.005 mm)
                if step == 1:
                    u_mm = step_time * 0.005
                elif step == 2:
                    u_mm = 0.005 + step_time * 0.005
                else:
                    continue

                u_um = u_mm * 1000.0
                eb_u_um.append(u_um)
                eb_eelas_mJ.append(e_elas_knmm * 1000.0)
                eb_efrac_mJ.append(e_frac_knmm * 1000.0)
                eb_etot_mJ.append(e_tot_knmm * 1000.0)
            except ValueError:
                pass

eb_u_um = np.array(eb_u_um)
eb_eelas_mJ = np.array(eb_eelas_mJ)
eb_efrac_mJ = np.array(eb_efrac_mJ)
eb_etot_mJ = np.array(eb_etot_mJ)

# Step C: Interpolate W_trap at exact energy evaluation points
s1_u_um = s1_u * 1000.0
eb_wtrap_mJ = np.interp(eb_u_um, s1_u_um, w_trap_mJ)

# Step D: Compute two-term bookkeeping difference
eb_rbook_mJ = eb_wtrap_mJ - (eb_eelas_mJ + eb_efrac_mJ)

print(f"Energy balance points parsed: {len(eb_u_um)}")
print(f"Displacement range: {eb_u_um[0]:.4f} to {eb_u_um[-1]:.4f} um")
print(f"Terminal W_trap: {eb_wtrap_mJ[-1]:.6f} mJ")
print(f"Terminal E_elas: {eb_eelas_mJ[-1]:.6f} mJ")
print(f"Terminal E_frac: {eb_efrac_mJ[-1]:.6f} mJ")
print(f"Terminal R_book: {eb_rbook_mJ[-1]:.6f} mJ ({eb_rbook_mJ[-1]/eb_wtrap_mJ[-1]*100:.4f}%)")

# Pre-peak check:
pre_idx = np.where(eb_u_um <= 5.0)[0]
max_pre_rbook = np.max(np.abs(eb_rbook_mJ[pre_idx]))
print(f"Pre-peak (u <= 5.0 um) max |R_book|: {max_pre_rbook:.8f} mJ")

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 8), sharex=True, gridspec_kw={'height_ratios': [2.5, 1]})

ax1.plot(eb_u_um, eb_wtrap_mJ, 'k-', label=r"External Work $W_{\mathrm{trap}}$", linewidth=2.2)
ax1.plot(eb_u_um, eb_eelas_mJ, 'b--', label=r"Elastic Strain Energy $E_{\mathrm{elas}}$", linewidth=1.8)
ax1.plot(eb_u_um, eb_efrac_mJ, 'r-.', label=r"Fracture Surface Energy $E_{\mathrm{frac}}$", linewidth=1.8)
ax1.plot(eb_u_um, eb_eelas_mJ + eb_efrac_mJ, 'g:', label=r"Two-Term Internal Energy Sum $E_{\mathrm{elas}} + E_{\mathrm{frac}}$", linewidth=2.0)

ax1.set_ylabel(r"Energy [$\mathrm{mJ}$] ($1\,\mathrm{mJ} = 10^{-3}\,\mathrm{kN\cdot mm}$)")
ax1.set_title("Global Energy Component Evolution (Baseline S1 / T2 Series)")
ax1.set_xlim([0.0, 10.2])
ax1.set_ylim([-0.05, 2.55])
ax1.grid(True)
ax1.legend(loc='center left')

# Annotate peak and post-peak transition
ax1.axvline(x=5.857, color='gray', linestyle=':', alpha=0.7)
ax1.text(5.95, 1.4, r"Peak load ($u_{\mathrm{peak}} = 5.86\,\mu\mathrm{m}$)", fontsize=9, color='dimgray')

# Bottom panel: Bookkeeping difference
ax2.plot(eb_u_um, eb_rbook_mJ, color='darkviolet', label=r"Two-Term Bookkeeping Diff $\mathcal{R}_{\mathrm{bookkeeping}} \equiv W_{\mathrm{trap}} - (E_{\mathrm{elas}} + E_{\mathrm{frac}})$")
ax2.set_xlabel(r"Prescribed Displacement $u$ [$\mu\mathrm{m}$]")
ax2.set_ylabel(r"Diff $\mathcal{R}_{\mathrm{book}}$ [$\mathrm{mJ}$]")
ax2.set_xlim([0.0, 10.2])
ax2.set_ylim([-0.002, 0.025])
ax2.grid(True)
ax2.legend(loc='upper left')

plt.tight_layout()
save_fig(fig, "fig_mode1_s1_energy_balance")
save_fig(fig, "FIGURE_M1_S1_ENERGY_EVOLUTION")
plt.close(fig)

# ==============================================================================
# 3. REGENERATE FIGURE 13: ADAPTIVE MESH CONVERGENCE (A1-A4 vs S1)
# ==============================================================================
print("\n--- Generating Adaptive Convergence Figure without W=4.26mJ ---")
a1_u, a1_rf = parse_fu(os.path.join(base_dir, "A1_adapt_1pct_71k_full_u010_MECHANICAL_FU_AUDITED.csv"))
a2_u, a2_rf = parse_fu(os.path.join(base_dir, "A2_adapt_2pct_15k_corrected_MECHANICAL_FU_AUDITED.csv"))
a3_u, a3_rf = parse_fu(os.path.join(base_dir, "A3_adapt_3pct_8k_corrected_MECHANICAL_FU_AUDITED.csv"))
a4_u, a4_rf = parse_fu(os.path.join(base_dir, "A4_adapt_5pct_4k_corrected_MECHANICAL_FU_AUDITED.csv"))

fig, ax = plt.subplots(figsize=(8.5, 6))
ax.plot(s1_u * 1000, s1_rf, 'k--', label=r"$S_1$ Uniform Ref ($15{,}192$ cells, $h=3\,\mu\mathrm{m}$)", linewidth=2.0)
ax.plot(a1_u * 1000, a1_rf, 'darkred', label=r"$A_1$ (1% Target Error, $71{,}320$ finite elements, Cutback $u=6.77\,\mu\mathrm{m}$)")
ax.plot(a2_u * 1000, a2_rf, 'darkblue', label=r"$A_2$ (2% Target Error, $15{,}396$ finite elements, Full to $10\,\mu\mathrm{m}$)")
ax.plot(a3_u * 1000, a3_rf, 'purple', label=r"$A_3$ (3% Target Error, $7{,}633$ finite elements, Full to $10\,\mu\mathrm{m}$)")
ax.plot(a4_u * 1000, a4_rf, 'darkorange', linestyle=':', label=r"$A_4$ (5% Target Error, $4{,}194$ finite elements, Full to $10\,\mu\mathrm{m}$)", linewidth=2.0)

ax.scatter([a1_u[-1]*1000], [a1_rf[-1]], color='darkred', s=45, zorder=5, marker='o')

ax.set_xlabel(r"Prescribed Displacement $u$ [$\mu\mathrm{m}$]")
ax.set_ylabel(r"Reaction Force $F$ [$\mathrm{kN}$]")
ax.set_title("Mode-I Force-Displacement Response for Native Adaptive Meshes (A1--A4 vs S1)")
ax.set_xlim([0.0, 10.2])
ax.set_ylim([-0.02, 0.85])
ax.grid(True)
ax.legend(loc='upper right')

ax.text(0.03, 0.15, 
        "Production UEL lineage: 71,320 (A1), 15,396 (A2), 7,633 (A3), 4,194 (A4).\n"
        "Offline sensitivity study (pre-analysis): 71,320 (1%), 17,687 (2%), 8,120 (3%), 4,356 (5%).\n"
        "A4 exhibits elevated plateau (F ~ 0.75 kN); OBSERVED_FORCE_PLATEAU (CRACK-PINNING HYPOTHESIS / NOT YET INDEPENDENTLY PROVEN).",
        transform=ax.transAxes, fontsize=8.2,
        bbox=dict(boxstyle='round,pad=0.5', facecolor='whitesmoke', edgecolor='gray', alpha=0.9))

save_fig(fig, "fig_mode1_adaptive_convergence")
save_fig(fig, "FIGURE_M1_ADAPTIVE_CONVERGENCE")
plt.close(fig)

print("\n=== All Corrected Figures Successfully Generated ===")
