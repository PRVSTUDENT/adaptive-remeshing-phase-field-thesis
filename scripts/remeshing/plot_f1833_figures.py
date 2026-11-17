# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1833_figures.py
======================================
Task F1833: State-Consistent Normalization Mesh Plotting Engine.
Generates:
1. Standalone publication mesh PNG and PDF for Cases 1, 2, 3, and 5:
   - results/figures/fig_f1833_case_1_standalone_mesh.png (.pdf)
   - results/figures/fig_f1833_case_2_standalone_mesh.png (.pdf)
   - results/figures/fig_f1833_case_3_standalone_mesh.png (.pdf)
   - results/figures/fig_f1833_case_5_standalone_mesh.png (.pdf)
2. 2x2 Publication Composite showing all 4 adapted meshes:
   - results/figures/fig_f1833_four_benchmark_synthesis.png (.pdf)
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization")
OUT_DIR = os.path.join(REPO_ROOT, "results", "figures")

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    with open(inp_path, "r") as f:
        in_nodes = False
        in_elements = False
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.startswith("*"):
                upper = line_str.upper()
                if upper.startswith("*NODE"):
                    in_nodes = True
                    in_elements = False
                    continue
                elif upper.startswith("*ELEMENT") and not upper.startswith("*ELEMENT OUTPUT"):
                    in_nodes = False
                    in_elements = True
                    continue
                else:
                    in_nodes = False
                    in_elements = False
                    continue
            if in_nodes:
                parts = line_str.split(",")
                nid = int(parts[0])
                coords = [float(x) for x in parts[1:]]
                nodes[nid] = (coords[0], coords[1])
            elif in_elements:
                parts = line_str.split(",")
                eid = int(parts[0])
                conn = [int(x) for x in parts[1:]]
                elements[eid] = conn
    return nodes, elements


def plot_single_mesh(inp_path, out_base, title_str, subtitle_str, x_lim=None, y_lim=None):
    nodes, elements = parse_inp_mesh(inp_path)
    patches = []
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            patches.append(Polygon(pts, closed=True))

    fig, ax = plt.subplots(figsize=(7, 7), dpi=300)
    pc = PatchCollection(patches, facecolor='none', edgecolor='#222222', linewidths=0.20)
    ax.add_collection(pc)

    all_x = [p[0] for p in nodes.values()]
    all_y = [p[1] for p in nodes.values()]
    ax.set_xlim(min(all_x) if x_lim is None else x_lim[0], max(all_x) if x_lim is None else x_lim[1])
    ax.set_ylim(min(all_y) if y_lim is None else y_lim[0], max(all_y) if y_lim is None else y_lim[1])
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontweight='bold', fontsize=10)
    ax.set_ylabel('Y [mm]', fontweight='bold', fontsize=10)
    ax.set_title(f"{title_str}\n{subtitle_str}", fontweight='bold', fontsize=11, pad=10)
    ax.grid(True, linestyle=':', alpha=0.4)
    plt.tight_layout()

    png_p = out_base + ".png"
    pdf_p = out_base + ".pdf"
    plt.savefig(png_p, dpi=300)
    plt.savefig(pdf_p)
    plt.close(fig)
    print(f"Saved: {png_p} and {pdf_p}")


