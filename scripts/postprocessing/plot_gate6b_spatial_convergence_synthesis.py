#!/usr/bin/env python3
"""
Mode-I Gate-6B Multi-Quantity Spatial Convergence Synthesis Plotter
===================================================================

Generates publication-quality 4-panel multi-quantity comparison figures
for the Mode-I benchmark across spatial discretizations:
  - Fixed Reference 15k (15,192 FE, Job 1409734, full horizon u=10 um)
  - Adaptive ET1 Baseline 14k (14,483 FE, Job 1409982, u=7.889 um, 98.5% drop)
  - ET1 Cn=0.50 Diagnostic (14,483 FE, Job 1410180, full horizon u=10 um)
  - Spatial Fine 58k 8T SMP (57,929 FE, Job 1410504, authoritative full horizon u=10 um)
  - Spatial Fine 58k Serial (57,929 FE, Job 1410179, partial post-peak 24h limit u=7.429 um)

Quantities plotted:
  (a) Structural Reaction Force F(u_y) vs prescribed displacement u_y in [0, 10] um
  (b) External Work W_ext(u_y) and Phase-Field Fracture Energy Functional E_frac(u_y) evolution
  (c) Stored Elastic Strain Energy E_elas(u_y) evolution
  (d) Energy Bookkeeping Discrepancy Delta_book(u_y) evolution

Author: Antigravity Multi-Agent Coordination
Protocol Version: 2
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def parse_dat_file(dat_path):
    records = []
    current_step = 1
    current_inc = 0
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'S T E P       2' in line:
                current_step = 2
            if 'INCREMENT' in line and 'SUMMARY' in line:
                parts = line.split()
                try:
                    inc_idx = parts.index('INCREMENT') + 1
                    current_inc = int(parts[inc_idx])
                except (ValueError, IndexError):
                    pass
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0] == '999999':
                try:
                    u2 = float(parts[1])
                    rf2 = float(parts[2])
                    records.append({'step': current_step, 'inc': current_inc, 'u_mm': u2, 'rf_kN': rf2})
                except ValueError:
                    pass
    return pd.DataFrame(records)

def map_energy_disp(df):
    u = []
    for _, row in df.iterrows():
        s = int(row['Step'])
        st = float(row['StepTime'])
        if s == 1:
            u.append(0.0050 * st)
        else:
            u.append(0.0050 + 0.0050 * st)
    df['u_mm'] = u
    df['e_elas_mJ'] = df['E_elastic_kNmm'] * 1000.0
    df['e_frac_mJ'] = df['E_fracture_kNmm'] * 1000.0
    df['e_tot_mJ'] = df['E_total_kNmm'] * 1000.0
    return df

def generate_plot(base_dir=None, output_dir=None, supervisor_three_case=False):
    if base_dir is None:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sync_doc_figures = output_dir is None
    if output_dir is None:
        output_dir = os.path.join(base_dir, "results", "figures", "mode1_gate6b")
    
    figures_doc_dir = os.path.join(base_dir, "docs", "MA_AdaptiveRemeshing_Report_2026_main", "figures")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(figures_doc_dir, exist_ok=True)
    
    pkg_ref = os.path.join(base_dir, "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k")
    pkg_et1 = os.path.join(base_dir, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
    pkg_cn = os.path.join(base_dir, "models", "pandey_kumar_mode1", "28_stage14_convergence_control_candidate")
    pkg_58k_ser = os.path.join(base_dir, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine")
    pkg_58k_8t = os.path.join(base_dir, "models", "pandey_kumar_mode1", "37_stage14_adaptive_candidate_spatial_fine_8thread")

    # 1. Load Reference (Job 1409734)
    df_ref_dat = parse_dat_file(os.path.join(pkg_ref, "PK_M1_REF15K_ENERGY.dat"))
    df_ref_en = pd.read_csv(os.path.join(pkg_ref, "uel_energy_balance.csv"))
    df_ref_en = map_energy_disp(df_ref_en)

    w_ext_ref = [0.0]
    for i in range(1, len(df_ref_dat)):
        du = df_ref_dat['u_mm'].iloc[i] - df_ref_dat['u_mm'].iloc[i-1]
        f_avg = 0.5 * (df_ref_dat['rf_kN'].iloc[i] + df_ref_dat['rf_kN'].iloc[i-1])
        w_ext_ref.append(w_ext_ref[-1] + f_avg * du * 1000.0)
    df_ref_dat['w_ext_mJ'] = w_ext_ref

    # 2. Load Canonical ET1 (Job 1409982)
    df_et1_fu = pd.read_csv(os.path.join(pkg_et1, "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv"))
    df_et1_en = pd.read_csv(os.path.join(pkg_et1, "uel_energy_balance.csv"))
    df_et1_en = map_energy_disp(df_et1_en)

    # 3. Load ET1 Cn=0.50 Diagnostic (Job 1410180)
    df_cn_fu = pd.read_csv(os.path.join(pkg_cn, "PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv"))

    # 4. Load Spatial Fine 58k 8T SMP (Job 1410504, Full Horizon)
    df_58k_dat = parse_dat_file(os.path.join(pkg_58k_8t, "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_8T.dat"))
    df_58k_en = pd.read_csv(os.path.join(pkg_58k_8t, "uel_energy_balance.csv"))
    df_58k_en = map_energy_disp(df_58k_en)

    w_ext_58k = [0.0]
    for i in range(1, len(df_58k_dat)):
        du = df_58k_dat['u_mm'].iloc[i] - df_58k_dat['u_mm'].iloc[i-1]
        f_avg = 0.5 * (df_58k_dat['rf_kN'].iloc[i] + df_58k_dat['rf_kN'].iloc[i-1])
        w_ext_58k.append(w_ext_58k[-1] + f_avg * du * 1000.0)
    df_58k_dat['w_ext_mJ'] = w_ext_58k

    # 5. Load Spatial Fine 58k Serial (Job 1410179, Partial Diagnostic)
    df_58k_ser_dat = parse_dat_file(os.path.join(pkg_58k_ser, "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.dat"))

    # Merged energy accounting
    df_ref_merged = pd.merge(df_ref_dat, df_ref_en, left_on=['step', 'inc'], right_on=['Step', 'Increment'], suffixes=('_dat', '_en'))
    df_ref_merged['delta_book_mJ'] = df_ref_merged['w_ext_mJ'] - df_ref_merged['e_tot_mJ']
    df_ref_merged['eps_book_pct'] = np.where(df_ref_merged['w_ext_mJ'] > 1e-6, np.abs(df_ref_merged['delta_book_mJ']) / df_ref_merged['w_ext_mJ'] * 100.0, 0.0)

    min_len = min(len(df_et1_fu), len(df_et1_en))
    df_et1_merged = df_et1_fu.iloc[:min_len].copy()
    df_et1_merged['e_elas_mJ'] = df_et1_en['e_elas_mJ'].iloc[:min_len].values
    df_et1_merged['e_frac_mJ'] = df_et1_en['e_frac_mJ'].iloc[:min_len].values
    df_et1_merged['e_tot_mJ'] = df_et1_en['e_tot_mJ'].iloc[:min_len].values
    df_et1_merged['delta_book_mJ'] = df_et1_merged['w_ext_mJ'] - df_et1_merged['e_tot_mJ']
    df_et1_merged['eps_book_pct'] = np.where(df_et1_merged['w_ext_mJ'] > 1e-6, np.abs(df_et1_merged['delta_book_mJ']) / df_et1_merged['w_ext_mJ'] * 100.0, 0.0)

    df_58k_merged = pd.merge(df_58k_dat, df_58k_en, left_on=['step', 'inc'], right_on=['Step', 'Increment'], suffixes=('_dat', '_en'))
    df_58k_merged['delta_book_mJ'] = df_58k_merged['w_ext_mJ'] - df_58k_merged['e_tot_mJ']
    df_58k_merged['eps_book_pct'] = np.where(df_58k_merged['w_ext_mJ'] > 1e-6, np.abs(df_58k_merged['delta_book_mJ']) / df_58k_merged['w_ext_mJ'] * 100.0, 0.0)

    # Plot 2x2 multi-panel figure
    fig, axes = plt.subplots(2, 2, figsize=(12.5, 10.5), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.26)

    plt.rcParams['font.sans-serif'] = 'Arial'
    plt.rcParams['font.family'] = 'sans-serif'

    c_ref = '#111111'
    c_et1 = '#1f77b4'
    c_cn = '#17becf'
    c_58k = '#d62728'
    c_58k_ser = '#ff7f0e'

    # Panel (a): Reaction Force vs Displacement
    ax = axes[0, 0]
    if supervisor_three_case:
        ax.plot(df_ref_dat['u_mm'] * 1000.0, df_ref_dat['rf_kN'], label=r'Fixed Benchmark Anchor 15k ($F_{\max}=0.758$ kN)', color=c_ref, lw=2.0)
        ax.plot(df_et1_fu['displacement_mm'] * 1000.0, df_et1_fu['reaction_force_kN'], label=r'Corrected Adaptive ET1 14k ($F_{\max}=0.744$ kN, $+0.279\%$ vs Fine)', color=c_et1, lw=1.8)
        ax.plot(df_58k_dat['u_mm'] * 1000.0, df_58k_dat['rf_kN'], label=r'Spatial-Fine Adaptive Ref 58k ($F_{\max}=0.742$ kN)', color=c_58k, lw=2.0)
    else:
        ax.plot(df_ref_dat['u_mm'] * 1000.0, df_ref_dat['rf_kN'], label=r'Fixed Benchmark Anchor 15k (Job 1409734, $F_{\max}=0.758$ kN)', color=c_ref, lw=2.0)
        ax.plot(df_et1_fu['displacement_mm'] * 1000.0, df_et1_fu['reaction_force_kN'], label=r'Corrected Adaptive ET1 14k (Job 1409982, $F_{\max}=0.744$ kN)', color=c_et1, lw=1.8)
        ax.plot(df_cn_fu['u_mm'] * 1000.0, df_cn_fu['f_tensile_kN'], label=r'ET1 $C_n=0.50$ Diagnostic (Job 1410180)', color=c_cn, lw=1.5, ls='--')
        ax.plot(df_58k_dat['u_mm'] * 1000.0, df_58k_dat['rf_kN'], label=r'Spatial-Fine Adaptive Ref 58k (Job 1410504, $F_{\max}=0.742$ kN)', color=c_58k, lw=2.0)

    # Annotate Job 1410179 serial parity point
    u_58k_ser_term = df_58k_ser_dat['u_mm'].iloc[-1] * 1000.0
    rf_58k_ser_term = df_58k_ser_dat['rf_kN'].iloc[-1]
    if not supervisor_three_case:
        ax.plot(u_58k_ser_term, rf_58k_ser_term, marker='^', markersize=8, color=c_58k_ser, markeredgecolor='black', markeredgewidth=0.8, zorder=9)
        ax.annotate(f'Serial 24h Stop\nJob 1410179 ($u = 7.429\\,\\mu\\mathrm{{m}}$)',
                    xy=(u_58k_ser_term, rf_58k_ser_term), xytext=(u_58k_ser_term - 3.2, rf_58k_ser_term + 0.16),
                    arrowprops=dict(facecolor=c_58k_ser, shrink=0.08, width=0.8, headwidth=4.0),
                    fontsize=7.8, color='#b25900',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='#fff8e1', edgecolor=c_58k_ser, alpha=0.9))

    # Annotate ET1 baseline stop
    u_et1_term = df_et1_fu['displacement_mm'].iloc[-1] * 1000.0
    rf_et1_term = df_et1_fu['reaction_force_kN'].iloc[-1]
    ax.plot(u_et1_term, rf_et1_term, marker='o', markersize=6, color=c_et1, markeredgecolor='black', markeredgewidth=0.8, zorder=10)
    if not supervisor_three_case:
        ax.annotate(f'ET1 Stagnation\n$u = 7.889\\,\\mu\\mathrm{{m}}$',
                    xy=(u_et1_term, rf_et1_term),
                    xytext=(u_et1_term + 0.25, rf_et1_term + 0.07),
                    fontsize=7.8, color=c_et1)

    ax.set_title('(a) Structural Reaction Force $F(u_y)$', fontsize=11, fontweight='bold')
    ax.set_xlabel('Prescribed Displacement $u_y$ [$\\mu\\mathrm{m}$]', fontsize=10)
    ax.set_ylabel('Reaction Force $F$ [$\\mathrm{kN}$]', fontsize=10)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(-0.02, 0.85)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.9)

    # Panel (b): External Work and Phase-Field Fracture Energy Functional
    ax = axes[0, 1]
    ax.plot(df_ref_merged['u_mm_dat'] * 1000.0, df_ref_merged['w_ext_mJ'], label='$W_{\\mathrm{ext}}$ Benchmark 15k', color=c_ref, lw=1.8)
    ax.plot(df_et1_merged['displacement_mm'] * 1000.0, df_et1_merged['w_ext_mJ'], label='$W_{\\mathrm{ext}}$ Adaptive ET1 14k', color=c_et1, lw=1.8)
    if not supervisor_three_case:
        ax.plot(df_cn_fu['u_mm'] * 1000.0, df_cn_fu['w_ext_mJ'], label='$W_{\\mathrm{ext}}$ $C_n=0.50$', color=c_cn, lw=1.4, ls=':')
    ax.plot(df_58k_merged['u_mm_dat'] * 1000.0, df_58k_merged['w_ext_mJ'], label='$W_{\\mathrm{ext}}$ Fine Adapt 58k', color=c_58k, lw=2.0)

    ax.plot(df_ref_merged['u_mm_dat'] * 1000.0, df_ref_merged['e_frac_mJ'], label='$\\mathcal{E}_{\\mathrm{frac}}$ Benchmark 15k', color=c_ref, lw=1.8, ls='--')
    ax.plot(df_et1_merged['displacement_mm'] * 1000.0, df_et1_merged['e_frac_mJ'], label='$\\mathcal{E}_{\\mathrm{frac}}$ Adaptive ET1 14k', color=c_et1, lw=1.8, ls='--')
    if not supervisor_three_case:
        ax.plot(df_cn_fu['u_mm'] * 1000.0, df_cn_fu['e_frac_mJ'], label='$\\mathcal{E}_{\\mathrm{frac}}$ $C_n=0.50$', color=c_cn, lw=1.4, ls='-.')
    ax.plot(df_58k_merged['u_mm_dat'] * 1000.0, df_58k_merged['e_frac_mJ'], label='$\\mathcal{E}_{\\mathrm{frac}}$ Fine Adapt 58k', color=c_58k, lw=2.0, ls='--')

    ax.set_title('(b) External Work $W_{\\mathrm{ext}}$ & Fracture Surface Functional $\\mathcal{E}_{\\mathrm{frac}}$', fontsize=11, fontweight='bold')
    ax.set_xlabel('Prescribed Displacement $u_y$ [$\\mu\\mathrm{m}$]', fontsize=10)
    ax.set_ylabel('Energy [$\\mathrm{mJ}$]', fontsize=10)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(-0.1, 2.7)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', fontsize=7.4, ncol=2, framealpha=0.9)

    # Panel (c): Stored Elastic Strain Energy
    ax = axes[1, 0]
    ax.plot(df_ref_merged['u_mm_dat'] * 1000.0, df_ref_merged['e_elas_mJ'], label='Fixed Benchmark Anchor 15k', color=c_ref, lw=1.8)
    ax.plot(df_et1_merged['displacement_mm'] * 1000.0, df_et1_merged['e_elas_mJ'], label='Corrected Adaptive ET1 14k', color=c_et1, lw=1.8)
    if not supervisor_three_case:
        ax.plot(df_cn_fu['u_mm'] * 1000.0, df_cn_fu['e_elas_mJ'], label='ET1 $C_n=0.50$ Diagnostic (Job 1410180)', color=c_cn, lw=1.5, ls='--')
    ax.plot(df_58k_merged['u_mm_dat'] * 1000.0, df_58k_merged['e_elas_mJ'], label='Spatial-Fine Adaptive Ref 58k', color=c_58k, lw=2.0)

    ax.set_title('(c) Stored Elastic Strain Energy $\\mathcal{E}_{\\mathrm{elas}}(u_y)$', fontsize=11, fontweight='bold')
    ax.set_xlabel('Prescribed Displacement $u_y$ [$\\mu\\mathrm{m}$]', fontsize=10)
    ax.set_ylabel('Elastic Energy $\\mathcal{E}_{\\mathrm{elas}}$ [$\\mathrm{mJ}$]', fontsize=10)
    ax.set_xlim(0, 10.2)
    ax.set_ylim(-0.05, 2.3)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=7.8, framealpha=0.9)

    # Panel (d): Energy Bookkeeping Discrepancy Evolution
    ax = axes[1, 1]
    ax.plot(df_ref_merged['u_mm_dat'] * 1000.0, df_ref_merged['delta_book_mJ'] * 1000.0, label='Fixed Benchmark 15k ($\\Delta_{\\mathrm{book}}$, 0.76%)', color=c_ref, lw=1.8)
    ax.plot(df_et1_merged['displacement_mm'] * 1000.0, df_et1_merged['delta_book_mJ'] * 1000.0, label='Adaptive ET1 14k ($\\Delta_{\\mathrm{book}}$, 1.10%)', color=c_et1, lw=1.8)
    if not supervisor_three_case:
        ax.plot(df_cn_fu['u_mm'] * 1000.0, df_cn_fu['delta_book_mJ'] * 1000.0, label='ET1 $C_n=0.50$ Diagnostic ($\\Delta_{\\mathrm{book}}$, 0.82%)', color=c_cn, lw=1.5, ls='--')
    ax.plot(df_58k_merged['u_mm_dat'] * 1000.0, df_58k_merged['delta_book_mJ'] * 1000.0, label='Spatial-Fine Adaptive 58k ($\\Delta_{\\mathrm{book}}$, 4.43%)', color=c_58k, lw=2.0)

    ax.axhline(0, color='gray', linestyle='-', linewidth=0.8, alpha=0.7)

    ax.set_title('(d) Energy Bookkeeping Discrepancy $\\Delta_{\\mathrm{book}}(u_y)$', fontsize=11, fontweight='bold')
    ax.set_xlabel('Prescribed Displacement $u_y$ [$\\mu\\mathrm{m}$]', fontsize=10)
    ax.set_ylabel('$\\Delta_{\\mathrm{book}} = W_{\\mathrm{ext}} - (\\mathcal{E}_{\\mathrm{elas}} + \\mathcal{E}_{\\mathrm{frac}})$ [$\\mu\\mathrm{J}$]', fontsize=10)
    ax.set_xlim(0, 10.2)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper left', fontsize=7.8, framealpha=0.9)

    if supervisor_three_case:
        # Legends sit in dedicated space below each panel, clear of all curves.
        fig.set_size_inches(13.5, 12.0)
        fig.subplots_adjust(hspace=0.78, wspace=0.28, bottom=0.15, top=0.94)
        for panel in axes.flat:
            handles, labels = panel.get_legend_handles_labels()
            panel.get_legend().remove()
            if panel is axes[0, 0]:
                labels = ['Fixed benchmark (15,192 FE)', 'Corrected ET1 (14,483 FE)',
                          'Spatial-fine adaptive (57,929 FE)']
            panel.legend(handles, labels, loc='upper center',
                         bbox_to_anchor=(0.5, -0.23), ncol=2 if panel is axes[0, 1] else 1,
                         fontsize=9, frameon=False, borderaxespad=0)

    pdf_path = os.path.join(output_dir, "fig_mode1_gate6b_spatial_convergence_synthesis.pdf")
    png_path = os.path.join(output_dir, "fig_mode1_gate6b_spatial_convergence_synthesis.png")

    plt.savefig(pdf_path, bbox_inches='tight')
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    
    # Keep the thesis copy synchronized only for the canonical all-case figure.
    if sync_doc_figures and not supervisor_three_case:
        plt.savefig(os.path.join(figures_doc_dir, "fig_mode1_gate6b_spatial_convergence_synthesis.pdf"), bbox_inches='tight')
        plt.savefig(os.path.join(figures_doc_dir, "fig_mode1_gate6b_spatial_convergence_synthesis.png"), bbox_inches='tight', dpi=300)
    
    plt.close()
    return pdf_path, png_path

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Generate Gate-6B Spatial Convergence Synthesis Figure")
    parser.add_argument("--base-dir", type=str, default=None, help="Project base directory")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for figures")
    parser.add_argument("--supervisor-three-case", action="store_true",
                        help="Plot only fixed reference, corrected ET1, and spatial-fine adaptive cases")
    args = parser.parse_args()
    
    pdf_out, png_out = generate_plot(args.base_dir, args.output_dir, args.supervisor_three_case)
    print(f"Plot generation complete:\n  {pdf_out}\n  {png_out}")
