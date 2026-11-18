"""Generate publication-quality mesh figures for F1856 L-Panel remeshing.
Renders:
1. results/figures/fig_f1856_lpanel_fracture_mesh.png (.pdf)
2. results/figures/fig_f1856_lpanel_elastic_mesh.png (.pdf)
3. results/figures/fig_f1856_lpanel_dual_driver_composite.png (.pdf)
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_damage_envelope_f1849 import MeshQualityAuditEngine

def render_mesh_on_axis(ax, inp_path, title, subtitle="", highlight_ligament=False):
    ns, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    polys = [[ns[n] for n in conn] for conn in list(quads.values()) + list(tris.values())]

    pcol = PolyCollection(polys, facecolors='white', edgecolors='#1a2634', linewidths=0.18, alpha=0.95)
    ax.add_collection(pcol)

    # Highlight re-entrant corner (50, 50)
    ax.plot(50.0, 50.0, marker='*', markersize=12, color='crimson', markeredgecolor='black', zorder=10, label='Corner $(50, 50)$')

    # Domain boundary outline
    l_outline_x = [0, 100, 100, 50, 50, 0, 0]
    l_outline_y = [0, 0, 50, 50, 100, 100, 0]
    ax.plot(l_outline_x, l_outline_y, color='black', linewidth=1.6, linestyle='-', zorder=5)

    if highlight_ligament:
        # Draw dashed rectangle for ligament band [0, 50] x [45, 65]
        rect = Rectangle((0, 45), 50, 20, fill=False, edgecolor='darkorange', linestyle='--', linewidth=1.5, zorder=8, label='Ligament Band ($100\\%\\ h \\leq l_0$)')
        ax.add_patch(rect)

    ax.set_xlim(-5, 105)
    ax.set_ylim(-5, 105)
    ax.set_aspect('equal')
    ax.set_xlabel('Coordinate $x$ [mm]', fontsize=10)
    ax.set_ylabel('Coordinate $y$ [mm]', fontsize=10)
    ax.set_title(title + '\n' + subtitle, fontsize=10.5, pad=8, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.legend(loc='upper right', framealpha=0.95, fontsize=8.5)

def main():
    fig_dir = os.path.join(REPO_ROOT, 'results', 'figures')
    os.makedirs(fig_dir, exist_ok=True)

    frac_inp = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'fracture_remesh', 'PK_ADAPT_UNFAMILIAR_L_PANEL_PHYS.inp')
    elas_inp = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '285_f1856_lpanel_damage_envelope_remesh', 'elastic_fallback_remesh', 'PK_GEN_ADAPT_UNFAMILIAR_L_PANEL_PHYS.inp')

    # Styling
    plt.rcParams.update({
        'font.size': 10,
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'figure.titlesize': 12,
        'mathtext.fontset': 'stix',
        'font.family': 'STIXGeneral'
    })

    # =========================================================================
    # Figure 1: Standalone Fracture Damage-Envelope Mesh
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7.2, 7.0), dpi=300)
    render_mesh_on_axis(
        ax, frac_inp,
        title='F1856: L-Panel Fracture Remesh (CONSTRUCTED_DAMAGE_ENVELOPE)',
        subtitle='15,896 elements | 98.11% quads | min det(J)=0.0175 | Ligament: 100% h <= l0',
        highlight_ligament=True
    )
    p_png = os.path.join(fig_dir, 'fig_f1856_lpanel_fracture_mesh.png')
    p_pdf = os.path.join(fig_dir, 'fig_f1856_lpanel_fracture_mesh.pdf')
    fig.savefig(p_png, dpi=300, bbox_inches='tight')
    fig.savefig(p_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved fracture mesh figure:", p_png)

    # =========================================================================
    # Figure 2: Standalone Elastic Native-Fallback Mesh
    # =========================================================================
    fig, ax = plt.subplots(figsize=(7.2, 7.0), dpi=300)
    render_mesh_on_axis(
        ax, elas_inp,
        title='F1856: L-Panel Elastic Fallback Remesh (NATIVE_ABAQUS_STRESS_RECOVERY_ERROR)',
        subtitle='567 elements | 97.53% quads | min det(J)=0.2113 | Gate 06: 2.58x (PASS)',
        highlight_ligament=False
    )
    p_png = os.path.join(fig_dir, 'fig_f1856_lpanel_elastic_mesh.png')
    p_pdf = os.path.join(fig_dir, 'fig_f1856_lpanel_elastic_mesh.pdf')
    fig.savefig(p_png, dpi=300, bbox_inches='tight')
    fig.savefig(p_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved elastic mesh figure:", p_png)

    # =========================================================================
    # Figure 3: Composite Synthesis Figure (1x2 side-by-side)
    # =========================================================================
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 6.8), dpi=300)
    render_mesh_on_axis(
        ax1, frac_inp,
        title='(a) Fracture Donor Remesh: Damage Envelope Driver',
        subtitle='15,896 elements (98.11% quads) | Selected: max(d)=0.677 >= 0.50\nLigament: 3,365 elements (100% h <= l0, 31.4% h <= l0/2)',
        highlight_ligament=True
    )
    render_mesh_on_axis(
        ax2, elas_inp,
        title='(b) Elastic Donor Remesh: Native Error Fallback Driver',
        subtitle='567 elements (97.53% quads) | Selected: max(d)=0.0 < 0.50 (Gate PASS)\nCorner: Gate 06 = 2.58x (PASS) | Mesh block 100% identical to F1846',
        highlight_ligament=False
    )
    fig.suptitle('F1856: Autonomous Driver Selection on Unfamiliar L-Panel Geometry\nFramework generalized_2d_adaptive_framework_driver_selection_f1852.py (42217DAB)', fontsize=12, fontweight='bold', y=0.98)
    p_png = os.path.join(fig_dir, 'fig_f1856_lpanel_dual_driver_composite.png')
    p_pdf = os.path.join(fig_dir, 'fig_f1856_lpanel_dual_driver_composite.pdf')
    fig.savefig(p_png, dpi=300, bbox_inches='tight')
    fig.savefig(p_pdf, bbox_inches='tight')
    plt.close(fig)
    print("Saved composite synthesis figure:", p_png)

if __name__ == '__main__':
    main()
