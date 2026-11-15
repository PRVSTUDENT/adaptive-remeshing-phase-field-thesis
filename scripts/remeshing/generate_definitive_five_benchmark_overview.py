# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_definitive_five_benchmark_overview.py

Generates the definitive publication-quality 5-benchmark overview figure for Master Thesis:
- Case 1: Mode-I Single-Edge Notched Plate (F1738 13,960 el, fully severed F1739)
- Case 2: Plate with an Off-Axis Hole (F1734 23,965 el, hole-breach F1752/F1753)
- Case 3: Rectangular Notched Plate with Hole and Pins (F1692/F1727 12,110 el, F1748 damage recovery)
- Case 4: Five-Hole Plate (F1725 13,017 el, 100% ligament compliance, F1759 preflight Exit 0)
- Case 5: Seven-Hole Plate (F1726 15,708 el, upper ligament selective refinement)

Features:
- Clean layout with zero overlapping text or clipping
- Physical element counts and exact parity vs published
- Clear status and physical fracture progress
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp, compute_element_metrics

BENCHMARK_SPECS = [
    {
        "key": "case_1",
        "title": "(a) Case 1: Mode-I Single-Edge Notched Plate",
        "subtitle": "Pandey & Kumar (2025) Sec. 4.1 | Task F1738 & F1739",
        "mesh_path": "models/pandey_kumar_mode1/226_f1738_case1_ligament_refinement/PK_F1738_CASE_1_ADAPT_PHYS.inp",
        "ell_0": 0.0075,
        "pub_elems": 13941,
        "status_line": "Status: SOLVED & VALIDATED (Complete Ligament Separation)",
        "detail_line": "Job 1423321: 2,050 inc, 99.96% load drop, 100% ligament resolved"
    },
    {
        "key": "case_2",
        "title": "(b) Case 2: Plate with an Off-Axis Hole",
        "subtitle": "Pandey & Kumar (2025) Sec. 4.4 | Tasks F1734, F1752 & F1753",
        "mesh_path": "models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_ADAPT_PHYS.inp",
        "ell_0": 0.0075,
        "pub_elems": 23618,
        "status_line": "Status: HOLE BREACH COMPLETE (Documented Distal Boundary Stall)",
        "detail_line": "Jobs 1423266/1423552: 255 inc, 59.9% load drop, crack severed to hole"
    },
    {
        "key": "case_3",
        "title": "(c) Case 3: Rectangular Notched Plate with Hole and Pins",
        "subtitle": "Pandey & Kumar (2025) Sec. 4.3 | Tasks 192, F1727 & F1748",
        "mesh_path": "models/pandey_kumar_mode1/192_pk_sec43_staggered_job1/PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp",
        "ell_0": 0.285,
        "pub_elems": 12168,
        "status_line": "Status: PARITY MATCHED (-0.48%) | NON-LINEAR DONOR REQUIRED",
        "detail_line": "Primary notch resolved; secondary path requires non-linear donor (F1748)"
    },
    {
        "key": "case_4",
        "title": "(d) Case 4: Five-Hole Plate",
        "subtitle": "Pandey & Kumar (2025) Sec. 4.5 | Tasks F1725 & F1759",
        "mesh_path": "models/pandey_kumar_mode1/217_f1725_physics_study/F1725_S2_COARSEN_ET315.inp",
        "ell_0": 0.008,
        "pub_elems": 12944,
        "status_line": "Status: SPATIAL MESH QUALIFIED | PRODUCTION PREFLIGHT COMPLETE",
        "detail_line": "100% area compliance (h <= l0) across Ligaments 2-4 | Datacheck EXIT 0"
    },
    {
        "key": "case_5",
        "title": "(e) Case 5: Seven-Hole Plate",
        "subtitle": "Pandey & Kumar (2025) Sec. 4.6 | Task F1726",
        "mesh_path": "models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp",
        "ell_0": 0.008,
        "pub_elems": 15714,
        "status_line": "Status: SPATIAL MESH QUALIFIED (-0.04% PARITY) | STAGED",
        "detail_line": "Upper ligament selectively refined (h <= l0) | Coarse donor verified"
    }
]

