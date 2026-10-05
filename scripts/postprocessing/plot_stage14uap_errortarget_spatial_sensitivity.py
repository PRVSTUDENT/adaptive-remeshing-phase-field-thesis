# -*- coding: utf-8 -*-
"""
Gate-6B Stage 14U-AQ: Publication-quality plotting of errorTarget (1, 2, 3, 5%) spatial sensitivity
and authentic finite-element mesh generation for Mode-I adaptive remeshing.

Generates:
1. Sizing Point Scatter Map (4-panel):
   - results/figures/mode1_gate6b/fig_mode1_stage14uap_errortarget_spatial_sensitivity.png (.pdf)
2. Authentic Finite-Element Mesh Wireframe & Sizing Plots:
   - results/figures/mode1_gate6b/Mode1_corrected_adaptive_mesh_ET2.png (.pdf)
   - results/figures/mode1_gate6b/Mode1_corrected_adaptive_mesh_ET3.png (.pdf)
   - results/figures/mode1_gate6b/Mode1_corrected_adaptive_mesh_ET5.png (.pdf)
   - results/figures/mode1_gate6b/Mode1_corrected_adaptive_mesh_ET2_ET3_ET5_comparison.png (.pdf)
"""
import os
import sys
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors

def parse_abaqus_inp(inp_path):
    """
    Parses Abaqus 2D input deck for nodes and element connectivity.
    """
    nodes = {}
    elements = []
    current_section = None

    with open(inp_path, 'r') as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith('**'):
                continue
            if line_str.startswith('*'):
                upper = line_str.upper()
                if upper.startswith('*NODE'):
                    current_section = 'NODE'
                elif upper.startswith('*ELEMENT'):
                    current_section = 'ELEMENT'
                elif upper.startswith('*PART'):
                    current_section = None
                elif upper.startswith('*END PART') or upper.startswith('*NSET') or upper.startswith('*ELSET') or upper.startswith('*SOLID') or upper.startswith('*MATERIAL') or upper.startswith('*STEP'):
                    current_section = None
                continue

            if current_section == 'NODE':
                tokens = [t.strip() for t in line_str.split(',') if t.strip()]
                if len(tokens) >= 3:
                    try:
                        nid = int(tokens[0])
                        x = float(tokens[1])
                        y = float(tokens[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif current_section == 'ELEMENT':
                tokens = [t.strip() for t in line_str.split(',') if t.strip()]
                if len(tokens) >= 4:
                    try:
                        eid = int(tokens[0])
                        conn = [int(tok) for tok in tokens[1:]]
                        elements.append((eid, conn))
                    except ValueError:
                        pass

    return nodes, elements

def compute_element_polygons_and_sizes(nodes, elements):
    polys = []
    h_um_list = []
    corridor_count = 0
    fine_l0_count = 0
    l0_um = 7.5

    for eid, conn in elements:
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) < 3:
            continue
        polys.append(coords)
        
        num_n = len(coords)
        area_sum = 0.0
        cy_sum = 0.0
        for i in range(num_n):
            j = (i + 1) % num_n
            area_sum += coords[i][0] * coords[j][1] - coords[j][0] * coords[i][1]
            cy_sum += coords[i][1]
        area = 0.5 * abs(area_sum)
        h_eq_um = math.sqrt(area) * 1000.0
        h_um_list.append(h_eq_um)

        cy = cy_sum / float(num_n)
        if 0.45 <= cy <= 0.55:
            corridor_count += 1
        if h_eq_um <= l0_um:
            fine_l0_count += 1

    return polys, np.array(h_um_list), corridor_count, fine_l0_count

def generate_sensitivity_scatter_plots(summary_json_path, csv_dir, out_pdf_path, out_png_path):
    with open(summary_json_path, 'r') as f:
        summary = json.load(f)
        
    error_targets = [1.0, 2.0, 3.0, 5.0]
    csv_files = {
        1.0: os.path.join(csv_dir, "elements_err_10pct.csv"),
        2.0: os.path.join(csv_dir, "elements_err_20pct.csv"),
        3.0: os.path.join(csv_dir, "elements_err_30pct.csv"),
        5.0: os.path.join(csv_dir, "elements_err_50pct.csv")
    }
    
    dfs = {}
    for et in error_targets:
        if os.path.isfile(csv_files[et]):
            dfs[et] = pd.read_csv(csv_files[et])
            
    fig, axes = plt.subplots(2, 2, figsize=(15, 12), sharex=True, sharey=True)
    axes = axes.flatten()
    
    norm = mcolors.Normalize(vmin=0.5, vmax=24.0)
    cmap = plt.get_cmap('viridis_r')
    
    classifications = {
        1.0: ("DIFFUSE DOMAIN OVERREFINEMENT", "crimson"),
        2.0: ("TOWARD TARGET LOCALIZATION", "forestgreen"),
        3.0: ("TOWARD TARGET LOCALIZATION", "forestgreen"),
        5.0: ("UNDER-RESOLVED CORRIDOR", "darkorange")
    }
    
    sc_last = None
    
    for idx, et in enumerate(error_targets):
        ax = axes[idx]
        if et in dfs:
            df = dfs[et]
            h_um = df['h_eq'] * 1000.0
            
            sc = ax.scatter(df['cx'], df['cy'], c=h_um, cmap=cmap, norm=norm,
                            s=np.clip(22.0 - h_um * 0.8, 1.5, 22.0), alpha=0.75, rasterized=True)
            sc_last = sc
            
            ax.axhspan(0.45, 0.55, color='lightgray', alpha=0.35, zorder=0)
            ax.axhline(0.45, color='gray', linestyle=':', linewidth=1.2, zorder=1)
            ax.axhline(0.55, color='gray', linestyle=':', linewidth=1.2, zorder=1)
            
            ax.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=2.2, label='Initial Notch ($a_0 = 0.5\\,\\mathrm{mm}$)', zorder=5)
            ax.plot([0.5, 1.0], [0.5, 0.5], 'r--', linewidth=1.5, alpha=0.8, label='Ligament Plane ($y = 0.5\\,\\mathrm{mm}$)', zorder=5)
            
            total_n = len(df)
            corr_n = len(df[(df['cy'] >= 0.45) & (df['cy'] <= 0.55)])
            fine_l0_n = len(df[h_um <= 7.5])
            fine_corr_n = len(df[(df['cy'] >= 0.45) & (df['cy'] <= 0.55) & (h_um <= 7.5)])
            
            corr_share_fine = (fine_corr_n / float(fine_l0_n) * 100.0) if fine_l0_n > 0 else 0.0
            fine_pct_total = (fine_l0_n / float(total_n) * 100.0) if total_n > 0 else 0.0
            
            h_min_um = np.min(h_um)
            h_med_um = np.median(h_um)
            
            cls_text, cls_color = classifications[et]
            
            ax.set_title(r"$\mathbf{errorTarget = %.1f\%%}$ ($N = %d$ Elements)" % (et, total_n),
                         fontsize=12, fontweight='bold', pad=8)
            
            ax.text(0.03, 0.94, cls_text, transform=ax.transAxes,
                    fontsize=9.5, fontweight='bold', color=cls_color,
                    bbox=dict(boxstyle='round,pad=0.25', facecolor='white', alpha=0.9, edgecolor=cls_color, linewidth=1.2))
            
            info_str = (
                f"$h_{{\\min}} = {h_min_um:.2f}\\,\\mu\\mathrm{{m}}$\n"
                f"$h_{{\\mathrm{{med}}}} = {h_med_um:.2f}\\,\\mu\\mathrm{{m}}$\n"
                f"$N(h \\leq \\ell_0) = {fine_l0_n}$ ({fine_pct_total:.1f}%)\n"
                f"Corridor Share: {corr_share_fine:.1f}%\n"
                f"Corridor $N$: {corr_n}"
            )
            ax.text(0.97, 0.04, info_str, transform=ax.transAxes,
                    fontsize=8.5, verticalalignment='bottom', horizontalalignment='right',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.88, edgecolor='silver'))
            
            ax.set_xlim(0.0, 1.0)
            ax.set_ylim(0.0, 1.0)
            ax.set_aspect('equal')
            ax.grid(True, linestyle=':', alpha=0.5)
            
            if idx in [2, 3]:
                ax.set_xlabel('Plate Coordinate $x$ [mm]', fontsize=11)
            if idx in [0, 2]:
                ax.set_ylabel('Plate Coordinate $y$ [mm]', fontsize=11)
                
            if idx == 0:
                ax.legend(loc='lower left', fontsize=8.5, framealpha=0.9)
                
    fig.subplots_adjust(right=0.88, top=0.92, bottom=0.08, left=0.08, wspace=0.12, hspace=0.18)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(sc_last, cax=cbar_ax)
    cbar.set_label(r'Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{\mathrm{Area}}$ [$\mu\mathrm{m}$] (Governing $\ell_0 = 7.5\,\mu\mathrm{m}$)',
                   fontsize=11, labelpad=10)
    cbar.ax.axhline(7.5, color='red', linestyle='--', linewidth=1.5)
    cbar.ax.text(1.3, 7.5, r'$\ell_0 = 7.5\,\mu\mathrm{m}$', color='red', fontsize=9.5, verticalalignment='center')
    
    plt.suptitle("Mode-I Pre-Analysis Companion Mesh: Spatial Sensitivity of Abaqus Native Error-Guided Sizing\n"
                 r"Effect of Target Error Tolerance $\eta \in \{1.0\%, 2.0\%, 3.0\%, 5.0\%\}$ on Crack Corridor ($|y - 0.5| \leq 0.05\,\mathrm{mm}$) Localization",
                 fontsize=13, fontweight='bold', y=0.97)
    
    os.makedirs(os.path.dirname(out_pdf_path), exist_ok=True)
    plt.savefig(out_pdf_path, dpi=300, bbox_inches='tight')
    plt.savefig(out_png_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Spatial sensitivity scatter plot generated: %s, %s" % (out_pdf_path, out_png_path))

def plot_single_mesh(nodes, elements, et_pct, out_base_path):
    polys, h_um, corr_count, fine_l0_count = compute_element_polygons_and_sizes(nodes, elements)
    n_elems = len(polys)
    n_nodes = len(nodes)

    fig, ax = plt.subplots(figsize=(8, 7.5), dpi=300)
    norm = mcolors.Normalize(vmin=0.5, vmax=24.0)
    cmap = plt.get_cmap('viridis_r')

    edge_lw = 0.25 if et_pct == 2.0 else (0.35 if et_pct == 3.0 else 0.45)
    
    pc = PolyCollection(polys, array=h_um, cmap=cmap, norm=norm,
                        edgecolors='black', linewidths=edge_lw, antialiased=True)
    ax.add_collection(pc)

    ax.plot([0.0, 0.5], [0.5, 0.5], color='red', linewidth=2.5, solid_capstyle='round',
            label='Initial Crack Seam ($a_0 = 0.5\\,\\mathrm{mm}$)', zorder=10)
    ax.plot(0.5, 0.5, marker='o', markersize=6.5, markerfacecolor='red', markeredgecolor='white',
            markeredgewidth=1.2, label='Crack Tip $(0.5, 0.5)\\,\\mathrm{mm}$', zorder=11)
    ax.plot([0.5, 1.0], [0.5, 0.5], color='red', linestyle='--', linewidth=1.5, alpha=0.75,
            label='Symmetry Ligament ($y = 0.5\\,\\mathrm{mm}$)', zorder=9)

    ax.axhline(0.45, color='dimgray', linestyle=':', linewidth=1.0, alpha=0.7, zorder=8)
    ax.axhline(0.55, color='dimgray', linestyle=':', linewidth=1.0, alpha=0.7, zorder=8)

    ax.set_xlim(0.0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.set_aspect('equal')
    ax.set_xlabel('Plate Coordinate $x$ [mm]', fontsize=11, fontweight='bold')
    ax.set_ylabel('Plate Coordinate $y$ [mm]', fontsize=11, fontweight='bold')

    h_min = np.min(h_um)
    h_med = np.median(h_um)
    h_max = np.max(h_um)
    fine_pct = (fine_l0_count / float(n_elems)) * 100.0

    title_str = (f"Mode-I Corrected Native Adaptive Mesh: $\\mathbf{{errorTarget = {et_pct:.1f}\\%}}$\n"
                 f"$N = {n_elems:,}$ Finite Elements, $N_{{\\mathrm{{nodes}}}} = {n_nodes:,}$ Nodes")
    ax.set_title(title_str, fontsize=12, fontweight='bold', pad=10)

    info_box = (
        f"$\\mathbf{{errorTarget}} = {et_pct:.1f}\\%$\n"
        f"Finite Elements: {n_elems:,}\n"
        f"Nodes: {n_nodes:,}\n"
        f"$h_{{\\min}} = {h_min:.2f}\\,\\mu\\mathrm{{m}}$ (${h_min/7.5:.2f}\\,\\ell_0$)\n"
        f"$h_{{\\mathrm{{median}}}} = {h_med:.2f}\\,\\mu\\mathrm{{m}}$\n"
        f"$h_{{\\max}} = {h_max:.2f}\\,\\mu\\mathrm{{m}}$\n"
        f"$N(h \\leq \\ell_0) = {fine_l0_count:,}$ ({fine_pct:.1f}%)\n"
        f"Corridor $N$: {corr_count:,}"
    )
    ax.text(0.03, 0.04, info_box, transform=ax.transAxes, fontsize=9.0,
            verticalalignment='bottom', horizontalalignment='left',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.92, edgecolor='gray', linewidth=1.0),
            zorder=12)

    ax.legend(loc='upper right', fontsize=8.5, framealpha=0.92, edgecolor='gray')

    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r'Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{\mathrm{Area}}$ [$\mu\mathrm{m}$]',
                   fontsize=10.5, labelpad=8)
    cbar.ax.axhline(7.5, color='red', linestyle='--', linewidth=1.5)
    cbar.ax.text(1.3, 7.5, r'$\ell_0 = 7.5\,\mu\mathrm{m}$', color='red', fontsize=9.0, verticalalignment='center')

    plt.tight_layout()
    os.makedirs(os.path.dirname(out_base_path), exist_ok=True)
    png_path = out_base_path + ".png"
    pdf_path = out_base_path + ".pdf"
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved: {png_path} and {pdf_path}")

