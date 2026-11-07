# -*- coding: utf-8 -*-
"""Generate publication-quality figures for Method A Original Framework benchmark.

Produces 4 publication-quality figures (300 DPI PNG and vector PDF):
  1. fig_method_a_original_framework_full_mesh: Full 1x1 mm plate showing notch, hole, adapted mesh.
  2. fig_method_a_original_framework_zoom_mesh: Zoomed view of notch tip, ligament, and off-axis hole.
  3. fig_method_a_original_vs_native_adapted: Side-by-side coarse (2,906 elements) vs adapted (46,747 elements).
  4. fig_method_a_miseseri_refinement_correlation: Preanalysis MISESERI error distribution vs adapted element resolution.
"""
import os
import re
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle
import matplotlib.ticker as ticker
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

def parse_inp_mesh(path):
    nodes = {}
    elements = {}
    current = None
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            u = line.upper()
            if re.match(r'^\*NODE\b', u) and not re.match(r'^\*NODE\s+(OUTPUT|PRINT|FILE)', u):
                current = 'NODE'
                continue
            elif re.match(r'^\*ELEMENT\b', u) and not re.match(r'^\*ELEMENT\s+(OUTPUT|PRINT|FILE)', u):
                current = 'ELEMENT'
                continue
            elif u.startswith('*'):
                current = None
                continue

            if current == 'NODE':
                parts = line.split(',')
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except (ValueError, IndexError):
                    pass
            elif current == 'ELEMENT':
                parts = [int(p.strip()) for p in line.split(',') if p.strip()]
                if len(parts) >= 4:
                    eid = parts[0]
                    elements[eid] = parts[1:]
    return nodes, elements