def build_poly_collection(nodes, elements, elem_types, values=None, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.10):
    verts = []
    vals = []
    elem_ids = sorted(elements.keys())
    for eid in elem_ids:
        nids = elements[eid]
        coords = np.array([nodes[nid] for nid in nids])
        verts.append(coords)
        if values is not None:
            vals.append(values.get(eid, 0.0))
            
    if values is not None:
        vals = np.array(vals)
        norm_vals = np.clip((vals - vmin) / (vmax - vmin) if vmax > vmin else vals, 0.0, 1.0)
        cmap = plt.get_cmap(cmap_name)
        colors = cmap(norm_vals)
        pc = PolyCollection(verts, facecolors=colors, edgecolors="black", linewidths=edge_lw)
    else:
        pc = PolyCollection(verts, facecolors="#e9ecef", edgecolors="black", linewidths=edge_lw)
    return pc

def main():
    fig = plt.figure(figsize=(18, 11), constrained_layout=False)
    # Define grid: 2 rows x 3 columns
    gs = fig.add_gridspec(2, 3, left=0.05, right=0.97, bottom=0.06, top=0.91, wspace=0.22, hspace=0.28)
    
    axes = []
    for r in range(2):
        for c in range(3):
            axes.append(fig.add_subplot(gs[r, c]))
            
    # Process the 5 benchmarks
    for idx, spec in enumerate(BENCHMARK_SPECS):
        ax = axes[idx]
        mesh_full_path = os.path.join(REPO_ROOT, spec["mesh_path"])
        nodes, elements, elem_types = parse_abaqus_inp(mesh_full_path)
        metrics = compute_element_metrics(nodes, elements, elem_types, spec["ell_0"])
        
        # Compute resolution ratios
        ratios = {}
        for eid, nids in elements.items():
            coords = np.array([nodes[nid] for nid in nids])
            x = coords[:, 0]
            y = coords[:, 1]
            a = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
            ratios[eid] = math.sqrt(a) / spec["ell_0"]
            
        pc = build_poly_collection(nodes, elements, elem_types, values=ratios, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.10)
        ax.add_collection(pc)
        
        bb = metrics["bounding_box"]
        dx = bb["x_max"] - bb["x_min"]
        dy = bb["y_max"] - bb["y_min"]
        ax.set_xlim(bb["x_min"] - 0.03 * dx, bb["x_max"] + 0.03 * dx)
        ax.set_ylim(bb["y_min"] - 0.03 * dy, bb["y_max"] + 0.03 * dy)
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]", fontsize=9.5)
        ax.set_ylabel("y [mm]", fontsize=9.5)
        ax.tick_params(labelsize=8.5)
        
        num_el = metrics["num_elements"]
        pub_el = spec["pub_elems"]
        parity = (num_el - pub_el) / pub_el * 100.0
        q_pct = metrics["quad_percentage"]
        min_h_um = metrics["element_size_stats_mm"]["min"] * 1e3
        h_l0_pct = metrics["compliance"]["h_le_ell0"]["count_pct"]
        
        title_str = (
            f"{spec['title']}\n"
            f"Authoritative: {num_el:,} el ({q_pct:.1f}% Q) | Published: {pub_el:,} el ({parity:+.2f}%)\n"
            f"$\\ell_0 = {spec['ell_0']}$ mm | $h_{{\\min}} = {min_h_um:.2f}\\,\\mu$m | $h \\leq \\ell_0$: {h_l0_pct:.1f}%"
        )
        ax.set_title(title_str, fontsize=9.5, fontweight="bold", pad=7)
        
        # Add status pill in lower left or upper left depending on geometry
        if spec["key"] == "case_3":
            # Place in open space
            ax.text(0.50, 0.04, spec["status_line"] + "\n" + spec["detail_line"],
                    transform=ax.transAxes, fontsize=7.2, fontweight="bold",
                    ha="center", va="bottom",
                    bbox=dict(boxstyle="square,pad=0.3", facecolor="#ffffff", edgecolor="#0d6efd", alpha=0.92))
        else:
            ax.text(0.50, 0.03, spec["status_line"] + "\n" + spec["detail_line"],
                    transform=ax.transAxes, fontsize=7.2, fontweight="bold",
                    ha="center", va="bottom",
                    bbox=dict(boxstyle="square,pad=0.3", facecolor="#ffffff", edgecolor="#198754" if "VALIDATED" in spec["status_line"] or "QUALIFIED" in spec["status_line"] or "BREACH" in spec["status_line"] else "#fd7e14", alpha=0.92))

    # Slot 6: Comprehensive Legend & Summary Table Panel
    ax_legend = axes[5]
    ax_legend.axis("off")
    
    # 1. Colorbar
    sm = plt.cm.ScalarMappable(cmap=plt.get_cmap("viridis_r"), norm=plt.Normalize(vmin=0.0, vmax=3.0))
    sm.set_array([])
    cax = ax_legend.inset_axes([0.08, 0.86, 0.84, 0.05])
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label(r"Spatial Resolution Ratio $h_e / \ell_0$ (Fine $\leq 1.0 \leq$ Coarse, Capped at 3.0)", fontsize=9.0, fontweight="bold")
    cb.ax.tick_params(labelsize=8.5)
    
    # 2. Structured benchmark summary text box (cleanly positioned below colorbar)
    summary_text = (
        "TASK F1737 / F1760: DEFINITIVE FIVE-BENCHMARK STATUS\n"
        "=================================================================\n"
        "Case 1 (Mode I Notch, Sec. 4.1):\n"
        "  - Mesh: 13,960 el (+0.14% vs 13,941 pub) | Task F1738\n"
        "  - Resolution: 100.0% area compliance (h <= l0/2) across ligament\n"
        "  - Fracture: 2,050 incs, 99.96% load drop, Exit 0 | VALIDATED\n"
        "-----------------------------------------------------------------\n"
        "Case 2 (Off-Axis Hole, Sec. 4.4):\n"
        "  - Mesh: 23,965 el (+1.47% vs 23,618 pub) | Task F1734\n"
        "  - Fracture: 255 incs, 59.9% load drop, severed into hole\n"
        "  - Status: Hole breach complete; distal stall at boundary\n"
        "-----------------------------------------------------------------\n"
        "Case 3 (Pins & Hole, Sec. 4.3):\n"
        "  - Mesh: 12,110 el (-0.48% vs 12,168 pub) | Baseline Parity\n"
        "  - Findings: Linear donor unrefined in secondary corridor;\n"
        "    authentic coupled damage donor recovered (Tasks F1748/F1756)\n"
        "-----------------------------------------------------------------\n"
        "Case 4 (Five-Hole Plate, Sec. 4.5):\n"
        "  - Mesh: 13,017 el (+0.56% vs 12,944 pub) | Task F1725\n"
        "  - Resolution: 100.0% area compliance across Ligaments 2, 3, 4\n"
        "  - Preflight: 3-layer deck built, cluster datacheck EXIT 0 (F1759)\n"
        "-----------------------------------------------------------------\n"
        "Case 5 (Seven-Hole Plate, Sec. 4.6):\n"
        "  - Mesh: 15,708 el (-0.04% vs 15,714 pub) | Task F1726\n"
        "  - Resolution: Upper ligament selectively refined (h <= l0)\n"
        "  - Status: Mesh parity matched, coarse donor verified\n"
        "=================================================================\n"
        "*Zero negative Jacobians across all 5 meshes (100% physically valid)."
    )
    
    ax_legend.text(0.08, 0.74, summary_text, transform=ax_legend.transAxes,
                   fontsize=7.6, verticalalignment="top", family="monospace",
                   bbox=dict(boxstyle="round,pad=0.5", facecolor="#f8f9fa", edgecolor="#495057", lw=1.2))
    
    fig.suptitle("Method A Error-Indicator Adaptive Remeshing: Definitive Five-Benchmark Synthesis\n"
                 "(Authentic Adapted Meshes, Spatial Resolution Metrics, and Fracture Validation Status)",
                 fontsize=13.5, fontweight="bold", y=0.97)
    
    out_dir = os.path.join(REPO_ROOT, "results", "figures")
    os.makedirs(out_dir, exist_ok=True)
    
    png_path = os.path.join(out_dir, "fig_f1760_five_benchmark_definitive_comparison.png")
    pdf_path = os.path.join(out_dir, "fig_f1760_five_benchmark_definitive_comparison.pdf")
    fig.savefig(png_path, dpi=300)
    fig.savefig(pdf_path)
    plt.close(fig)
    print(f"Definitive synthesis figure saved:\n  PNG: {png_path}\n  PDF: {pdf_path}")
    
    # Also update fig_f1736_five_case_comparison_corrected to overwrite the obsolete figure
    old_png = os.path.join(out_dir, "fig_f1736_five_case_comparison_corrected.png")
    old_pdf = os.path.join(out_dir, "fig_f1736_five_case_comparison_corrected.pdf")
    root_png = os.path.join(REPO_ROOT, "figures", "fig_f1736_five_case_comparison_corrected.png")
    
    import shutil
    shutil.copyfile(png_path, old_png)
    shutil.copyfile(pdf_path, old_pdf)
    shutil.copyfile(png_path, root_png)
    print("Synchronized with fig_f1736_five_case_comparison_corrected paths.")

if __name__ == "__main__":
    main()
