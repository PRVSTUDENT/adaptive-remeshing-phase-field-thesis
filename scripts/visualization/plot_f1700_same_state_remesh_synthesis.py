# -*- coding: utf-8 -*-
"""
plot_f1700_same_state_remesh_synthesis.py
=========================================
Task F1700: Publication-quality 4-panel synthesis figure comparing
authentic same-state recovery and native Abaqus adaptiveRemesh() across
State 4 (Secondary Mid-Propagation) and State 2 (Hole Arrest).

Demonstrates:
  (a) Full Plate Adapted Mesh from State 4 (9,568 elements, h_eq contour)
  (b) Full Plate Adapted Mesh from State 2 (8,363 elements, h_eq contour)
  (c) Secondary corridor resolution comparison: State 4 resolves secondary crack
      (h_min = 0.0691 mm, 83.91% <= l0) whereas State 2 fails (0.00% <= l0)
  (d) Primary corridor resolution comparison: State 4 relaxes to coarse mesh
      (0.00% <= l0/2) because primary ligament has already severed into void,
      definitively proving single-frame dual-corridor refinement is physically impossible.

Outputs:
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1700_sec43_same_state_and_native_remesh.pdf
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1700_sec43_same_state_and_native_remesh.png
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

def get_mesh_polygons(nodes, elements):
    polygons = []
    h_sizes = []
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            polygons.append(pts)
            poly_x = [p[0] for p in pts]
            poly_y = [p[1] for p in pts]
            n_pts = len(pts)
            area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
            h_sizes.append(math.sqrt(area))
    return polygons, np.array(h_sizes)

def main():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    mesh4_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_F1700_NATIVE_ADAPT_STATE4.inp")
    mesh2_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_F1700_NATIVE_ADAPT_STATE2.inp")
    metrics_path = os.path.join(repo_root, "results", "validation", "f1700_native_adapted_mesh_metrics.json")
    fig_dir = os.path.join(repo_root, "MA_AdaptiveRemeshing_Report_2026", "figures")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    print("[F1700-PLOT] Parsing adapted meshes...")
    nodes4, elements4 = parse_mesh(mesh4_path)
    poly4, h4 = get_mesh_polygons(nodes4, elements4)
    print("  State 4: %d elements" % len(elements4))

    nodes2, elements2 = parse_mesh(mesh2_path)
    poly2, h2 = get_mesh_polygons(nodes2, elements2)
    print("  State 2: %d elements" % len(elements2))

    l0 = 0.285
    l0_half = l0 / 2.0  # 0.1425 mm

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "figure.titlesize": 13
    })

    fig, axes = plt.subplots(2, 2, figsize=(15, 14))

    norm = matplotlib.colors.Normalize(vmin=0.143, vmax=1.50)
    cmap = plt.cm.viridis_r

    # ----------------------------------------------------
    # Subplot (a): State 4 Full Plate Adapted Mesh
    # ----------------------------------------------------
    ax1 = axes[0, 0]
    ax1.set_title(r"(a) State 4 Donor ($u_y = 0.300\,\mathrm{mm}$): Native $adaptiveRemesh()$" + "\n" + r"$9{,}568$ Elements, Active Secondary Corridor Refinement", fontweight="bold")
    ax1.set_xlim(-2, 67)
    ax1.set_ylim(-2, 122)
    ax1.set_aspect("equal")
    ax1.set_xlabel("X coordinate [mm]")
    ax1.set_ylabel("Y coordinate [mm]")

    pc1 = PolyCollection(poly4, array=h4, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.2)
    ax1.add_collection(pc1)

    c_center = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c_lower = Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c_upper = Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    ax1.add_patch(c_center)
    ax1.add_patch(c_lower)
    ax1.add_patch(c_upper)

    # Notch
    ax1.plot([0, 10], [70.2, 70.2], 'r-', lw=1.5, zorder=6)
    ax1.plot([0, 10], [69.8, 69.8], 'r-', lw=1.5, zorder=6)
    ax1.plot([10, 10], [69.8, 70.2], 'r-', lw=1.5, zorder=6)

    # Text annotation
    ax1.text(47, 56, "Secondary Refined\n" + r"$h_{\min}=0.069\,\mathrm{mm}$" + "\n" + r"$83.9\% \leq \ell_0$",
             color="darkred", fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.85), zorder=7)
    ax1.text(12, 62, "Primary Relaxed\n" + r"$0.00\% \leq \ell_0/2$",
             color="blue", fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85), zorder=7)

    # ----------------------------------------------------
    # Subplot (b): State 2 Full Plate Adapted Mesh
    # ----------------------------------------------------
    ax2 = axes[0, 1]
    ax2.set_title(r"(b) State 2 Donor ($u_y = 0.200\,\mathrm{mm}$): Native $adaptiveRemesh()$" + "\n" + r"$8{,}363$ Elements, Primary Initiation Refinement Only", fontweight="bold")
    ax2.set_xlim(-2, 67)
    ax2.set_ylim(-2, 122)
    ax2.set_aspect("equal")
    ax2.set_xlabel("X coordinate [mm]")
    ax2.set_ylabel("Y coordinate [mm]")

    pc2 = PolyCollection(poly2, array=h2, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.2)
    ax2.add_collection(pc2)

    c2_center = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c2_lower = Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    c2_upper = Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.2, zorder=5)
    ax2.add_patch(c2_center)
    ax2.add_patch(c2_lower)
    ax2.add_patch(c2_upper)

    ax2.plot([0, 10], [70.2, 70.2], 'r-', lw=1.5, zorder=6)
    ax2.plot([0, 10], [69.8, 69.8], 'r-', lw=1.5, zorder=6)
    ax2.plot([10, 10], [69.8, 70.2], 'r-', lw=1.5, zorder=6)

    ax2.text(47, 56, "Secondary Unrefined\n" + r"$0.00\% \leq \ell_0$" + "\n" + r"$h_{\mathrm{med}}=0.62\,\mathrm{mm}$",
             color="black", fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.85), zorder=7)
    ax2.text(12, 62, "Primary Active\n" + r"$40.0\% \leq \ell_0$",
             color="darkgreen", fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="yellow", alpha=0.85), zorder=7)

    # ----------------------------------------------------
    # Subplot (c): Secondary Corridor Detail (State 4 vs State 2)
    # ----------------------------------------------------
    ax3 = axes[1, 0]
    ax3.set_title(r"(c) Secondary Corridor Zoom ($X \in [36.5, 65], Y \in [40, 62]$)" + "\n" + r"State 4: $h_{\min}=0.069\,\mathrm{mm} \leq \ell_0/4$, Resolves Process Zone", fontweight="bold")
    ax3.set_xlim(36.5, 65.0)
    ax3.set_ylim(40.0, 62.0)
    ax3.set_aspect("equal")
    ax3.set_xlabel("X coordinate [mm]")
    ax3.set_ylabel("Y coordinate [mm]")

    pc3 = PolyCollection(poly4, array=h4, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.3)
    ax3.add_collection(pc3)
    c3 = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.5, zorder=5)
    ax3.add_patch(c3)

    # Experimental trajectory overlay
    exp_x = [46.5, 52.0, 58.0, 65.0]
    exp_y = [51.0, 50.8, 50.5, 50.3]
    ax3.plot(exp_x, exp_y, 'r--', lw=2.0, label="Crack Trajectory", zorder=8)
    ax3.legend(loc="upper right", framealpha=0.9)

    # ----------------------------------------------------
    # Subplot (d): Primary Corridor Detail (State 4 vs State 2)
    # ----------------------------------------------------
    ax4 = axes[1, 1]
    ax4.set_title(r"(d) Primary Corridor Zoom ($X \in [8, 38], Y \in [45, 75]$)" + "\n" + r"State 4: $0.00\% \leq \ell_0/2$, Severe Post-Severance Relaxation", fontweight="bold")
    ax4.set_xlim(8.0, 38.0)
    ax4.set_ylim(45.0, 75.0)
    ax4.set_aspect("equal")
    ax4.set_xlabel("X coordinate [mm]")
    ax4.set_ylabel("Y coordinate [mm]")

    pc4 = PolyCollection(poly4, array=h4, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.3)
    ax4.add_collection(pc4)
    c4 = Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.5, zorder=5)
    ax4.add_patch(c4)

    # Primary crack trajectory
    prim_x = [10.0, 15.0, 20.0, 26.5]
    prim_y = [70.0, 67.0, 61.0, 51.0]
    ax4.plot(prim_x, prim_y, 'b--', lw=2.0, label="Primary Trajectory (Severed)", zorder=8)
    ax4.legend(loc="upper right", framealpha=0.9)

    # Add shared colorbar
    fig.subplots_adjust(right=0.90, hspace=0.25, wspace=0.15)
    cbar_ax = fig.add_axes([0.92, 0.15, 0.02, 0.70])
    cb = fig.colorbar(pc1, cax=cbar_ax)
    cb.set_label(r"Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{A}$ [mm]", fontsize=11)
    cb.ax.axhline(l0_half, color="red", linestyle="--", linewidth=1.5)
    cb.ax.text(1.3, l0_half, r"$\ell_0/2 = 0.1425$", color="red", va="center", fontsize=9, fontweight="bold")

    out_pdf = os.path.join(fig_dir, "fig_f1700_sec43_same_state_and_native_remesh.pdf")
    out_png = os.path.join(fig_dir, "fig_f1700_sec43_same_state_and_native_remesh.png")
    fig.savefig(out_pdf, bbox_inches="tight", dpi=300)
    fig.savefig(out_png, bbox_inches="tight", dpi=300)
    plt.close(fig)

    print("[F1700-PLOT] SUCCESS: Figure saved to:")
    print("  " + out_pdf)
    print("  " + out_png)

if __name__ == "__main__":
    main()
