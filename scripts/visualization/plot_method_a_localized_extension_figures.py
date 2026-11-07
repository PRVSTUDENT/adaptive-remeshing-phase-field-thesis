# -*- coding: utf-8 -*-
"""Generate publication-quality figures for Damage-Informed Localized Method A Extension.

Produces 4 publication-quality figures (300 DPI PNG and vector PDF):
  1. fig_method_a_localized_extension_full_mesh: Full 1x1 mm plate adapted mesh.
  2. fig_method_a_localized_extension_zoom_mesh: Zoomed view of notch, ligament, and hole.
  3. fig_method_a_native_vs_localized_comparison: Side-by-side native (46,747) vs localized (23,664) mesh.
  4. fig_method_a_indicator_support_overlay: Precritical indicator support overlaid with resulting mesh resolution.
"""
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Polygon, Rectangle
import matplotlib.ticker as ticker
from scipy.spatial import ConvexHull

from scripts.validation.validate_method_a_localized_extension_mesh import parse_inp_mesh

def compute_polys_and_metrics(nodes, elements):
    polys = []
    max_edges = []
    h_equivs = []
    centroids = []
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        n_pts = len(coords)
        if n_pts < 3: continue
        polys.append(coords)
        x = [c[0] for c in coords]
        y = [c[1] for c in coords]
        area = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(n_pts-1)) + (x[-1]*y[0] - x[0]*y[-1]))
        edge_lens = [np.hypot(x[(i+1)%n_pts] - x[i], y[(i+1)%n_pts] - y[i]) for i in range(n_pts)]
        max_edges.append(max(edge_lens) * 1000.0)
        h_equivs.append(np.sqrt(area) * 1000.0)
        centroids.append((np.mean(x), np.mean(y)))
    return polys, np.array(max_edges), np.array(h_equivs), np.array(centroids)

def save_fig(fig, base_name, out_dirs):
    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        png_path = os.path.join(d, base_name + '.png')
        pdf_path = os.path.join(d, base_name + '.pdf')
        fig.savefig(png_path, dpi=300, bbox_inches='tight')
        fig.savefig(pdf_path, bbox_inches='tight')
        print("Saved %s and %s" % (png_path, pdf_path))

