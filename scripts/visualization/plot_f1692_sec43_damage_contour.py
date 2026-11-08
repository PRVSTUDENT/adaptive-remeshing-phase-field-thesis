# -*- coding: utf-8 -*-
"""
plot_f1692_sec43_damage_contour.py
==================================
Plots publication-quality damage field contour for Task F1692:
Pandey-Kumar Section 4.3 Staggered Solver Rerun.
Shows full 65 x 120 mm plate with 3 holes, initial notch,
and both crack paths (primary notch->hole and secondary hole->right boundary).
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
PHYS_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_PHYS.inp")
DAMAGED_JSON = os.path.join(MODEL_DIR, "f1692_damaged_elements.json")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def parse_inp_mesh(inp_path):
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
                nid = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                nodes[nid] = (x, y)
            elif in_elements:
                parts = [int(p.strip()) for p in line_str.split(",")]
                eid = parts[0]
                conn = parts[1:]
                elements[eid] = conn

    return nodes, elements

def main():
    print("Parsing physical mesh: %s" % PHYS_INP)
    nodes, elements = parse_inp_mesh(PHYS_INP)
    print("Parsed %d nodes and %d elements." % (len(nodes), len(elements)))

    print("Loading damage data: %s" % DAMAGED_JSON)
    with open(DAMAGED_JSON, "r") as f:
        damage_data = json.load(f)

    n_phys = len(elements)
    damaged_dict = {}
    for item in damage_data.get("damaged_elements", []):
        raw_eid = item["element"]
        phys_eid = ((raw_eid - 1) % n_phys) + 1
        d_val = item["damage"]
        # Keep maximum damage if multiple layers report for the same physical element
        if phys_eid not in damaged_dict or d_val > damaged_dict[phys_eid]:
            damaged_dict[phys_eid] = d_val

    # Build polygons and damage array
    polys = []
    d_vals = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            polys.append(pts)
            d = damaged_dict.get(eid, 0.0)
            d_vals.append(d)

    d_arr = np.array(d_vals)
    print("Damage stats: min=%.4f, max=%.4f, count(d>0.10)=%d, count(d>0.80)=%d" % (
        d_arr.min(), d_arr.max(), np.sum(d_arr > 0.10), np.sum(d_arr > 0.80)
    ))

    # Plot
    fig, ax = plt.subplots(figsize=(6.5, 9.5), dpi=300)

    # Colormap: white -> light orange -> crimson -> dark red
    cmap = plt.cm.get_cmap("inferno")

    coll = PolyCollection(polys, array=d_arr, cmap=cmap, edgecolors="none", clim=(0.0, 1.0))
    ax.add_collection(coll)

    # Overlay wireframe for holes and notch
    # Plate boundary: 65 x 120 mm
    ax.plot([0, 65, 65, 0, 0], [0, 0, 120, 120, 0], color="black", lw=1.2)
    # Notch: 10 x 0.4 mm at y = 70
    ax.plot([0, 10, 10, 0], [70.2, 70.2, 69.8, 69.8], color="black", lw=1.2)

    # 3 Holes
    hole_center = Circle((36.5, 51.0), 10.0, fill=True, facecolor="white", edgecolor="black", lw=1.2, zorder=5)
    hole_lower = Circle((20.0, 20.0), 5.0, fill=True, facecolor="lightgray", edgecolor="black", lw=1.2, zorder=5)
    hole_upper = Circle((20.0, 100.0), 5.0, fill=True, facecolor="lightgray", edgecolor="black", lw=1.2, zorder=5)
    ax.add_patch(hole_center)
    ax.add_patch(hole_lower)
    ax.add_patch(hole_upper)

    # Annotations
    ax.text(10.5, 71.5, "Initial Notch\n(10 mm)", fontsize=9, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void\n$R=10$ mm", ha="center", va="center", fontsize=8, color="black", zorder=10)
    ax.text(20.0, 20.0, "Pin\nFixed", ha="center", va="center", fontsize=7.5, color="black", zorder=10)
    ax.text(20.0, 100.0, "Pin\n$u_y$", ha="center", va="center", fontsize=7.5, color="black", zorder=10)

    # Crack path callouts
    ax.annotate("Primary Crack\n(Notch -> Void)", xy=(22.0, 61.0), xytext=(5.0, 48.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold", zorder=10)

    ax.annotate("Secondary Crack\n(Void -> Boundary)", xy=(54.0, 51.0), xytext=(48.0, 36.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold", zorder=10)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)", fontsize=11)
    ax.set_ylabel("y (mm)", fontsize=11)
    ax.set_title("Pandey--Kumar Section 4.3 Staggered Phase-Field Fracture\nConverged Dual-Branch Crack Paths ($d = 1.0$)",
                 fontsize=11, fontweight="bold", pad=12)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Phase-Field Damage $d$", fontsize=10)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1692_sec43_damage_contour.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1692_sec43_damage_contour.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)

    print("Saved publication figures:")
    print("  %s" % pdf_path)
    print("  %s" % png_path)

if __name__ == "__main__":
    main()
