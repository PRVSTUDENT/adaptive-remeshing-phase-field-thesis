"""
Independent Benchmark Plotting: Plate with Central Circular Hole Adaptive Remeshing.
Generates publication-quality 4-panel figure showing symmetric stress concentration
refinement across errorTarget = 1, 2, 3, 5%.
"""
import os
import sys
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

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
            
    fig = plt.figure(figsize=(14, 11))
    
    theta = np.linspace(0, 2*np.pi, 200)
    circle_x = 0.5 + 0.1 * np.cos(theta)
    circle_y = 0.5 + 0.1 * np.sin(theta)
    
    for idx, et in enumerate(error_targets, start=1):
        ax = fig.add_subplot(2, 2, idx)
        if et in dfs:
            df = dfs[et]
            sc = ax.scatter(df['cx'], df['cy'], c=df['h_eq']*1000.0, cmap='plasma_r',
                            s=np.clip(25.0 - df['h_eq']*400.0, 2.0, 25.0), alpha=0.75)
            
            # Plot circular hole
            ax.plot(circle_x, circle_y, 'k-', linewidth=2.5, label='Circular Hole ($R=0.1$)')
            # Plot lateral flank markers
            ax.plot([0.4], [0.5], 'ro', markersize=6, label='Peak Stress Concentration ($K_t \\approx 3$)')
            ax.plot([0.6], [0.5], 'ro', markersize=6)
            
            cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
            cbar.set_label('Equivalent Size $h_{\\mathrm{eq}}$ [$\\mu\\mathrm{m}$]', fontsize=10)
            
            case_data = summary.get('results_by_error_target', {}).get(str(et), {})
            total_n = case_data.get('total_elements', len(df))
            sym_ratio = case_data.get('flank_symmetry_ratio', 1.0)
            flank_n = case_data.get('total_flank_elements', 0)
            
            ax.set_title(r"$\mathbf{errorTarget = %.1f\%%}$ ($N = %d$, Flank $N = %d$, Sym: $%.2f$)" % (
                et, total_n, flank_n, sym_ratio), fontsize=12, fontweight='bold')
            ax.set_xlabel('Plate Coordinate $x$ [mm]', fontsize=11)
            ax.set_ylabel('Plate Coordinate $y$ [mm]', fontsize=11)
            ax.set_xlim(0.0, 1.0)
            ax.set_ylim(0.0, 1.0)
            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.6)
            if idx == 1:
                ax.legend(loc='lower left', fontsize=8.5)
                
    plt.suptitle("Independent Benchmark: 2D Plate with Central Circular Hole ($R=0.1\\,\\mathrm{mm}$)\n"
                 "Abaqus Native MISESERI Adaptive Remeshing Verification across Error Targets",
                 fontsize=14, fontweight='bold', y=0.99)
    plt.tight_layout()
    plt.savefig(out_pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Plate with hole plot saved: %s, %s" % (out_pdf_path, out_png_path))

if __name__ == "__main__":
    if len(sys.argv) >= 5:
        generate_plate_hole_plots(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
