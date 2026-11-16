# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1826_figures.py
========================================
Task F1826: Figure Generation for 4-Benchmark Harmonized Adapter Meshes.
Produces:
1. Individual standalone mesh views for Cases 1, 2, 3, and 5:
   - models/pandey_kumar_mode1/270_f1826_adapter_harmonization/figures/fig_f1826_case_{cid}_mesh.png / .pdf
2. 4-Panel publication-quality composite:
   - results/figures/fig_f1826_four_benchmark_harmonization.png / .pdf
   - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1826_four_benchmark_harmonization.pdf
"""
import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine
BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "270_f1826_adapter_harmonization")
OUT_FIG_DIR = os.path.join(BASE_DIR, "figures")
RESULTS_FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
REPORT_FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

CASES = [
    {
        "id": "case_1",
        "num": "Case 1",
        "title": "Case 1: Edge-Cracked Plate (eta_R = 4.5%)",
        "inp_path": os.path.join(BASE_DIR, "case1", "PK_F1826_CASE_1_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "xlim": (-0.02, 1.02),
        "ylim": (-0.02, 1.02),
        "aspect": "equal"
    },
    {
        "id": "case_2",
        "num": "Case 2",
        "title": "Case 2: Off-Axis Hole (eta_R = 4.0%)",
        "inp_path": os.path.join(BASE_DIR, "case2", "PK_F1826_CASE_2_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "xlim": (-0.02, 1.02),
        "ylim": (-0.02, 1.02),
        "aspect": "equal"
    },
    {
        "id": "case_3",
        "num": "Case 3",
        "title": "Case 3: Notched Plate w/ Pins (eta_R = 3.0%)",
        "inp_path": os.path.join(BASE_DIR, "case3", "PK_F1826_CASE_3_ADAPT_PHYS.inp"),
        "l0": 0.285,
        "xlim": (-2.0, 67.0),
        "ylim": (-2.0, 122.0),
        "aspect": "equal"
    },
    {
        "id": "case_5",
        "num": "Case 5",
        "title": "Case 5: Seven-Hole Plate (eta_R = 5.68%)",
        "inp_path": os.path.join(BASE_DIR, "case5", "PK_F1826_CASE_5_ADAPT_PHYS.inp"),
        "l0": 0.0080,
        "xlim": (-0.02, 1.02),
        "ylim": (-0.02, 1.02),
        "aspect": "equal"
    }
]


def parse_inp_mesh(filepath):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(filepath)
    elements = list(quads.values()) + list(tris.values())
    return nodes, elements


def render_mesh_on_ax(ax, nodes, elements, title, edge_lw=0.12):
    verts = []
    for conn in elements:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) >= 3:
            verts.append(np.array(pts))

    pc = PolyCollection(verts, facecolors="#f1f5f9", edgecolors="#1e293b", linewidths=edge_lw)
    ax.add_collection(pc)
    ax.set_title(title, fontsize=10, fontweight="bold")
    ax.set_xlabel("x [mm]", fontsize=9)
    ax.set_ylabel("y [mm]", fontsize=9)
    ax.tick_params(labelsize=8)
    ax.grid(True, linestyle=":", alpha=0.3)


def main():
    os.makedirs(OUT_FIG_DIR, exist_ok=True)
    os.makedirs(RESULTS_FIG_DIR, exist_ok=True)
    os.makedirs(REPORT_FIG_DIR, exist_ok=True)

    # 1. Standalone figures
    for c in CASES:
        inp = c["inp_path"]
        if not os.path.exists(inp):
            print("Skipping %s: mesh not found at %s" % (c["id"], inp))
            continue

        nodes, elements = parse_inp_mesh(inp)
        fig, ax = plt.subplots(figsize=(6, 6))
        sub_title = "%s (%d elements)" % (c["title"], len(elements))
        render_mesh_on_ax(ax, nodes, elements, sub_title, edge_lw=0.15)
        ax.set_xlim(c["xlim"])
        ax.set_ylim(c["ylim"])
        ax.set_aspect(c["aspect"])

        png_path = os.path.join(OUT_FIG_DIR, "fig_f1826_%s_mesh.png" % c["id"])
        pdf_path = os.path.join(OUT_FIG_DIR, "fig_f1826_%s_mesh.pdf" % c["id"])
        plt.tight_layout()
        plt.savefig(png_path, dpi=300)
        plt.savefig(pdf_path)
        plt.close(fig)
        print("Generated standalone: %s" % png_path)

    # 2. 4-Panel Composite
    fig, axes = plt.subplots(2, 2, figsize=(11, 11))
    flat_axes = axes.flatten()

    all_found = True
    for idx, c in enumerate(CASES):
        ax = flat_axes[idx]
        inp = c["inp_path"]
        if not os.path.exists(inp):
            all_found = False
            ax.text(0.5, 0.5, "Mesh pending: %s" % c["id"], ha="center", va="center")
            continue

        nodes, elements = parse_inp_mesh(inp)
        panel_label = chr(ord('a') + idx)
        title = "(%s) %s\nN = %d elements" % (panel_label, c["title"], len(elements))
        render_mesh_on_ax(ax, nodes, elements, title, edge_lw=0.10)
        ax.set_xlim(c["xlim"])
        ax.set_ylim(c["ylim"])
        ax.set_aspect(c["aspect"])

    plt.suptitle("Task F1826: 4-Benchmark Adaptive Meshes under Harmonized Adapters", fontsize=12, fontweight="bold", y=0.99)
    plt.tight_layout()

    composite_png = os.path.join(RESULTS_FIG_DIR, "fig_f1826_four_benchmark_harmonization.png")
    composite_pdf = os.path.join(RESULTS_FIG_DIR, "fig_f1826_four_benchmark_harmonization.pdf")
    plt.savefig(composite_png, dpi=300)
    plt.savefig(composite_pdf)

    # Also copy to report figures directory
    report_pdf = os.path.join(REPORT_FIG_DIR, "fig_f1826_four_benchmark_harmonization.pdf")
    report_png = os.path.join(REPORT_FIG_DIR, "fig_f1826_four_benchmark_harmonization.png")
    plt.savefig(report_pdf)
    plt.savefig(report_png, dpi=300)

    # Also save to 270 figures dir
    plt.savefig(os.path.join(OUT_FIG_DIR, "fig_f1826_four_benchmark_harmonization.png"), dpi=300)
    plt.savefig(os.path.join(OUT_FIG_DIR, "fig_f1826_four_benchmark_harmonization.pdf"))
    plt.close(fig)

    print("Generated composite: %s and %s" % (composite_png, composite_pdf))


if __name__ == "__main__":
    main()