def plot_2x2_composite(cases_data, out_base):
    fig, axes = plt.subplots(2, 2, figsize=(13, 13), dpi=300)
    ax_list = [axes[0, 0], axes[0, 1], axes[1, 0], axes[1, 1]]

    for i, c in enumerate(cases_data):
        ax = ax_list[i]
        nodes, elements = parse_inp_mesh(c["inp"])
        patches = [Polygon([nodes[nid] for nid in conn if nid in nodes], closed=True)
                   for conn in elements.values() if len(conn) >= 3]
        pc = PatchCollection(patches, facecolor='none', edgecolor='#222222', linewidths=0.15)
        ax.add_collection(pc)

        all_x = [p[0] for p in nodes.values()]
        all_y = [p[1] for p in nodes.values()]
        ax.set_xlim(min(all_x) if c["xlim"] is None else c["xlim"][0], max(all_x) if c["xlim"] is None else c["xlim"][1])
        ax.set_ylim(min(all_y) if c["ylim"] is None else c["ylim"][0], max(all_y) if c["ylim"] is None else c["ylim"][1])
        ax.set_aspect('equal')
        ax.set_xlabel('X [mm]', fontweight='bold', fontsize=9)
        ax.set_ylabel('Y [mm]', fontweight='bold', fontsize=9)
        ax.set_title(f"({chr(97+i)}) {c['title']}\n{c['meta']}", fontweight='bold', fontsize=10, pad=8)
        ax.grid(True, linestyle=':', alpha=0.35)

    plt.suptitle("Task F1833: Benchmark Adaptive Meshes under State-Consistent Normalization\n"
                 r"$\eta_e = \max_k (\mathrm{MISESERI}_{e,k} / \mathrm{MISESAVG}_k)$ Across Evolving Donor States",
                 fontsize=13, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.95])

    png_p = out_base + ".png"
    pdf_p = out_base + ".pdf"
    plt.savefig(png_p, dpi=300)
    plt.savefig(pdf_p)
    plt.close(fig)
    print(f"Saved 2x2 Composite: {png_p} and {pdf_p}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    cases = [
        {
            "cid": "case_1",
            "title": "Case 1: Mode-I Edge-Cracked Plate",
            "meta": r"$\eta_R = 4.5\%$, 5-State Recovery Donor (9,234 elements, Quad: 97.14%)",
            "inp": os.path.join(BASE_DIR, "case1", "PK_F1833_CASE_1_ADAPT_PHYS.inp"),
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "out_base": os.path.join(OUT_DIR, "fig_f1833_case_1_standalone_mesh")
        },
        {
            "cid": "case_2",
            "title": "Case 2: Mode-I Plate with Off-Axis Hole",
            "meta": r"$\eta_R = 4.0\%$, 4-State Recovery Donor (117,181 elements, Quad: 97.58%)",
            "inp": os.path.join(BASE_DIR, "case2", "PK_F1833_CASE_2_ADAPT_PHYS.inp"),
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "out_base": os.path.join(OUT_DIR, "fig_f1833_case_2_standalone_mesh")
        },
        {
            "cid": "case_3",
            "title": "Case 3: Notched Plate with Pins and Hole",
            "meta": r"$\eta_R = 3.0\%$, 3-State Recovery Donor (130,218 elements, Quad: 97.38%)",
            "inp": os.path.join(BASE_DIR, "case3", "PK_F1833_CASE_3_ADAPT_PHYS.inp"),
            "xlim": (-2.0, 67.0),
            "ylim": (-2.0, 122.0),
            "out_base": os.path.join(OUT_DIR, "fig_f1833_case_3_standalone_mesh")
        },
        {
            "cid": "case_5",
            "title": "Case 5: Plate with Seven Holes",
            "meta": r"$\eta_R = 5.68\%$, Single-State Pre-Crack Parity (15,466 elements, Quad: 97.90%)",
            "inp": os.path.join(BASE_DIR, "case5", "PK_F1833_CASE_5_ADAPT_PHYS.inp"),
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "out_base": os.path.join(OUT_DIR, "fig_f1833_case_5_standalone_mesh")
        }
    ]

    for c in cases:
        plot_single_mesh(
            c["inp"], c["out_base"],
            c["title"], c["meta"],
            x_lim=c["xlim"], y_lim=c["ylim"]
        )

    # 2x2 Composite
    composite_base = os.path.join(OUT_DIR, "fig_f1833_four_benchmark_synthesis")
    plot_2x2_composite(cases, composite_base)

if __name__ == "__main__":
    main()
