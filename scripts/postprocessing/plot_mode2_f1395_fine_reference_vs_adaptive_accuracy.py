#!/usr/bin/env python3
"""
plot_mode2_f1395_fine_reference_vs_adaptive_accuracy.py
Publication-Quality Master Synthesis: Fixed Fine 72k Reference vs Native Adaptive ET3 Fracture Response.

Author: Gemini Antigravity (Autonomous Scientific Agent)
Task: F1395 — Mode-II Fine Reference Qualification & Adaptive Accuracy Synthesis
Date: 2026-10-10
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
EVIDENCE_DIR = os.path.join(REPO_ROOT, 'runs', 'mode2', 'fixed_convergence', 'evidence')
FIG_DIR = os.path.join(REPO_ROOT, 'results', 'figures', 'mode2')
os.makedirs(FIG_DIR, exist_ok=True)

def parse_dat_rp(dat_path):
    if not os.path.exists(dat_path):
        return np.array([]), np.array([])
    u_vals, rf_vals = [], []
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if line.strip().startswith('999999'):
                parts = line.split()
                if len(parts) >= 3:
                    try:
                        u_vals.append(float(parts[1]))
                        rf_vals.append(float(parts[2]))
                    except ValueError:
                        pass
    return np.array(u_vals), np.array(rf_vals)

def generate_f1395_synthesis_figure():
    # 1. Load Datasets
    u_72k, rf_72k = parse_dat_rp(os.path.join(EVIDENCE_DIR, '04_fine_72k', 'M2_FIX_FINE_72K.dat'))
    u_et3, rf_et3 = parse_dat_rp(os.path.join(EVIDENCE_DIR, 'et3_adapt_21k', 'Job-2_UEL.dat'))
    u_et2, rf_et2 = parse_dat_rp(os.path.join(EVIDENCE_DIR, 'et2_adapt_37k', 'Job-2_UEL.dat'))
    u_40k, rf_40k = parse_dat_rp(os.path.join(EVIDENCE_DIR, '03_int_40k', 'M2_FIX_INT_40K.dat'))
    u_18k, rf_18k = parse_dat_rp(os.path.join(EVIDENCE_DIR, '02_med_18k', 'M2_FIX_MED_18K.dat'))
    u_2p5k, rf_2p5k = parse_dat_rp(os.path.join(EVIDENCE_DIR, '01_coarse_2p5k', 'M2_FIX_COARSE_2P5K.dat'))

    u_72k_um = u_72k * 1000.0
    rf_72k_n = rf_72k * 1000.0
    u_et3_um = u_et3 * 1000.0
    rf_et3_n = rf_et3 * 1000.0
    u_et2_um = u_et2 * 1000.0
    rf_et2_n = rf_et2 * 1000.0

    # Literature curve
    lit_u = np.array([0.0, 2.0, 4.0, 6.0, 7.0, 7.5, 8.0, 8.3, 8.5, 9.0, 10.0, 12.0, 15.0, 20.0])
    lit_f = np.array([0.0, 91.4, 182.7, 274.1, 319.8, 342.6, 361.0, 365.74, 360.0, 345.0, 330.0, 320.0, 312.0, 305.0])

    # Crack paths
    df_crack_72k = pd.read_csv(os.path.join(EVIDENCE_DIR, '04_fine_72k', 'fine_72k_extracted_crack_path.csv'))
    df_crack_et3 = pd.read_csv(os.path.join(EVIDENCE_DIR, 'et3_adapt_21k', 'mode2_extracted_crack_path.csv'))

    plt.rcParams.update({
        'font.size': 11,
        'font.family': 'serif',
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 9.5,
        'figure.titlesize': 14,
        'lines.linewidth': 1.8,
        'grid.alpha': 0.4
    })

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # --- PANEL 1: Global Force-Displacement Response ---
    ax1.plot(u_72k_um, rf_72k_n, '-', color='#d62728', lw=2.4, label='Fixed Fine 72k Reference ($71.8\\mathrm{k}$ FEs, Exit 0)')
    ax1.plot(u_et3_um, rf_et3_n, '--', color='#1f77b4', lw=2.2, label='Adapted ET3 ($21.1\\mathrm{k}$ FEs, Exit 0, $0.91\\%$ Peak Err)')
    ax1.plot(u_et2_um, rf_et2_n, ':', color='#8c564b', lw=1.8, label='Adapted ET2 ($37.6\\mathrm{k}$ FEs, Partial @ $9.42\\,\\mu\\mathrm{m}$)')
    ax1.plot(u_40k * 1000.0, rf_40k * 1000.0, '-.', color='#ff7f0e', lw=1.4, alpha=0.7, label='Fixed Interm. 40k ($40.0\\mathrm{k}$ FEs, Exit 1)')
    ax1.plot(u_18k * 1000.0, rf_18k * 1000.0, '-.', color='#2ca02c', lw=1.4, alpha=0.7, label='Fixed Medium 18k ($18.0\\mathrm{k}$ FEs, Exit 0)')
    ax1.plot(lit_u, lit_f, 'k:', lw=2.0, label='Published Fig. 13(a) (Digitized, $F_{\\max}=365.7\\,\\mathrm{N}$)')

    # Markers for peaks
    ax1.plot(9.47, 415.99, 'o', color='#d62728', markersize=6)
    ax1.plot(9.41, 412.21, '^', color='#1f77b4', markersize=6)

    ax1.annotate('Fine 72k Peak\n$415.99\\,\\mathrm{N}$ @ $9.47\\,\\mu\\mathrm{m}$', xy=(9.47, 415.99), xytext=(5.5, 470.0),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='#d62728'))
    ax1.annotate('Adapted ET3 Peak\n$412.21\\,\\mathrm{N}$ @ $9.41\\,\\mu\\mathrm{m}$ ($-0.91\\%$)', xy=(9.41, 412.21), xytext=(10.5, 460.0),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='#1f77b4'))

    ax1.set_xlabel('Prescribed Shear Displacement $u_x$ [$\\mu\\mathrm{m}$]')
    ax1.set_ylabel('Reaction Force $RF_1$ [$\\mathrm{N}$]')
    ax1.set_title('(a) Full Fracture Response: Fixed Fine vs. Adaptive Solutions')
    ax1.set_xlim(0.0, 20.5)
    ax1.set_ylim(0.0, 550.0)
    ax1.grid(True, linestyle=':')
    ax1.legend(loc='lower right', framealpha=0.92)

    # --- PANEL 2: Pointwise Discrepancy & Relative Force Error ---
    u_grid = np.linspace(0.0, 20.0, 2001)
    rf_72k_grid = np.interp(u_grid, u_72k_um, rf_72k_n)
    rf_et3_grid = np.interp(u_grid, u_et3_um, rf_et3_n)

    abs_err = np.abs(rf_et3_grid - rf_72k_grid)
    rel_err = np.zeros_like(u_grid)
    mask = rf_72k_grid > 5.0
    rel_err[mask] = (rf_et3_grid[mask] - rf_72k_grid[mask]) / rf_72k_grid[mask] * 100.0

    color_err = '#1f77b4'
    ax2.plot(u_grid, rel_err, '-', color=color_err, lw=2.0, label='Signed Relative Error: $(RF_{\\mathrm{ET3}} - RF_{\\mathrm{72k}}) / RF_{\\mathrm{72k}}$')
    ax2.axhline(0.0, color='k', linestyle='-', lw=0.8)
    ax2.axhline(-0.91, color='#d62728', linestyle='--', lw=1.2, label='Peak Force Relative Error ($-0.91\\%$)')
    ax2.axhline(-1.82, color='#2ca02c', linestyle=':', lw=1.2, label='Terminal Force Error @ $20\\,\\mu\\mathrm{m}$ ($-1.82\\%$)')

    # Shading for pre-peak regime
    ax2.axvspan(0.0, 9.47, color='#2ca02c', alpha=0.08, label='Pre-Peak Elastic & Initiation Zone ($|\\mathrm{Err}| < 0.45\\%$)')
    ax2.axvspan(9.47, 20.0, color='#ff7f0e', alpha=0.06, label='Post-Peak Propagation Zone')

    ax2.set_xlabel('Prescribed Shear Displacement $u_x$ [$\\mu\\mathrm{m}$]')
    ax2.set_ylabel('Relative Reaction Force Error [$\\%$]')
    ax2.set_title('(b) Pointwise Relative Force Discrepancy across 20 $\\mu\\mathrm{m}$ Horizon')
    ax2.set_xlim(0.0, 20.5)
    ax2.set_ylim(-15.0, 5.0)
    ax2.grid(True, linestyle=':')
    ax2.legend(loc='lower left', framealpha=0.92)

    # --- PANEL 3: Comparative Crack Trajectory Alignment ---
    ax3.plot(df_crack_72k['x_weighted_d_mm'], df_crack_72k['y_station_mm'], 'o-', color='#d62728', lw=2.2, markersize=4.5, label='Fixed Fine 72k Crack Path ($\\theta = -61.25^\\circ$, Exit 0)')
    ax3.plot(df_crack_et3['x_weighted_d_mm'], df_crack_et3['y_station_mm'], 's--', color='#1f77b4', lw=2.0, markersize=4.5, label='Adapted ET3 Crack Path ($\\theta = -58.04^\\circ$, Exit 0)')

    # Initial notch / seam
    ax3.plot([0.0, 0.50], [0.50, 0.50], 'k-', lw=3.0, label='Initial Zero-Gap Crack Seam ($a_0=0.5\\,\\mathrm{mm}$)')

    # Specimen boundaries
    ax3.plot([0.0, 1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0, 0.0], 'k--', lw=0.8, alpha=0.5)

    ax3.annotate('Crack Initiation\n$(0.50, 0.50)$', xy=(0.50, 0.50), xytext=(0.35, 0.58),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='black'))
    ax3.annotate('Fine 72k Tip @ $20\\,\\mu\\mathrm{m}$\n$h_{\\mathrm{lig}} = 60\\,\\mu\\mathrm{m}$ ($88.0\\%$ traversed)', xy=(0.776, 0.06), xytext=(0.60, 0.15),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='#d62728'))
    ax3.annotate('ET3 Tip @ $20\\,\\mu\\mathrm{m}$\n$h_{\\mathrm{lig}} = 56\\,\\mu\\mathrm{m}$ ($88.7\\%$ traversed)', xy=(0.770, 0.056), xytext=(0.50, 0.02),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='#1f77b4'))

    ax3.set_xlabel('Spatial Coordinate $x$ [$\\mathrm{mm}$]')
    ax3.set_ylabel('Spatial Coordinate $y$ [$\\mathrm{mm}$]')
    ax3.set_title('(c) Crack Trajectory Alignment & Ligament Traversal ($\\|\\Delta x\\| < 0.27\\,l_0$)')
    ax3.set_xlim(0.30, 0.95)
    ax3.set_ylim(-0.02, 0.65)
    ax3.grid(True, linestyle=':')
    ax3.legend(loc='upper right', framealpha=0.92)

    # --- PANEL 4: Computational Cost & Speedup Metrics ---
    metrics = ['Finite Elements', 'Walltime [hours]', 'CPU Time [hours]', 'Peak RAM [GB]']
    val_72k = [71824 / 1000.0, 86126 / 3600.0, 79600 / 3600.0, 3.0]
    val_et3 = [21063 / 1000.0, 30900 / 3600.0, 30750 / 3600.0, 1.5]
    labels_k = ['Elements [$\\times 10^3$]', 'Walltime [h]', 'CPU Time [h]', 'Peak RAM [GB]']

    x_idx = np.arange(len(metrics))
    width = 0.35

    rects1 = ax4.bar(x_idx - width/2, val_72k, width, label='Fixed Fine 72k', color='#d62728', alpha=0.85, edgecolor='black')
    rects2 = ax4.bar(x_idx + width/2, val_et3, width, label='Adapted ET3', color='#1f77b4', alpha=0.85, edgecolor='black')

    # Add text labels on bars
    for rect, val in zip(rects1, val_72k):
        ax4.text(rect.get_x() + rect.get_width()/2.0, val + 0.6, f'{val:.1f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')
    for rect, val in zip(rects2, val_et3):
        ax4.text(rect.get_x() + rect.get_width()/2.0, val + 0.6, f'{val:.1f}', ha='center', va='bottom', fontsize=9.5, fontweight='bold')

    # Annotate speedup / reduction percentages
    ax4.text(0, max(val_72k[0], val_et3[0]) + 5.5, '-70.7%', ha='center', color='#1f77b4', fontweight='bold', fontsize=11)
    ax4.text(1, max(val_72k[1], val_et3[1]) + 2.5, '2.79x faster\n(-64.1%)', ha='center', color='#1f77b4', fontweight='bold', fontsize=10)
    ax4.text(2, max(val_72k[2], val_et3[2]) + 2.5, '2.59x faster\n(-61.4%)', ha='center', color='#1f77b4', fontweight='bold', fontsize=10)
    ax4.text(3, max(val_72k[3], val_et3[3]) + 0.6, '-50.0%', ha='center', color='#1f77b4', fontweight='bold', fontsize=11)

    ax4.set_xticks(x_idx)
    ax4.set_xticklabels(labels_k)
    ax4.set_ylabel('Resource Measure')
    ax4.set_title('(d) Computational Efficiency: 70.7% Elements Reduced, 2.79x Solver Speedup')
    ax4.set_ylim(0.0, 85.0)
    ax4.grid(True, axis='y', linestyle=':')
    ax4.legend(loc='upper right', framealpha=0.92)

    plt.tight_layout()
    pdf_out = os.path.join(FIG_DIR, 'fig_mode2_f1395_fine_reference_vs_adaptive_accuracy.pdf')
    png_out = os.path.join(FIG_DIR, 'fig_mode2_f1395_fine_reference_vs_adaptive_accuracy.png')
    plt.savefig(pdf_out, dpi=300)
    plt.savefig(png_out, dpi=300)
    plt.close()
    print(f"Master synthesis figure generated successfully:\n  {pdf_out}\n  {png_out}")

if __name__ == '__main__':
    generate_f1395_synthesis_figure()
