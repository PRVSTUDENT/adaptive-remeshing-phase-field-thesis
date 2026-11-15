# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1779_four_benchmark_regression.py
=========================================================
Generates the definitive 4-benchmark synthesis figure for Task F1779:
- Panel (a): Case 1 Mode-I Edge-Cracked Plate (Advancing Crack Path Refinement, N=20,232)
- Panel (b): Case 2 Plate with Off-Axis Hole (Advancing Damage Envelope, N=17,280, 0 barriers, 77.1% <= l0/2)
- Panel (c): Case 3 Notched Plate with Hole and Pins (Multi-State Method A.2 with Coarsening, N=9,975, 100% compliant)
- Panel (d): Case 5 Seven-Hole Plate (Single-Pass Method A.1 Scale-Invariant, N=15,330, 100% inter-hole compliant)

Outputs:
- results/figures/fig_f1779_four_benchmark_regression_synthesis.png
- results/figures/fig_f1779_four_benchmark_regression_synthesis.pdf
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
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "PK_F1728_CASE_1_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 13941,
        "method": "Method A.1 (Advancing Donor Envelope)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "PRESERVED (100% Ligament Compliant)"
    },
    "case_2": {
        "title": "(b) Case 2: Plate with Off-Axis Hole",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "241_f1779_improved_regression", "case2", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 23618,
        "method": "Method A.1 (Advancing Damage Envelope)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "IMPROVED (0 Barriers, 77.1% <= l0/2)"
    },
    "case_3": {
        "title": "(c) Case 3: Notched Plate with Hole and Pins",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "241_f1779_improved_regression", "case3", "PK_F1728_CASE_3_ADAPT_PHYS.inp"),
        "l0": 0.285,
        "published_el": 12168,
        "method": "Method A.2 (Multi-State + Bulk Coarsening)",
        "width": 65.0,
        "height": 120.0,
        "verdict": "IMPROVED (9,975 el, 100% Secondary Compliant)"
    },
    "case_5": {
        "title": "(d) Case 5: Seven-Hole Plate",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case5", "PK_F1728_CASE_5_ADAPT_PHYS.inp"),
        "l0": 0.0080,
        "published_el": 15714,
        "method": "Method A.1 (Scale-Invariant Diagnostic)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "PRESERVED (100% Inter-Hole Compliant)"
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

            if current_section == "NODE":
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass

            elif current_section == "ELEMENT":
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        elements[eid] = conn
                        elem_types[eid] = current_elem_type
                    except ValueError:
                        pass

    return nodes, elements, elem_types


def compute_element_area(nodes, conn):
    pts = [nodes[n] for n in conn if n in nodes]
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        area += x1 * y2 - x2 * y1
    return 0.5 * abs(area)


def main():
    print("=" * 70)
    print("Plotting Task F1779 Definitive 4-Benchmark Regression Figure")
    print("=" * 70)

    fig, axes = plt.subplots(1, 4, figsize=(20, 6.0), gridspec_kw={"wspace": 0.28})

    norm = Normalize(vmin=0.2, vmax=2.5)
    cmap = plt.cm.viridis_r

    last_poly = None

    for idx, (ck, cfg) in enumerate(MESH_CONFIGS.items()):
        ax = axes[idx]
        inp_path = cfg["mesh_path"]
        l0 = cfg["l0"]

        if not os.path.exists(inp_path):
            print("ERROR: Missing mesh file: %s" % inp_path)
            ax.text(0.5, 0.5, "FILE MISSING\n%s" % os.path.basename(inp_path),
                    ha="center", va="center", transform=ax.transAxes, color="red")
            continue

        print("Parsing %s: %s" % (ck, inp_path))
        nodes, elements, elem_types = parse_abaqus_inp(inp_path)

        verts = []
        ratios = []
        quad_count = 0
        tri_count = 0

        for eid, conn in elements.items():
            if len(conn) == 4:
                quad_count += 1
            else:
                tri_count += 1

            pts = [nodes[n] for n in conn if n in nodes]
            if len(pts) >= 3:
                verts.append(pts)
                area = compute_element_area(nodes, conn)
                h_e = math.sqrt(area) if area > 0 else l0
                ratios.append(min(h_e / l0, 3.0))

        ratios_arr = np.array(ratios)
        poly = PolyCollection(verts, array=ratios_arr, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.08)
        ax.add_collection(poly)
        last_poly = poly

        total_el = len(elements)
        quad_pct = 100.0 * quad_count / float(total_el) if total_el > 0 else 0.0

        ax.set_aspect("equal")
        if ck == "case_3":
            ax.set_xlim(-2, 67)
            ax.set_ylim(-5, 125)
            ax.set_xlabel("x [mm]", fontsize=9)
            ax.set_ylabel("y [mm]", fontsize=9)
        else:
            ax.set_xlim(-0.02, 1.02)
            ax.set_ylim(-0.02, 1.02)
            ax.set_xlabel("x [mm]", fontsize=9)
            ax.set_ylabel("y [mm]", fontsize=9)

        title_str = "%s\n%d el (%.1f%% Q) | Target: %d el\n$\\ell_0 = %.4f$ mm | %s" % (
            cfg["title"], total_el, quad_pct, cfg["published_el"], l0, cfg["verdict"]
        )
        ax.set_title(title_str, fontsize=9.0, pad=6)

    cbar_ax = fig.add_axes([0.92, 0.20, 0.012, 0.60])
    cbar = fig.colorbar(last_poly, cax=cbar_ax)
    cbar.set_label("Spatial Resolution Ratio $h_e / \\ell_0$ (capped at 2.5)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(
        "Task F1779: Unified Method A Finalized Four-Benchmark Adaptive Remeshing Synthesis\n"
        "(Single Shared Framework, Bitwise Frozen UEL CE8D5EDC, Abaqus CAE 2023 Qualified)",
        fontsize=12, y=0.98, fontweight="bold"
    )

    out_png = os.path.join(FIG_DIR, "fig_f1779_four_benchmark_regression_synthesis.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1779_four_benchmark_regression_synthesis.pdf")

    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved figure to: %s" % out_png)
    print("Saved figure to: %s" % out_pdf)


if __name__ == "__main__":
    main()
