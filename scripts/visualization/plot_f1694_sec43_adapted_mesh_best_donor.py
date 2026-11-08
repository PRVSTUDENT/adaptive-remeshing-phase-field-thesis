# -*- coding: utf-8 -*-
"""
plot_f1694_sec43_adapted_mesh_best_donor.py
===========================================
Task F1694 Stage 3: Publication-quality wireframe and element size plot of the
adapted mesh generated from Donor (b): Secondary Mid-Propagation recovery
(PK_SEC43_STAGGERED_RECOVERY_SEC_MIDPROP.odb, uy = 0.300 mm).

Compares adapted mesh resolution against Pandey-Kumar (2025) Fig. 16b.
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.patches import Circle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
ADAPT_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp")
METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_adapted_mesh_best_donor_metrics.json")
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

    # Color elements by equivalent size
    cmap = plt.get_cmap("viridis_r")
    coll = PolyCollection(polys, array=np.array(h_vals), cmap=cmap, edgecolors="none", clim=(0.08, 1.5))
    ax.add_collection(coll)

    # Plot mesh wireframe
    lc = LineCollection(lines, colors="#2b2b2b", linewidths=0.25, alpha=0.6)
    ax.add_collection(lc)

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

    # Overlay Fig. 15a experimental crack path
    t_prim = np.linspace(0, 1, 50)
    x_prim = (1-t_prim)**2 * 10.0 + 2*(1-t_prim)*t_prim * 18.0 + t_prim**2 * 27.5
    y_prim = (1-t_prim)**2 * 70.0 + 2*(1-t_prim)*t_prim * 68.0 + t_prim**2 * 56.5
    ax.plot(x_prim, y_prim, color="red", lw=2.0, ls="--", zorder=8, label="Fig. 15a Exp. Path")

    t_sec = np.linspace(0, 1, 50)
    x_sec = (1-t_sec)**2 * 46.5 + 2*(1-t_sec)*t_sec * 55.0 + t_sec**2 * 65.0
    y_sec = (1-t_sec)**2 * 51.0 + 2*(1-t_sec)*t_sec * 50.0 + t_sec**2 * 48.0
    ax.plot(x_sec, y_sec, color="red", lw=2.0, ls="--", zorder=8)

    # Annotations
    ax.text(10.5, 71.5, "Notch\nTip", fontsize=8.5, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void\n$R=10$ mm", ha="center", va="center", fontsize=8, color="black", zorder=10)

    # Callouts
    ax.annotate(r"Primary Corridor Refined" + "\n" + r"($h_{\min} = 0.088\,\mathrm{mm} \leq \ell_0/3$)",
                xy=(18.0, 62.0), xytext=(3.0, 48.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8.5, fontweight="bold", zorder=10)

    ax.annotate(r"Secondary Corridor Moderately Refined" + "\n" + r"($h_{\mathrm{med}} = 0.502\,\mathrm{mm} < 1.5\,\mathrm{mm}$ coarse)" + "\n" + r"(0.0% $\leq \ell_0/2 = 0.143\,\mathrm{mm}$)",
                xy=(54.0, 51.0), xytext=(30.0, 36.0),
                arrowprops=dict(facecolor="black", shrink=0.05, width=1, headwidth=5),
                fontsize=8, fontweight="bold", zorder=10)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")
    ax.set_xlabel("x (mm)", fontsize=11)
    ax.set_ylabel("y (mm)", fontsize=11)
    ax.set_title(r"$\mathbf{Task\; F1694\; Best\text{-}Donor\; Adapted\; Mesh\; (12{,}110\; Elements)}$" + "\n" +
                 r"Native Remeshing from Secondary Mid-Propagation Donor ($u_y = 0.300\,\mathrm{mm}$)",
                 fontsize=10.5, pad=12)

    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.85)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label(r"Equivalent Element Size $h_{\mathrm{equiv}}$ (mm)", fontsize=10)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1694_sec43_adapted_mesh_best_donor.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1694_sec43_adapted_mesh_best_donor.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)

    print("Saved publication adapted mesh figures:")
    print("  %s" % pdf_path)
    print("  %s" % png_path)

if __name__ == "__main__":
    main()
