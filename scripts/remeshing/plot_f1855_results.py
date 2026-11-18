"""Generate publication-quality figures for F1855 L-Panel fracture Job-1.
Renders:
1. results/figures/fig_f1855_lpanel_damage_contour.png (.pdf)
2. results/figures/fig_f1855_lpanel_load_displacement.png (.pdf)
3. results/figures/fig_f1855_lpanel_fracture_job1_synthesis.png (.pdf)
"""
import os
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def main():
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    data_path = os.path.join(root_dir, 'results', 'validation', 'f1855_plot_data.json')
    fig_dir = os.path.join(root_dir, 'results', 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    with open(data_path, 'r') as f:
        data = json.load(f)

    elements = data['elements']
    nodes = {int(k): v for k, v in data['nodes'].items()}
    ld_curve = data['ld_curve']
    peak_pt = data['peak_pt']
    final_pt = data['final_pt']
    top_el = data['top_element']

    # Set style
    plt.style.use('seaborn-v0_8-paper' if 'seaborn-v0_8-paper' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 11,
        'axes.titlesize': 12,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 13,
        'mathtext.fontset': 'stix',
        'font.family': 'STIXGeneral'
    })

    # =========================================================================
    # Figure 1: L-Panel Damage Field Contour
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7.5, 7.0), dpi=300)

    patches = []
    damage_vals = []

    for el in elements:
        conn = el['connectivity']
        pts = np.array([nodes[nid][:2] for nid in conn])
        patches.append(Polygon(pts, closed=True))
        damage_vals.append(el['damage'])

    damage_vals = np.array(damage_vals)
    cmap = cm.viridis
    norm = mcolors.Normalize(vmin=0.0, vmax=max(0.70, float(np.max(damage_vals))))

    pcol = PatchCollection(patches, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.5, alpha=0.92)
    pcol.set_array(damage_vals)
    ax.add_collection(pcol)

    # Re-entrant corner highlight
    ax.plot(50.0, 50.0, marker='*', markersize=14, color='crimson', markeredgecolor='black', markeredgewidth=1.2, zorder=10, label='Re-entrant Corner $(50, 50)$')

    # Peak damage element centroid
    peak_cx, peak_cy = top_el['centroid']
    ax.plot(peak_cx, peak_cy, marker='o', markersize=9, color='gold', markeredgecolor='black', markeredgewidth=1.2, zorder=11, label=r'Peak Damage Element 93 ($d = 0.6772$)')

    # Ligament crack propagation annotation
    ax.annotate(r'Crack Initiation at $(50, 50)$' + '\n' + r'$d_{\max} = 0.6772 \geq 0.5$',
                xy=(peak_cx, peak_cy), xytext=(peak_cx - 28, peak_cy + 18),
                arrowprops=dict(facecolor='black', edgecolor='black', arrowstyle='->', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='darkred', lw=1.2, alpha=0.95),
                fontweight='bold', color='darkred', fontsize=9.5)

    # Domain boundary outline for clear visualization
    l_outline_x = [0, 100, 100, 50, 50, 0, 0]
    l_outline_y = [0, 0, 50, 50, 100, 100, 0]
    ax.plot(l_outline_x, l_outline_y, color='black', linewidth=1.8, linestyle='-', zorder=5)

    # Inset Zoom around notch
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes
    ax_inset = inset_axes(ax, width="38%", height="38%", loc='lower left', bbox_to_anchor=(0.04, 0.04, 0.9, 0.9), bbox_transform=ax.transAxes)

    patches_inset = []
    damage_inset = []
    for el in elements:
        conn = el['connectivity']
        pts = np.array([nodes[nid][:2] for nid in conn])
        patches_inset.append(Polygon(pts, closed=True))
        damage_inset.append(el['damage'])

    pcol_inset = PatchCollection(patches_inset, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.6, alpha=0.95)
    pcol_inset.set_array(np.array(damage_inset))
    ax_inset.add_collection(pcol_inset)
    ax_inset.plot(50.0, 50.0, marker='*', markersize=11, color='crimson', markeredgecolor='black', zorder=10)
    ax_inset.plot(peak_cx, peak_cy, marker='o', markersize=7, color='gold', markeredgecolor='black', zorder=11)
    ax_inset.set_xlim(30, 60)
    ax_inset.set_ylim(40, 70)
    ax_inset.set_title('Notch Region Zoom', fontsize=8.5, fontweight='bold', pad=3)
    ax_inset.tick_params(labelsize=7)
    ax_inset.grid(True, linestyle=':', alpha=0.5)

    # Colorbar
    cbar = fig.colorbar(pcol, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
    cbar.set_label(r'Phase-Field Damage $d$ (SDV1)', fontsize=11, labelpad=8)
    cbar.ax.axhline(0.5, color='red', linestyle='--', linewidth=1.5, label=r'$d_{\rm core} = 0.5$')

    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')
    ax.set_xlabel('Coordinate $x$ [mm]')
    ax.set_ylabel('Coordinate $y$ [mm]')
    ax.set_title(r'F1855: L-Panel Phase-Field Damage Contour on Coarse Mesh (340 Elements)' + '\n' +
                 r'Job 1424382.mmaster02 ($u_2 = 0.1391\,\rm{mm}$, $t = 0.3908$)', pad=10)
    ax.legend(loc='upper right', framealpha=0.95, facecolor='white', edgecolor='gray')
    ax.grid(True, linestyle=':', alpha=0.4)

    fig_damage_png = os.path.join(fig_dir, 'fig_f1855_lpanel_damage_contour.png')
    fig_damage_pdf = os.path.join(fig_dir, 'fig_f1855_lpanel_damage_contour.pdf')
    fig.savefig(fig_damage_png, dpi=300, bbox_inches='tight')
    fig.savefig(fig_damage_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved damage contour:", fig_damage_png)

    # =========================================================================
    # Figure 2: Load-Displacement Response
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7.2, 5.0), dpi=300)

    u2_vals = [pt['u2_mm'] for pt in ld_curve]
    rf2_vals = [pt['rf2_kn'] for pt in ld_curve]

    # Split into Step-1 and Step-2
    s1_u2 = [pt['u2_mm'] for pt in ld_curve if pt['step'] == 'Step-1']
    s1_rf2 = [pt['rf2_kn'] for pt in ld_curve if pt['step'] == 'Step-1']
    s2_u2 = [pt['u2_mm'] for pt in ld_curve if pt['step'] == 'Step-2']
    s2_rf2 = [pt['rf2_kn'] for pt in ld_curve if pt['step'] == 'Step-2']

    ax.plot(s1_u2, s1_rf2, color='navy', lw=2.0, label=r'Step-1: Precritical Loading ($u_2 \leq 0.10\,\mathrm{mm}$)')
    ax.plot(s2_u2, s2_rf2, color='crimson', lw=2.2, label=r'Step-2: Fracture Softening ($u_2 > 0.10\,\mathrm{mm}$)')

    # Mark Peak
    ax.plot(peak_pt['u2_mm'], peak_pt['rf2_kn'], marker='s', markersize=8, color='gold', markeredgecolor='black', zorder=10,
            label=r'Peak Reaction Force: $F_{\max} = 12.024\,\mathrm{kN}$ at $u_2 = 0.1352\,\mathrm{mm}$')

    # Mark Cutback Termination
    ax.plot(final_pt['u2_mm'], final_pt['rf2_kn'], marker='X', markersize=9, color='darkred', markeredgecolor='black', zorder=10,
            label=r'Cutback Termination: $F = 11.633\,\mathrm{kN}$ at $u_2 = 0.1391\,\mathrm{mm}$')

    # Softening annotation
    drop_pct = (peak_pt['rf2_kn'] - final_pt['rf2_kn']) / peak_pt['rf2_kn'] * 100.0
    ax.annotate(r'$\mathbf{Softening\ Initiated:}$' + '\n' +
                r'$\Delta F = -0.391\,\mathrm{kN}$ ($-3.25\%$) before min $\Delta t$',
                xy=(final_pt['u2_mm'], final_pt['rf2_kn']), xytext=(0.065, 8.5),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                bbox=dict(boxstyle='round,pad=0.4', fc='white', ec='crimson', lw=1.2, alpha=0.95),
                fontsize=9.5)

    ax.set_xlabel('Vertical Displacement $u_2$ [mm]')
    ax.set_ylabel('Reaction Force $F_2$ [kN]')
    ax.set_title('F1855: L-Panel Load-Displacement Response (Job 1424382.mmaster02)\nFrozen Isotropic UEL (CE8D5EDC) + F1830 Native Interface (E5C98B6F)', pad=10)
    ax.set_xlim(0.0, 0.15)
    ax.set_ylim(0.0, 13.5)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='lower right', framealpha=0.95, facecolor='white', edgecolor='gray')

    fig_ld_png = os.path.join(fig_dir, 'fig_f1855_lpanel_load_displacement.png')
    fig_ld_pdf = os.path.join(fig_dir, 'fig_f1855_lpanel_load_displacement.pdf')
    fig.savefig(fig_ld_png, dpi=300, bbox_inches='tight')
    fig.savefig(fig_ld_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved load-displacement plot:", fig_ld_png)

    # =========================================================================
    # Figure 3: Composite Synthesis Figure (1x2 side-by-side)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=300)

    # Panel A: Damage contour
    pcol1 = PatchCollection(patches, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.4, alpha=0.92)
    pcol1.set_array(damage_vals)
    ax1.add_collection(pcol1)
    ax1.plot(50.0, 50.0, marker='*', markersize=12, color='crimson', markeredgecolor='black', zorder=10, label='Re-entrant Corner')
    ax1.plot(peak_cx, peak_cy, marker='o', markersize=8, color='gold', markeredgecolor='black', zorder=11, label=r'Peak $d_{\max} = 0.6772$')
    ax1.plot(l_outline_x, l_outline_y, color='black', linewidth=1.5, zorder=5)
    ax1.set_xlim(-5, 105)
    ax1.set_ylim(-5, 105)
    ax1.set_aspect('equal')
    ax1.set_xlabel('Coordinate $x$ [mm]')
    ax1.set_ylabel('Coordinate $y$ [mm]')
    ax1.set_title('(a) Phase-Field Damage Field $d$ (SDV1) on Coarse Mesh', pad=8, fontweight='bold')
    ax1.legend(loc='upper right', framealpha=0.95, fontsize=8.5)
    ax1.grid(True, linestyle=':', alpha=0.4)
    cbar1 = fig.colorbar(pcol1, ax=ax1, orientation='vertical', fraction=0.046, pad=0.04)
    cbar1.set_label(r'Damage $d$ (SDV1)')

    # Panel B: Load-displacement
    ax2.plot(s1_u2, s1_rf2, color='navy', lw=2.0, label=r'Step-1: Precritical ($u_2 \leq 0.10\,\mathrm{mm}$)')
    ax2.plot(s2_u2, s2_rf2, color='crimson', lw=2.2, label=r'Step-2: Softening ($u_2 > 0.10\,\mathrm{mm}$)')
    ax2.plot(peak_pt['u2_mm'], peak_pt['rf2_kn'], marker='s', markersize=8, color='gold', markeredgecolor='black', zorder=10,
             label=r'Peak: $F_{\max} = 12.024\,\mathrm{kN}$')
    ax2.plot(final_pt['u2_mm'], final_pt['rf2_kn'], marker='X', markersize=9, color='darkred', markeredgecolor='black', zorder=10,
             label=r'Termination: $F = 11.633\,\mathrm{kN}$')
    ax2.set_xlabel('Vertical Displacement $u_2$ [mm]')
    ax2.set_ylabel('Reaction Force $F_2$ [kN]')
    ax2.set_title('(b) Structural Reaction Force vs. Displacement Curve', pad=8, fontweight='bold')
    ax2.set_xlim(0.0, 0.15)
    ax2.set_ylim(0.0, 13.5)
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='lower right', framealpha=0.95, fontsize=8.5)

    fig_synth_png = os.path.join(fig_dir, 'fig_f1855_lpanel_fracture_job1_synthesis.png')
    fig_synth_pdf = os.path.join(fig_dir, 'fig_f1855_lpanel_fracture_job1_synthesis.pdf')
    fig.savefig(fig_synth_png, dpi=300, bbox_inches='tight')
    fig.savefig(fig_synth_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved composite synthesis figure:", fig_synth_png)
    plt.close(fig)
    print("Saved composite synthesis figure:", fig_synth_png)

if __name__ == '__main__':
    main()
