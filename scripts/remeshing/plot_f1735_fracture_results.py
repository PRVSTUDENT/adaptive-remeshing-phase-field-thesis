# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1735_fracture_results.py

Generates publication-quality figures for Task F1735 Case 2 Adapted-Mesh
Phase-Field Fracture Simulation:
- Subplot 1: Force-Displacement (F-u) Curve
- Subplot 2: Energy Evolution (Elastic Strain Energy vs Fracture Dissipation)
"""

import os
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def main():
    repo = r'D:\Master thesis\Adaptive remeshing'
    curve_csv = os.path.join(repo, 'results/validation/f1735_case2_fracture_curve.csv')
    energy_csv = os.path.join(repo, 'results/validation/f1735_case2_fracture_evidence/uel_energy_balance.csv')
    fig_dir = os.path.join(repo, 'results/figures')
    os.makedirs(fig_dir, exist_ok=True)
    out_png = os.path.join(fig_dir, 'f1735_case2_fracture_response.png')

    # Load F-u curve
    u_vals = []
    rf_N = []
    with open(curve_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_vals.append(float(r['u_mm']))
            rf_N.append(float(r['rf_N']))

    # Load energy data
    e_total_time = []
    e_u_mm = []
    e_elas = []
    e_frac = []
    e_tot = []
    with open(energy_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if not row or len(row) < 7:
                continue
            step = int(row[0].strip())
            step_time = float(row[3].strip())
            # Calculate displacement from step and step_time
            if step == 1:
                u = step_time * 0.005
            else:
                u = 0.005 + step_time * 0.007
            e_u_mm.append(u)
            e_elas.append(float(row[4].strip()) * 1000.0) # Convert kN*mm to N*mm (mJ)
            e_frac.append(float(row[5].strip()) * 1000.0)
            e_tot.append(float(row[6].strip()) * 1000.0)

    # Plot 2-panel figure
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), dpi=300)

    # 1. Force-displacement curve
    ax1.plot([u * 1000.0 for u in u_vals], rf_N, 'b-', linewidth=2.2, label='F1735 Adapted Mesh (23,965 CPE4 elements)')
    ax1.axvline(x=0.005476 * 1000.0, color='r', linestyle='--', alpha=0.7, label=r'Peak Force $F_{\max} = 571.7\,\mathrm{N}$ ($u = 5.48\,\mu\mathrm{m}$)')
    ax1.scatter([0.005476 * 1000.0], [571.68], color='red', s=60, zorder=5)
    ax1.scatter([u_vals[-1] * 1000.0], [rf_N[-1]], color='darkblue', s=60, zorder=5, label=r'Terminal State ($57.2\%$ load drop, $F = 244.4\,\mathrm{N}$)')

    ax1.set_xlabel(r'Prescribed Displacement $u_y$ ($\mu\mathrm{m}$)', fontsize=12, fontweight='bold')
    ax1.set_ylabel(r'Reaction Force $RF_y$ ($\mathrm{N}$)', fontsize=12, fontweight='bold')
    ax1.set_title(r'Case 2 Adapted-Mesh Force–Displacement Response', fontsize=13, fontweight='bold')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='lower left', fontsize=10, frameon=True)

    # Annotate K0 and drop
    ax1.annotate(r'$K_0 = 112.95\,\mathrm{kN/mm}$', xy=(2.0, 226.0), xytext=(0.5, 380.0),
                 arrowprops=dict(arrowstyle='->', lw=1.2, color='black'), fontsize=10, fontweight='bold')

    # 2. Energy balance evolution
    ax2.plot([u * 1000.0 for u in e_u_mm], e_tot, 'k-', linewidth=2.0, label=r'Total Work $W_{\mathrm{ext}}$')
    ax2.plot([u * 1000.0 for u in e_u_mm], e_elas, 'g--', linewidth=2.0, label=r'Elastic Strain Energy $E_{\mathrm{elas}}$')
    ax2.plot([u * 1000.0 for u in e_u_mm], e_frac, 'm-.', linewidth=2.0, label=r'Fracture Dissipation $E_{\mathrm{frac}}$')

    ax2.set_xlabel(r'Prescribed Displacement $u_y$ ($\mu\mathrm{m}$)', fontsize=12, fontweight='bold')
    ax2.set_ylabel(r'Internal Energy ($\mathrm{N\cdot mm}$ or $\mathrm{mJ}$)', fontsize=12, fontweight='bold')
    ax2.set_title(r'Thermodynamic Energy Balance & Dissipation', fontsize=13, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper left', fontsize=10, frameon=True)

    # Highlight crack initiation and propagation
    ax2.axvline(x=0.005476 * 1000.0, color='r', linestyle='--', alpha=0.7, label=r'Crack Propagation Onset')

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"Publication figure saved to: {out_png}")

if __name__ == '__main__':
    main()
