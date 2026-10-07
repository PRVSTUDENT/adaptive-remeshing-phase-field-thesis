#!/usr/bin/env python3
"""
Publication-Grade Mode-II ET2 Adaptive Mesh Topology Exporter
-------------------------------------------------------------
Generates publication-quality figures showing the actual element edges /
mesh lines for the corrected Mode-II native adaptive remeshed mesh:
  - Discretization: errorTarget = 2.0% (ET2)
  - Element count: 21,496 finite elements (20,934 CPE4 + 562 CPE3)
  - Node count: 21,615 nodes
  - Source deck: models/pandey_kumar_mode2/04_adaptive_miseseri/JOB_MODE2_ADAPTIVE_ET2.inp

Figures exported:
  1. Full-domain actual mesh topology (mesh lines, no centroid scatter, no colormap)
  2. Zoomed crack-corridor mesh topology (actual mesh lines, notch tip to bottom boundary)
  3. Side-by-side comparison figure with digitized Pandey & Kumar (2025) Fig. 12(b)

Output directory: results/figures/mode2/
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from PIL import Image

def parse_inp_mesh(inp_path):
    """Parse node coordinates and unique element boundary edges from Abaqus .inp."""
    nodes = {}
    edges = set()
    cpe3_count = 0
    cpe4_count = 0
    mode = None

    with open(inp_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            if line.startswith('*'):
                mode = None
                l_lower = line.lower()
                if l_lower.startswith('*node'):
                    mode = 'node'
                elif 'type=cpe3' in l_lower:
                    mode = 'cpe3'
                elif 'type=cpe4' in l_lower:
                    mode = 'cpe4'
                continue

            if mode == 'node':
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
            elif mode == 'cpe3':
                parts = [int(p.strip()) for p in line.split(',')]
                n1, n2, n3 = parts[1], parts[2], parts[3]
                edges.add((min(n1, n2), max(n1, n2)))
                edges.add((min(n2, n3), max(n2, n3)))
                edges.add((min(n3, n1), max(n3, n1)))
                cpe3_count += 1
            elif mode == 'cpe4':
                parts = [int(p.strip()) for p in line.split(',')]
                n1, n2, n3, n4 = parts[1], parts[2], parts[3], parts[4]
                edges.add((min(n1, n2), max(n1, n2)))
                edges.add((min(n2, n3), max(n2, n3)))
                edges.add((min(n3, n4), max(n3, n4)))
                edges.add((min(n4, n1), max(n4, n1)))
                cpe4_count += 1

    total_elements = cpe3_count + cpe4_count
    segments = []
    for u, v in edges:
        if u in nodes and v in nodes:
            segments.append([nodes[u], nodes[v]])

    return nodes, segments, total_elements, cpe3_count, cpe4_count


def generate_figures():
    # Paths
    base_dir = r"D:\Master thesis\Adaptive remeshing"
    inp_path = os.path.join(base_dir, "models", "pandey_kumar_mode2", "04_adaptive_miseseri", "JOB_MODE2_ADAPTIVE_ET2.inp")
    out_dir = os.path.join(base_dir, "results", "figures", "mode2")
    os.makedirs(out_dir, exist_ok=True)

    raw_crop_path = r"C:\Users\pruth\.gemini\antigravity-cli\brain\589fb9ef-11f4-491a-bddb-4006c64021b7\paper_fig12b_mesh_crop.png"

    print("Parsing input deck:", inp_path)
    nodes, segments, total_elements, cpe3_count, cpe4_count = parse_inp_mesh(inp_path)
    print(f"Loaded {len(nodes):,} nodes, {total_elements:,} elements ({cpe4_count:,} CPE4, {cpe3_count:,} CPE3)")
    print(f"Generated {len(segments):,} unique edge segments")

    # Matplotlib styling for high-quality publication
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.labelsize'] = 11
    plt.rcParams['axes.titlesize'] = 12
    plt.rcParams['figure.titlesize'] = 13

    # =========================================================================
    # FIGURE 1: Full-domain mesh topology
    # =========================================================================
    print("Generating Figure 1: Full-domain mesh topology...")
    fig, ax = plt.subplots(figsize=(7.5, 7.0), dpi=300)

    # LineCollection of actual element edges
    lc = LineCollection(segments, linewidths=0.25, colors='#1e293b', antialiased=True)
    ax.add_collection(lc)

    # Draw domain boundary box [0, 1] x [0, 1]
    ax.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color='#0f172a', linewidth=1.5, zorder=5)

    # Pre-existing crack seam (notch): from (0, 0.5) to (0.5, 0.5)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linewidth=2.5, solid_capstyle='round', zorder=6,
            label='Pre-existing crack seam ($a_0 = 0.5$ mm)')
    ax.plot(0.5, 0.5, marker='o', markersize=6, color='#dc2626', markeredgecolor='white', markeredgewidth=1.2, zorder=7,
            label='Initial crack tip (0.50, 0.50)')

    # Labels and formatting
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('Spatial coordinate $x$ [mm]')
    ax.set_ylabel('Spatial coordinate $y$ [mm]')
    ax.set_title('Mode-II Native Adaptive Remeshing Topology\n(ET2: 21,496 Finite Elements, 21,615 Nodes)', pad=12, fontweight='bold')

    # Information box
    info_text = (
        "Case: Mode-II Pure Shear Benchmark\n"
        "Adaptive Rule: errorTarget = 2.0% (ET2)\n"
        "Finite Elements: 21,496 (20,934 CPE4 + 562 CPE3)\n"
        "Min element size: $h_{\\min} \\approx 0.00076$ mm ($h_{\\min}/l_0 = 0.051$)\n"
        "Pandey & Kumar (2025) parity: +7.7% vs 19,963 FE"
    )
    ax.text(0.04, 0.18, info_text, transform=ax.transAxes, fontsize=8.5,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='#f8fafc', edgecolor='#cbd5e1', alpha=0.92),
            zorder=8)

    ax.legend(loc='upper left', framealpha=0.92, facecolor='#f8fafc', edgecolor='#cbd5e1')
    ax.grid(True, linestyle=':', alpha=0.4, color='#94a3b8')

    plt.tight_layout()
    fig1_png = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_fulldomain.png")
    fig1_pdf = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_fulldomain.pdf")
    fig.savefig(fig1_png, dpi=300)
    fig.savefig(fig1_pdf)
    plt.close(fig)
    print(f"Saved Figure 1: {fig1_png}")

    # =========================================================================
    # FIGURE 2: Zoomed crack-corridor mesh topology
    # =========================================================================
    print("Generating Figure 2: Zoomed crack-corridor mesh topology...")
    fig, ax = plt.subplots(figsize=(8.0, 7.0), dpi=300)

    # LineCollection of actual element edges (slightly bolder for zoom)
    lc_zoom = LineCollection(segments, linewidths=0.35, colors='#1e293b', antialiased=True)
    ax.add_collection(lc_zoom)

    # Pre-existing crack seam
    ax.plot([0.35, 0.5], [0.5, 0.5], color='#dc2626', linewidth=2.8, zorder=6,
            label='Pre-existing crack seam ($y = 0.5$ mm)')
    ax.plot(0.5, 0.5, marker='o', markersize=7, color='#dc2626', markeredgecolor='white', markeredgewidth=1.5, zorder=7,
            label='Crack tip $(x_0=0.50, y_0=0.50)$')

    # Literature reported corridor centerline from Pandey & Kumar Fig. 12(b)
    x_12b = np.array([0.500, 0.535, 0.585, 0.650, 0.725, 0.800, 0.868])
    y_12b = np.array([0.500, 0.430, 0.340, 0.235, 0.140, 0.060, 0.000])
    ax.plot(x_12b, y_12b, color='#2563eb', linestyle='--', linewidth=2.0, zorder=8,
            label=r'Pandey & Kumar Fig. 12(b) corridor ($\theta = -53.65^\circ$)')

    # Zoom window: captures crack tip and entire inclined corridor to bottom boundary
    ax.set_xlim(0.40, 0.98)
    ax.set_ylim(-0.02, 0.58)
    ax.set_aspect('equal')
    ax.set_xlabel('Spatial coordinate $x$ [mm]')
    ax.set_ylabel('Spatial coordinate $y$ [mm]')
    ax.set_title('Zoomed Mode-II Crack-Corridor Adaptive Mesh Topology\n(Actual Element Edges, ET2: 21,496 FE)', pad=12, fontweight='bold')

    # Annotation of corridor orientation and boundary exit
    ax.annotate(r'Refinement corridor exit' + '\n' + r'$x \approx 0.868$ mm at $y = 0$',
                xy=(0.868, 0.005), xytext=(0.68, 0.07),
                arrowprops=dict(facecolor='#0f172a', shrink=0.08, width=1.2, headwidth=6),
                fontsize=8.5, fontweight='semibold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8fafc', edgecolor='#cbd5e1'))

    ax.annotate('Dense refinement along\ninclined shear crack path',
                xy=(0.66, 0.28), xytext=(0.43, 0.20),
                arrowprops=dict(facecolor='#0f172a', shrink=0.08, width=1.2, headwidth=6),
                fontsize=8.5, fontweight='semibold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#f8fafc', edgecolor='#cbd5e1'))

    ax.legend(loc='upper right', framealpha=0.92, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=8.5)
    ax.grid(True, linestyle=':', alpha=0.4, color='#94a3b8')

    plt.tight_layout()
    fig2_png = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_corridor_zoom.png")
    fig2_pdf = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_corridor_zoom.pdf")
    fig.savefig(fig2_png, dpi=300)
    fig.savefig(fig2_pdf)
    plt.close(fig)
    print(f"Saved Figure 2: {fig2_png}")

    # =========================================================================
    # FIGURE 3: Side-by-Side Comparison with Pandey & Kumar Fig. 12(b)
    # =========================================================================
    if os.path.exists(raw_crop_path):
        print("Generating Figure 3: Side-by-side comparison with Fig. 12(b)...")
        im_raw = Image.open(raw_crop_path)
        w, h = im_raw.size
        # Clean crop to isolate the mesh area without label text on left or colorbar on right
        box = (int(w * 0.165), int(h * 0.02), int(w * 0.895), int(h * 0.98))
        im_clean = im_raw.crop(box)

        fig, (ax_ours, ax_paper) = plt.subplots(1, 2, figsize=(14.2, 6.8), dpi=300)

        # Left panel: Our full-domain ET2 mesh topology
        lc_comp = LineCollection(segments, linewidths=0.25, colors='#1e293b', antialiased=True)
        ax_ours.add_collection(lc_comp)
        ax_ours.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color='#0f172a', linewidth=1.5, zorder=5)
        ax_ours.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linewidth=2.5, zorder=6, label='Pre-existing crack seam ($a_0=0.5$ mm)')
        ax_ours.plot(0.5, 0.5, marker='o', markersize=6, color='#dc2626', markeredgecolor='white', markeredgewidth=1.2, zorder=7, label='Crack tip (0.50, 0.50)')
        ax_ours.plot(x_12b, y_12b, color='#2563eb', linestyle='--', linewidth=1.8, zorder=8, label=r'Literature corridor ($\theta=-53.65^\circ$)')

        ax_ours.set_xlim(-0.02, 1.02)
        ax_ours.set_ylim(-0.02, 1.02)
        ax_ours.set_aspect('equal')
        ax_ours.set_xlabel('Spatial coordinate $x$ [mm]')
        ax_ours.set_ylabel('Spatial coordinate $y$ [mm]')
        ax_ours.set_title('(a) Present Corrected Native Remeshed Mesh\n(ET2: 21,496 Finite Elements, $h_{\\min}=0.76\\,\\mu$m)', pad=10, fontweight='bold')
        ax_ours.legend(loc='upper left', framealpha=0.92, facecolor='#f8fafc', edgecolor='#cbd5e1', fontsize=8.5)
        ax_ours.grid(True, linestyle=':', alpha=0.4, color='#94a3b8')

        # Right panel: Digitized Pandey & Kumar (2025) Fig. 12(b)
        ax_paper.imshow(im_clean, extent=[0.0, 1.0, 0.0, 1.0])
        ax_paper.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], color='#0f172a', linewidth=1.5, zorder=5)
        ax_paper.set_xlim(-0.02, 1.02)
        ax_paper.set_ylim(-0.02, 1.02)
        ax_paper.set_aspect('equal')
        ax_paper.set_xlabel('Normalized coordinate $x$ [-]')
        ax_paper.set_ylabel('Normalized coordinate $y$ [-]')
        ax_paper.set_title('(b) Benchmark Literature Mesh: Pandey & Kumar (2025) Fig. 12(b)\n(Reported Adaptive Mesh: 19,963 Finite Elements)', pad=10, fontweight='bold')
        ax_paper.grid(True, linestyle=':', alpha=0.3, color='#94a3b8')

        plt.suptitle('Mode-II Adaptive Mesh Topology Parity: Present Work (21,496 FE) vs. Pandey & Kumar Fig. 12(b) (19,963 FE)',
                     fontsize=13, fontweight='bold', y=0.98)
        plt.tight_layout(rect=[0.02, 0.02, 0.98, 0.94])

        fig3_png = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_comparison_fig12b.png")
        fig3_pdf = os.path.join(out_dir, "fig_mode2_et2_mesh_topology_comparison_fig12b.pdf")
        fig.savefig(fig3_png, dpi=300)
        fig.savefig(fig3_pdf)
        plt.close(fig)
        print(f"Saved Figure 3: {fig3_png}")
    else:
        print("Warning: paper_fig12b_mesh_crop.png not found; skipping Figure 3.")

    print("All Mode-II ET2 mesh topology figures successfully generated!")

if __name__ == '__main__':
    generate_figures()
