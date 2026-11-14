# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1736_meshes.py

Generates publication-quality figures for Task F1736:
1. Five standalone 4-panel benchmark figures showing:
   - Panel (a): Original coarse mesh
   - Panel (b): Authoritative adapted physical mesh
   - Panel (c): Spatial resolution ratio h_e / ell_0
   - Panel (d): Physical damage / error-indicator correspondence overlay
2. One corrected 5-case comparative overview figure (PNG + vector PDF).
"""

import os
import sys
import math
import csv
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Rectangle, Circle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_f1736_spatial_resolution import (
    BENCHMARK_CONFIGS, parse_abaqus_inp, compute_element_metrics
)

FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "figure.titlesize": 13,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

COARSE_MESH_PATHS = {
    "case_1": os.path.join("models", "pandey_kumar_mode1", "00_aux_continuum_preanalysis", "PK_MODE1_AUX_CONTINUUM.inp"),
    "case_2": os.path.join("models", "pandey_kumar_mode1", "220_f1729_case2_recovery_datacheck", "PK_HOLE_COMPANION_RECOVERY.inp"),
    "case_3": os.path.join("models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp"),
    "case_4": os.path.join("models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery", "PK_F1718_RECOVERY_PHYS.inp"),
    "case_5": os.path.join("models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
}

def build_poly_collection(nodes, elements, elem_types, values=None, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.15):
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

def plot_standalone_figure(case_key, cfg):
    """
    Renders a 4-panel publication figure for a specific benchmark:
    (a) Coarse mesh
    (b) Adapted mesh
    (c) Spatial resolution ratio h_e / ell_0
    (d) Damage / process-zone overlay with explicit status
    """
    final_inp = os.path.join(REPO_ROOT, cfg["final_mesh_path"])
    coarse_inp = os.path.join(REPO_ROOT, COARSE_MESH_PATHS[case_key])
    
    # Parse final adapted mesh
    fnodes, felems, fetypes = parse_abaqus_inp(final_inp)
    fstats = compute_element_metrics(fnodes, felems, fetypes, cfg["ell_0"])
    
    # Parse coarse mesh
    cnodes, celems, cetypes = parse_abaqus_inp(coarse_inp)
    cstats = compute_element_metrics(cnodes, celems, cetypes, cfg["ell_0"])
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    ((ax_coarse, ax_adapt), (ax_res, ax_dam)) = axes
    
    bb = fstats["bounding_box"]
    dx = bb["x_max"] - bb["x_min"]
    dy = bb["y_max"] - bb["y_min"]
    pad_x = 0.04 * dx
    pad_y = 0.04 * dy
    xlims = (bb["x_min"] - pad_x, bb["x_max"] + pad_x)
    ylims = (bb["y_min"] - pad_y, bb["y_max"] + pad_y)
    
    # -------------------------------------------------------------
    # Panel (a): Original Coarse Mesh
    # -------------------------------------------------------------
    pc_coarse = build_poly_collection(cnodes, celems, cetypes, edge_lw=0.25)
    ax_coarse.add_collection(pc_coarse)
    ax_coarse.set_xlim(xlims)
    ax_coarse.set_ylim(ylims)
    ax_coarse.set_aspect("equal")
    ax_coarse.set_xlabel("x [mm]")
    ax_coarse.set_ylabel("y [mm]")
    ax_coarse.set_title(f"(a) Original Coarse Mesh\n{cstats['num_elements']} elements ({cstats['quad_percentage']:.1f}% Q) | {cstats['num_nodes']} nodes", fontweight="bold")
    
    # -------------------------------------------------------------
    # Panel (b): Authoritative Final Adapted Mesh
    # -------------------------------------------------------------
    pc_adapt = build_poly_collection(fnodes, felems, fetypes, edge_lw=0.10)
    ax_adapt.add_collection(pc_adapt)
    ax_adapt.set_xlim(xlims)
    ax_adapt.set_ylim(ylims)
    ax_adapt.set_aspect("equal")
    ax_adapt.set_xlabel("x [mm]")
    ax_adapt.set_ylabel("y [mm]")
    ax_adapt.set_title(f"(b) Authoritative Adapted Mesh\n{fstats['num_elements']} elements ({fstats['quad_percentage']:.1f}% Q) | {fstats['num_nodes']} nodes", fontweight="bold")
    
    # -------------------------------------------------------------
    # Panel (c): Spatial Resolution Field h_e / ell_0
    # -------------------------------------------------------------
    ratios_dict = {}
    for eid, nids in felems.items():
        coords = np.array([fnodes[nid] for nid in nids])
        x = coords[:, 0]
        y = coords[:, 1]
        a = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
        ratios_dict[eid] = math.sqrt(a) / cfg["ell_0"]
        
    pc_res = build_poly_collection(fnodes, felems, fetypes, values=ratios_dict, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.08)
    ax_res.add_collection(pc_res)
    ax_res.set_xlim(xlims)
    ax_res.set_ylim(ylims)
    ax_res.set_aspect("equal")
    ax_res.set_xlabel("x [mm]")
    ax_res.set_ylabel("y [mm]")
    comp = fstats["compliance"]
    ax_res.set_title(f"(c) Spatial Resolution $h_e / \\ell_0$ (Capped at 3.0)\n$h \\leq \\ell_0$: {comp['h_le_ell0']['count_pct']:.1f}% count ({comp['h_le_ell0']['area_pct']:.1f}% area) | $h_{{\\min}} = {fstats['element_size_stats_mm']['min']*1e3:.2f}\\,\\mu$m", fontweight="bold")
    
    sm_res = plt.cm.ScalarMappable(cmap=plt.get_cmap("viridis_r"), norm=plt.Normalize(vmin=0.0, vmax=3.0))
    sm_res.set_array([])
    cb_res = fig.colorbar(sm_res, ax=ax_res, orientation="horizontal", pad=0.10, shrink=0.85)
    cb_res.set_label(r"Resolution Ratio $h_e / \ell_0$ (Fine $\leq 1.0 \rightarrow$ Yellow, Coarse $\rightarrow$ Purple)")
    
    # -------------------------------------------------------------
    # Panel (d): Physical Damage / Process-Zone Overlay
    # -------------------------------------------------------------
    if case_key == "case_2":
        # Load authentic extracted damage field from Task F1735
        dam_csv = os.path.join(REPO_ROOT, "results", "validation", "f1735_case2_final_frame_sdv.csv")
        dam_dict = {}
        if os.path.exists(dam_csv):
            with open(dam_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    eid = int(row["physical_element_id"])
                    dam_dict[eid] = float(row["damage_d"])
        pc_dam = build_poly_collection(fnodes, felems, fetypes, values=dam_dict, cmap_name="inferno", vmin=0.0, vmax=1.0, edge_lw=0.08)
        ax_dam.add_collection(pc_dam)
        ax_dam.set_title(f"(d) Authentic Coupled Phase-Field Damage ($u = 0.00768\\,$mm)\nJob 1423271 (Exit 1 at min dt) | 343 Broken Elements into Hole", fontweight="bold")
        sm_dam = plt.cm.ScalarMappable(cmap=plt.get_cmap("inferno"), norm=plt.Normalize(vmin=0.0, vmax=1.0))
        sm_dam.set_array([])
        cb_dam = fig.colorbar(sm_dam, ax=ax_dam, orientation="horizontal", pad=0.10, shrink=0.85)
        cb_dam.set_label(r"Phase-Field Damage $d$ ($0 = $ Intact, $1 = $ Fully Broken)")
    else:
        # Mesh wireframe with physical crack trajectory & process zone annotation
        pc_dam = build_poly_collection(fnodes, felems, fetypes, edge_lw=0.12)
        ax_dam.add_collection(pc_dam)
        
        # Add visual overlay and text note
        if case_key == "case_1":
            ax_dam.plot([0.5, 1.0], [0.5, 0.5], color="#e41a1c", linestyle="--", linewidth=2.0, label="Expected Straight Crack Path")
            status_text = (
                "DAMAGE VALIDATION: NOT DEMONSTRATED\n"
                "--------------------------------------------------\n"
                "Donor Type: Linear elastic companion stress\n"
                "Refinement Coverage: Highly localized at tip (x=0.5)\n"
                "Distal Path (x > 0.65): Unrefined (h ~ 12-18 um > ell_0)\n"
                "Classification: PARTIAL — LOCALIZED REFINEMENT"
            )
            ax_dam.set_title("(d) Process-Zone & Propagation Path Evaluation\nRefinement Concentrated at Tip; Distal Ligament Coarse", fontweight="bold")
        elif case_key == "case_3":
            ax_dam.plot([10.0, 36.5], [70.0, 51.0], color="#e41a1c", linestyle="--", linewidth=2.0, label="Primary Path (Notch -> Hole)")
            ax_dam.plot([36.5, 65.0], [51.0, 51.0], color="#377eb8", linestyle=":", linewidth=2.0, label="Secondary Path (Hole -> Right Edge)")
            status_text = (
                "DAMAGE VALIDATION: NOT DEMONSTRATED\n"
                "--------------------------------------------------\n"
                "Donor Type: Staggered coupled pre-peak (u=0.105 mm)\n"
                "Primary Corridor: Moderately refined (h <= ell_0)\n"
                "Secondary Corridor: UNREFINED (h ~ 400-800 um > ell_0)\n"
                "Classification: INCONCLUSIVE — INSUFFICIENT EVIDENCE"
            )
            ax_dam.set_title("(d) Process-Zone & Propagation Path Evaluation\nSecondary Crack Corridor Insufficiently Resolved", fontweight="bold")
        elif case_key == "case_4":
            status_text = (
                "DAMAGE VALIDATION: NOT DEMONSTRATED\n"
                "--------------------------------------------------\n"
                "Donor Type: Authentic coarse phase-field (State 2)\n"
                "Refinement Coverage: Continuous bridge 1->2->3->4\n"
                "Forward Adapted Fracture Run: NOT EXECUTED\n"
                "Classification: PASS — SPATIAL MESH QUALIFIED"
            )
            ax_dam.set_title("(d) Process-Zone & Refinement Correspondence\nContinuous Multi-Ligament Refinement Bridge", fontweight="bold")
        elif case_key == "case_5":
            status_text = (
                "DAMAGE VALIDATION: NOT DEMONSTRATED\n"
                "--------------------------------------------------\n"
                "Donor Type: Authentic coarse phase-field (u=0.0048 mm)\n"
                "Refinement Coverage: Concentrated upper ligament (1, 2, 3)\n"
                "Forward Adapted Fracture Run: NOT EXECUTED\n"
                "Classification: PASS — SPATIAL MESH QUALIFIED"
            )
            ax_dam.set_title("(d) Process-Zone & Refinement Correspondence\nSelective Upper-Ligament Process-Zone Enclosure", fontweight="bold")
            
        ax_dam.text(0.04, 0.40, status_text, transform=ax_dam.transAxes, fontsize=8.5,
                    verticalalignment="top", family="monospace",
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff3cd", edgecolor="#856404"))
        if case_key in ["case_1", "case_3"]:
            ax_dam.legend(loc="upper right", framealpha=0.9, fontsize=8.5)

    ax_dam.set_xlim(xlims)
    ax_dam.set_ylim(ylims)
    ax_dam.set_aspect("equal")
    ax_dam.set_xlabel("x [mm]")
    ax_dam.set_ylabel("y [mm]")
    
    fig.suptitle(f"F1736 Standalone Benchmark Reassessment: {cfg['name']}\n(Physical Geometry: [{bb['x_min']:.1f}, {bb['x_max']:.1f}] $\\times$ [{bb['y_min']:.1f}, {bb['y_max']:.1f}] mm, $\\ell_0 = {cfg['ell_0']}$ mm)",
                 fontsize=13, fontweight="bold", y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    out_png = os.path.join(FIG_DIR, f"fig_f1736_{case_key}_standalone_mesh.png")
    out_pdf = os.path.join(FIG_DIR, f"fig_f1736_{case_key}_standalone_mesh.pdf")
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"Saved enhanced 4-panel standalone figure for {case_key}: {os.path.relpath(out_png, REPO_ROOT)}")

def plot_corrected_five_case_comparison():
    fig = plt.figure(figsize=(18, 10))
    gs = fig.add_gridspec(2, 3, wspace=0.25, hspace=0.35)
    
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[0, 2]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1])
    ]
    
    cax_panel = fig.add_subplot(gs[1, 2])
    cax_panel.axis("off")
    
    case_keys = ["case_1", "case_2", "case_3", "case_4", "case_5"]
    
    for idx, case_key in enumerate(case_keys):
        ax = axes[idx]
        cfg = BENCHMARK_CONFIGS[case_key]
        inp_path = os.path.join(REPO_ROOT, cfg["final_mesh_path"])
        nodes, elements, elem_types = parse_abaqus_inp(inp_path)
        stats = compute_element_metrics(nodes, elements, elem_types, cfg["ell_0"])
        
        ratios_dict = {}
        for eid, nids in elements.items():
            coords = np.array([nodes[nid] for nid in nids])
            x = coords[:, 0]
            y = coords[:, 1]
            a = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
            ratios_dict[eid] = math.sqrt(a) / cfg["ell_0"]
            
        pc = build_poly_collection(nodes, elements, elem_types, values=ratios_dict, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.12)
        ax.add_collection(pc)
        
        bb = stats["bounding_box"]
        dx = bb["x_max"] - bb["x_min"]
        dy = bb["y_max"] - bb["y_min"]
        pad_x = 0.04 * dx
        pad_y = 0.04 * dy
        ax.set_xlim(bb["x_min"] - pad_x, bb["x_max"] + pad_x)
        ax.set_ylim(bb["y_min"] - pad_y, bb["y_max"] + pad_y)
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]", fontsize=9)
        ax.set_ylabel("y [mm]", fontsize=9)
        
        title_text = (
            f"({chr(97+idx)}) {cfg['name']}\n"
            f"Authoritative: {stats['num_elements']} el ({stats['quad_percentage']:.1f}% Q) | Pub: {cfg['published_elements']} el\n"
            f"$\\ell_0 = {cfg['ell_0']}$ mm | $h_{{\\min}} = {stats['element_size_stats_mm']['min']*1e3:.2f}\\,\\mu$m | $h \\leq \\ell_0$: {stats['compliance']['h_le_ell0']['count_pct']:.1f}%"
        )
        ax.set_title(title_text, fontsize=9.5, fontweight="bold")
    
    # Legend and Summary in the 6th slot
    sm = plt.cm.ScalarMappable(cmap=plt.get_cmap("viridis_r"), norm=plt.Normalize(vmin=0.0, vmax=3.0))
    sm.set_array([])
    cb = fig.colorbar(sm, ax=cax_panel, orientation="horizontal", fraction=0.15, pad=0.1, shrink=0.85)
    cb.set_label(r"Spatial Resolution Ratio $h_e / \ell_0$ (Capped at 3.0)", fontsize=10)
    
    summary_box_text = (
        "TASK F1736: AUDITED BENCHMARK STATUS\n"
        "--------------------------------------------------\n"
        "Case 1 (Mode I): 14,147 el (Pub: 13,762 el)\n"
        "  - Status: PARTIAL — LOCALIZED REFINEMENT\n"
        "  - Gap: Ligament distal to tip unrefined prior to crack\n"
        "Case 2 (Off-Axis Hole): 23,965 el (Pub: 23,618 el)\n"
        "  - Status: PASS — SPATIAL MESH QUALIFIED\n"
        "  - Note: Fracture sim ran (252 inc), stopped at min dt\n"
        "Case 3 (Sec 4.3): 12,110 el (Pub: 12,168 el)\n"
        "  - Status: INCONCLUSIVE — INSUFFICIENT EVIDENCE\n"
        "  - Gap: Secondary corridor unrefined (h > ell_0)\n"
        "Case 4 (Five Hole): 13,017 el (Pub: 12,944 el)\n"
        "  - Status: PASS — SPATIAL MESH QUALIFIED\n"
        "  - Note: Fracture sim NOT DEMONSTRATED\n"
        "Case 5 (Seven Hole): 15,708 el (Pub: 15,714 el)\n"
        "  - Status: PASS — SPATIAL MESH QUALIFIED\n"
        "  - Note: Fracture sim NOT DEMONSTRATED\n"
        "--------------------------------------------------\n"
        "*Zero negative Jacobians across all 5 meshes."
    )
    cax_panel.text(0.05, 0.40, summary_box_text, transform=cax_panel.transAxes, fontsize=8.5,
                   verticalalignment="top", family="monospace",
                   bbox=dict(boxstyle="round,pad=0.6", facecolor="#f8f9fa", edgecolor="#495057"))
    
    fig.suptitle("F1736: Independent Scientific Reassessment of Five-Geometry Method A Adaptive Meshes\n(Authentic Final Meshes from Tasks F1725, F1726, F1728, F1734, and Task 192)",
                 fontsize=14, fontweight="bold", y=0.98)
    
    out_png = os.path.join(FIG_DIR, "fig_f1736_five_case_comparison_corrected.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1736_five_case_comparison_corrected.pdf")
    fig.savefig(out_png, dpi=300)
    fig.savefig(out_pdf)
    plt.close(fig)
    print(f"Saved corrected five-case comparison figure: {os.path.relpath(out_png, REPO_ROOT)}")
    
    root_fig_png = os.path.join(REPO_ROOT, "figures", "fig_f1736_five_case_comparison_corrected.png")
    os.makedirs(os.path.dirname(root_fig_png), exist_ok=True)
    import shutil
    shutil.copyfile(out_png, root_fig_png)

def main():
    print("Generating enhanced 4-panel standalone benchmark figures...")
    for case_key, cfg in BENCHMARK_CONFIGS.items():
        plot_standalone_figure(case_key, cfg)
    
    print("\nGenerating corrected 5-case comparison figure...")
    plot_corrected_five_case_comparison()
    print("All figure generation completed successfully.")

if __name__ == "__main__":
    main()
