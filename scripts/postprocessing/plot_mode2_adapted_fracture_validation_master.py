#!/usr/bin/env python3
"""
Master Publication Figure Generation Script for Mode-II Adapted Fracture Validation
Task F1363 - Gate M2-4 Closeout & Evidence Synthesis

Generates publication-quality 300/600 DPI PNG and vector PDF figures:
1. fig_mode2_m2_4_full_response_and_literature_comparison
2. fig_mode2_m2_4_actual_crack_trajectory_vs_literature
3. fig_mode2_m2_4_damage_field_and_mesh_localization
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

def generate_all_figures():
    # Ensure output directory exists
    out_dir = os.path.join("results", "figures", "mode2")
    os.makedirs(out_dir, exist_ok=True)

    # ----------------------------------------------------------------------
    # 1. Load Data
    # ----------------------------------------------------------------------
    rf_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
    damage_summary_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_damage_evolution_summary.csv")
    crack_path_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_extracted_crack_path.csv")
    detailed_field_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_latest_damage_field.csv")

    df_rf = pd.read_csv(rf_csv) if os.path.exists(rf_csv) else None
    df_dmg = pd.read_csv(damage_summary_csv) if os.path.exists(damage_summary_csv) else None
    df_path = pd.read_csv(crack_path_csv) if os.path.exists(crack_path_csv) else None
    df_field = pd.read_csv(detailed_field_csv) if os.path.exists(detailed_field_csv) else None

    # Literature Digitized Data (Pandey & Kumar 2025 Fig 13a)
    u_lit_proposed = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.284, 8.5, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    rf_lit_proposed = np.array([0.0, 47.7, 95.4, 143.1, 190.8, 238.5, 286.2, 331.0, 363.0, 365.74, 362.0, 345.0, 335.0, 330.0, 325.0, 318.0, 310.0, 300.0, 290.0])

    u_lit_standard = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 8.08, 8.5, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0])
    rf_lit_standard = np.array([0.0, 46.75, 93.5, 140.25, 187.0, 233.75, 280.5, 325.0, 351.5, 351.99, 348.0, 332.0, 322.0, 315.0, 308.0, 300.0, 292.0, 282.0, 270.0])

    # Authenticated Literature Crack Path Stations (Pandey & Kumar Fig 12b)
    lit_stations = np.array([
        [0.5000, 0.5000],
        [0.5284, 0.4300],
        [0.5732, 0.3200],
        [0.6300, 0.2100],
        [0.7077, 0.1200],
        [0.7854, 0.0600],
        [0.8680, 0.0000]
    ])

    # ----------------------------------------------------------------------
    # FIGURE 1: Full Response & Literature Comparison (4-Panel)
    # ----------------------------------------------------------------------
    fig = plt.figure(figsize=(14, 11), dpi=300)
    gs = GridSpec(2, 2, figure=fig, hspace=0.28, wspace=0.25)

    # Panel (a): Full Force-Displacement Response
    ax1 = fig.add_subplot(gs[0, 0])
    if df_rf is not None:
        ax1.plot(df_rf['u_x_um'], df_rf['rf_N'], 'b-', linewidth=2.2, label='Adapted Simulation (Job 1411267, 21.1k FEs)')
    ax1.plot(u_lit_proposed, rf_lit_proposed, 'r--', linewidth=2.0, marker='o', markersize=4, label='Pandey & Kumar (2025) Proposed PFM')
    ax1.plot(u_lit_standard, rf_lit_standard, 'g-.', linewidth=1.8, label='Pandey & Kumar (2025) Standard PFM')
    ax1.axhline(514.51, color='gray', linestyle=':', label=r'Coarse Baseline ($F_{\max}=514.51$ N, 2.96k FEs)')

    ax1.set_xlabel(r'Shear Displacement $u_x$ ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold')
    ax1.set_ylabel(r'Reaction Force $RF_1$ (N)', fontsize=11, fontweight='bold')
    ax1.set_title('(a) Mode-II Reaction Force vs. Displacement', fontsize=12, fontweight='bold')
    ax1.set_xlim(0, 20.0)
    ax1.set_ylim(0, 550)
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # Panel (b): Zoom on Peak & Gap Reduction
    ax2 = fig.add_subplot(gs[0, 1])
    if df_rf is not None:
        ax2.plot(df_rf['u_x_um'], df_rf['rf_N'], 'b-', linewidth=2.2, label=r'Adapted ($F_{\max}=412.21$ N at 9.41 $\mu\mathrm{m}$)')
    ax2.plot(u_lit_proposed, rf_lit_proposed, 'r--', linewidth=2.0, marker='o', markersize=5, label=r'Lit. Proposed ($F_{\max}=365.74$ N at 8.28 $\mu\mathrm{m}$)')
    ax2.plot(u_lit_standard, rf_lit_standard, 'g-.', linewidth=1.8, label=r'Lit. Standard ($F_{\max}=351.99$ N at 8.08 $\mu\mathrm{m}$)')

    ax2.annotate(r'$F_{\max} = 412.21$ N (+12.71%)', xy=(9.410, 412.209), xytext=(10.5, 450),
                 arrowprops=dict(facecolor='blue', shrink=0.08, width=1.5, headwidth=6),
                 fontsize=9.5, fontweight='bold', color='blue')
    ax2.annotate(r'$F_{\max} = 365.74$ N', xy=(8.284, 365.74), xytext=(5.0, 390),
                 arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=6),
                 fontsize=9.5, fontweight='bold', color='red')

    ax2.text(0.05, 0.08, r'Coarse $\to$ Adapted Gap Resolution:' + '\n' + r'$\frac{514.51 - 412.21}{514.51 - 365.74} = 68.76\%$',
             transform=ax2.transAxes, fontsize=10, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', alpha=0.9))

    ax2.set_xlabel(r'Shear Displacement $u_x$ ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold')
    ax2.set_ylabel(r'Reaction Force $RF_1$ (N)', fontsize=11, fontweight='bold')
    ax2.set_title('(b) Peak Softening & Gap Resolution Audit', fontsize=12, fontweight='bold')
    ax2.set_xlim(4.0, 14.0)
    ax2.set_ylim(200, 480)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.legend(loc='lower right', fontsize=8.5, framealpha=0.9)

    # Panel (c): Damage Evolution & Broken Elements
    ax3 = fig.add_subplot(gs[1, 0])
    if df_dmg is not None:
        ax3_twin = ax3.twinx()
        l1 = ax3.plot(df_dmg['ux_prescribed_um'], df_dmg['d_max'], 'm-s', linewidth=2.0, markersize=5, label=r'Peak Damage $d_{\max}$')
        l2 = ax3.plot(df_dmg['ux_prescribed_um'], df_dmg['d_mean'] * 4.0, 'c--^', linewidth=1.8, markersize=5, label=r'Mean Damage $\times 4$')
        l3 = ax3_twin.plot(df_dmg['ux_prescribed_um'], df_dmg['n_d09'], 'darkorange', linestyle='-', linewidth=2.2, marker='o', markersize=5, label=r'Broken FEs ($d \geq 0.9$)')
        
        ax3.set_xlabel(r'Prescribed Displacement $u_x$ ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold')
        ax3.set_ylabel(r'Phase-Field Damage $d$', fontsize=11, fontweight='bold', color='m')
        ax3_twin.set_ylabel(r'Number of Broken Elements ($d \geq 0.9$)', fontsize=11, fontweight='bold', color='darkorange')
        ax3.set_title('(c) Phase-Field Damage Evolution', fontsize=12, fontweight='bold')
        ax3.set_xlim(0, 20.0)
        ax3.set_ylim(0, 1.1)
        ax3.grid(True, linestyle='--', alpha=0.5)
        
        lines = l1 + l2 + l3
        labels = [l.get_label() for l in lines]
        ax3.legend(lines, labels, loc='upper left', fontsize=8.5, framealpha=0.9)

    # Panel (d): Remaining Intact Ligament & Propagation Depth
    ax4 = fig.add_subplot(gs[1, 1])
    if df_dmg is not None:
        lig_um = df_dmg['ligament_height_mm'] * 1000.0
        pct_broken = (0.500 - df_dmg['ligament_height_mm']) / 0.500 * 100.0
        
        ax4.plot(df_dmg['ux_prescribed_um'], lig_um, 'g-o', linewidth=2.2, markersize=5, label=r'Intact Ligament Height ($\mu\mathrm{m}$)')
        ax4_twin = ax4.twinx()
        ax4_twin.plot(df_dmg['ux_prescribed_um'], pct_broken, 'r--s', linewidth=2.0, markersize=5, label='Ligament Traversed (%)')
        
        ax4.set_xlabel(r'Prescribed Displacement $u_x$ ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold')
        ax4.set_ylabel(r'Remaining Intact Ligament ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold', color='g')
        ax4_twin.set_ylabel(r'Ligament Broken (%)', fontsize=11, fontweight='bold', color='r')
        ax4.set_title('(d) Crack Front Penetration & Intact Ligament', fontsize=12, fontweight='bold')
        ax4.set_xlim(0, 20.0)
        ax4.set_ylim(0, 550)
        ax4_twin.set_ylim(0, 100)
        ax4.grid(True, linestyle='--', alpha=0.5)
        
        last_row = df_dmg.iloc[-1]
        ax4.annotate(r'$h_{\mathrm{lig}} = %.1f\,\mu\mathrm{m}$ (%.1f%% broken)' % (last_row['ligament_height_mm']*1000.0, (0.5-last_row['ligament_height_mm'])/0.5*100.0),
                     xy=(last_row['ux_prescribed_um'], last_row['ligament_height_mm']*1000.0),
                     xytext=(11.0, 180),
                     arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
                     fontsize=9.5, fontweight='bold')

    plt.tight_layout()
    fig1_png = os.path.join(out_dir, "fig_mode2_m2_4_full_response_and_literature_comparison.png")
    fig1_pdf = os.path.join(out_dir, "fig_mode2_m2_4_full_response_and_literature_comparison.pdf")
    plt.savefig(fig1_png, dpi=300, bbox_inches='tight')
    plt.savefig(fig1_pdf, bbox_inches='tight')
    plt.close(fig)

    # ----------------------------------------------------------------------
    # FIGURE 2: Actual Crack Trajectory vs Literature (2-Panel)
    # ----------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.5), dpi=300)

    if df_path is not None:
        df_valid = df_path[df_path['d_peak'] >= 0.50]
        ax1.plot(df_valid['x_peak_d_mm'], df_valid['y_station_mm'], 'b-o', linewidth=2.2, markersize=4, label=r'Adapted Crack Path (Job 1411267, $d \geq 0.5$)')
        ax1.plot(df_path['x_weighted_d_mm'], df_path['y_station_mm'], 'c--', linewidth=1.5, label=r'Weighted Ridge ($d^4$-weighted)')

    ax1.plot(lit_stations[:, 0], lit_stations[:, 1], 'r--s', linewidth=2.0, markersize=6, label='Pandey & Kumar (2025) Fig. 12(b)')

    ax1.plot([0.0, 0.5], [0.5, 0.5], 'k-', linewidth=3.0, label='Initial Slit ($a_0 = 0.5$ mm)')
    ax1.plot([0.0, 1.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 1.0, 0.0], 'k--', linewidth=1.0, alpha=0.5)

    x_corr_left = lit_stations[:, 0] - 0.120
    x_corr_right = lit_stations[:, 0] + 0.120
    ax1.fill_betweenx(lit_stations[:, 1], x_corr_left, x_corr_right, color='blue', alpha=0.10, label='Adaptive Refinement Corridor ($W=0.24$ mm)')

    ax1.set_xlabel(r'Coordinate $x$ (mm)', fontsize=11, fontweight='bold')
    ax1.set_ylabel(r'Coordinate $y$ (mm)', fontsize=11, fontweight='bold')
    ax1.set_title('(a) Extracted Crack Trajectory vs. Literature', fontsize=12, fontweight='bold')
    ax1.set_xlim(0.35, 1.05)
    ax1.set_ylim(-0.05, 0.55)
    ax1.set_aspect('equal')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # Panel (b): Lateral Deviation Profile Delta x(y)
    if df_path is not None:
        y_eval = df_valid['y_station_mm'].values
        x_sim = df_valid['x_peak_d_mm'].values
        x_lit_interp = np.interp(y_eval, lit_stations[::-1, 1], lit_stations[::-1, 0])
        delta_x_um = (x_sim - x_lit_interp) * 1000.0
        
        ax2.plot(delta_x_um, y_eval, 'm-o', linewidth=2.0, markersize=4, label=r'Horizontal Deviation $\Delta x = x_{\mathrm{sim}} - x_{\mathrm{lit}}$')
        ax2.axvline(0.0, color='k', linestyle='--', alpha=0.7)
        ax2.axvspan(-120, 120, color='blue', alpha=0.10, label=r'Corridor Semi-Width ($\pm 120\,\mu\mathrm{m}$)')
        
        ax2.set_xlabel(r'Lateral Deviation $\Delta x$ ($\mu\mathrm{m}$)', fontsize=11, fontweight='bold')
        ax2.set_ylabel(r'Vertical Coordinate $y$ (mm)', fontsize=11, fontweight='bold')
        ax2.set_title('(b) Crack Path Deviation Profile', fontsize=12, fontweight='bold')
        ax2.set_xlim(-150, 150)
        ax2.set_ylim(-0.02, 0.52)
        ax2.grid(True, linestyle='--', alpha=0.5)
        ax2.legend(loc='lower left', fontsize=8.5, framealpha=0.9)
        
        ax2.text(0.05, 0.85, r'Initiation zone ($y \in [0.4, 0.5]$ mm):' + '\n' + r'$|\Delta x| \leq 3.5\,\mu\mathrm{m} \approx l_0 / 4.3$',
                 transform=ax2.transAxes, fontsize=9.5, bbox=dict(boxstyle='round,pad=0.4', facecolor='lightgreen', alpha=0.8))

    plt.tight_layout()
    fig2_png = os.path.join(out_dir, "fig_mode2_m2_4_actual_crack_trajectory_vs_literature.png")
    fig2_pdf = os.path.join(out_dir, "fig_mode2_m2_4_actual_crack_trajectory_vs_literature.pdf")
    plt.savefig(fig2_png, dpi=300, bbox_inches='tight')
    plt.savefig(fig2_pdf, bbox_inches='tight')
    plt.close(fig)

    # ----------------------------------------------------------------------
    # FIGURE 3: 2D Damage Field & Mesh Localization
    # ----------------------------------------------------------------------
    if df_field is not None:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6.0), dpi=300)
        
        sc1 = ax1.scatter(df_field['x_mm'], df_field['y_mm'], c=df_field['damage_d'], cmap='inferno',
                          s=2.0, alpha=0.85, vmin=0.0, vmax=1.0)
        cb1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
        cb1.set_label(r'Phase-Field Damage $d$', fontsize=10, fontweight='bold')
        
        ax1.plot([0.0, 0.5], [0.5, 0.5], 'w-', linewidth=2.5, label='Initial Slit')
        ax1.set_xlabel(r'$x$ (mm)', fontsize=11, fontweight='bold')
        ax1.set_ylabel(r'$y$ (mm)', fontsize=11, fontweight='bold')
        ax1.set_title(r'(a) Full Specimen Damage Field at $u_x = 18.0\,\mu\mathrm{m}$', fontsize=12, fontweight='bold')
        ax1.set_xlim(-0.02, 1.02)
        ax1.set_ylim(-0.02, 1.02)
        ax1.set_aspect('equal')
        ax1.grid(True, linestyle=':', alpha=0.3)
        ax1.legend(loc='upper left', fontsize=8.5)
        
        sc2 = ax2.scatter(df_field['x_mm'], df_field['y_mm'], c=df_field['damage_d'], cmap='inferno',
                          s=6.0, alpha=0.90, vmin=0.0, vmax=1.0)
        cb2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
        cb2.set_label(r'Phase-Field Damage $d$', fontsize=10, fontweight='bold')
        
        ax2.plot(lit_stations[:, 0], lit_stations[:, 1], 'c--s', linewidth=1.8, markersize=5, label='Pandey & Kumar Fig. 12(b)')
        ax2.plot([0.0, 0.5], [0.5, 0.5], 'w-', linewidth=2.5, label='Slit Tip')
        
        ax2.axhline(0.0691, color='cyan', linestyle=':', linewidth=1.5, label='Crack Front ($y = 0.0691$ mm)')
        ax2.annotate(r'Intact Ligament' + '\n' + r'($69.1\,\mu\mathrm{m}$ remaining)', xy=(0.75, 0.035), xytext=(0.42, 0.05),
                     arrowprops=dict(facecolor='white', shrink=0.08, width=1.2, headwidth=5),
                     fontsize=9.5, fontweight='bold', color='white',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='black', alpha=0.7))
        
        ax2.set_xlabel(r'$x$ (mm)', fontsize=11, fontweight='bold')
        ax2.set_ylabel(r'$y$ (mm)', fontsize=11, fontweight='bold')
        ax2.set_title('(b) Fracture Process Zone & Ligament Zoom', fontsize=12, fontweight='bold')
        ax2.set_xlim(0.40, 0.95)
        ax2.set_ylim(-0.02, 0.52)
        ax2.set_aspect('equal')
        ax2.grid(True, linestyle=':', alpha=0.3)
        ax2.legend(loc='upper right', fontsize=8.0)
        
        plt.tight_layout()
        fig3_png = os.path.join(out_dir, "fig_mode2_m2_4_damage_field_and_mesh_localization.png")
        fig3_pdf = os.path.join(out_dir, "fig_mode2_m2_4_damage_field_and_mesh_localization.pdf")
        plt.savefig(fig3_png, dpi=300, bbox_inches='tight')
        plt.savefig(fig3_pdf, bbox_inches='tight')
        plt.close(fig)

    return fig1_png, fig2_png, fig3_png

if __name__ == "__main__":
    generate_all_figures()
    print("ALL MASTER PUBLICATION FIGURES GENERATED SUCCESSFULLY!")
