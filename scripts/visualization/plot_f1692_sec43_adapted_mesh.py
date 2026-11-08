# -*- coding: utf-8 -*-
"""
plot_f1692_sec43_adapted_mesh.py
================================
Plots publication-quality wireframe of adapted physical mesh for Task F1692:
Pandey-Kumar Section 4.3 Staggered Adaptive Remeshing.
Compares adapted mesh resolution against paper Fig. 16b.
"""

import os
import sys
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Circle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
ADAPT_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_ADAPT_PHYS.inp")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

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
                except ValueError:
                    continue

    return nodes, elements

def main():
    print("Parsing adapted mesh: %s" % ADAPT_INP)
    nodes, elements = parse_mesh(ADAPT_INP)
    print("Parsed %d nodes and %d elements." % (len(nodes), len(elements)))

    # Compute element sizes (h_eq = sqrt(area))
    polys = []
    h_vals = []
    lines = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            polys.append(pts)
            poly_x = [p[0] for p in pts]
            poly_y = [p[1] for p in pts]
            area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%len(pts)] - poly_y[i]*poly_x[(i+1)%len(pts)] for i in range(len(pts))]))
            h_vals.append(math.sqrt(area))
            for i in range(len(pts)):
                p1 = pts[i]
                p2 = pts[(i+1)%len(pts)]
                lines.append((p1, p2))

    fig, ax = plt.subplots(figsize=(6.5, 9.5), dpi=300)

    # Plot mesh wireframe
    lc = LineCollection(lines, colors="#2b2b2b", linewidths=0.25, alpha=0.7)
    ax.add_collection(lc)

    # Color elements by equivalent size
    import numpy as np
    cmap = plt.cm.get_cmap("viridis_r")
    coll = PolyCollection(polys, array=np.array(h_vals), cmap=cmap, edgecolors="none", clim=(0.05, 1.5))
    ax.add_collection(coll)

    # Plate boundary and notch
    ax.plot([0, 65, 65, 0, 0], [0, 0, 120, 120, 0], color="black", lw=1.2)
    ax.plot([0, 10, 10, 0], [70.2, 70.2, 69.8, 69.8], color="black", lw=1.2)

    # Holes
    hole_center = Circle((36.5, 51.0), 10.0, fill=True, facecolor="white", edgecolor="black", lw=1.2, zorder=5)
    hole_lower = Circle((20.0, 20.0), 5.0, fill=True, facecolor="white", edgecolor="black", lw=1.2, zorder=5)
    hole_upper = Circle((20.0, 100.0), 5.0, fill=True, facecolor="white", edgecolor="black", lw=1.2, zorder=5)
    ax.add_patch(hole_center)
    ax.add_patch(hole_lower)
    ax.add_patch(hole_upper)

    # Annotations
    ax.text(10.5, 71.5, "Notch\nTip", fontsize=8.5, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void\n$R=10$ mm", ha="center", va="center", fontsize=8, color="black", zorder=10)

    # Callouts
    ax.annotate("Primary Corridor Refined\n($h_{\\min} = 0.067$ mm $\\leq \\ell_0/4$)",
                xy=(18.0, 62.0), xytext=(3.0, 48.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold", zorder=10)

    ax.annotate("Secondary Corridor Unrefined\n($h_{\\mathrm{med}} = 0.573$ mm $\\gg \\ell_0/2$, 0.0% $\\leq \\ell_0/2$)",
                xy=(54.0, 51.0), xytext=(35.0, 36.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold", zorder=10)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)", fontsize=11)
    ax.set_ylabel("y (mm)", fontsize=11)
    ax.set_title("Pandey--Kumar Section 4.3 Native Adapted Mesh ($15{,}625$ Elements)\nSingle-Rule Native Remeshing from Degraded Donor Frame",
                 fontsize=10.5, fontweight="bold", pad=12)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Equivalent Element Size $h_{\\mathrm{equiv}}$ (mm)", fontsize=10)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1692_sec43_adapted_mesh.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1692_sec43_adapted_mesh.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)

    print("Saved publication adapted mesh figures:")
    print("  %s" % pdf_path)
    print("  %s" % png_path)

if __name__ == "__main__":
    main()
