# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1701_pointwise_and_history_aware_synthesis.py
========================================================================
Task F1701: Publication-quality 4-panel synthesis figure comparing
instantaneous single-frame native remeshing against the history-aware
dual-corridor adaptive remeshing framework.
"""

from __future__ import print_function
import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

def log(msg):
    print("[F1701-PLOT] " + str(msg))
    sys.stdout.flush()

def parse_mesh(inp_path):
    log("Reading " + str(inp_path) + "...")
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
                try:
                    parts = [p.strip() for p in line_str.split(",")]
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except (ValueError, IndexError):
                    continue
            elif in_elements:
                try:
                    parts = [p.strip() for p in line_str.split(",")]
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:] if p]
                    elements[eid] = conn
                except (ValueError, IndexError):
                    continue

    polys = []
    h_eqs = []
    centroids = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            poly_x = [pt[0] for pt in pts]
            poly_y = [pt[1] for pt in pts]
            n_pts = len(pts)
            area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
            h = math.sqrt(area)
            cx = sum(poly_x) / float(n_pts)
            cy = sum(poly_y) / float(n_pts)
            polys.append(pts)
            h_eqs.append(h)
            centroids.append((cx, cy))

    log("Parsed %d elements, %d polys" % (len(elements), len(polys)))
    return {
        "nodes": nodes,
        "elements": elements,
        "polys": polys,
        "h_eqs": np.array(h_eqs),
        "centroids": centroids
    }

def main():
    repo_root = r"D:\Master thesis\Adaptive remeshing"
    mesh_s4_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_F1700_NATIVE_ADAPT_STATE4.inp")
    mesh_hist_path = os.path.join(repo_root, "models", "pandey_kumar_mode1", "201_pk_sec43_pointwise_stress", "PK_SEC43_F1701_HISTORY_AWARE_ADAPT.inp")

    out_pdf = os.path.join(repo_root, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.pdf")
    out_png = os.path.join(repo_root, "MA_AdaptiveRemeshing_Report_2026", "figures", "fig_f1701_history_aware_remesh_synthesis.png")

    mesh_s4 = parse_mesh(mesh_s4_path)
    mesh_hist = parse_mesh(mesh_hist_path)

    log("Constructing 4-panel figure...")
    fig = plt.figure(figsize=(14, 11), dpi=300)

    cmap = plt.cm.viridis_r
    norm = matplotlib.colors.Normalize(vmin=0.07, vmax=1.20)

    # Panel (a): Single-Frame State 4 Mesh
    ax1 = fig.add_subplot(2, 2, 1)
    coll1 = PolyCollection(mesh_s4["polys"], array=mesh_s4["h_eqs"], cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
    ax1.add_collection(coll1)
    ax1.set_xlim(-2, 67)
    ax1.set_ylim(-2, 122)
    ax1.set_aspect("equal")
    ax1.set_title("(a) Single-Frame State 4 Adaptive Mesh (9,568 elements)\nSecondary Refined (h_min=0.069 mm); Primary Relaxed (0.00% <= l0/2)", fontsize=10, fontweight="bold")
    ax1.set_xlabel("x [mm]")
    ax1.set_ylabel("y [mm]")
    ax1.annotate("Arrested Void\n(Stress Relaxed,\nCoarse h > 0.4 mm)", xy=(18, 55), xytext=(2, 35),
                 arrowprops=dict(facecolor='red', shrink=0.05, width=1, headwidth=4), fontsize=8, color='red', fontweight='bold')
    ax1.annotate("Active Process Zone\n(Fine h_min=0.069 mm)", xy=(52, 51), xytext=(35, 25),
                 arrowprops=dict(facecolor='blue', shrink=0.05, width=1, headwidth=4), fontsize=8, color='blue', fontweight='bold')

    # Panel (b): History-Aware Adapted Mesh
    ax2 = fig.add_subplot(2, 2, 2)
    coll2 = PolyCollection(mesh_hist["polys"], array=mesh_hist["h_eqs"], cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
    ax2.add_collection(coll2)
    ax2.set_xlim(-2, 67)
    ax2.set_ylim(-2, 122)
    ax2.set_aspect("equal")
    ax2.set_title("(b) History-Aware Dual-Corridor Mesh (10,597 elements)\neta_hist = max(eta_1, eta_2) with coarseningFactor=NOT_ALLOWED", fontsize=10, fontweight="bold")
    ax2.set_xlabel("x [mm]")
    ax2.set_ylabel("y [mm]")
    ax2.annotate("Preserved Primary Wake\n(h <= l0/2, 47.3% <= l0)", xy=(18, 60), xytext=(2, 35),
                 arrowprops=dict(facecolor='green', shrink=0.05, width=1, headwidth=4), fontsize=8, color='green', fontweight='bold')
    ax2.annotate("Simultaneous Secondary\n(h_min=0.089 mm, 84.5% <= l0)", xy=(54, 51), xytext=(32, 25),
                 arrowprops=dict(facecolor='green', shrink=0.05, width=1, headwidth=4), fontsize=8, color='green', fontweight='bold')

    cbar = fig.colorbar(coll2, ax=[ax1, ax2], orientation="vertical", fraction=0.02, pad=0.04)
    cbar.set_label("Equivalent Element Size h_eq = sqrt(Area) [mm]", fontsize=9)

    # Panel (c): Primary Corridor Comparison (Zoomed Box)
    ax3 = fig.add_subplot(2, 2, 3)
    prim_polys_hist = [p for p in mesh_hist["polys"] if any(8 <= pt[0] <= 38 and 45 <= pt[1] <= 75 for pt in p)]
    prim_h_hist = [mesh_hist["h_eqs"][i] for i, p in enumerate(mesh_hist["polys"]) if any(8 <= pt[0] <= 38 and 45 <= pt[1] <= 75 for pt in p)]

    coll3 = PolyCollection(prim_polys_hist, array=np.array(prim_h_hist), cmap=cmap, norm=norm, edgecolors="black", linewidths=0.2)
    ax3.add_collection(coll3)
    ax3.set_xlim(8, 38)
    ax3.set_ylim(45, 75)
    ax3.set_aspect("equal")
    ax3.set_title("(c) Primary Corridor Detail: History-Aware Refinement\nContinuous refinement preserved between notch tip (x=10) and central hole", fontsize=10, fontweight="bold")
    ax3.set_xlabel("x [mm]")
    ax3.set_ylabel("y [mm]")
    ax3.plot([10, 26.5], [70, 51], "r--", linewidth=1.5, label="Crack Path Centerline")
    ax3.legend(loc="upper right", fontsize=8)

    # Panel (d): Quantitative Comparison Chart
    ax4 = fig.add_subplot(2, 2, 4)
    categories = ["State 2 (Hole Arrest)", "State 4 (Secondary Prop)", "History-Aware (Dual-Crack)"]
    x = np.arange(len(categories))
    width = 0.35

    prim_pct_le_l0 = [40.0, 36.1, 47.3]
    sec_pct_le_l0  = [0.0, 83.9, 84.5]

    rects1 = ax4.bar(x - width/2, prim_pct_le_l0, width, label="Primary Corridor (% <= l0)", color="#2b5c8f")
    rects2 = ax4.bar(x + width/2, sec_pct_le_l0, width, label="Secondary Corridor (% <= l0)", color="#d95f02")

    ax4.set_ylabel("Resolution Metric: Elements with h <= l0 [%]", fontsize=9)
    ax4.set_title("(d) Corridor Resolution Comparison Across Methodologies\nHistory-Aware envelope achieves simultaneous dual-branch resolution", fontsize=10, fontweight="bold")
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories, fontsize=9)
    ax4.legend(loc="upper left", fontsize=9)
    ax4.set_ylim(0, 105)
    ax4.grid(axis="y", linestyle=":", alpha=0.6)

    for rect in rects1:
        h = rect.get_height()
        ax4.annotate("%.1f%%" % h, xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")
    for rect in rects2:
        h = rect.get_height()
        ax4.annotate("%.1f%%" % h, xy=(rect.get_x() + rect.get_width() / 2, h),
                     xytext=(0, 3), textcoords="offset points", ha="center", va="bottom", fontsize=8, fontweight="bold")

    plt.tight_layout()
    log("Saving to " + str(out_pdf) + " and " + str(out_png) + "...")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, bbox_inches="tight")
    log("Figure successfully created!")

if __name__ == "__main__":
    main()
