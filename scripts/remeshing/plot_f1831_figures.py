# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1831_figures.py
========================================
Task F1831: Figure Generation for Matched Donor Experiment.
Generates:
1. Individual standalone mesh views for Cases 1, 2, 3, and 5:
   - models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/figures/fig_f1831_case_{cid}_mesh.png / .pdf
   - results/figures/fig_f1831_case_{cid}_matched_mesh.png / .pdf
2. 4-Panel publication-quality composite:
   - results/figures/fig_f1831_matched_donor_synthesis.png / .pdf
   - models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/figures/fig_f1831_matched_donor_synthesis.png / .pdf
   - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1831_matched_donor_synthesis.pdf
"""
import os
import sys
import shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

BASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "272_f1831_matched_donor_experiment")
OUT_FIG_DIR = os.path.join(BASE_DIR, "figures")
RESULTS_FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
REPORT_FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

for d in [OUT_FIG_DIR, RESULTS_FIG_DIR, REPORT_FIG_DIR]:
    if not os.path.exists(d):
        os.makedirs(d)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

# Stage meshes into 272_f1831_matched_donor_experiment
for sub in ["case1", "case2", "case3", "case5"]:
    p = os.path.join(BASE_DIR, sub)
    if not os.path.exists(p):
        os.makedirs(p)

src_c1 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_F1812_CASE_1_ADAPT_PHYS.inp")
dst_c1 = os.path.join(BASE_DIR, "case1", "PK_F1831_CASE_1_PHYS.inp")
if os.path.exists(src_c1) and not os.path.exists(dst_c1):
    shutil.copyfile(src_c1, dst_c1)

src_c2_a1 = os.path.join(REPO_ROOT, "scratch", "test_c2_single_state", "PK_C2_SINGLE_DIRECT_PHYS.inp")
dst_c2_a1 = os.path.join(BASE_DIR, "case2", "PK_F1831_CASE_2_A1_PHYS.inp")
if os.path.exists(src_c2_a1) and not os.path.exists(dst_c2_a1):
    shutil.copyfile(src_c2_a1, dst_c2_a1)

src_c2_a2 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case2", "PK_F1812_CASE_2_ADAPT_PHYS.inp")
dst_c2_a2 = os.path.join(BASE_DIR, "case2", "PK_F1831_CASE_2_PHYS.inp")
if os.path.exists(src_c2_a2) and not os.path.exists(dst_c2_a2):
    shutil.copyfile(src_c2_a2, dst_c2_a2)

src_c3_a1 = os.path.join(REPO_ROOT, "scratch", "test_c3_single_state", "PK_C3_SINGLE_DIRECT_PHYS.inp")
dst_c3_a1 = os.path.join(BASE_DIR, "case3", "PK_F1831_CASE_3_A1_PHYS.inp")
if os.path.exists(src_c3_a1) and not os.path.exists(dst_c3_a1):
    shutil.copyfile(src_c3_a1, dst_c3_a1)

src_c3_a2 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case3", "PK_F1812_CASE_3_ADAPT_PHYS.inp")
dst_c3_a2 = os.path.join(BASE_DIR, "case3", "PK_F1831_CASE_3_PHYS.inp")
if os.path.exists(src_c3_a2) and not os.path.exists(dst_c3_a2):
    shutil.copyfile(src_c3_a2, dst_c3_a2)

src_c5 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case5", "PK_F1812_CASE_5_ADAPT_PHYS.inp")
dst_c5 = os.path.join(BASE_DIR, "case5", "PK_F1831_CASE_5_PHYS.inp")
if os.path.exists(src_c5) and not os.path.exists(dst_c5):
    shutil.copyfile(src_c5, dst_c5)

CASES = [
    {
        "id": "case_1",
        "num": "Case 1",
        "title": "Case 1: Edge-Cracked Plate (eta_R = 4.5%)\nMulti-State Recovery: 25,461 el, 97.19% Ligament",
        "inp_path": dst_c1,
        "l0": 0.0075,
        "xlim": (-0.02, 1.02),
        "ylim": (-0.02, 1.02),
        "aspect": "equal"
    },
    {
        "id": "case_2",
        "num": "Case 2",
        "title": "Case 2: Off-Axis Hole (eta_R = 4.0%)\nA.1 Single: 13.6k (43.7% Distal) | A.2 Multi: 41.4k (99.9%)",
        "inp_path": dst_c2_a2,
        "l0": 0.0075,
        "xlim": (-0.02, 1.02),
        "ylim": (-0.02, 1.02),
        "aspect": "equal"
    },
    {
        "id": "case_3",
        "num": "Case 3",
        "title": "Case 3: Notched Plate w/ Pins (eta_R = 3.0%)\nA.1 Single: 44.5k (42.8% Sec) | A.2 Multi: 77.8k (93.8%)",
        "inp_path": dst_c3_a2,
        "l0": 0.285,
        "xlim": (-2.0, 67.0),
        "ylim": (-2.0, 122.0),
        "aspect": "equal"
    },
    {
        "id": "case_5",
        "num": "Case 5",
        "title": "Case 5: Seven-Hole Plate (eta_R = 5.68%)\nMatched Donor: 15,466 el, 97.41% Inter-Hole",
        "inp_path": dst_c5,
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
    ax.grid(True, linestyle=":", alpha=0.5, color="#94a3b8")

def generate_all():
    print("Generating standalone mesh figures...")
    for c in CASES:
        cid = c["id"]
        inp = c["inp_path"]
        print("  Rendering %s from %s..." % (cid, inp))
        nodes, elements = parse_inp_mesh(inp)

        fig, ax = plt.subplots(figsize=(7, 7))
        render_mesh_on_ax(ax, nodes, elements, c["title"], edge_lw=0.12)
        ax.set_xlim(c["xlim"])
        ax.set_ylim(c["ylim"])
        ax.set_aspect(c["aspect"])
        plt.tight_layout()

        png_p1 = os.path.join(OUT_FIG_DIR, "fig_f1831_%s_mesh.png" % cid)
        pdf_p1 = os.path.join(OUT_FIG_DIR, "fig_f1831_%s_mesh.pdf" % cid)
        png_p2 = os.path.join(RESULTS_FIG_DIR, "fig_f1831_%s_matched_mesh.png" % cid)
        pdf_p2 = os.path.join(RESULTS_FIG_DIR, "fig_f1831_%s_matched_mesh.pdf" % cid)

        fig.savefig(png_p1, dpi=300)
        fig.savefig(pdf_p1)
        fig.savefig(png_p2, dpi=300)
        fig.savefig(pdf_p2)
        plt.close(fig)

    print("Generating 4-panel publication composite...")
    fig, axes = plt.subplots(2, 2, figsize=(14, 14))
    axes = axes.flatten()

    for idx, c in enumerate(CASES):
        ax = axes[idx]
        nodes, elements = parse_inp_mesh(c["inp_path"])
        panel_label = "(%s)" % chr(97 + idx)
        title = "%s %s" % (panel_label, c["title"])
        render_mesh_on_ax(ax, nodes, elements, title, edge_lw=0.10)
        ax.set_xlim(c["xlim"])
        ax.set_ylim(c["ylim"])
        ax.set_aspect(c["aspect"])

    plt.suptitle("Task F1831: Four-Benchmark Matched Donor Sizing & Resolution Synthesis", fontsize=13, fontweight="bold", y=0.995)
    plt.tight_layout()

    comp_png1 = os.path.join(OUT_FIG_DIR, "fig_f1831_matched_donor_synthesis.png")
    comp_pdf1 = os.path.join(OUT_FIG_DIR, "fig_f1831_matched_donor_synthesis.pdf")
    comp_png2 = os.path.join(RESULTS_FIG_DIR, "fig_f1831_matched_donor_synthesis.png")
    comp_pdf2 = os.path.join(RESULTS_FIG_DIR, "fig_f1831_matched_donor_synthesis.pdf")
    comp_pdf3 = os.path.join(REPORT_FIG_DIR, "fig_f1831_matched_donor_synthesis.pdf")

    fig.savefig(comp_png1, dpi=300)
    fig.savefig(comp_pdf1)
    fig.savefig(comp_png2, dpi=300)
    fig.savefig(comp_pdf2)
    fig.savefig(comp_pdf3)
    plt.close(fig)
    print("Figures successfully generated!")

if __name__ == "__main__":
    generate_all()