def main():
    out_dirs = [
        'MA_AdaptiveRemeshing_Report_2026/figures',
        'docs/MA_AdaptiveRemeshing_Report_2026_main/figures'
    ]
    
    localized_phys = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_EXT_PHYS.inp'
    native_phys = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_ORIG_METHOD_A_PROD_PHYS.inp'
    
    print("Parsing localized mesh...")
    nodes_loc, elems_loc = parse_inp_mesh(localized_phys)
    polys_loc, me_loc, he_loc, cents_loc = compute_polys_and_metrics(nodes_loc, elems_loc)
    
    print("Parsing native mesh...")
    nodes_nat, elems_nat = parse_inp_mesh(native_phys)
    polys_nat, me_nat, he_nat, cents_nat = compute_polys_and_metrics(nodes_nat, elems_nat)
    
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['mathtext.fontset'] = 'cm'
    
    norm_h = matplotlib.colors.LogNorm(vmin=1.0, vmax=25.0)
    cmap = plt.cm.viridis_r
    
    # -------------------------------------------------------------
    # Figure 1: Full 1x1 mm Plate Localized Adapted Mesh
    # -------------------------------------------------------------
    print("Generating Figure 1: Full Localized Mesh...")
    fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=300)
    
    pc = PolyCollection(polys_loc, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.12)
    pc.set_array(he_loc)
    ax.add_collection(pc)
    
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.5, label=r'Notch ($a_0 = 0.5\,\mathrm{mm}$)')
    ax.scatter([0.5], [0.5], color='#d90429', s=50, zorder=5, label=r'Notch tip $(0.5, 0.5)$')
    
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4, label=r'Hole ($R = 0.10\,\mathrm{mm}$)')
    ax.add_patch(hole)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=60, zorder=5)
    
    zoom_rect = Rectangle((0.44, 0.44), 0.38, 0.38, linewidth=1.8, edgecolor='#0077b6', facecolor='none', linestyle=':', zorder=6, label=r'Zoom window')
    ax.add_patch(zoom_rect)
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel(r'$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title(r'Damage-Informed Localized Method A Mesh ($N = 23,664$ elements)', fontsize=13, fontweight='bold', pad=10)
    
    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Equivalent element size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    ax.legend(loc='lower left', framealpha=0.92, fontsize=9.5, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.4, color='#888888')
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_localized_extension_full_mesh', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 2: Zoomed Fracture Process Zone Mesh
    # -------------------------------------------------------------
    print("Generating Figure 2: Zoomed Fracture Process Zone...")
    fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=300)
    
    pc_zoom = PolyCollection(polys_loc, cmap=cmap, norm=norm_h, edgecolors='#222222', linewidths=0.25)
    pc_zoom.set_array(he_loc)
    ax.add_collection(pc_zoom)
    
    ax.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=3.0, label=r'Notch ($a_0 = 0.5\,\mathrm{mm}$)')
    ax.scatter([0.5], [0.5], color='#d90429', s=70, zorder=5, label=r'Notch tip $(0.5, 0.5)$')
    
    hole_zoom = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.5, linestyle='--', zorder=4, label=r'Hole ($R = 0.10\,\mathrm{mm}$)')
    ax.add_patch(hole_zoom)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=80, zorder=5)
    
    ax.set_xlim(0.44, 0.82)
    ax.set_ylim(0.44, 0.82)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel(r'$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title(r'Localized Method A: Zoomed Ligament & Hole Discretization', fontsize=13, fontweight='bold', pad=10)
    
    cbar = fig.colorbar(pc_zoom, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Equivalent element size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    ax.legend(loc='lower right', framealpha=0.92, fontsize=10, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.5, color='#888888')
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_localized_extension_zoom_mesh', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 3: Side-by-Side Native vs Localized Mesh Comparison
    # -------------------------------------------------------------
    print("Generating Figure 3: Side-by-Side Comparison...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.0), dpi=300)
    
    # Left: Native Method A (46,747 elements, bulk over-refined)
    pc1 = PolyCollection(polys_nat, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.10)
    pc1.set_array(he_nat)
    ax1.add_collection(pc1)
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2)
    ax1.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5)
    h1 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax1.add_patch(h1)
    ax1.scatter([0.65], [0.65], color='#d90429', marker='+', s=50, zorder=5)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_xlabel(r'$x$ [mm]', fontsize=11)
    ax1.set_ylabel(r'$y$ [mm]', fontsize=11)
    ax1.set_title(r'(a) Native Method A ($N = 46,747$, Bulk Over-Refined)', fontsize=12, fontweight='bold', pad=8)
    ax1.grid(True, linestyle=':', alpha=0.3)
    
    # Right: Damage-Informed Localized Method A (23,664 elements, selective)
    pc2 = PolyCollection(polys_loc, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.12)
    pc2.set_array(he_loc)
    ax2.add_collection(pc2)
    ax2.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2)
    ax2.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5)
    h2 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax2.add_patch(h2)
    ax2.scatter([0.65], [0.65], color='#d90429', marker='+', s=50, zorder=5)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect('equal')
    ax2.set_xlabel(r'$x$ [mm]', fontsize=11)
    ax2.set_ylabel(r'$y$ [mm]', fontsize=11)
    ax2.set_title(r'(b) Damage-Informed Extension ($N = 23,664$, Selective)', fontsize=12, fontweight='bold', pad=8)
    ax2.grid(True, linestyle=':', alpha=0.3)
    
    # Shared colorbar
    fig.subplots_adjust(right=0.88, wspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    cbar = fig.colorbar(pc2, cax=cbar_ax)
    cbar.set_label(r'Equivalent element size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    save_fig(fig, 'fig_method_a_native_vs_localized_comparison', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 4: Indicator Support Overlay vs Mesh Resolution
    # -------------------------------------------------------------
    print("Generating Figure 4: Indicator Support Overlay...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.8), dpi=300)
    
    # Load authentic precritical damage points
    from scripts.remeshing.generate_damage_informed_method_a_mesh import compute_indicator_support_boundary
    support_verts = compute_indicator_support_boundary(
        'results/validation/f1642_pilot_localized_damage.csv', d_thresh=0.08, l0=0.0075
    )
    poly_support = Polygon(support_verts, closed=True, edgecolor='#00f0ff', facecolor='none', linewidth=2.2, linestyle='-', zorder=6, label=r'Indicator support $\Omega_{\mathrm{FPZ}} \oplus \mathcal{B}_{3\ell_0}$')
    
    # Panel 1: Precritical damage field with indicator support contour
    # Scatter damage points
    import csv
    d_pts = []
    with open('results/validation/f1642_pilot_top_damage_elements.csv') as f:
        for r in csv.DictReader(f):
            d_pts.append((float(r['x']), float(r['y']), float(r['damage'])))
    d_pts = np.array(d_pts)
    
    sc = ax1.scatter(d_pts[:,0], d_pts[:,1], c=d_pts[:,2], cmap='plasma', s=8, vmin=0.0, vmax=0.45, zorder=3)
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2)
    ax1.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5)
    h_ov1 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax1.add_patch(h_ov1)
    ax1.add_patch(poly_support)
    ax1.set_xlim(0.44, 0.82)
    ax1.set_ylim(0.44, 0.82)
    ax1.set_aspect('equal')
    ax1.set_xlabel(r'$x$ [mm]', fontsize=11)
    ax1.set_ylabel(r'$y$ [mm]', fontsize=11)
    ax1.set_title(r'(a) Precritical Damage $d \geq 0.08$ & Support Boundary', fontsize=12, fontweight='bold', pad=8)
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.legend(loc='lower left', framealpha=0.9, fontsize=9.5)
    cb1 = fig.colorbar(sc, ax=ax1, fraction=0.046, pad=0.04)
    cb1.set_label(r'Precritical Phase-Field Damage $d$', fontsize=11, labelpad=8)
    
    # Panel 2: Resulting adapted element size with indicator support contour
    pc_ov = PolyCollection(polys_loc, cmap=cmap, norm=norm_h, edgecolors='#333333', linewidths=0.20)
    pc_ov.set_array(he_loc)
    ax2.add_collection(pc_ov)
    poly_support2 = Polygon(support_verts, closed=True, edgecolor='#d90429', facecolor='none', linewidth=2.2, linestyle='--', zorder=6, label=r'Indicator support boundary')
    ax2.add_patch(poly_support2)
    ax2.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.5)
    ax2.scatter([0.5], [0.5], color='#d90429', s=50, zorder=5)
    h_ov2 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax2.add_patch(h_ov2)
    ax2.set_xlim(0.44, 0.82)
    ax2.set_ylim(0.44, 0.82)
    ax2.set_aspect('equal')
    ax2.set_xlabel(r'$x$ [mm]', fontsize=11)
    ax2.set_ylabel(r'$y$ [mm]', fontsize=11)
    ax2.set_title(r'(b) Adapted Mesh Resolution $h$ & Support Alignment', fontsize=12, fontweight='bold', pad=8)
    ax2.grid(True, linestyle=':', alpha=0.3)
    ax2.legend(loc='lower left', framealpha=0.9, fontsize=9.5)
    cb2 = fig.colorbar(pc_ov, ax=ax2, fraction=0.046, pad=0.04)
    cb2.set_label(r'Equivalent element size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=11, labelpad=8)
    cb2.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_indicator_support_overlay', out_dirs)
    plt.close(fig)
    print("All 4 publication figures generated successfully!")

if __name__ == '__main__':
    main()
