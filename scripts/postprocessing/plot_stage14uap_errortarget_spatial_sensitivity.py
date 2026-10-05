"""
Gate-6B Stage 14U-AQ: Publication-quality plotting of errorTarget (1, 2, 3, 5%) spatial sensitivity.
Highlights crack corridor boundaries (y in [0.45, 0.55] mm), enforced l0 = 7.5 um length scale,
and quantitative spatial classification metrics with identical colorbar scaling.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

def generate_sensitivity_plots(summary_json_path, csv_dir, out_pdf_path, out_png_path):
    with open(summary_json_path, 'r') as f:
        summary = json.load(f)
        
    error_targets = [1.0, 2.0, 3.0, 5.0]
    csv_files = {
        1.0: os.path.join(csv_dir, "elements_err_10pct.csv"),
        2.0: os.path.join(csv_dir, "elements_err_20pct.csv"),
        3.0: os.path.join(csv_dir, "elements_err_30pct.csv"),
        5.0: os.path.join(csv_dir, "elements_err_50pct.csv")
    }
    
    dfs = {}
    for et in error_targets:
        if os.path.isfile(csv_files[et]):
            dfs[et] = pd.read_csv(csv_files[et])
            
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), sharex=True, sharey=True)
    axes = axes.flatten()
    
    norm = mcolors.Normalize(vmin=0.5, vmax=24.0)
    cmap = plt.get_cmap('viridis_r')
    
    classifications = {
        1.0: ("DIFFUSE DOMAIN OVERREFINEMENT", "crimson"),
        2.0: ("TOWARD TARGET LOCALIZATION", "forestgreen"),
        3.0: ("TOWARD TARGET LOCALIZATION", "forestgreen"),
        5.0: ("UNDER-RESOLVED CORRIDOR", "darkorange")
    }
    
    sc_last = None
    
    for idx, et in enumerate(error_targets):
        ax = axes[idx]
        if et in dfs:
            df = dfs[et]
            h_um = df['h_eq'] * 1000.0
            
            # Sizing point scatter
            sc = ax.scatter(df['cx'], df['cy'], c=h_um, cmap=cmap, norm=norm,
                            s=np.clip(22.0 - h_um * 0.8, 1.5, 22.0), alpha=0.75, rasterized=True)
            sc_last = sc
            
            # Crack corridor shading and boundary lines
            ax.axhspan(0.45, 0.55, color='lightgray', alpha=0.35, zorder=0)
            ax.axhline(0.45, color='gray', linestyle=':', linewidth=1.2, zorder=1)
            ax.axhline(0.55, color='gray', linestyle=':', linewidth=1.2, zorder=1)
            
            # Seam and propagation lines
            ax.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=2.2, label='Initial Notch ($a_0 = 0.5\\,\\mathrm{mm}$)', zorder=5)
            ax.plot([0.5, 1.0], [0.5, 0.5], 'r--', linewidth=1.5, alpha=0.8, label='Ligament Plane ($y = 0.5\\,\\mathrm{mm}$)', zorder=5)
            
            total_n = len(df)
            corr_n = len(df[(df['cy'] >= 0.45) & (df['cy'] <= 0.55)])
            fine_l0_n = len(df[h_um <= 7.5])
            fine_corr_n = len(df[(df['cy'] >= 0.45) & (df['cy'] <= 0.55) & (h_um <= 7.5)])
            
            corr_share_fine = (fine_corr_n / float(fine_l0_n) * 100.0) if fine_l0_n > 0 else 0.0
            fine_pct_total = (fine_l0_n / float(total_n) * 100.0) if total_n > 0 else 0.0
            
            h_min_um = np.min(h_um)
            h_med_um = np.median(h_um)
            
            cls_text, cls_color = classifications[et]
            
            ax.set_title(r"$\mathbf{errorTarget = %.1f\%%}$ ($N = %d$ Elements)" % (et, total_n),
                         fontsize=12, fontweight='bold', pad=8)
            
            # Add classification banner
            ax.text(0.03, 0.94, cls_text, transform=ax.transAxes,
                    fontsize=9.5, fontweight='bold', color=cls_color,
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.9, edgecolor=cls_color, linewidth=1.2))
            
            # Metrics summary box
            info_str = (
                f"$h_{{\\min}} = {h_min_um:.2f}\\,\\mu\\mathrm{{m}}$\n"
                f"$h_{{\\mathrm{{med}}}} = {h_med_um:.2f}\\,\\mu\\mathrm{{m}}$\n"
                f"$N(h \\leq \\ell_0) = {fine_l0_n}$ ({fine_pct_total:.1f}%)\n"
                f"Corridor Share: {corr_share_fine:.1f}%\n"
                f"Corridor $N$: {corr_n}"
            )
            ax.text(0.97, 0.04, info_str, transform=ax.transAxes,
                    fontsize=8.5, verticalalignment='bottom', horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.88, edgecolor='silver'))
            
            ax.set_xlim(0.0, 1.0)
            ax.set_ylim(0.0, 1.0)
            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.5)
            
            if idx in [2, 3]:
                ax.set_xlabel('Plate Coordinate $x$ [mm]', fontsize=11)
            if idx in [0, 2]:
                ax.set_ylabel('Plate Coordinate $y$ [mm]', fontsize=11)
                
            if idx == 0:
                ax.legend(loc='lower left', fontsize=8.5, framealpha=0.9)
                
    # Colorbar
    fig.subplots_adjust(right=0.88, top=0.92, bottom=0.08, left=0.08, wspace=0.12, hspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(sc_last, cax=cbar_ax)
    cbar.set_label(r'Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{\mathrm{Area}}$ [$\mu\mathrm{m}$] (Governing $\ell_0 = 7.5\,\mu\mathrm{m}$)',
                   fontsize=11, labelpad=10)
    cbar.ax.axhline(7.5, color='red', linestyle='--', linewidth=1.5)
    cbar.ax.text(1.3, 7.5, r'$\ell_0 = 7.5\,\mu\mathrm{m}$', color='red', fontsize=9.5, verticalalignment='center')
    
    plt.suptitle("Mode-I Pre-Analysis Companion Mesh: Spatial Sensitivity of Abaqus Native Error-Guided Sizing\n"
                 r"Effect of Target Error Tolerance $\eta \in \{1.0\%, 2.0\%, 3.0\%, 5.0\%\}$ on Crack Corridor ($|y - 0.5| \leq 0.05\,\mathrm{mm}$) Localization",
                 fontsize=13, fontweight='bold', y=0.97)
    
    os.makedirs(os.path.dirname(out_pdf_path), exist_ok=True)
    plt.savefig(out_pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Spatial sensitivity plot generated successfully: %s, %s" % (out_pdf_path, out_png_path))

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        generate_sensitivity_plots(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        # Default standalone execution
        summary_path = "models/pandey_kumar_mode1/32_stage14_remeshing_errortarget_sensitivity/MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json"
        csv_dir_path = "models/pandey_kumar_mode1/32_stage14_remeshing_errortarget_sensitivity"
        out_pdf = "results/figures/mode1_gate6b/fig_mode1_stage14uap_errortarget_spatial_sensitivity.pdf"
        out_png = "results/figures/mode1_gate6b/fig_mode1_stage14uap_errortarget_spatial_sensitivity.png"
        generate_sensitivity_plots(summary_path, csv_dir_path, out_pdf, out_png)
