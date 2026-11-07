"""
scripts/visualization/plot_f1679_time_resolved_crack.py
======================================================
Generates a multi-panel publication-quality figure illustrating the time-resolved
two-stage phase-field crack propagation, arrest at the off-axis hole, and secondary
snap-through to complete severance for the Method A 20,213-element mesh.
"""

import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd

def main():
    summary_path = "results/validation/f1679_time_resolved_crack_summary.json"
    csv_path = "results/validation/f1679_time_resolved_crack_states.csv"
    rf_u_path = "results/validation/f1678_prod_rf_u.csv"

    with open(summary_path, 'r') as f:
        summaries = json.load(f)

    df_states = pd.read_csv(csv_path)
    df_rf = pd.read_csv(rf_u_path)

    # Setup 4 key chronological panels + 1 load-displacement overview
    # Selected states:
    # 1. Peak force (step2_peak, u=0.00570 mm)
    # 2. Primary crack reaches hole (step2_inc180, u=0.00752 mm)
    # 3. Secondary nucleation at hole flank (step2_inc198, u=0.00776 mm)
    # 4. Final severed state (step2_final, u=0.01200 mm)
    panels = [
        {"name": "step2_peak", "title": "(a) Damage Initiation at Notch Tip\n$u = 0.00570$ mm, $P = 0.593$ kN"},
        {"name": "step2_inc180", "title": "(b) Primary Deflection & Arrest at Hole\n$u = 0.00752$ mm, $P = 0.494$ kN"},
        {"name": "step2_inc198", "title": "(c) Secondary Crack Nucleation\n$u = 0.00776$ mm, $P = 0.471$ kN"},
        {"name": "step2_final", "title": "(d) Complete Ligament Severance\n$u = 0.01200$ mm, $P = 0.0004$ kN"}
    ]

    fig = plt.figure(figsize=(15, 11), dpi=300)
    # 2x2 grid of crack maps on the left/center, 1 load-displacement curve on bottom or right
    # Let's use GridSpec: top row (2 panels), bottom row (2 panels), right side or separate layout
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(2, 3, figure=fig, width_ratios=[1, 1, 1.15], wspace=0.25, hspace=0.30)

    hole_center = (0.65, 0.65)
    hole_radius = 0.10

    scatter_handles = []
    for idx, pinfo in enumerate(panels):
        row = idx // 2
        col = idx % 2
        ax = fig.add_subplot(gs[row, col])

        # Draw specimen outline
        rect = patches.Rectangle((0, 0), 1.0, 1.0, linewidth=1.2, edgecolor='black', facecolor='#fcfcfc', zorder=1)
        ax.add_patch(rect)

        # Draw initial horizontal notch
        ax.plot([0.0, 0.50], [0.50, 0.50], color='black', linewidth=2.5, solid_capstyle='round', zorder=4)

        # Draw off-axis circular hole
        hole = patches.Circle(hole_center, hole_radius, linewidth=1.2, edgecolor='black', facecolor='white', zorder=3)
        ax.add_patch(hole)

        # Filter damaged elements for this state
        sub = df_states[df_states['state_name'] == pinfo['name']]
        
        # Plot damage field using scatter
        # Clamp damage to [0, 1] for visual colormap
        d_vals = np.clip(sub['damage'].values, 0.0, 1.0)
        sc = ax.scatter(
            sub['x_mm'].values, sub['y_mm'].values,
            c=d_vals, cmap='plasma', s=4, vmin=0.0, vmax=1.0, alpha=0.9, zorder=2
        )
        scatter_handles.append(sc)

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_title(pinfo['title'], fontsize=11, fontweight='bold', pad=8)
        ax.set_xlabel('$x$ [mm]', fontsize=10)
        ax.set_ylabel('$y$ [mm]', fontsize=10)
        ax.grid(True, linestyle=':', alpha=0.4)

    # Plot (e) Load-Displacement P(u) curve on the right (spanning both rows)
    ax_rf = fig.add_subplot(gs[:, 2])
    u_vals = df_rf['u2_mm'].values
    rf_vals = df_rf['rf2_kN'].values
    ax_rf.plot(u_vals * 1000, rf_vals, color='#1f77b4', linewidth=2.0, label='Method A Refined ($20{,}213$ FEs)')

    # Add markers for the 4 chronological states
    marker_states = [
        (0.00570, 0.59339, '(a) Peak Load', '#d62728', 'o'),
        (0.00752, 0.49399, '(b) Hole Arrest', '#ff7f0e', 's'),
        (0.00776, 0.47128, '(c) Flank Nucleation', '#9467bd', '^'),
        (0.01200, 0.000415, '(d) Final Severance', '#2ca02c', 'D')
    ]
    for u_m, p_m, lbl, col, mkr in marker_states:
        ax_rf.scatter([u_m * 1000], [p_m], color=col, s=70, marker=mkr, zorder=5, label=lbl)

    ax_rf.set_xlabel('Prescribed Top Displacement $u_y$ [$\\mu$m]', fontsize=11, fontweight='bold')
    ax_rf.set_ylabel('Reaction Force $P$ [kN]', fontsize=11, fontweight='bold')
    ax_rf.set_title('(e) Equilibrium Reaction Force Response', fontsize=12, fontweight='bold', pad=10)
    ax_rf.grid(True, linestyle='--', alpha=0.5)
    ax_rf.set_xlim(0, 12.5)
    ax_rf.set_ylim(-0.02, 0.65)
    ax_rf.legend(loc='upper right', fontsize=9, framealpha=0.95)

    # Add shared colorbar for damage at the bottom
    cbar_ax = fig.add_axes([0.15, 0.03, 0.40, 0.02])
    cbar = fig.colorbar(scatter_handles[0], cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Phase-Field Damage $d$ [-] ($0 = \\text{intact}, 1 = \\text{broken}$)', fontsize=10, fontweight='bold')

    out_png = "MA_AdaptiveRemeshing_Report_2026/figures/f1679_time_resolved_crack_progression.png"
    out_pdf = "MA_AdaptiveRemeshing_Report_2026/figures/f1679_time_resolved_crack_progression.pdf"
    plt.savefig(out_png, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close()
    print(f"Generated time-resolved crack progression figure: {out_png} and {out_pdf}")

if __name__ == '__main__':
    main()
