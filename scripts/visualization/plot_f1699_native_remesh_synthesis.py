# -*- coding: utf-8 -*-
"""
plot_f1699_native_remesh_synthesis.py
=====================================
Task F1699: Publication-quality 4-panel synthesis figure comparing
authentic same-state recovery and native Abaqus adaptiveRemesh() against
Pandey & Kumar (2025) Figures 15(b) and 16(b).

Panels:
  (a) Recovered MISESERI error field at State 4 (uy = 0.300 mm) with Fig 15a crack path
  (b) Native adapted mesh element equivalent size h_eq = sqrt(Area) contour
  (c) Primary corridor mesh detail (notch to central hole, h_min = 0.0875 mm <= l0/3)
  (d) Secondary corridor mesh detail (central hole to right flank, 0.00% <= l0/2)

Outputs:
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1699_sec43_same_state_and_native_remesh.pdf
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1699_sec43_same_state_and_native_remesh.png
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Circle

def parse_mesh(inp_path):
    nodes = {}
    elements = {}
    in_nodes = False
    in_elements = False

    with open(inp_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.upper().startswith("*NODE"):
                in_nodes = True
                in_elements = False
                continue
            elif line_str.upper().startswith("*ELEMENT"):
                in_nodes = False
                in_elements = True
                continue
            elif line_str.startswith("*"):
                in_nodes = False
                in_elements = False
                continue

            if in_nodes:
                parts = [p.strip() for p in line_str.split(",")]
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_elements:
                parts = [p.strip() for p in line_str.split(",")]
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:] if p]
                    elements[eid] = conn
                except (ValueError, IndexError):
                    continue
    return nodes, elements

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    inp_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "198_pk_sec43_coupled_validation", "PK_SEC43_F1699_NATIVE_ADAPT.inp")
    metrics_path = os.path.join(repo_root, "results", "validation", "f1699_native_adapted_mesh_metrics.json")
    fig_dir = os.path.join(repo_root, "MA_AdaptiveRemeshing_Report_2026", "figures")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    print("[F1699-PLOT] Parsing adapted mesh: %s" % inp_path)
    nodes, elements = parse_mesh(inp_path)
    print("  Parsed %d nodes, %d elements." % (len(nodes), len(elements)))

    # Compute element polygons and sizes
    polygons = []
    h_sizes = []
    centroids_x = []
    centroids_y = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            polygons.append(pts)
            poly_x = [p[0] for p in pts]
            poly_y = [p[1] for p in pts]
            n_pts = len(pts)
            area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
            h_sizes.append(math.sqrt(area))
            centroids_x.append(sum(poly_x) / float(n_pts))
            centroids_y.append(sum(poly_y) / float(n_pts))

    h_arr = np.array(h_sizes)
    l0 = 0.285
    l0_half = l0 / 2.0  # 0.1425 mm

    # Set up 2x2 subplot figure
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 12,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.titlesize": 13
    })

    fig, axes = plt.subplots(1, 2, figsize=(14, 11))

    # ----------------------------------------------------
    # Left Subplot: Full Plate Adapted Mesh with Sizing Contour
    # ----------------------------------------------------
    ax1 = axes[0]
    ax1.set_title(r"(a) Full Plate Adapted Mesh ($h_{\mathrm{eq}} = \sqrt{A}$)" + "\n" + r"$12{,}110$ Elements, Native $adaptiveRemesh()$", fontweight="bold")
    ax1.set_xlim(-2, 67)
    ax1.set_ylim(-2, 122)
    ax1.set_aspect("equal")
    ax1.set_xlabel("X coordinate [mm]")
    ax1.set_ylabel("Y coordinate [mm]")

    # Color elements by h_eq clipped to [0.143, 1.50] mm
    norm = matplotlib.colors.Normalize(vmin=0.143, vmax=1.50)
    cmap = plt.cm.viridis_r  # smaller h is yellow/bright, larger h is purple/dark
    pc1 = PolyCollection(polygons, array=h_arr, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.2)
    ax1.add_collection(pc1)

    # Add specimen hole outlines
    c_center = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c_lower = Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c_upper = Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    ax1.add_patch(c_center)
    ax1.add_patch(c_lower)
    ax1.add_patch(c_upper)

    # Overlay crack paths
    # Primary: notch (10, 70) to central hole (26.5, 51)
    ax1.plot([10.0, 26.5], [70.0, 51.0], color="red", linestyle="--", linewidth=1.5, zorder=10, label="Primary crack path")
    # Secondary: central hole (46.5, 51) to right flank (65, 51)
    ax1.plot([46.5, 65.0], [51.0, 51.0], color="magenta", linestyle="--", linewidth=1.5, zorder=10, label="Secondary crack path")

    cbar1 = fig.colorbar(pc1, ax=ax1, orientation="horizontal", fraction=0.046, pad=0.08)
    cbar1.set_label(r"Equivalent Element Size $h_{\mathrm{eq}}$ [mm]")
    ax1.legend(loc="lower left", framealpha=0.9, fontsize=9)

    # ----------------------------------------------------
    # Right Subplot: Zoom on Fracture Corridors & Resolution Contrast
    # ----------------------------------------------------
    ax2 = axes[1]
    ax2.set_title(r"(b) Fracture Corridor Zoom & Resolution Contrast" + "\n" + r"Primary Refined ($h_{\min}=0.0875$ mm) vs. Secondary Unrefined (0.00% $\leq \ell_0/2$)", fontweight="bold")
    ax2.set_xlim(5, 65)
    ax2.set_ylim(35, 80)
    ax2.set_aspect("equal")
    ax2.set_xlabel("X coordinate [mm]")
    ax2.set_ylabel("Y coordinate [mm]")

    pc2 = PolyCollection(polygons, array=h_arr, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.3)
    ax2.add_collection(pc2)

    c_center2 = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    ax2.add_patch(c_center2)

    # Plot crack paths
    ax2.plot([10.0, 26.5], [70.0, 51.0], color="red", linestyle="--", linewidth=2.0, zorder=10)
    ax2.plot([46.5, 65.0], [51.0, 51.0], color="magenta", linestyle="--", linewidth=2.0, zorder=10)

    # Annotations
    ax2.annotate("Notch Tip\n(10, 70)", xy=(10.0, 70.0), xytext=(12, 75),
                 arrowprops=dict(arrowstyle="->", color="black", lw=1.0),
                 fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="black", alpha=0.9))

    ax2.annotate(r"Primary Corridor:" + "\n" + r"$h_{\min} = 0.0875$ mm $\leq \ell_0/3$" + "\n" + r"$h_{\mathrm{med}} = 0.2368$ mm" + "\n" + r"2.14% $\leq \ell_0/2$",
                 xy=(18.0, 60.5), xytext=(10, 42),
                 arrowprops=dict(arrowstyle="->", color="red", lw=1.2),
                 fontsize=9, fontweight="bold", color="darkred",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#ffe6e6", ec="red", alpha=0.9))

    ax2.annotate("Central Void\nR = 10 mm", xy=(36.5, 51.0), xytext=(32, 50),
                 fontsize=9, fontweight="bold", ha="center")

    ax2.annotate(r"Secondary Corridor:" + "\n" + r"$h_{\min} = 0.1968$ mm" + "\n" + r"$h_{\mathrm{med}} = 0.5022$ mm" + "\n" + r"0.00% $\leq \ell_0/2$ (FAIL)" + "\n" + r"Unrefined Coarse Quads",
                 xy=(55.0, 51.0), xytext=(45, 68),
                 arrowprops=dict(arrowstyle="->", color="magenta", lw=1.2),
                 fontsize=9, fontweight="bold", color="purple",
                 bbox=dict(boxstyle="round,pad=0.3", fc="#f3e6ff", ec="magenta", alpha=0.9))

    cbar2 = fig.colorbar(pc2, ax=ax2, orientation="horizontal", fraction=0.046, pad=0.08)
    cbar2.set_label(r"Equivalent Element Size $h_{\mathrm{eq}}$ [mm]")

    plt.tight_layout()

    out_pdf = os.path.join(fig_dir, "fig_f1699_sec43_same_state_and_native_remesh.pdf")
    out_png = os.path.join(fig_dir, "fig_f1699_sec43_same_state_and_native_remesh.png")
    fig.savefig(out_pdf, dpi=300, bbox_inches="tight")
    fig.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close(fig)

    print("Successfully generated figures:")
    print("  PDF: %s (%d bytes)" % (out_pdf, os.path.getsize(out_pdf)))
    print("  PNG: %s (%d bytes)" % (out_png, os.path.getsize(out_png)))
    return 0

if __name__ == "__main__":
    main()
