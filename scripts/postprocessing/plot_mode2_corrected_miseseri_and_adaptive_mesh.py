# -*- coding: utf-8 -*-
"""
plot_mode2_corrected_miseseri_and_adaptive_mesh.py
Generates publication-quality 4-panel figure comparing:
Panel (a): Original pre-analysis (Job 1410790, d=0) stationary error & circular mesh
Panel (b): Corrected coarse pre-analysis (Job 1411104) propagating phase-field damage
Panel (c): Corrected pre-analysis MISESERI / MISESAVG diagonal corridor vs Fig. 6(b)
Panel (d): Corrected native adaptive mesh (Job 1411104, Step-2) vs published Fig. 12(b)
"""
import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle, Polygon
import pandas as pd

def main():
    base_dir = r"D:\Master thesis\Adaptive remeshing"
    model_dir = os.path.join(base_dir, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis")
    extracted_dir = os.path.join(model_dir, "extracted_corrected_miseseri")
    remesh_dir = os.path.join(model_dir, "m2_corrected_remesh")
    fig_dir = os.path.join(base_dir, "results", "figures", "mode2")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    # 1. Load Original Pre-analysis data
    orig_mises_path = os.path.join(model_dir, "miseseri_snapshot_ux_0p01000.csv")
    orig_mesh_path = os.path.join(model_dir, "m2_3_mesh_elements_et2pct.csv")
    df_orig_mises = pd.read_csv(orig_mises_path) if os.path.exists(orig_mises_path) else None
    df_orig_mesh = pd.read_csv(orig_mesh_path) if os.path.exists(orig_mesh_path) else None

    # 2. Load Corrected Snapshots
    df_c_s1 = pd.read_csv(os.path.join(extracted_dir, "corrected_coarse_fields_ux_0p01000.csv"))
    df_c_peak = pd.read_csv(os.path.join(extracted_dir, "corrected_coarse_fields_ux_0p01343_peak.csv"))
    df_c_prop = pd.read_csv(os.path.join(extracted_dir, "corrected_coarse_fields_ux_0p01626_prop.csv"))
    df_c_final = pd.read_csv(os.path.join(extracted_dir, "corrected_coarse_fields_ux_0p02000_final.csv"))

    # 3. Load Corrected Adapted Mesh (ET = 2% and 3%)
    corr_mesh_2pct_path = os.path.join(remesh_dir, "m2_corrected_mesh_elements_et2pct.csv")
    corr_mesh_3pct_path = os.path.join(remesh_dir, "m2_corrected_mesh_elements_et3pct.csv")
    df_corr_mesh = pd.read_csv(corr_mesh_2pct_path) if os.path.exists(corr_mesh_2pct_path) else None
    df_corr_mesh_3 = pd.read_csv(corr_mesh_3pct_path) if os.path.exists(corr_mesh_3pct_path) else None

    # 4. Load Manifest
    manifest_path = os.path.join(remesh_dir, "MODE2_CORRECTED_REMESH_MANIFEST.json")
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    # Digitized literature points
    fig6b_pts = [
        (0.495, 0.514), (0.540, 0.460), (0.600, 0.380),
        (0.680, 0.280), (0.760, 0.180), (0.840, 0.080), (0.930, 0.000)
    ]
    fig12b_pts = [
        (0.500, 0.500), (0.535, 0.430), (0.585, 0.340),
        (0.650, 0.235), (0.725, 0.140), (0.800, 0.060), (0.868, 0.000)
    ]

    # Create figure
    plt.style.use('default')
    fig = plt.figure(figsize=(16, 14), dpi=300)
    gs = gridspec.GridSpec(2, 2, figure=fig, wspace=0.28, hspace=0.30)

    # -------------------------------------------------------------
    # Panel (a): Original Pre-analysis (Job 1410790) Error & Circular Mesh
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 0])
    if df_orig_mesh is not None:
        fine_orig = df_orig_mesh[df_orig_mesh['h_eq'] <= 0.008]
        coarse_orig = df_orig_mesh[df_orig_mesh['h_eq'] > 0.008]
        ax1.scatter(coarse_orig['xc'], coarse_orig['yc'], c='#e0e0e0', s=1.5, alpha=0.5, label=r'Coarse elements ($h > 8\,\mu\mathrm{m}$)')
        sc1 = ax1.scatter(fine_orig['xc'], fine_orig['yc'], c=fine_orig['h_eq']*1000.0, cmap='viridis_r', s=2.5, vmin=1.0, vmax=8.0, label=r'Refined elements ($h \leq 8\,\mu\mathrm{m}$)')
        cbar1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
        cbar1.set_label(r'Element size $h$ ($\mu\mathrm{m}$)', fontsize=10)

    # Initial slit line
    ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=2.5, label=r'Initial slit ($a_0 = 0.5$ mm)')
    ax1.plot(0.5, 0.5, 'ro', ms=6)

    # Overlay circular contour
    circle = plt.Circle((0.5, 0.5), 0.18, color='magenta', fill=False, ls='--', lw=2.0, label='Circular refinement cluster')
    ax1.add_patch(circle)

    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_xlabel(r'$X$ coordinate (mm)', fontsize=11)
    ax1.set_ylabel(r'$Y$ coordinate (mm)', fontsize=11)
    ax1.set_title(r'(a) Original Pre-Analysis (Job 1410790, $d \equiv 0$):' + '\n' + r'Stationary Singularity & Circular Cluster (22,530 FEs)', fontsize=12, fontweight='bold')
    ax1.grid(True, ls=':', alpha=0.4)
    ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # -------------------------------------------------------------
    # Panel (b): Corrected Coarse Pre-Analysis Damage Evolution
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    sc2 = ax2.scatter(df_c_final['xc'], df_c_final['yc'], c=df_c_final['damage_sdv1'], cmap='inferno', s=16.0, vmin=0.0, vmax=1.0)
    cbar2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label(r'Phase-Field Damage $d$', fontsize=10)

    # Initial slit
    ax2.plot([0.0, 0.5], [0.5, 0.5], 'c-', lw=2.5, label=r'Initial slit ($a_0 = 0.5$ mm)')

    # Plot crack tips at key frames
    snaps_pts = [
        (0.5000, 0.5000),
        (0.5218, 0.4606),
        (0.5048, 0.4230),
        (0.6097, 0.2894),
        (0.7425, 0.1127)
    ]
    xs = [p[0] for p in snaps_pts]
    ys = [p[1] for p in snaps_pts]
    ax2.plot(xs, ys, 'w--', lw=2.0, marker='o', ms=5, label=r'Crack Path ($\theta = -57.95^\circ$, exit $x=0.813$)')

    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect('equal')
    ax2.set_xlabel(r'$X$ coordinate (mm)', fontsize=11)
    ax2.set_ylabel(r'$Y$ coordinate (mm)', fontsize=11)
    ax2.set_title(r'(b) Corrected Pre-Analysis (Job 1411104, RHS Repaired):' + '\n' + r'Propagating Damage & Oblique Mode-II Crack ($d_{\max}=1.0$)', fontsize=12, fontweight='bold')
    ax2.grid(True, ls=':', alpha=0.4)
    ax2.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # -------------------------------------------------------------
    # Panel (c): Corrected MISESERI Error Field vs Fig. 6(b)
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[1, 0])
    sc3 = ax3.scatter(df_c_final['xc'], df_c_final['yc'], c=df_c_final['eta_e'], cmap='plasma', s=16.0, vmin=0.0, vmax=10.0)
    cbar3 = plt.colorbar(sc3, ax=ax3, fraction=0.046, pad=0.04)
    cbar3.set_label(r'Relative Error $\eta_e = \mathrm{MISESERI} / \mathrm{MISESAVG}$', fontsize=10)

    # Plot published Fig 6b points
    f6_x = [p[0] for p in fig6b_pts]
    f6_y = [p[1] for p in fig6b_pts]
    ax3.plot(f6_x, f6_y, 'g-^', lw=2.2, ms=7, label=r'Pandey & Kumar Fig. 6(b) Error Corridor')

    # Initial slit
    ax3.plot([0.0, 0.5], [0.5, 0.5], 'w-', lw=2.5, label=r'Initial slit')

    ax3.set_xlim(-0.02, 1.02)
    ax3.set_ylim(-0.02, 1.02)
    ax3.set_aspect('equal')
    ax3.set_xlabel(r'$X$ coordinate (mm)', fontsize=11)
    ax3.set_ylabel(r'$Y$ coordinate (mm)', fontsize=11)
    ax3.set_title(r'(c) Corrected Stress Discretization Error Field:' + '\n' + r'Emergence of Downward-Right Diagonal Corridor ($\theta=-34.1^\circ$)', fontsize=12, fontweight='bold')
    ax3.grid(True, ls=':', alpha=0.4)
    ax3.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # -------------------------------------------------------------
    # Panel (d): Corrected Native Adaptive Mesh vs Published Fig. 12(b)
    # -------------------------------------------------------------
    ax4 = fig.add_subplot(gs[1, 1])
    if df_corr_mesh is not None:
        fine_corr = df_corr_mesh[df_corr_mesh['h_eq'] <= 0.008]
        coarse_corr = df_corr_mesh[df_corr_mesh['h_eq'] > 0.008]
        ax4.scatter(coarse_corr['xc'], coarse_corr['yc'], c='#e0e0e0', s=1.5, alpha=0.4, label=r'Coarse elements ($h > 8\,\mu\mathrm{m}$)')
        sc4 = ax4.scatter(fine_corr['xc'], fine_corr['yc'], c=fine_corr['h_eq']*1000.0, cmap='viridis_r', s=2.5, vmin=1.0, vmax=8.0, label=r'Refined elements ($h \leq 8\,\mu\mathrm{m}$)')
        cbar4 = plt.colorbar(sc4, ax=ax4, fraction=0.046, pad=0.04)
        cbar4.set_label(r'Element size $h$ ($\mu\mathrm{m}$)', fontsize=10)

    # Initial slit
    ax4.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=2.5, label=r'Initial slit ($a_0 = 0.5$ mm)')

    # Centerline from manifest ET_2PCT
    c_pts = manifest['sweep_results']['ET_2PCT']['centerline_points']
    c_xs = [p[0] for p in c_pts]
    c_ys = [p[1] for p in c_pts]
    ax4.plot(c_xs, c_ys, 'b-o', lw=2.2, ms=5, label=r'Generated Mesh Centerline ($\theta = -49.44^\circ$)')

    # Published Fig 12b points
    f12_x = [p[0] for p in fig12b_pts]
    f12_y = [p[1] for p in fig12b_pts]
    ax4.plot(f12_x, f12_y, 'm--s', lw=2.2, ms=6, label=r'Pandey & Kumar Fig. 12(b) Path ($19{,}963$ FEs)')

    ax4.set_xlim(-0.02, 1.02)
    ax4.set_ylim(-0.02, 1.02)
    ax4.set_aspect('equal')
    ax4.set_xlabel(r'$X$ coordinate (mm)', fontsize=11)
    ax4.set_ylabel(r'$Y$ coordinate (mm)', fontsize=11)
    ax4.set_title(r'(d) Corrected Native Adaptive Mesh (`ET_2PCT`, 37,575 FEs):' + '\n' + r'Genuine Diagonal Curved Refinement Corridor to Bottom Edge', fontsize=12, fontweight='bold')
    ax4.grid(True, ls=':', alpha=0.4)
    ax4.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    # Save figures
    png_path = os.path.join(fig_dir, "fig_mode2_corrected_miseseri_and_adaptive_mesh.png")
    png_600_path = os.path.join(fig_dir, "fig_mode2_corrected_miseseri_and_adaptive_mesh_600dpi.png")
    pdf_path = os.path.join(fig_dir, "fig_mode2_corrected_miseseri_and_adaptive_mesh.pdf")

    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.savefig(png_600_path, dpi=600, bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.close()

    print("Successfully generated publication figures:")
    print("  300 DPI PNG :", png_path)
    print("  600 DPI PNG :", png_600_path)
    print("  Vector PDF  :", pdf_path)

if __name__ == "__main__":
    main()
