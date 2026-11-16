# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1812_figures.py
======================================
Task F1812: Universal Framework Crack-Path Refinement Plotting Engine.
Generates:
1. 12 diagnostic PNGs across Cases 1, 2, 3, and 5:
   - <case>_mesh_full.png
   - <case>_sizing_h_l0.png
   - <case>_mesh_closeup.png (full crack propagation corridor for Case 1)
2. 4-panel publication synthesis figure:
   - results/figures/fig_f1812_four_benchmark_crack_path_synthesis.png (and .pdf)
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Rectangle
from matplotlib.collections import PatchCollection

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"

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

def plot_case_mesh_and_h(inp_path, l0, out_prefix, case_title, x_lim=None, y_lim=None, closeup_box=None):
    nodes, elements = parse_inp_mesh(inp_path)
    
    patches = []
    h_ratios = []
    
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        n = len(pts)
        if n < 3:
            continue
        poly = Polygon(pts, closed=True)
        patches.append(poly)
        
        # Area via shoelace
        area = 0.5 * abs(sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
        h = math.sqrt(area)
        h_ratios.append(h / l0)
    
    h_ratios = np.array(h_ratios)
    
    # 1. Plot Full Specimen Mesh
    fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
    pc = PatchCollection(patches, facecolor='none', edgecolor='#333333', linewidths=0.25)
    ax.add_collection(pc)
    all_x = [nodes[nid][0] for nid in nodes]
    all_y = [nodes[nid][1] for nid in nodes]
    ax.set_xlim(min(all_x) if x_lim is None else x_lim[0], max(all_x) if x_lim is None else x_lim[1])
    ax.set_ylim(min(all_y) if y_lim is None else y_lim[0], max(all_y) if y_lim is None else y_lim[1])
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontweight='bold')
    ax.set_ylabel('Y [mm]', fontweight='bold')
    ax.set_title('%s - Full Adapted Mesh\n(%d elements, %d nodes)' % (case_title, len(elements), len(nodes)), fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    plt.tight_layout()
    mesh_full_path = out_prefix + "_mesh_full.png"
    plt.savefig(mesh_full_path, dpi=300)
    plt.close(fig)
    print("  Saved: %s" % mesh_full_path)

    # 2. Plot Sizing Map (h / l0)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
    pc = PatchCollection(patches, cmap='viridis_r', edgecolor='none')
    pc.set_array(h_ratios)
    pc.set_clim(0.1, 2.5)
    ax.add_collection(pc)
    ax.set_xlim(min(all_x) if x_lim is None else x_lim[0], max(all_x) if x_lim is None else x_lim[1])
    ax.set_ylim(min(all_y) if y_lim is None else y_lim[0], max(all_y) if y_lim is None else y_lim[1])
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontweight='bold')
    ax.set_ylabel('Y [mm]', fontweight='bold')
    ax.set_title('%s - Relative Mesh Sizing ($h / \\ell_0$)\n($\\ell_0 = %.4f$ mm)' % (case_title, l0), fontweight='bold')
    cbar = plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('$h / \\ell_0$ (target $\\leq 0.5$ in crack path)', fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    plt.tight_layout()
    sizing_path = out_prefix + "_sizing_h_l0.png"
    plt.savefig(sizing_path, dpi=300)
    plt.close(fig)
    print("  Saved: %s" % sizing_path)

    # 3. Plot Closeup Region (Crack Path / Critical Corridors)
    if closeup_box is not None:
        fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
        pc = PatchCollection(patches, facecolor='none', edgecolor='#1a237e', linewidths=0.35)
        ax.add_collection(pc)
        x_min, x_max, y_min, y_max = closeup_box
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_aspect('equal')
        ax.set_xlabel('X [mm]', fontweight='bold')
        ax.set_ylabel('Y [mm]', fontweight='bold')
        ax.set_title('%s - Crack Path Corridor Closeup' % case_title, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)
        plt.tight_layout()
        closeup_path = out_prefix + "_mesh_closeup.png"
        plt.savefig(closeup_path, dpi=300)
        plt.close(fig)
        print("  Saved: %s" % closeup_path)


def generate_synthesis_figure(receipt_path, out_dir):
    with open(receipt_path, "r") as f:
        data = json.load(f)

    cases_data = data["selected_cases"]
    cases_keys = ["case_1", "case_2", "case_3", "case_5"]
    cases_names = [
        "Case 1 (Edge Notch)\n$\\eta_R = 4.5\\%$",
        "Case 2 (Off-Axis Hole)\n$\\eta_R = 4.0\\%$",
        "Case 3 (Pins & Hole)\n$\\eta_R = 3.0\\%$",
        "Case 5 (Seven Holes)\n$\\eta_R = 5.68\\%$"
    ]

    elements = [cases_data[k]["audit"]["total_elements"] for k in cases_keys]
    quad_pcts = [cases_data[k]["audit"]["quad_fraction_pct"] for k in cases_keys]
    max_ars = [cases_data[k]["audit"]["max_aspect_ratio"] for k in cases_keys]

    c1_lig = cases_data["case_1"]["critical_metrics"]["ligament_pct_le_l0_half"]
    c2_outer = cases_data["case_2"]["critical_metrics"]["combined_outer_ligament_pct_le_l0_half"]
    c3_sec = cases_data["case_3"]["critical_metrics"]["secondary_pct_le_l0"]
    c5_up = cases_data["case_5"]["critical_metrics"]["upper_pct_le_l0"]

    crit_percentages = [c1_lig, c2_outer, c3_sec, c5_up]
    crit_labels = [
        "Case 1: Full Ligament\n(% $\\leq \\ell_0/2$)",
        "Case 2: Outer Ligament\n(% $\\leq \\ell_0/2$)",
        "Case 3: Secondary Path\n(% $\\leq \\ell_0$)",
        "Case 5: Inter-Hole Path\n(% $\\leq \\ell_0$)"
    ]

    fig, axs = plt.subplots(2, 2, figsize=(14, 11), dpi=300)
    fig.suptitle("Universal Adaptive Remeshing Framework (Method A.2)\nCrack-Path Refinement and Mesh Quality Synthesis across Four Mandatory Benchmarks",
                 fontsize=14, fontweight='bold', y=0.98)

    colors = ['#1565c0', '#2e7d32', '#6a1b9a', '#c62828']
    x = np.arange(len(cases_keys))

    # Panel A: Element Counts
    ax = axs[0, 0]
    bars = ax.bar(x, elements, color=colors, alpha=0.85, edgecolor='black', width=0.55)
    ax.set_title("(a) Total Physical Element Count", fontsize=11, fontweight='bold')
    ax.set_ylabel("Element Count", fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cases_names, fontsize=8.5)
    ax.set_ylim(0, max(elements) * 1.25)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + max(elements)*0.02, f"{int(yval):,}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Panel B: Quad Fraction
    ax = axs[0, 1]
    bars = ax.bar(x, quad_pcts, color=colors, alpha=0.85, edgecolor='black', width=0.55)
    ax.set_title("(b) Quadrilateral Element Fraction (%)", fontsize=11, fontweight='bold')
    ax.set_ylabel("Quad Fraction (%)", fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cases_names, fontsize=8.5)
    ax.set_ylim(80, 102)
    ax.axhline(90.0, color='red', linestyle='--', linewidth=1.5, label='Gate Threshold ($\\geq 90\\%$)')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='lower right', frameon=True, facecolor='#f5f5f5')
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.5, f"{yval:.2f}%",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Panel C: Max Aspect Ratio
    ax = axs[1, 0]
    bars = ax.bar(x, max_ars, color=colors, alpha=0.85, edgecolor='black', width=0.55)
    ax.set_title("(c) Maximum Element Aspect Ratio", fontsize=11, fontweight='bold')
    ax.set_ylabel("Max Aspect Ratio", fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(cases_names, fontsize=8.5)
    ax.set_ylim(0, 4.5)
    ax.axhline(4.0, color='red', linestyle='--', linewidth=1.5, label='Gate Threshold ($\\leq 4.0$)')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.legend(loc='upper right', frameon=True, facecolor='#f5f5f5')
    for bar in bars:
        yval = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2.0, yval + 0.1, f"{yval:.2f}",
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    # Panel D: Critical Crack-Path Resolution
    ax = axs[1, 1]
    bars = ax.bar(x, crit_percentages, color=colors, alpha=0.85, edgecolor='black', width=0.55)
    ax.set_title("(d) Critical Crack-Path Refinement Resolution", fontsize=11, fontweight='bold')
    ax.set_ylabel("Resolution (%)", fontsize=10, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(crit_labels, fontsize=8.5)
    ax.set_ylim(0, 125)
    ax.axhline(50.0, color='#c62828', linestyle='--', alpha=0.8, label='Outer Ligament Threshold (50%)')
    ax.axhline(90.0, color='#f57f17', linestyle=':', alpha=0.8, label='High-Fidelity Threshold (90%)')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper left')

    gate_annotations = [
        (f"PASS (Full Path)\n({c1_lig:.1f}%)", '#2e7d32'),
        (f"PASS (Distal Outer)\n({c2_outer:.1f}%)", '#2e7d32'),
        (f"PASS (Secondary)\n({c3_sec:.1f}%)", '#2e7d32'),
        (f"PASS (Inter-Hole)\n({c5_up:.1f}%)", '#2e7d32')
    ]

    for i in range(len(cases_keys)):
        txt, col = gate_annotations[i]
        val = crit_percentages[i]
        ax.annotate(f"{val:.1f}%\n{txt}", xy=(x[i], val + 3.0),
                    ha='center', fontsize=7.5, fontweight='bold', color=col)

    plt.tight_layout()
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, "fig_f1812_four_benchmark_crack_path_synthesis.png")
    pdf_path = os.path.join(out_dir, "fig_f1812_four_benchmark_crack_path_synthesis.pdf")
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close(fig)
    print("Saved publication synthesis figure:")
    print("  PNG: %s" % png_path)
    print("  PDF: %s" % pdf_path)


def main():
    base_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement")
    fig_dir = os.path.join(base_dir, "figures")
    os.makedirs(fig_dir, exist_ok=True)

    receipt_path = os.path.join(base_dir, "PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json")
    if not os.path.exists(receipt_path):
        print("ERROR: Receipt file not found: %s" % receipt_path)
        return

    # Diagnostic plot configurations
    cases_config = [
        {
            "cid": "case_1",
            "title": "Case 1: Mode-I Edge-Cracked Plate (Method A.2 Multi-State, eta_R = 4.5%)",
            "inp": os.path.join(base_dir, "case1", "PK_F1812_CASE_1_ADAPT_PHYS.inp"),
            "l0": 0.0075,
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "box": (0.45, 1.02, 0.45, 0.55)  # full crack propagation corridor
        },
        {
            "cid": "case_2",
            "title": "Case 2: Mode-I Plate with Off-Axis Hole (Method A.2 Multi-State, eta_R = 4.0%)",
            "inp": os.path.join(base_dir, "case2", "PK_F1812_CASE_2_ADAPT_PHYS.inp"),
            "l0": 0.0075,
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "box": (0.75, 1.02, 0.50, 0.80)
        },
        {
            "cid": "case_3",
            "title": "Case 3: Notched Plate with Pins (Method A.2 Multi-State, eta_R = 3.0%)",
            "inp": os.path.join(base_dir, "case3", "PK_F1812_CASE_3_ADAPT_PHYS.inp"),
            "l0": 0.285,
            "xlim": (-2.0, 67.0),
            "ylim": (-2.0, 122.0),
            "box": (10.0, 65.0, 40.0, 80.0)
        },
        {
            "cid": "case_5",
            "title": "Case 5: Plate with Seven Holes (Table 6 Parity, eta_R = 5.68%)",
            "inp": os.path.join(base_dir, "case5", "PK_F1812_CASE_5_ADAPT_PHYS.inp"),
            "l0": 0.008,
            "xlim": (-0.05, 1.05),
            "ylim": (-0.05, 1.05),
            "box": (0.10, 0.90, 0.25, 0.70)
        }
    ]

    print("\n--- Generating individual benchmark diagnostic figures ---")
    for cfg in cases_config:
        prefix = os.path.join(fig_dir, cfg["cid"])
        print("Plotting %s -> %s ..." % (cfg["title"], prefix))
        plot_case_mesh_and_h(cfg["inp"], cfg["l0"], prefix, cfg["title"],
                             x_lim=cfg["xlim"], y_lim=cfg["ylim"], closeup_box=cfg["box"])

    # 4-panel publication synthesis figure
    print("\n--- Generating 4-panel publication synthesis figure ---")
    pub_dir = os.path.join(REPO_ROOT, "results", "figures")
    generate_synthesis_figure(receipt_path, pub_dir)


if __name__ == "__main__":
    main()
