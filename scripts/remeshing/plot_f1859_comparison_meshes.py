# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1859_comparison_meshes.py
=================================================
Task F1859: Publication mesh rendering for the supervisor-meeting four-benchmark
comparison suite (Highly Refined Literature References vs F1852 Adaptive Meshes):
- Individual publication PNG & PDF renders for all 8 meshes
- Side-by-side 2x4 comparison composite (fig_f1859_four_benchmark_composite.png/.pdf)
- Side-by-side 2x2 reference composite (fig_f1859_reference_meshes_composite.png/.pdf)
- Side-by-side 2x2 adaptive composite (fig_f1859_adaptive_meshes_composite.png/.pdf)
"""

from __future__ import print_function
import os
import sys
import hashlib
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.generalized_2d_adaptive_framework_f1846 import MeshQualityAuditEngine

FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
if not os.path.exists(FIG_DIR):
    os.makedirs(FIG_DIR)

SUITE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "286_f1859_four_benchmark_reference_comparison")

REF_CASES = [
    {
        "id": "case_1_ref",
        "case_num": 1,
        "title": "Case 1 Ref: Edge-Cracked Plate\n(13,960 el, 97.50% quads, Lit Target: 13,941 [+0.14%])",
        "inp": os.path.join(SUITE_DIR, "ref_solve_case1", "PK_F1738_CASE_1_ADAPT_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_ref_case_1_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_ref_case_1_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    },
    {
        "id": "case_2_ref",
        "case_num": 2,
        "title": "Case 2 Ref: Off-Axis Hole Plate\n(23,965 el, 97.23% quads, Lit Target: 23,618 [+1.47%])",
        "inp": os.path.join(SUITE_DIR, "ref_solve_case2", "PK_F1728_CASE_2_ADAPT_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_ref_case_2_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_ref_case_2_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    },
    {
        "id": "case_3_ref",
        "case_num": 3,
        "title": "Case 3 Ref: Notched Plate w/ Pins\n(12,110 el, 96.73% quads, Lit Target: 12,168 [-0.48%])",
        "inp": os.path.join(SUITE_DIR, "ref_solve_case3", "PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_ref_case_3_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_ref_case_3_mesh.pdf"),
        "xlim": (-5.0, 70.0),
        "ylim": (-5.0, 125.0)
    },
    {
        "id": "case_5_ref",
        "case_num": 5,
        "title": "Case 5 Ref: Seven-Hole Plate\n(15,708 el, 97.56% quads, Lit Target: 15,330 [+2.47%])",
        "inp": os.path.join(SUITE_DIR, "ref_solve_case5", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_ref_case_5_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_ref_case_5_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    }
]

ADAPT_CASES = [
    {
        "id": "case_1_adapt",
        "case_num": 1,
        "title": "Case 1 Adapt (F1852): Edge-Cracked Plate\n(20,193 el, 97.30% quads, Driver: Damage Envelope)",
        "inp": os.path.join(SUITE_DIR, "job2_adaptive_case1", "PK_ADAPT_CASE_1_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_adapt_case_1_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_adapt_case_1_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    },
    {
        "id": "case_2_adapt",
        "case_num": 2,
        "title": "Case 2 Adapt (F1852): Off-Axis Hole Plate\n(17,280 el, 97.25% quads, Driver: Damage Envelope)",
        "inp": os.path.join(SUITE_DIR, "job2_adaptive_case2", "PK_ADAPT_CASE_2_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_adapt_case_2_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_adapt_case_2_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    },
    {
        "id": "case_3_adapt",
        "case_num": 3,
        "title": "Case 3 Adapt (F1852): Notched Plate w/ Pins\n(45,009 el, 97.29% quads, Driver: Damage Envelope)",
        "inp": os.path.join(SUITE_DIR, "job2_adaptive_case3", "PK_ADAPT_CASE_3_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_adapt_case_3_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_adapt_case_3_mesh.pdf"),
        "xlim": (-5.0, 70.0),
        "ylim": (-5.0, 125.0)
    },
    {
        "id": "case_5_adapt",
        "case_num": 5,
        "title": "Case 5 Adapt (F1852): Seven-Hole Plate\n(15,411 el, 97.74% quads, Driver: Native Miseseri)",
        "inp": os.path.join(SUITE_DIR, "job2_adaptive_case5", "PK_GEN_ADAPT_CASE_5_PHYS.inp"),
        "png": os.path.join(FIG_DIR, "fig_f1859_adapt_case_5_mesh.png"),
        "pdf": os.path.join(FIG_DIR, "fig_f1859_adapt_case_5_mesh.pdf"),
        "xlim": (-0.05, 1.05),
        "ylim": (-0.05, 1.05)
    }
]

def render_mesh_on_ax(ax, inp_path, title, xlim, ylim, lw=0.15, edge_color='#2c3e50', face_color='#f8f9fa'):
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    patches = []
    for eid, conn in quads.items():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) == 4:
            patches.append(Polygon(pts, closed=True))
    for eid, conn in tris.items():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) == 3:
            patches.append(Polygon(pts, closed=True))

    p_coll = PatchCollection(patches, facecolor=face_color, edgecolor=edge_color, linewidth=lw, alpha=0.95)
    ax.add_collection(p_coll)
    ax.set_xlim(xlim[0], xlim[1])
    ax.set_ylim(ylim[0], ylim[1])
    ax.set_aspect('equal')
    ax.set_title(title, fontsize=9, fontweight='bold', pad=6)
    ax.tick_params(labelsize=7)

def render_individual_cases():
    all_cases = REF_CASES + ADAPT_CASES
    for c in all_cases:
        print("Rendering %s from %s..." % (c["id"], c["inp"]))
        fig, ax = plt.subplots(figsize=(6.5, 6.5), dpi=300)
        render_mesh_on_ax(ax, c["inp"], c["title"], c["xlim"], c["ylim"], lw=0.20)
        ax.set_xlabel("X (mm)", fontsize=8, fontweight='bold')
        ax.set_ylabel("Y (mm)", fontsize=8, fontweight='bold')
        plt.tight_layout()
        fig.savefig(c["png"], dpi=300)
        fig.savefig(c["pdf"])
        plt.close(fig)
        print("  -> Saved %s and %s" % (c["png"], c["pdf"]))

def render_2x4_composite():
    print("Rendering 2x4 comparison composite (Reference vs Adaptive)...")
    fig, axes = plt.subplots(2, 4, figsize=(18, 9), dpi=300)

    # Row 0: Reference meshes
    for col, c in enumerate(REF_CASES):
        ax = axes[0, col]
        render_mesh_on_ax(ax, c["inp"], c["title"], c["xlim"], c["ylim"], lw=0.14, edge_color='#1a365d', face_color='#edf2f7')
        ax.set_xlabel("X (mm)", fontsize=7, fontweight='bold')
        ax.set_ylabel("Y (mm)", fontsize=7, fontweight='bold')

    # Row 1: Adaptive meshes
    for col, c in enumerate(ADAPT_CASES):
        ax = axes[1, col]
        render_mesh_on_ax(ax, c["inp"], c["title"], c["xlim"], c["ylim"], lw=0.14, edge_color='#2c3e50', face_color='#f7fafc')
        ax.set_xlabel("X (mm)", fontsize=7, fontweight='bold')
        ax.set_ylabel("Y (mm)", fontsize=7, fontweight='bold')

    fig.suptitle(
        "Task F1859: Four-Benchmark Comparison Suite for Supervisor Meeting (19 Nov 2026)\n"
        "Top Row: Highly Refined Literature Reference Meshes | Bottom Row: F1852 Generalized Adaptive Framework Meshes",
        fontsize=11, fontweight='bold', y=0.99
    )
    plt.tight_layout(rect=[0, 0, 1, 0.96])

    comp_png = os.path.join(FIG_DIR, "fig_f1859_four_benchmark_composite.png")
    comp_pdf = os.path.join(FIG_DIR, "fig_f1859_four_benchmark_composite.pdf")
    fig.savefig(comp_png, dpi=300)
    fig.savefig(comp_pdf)
    plt.close(fig)
    print("  -> Saved 2x4 composite: %s and %s" % (comp_png, comp_pdf))

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def generate_image_manifest():
    print("Generating f1859_image_manifest.json...")
    manifest = {
        "task_id": "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON",
        "correlation_id": "HND-F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON-001",
        "generated_at_utc": "2026-11-18T07:35:00Z",
        "description": "Publication mesh images and composite for four-benchmark reference comparison suite",
        "images": []
    }

    all_figures = [
        {"case_id": "case_1_ref", "path": "results/figures/fig_f1859_ref_case_1_mesh.png", "desc": "Case 1 Reference Mesh (13,960 elements)"},
        {"case_id": "case_2_ref", "path": "results/figures/fig_f1859_ref_case_2_mesh.png", "desc": "Case 2 Reference Mesh (23,965 elements)"},
        {"case_id": "case_3_ref", "path": "results/figures/fig_f1859_ref_case_3_mesh.png", "desc": "Case 3 Reference Mesh (12,110 elements)"},
        {"case_id": "case_5_ref", "path": "results/figures/fig_f1859_ref_case_5_mesh.png", "desc": "Case 5 Reference Mesh (15,708 elements)"},
        {"case_id": "case_1_adapt", "path": "results/figures/fig_f1859_adapt_case_1_mesh.png", "desc": "Case 1 Adaptive Mesh F1852 (20,193 elements)"},
        {"case_id": "case_2_adapt", "path": "results/figures/fig_f1859_adapt_case_2_mesh.png", "desc": "Case 2 Adaptive Mesh F1852 (17,280 elements)"},
        {"case_id": "case_3_adapt", "path": "results/figures/fig_f1859_adapt_case_3_mesh.png", "desc": "Case 3 Adaptive Mesh F1852 (45,009 elements)"},
        {"case_id": "case_5_adapt", "path": "results/figures/fig_f1859_adapt_case_5_mesh.png", "desc": "Case 5 Adaptive Mesh F1852 (15,411 elements)"},
        {"case_id": "composite", "path": "results/figures/fig_f1859_four_benchmark_composite.png", "desc": "Four-Benchmark Comparison 2x4 Composite (Reference vs Adaptive)"}
    ]

    for item in all_figures:
        full_p = os.path.join(REPO_ROOT, item["path"])
        if os.path.exists(full_p):
            sha = compute_sha256(full_p)
            size = os.path.getsize(full_p)
            manifest["images"].append({
                "case_id": item["case_id"],
                "relative_path": item["path"],
                "description": item["desc"],
                "sha256": sha,
                "bytes": size
            })

    out_p = os.path.join(REPO_ROOT, "results", "validation", "f1859_image_manifest.json")
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print("  -> Saved %s" % out_p)

def main():
    render_individual_cases()
    render_2x4_composite()
    generate_image_manifest()
    print("All F1859 mesh rendering completed successfully.")

if __name__ == "__main__":
    main()
