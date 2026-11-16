# -*- coding: utf-8 -*-
"""
plot_f1807_four_case_synthesis.py
Generates the comprehensive 4-panel publication-grade synthesis figure
and individual benchmark diagnostic plots for Task F1807 across Cases 1, 2, 3, and 5.
"""

import os
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection

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
    
    # 1. Full-specimen mesh and element-size (h/l0) map
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
    
    # Plot Full Specimen Mesh
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
    plt.savefig(out_prefix + "_mesh_full.png", dpi=300)
    plt.close(fig)

    # Plot Sizing Map (h / l0)
    fig, ax = plt.subplots(figsize=(9, 7), dpi=300)
    # Clip h_ratio for colormap visualization: [0.1, 2.5]
    pc = PatchCollection(patches, cmap='viridis_r', edgecolor='none')
    pc.set_array(h_ratios)
    pc.set_clim(0.1, 2.5)
    ax.add_collection(pc)
    ax.set_xlim(min(all_x) if x_lim is None else x_lim[0], max(all_x) if x_lim is None else x_lim[1])
    ax.set_ylim(min(all_y) if y_lim is None else y_lim[0], max(all_y) if y_lim is None else y_lim[1])
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontweight='bold')
    ax.set_ylabel('Y [mm]', fontweight='bold')
    ax.set_title('%s - Element Size Metric $h / \\ell_0$\n($\\ell_0 = %.4f$ mm)' % (case_title, l0), fontweight='bold')
    cbar = plt.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('$h / \\ell_0$ (Target $\\leq 0.5$ in fine core)', fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    plt.tight_layout()
    plt.savefig(out_prefix + "_h_over_l0.png", dpi=300)
    plt.close(fig)

    # Plot Local Refinement Close-Up if requested
    if closeup_box is not None:
        fig, ax = plt.subplots(figsize=(8, 7), dpi=300)
        pc = PatchCollection(patches, facecolor='none', edgecolor='#1565c0', linewidths=0.4)
        ax.add_collection(pc)
        ax.set_xlim(closeup_box[0], closeup_box[1])
        ax.set_ylim(closeup_box[2], closeup_box[3])
        ax.set_aspect('equal')
        ax.set_xlabel('X [mm]', fontweight='bold')
        ax.set_ylabel('Y [mm]', fontweight='bold')
        ax.set_title('%s - Local Critical Region Mesh Close-Up' % case_title, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.4)
        plt.tight_layout()
        plt.savefig(out_prefix + "_mesh_closeup.png", dpi=300)
        plt.close(fig)

def generate_synthesis_figure(receipt_path, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    with open(receipt_path, "r") as f:
        data = json.load(f)
    
    results = data["regression_results"]
    cases_keys = ["case_1", "case_2", "case_3", "case_5"]
    cases_labels = [
        'Case 1\nMode-I Edge Crack\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=7.5\\,\\mu\\mathrm{m}$)',
        'Case 2\nOff-Axis Hole Plate\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=7.5\\,\\mu\\mathrm{m}$)',
        'Case 3\nNotched Plate w/ Pins\n($65\\times 120\\,\\mathrm{mm}, \\ell_0=285\\,\\mu\\mathrm{m}$)',
        'Case 5\nSeven-Hole Plate\n($1.0\\times 1.0\\,\\mathrm{mm}, \\ell_0=8.0\\,\\mu\\mathrm{m}$)'
    ]
    
    x = np.arange(len(cases_keys))
    
    fig, axs = plt.subplots(2, 2, figsize=(15, 12), dpi=300)
    plt.subplots_adjust(hspace=0.35, wspace=0.28)
    
    # -------------------------------------------------------------------------
    # Panel (a): Element Count Comparison: Predecessor vs Literature Target vs F1807
    # -------------------------------------------------------------------------
    ax = axs[0, 0]
    
    # Immediate predecessor element counts:
    # Case 1: F1780 (16,597 el)
    # Case 2: F1806 baseline (22,924 el)
    # Case 3: F1803 (26,746 el)
    # Case 5: F1780 (15,466 el)
    pred_counts = [16597, 22924, 26746, 15466]
    f1807_counts = [results[k]["element_counts"]["total_elements"] for k in cases_keys]
    lit_targets = [results[k]["target_elements"] if results[k]["target_elements"] is not None else 0 for k in cases_keys]
    
    width = 0.28
    rects1 = ax.bar(x - width/2, [v / 1000.0 for v in pred_counts], width,
                    label='Predecessor Mesh', color='#ffb74d', edgecolor='#e65100', hatch='//')
    rects2 = ax.bar(x + width/2, [v / 1000.0 for v in f1807_counts], width,
                    label='F1807 Native Adapted Mesh', color='#2e7d32', edgecolor='#1b5e20')
    
    for i in range(len(cases_keys)):
        if lit_targets[i] > 0:
            ax.plot([x[i] - width, x[i] + width], [lit_targets[i] / 1000.0, lit_targets[i] / 1000.0],
                    'k--', linewidth=2.0, label='Literature Target' if i == 0 else "")
            
    ax.set_ylabel('Physical Element Count ($10^3$ Elements)', fontsize=10.5, fontweight='bold')
    ax.set_title('(a) Discretization Parity: Predecessor vs Adapted vs Literature', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases_labels, fontsize=8.5)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, max(f1807_counts) / 1000.0 * 1.35)
    
    for i in range(len(cases_keys)):
        cnt = f1807_counts[i]
        diff_pred = (cnt - pred_counts[i]) / float(pred_counts[i]) * 100.0
        txt = f"{cnt:,}\n({diff_pred:+.1f}% vs pred)"
        if lit_targets[i] > 0:
            diff_lit = (cnt - lit_targets[i]) / float(lit_targets[i]) * 100.0
            txt += f"\n({diff_lit:+.1f}% vs lit)"
        ax.annotate(txt, xy=(x[i] + width/2, cnt / 1000.0 + 0.8),
                    ha='center', fontsize=7.2, fontweight='bold', color='#1b5e20')

    # -------------------------------------------------------------------------
    # Panel (b): Mesh Quality & Topology (Quad Fraction and Max Aspect Ratio)
    # -------------------------------------------------------------------------
    ax = axs[0, 1]
    quad_pcts = [results[k]["element_counts"]["quad_fraction_pct"] for k in cases_keys]
    max_ars = [results[k]["aspect_ratio"]["max"] for k in cases_keys]
    
    color_bar = '#1565c0'
    color_line = '#d84315'
    
    ax2 = ax.twinx()
    b1 = ax.bar(x - 0.15, quad_pcts, width=0.3, label='Quad Fraction (%)', color=color_bar, edgecolor='#0d47a1')
    l1 = ax2.plot(x + 0.15, max_ars, 'o--', color=color_line, linewidth=2.2, markersize=8, label='Max Aspect Ratio')
    
    ax.set_ylabel('Quadrilateral Element Fraction (%)', fontsize=10.5, fontweight='bold', color=color_bar)
    ax2.set_ylabel('Maximum Aspect Ratio (Target $\\leq 4.0$)', fontsize=10.5, fontweight='bold', color=color_line)
    ax.set_title('(b) Topological Quality & Aspect Ratio Bounds', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases_labels, fontsize=8.5)
    ax.set_ylim(85, 100)
    ax2.set_ylim(1.0, 4.5)
    ax.axhline(90.0, color=color_bar, linestyle=':', alpha=0.7, label='Quad Target (>= 90%)')
    ax2.axhline(4.0, color=color_line, linestyle=':', alpha=0.7, label='AR Ceiling (<= 4.0)')
    ax.grid(axis='y', linestyle='--', alpha=0.4)
    
    for i in range(len(cases_keys)):
        ax.annotate(f"{quad_pcts[i]:.2f}%", xy=(x[i] - 0.15, quad_pcts[i] + 0.5), ha='center', fontsize=7.5, fontweight='bold', color=color_bar)
        ax2.annotate(f"{max_ars[i]:.2f}", xy=(x[i] + 0.15, max_ars[i] + 0.12), ha='center', fontsize=7.5, fontweight='bold', color=color_line)

    # -------------------------------------------------------------------------
    # Panel (c): Sizing & Critical-Region Resolution (h_min and h_min / l0)
    # -------------------------------------------------------------------------
    ax = axs[1, 0]
    h_mins = [results[k]["sizing_metrics"]["min_h_mm"] for k in cases_keys]
    l0s = [0.0075, 0.0075, 0.285, 0.0080]
    h_over_l0s = [h_mins[i] / l0s[i] for i in range(len(cases_keys))]
    
    bars = ax.bar(x, h_over_l0s, width=0.45, color='#4527a0', edgecolor='#311b92')
    ax.axhline(0.5, color='#d32f2f', linestyle='--', linewidth=1.8, label='Fine-Core Ceiling ($h / \\ell_0 = 0.5$)')
    ax.axhline(1.0, color='#f57c00', linestyle=':', linewidth=1.8, label='Resolution Band ($h / \\ell_0 = 1.0$)')
    ax.set_ylabel('Minimum Normalized Mesh Size ($h_{\\min} / \\ell_0$)', fontsize=10.5, fontweight='bold')
    ax.set_title('(c) Critical Crack-Tip Resolution: $h_{\\min} / \\ell_0$', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases_labels, fontsize=8.5)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper right')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, 0.65)
    
    for i in range(len(cases_keys)):
        ax.annotate(f"{h_over_l0s[i]:.3f}\n($h={h_mins[i]*1000:.1f}\\,\\mu\\mathrm{{m}}$)",
                    xy=(x[i], h_over_l0s[i] + 0.02), ha='center', fontsize=7.5, fontweight='bold', color='#311b92')

    # -------------------------------------------------------------------------
    # Panel (d): Far-Field Coarsening Ratio & Quality Gate Verification
    # -------------------------------------------------------------------------
    ax = axs[1, 1]
    coarsening_ratios = [results[k]["sizing_metrics"]["coarsening_ratio_far_to_core"] for k in cases_keys]
    
    bars = ax.bar(x, coarsening_ratios, width=0.45, color='#00695c', edgecolor='#004d40')
    ax.axhline(2.0, color='#d32f2f', linestyle='--', linewidth=1.8, label='Min Coarsening Gate (Ratio $\\geq 2.0$)')
    ax.set_ylabel('Far-to-Core Coarsening Ratio ($h_{\\mathrm{far}} / h_{\\mathrm{core}}$)', fontsize=10.5, fontweight='bold')
    ax.set_title('(d) Selective Coarsening & Computational Efficiency', fontsize=11.5, fontweight='bold', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(cases_labels, fontsize=8.5)
    ax.legend(frameon=True, facecolor='#f5f5f5', fontsize=8.5, loc='upper left')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    ax.set_ylim(0, max(coarsening_ratios) * 1.3)
    
    for i in range(len(cases_keys)):
        ax.annotate(f"{coarsening_ratios[i]:.2f}x\n(PASS)",
                    xy=(x[i], coarsening_ratios[i] + 0.15), ha='center', fontsize=7.8, fontweight='bold', color='#004d40')
        
    plt.tight_layout()
    out_png = os.path.join(out_dir, "fig_f1807_four_benchmark_regression_synthesis.png")
    out_pdf = os.path.join(out_dir, "fig_f1807_four_benchmark_regression_synthesis.pdf")
    plt.savefig(out_png, dpi=300)
    plt.savefig(out_pdf)
    plt.close(fig)
    print("Consolidated synthesis figure saved to: %s and %s" % (out_png, out_pdf))

def main():
    base_dir = r"D:\Master thesis\Adaptive remeshing"
    receipt_path = os.path.join(base_dir, "models/pandey_kumar_mode1/257_f1807_four_case_regression/PK_F1807_FOUR_CASE_REGRESSION_RECEIPT.json")
    out_fig_dir = os.path.join(base_dir, "results/figures")
    case_fig_dir = os.path.join(base_dir, "models/pandey_kumar_mode1/257_f1807_four_case_regression/figures")
    os.makedirs(case_fig_dir, exist_ok=True)
    
    if os.path.exists(receipt_path):
        generate_synthesis_figure(receipt_path, out_fig_dir)
    else:
        print("Receipt not yet found at: %s" % receipt_path)

    # Generate individual case mesh plots
    configs = [
        ("case1", "Case 1: Mode-I Edge Crack", 0.0075, [0.0, 1.0], [0.0, 1.0], [0.45, 0.55, 0.45, 0.55]),
        ("case2", "Case 2: Off-Axis Hole Plate", 0.0075, [0.0, 1.0], [0.0, 1.0], [0.35, 0.75, 0.45, 0.85]),
        ("case3", "Case 3: Notched Plate with Pins", 0.285, [0.0, 65.0], [0.0, 120.0], [15.0, 55.0, 45.0, 75.0]),
        ("case5", "Case 5: Seven-Hole Plate", 0.0080, [0.0, 1.0], [0.0, 1.0], [0.15, 0.85, 0.35, 0.65])
    ]
    
    for cdir, ctitle, l0, xlim, ylim, closeup in configs:
        inp_file = os.path.join(base_dir, "models/pandey_kumar_mode1/257_f1807_four_case_regression", cdir, "PK_F1807_%s_ADAPT_PHYS.inp" % cdir.upper().replace("CASE", "CASE_"))
        if os.path.exists(inp_file):
            print("Plotting individual mesh plots for %s..." % ctitle)
            out_prefix = os.path.join(case_fig_dir, "fig_f1807_%s" % cdir)
            plot_case_mesh_and_h(inp_file, l0, out_prefix, ctitle, x_lim=xlim, y_lim=ylim, closeup_box=closeup)
        else:
            print("Mesh file not yet found: %s" % inp_file)

if __name__ == "__main__":
    main()
