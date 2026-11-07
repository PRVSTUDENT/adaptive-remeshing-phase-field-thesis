# -*- coding: utf-8 -*-
"""Generate publication-quality mesh visualization figures for Method A off-axis hole benchmark.

Reads authentic Abaqus input decks:
    Original mesh: PK_HOLE_METHOD_A_PROD_PHYS.inp (46,747 physical elements)
    Adapted mesh:  PK_HOLE_METHOD_A_ADAPT_PHYS.inp (52,447 physical elements)

Generates:
    1. Full 1x1 mm plate adapted finite element mesh.
    2. Zoomed mesh around notch tip, ligament, and off-axis hole.
    3. Side-by-side comparison of original 46k vs adapted 52k mesh.

Saves 300 DPI PNG and vector PDF in thesis figures directories.
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

def parse_inp_mesh(path):
    """Parse nodes and elements from Abaqus .inp file."""
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

def compute_element_areas(nodes, elements):
    """Compute element area and equivalent size h = sqrt(A) in micrometers."""
    areas = []
    polys = []
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) < 3:
            continue
        polys.append(coords)
        # Shoelace formula for polygon area
        x = [c[0] for c in coords]
        y = [c[1] for c in coords]
        a = 0.5 * abs(sum(x[i]*y[i+1] - x[i+1]*y[i] for i in range(len(coords)-1)) + (x[-1]*y[0] - x[0]*y[-1]))
        areas.append(a)
    h_um = np.sqrt(np.array(areas)) * 1000.0  # mm -> um
    return polys, h_um

def plot_full_adapted_mesh(nodes_adapt, elems_adapt, out_png, out_pdf):
    """Figure 1: Full 1x1 mm plate showing initial notch, circular hole and adapted finite-element mesh."""
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=300)

    polys, h_um = compute_element_areas(nodes_adapt, elems_adapt)

    # Use color mapping for element size
    # Cap color range between 1.0 um and 20.0 um
    norm = matplotlib.colors.LogNorm(vmin=1.0, vmax=25.0)
    cmap = plt.cm.viridis_r

    pc = PolyCollection(polys, cmap=cmap, norm=norm, edgecolors='#1a1a1a', linewidths=0.12)
    pc.set_array(h_um)
    ax.add_collection(pc)

    # Notch line: x in [0, 0.5], y = 0.5
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.2, label='Initial notch ($a_0 = 0.5\\,\\mathrm{mm}$)')
    ax.scatter([0.5], [0.5], color='#d90429', s=45, zorder=5, label='Notch tip $(0.5, 0.5)$')

    # Hole outline
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4, label='Off-axis hole ($R = 0.10\\,\\mathrm{mm}$)')
    ax.add_patch(hole)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=50, zorder=5)

    # Zoom window boundary indicator
    zoom_rect = Rectangle((0.44, 0.44), 0.38, 0.38, linewidth=1.8, edgecolor='#0077b6', facecolor='none', linestyle=':', zorder=6, label='Refined FPZ window')
    ax.add_patch(zoom_rect)

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel('$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title('Method A Indicator-Adapted Discretization ($N = 52,447$ elements)', fontsize=13, fontweight='bold', pad=10)

    # Colorbar
    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

    ax.legend(loc='lower left', framealpha=0.92, fontsize=9.5, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.4, color='#888888')

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf, format='pdf')
    plt.close(fig)
    print(f"Full adapted mesh saved: {out_png} and {out_pdf}")

def plot_zoomed_adapted_mesh(nodes_adapt, elems_adapt, out_png, out_pdf):
    """Figure 2: Zoomed mesh around notch tip, ligament and off-axis hole showing refinement and grading."""
    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=300)

    polys, h_um = compute_element_areas(nodes_adapt, elems_adapt)

    # Filter polygons to zoomed region for clean rendering
    zoom_xmin, zoom_xmax = 0.44, 0.82
    zoom_ymin, zoom_ymax = 0.44, 0.82

    zoomed_polys = []
    zoomed_h = []
    for p, h in zip(polys, h_um):
        cx = sum(pt[0] for pt in p) / len(p)
        cy = sum(pt[1] for pt in p) / len(p)
        if zoom_xmin - 0.02 <= cx <= zoom_xmax + 0.02 and zoom_ymin - 0.02 <= cy <= zoom_ymax + 0.02:
            zoomed_polys.append(p)
            zoomed_h.append(h)

    norm = matplotlib.colors.LogNorm(vmin=0.8, vmax=10.0)
    cmap = plt.cm.viridis_r

    pc = PolyCollection(zoomed_polys, cmap=cmap, norm=norm, edgecolors='#222222', linewidths=0.25)
    pc.set_array(np.array(zoomed_h))
    ax.add_collection(pc)

    # Notch line and tip
    ax.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.8, zorder=5)
    ax.scatter([0.5], [0.5], color='#d90429', s=70, zorder=6, label='Notch tip $(0.5, 0.5)$')

    # Hole
    hole = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.5, linestyle='--', zorder=4, label='Hole boundary ($R = 0.10\\,\\mathrm{mm}$)')
    ax.add_patch(hole)
    ax.scatter([0.65], [0.65], color='#d90429', marker='+', s=80, zorder=6, label='Hole center $(0.65, 0.65)$')

    # Annotations for mesh tiers
    ax.annotate('Core FPZ ($h \\approx 1.0\\,\\mu\\mathrm{m}$)', xy=(0.53, 0.52), xytext=(0.46, 0.57),
                arrowprops=dict(facecolor='#111111', shrink=0.08, width=1.0, headwidth=5),
                fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85))

    ax.annotate('Ligament corridor', xy=(0.58, 0.58), xytext=(0.47, 0.66),
                arrowprops=dict(facecolor='#111111', shrink=0.08, width=1.0, headwidth=5),
                fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85))

    ax.annotate('Boundary refinement', xy=(0.65, 0.75), xytext=(0.60, 0.80),
                arrowprops=dict(facecolor='#111111', shrink=0.08, width=1.0, headwidth=5),
                fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.85))

    ax.set_xlim(zoom_xmin, zoom_xmax)
    ax.set_ylim(zoom_ymin, zoom_ymax)
    ax.set_aspect('equal')
    ax.set_xlabel('$x$ [mm]', fontsize=12, labelpad=6)
    ax.set_ylabel('$y$ [mm]', fontsize=12, labelpad=6)
    ax.set_title('Zoomed Fracture-Process Zone Discretization & Mesh Grading', fontsize=13, fontweight='bold', pad=10)

    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

    ax.legend(loc='lower right', framealpha=0.92, fontsize=9.5, edgecolor='#cccccc')
    ax.grid(True, linestyle=':', alpha=0.3, color='#888888')

    plt.tight_layout()
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf, format='pdf')
    plt.close(fig)
    print(f"Zoomed adapted mesh saved: {out_png} and {out_pdf}")

def plot_mesh_comparison_side_by_side(nodes_orig, elems_orig, nodes_adapt, elems_adapt, out_png, out_pdf):
    """Figure 3: Side-by-side original 46,747-element mesh vs adapted 52,447-element mesh."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.8), dpi=300)

    # Compute areas
    polys_orig, h_orig = compute_element_areas(nodes_orig, elems_orig)
    polys_adapt, h_adapt = compute_element_areas(nodes_adapt, elems_adapt)

    # Zoom window for detailed comparison
    zoom_xmin, zoom_xmax = 0.44, 0.82
    zoom_ymin, zoom_ymax = 0.44, 0.82

    # Filter
    polys1, h1 = [], []
    for p, h in zip(polys_orig, h_orig):
        cx = sum(pt[0] for pt in p) / len(p)
        cy = sum(pt[1] for pt in p) / len(p)
        if zoom_xmin - 0.02 <= cx <= zoom_xmax + 0.02 and zoom_ymin - 0.02 <= cy <= zoom_ymax + 0.02:
            polys1.append(p)
            h1.append(h)

    polys2, h2 = [], []
    for p, h in zip(polys_adapt, h_adapt):
        cx = sum(pt[0] for pt in p) / len(p)
        cy = sum(pt[1] for pt in p) / len(p)
        if zoom_xmin - 0.02 <= cx <= zoom_xmax + 0.02 and zoom_ymin - 0.02 <= cy <= zoom_ymax + 0.02:
            polys2.append(p)
            h2.append(h)

    norm = matplotlib.colors.LogNorm(vmin=0.8, vmax=15.0)
    cmap = plt.cm.viridis_r

    # Left: Original 46k mesh
    pc1 = PolyCollection(polys1, cmap=cmap, norm=norm, edgecolors='#222222', linewidths=0.25)
    pc1.set_array(np.array(h1))
    ax1.add_collection(pc1)

    ax1.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.5, zorder=5)
    ax1.scatter([0.5], [0.5], color='#d90429', s=60, zorder=6)
    hole1 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax1.add_patch(hole1)
    ax1.scatter([0.65], [0.65], color='#d90429', marker='+', s=60, zorder=6)

    ax1.set_xlim(zoom_xmin, zoom_xmax)
    ax1.set_ylim(zoom_ymin, zoom_ymax)
    ax1.set_aspect('equal')
    ax1.set_xlabel('$x$ [mm]', fontsize=11, labelpad=5)
    ax1.set_ylabel('$y$ [mm]', fontsize=11, labelpad=5)
    ax1.set_title('(a) Original Discretization\n$N = 46,747$ elements ($h_{\\mathrm{tip}} \\approx 3.5\\,\\mu\\mathrm{m}$)', fontsize=12, fontweight='bold', pad=8)
    ax1.grid(True, linestyle=':', alpha=0.3, color='#888888')

    # Right: Adapted 52k mesh
    pc2 = PolyCollection(polys2, cmap=cmap, norm=norm, edgecolors='#222222', linewidths=0.25)
    pc2.set_array(np.array(h2))
    ax2.add_collection(pc2)

    ax2.plot([0.44, 0.5], [0.5, 0.5], color='#d90429', linewidth=2.5, zorder=5)
    ax2.scatter([0.5], [0.5], color='#d90429', s=60, zorder=6)
    hole2 = Circle((0.65, 0.65), 0.10, edgecolor='#d90429', facecolor='white', linewidth=2.0, linestyle='--', zorder=4)
    ax2.add_patch(hole2)
    ax2.scatter([0.65], [0.65], color='#d90429', marker='+', s=60, zorder=6)

    ax2.set_xlim(zoom_xmin, zoom_xmax)
    ax2.set_ylim(zoom_ymin, zoom_ymax)
    ax2.set_aspect('equal')
    ax2.set_xlabel('$x$ [mm]', fontsize=11, labelpad=5)
    ax2.set_ylabel('$y$ [mm]', fontsize=11, labelpad=5)
    ax2.set_title('(b) Indicator-Adapted Discretization\n$N = 52,447$ elements ($h_{\\mathrm{tip}} \\approx 1.17\\,\\mu\\mathrm{m}$, $+66.6\\%$ resolution)', fontsize=12, fontweight='bold', pad=8)
    ax2.grid(True, linestyle=':', alpha=0.3, color='#888888')

    # Common colorbar
    fig.subplots_adjust(right=0.88)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.02, 0.70])
    cbar = fig.colorbar(pc2, cax=cbar_ax)
    cbar.set_label('Equivalent element size $h = \\sqrt{A}$ [$\\mu\\mathrm{m}$]', fontsize=11, labelpad=8)
    cbar.ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.1f'))

    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.close(fig)
    print(f"Side-by-side comparison saved: {out_png} and {out_pdf}")

