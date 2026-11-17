# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1834_figures.py
======================================
Task F1834: Early-State Blowup Guard Mesh Plotting Engine.
Generates:
1. Standalone publication mesh PNG and PDF for Cases 1, 2, 3, and 5:
   - results/figures/fig_f1834_case_1_standalone_mesh.png (.pdf)
   - results/figures/fig_f1834_case_2_standalone_mesh.png (.pdf)
   - results/figures/fig_f1834_case_3_standalone_mesh.png (.pdf)
   - results/figures/fig_f1834_case_5_standalone_mesh.png (.pdf)
2. 2x2 Publication Composite showing all 4 adapted meshes:
   - results/figures/fig_f1834_four_benchmark_synthesis.png (.pdf)
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
F1834_BASE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "274_f1834_blowup_guard")
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

    plt.suptitle("Task F1834: Shared Framework Blowup Guard Adapted Meshes (All 4 Cases)",
                 fontweight='bold', fontsize=14, y=0.995)
    plt.tight_layout()
    png_p = out_base + ".png"
    pdf_p = out_base + ".pdf"
    plt.savefig(png_p, dpi=300)
    plt.savefig(pdf_p)
    plt.close(fig)
    print(f"Saved 2x2 Composite: {png_p} and {pdf_p}")


def main(target_tag="thresh_050"):
    if not os.path.exists(OUT_DIR):
        os.makedirs(OUT_DIR)

    tag_dir = os.path.join(F1834_BASE, target_tag)
    print(f"Plotting figures from target tag directory: {tag_dir}")

    # Case 1
    c1_inp = os.path.join(tag_dir, "case1", f"PK_F1834_C1_{target_tag.upper()}_ADAPT_PHYS.inp")
    c1_rec = os.path.join(tag_dir, "case1", f"PK_F1834_C1_{target_tag.upper()}_RECEIPT.json")
    with open(c1_rec, "r") as f:
        r1 = json.load(f)
    n1 = r1["audit_metrics"]["total_elements"]
    q1 = r1["audit_metrics"]["quad_fraction_pct"]
    coarse1 = r1["audit_metrics"]["coarsening_ratio"]
    plot_single_mesh(
        c1_inp,
        os.path.join(OUT_DIR, "fig_f1834_case_1_standalone_mesh"),
        "Case 1: Mode-I Edge-Cracked Plate (Blowup Guard, eta_R=4.5%)",
        f"Elements: {n1:,} | Quad: {q1:.1f}% | Far-Field Coarsening: {coarse1:.2f}x",
        x_lim=(0.0, 1.0), y_lim=(0.0, 1.0)
    )

    # Case 2
    c2_inp = os.path.join(tag_dir, "case2", f"PK_F1834_C2_{target_tag.upper()}_ADAPT_PHYS.inp")
    c2_rec = os.path.join(tag_dir, "case2", f"PK_F1834_C2_{target_tag.upper()}_RECEIPT.json")
    with open(c2_rec, "r") as f:
        r2 = json.load(f)
    n2 = r2["audit_metrics"]["total_elements"]
    q2 = r2["audit_metrics"]["quad_fraction_pct"]
    coarse2 = r2["audit_metrics"]["coarsening_ratio"]
    plot_single_mesh(
        c2_inp,
        os.path.join(OUT_DIR, "fig_f1834_case_2_standalone_mesh"),
        "Case 2: Mode-I Plate with Off-Axis Hole (Blowup Guard, eta_R=4.0%)",
        f"Elements: {n2:,} | Quad: {q2:.1f}% | Far-Field Coarsening: {coarse2:.2f}x",
        x_lim=(0.0, 1.0), y_lim=(0.0, 1.0)
    )

    # Case 3
    c3_inp = os.path.join(tag_dir, "case3", f"PK_F1834_C3_{target_tag.upper()}_ADAPT_PHYS.inp")
    c3_rec = os.path.join(tag_dir, "case3", f"PK_F1834_C3_{target_tag.upper()}_RECEIPT.json")
    with open(c3_rec, "r") as f:
        r3 = json.load(f)
    n3 = r3["audit_metrics"]["total_elements"]
    q3 = r3["audit_metrics"]["quad_fraction_pct"]
    coarse3 = r3["audit_metrics"]["coarsening_ratio"]
    plot_single_mesh(
        c3_inp,
        os.path.join(OUT_DIR, "fig_f1834_case_3_standalone_mesh"),
        "Case 3: Notched Plate with Pins (Blowup Guard, eta_R=3.0%)",
        f"Elements: {n3:,} | Quad: {q3:.1f}% | Far-Field Coarsening: {coarse3:.2f}x",
        x_lim=(0.0, 120.0), y_lim=(0.0, 120.0)
    )

    # Case 5
    c5_inp = os.path.join(tag_dir, "case5", f"PK_F1834_C5_{target_tag.upper()}_ADAPT_PHYS.inp")
    c5_rec = os.path.join(tag_dir, "case5", f"PK_F1834_C5_{target_tag.upper()}_RECEIPT.json")
    with open(c5_rec, "r") as f:
        r5 = json.load(f)
    n5 = r5["audit_metrics"]["total_elements"]
    q5 = r5["audit_metrics"]["quad_fraction_pct"]
    coarse5 = r5["audit_metrics"]["coarsening_ratio"]
    plot_single_mesh(
        c5_inp,
        os.path.join(OUT_DIR, "fig_f1834_case_5_standalone_mesh"),
        "Case 5: Plate with Seven Holes (Table 6 Parity, eta_R=5.68%)",
        f"Elements: {n5:,} | Quad: {q5:.1f}% | Far-Field Coarsening: {coarse5:.2f}x",
        x_lim=(0.0, 1.0), y_lim=(0.0, 1.0)
    )

    # 2x2 Composite
    cases_data = [
        {
            "inp": c1_inp,
            "title": "Case 1: Mode-I Edge-Cracked Plate",
            "meta": f"Elements: {n1:,} | Quad: {q1:.1f}% | Coarsening: {coarse1:.2f}x",
            "xlim": (0.0, 1.0), "ylim": (0.0, 1.0)
        },
        {
            "inp": c2_inp,
            "title": "Case 2: Mode-I Plate with Off-Axis Hole",
            "meta": f"Elements: {n2:,} | Quad: {q2:.1f}% | Coarsening: {coarse2:.2f}x",
            "xlim": (0.0, 1.0), "ylim": (0.0, 1.0)
        },
        {
            "inp": c3_inp,
            "title": "Case 3: Notched Plate with Pins",
            "meta": f"Elements: {n3:,} | Quad: {q3:.1f}% | Coarsening: {coarse3:.2f}x",
            "xlim": (0.0, 120.0), "ylim": (0.0, 120.0)
        },
        {
            "inp": c5_inp,
            "title": "Case 5: Plate with Seven Holes",
            "meta": f"Elements: {n5:,} | Quad: {q5:.1f}% | Coarsening: {coarse5:.2f}x",
            "xlim": (0.0, 1.0), "ylim": (0.0, 1.0)
        }
    ]
    plot_2x2_composite(cases_data, os.path.join(OUT_DIR, "fig_f1834_four_benchmark_synthesis"))
    print("\nAll F1834 publication figures successfully generated.")


if __name__ == "__main__":
    tag = sys.argv[1] if len(sys.argv) > 1 else "thresh_050"
    main(tag)
