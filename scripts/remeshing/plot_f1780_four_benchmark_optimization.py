# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1780_four_benchmark_optimization.py
===========================================================
Generates the definitive 4-benchmark optimization synthesis figure for Task F1780:
- Panel (a): Case 1 Mode-I Edge-Cracked Plate (Advancing Crack Path Refinement, N=16,597, Tip <= l0/2: 75.0%)
- Panel (b): Case 2 Plate with Off-Axis Hole (Calibrated Distal Refinement, N=32,983, 100% <= l0/2, 0 barriers)
- Panel (c): Case 3 Notched Plate with Hole and Pins (Multi-State + Notch Seeding, N=10,064, max AR=3.09, 100% secondary)
- Panel (d): Case 5 Seven-Hole Plate (Single-Pass Method A.1, N=15,466, Zero Regression, max AR=2.37)

Outputs:
- results/figures/fig_f1780_four_benchmark_optimization_synthesis.png
- results/figures/fig_f1780_four_benchmark_optimization_synthesis.pdf
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

MESH_CONFIGS = {
    "case_1": {
        "title": "(a) Case 1: Mode-I Edge-Cracked Plate",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "242_f1780_optimized_regression", "case1", "PK_F1728_CASE_1_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 13941,
        "method": "Method A.1 (Advancing Donor Envelope)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "OPTIMIZED (16,597 el, 75.0% Tip <= l0/2, 100% Ligament)"
    },
    "case_2": {
        "title": "(b) Case 2: Plate with Off-Axis Hole",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "242_f1780_optimized_regression", "case2", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 23618,
        "method": "Method A.1 (Advancing Damage Envelope)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "OPTIMIZED (32,983 el, 100% Distal <= l0/2, 0 Barriers)"
    },
    "case_3": {
        "title": "(c) Case 3: Notched Plate with Hole and Pins",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "242_f1780_optimized_regression", "case3", "PK_F1728_CASE_3_ADAPT_PHYS.inp"),
        "l0": 0.285,
        "published_el": 12168,
        "method": "Method A.2 (Multi-State + Notch Root Seeding)",
        "width": 65.0,
        "height": 120.0,
        "verdict": "OPTIMIZED (10,064 el, Max AR 3.09 <= 4.0, 100% Sec)"
    },
    "case_5": {
        "title": "(d) Case 5: Seven-Hole Plate",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "242_f1780_optimized_regression", "case5", "PK_F1728_CASE_5_ADAPT_PHYS.inp"),
        "l0": 0.0080,
        "published_el": 15714,
        "method": "Method A.1 (Scale-Invariant Stress Recovery)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "PRESERVED (15,466 el, Max AR 2.37, Zero Regression)"
    }
}


def parse_abaqus_inp(inp_path):
    nodes = {}
    elements = {}
    elem_types = {}
    current_section = None
    current_elem_type = None

    with open(inp_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue

            if line_str.startswith("*"):
                upper = line_str.upper()
                if upper.startswith("*NODE"):
                    current_section = "NODE"
                elif upper.startswith("*ELEMENT"):
                    current_section = "ELEMENT"
                    parts = upper.split(",")
                    current_elem_type = "UNKNOWN"
                    for p in parts:
                        if "TYPE" in p:
                            current_elem_type = p.split("=")[-1].strip()
                else:
                    current_section = None
                continue

            parts = [p.strip() for p in line_str.split(",") if p.strip()]
            if current_section == "NODE" and len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x, y = float(parts[1]), float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
            elif current_section == "ELEMENT" and len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:]]
                    elements[eid] = conn
                    elem_types[eid] = current_elem_type
                except ValueError:
                    pass

    return nodes, elements, elem_types


def compute_element_polygons_and_ratio(nodes, elements, l0):
    polygons = []
    ratios = []

    for eid, conn in elements.items():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) not in (3, 4):
            continue

        polygons.append(pts)

        if len(pts) == 4:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
            area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
        else:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
            area = 0.5 * abs(x1*(y2 - y3) + x2*(y3 - y1) + x3*(y1 - y2))

        h_elem = math.sqrt(max(1e-12, area))
        ratio = h_elem / l0
        ratios.append(ratio)

    return polygons, np.array(ratios)


def plot_four_benchmark_regression():
    fig, axes = plt.subplots(2, 2, figsize=(15, 13))
    axes = axes.flatten()

    cmap = plt.cm.get_cmap("viridis_r")
    norm = Normalize(vmin=0.2, vmax=2.5)

    case_order = ["case_1", "case_2", "case_3", "case_5"]

    for idx, ckey in enumerate(case_order):
        ax = axes[idx]
        cfg = MESH_CONFIGS[ckey]
        inp_path = cfg["mesh_path"]
        l0 = cfg["l0"]

        print("Plotting %s from %s..." % (cfg["title"], inp_path))
        nodes, elements, _ = parse_abaqus_inp(inp_path)
        polygons, ratios = compute_element_polygons_and_ratio(nodes, elements, l0)

        n_elem = len(elements)
        quad_count = sum(1 for conn in elements.values() if len(conn) == 4)
        quad_pct = 100.0 * quad_count / max(n_elem, 1)

        collection = PolyCollection(polygons, cmap=cmap, norm=norm, edgecolors="none", linewidths=0.0)
        collection.set_array(ratios)
        ax.add_collection(collection)

        ax.set_aspect("equal")
        w, h = cfg["width"], cfg["height"]
        pad_x, pad_y = 0.04 * w, 0.04 * h
        ax.set_xlim(-pad_x, w + pad_x)
        ax.set_ylim(-pad_y, h + pad_y)

        unit = "mm"
        ax.set_xlabel("x [%s]" % unit, fontsize=11, fontweight="bold")
        ax.set_ylabel("y [%s]" % unit, fontsize=11, fontweight="bold")

        title_text = "%s\n%s: %d el (%.1f%% quads) | Ref: %d el" % (
            cfg["title"], cfg["verdict"], n_elem, quad_pct, cfg["published_el"]
        )
        ax.set_title(title_text, fontsize=11, fontweight="bold", pad=8)
        ax.tick_params(labelsize=10)
        ax.grid(True, linestyle=":", alpha=0.3)

    plt.tight_layout()
    fig.subplots_adjust(bottom=0.10, hspace=0.25, wspace=0.18)
    cbar_ax = fig.add_axes([0.20, 0.04, 0.60, 0.022])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax, orientation="horizontal")
    cbar.set_label(r"Spatial Discretization Ratio $h / \ell_0$ (Fine $\leq 0.5$, Process Zone $\leq 1.0$, Coarse $> 1.0$)",
                    fontsize=12, fontweight="bold", labelpad=6)
    cbar.ax.tick_params(labelsize=11)

    out_png = os.path.join(FIG_DIR, "fig_f1780_four_benchmark_optimization_synthesis.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1780_four_benchmark_optimization_synthesis.pdf")

    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close()
    print("SUCCESS: 4-benchmark synthesis plot saved to:")
    print("  %s" % out_png)
    print("  %s" % out_pdf)

if __name__ == "__main__":
    plot_four_benchmark_regression()
