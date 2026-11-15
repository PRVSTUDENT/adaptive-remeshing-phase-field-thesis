# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1774_four_benchmark_regression.py
=========================================================
Generates the definitive 4-benchmark synthesis figure for Task F1774:
- Panel (a): Case 1 Mode-I Edge-Cracked Plate (Advancing Crack Path Refinement, N=20,232)
- Panel (b): Case 2 Plate with Off-Axis Hole (Single-Pass Method A.1, N=23,965)
- Panel (c): Case 3 Notched Plate with Hole and Pins (Multi-State Method A.2 2-Pass Envelope, N=28,933)
- Panel (d): Case 5 Seven-Hole Plate (Single-Pass Method A.1 Scale-Invariant, N=15,330)

Outputs:
- results/figures/fig_f1774_four_benchmark_regression_synthesis.png
- results/figures/fig_f1774_four_benchmark_regression_synthesis.pdf
- MA_AdaptiveRemeshing_Report_2026/figures/fig_f1774_four_benchmark_regression_synthesis.png
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
REPORT_FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
os.makedirs(FIG_DIR, exist_ok=True)
os.makedirs(REPORT_FIG_DIR, exist_ok=True)

MESH_CONFIGS = {
    "case_1": {
        "title": "(a) Case 1: Mode-I Edge-Cracked Plate",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "239_f1772_case1_remesh", "PK_F1728_CASE_1_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 13762,
        "method": "Method A.1 (Advancing Donor Envelope)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "IMPROVED (100% Ligament Compliant)"
    },
    "case_2": {
        "title": "(b) Case 2: Plate with Off-Axis Hole",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case2", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "published_el": 23618,
        "method": "Method A.1 (Single-Pass Recovery)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "QUALIFIED (+1.47% Parity, Exit 0)"
    },
    "case_3": {
        "title": "(c) Case 3: Notched Plate with Hole and Pins",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case3", "PK_F1728_CASE_3_ADAPT_PHYS.inp"),
        "l0": 0.285,
        "published_el": 12168,
        "method": "Method A.2 (2-Pass Sequential Envelope)",
        "width": 65.0,
        "height": 120.0,
        "verdict": "IMPROVED (Both Corridors Resolved)"
    },
    "case_5": {
        "title": "(d) Case 5: Seven-Hole Plate",
        "mesh_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "case5", "PK_F1728_CASE_5_ADAPT_PHYS.inp"),
        "l0": 0.0080,
        "published_el": 15714,
        "method": "Method A.1 (Scale-Invariant Diagnostic)",
        "width": 1.0,
        "height": 1.0,
        "verdict": "QUALIFIED (-2.44% Parity, Exit 0)"
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
                elif upper.startswith("*"):
                    current_section = "OTHER"
                continue

            if current_section == "NODE":
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) >= 3:
                    try:
                        n_id = int(tokens[0])
                        x = float(tokens[1])
                        y = float(tokens[2])
                        nodes[n_id] = (x, y)
                    except ValueError:
                        pass

            elif current_section == "ELEMENT":
                tokens = [t.strip() for t in line_str.split(",") if t.strip()]
                if len(tokens) >= 4:
                    try:
                        e_id = int(tokens[0])
                        conn = [int(t) for t in tokens[1:]]
                        elements[e_id] = conn
                        elem_types[e_id] = current_elem_type
                    except ValueError:
                        pass

    return nodes, elements, elem_types


def compute_element_area(nodes, conn):
    pts = [nodes[n] for n in conn if n in nodes]
    if len(pts) < 3:
        return 0.0
    # Shoelace formula
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(area) * 0.5


def main():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 9,
        "axes.labelsize": 9,
        "axes.titlesize": 10,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "figure.titlesize": 12,
        "figure.dpi": 300,
        "savefig.dpi": 300,
    })

    fig, axes = plt.subplots(1, 4, figsize=(18, 5.2), gridspec_kw={"wspace": 0.28})

    case_keys = ["case_1", "case_2", "case_3", "case_5"]
    norm = Normalize(vmin=0.0, vmax=3.0)
    cmap = plt.cm.get_cmap("viridis_r")

    last_poly = None

    for ax_idx, ck in enumerate(case_keys):
        cfg = MESH_CONFIGS[ck]
        ax = axes[ax_idx]
        inp_path = cfg["mesh_path"]
        l0 = cfg["l0"]

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
            ax.set_xlabel("x [mm]")
            ax.set_ylabel("y [mm]")
        else:
            ax.set_xlim(-0.02, 1.02)
            ax.set_ylim(-0.02, 1.02)
            ax.set_xlabel("x [mm]")
            ax.set_ylabel("y [mm]")

        title_str = "%s\n%d el (%.1f%% Q) | Pub: %d el\n$\\ell_0 = %.4f$ mm | %s" % (
            cfg["title"], total_el, quad_pct, cfg["published_el"], l0, cfg["verdict"]
        )
        ax.set_title(title_str, fontsize=9.5, pad=6)

    # Add colorbar
    cbar_ax = fig.add_axes([0.92, 0.20, 0.012, 0.60])
    cbar = fig.colorbar(last_poly, cax=cbar_ax)
    cbar.set_label("Spatial Resolution Ratio $h_e / \\ell_0$ (capped at 3.0)", fontsize=9)
    cbar.ax.tick_params(labelsize=8)

    fig.suptitle(
        "Task F1774: Unified Method A Four-Benchmark Adaptive Remeshing Synthesis\n"
        "(Frozen Shared Framework blob 8D71F38F, Frozen UEL CE8D5EDC, Abaqus CAE 2023 Datacheck Exit 0)",
        fontsize=12, y=0.98, fontweight="bold"
    )

    out_png = os.path.join(FIG_DIR, "fig_f1774_four_benchmark_regression_synthesis.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1774_four_benchmark_regression_synthesis.pdf")
    report_png = os.path.join(REPORT_FIG_DIR, "fig_f1774_four_benchmark_regression_synthesis.png")

    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, dpi=300, bbox_inches="tight")
    plt.savefig(report_png, dpi=300, bbox_inches="tight")
    plt.close()

    print("Saved figure to: %s" % out_png)
    print("Saved figure to: %s" % out_pdf)
    print("Saved figure to: %s" % report_png)


if __name__ == "__main__":
    main()