def compute_polys_and_h(nodes, elements):
    polys = []
    areas = []
    centroids = []
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) < 3:
            continue
        polys.append(coords)
        x = [c[0] for c in coords]
        y = [c[1] for c in coords]
        a = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(len(coords)-1)) + (x[-1]*y[0] - x[0]*y[-1]))
        areas.append(a)
        centroids.append((np.mean(x), np.mean(y)))
    h_um = np.sqrt(np.array(areas)) * 1000.0  # mm -> um
    return polys, h_um, np.array(centroids)

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
    
    # 1. Load adapted mesh
    phys_inp = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_ORIG_METHOD_A_PROD_PHYS.inp'
    print("Parsing adapted mesh: %s" % phys_inp)
    nodes_adapt, elems_adapt = parse_inp_mesh(phys_inp)
    polys_adapt, h_adapt, cents_adapt = compute_polys_and_h(nodes_adapt, elems_adapt)
    n_adapt = len(polys_adapt)
    print("Adapted mesh elements: %d" % n_adapt)
    
    # 2. Load coarse preanalysis mesh data
    npz_path = 'results/validation/method_a_plotting_data.npz'
    print("Loading coarse preanalysis data: %s" % npz_path)
    data = np.load(npz_path, allow_pickle=True)
    coarse_polys = [p.tolist() for p in data['coarse_polys']]
    coarse_miseseri = data['coarse_miseseri']
    coarse_h = data['coarse_h']
    n_coarse = len(coarse_polys)
    print("Coarse mesh elements: %d" % n_coarse)

    # Styling settings
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['mathtext.fontset'] = 'cm'
    
    # -------------------------------------------------------------
    # Figure 1: Full 1x1 mm Plate Adapted Mesh
    # -------------------------------------------------------------
    print("Generating Figure 1: Full Plate Adapted Mesh...")
    fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=300)
    norm_h = matplotlib.colors.LogNorm(vmin=1.0, vmax=25.0)
    cmap = plt.cm.viridis_r
    
    pc = PolyCollection(polys_adapt, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.10)
    pc.set_array(h_adapt)
    ax.add_collection(pc)
    
    # Notch line: x in [0, 0.5], y = 0.5
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.5, label='Initial notch ($a_0 = 0.5\\,\\mathrm{mm}$)')
    ax.scatter([0.5], [0.5], color='#d90429', s=50, zorder=5, label='Notch tip $(0.5, 0.5)$')
    
    # Hole outline
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4, label='Off-axis hole ($R = 0.10\\,\\mathrm{mm}$)')
    ax.add_patch(hole)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=60, zorder=5)
    
    # Zoom window indicator
    zoom_rect = Rectangle((0.44, 0.44), 0.38, 0.38, linewidth=1.8, edgecolor='#0077b6', facecolor='none', linestyle=':', zorder=6, label='Fracture Process Window')
    ax.add_patch(zoom_rect)
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel('$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title('Method A Original Framework: Indicator-Adapted Mesh ($N = 46,747$ elements)', fontsize=13, fontweight='bold', pad=10)
    
    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    ax.legend(loc='lower left', framealpha=0.92, fontsize=9.5, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.4, color='#888888')
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_original_framework_full_mesh', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 2: Zoomed Fracture Process Zone Mesh
    # -------------------------------------------------------------
    print("Generating Figure 2: Zoomed Fracture Process Zone...")
    fig, ax = plt.subplots(figsize=(8.5, 7.5), dpi=300)
    
    pc_zoom = PolyCollection(polys_adapt, cmap=cmap, norm=norm_h, edgecolors='#222222', linewidths=0.25)
    pc_zoom.set_array(h_adapt)
    ax.add_collection(pc_zoom)
    
    ax.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=3.0, label='Notch ($a_0 = 0.5\\,\\mathrm{mm}$)')
    ax.scatter([0.5], [0.5], color='#d90429', s=70, zorder=5, label='Notch tip $(0.5, 0.5)$')
    
    hole_zoom = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.5, linestyle='--', zorder=4, label='Hole ($R = 0.10\\,\\mathrm{mm}$)')
    ax.add_patch(hole_zoom)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=80, zorder=5)
    
    ax.set_xlim(0.44, 0.82)
    ax.set_ylim(0.44, 0.82)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel('$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title('Method A Original Framework: Zoomed Ligament & Hole Discretization', fontsize=13, fontweight='bold', pad=10)
    
    cbar = fig.colorbar(pc_zoom, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    ax.legend(loc='lower right', framealpha=0.92, fontsize=10, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.5, color='#888888')
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_original_framework_zoom_mesh', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 3: Side-by-Side Coarse vs Native Adapted Mesh
    # -------------------------------------------------------------
    print("Generating Figure 3: Side-by-Side Coarse vs Native Adapted...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.0), dpi=300)
    
    # Left: Coarse mesh
    pc_coarse = PolyCollection(coarse_polys, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.35)
    pc_coarse.set_array(coarse_h)
    ax1.add_collection(pc_coarse)
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2)
    ax1.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5)
    hole1 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax1.add_patch(hole1)
    ax1.scatter([0.65], [0.65], color='#d90429', marker='+', s=50, zorder=5)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_xlabel('$x$ [mm]', fontsize=11)
    ax1.set_ylabel('$y$ [mm]', fontsize=11)
    ax1.set_title('(a) Authentic Preanalysis Coarse Mesh ($N = 2,906$)', fontsize=12, fontweight='bold', pad=8)
    ax1.grid(True, linestyle=':', alpha=0.3)
    
    # Right: Native Adapted mesh
    pc_adapt = PolyCollection(polys_adapt, cmap=cmap, norm=norm_h, edgecolors='#1a1a1a', linewidths=0.10)
    pc_adapt.set_array(h_adapt)
    ax2.add_collection(pc_adapt)
    ax2.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2)
    ax2.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5)
    hole2 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax2.add_patch(hole2)
    ax2.scatter([0.65], [0.65], color='#d90429', marker='+', s=50, zorder=5)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect('equal')
    ax2.set_xlabel('$x$ [mm]', fontsize=11)
    ax2.set_ylabel('$y$ [mm]', fontsize=11)
    ax2.set_title('(b) Native Method A Adapted Mesh ($N = 46,747$)', fontsize=12, fontweight='bold', pad=8)
    ax2.grid(True, linestyle=':', alpha=0.3)
    
    # Shared colorbar
    fig.subplots_adjust(right=0.88, wspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    cbar = fig.colorbar(pc_adapt, cax=cbar_ax)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))
    
    save_fig(fig, 'fig_method_a_original_vs_native_adapted', out_dirs)
    plt.close(fig)

    # -------------------------------------------------------------
    # Figure 4: MISESERI Field vs Refinement Correlation
    # -------------------------------------------------------------
    print("Generating Figure 4: MISESERI vs Refinement Correlation...")
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.8), dpi=300)
    
    # Left: Preanalysis MISESERI field map
    norm_miseseri = matplotlib.colors.LogNorm(vmin=0.5, vmax=1000.0)
    pc_m = PolyCollection(coarse_polys, cmap=plt.cm.inferno, norm=norm_miseseri, edgecolors='#333333', linewidths=0.3)
    pc_m.set_array(coarse_miseseri)
    ax1.add_collection(pc_m)
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='#00f0ff', linewidth=2.2, label='Notch ($a_0 = 0.5\\,\\mathrm{mm}$)')
    hole_m = Circle((0.65, 0.65), 0.10, edgecolor='#00f0ff', facecolor='white', linewidth=2.0, linestyle='--', zorder=4, label='Hole ($R = 0.10\\,\\mathrm{mm}$)')
    ax1.add_patch(hole_m)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_xlabel('$x$ [mm]', fontsize=11)
    ax1.set_ylabel('$y$ [mm]', fontsize=11)
    ax1.set_title('(a) Authentic Preanalysis MISESERI Field ($N = 2,906$)', fontsize=12, fontweight='bold', pad=8)
    ax1.grid(True, linestyle=':', alpha=0.3)
    ax1.legend(loc='lower left', framealpha=0.9, fontsize=9.5)
    cbar1 = fig.colorbar(pc_m, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label('MISESERI Error Indicator [\\%]', fontsize=11, labelpad=8)
    
    # Right: Spatial correlation scatter plot
    # Interpolate coarse MISESERI at adapted element centroids
    coarse_cents = []
    for p in coarse_polys:
        coords = np.array(p)
        coarse_cents.append((np.mean(coords[:, 0]), np.mean(coords[:, 1])))
    tree = cKDTree(np.array(coarse_cents))
    _, idxs = tree.query(cents_adapt)
    interp_m = coarse_miseseri[idxs]
    inv_h = 1000.0 / h_adapt  # 1/mm -> refinement intensity
    
    rho, _ = spearmanr(interp_m, inv_h)
    
    # 2D Hexbin density plot for clarity with 46k elements
    hb = ax2.hexbin(interp_m, h_adapt, xscale='log', yscale='log', gridsize=45, cmap='plasma', mincnt=1, bins='log')
    ax2.set_xlabel('Preanalysis MISESERI [\\%]', fontsize=11, labelpad=6)
    ax2.set_ylabel('Adapted Element Size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=6)
    ax2.set_title('(b) Error Indicator vs Mesh Resolution (Spearman $\\rho = %.4f$)' % rho, fontsize=12, fontweight='bold', pad=8)
    ax2.grid(True, which='both', linestyle=':', alpha=0.4)
    
    # Reference lines
    ax2.axhline(1.5, color='#d90429', linestyle='--', linewidth=1.8, label=r'Target $h \leq l_0/5 = 1.5\ \mu\mathrm{m}$')
    ax2.axvline(2.0, color='#0077b6', linestyle=':', linewidth=1.8, label=r'RemeshingRule Target (2.0%)')
    ax2.legend(loc='upper right', framealpha=0.92, fontsize=9.5)
    
    cbar2 = fig.colorbar(hb, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label('Element Count $\\log_{10}(N)$', fontsize=11, labelpad=8)
    
    plt.tight_layout()
    save_fig(fig, 'fig_method_a_miseseri_refinement_correlation', out_dirs)
    plt.close(fig)
    print("All 4 publication figures generated successfully!")

if __name__ == '__main__':
    main()
