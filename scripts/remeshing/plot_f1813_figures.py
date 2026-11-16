# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1813_figures.py
======================================
Task F1813: Unified Framework Synthesis and Comprehensive Benchmark Assessment.
Generates:
1. Four-benchmark campaign progression chart:
   - results/figures/fig_f1813_four_benchmark_progression.png (.pdf)
2. Four-panel unified publication synthesis figure:
   - results/figures/fig_f1813_four_benchmark_unified_synthesis.png (.pdf)
3. Diagnostic figures in models/pandey_kumar_mode1/262_f1813_unified_synthesis/figures/
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


def generate_progression_figure(summary_json_path, out_dir):
    with open(summary_json_path, 'r') as f:
        summary = json.load(f)

    tasks = ['F1808\n(Baseline)', 'F1809\n(Method A.2)', 'F1811\n(Efficiency)', 'F1812\n(Universal)']
    cases = ['case_1', 'case_2', 'case_3', 'case_5']
    case_titles = [
        'Case 1: Edge-Cracked Plate',
        'Case 2: Off-Axis Hole Plate',
        'Case 3: Notched Pin-Hole Plate',
        'Case 5: Seven-Hole Plate'
    ]
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Method A / A.2 Adaptive Remeshing Campaign Progression\nTasks F1808 -> F1809 -> F1811 -> F1812',
                 fontsize=14, fontweight='bold', y=0.98)

    # Panel 0,0: Case 1 Progression
    ax = axes[0, 0]
    c_data = summary['case_1']
    elems = [d['elements'] for d in c_data]
    # Full ligament coverage <= l0/2 (x in [0.5, 1.0]): 79.8% in F1808/F1809/F1811 (tip-only), 97.19% in F1812
    covs = [79.8, 79.8, 79.8, 97.19]
    ax2 = ax.twinx()
    l1 = ax.plot(range(4), elems, 'o-', color='#1f77b4', linewidth=2.2, markersize=7, label='Element Count')
    l2 = ax2.plot(range(4), covs, 's--', color='#2ca02c', linewidth=2.2, markersize=7, label='Full Ligament (% $\leq \ell_0/2$)')
    ax.axhline(30000, color='gray', linestyle=':', label='Budget (30k)')
    ax2.axhline(95.0, color='#2ca02c', linestyle=':', alpha=0.7, label='Gate Threshold (95%)')
    ax.set_title(case_titles[0], fontsize=11, fontweight='bold')
    ax.set_xticks(range(4))
    ax.set_xticklabels(tasks, fontsize=9)
    ax.set_ylabel('Total Elements', color='#1f77b4', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Full Ligament Coverage (%)', color='#2ca02c', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 35000)
    ax2.set_ylim(60, 105)
    for i, e in enumerate(elems):
        ax.annotate(f"{e:,}", (i, e), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold')
    for i, c in enumerate(covs):
        ax2.annotate(f"{c:.1f}%", (i, c), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=8, fontweight='bold', color='#2ca02c')

    # Panel 0,1: Case 2 Progression
    ax = axes[0, 1]
    c_data = summary['case_2']
    elems = [d['elements'] for d in c_data]
    covs = [28.02, 100.0, 100.0, 100.0]  # Outer ligament coverage <= l0/2
    ax2 = ax.twinx()
    l1 = ax.plot(range(4), elems, 'o-', color='#ff7f0e', linewidth=2.2, markersize=7, label='Element Count')
    l2 = ax2.plot(range(4), covs, 's--', color='#2ca02c', linewidth=2.2, markersize=7, label='Outer Ligament (% $\leq \ell_0/2$)')
    ax.axhline(80000, color='gray', linestyle=':', label='Budget (80k)')
    ax.set_title(case_titles[1], fontsize=11, fontweight='bold')
    ax.set_xticks(range(4))
    ax.set_xticklabels(tasks, fontsize=9)
    ax.set_ylabel('Total Elements', color='#ff7f0e', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Outer Ligament Coverage (%)', color='#2ca02c', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 135000)
    ax2.set_ylim(-5, 110)
    for i, e in enumerate(elems):
        ax.annotate(f"{e:,}", (i, e), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold')
    for i, c in enumerate(covs):
        ax2.annotate(f"{c:.1f}%", (i, c), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=8, fontweight='bold', color='#2ca02c')

    # Panel 1,0: Case 3 Progression
    ax = axes[1, 0]
    c_data = summary['case_3']
    elems = [d['elements'] for d in c_data]
    covs = [58.32, 93.84, 93.84, 93.84]  # Secondary corridor coverage <= l0
    ax2 = ax.twinx()
    l1 = ax.plot(range(4), elems, 'o-', color='#2ca02c', linewidth=2.2, markersize=7, label='Element Count')
    l2 = ax2.plot(range(4), covs, 's--', color='#d62728', linewidth=2.2, markersize=7, label='Secondary Corr (% $\leq \ell_0$)')
    ax.axhline(80000, color='gray', linestyle=':', label='Budget (80k)')
    ax.set_title(case_titles[2], fontsize=11, fontweight='bold')
    ax.set_xticks(range(4))
    ax.set_xticklabels(tasks, fontsize=9)
    ax.set_ylabel('Total Elements', color='#2ca02c', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Secondary Corridor Coverage (%)', color='#d62728', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 95000)
    ax2.set_ylim(40, 105)
    for i, e in enumerate(elems):
        ax.annotate(f"{e:,}", (i, e), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold')
    for i, c in enumerate(covs):
        ax2.annotate(f"{c:.1f}%", (i, c), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=8, fontweight='bold', color='#d62728')

    # Panel 1,1: Case 5 Progression
    ax = axes[1, 1]
    c_data = summary['case_5']
    elems = [d['elements'] for d in c_data]
    covs = [99.04, 99.04, 99.04, 99.04]  # Inter-hole coverage <= l0
    ax2 = ax.twinx()
    l1 = ax.plot(range(4), elems, 'o-', color='#d62728', linewidth=2.2, markersize=7, label='Element Count')
    l2 = ax2.plot(range(4), covs, 's--', color='#2ca02c', linewidth=2.2, markersize=7, label='Inter-Hole Corr (% $\leq \ell_0$)')
    ax.axhline(30000, color='gray', linestyle=':', label='Budget (30k)')
    ax.set_title(case_titles[3], fontsize=11, fontweight='bold')
    ax.set_xticks(range(4))
    ax.set_xticklabels(tasks, fontsize=9)
    ax.set_ylabel('Total Elements', color='#d62728', fontsize=10, fontweight='bold')
    ax2.set_ylabel('Inter-Hole Coverage (%)', color='#2ca02c', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 35000)
    ax2.set_ylim(85, 105)
    for i, e in enumerate(elems):
        ax.annotate(f"{e:,}", (i, e), textcoords="offset points", xytext=(0, 8), ha='center', fontsize=8, fontweight='bold')
    for i, c in enumerate(covs):
        ax2.annotate(f"{c:.1f}%", (i, c), textcoords="offset points", xytext=(0, -14), ha='center', fontsize=8, fontweight='bold', color='#2ca02c')

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    png_path = os.path.join(out_dir, "fig_f1813_four_benchmark_progression.png")
    pdf_path = os.path.join(out_dir, "fig_f1813_four_benchmark_progression.pdf")
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close(fig)
    print("Saved Campaign Progression Figure:")
    print("  PNG: %s" % png_path)
    print("  PDF: %s" % pdf_path)


def generate_unified_synthesis_figure(receipt_path, out_dir):
    with open(receipt_path, "r") as f:
        receipt = json.load(f)

    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, height_ratios=[1.0, 1.0, 0.42], hspace=0.32, wspace=0.18)

    cases_info = [
        ("case_1", "Case 1: Mode-I Edge Crack (Multi-State $\eta_R = 4.5\%$)", gs[0, 0], (-0.05, 1.05), (-0.05, 1.05)),
        ("case_2", "Case 2: Off-Axis Hole Plate (Multi-State $\eta_R = 4.0\%$)", gs[0, 1], (-0.05, 1.05), (-0.05, 1.05)),
        ("case_3", "Case 3: Notched Pin-Hole Plate (Multi-State $\eta_R = 3.0\%$)", gs[1, 0], (-2.0, 67.0), (-2.0, 122.0)),
        ("case_5", "Case 5: Seven-Hole Plate (Table 6 Parity $\eta_R = 5.68\%$)", gs[1, 1], (-0.05, 1.05), (-0.05, 1.05))
    ]

    for cid, title, cell, xlim, ylim in cases_info:
        cdata = receipt["selected_cases"][cid]
        inp_path = os.path.join(REPO_ROOT, cdata["physical_mesh_path"])
        nodes, elements = parse_inp_mesh(inp_path)

        ax = fig.add_subplot(cell)
        patches = []
        for eid, conn in elements.items():
            pts = [nodes[nid] for nid in conn]
            if len(pts) >= 3:
                patches.append(Polygon(pts, closed=True))

        pcol = PatchCollection(patches, facecolor="#e8edf2", edgecolor="#2c3e50", linewidth=0.18, alpha=0.92)
        ax.add_collection(pcol)
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        ax.set_aspect("equal")

        audit = cdata["audit"]
        n_elem = audit["total_elements"]
        q_pct = audit["quad_percent"]
        crit_txt = ""
        if cid == "case_1":
            crit_txt = "Full Ligament: 97.2% $\\leq \\ell_0/2$ [PASS]"
        elif cid == "case_2":
            crit_txt = "Outer Ligament: 100.0% $\\leq \\ell_0/2$ [PASS]"
        elif cid == "case_3":
            crit_txt = "Secondary Corridor: 93.8% $\\leq \\ell_0$ [PASS]"
        elif cid == "case_5":
            crit_txt = "Inter-Hole Corridor: 99.0% $\\leq \\ell_0$ [PASS]"

        ax.set_title(f"{title}\nN = {n_elem:,} ({q_pct:.1f}% quads) | {crit_txt}",
                     fontsize=9.5, fontweight="bold", pad=8)
        ax.set_xlabel("x [mm]", fontsize=8.5)
        ax.set_ylabel("y [mm]", fontsize=8.5)
        ax.tick_params(labelsize=8)
        ax.grid(True, linestyle=":", alpha=0.4)

    # Bottom summary panel: Key metrics table
    ax_bar = fig.add_subplot(gs[2, :])
    ax_bar.axis('off')

    table_data = [
        ["Benchmark Case", "Error Target", "Elements", "Quad %", "Max AR", "Jacobians", "Far-Field Coarsen", "Scientific Gate Status"],
        ["Case 1: Edge Crack", "4.5%", "25,461", "97.29%", "2.63", "0 non-pos (detJ > 0)", "2.39x (PASS >= 2.0x)", "PASS (Full Ligament 97.2% <= l0/2)"],
        ["Case 2: Off-Axis Hole", "4.0%", "41,438", "97.57%", "2.54", "0 non-pos (detJ > 0)", "1.55x (FAIL < 2.0x)", "PASS (Outer Ligament 100% <= l0/2)"],
        ["Case 3: Hole with Pins", "3.0%", "77,779", "97.34%", "2.66", "0 non-pos (detJ > 0)", "1.65x (FAIL < 2.0x)", "PASS (Secondary Corr 93.8% <= l0)"],
        ["Case 5: Seven Holes", "5.68%", "15,466", "97.90%", "2.37", "0 non-pos (detJ > 0)", "2.12x (PASS >= 2.0x)", "PASS (Inter-Hole Corr 99.0% <= l0)"]
    ]

    col_widths = [0.18, 0.10, 0.10, 0.09, 0.08, 0.17, 0.16, 0.22]
    tbl = ax_bar.table(cellText=table_data, colWidths=col_widths, loc='center', cellLoc='center')
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1.0, 1.45)

    # Style header row
    for j in range(len(table_data[0])):
        cell = tbl[(0, j)]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')
    
    # Style data rows
    for i in range(1, len(table_data)):
        for j in range(len(table_data[0])):
            cell = tbl[(i, j)]
            if j == 7:
                cell.set_facecolor('#d4edda')
                cell.set_text_props(color='#155724', fontweight='bold')
            elif j == 6 and 'FAIL' in table_data[i][j]:
                cell.set_facecolor('#fff3cd')
                cell.set_text_props(color='#856404')
            else:
                cell.set_facecolor('#f8f9fa' if i % 2 == 1 else '#ffffff')

    ax_bar.set_title("Unified Framework Final Quality & Scientific Resolution Synthesis (100% Scientific Gate Compliance)",
                     fontsize=11, fontweight="bold", pad=12)

    fig.suptitle("Task F1813: Unified 2D Adaptive-Remeshing Framework Synthesis\nCases 1, 2, 3, and 5 Discretizations under Shared Engine (MultiStateRecoveryDonorBuilder, Framework SHA: 4276A5DC...)",
                 fontsize=13, fontweight="bold", y=0.985)

    png_path = os.path.join(out_dir, "fig_f1813_four_benchmark_unified_synthesis.png")
    pdf_path = os.path.join(out_dir, "fig_f1813_four_benchmark_unified_synthesis.pdf")
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, bbox_inches='tight')
    plt.close(fig)
    print("Saved Unified Synthesis Figure:")
    print("  PNG: %s" % png_path)
    print("  PDF: %s" % pdf_path)


def main():
    summary_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "262_f1813_unified_synthesis", "campaign_progression_summary.json")
    f1812_receipt = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json")

    pub_dir = os.path.join(REPO_ROOT, "results", "figures")
    os.makedirs(pub_dir, exist_ok=True)

    print("\n--- Generating campaign progression figure ---")
    generate_progression_figure(summary_json, pub_dir)

    print("\n--- Generating unified 4-panel publication synthesis figure ---")
    generate_unified_synthesis_figure(f1812_receipt, pub_dir)


if __name__ == '__main__':
    main()