if __name__ == '__main__':
    orig_inp = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PROD_PHYS.inp'
    adapt_inp = 'models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_ADAPT_PHYS.inp'

    out_dirs = [
        'MA_AdaptiveRemeshing_Report_2026/figures',
        'docs/MA_AdaptiveRemeshing_Report_2026_main/figures'
    ]

    print("Parsing original mesh...")
    nodes_orig, elems_orig = parse_inp_mesh(orig_inp)
    print(f"Original: {len(nodes_orig)} nodes, {len(elems_orig)} elements")

    print("Parsing adapted mesh...")
    nodes_adapt, elems_adapt = parse_inp_mesh(adapt_inp)
    print(f"Adapted: {len(nodes_adapt)} nodes, {len(elems_adapt)} elements")

    for d in out_dirs:
        os.makedirs(d, exist_ok=True)
        print(f"\n--- Generating figures for: {d} ---")
        plot_full_adapted_mesh(
            nodes_adapt, elems_adapt,
            os.path.join(d, 'fig_method_a_hole_adapted_mesh_full.png'),
            os.path.join(d, 'fig_method_a_hole_adapted_mesh_full.pdf')
        )
        plot_zoomed_adapted_mesh(
            nodes_adapt, elems_adapt,
            os.path.join(d, 'fig_method_a_hole_adapted_mesh_zoom.png'),
            os.path.join(d, 'fig_method_a_hole_adapted_mesh_zoom.pdf')
        )
        plot_mesh_comparison_side_by_side(
            nodes_orig, elems_orig, nodes_adapt, elems_adapt,
            os.path.join(d, 'fig_method_a_hole_mesh_comparison.png'),
            os.path.join(d, 'fig_method_a_hole_mesh_comparison.pdf')
        )

    print("\nAll publication mesh figures generated successfully.")