def plot_comparison_figure(case_data, out_base_path):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), dpi=300, sharex=True, sharey=True)

    norm = mcolors.Normalize(vmin=0.5, vmax=24.0)
    cmap = plt.get_cmap('viridis_r')
    last_pc = None

    for idx, (et_pct, (nodes, elements)) in enumerate(case_data):
        ax = axes[idx]
        polys, h_um, corr_count, fine_l0_count = compute_element_polygons_and_sizes(nodes, elements)
        n_elems = len(polys)
        n_nodes = len(nodes)

        edge_lw = 0.22 if et_pct == 2.0 else (0.32 if et_pct == 3.0 else 0.42)
        pc = PolyCollection(polys, array=h_um, cmap=cmap, norm=norm,
                            edgecolors='black', linewidths=edge_lw, antialiased=True)
        ax.add_collection(pc)
        last_pc = pc

        ax.plot([0.0, 0.5], [0.5, 0.5], color='red', linewidth=2.2, solid_capstyle='round', zorder=10)
        ax.plot(0.5, 0.5, marker='o', markersize=5.5, markerfacecolor='red', markeredgecolor='white',
                markeredgewidth=1.0, zorder=11)
        ax.plot([0.5, 1.0], [0.5, 0.5], color='red', linestyle='--', linewidth=1.2, alpha=0.75, zorder=9)

        ax.axhline(0.45, color='dimgray', linestyle=':', linewidth=0.9, alpha=0.7, zorder=8)
        ax.axhline(0.55, color='dimgray', linestyle=':', linewidth=0.9, alpha=0.7, zorder=8)

        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.set_aspect('equal')
        ax.set_xlabel('Plate Coordinate $x$ [mm]', fontsize=11, fontweight='bold')
        if idx == 0:
            ax.set_ylabel('Plate Coordinate $y$ [mm]', fontsize=11, fontweight='bold')

        h_min = np.min(h_um)
        h_med = np.median(h_um)
        fine_pct = (fine_l0_count / float(n_elems)) * 100.0

        ax.set_title(f"$\\mathbf{{errorTarget = {et_pct:.1f}\\%}}$\n$N = {n_elems:,}$ Elements ($N_{{\\mathrm{{nodes}}}} = {n_nodes:,}$)",
                     fontsize=11.5, fontweight='bold', pad=8)

        info_box = (
            f"$h_{{\\min}} = {h_min:.2f}\\,\\mu\\mathrm{{m}}$\n"
            f"$h_{{\\mathrm{{med}}}} = {h_med:.2f}\\,\\mu\\mathrm{{m}}$\n"
            f"$N(h \\leq \\ell_0) = {fine_l0_count:,}$ ({fine_pct:.1f}%)\n"
            f"Corridor $N = {corr_count:,}$"
        )
        ax.text(0.04, 0.04, info_box, transform=ax.transAxes, fontsize=8.5,
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.35', facecolor='white', alpha=0.92, edgecolor='gray', linewidth=0.8),
                zorder=12)

    fig.subplots_adjust(left=0.05, right=0.90, bottom=0.10, top=0.88, wspace=0.10)
    cbar_ax = fig.add_axes([0.915, 0.15, 0.015, 0.68])
    cbar = fig.colorbar(last_pc, cax=cbar_ax)
    cbar.set_label(r'Equivalent Element Size $h_{\mathrm{eq}} = \sqrt{\mathrm{Area}}$ [$\mu\mathrm{m}$] ($\ell_0 = 7.5\,\mu\mathrm{m}$)',
                   fontsize=11, labelpad=8)
    cbar.ax.axhline(7.5, color='red', linestyle='--', linewidth=1.5)
    cbar.ax.text(1.3, 7.5, r'$\ell_0 = 7.5\,\mu\mathrm{m}$', color='red', fontsize=9.0, verticalalignment='center')

    plt.suptitle("Mode-I Corrected Native Adaptive Meshes: Spatial Refinement Comparison\n"
                 r"Effect of Error Tolerance $\eta \in \{2.0\%, 3.0\%, 5.0\%\}$ on Crack Corridor ($|y - 0.5| \leq 0.05\,\mathrm{mm}$) Sizing and Density",
                 fontsize=13, fontweight='bold', y=0.98)

    os.makedirs(os.path.dirname(out_base_path), exist_ok=True)
    png_path = out_base_path + ".png"
    pdf_path = out_base_path + ".pdf"
    plt.savefig(png_path, dpi=300, bbox_inches='tight')
    plt.savefig(pdf_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved comparison figure: {png_path} and {pdf_path}")

def main():
    base_dir = r"models/pandey_kumar_mode1/32_stage14_remeshing_errortarget_sensitivity"
    out_dir = r"results/figures/mode1_gate6b"
    summary_path = os.path.join(base_dir, "MODE1_STAGE14UAP_ERRORTARGET_SENSITIVITY_SUMMARY.json")

    # 1. Generate scatter map
    out_pdf_sc = os.path.join(out_dir, "fig_mode1_stage14uap_errortarget_spatial_sensitivity.pdf")
    out_png_sc = os.path.join(out_dir, "fig_mode1_stage14uap_errortarget_spatial_sensitivity.png")
    generate_sensitivity_scatter_plots(summary_path, base_dir, out_pdf_sc, out_png_sc)

    # 2. Generate mesh plots
    cases = [
        (2.0, "PK_M1_STAGE14UAP_ERR_20PCT.inp", "Mode1_corrected_adaptive_mesh_ET2"),
        (3.0, "PK_M1_STAGE14UAP_ERR_30PCT.inp", "Mode1_corrected_adaptive_mesh_ET3"),
        (5.0, "PK_M1_STAGE14UAP_ERR_50PCT.inp", "Mode1_corrected_adaptive_mesh_ET5")
    ]

    loaded_cases = []
    for et_pct, fname, out_name in cases:
        inp_p = os.path.join(base_dir, fname)
        if os.path.isfile(inp_p):
            print(f"Parsing {inp_p}...")
            nodes, elements = parse_abaqus_inp(inp_p)
            print(f"  -> {len(nodes)} nodes, {len(elements)} elements")
            out_p = os.path.join(out_dir, out_name)
            plot_single_mesh(nodes, elements, et_pct, out_p)
            loaded_cases.append((et_pct, (nodes, elements)))

    if len(loaded_cases) == 3:
        comp_out = os.path.join(out_dir, "Mode1_corrected_adaptive_mesh_ET2_ET3_ET5_comparison")
        plot_comparison_figure(loaded_cases, comp_out)

if __name__ == "__main__":
    main()
