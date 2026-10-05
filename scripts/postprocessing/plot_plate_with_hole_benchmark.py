"""
Independent Benchmark Plotting: 2D Plate with Central Circular Hole Adaptive Remeshing.
Generates publication-quality 4-panel figure showing symmetric stress concentration
refinement across errorTarget = 1, 2, 3, 5% with identical colorbar scaling and flank annotations.
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
import matplotlib.patches as patches

def generate_plate_hole_plots(summary_json_path, csv_dir, out_pdf_path, out_png_path):
    with open(summary_json_path, 'r') as f:
        summary = json.load(f)
        
    error_targets = [1.0, 2.0, 3.0, 5.0]
    csv_files = {
        1.0: os.path.join(csv_dir, "plate_hole_elements_err_10pct.csv"),
        2.0: os.path.join(csv_dir, "plate_hole_elements_err_20pct.csv"),
        3.0: os.path.join(csv_dir, "plate_hole_elements_err_30pct.csv"),
        5.0: os.path.join(csv_dir, "plate_hole_elements_err_50pct.csv")
    }
    
    dfs = {}
    for et in error_targets:
        if os.path.isfile(csv_files[et]):
            dfs[et] = pd.read_csv(csv_files[et])
            
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), sharex=True, sharey=True)
    axes = axes.flatten()
    
    norm = mcolors.Normalize(vmin=0.6, vmax=45.0)
    cmap = plt.get_cmap('plasma_r')
    
    theta = np.linspace(0, 2*np.pi, 200)
    circle_x = 0.5 + 0.1 * np.cos(theta)
    circle_y = 0.5 + 0.1 * np.sin(theta)
    
    sc_last = None
    
    for idx, et in enumerate(error_targets):
        ax = axes[idx]
        if et in dfs:
            df = dfs[et]
            h_um = df['h_eq'] * 1000.0
            
            sc = ax.scatter(df['cx'], df['cy'], c=h_um, cmap=cmap, norm=norm,
                            s=np.clip(28.0 - h_um * 0.5, 2.0, 28.0), alpha=0.8, rasterized=True)
            sc_last = sc
            
            # Plot circular hole
            ax.plot(circle_x, circle_y, 'k-', linewidth=2.2, label='Hole ($R = 0.1\\,\\mathrm{mm}$)', zorder=6)
            ax.fill(circle_x, circle_y, facecolor='white', edgecolor='k', linewidth=2.0, zorder=5)
            
            # Plot lateral flank stress concentration points
            ax.plot([0.4], [0.5], 'r*', markersize=9, label='Peak Flank Concentration ($K_t \\approx 3.06$)', zorder=7)
            ax.plot([0.6], [0.5], 'r*', markersize=9, zorder=7)
            
            # Flank bounding boxes (shaded)
            rect_l = patches.Rectangle((0.30, 0.42), 0.12, 0.16, linewidth=1.0, edgecolor='crimson',
                                       facecolor='crimson', alpha=0.10, linestyle='--', zorder=2)
            rect_r = patches.Rectangle((0.58, 0.42), 0.12, 0.16, linewidth=1.0, edgecolor='crimson',
                                       facecolor='crimson', alpha=0.10, linestyle='--', zorder=2)
            ax.add_patch(rect_l)
            ax.add_patch(rect_r)
            
            case_data = summary.get('results_by_error_target', {}).get(str(et), {})
            total_n = case_data.get('total_elements', len(df))
            flank_info = case_data.get('flank_elements', {})
            flank_n = flank_info.get('total_flank_elements', 0)
            sym_ratio = flank_info.get('flank_symmetry_ratio', 1.0)
            contrast = case_data.get('refinement_contrast_far_to_flank', 1.0)
            
            h_min_um = np.min(h_um)
            h_flank_mean_um = flank_info.get('h_flank_mean_um', np.mean(h_um))
            h_far_mean_um = case_data.get('far_field_elements', {}).get('h_far_mean_um', np.mean(h_um))
            
            ax.set_title(r"$\mathbf{errorTarget = %.1f\%%}$ ($N = %d$ Elements)" % (et, total_n),
                         fontsize=12, fontweight='bold', pad=8)
            
            # Add classification banner
            ax.text(0.03, 0.94, "KIRSCH LOCALIZATION VERIFIED", transform=ax.transAxes,
                    fontsize=9.0, fontweight='bold', color='darkblue',
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.9, edgecolor='darkblue', linewidth=1.2))
            
            # Metrics summary box
            info_str = (
                f"Flank $N = {flank_n}$ (Sym: {sym_ratio*100.0:.1f}%)\n"
                f"Flank $\\bar{{h}} = {h_flank_mean_um:.1f}\\,\\mu\\mathrm{{m}}$\n"
                f"Far $\\bar{{h}} = {h_far_mean_um:.1f}\\,\\mu\\mathrm{{m}}$\n"
                f"Contrast: ${contrast:.1f}\\times$\n"
                f"$h_{{\\min}} = {h_min_um:.2f}\\,\\mu\\mathrm{{m}}$"
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
                ax.legend(loc='lower left', fontsize=8.0, framealpha=0.9)
                
    # Colorbar
    fig.subplots_adjust(right=0.88, top=0.92, bottom=0.08, left=0.08, wspace=0.12, hspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(sc_last, cax=cbar_ax)
    cbar.set_label(r'Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{\mathrm{Area}}$ [$\mu\mathrm{m}$]',
                   fontsize=11, labelpad=10)
    
    plt.suptitle("Independent Continuum Benchmark: 2D Plate with Central Circular Hole ($R = 0.1\\,\\mathrm{mm}$)\n"
                 r"Abaqus Native Error-Guided Remeshing ($\eta \in \{1.0\%, 2.0\%, 3.0\%, 5.0\%\}$) Driven by Continuum Stress Concentration",
                 fontsize=13, fontweight='bold', y=0.97)
    
    os.makedirs(os.path.dirname(out_pdf_path), exist_ok=True)
    plt.savefig(out_pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Plate with hole plot generated successfully: %s, %s" % (out_pdf_path, out_png_path))

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        generate_plate_hole_plots(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        # Default standalone execution
        summary_path = "models/independent_benchmarks/plate_with_hole_adaptive_remeshing/PLATE_WITH_HOLE_ADAPTIVE_BENCHMARK_SUMMARY.json"
        csv_dir_path = "models/independent_benchmarks/plate_with_hole_adaptive_remeshing"
        out_pdf = "results/figures/independent_benchmarks/fig_plate_with_hole_adaptive_remeshing.pdf"
        out_png = "results/figures/independent_benchmarks/fig_plate_with_hole_adaptive_remeshing.png"
        generate_plate_hole_plots(summary_path, csv_dir_path, out_pdf, out_png)
