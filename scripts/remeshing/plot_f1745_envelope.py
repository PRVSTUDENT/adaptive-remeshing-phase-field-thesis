# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1745_envelope.py

Generates publication-quality figure for Task F1745:
Case 3 (Sec 4.3 Rectangular Notched Plate with Hole and Pins)
Unified 5-State Error-Indicator Envelope Qualification.

Panels:
  (a) Coarse Base Mesh (3,923 elements) with Benchmark Geometry and Loading Holes
  (b) Unified 5-State Normalized Error-Indicator Envelope eta_hat_e^(env)
  (c) Donor State Dominance Map (T1, T2, T3, S2, S4) Across Coarse Topology
  (d) Dual-Corridor Along-Path Envelope Profiles (Primary Notch-to-Hole vs Secondary Hole-to-Boundary)
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp

FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.labelsize": 9.5,
    "axes.titlesize": 10.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "figure.titlesize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

def build_poly_collection(nodes, elements, values=None, colors_dict=None, cmap_name="inferno", vmin=0.0, vmax=3.0, edge_lw=0.15):
    verts = []
    c_list = []
    
    if values is not None:
        cmap = plt.get_cmap(cmap_name)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        for eid, conn in elements.items():
            coords = [nodes[nid] for nid in conn if nid in nodes]
            if len(coords) >= 3:
                verts.append(coords)
                val = values.get(str(eid), values.get(eid, 0.0))
                c_list.append(cmap(norm(val)))
        pc = PolyCollection(verts, facecolors=c_list, edgecolors="black", linewidths=edge_lw)
    elif colors_dict is not None:
        for eid, conn in elements.items():
            coords = [nodes[nid] for nid in conn if nid in nodes]
            if len(coords) >= 3:
                verts.append(coords)
                col = colors_dict.get(str(eid), colors_dict.get(eid, "#cccccc"))
                c_list.append(col)
        pc = PolyCollection(verts, facecolors=c_list, edgecolors="black", linewidths=edge_lw)
    else:
        for eid, conn in elements.items():
            coords = [nodes[nid] for nid in conn if nid in nodes]
            if len(coords) >= 3:
                verts.append(coords)
        pc = PolyCollection(verts, facecolors="#e6eff8", edgecolors="#2b4c7e", linewidths=edge_lw)
        
    return pc

def main():
    coarse_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp")
    map_json = os.path.join(REPO_ROOT, "results", "validation", "f1745_element_envelope_map.json")
    eval_json = os.path.join(REPO_ROOT, "results", "validation", "f1745_case3_envelope_evaluation.json")
    
    print("Parsing coarse mesh: %s" % coarse_inp)
    nodes_c, elems_c, types_c = parse_abaqus_inp(coarse_inp)
    
    with open(map_json, "r") as f:
        elem_map = json.load(f)["elements"]
        
    with open(eval_json, "r") as f:
        eval_summary = json.load(f)

    # Extract eta values and dominant states
    eta_vals = {eid: elem_map[eid]["eta"] for eid in elem_map}
    state_vals = {eid: elem_map[eid]["dominant_state"] for eid in elem_map}
    
    # State color palette
    state_colors_palette = {
        "T1": "#1f77b4",  # Blue: Inc 260 primary initiation
        "T2": "#2ca02c",  # Green: Inc 300 primary mid-propagation
        "T3": "#17becf",  # Cyan: Inc 340 primary approach to hole
        "S2": "#ff7f0e",  # Orange: Inc 400 hole arrest
        "S4": "#d62728"   # Red: Inc 600 secondary propagation
    }
    elem_colors = {eid: state_colors_palette.get(state_vals[eid], "#999999") for eid in state_vals}

    # Compute centroids for along-path sampling
    centroids = {}
    for eid, conn in elems_c.items():
        coords = [nodes_c[nid] for nid in conn if nid in nodes_c]
        cx = sum(c[0] for c in coords) / float(len(coords))
        cy = sum(c[1] for c in coords) / float(len(coords))
        centroids[eid] = (cx, cy)

    # Primary path: (10.0, 70.0) to (26.5, 51.0), length L_prim = 24.60 mm
    # Secondary path: (46.5, 50.73) to (65.0, 52.25), length L_sec = 18.56 mm
    def sample_corridor(x1, y1, x2, y2, corridor_w):
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        res = []
        for eid, (cx, cy) in centroids.items():
            t = ((cx - x1)*dx + (cy - y1)*dy) / (L*L)
            if 0.0 <= t <= 1.0:
                dist = math.hypot(cx - (x1 + t*dx), cy - (y1 + t*dy))
                if dist <= corridor_w:
                    res.append((t * L, eta_vals.get(str(eid), 0.0), state_vals.get(str(eid), "T1")))
        res.sort(key=lambda item: item[0])
        return res

    l0 = 0.285
    corridor_w = 2.0 * l0
    prim_samples = sample_corridor(10.0, 70.0, 26.5, 51.0, corridor_w)
    sec_samples = sample_corridor(46.5, 50.73, 65.0, 52.25, corridor_w)

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 1], height_ratios=[1, 1], wspace=0.28, hspace=0.26)

    # Holes definition
    holes = [
        Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
    ]

    # Panel (a): Base Coarse Mesh
    ax_a = fig.add_subplot(gs[:, 0])
    pc_a = build_poly_collection(nodes_c, elems_c, edge_lw=0.2)
    ax_a.add_collection(pc_a)
    for h in [
        Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
    ]:
        ax_a.add_patch(h)
    ax_a.plot([0, 10], [70, 70], color="crimson", linewidth=2.0, zorder=6, label="Initial Notch")
    ax_a.set_xlim(-2, 67)
    ax_a.set_ylim(-2, 122)
    ax_a.set_aspect("equal")
    ax_a.set_xlabel("x [mm]")
    ax_a.set_ylabel("y [mm]")
    ax_a.set_title("(a) Base Coarse Mesh (3,923 Elements)\nPandey & Kumar (2025) Sec 4.3")
    ax_a.grid(True, linestyle=":", alpha=0.5)
    ax_a.text(12, 72, "Notch tip\n(10, 70)", fontsize=7.5, color="crimson", weight="bold")
    ax_a.text(36.5, 51.0, "Center\nHole", ha="center", va="center", fontsize=7.5, zorder=6)
    ax_a.text(20.0, 100.0, "Top\nPin", ha="center", va="center", fontsize=7.0, zorder=6)
    ax_a.text(20.0, 20.0, "Bottom\nPin", ha="center", va="center", fontsize=7.0, zorder=6)

    # Panel (b): Normalized Error-Indicator Envelope
    ax_b = fig.add_subplot(gs[0, 1])
    pc_b = build_poly_collection(nodes_c, elems_c, values=eta_vals, cmap_name="inferno", vmin=0.0, vmax=2.5, edge_lw=0.1)
    ax_b.add_collection(pc_b)
    for h in [
        Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
    ]:
        ax_b.add_patch(h)
    ax_b.plot([0, 10], [70, 70], color="cyan", linewidth=1.5, zorder=6)
    ax_b.set_xlim(-2, 67)
    ax_b.set_ylim(-2, 122)
    ax_b.set_aspect("equal")
    ax_b.set_xlabel("x [mm]")
    ax_b.set_ylabel("y [mm]")
    ax_b.set_title("(b) 5-State Error-Indicator Envelope $\\hat{\\eta}_e^{(\\mathrm{env})}$\nDual-Corridor Activation (Max = 15.71)")
    ax_b.grid(True, linestyle=":", alpha=0.5)
    cbar_b = fig.colorbar(matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=0.0, vmax=2.5), cmap="inferno"), ax=ax_b, fraction=0.046, pad=0.04)
    cbar_b.set_label("Normalized Relative Error $\\hat{\\eta}_e^{(\\mathrm{env})}$")

    # Panel (c): State Dominance Map
    ax_c = fig.add_subplot(gs[0, 2])
    pc_c = build_poly_collection(nodes_c, elems_c, colors_dict=elem_colors, edge_lw=0.1)
    ax_c.add_collection(pc_c)
    for h in [
        Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
        Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
    ]:
        ax_c.add_patch(h)
    ax_c.set_xlim(-2, 67)
    ax_c.set_ylim(-2, 122)
    ax_c.set_aspect("equal")
    ax_c.set_xlabel("x [mm]")
    ax_c.set_ylabel("y [mm]")
    ax_c.set_title("(c) Governing Donor State Dominance\nSpatial Partitioning Across Checkpoints")
    ax_c.grid(True, linestyle=":", alpha=0.5)
    # Legend for states
    legend_elements = [
        matplotlib.patches.Patch(facecolor=state_colors_palette["T1"], edgecolor="black", label="T1: Inc 260 (1,757 el, 44.8%)"),
        matplotlib.patches.Patch(facecolor=state_colors_palette["T2"], edgecolor="black", label="T2: Inc 300 (919 el, 23.4%)"),
        matplotlib.patches.Patch(facecolor=state_colors_palette["T3"], edgecolor="black", label="T3: Inc 340 (1,172 el, 29.9%)"),
        matplotlib.patches.Patch(facecolor=state_colors_palette["S2"], edgecolor="black", label="S2: Inc 400 (30 el, 0.8%)"),
        matplotlib.patches.Patch(facecolor=state_colors_palette["S4"], edgecolor="black", label="S4: Inc 600 (45 el, 1.1%)"),
    ]
    ax_c.legend(handles=legend_elements, loc="lower right", fontsize=7.5, framealpha=0.9)

    # Panel (d): Along-Path Error Profiles
    ax_d = fig.add_subplot(gs[1, 1:])
    
    # Primary path
    s_prim = [item[0] for item in prim_samples]
    eta_prim = [item[1] for item in prim_samples]
    ax_d.plot(s_prim, eta_prim, color="#1f77b4", marker="o", markersize=3.5, linewidth=1.5, label="Primary Corridor (Notch Tip $\\to$ Center Hole, $L = 24.6\\,\\mathrm{mm}$)")
    
    # Secondary path (offset by L_prim + 5 mm for visualization in single sequence)
    offset_sec = 30.0
    s_sec = [item[0] + offset_sec for item in sec_samples]
    eta_sec = [item[1] for item in sec_samples]
    ax_d.plot(s_sec, eta_sec, color="#d62728", marker="s", markersize=3.5, linewidth=1.5, label="Secondary Corridor (Center Hole $\\to$ Right Boundary, $L = 18.6\\,\\mathrm{mm}$)")
    
    # Baseline mean reference line
    mean_bg = eval_summary["envelope_statistics"]["mean"]
    ax_d.axhline(mean_bg, color="gray", linestyle="--", linewidth=1.0, label="Global Mean Background $\\bar{\\eta} = 0.122$")
    ax_d.axhline(1.0, color="black", linestyle=":", linewidth=1.0, label="Nominal Sizing Level $\\hat{\\eta} = 1.0$")

    ax_d.set_xlabel("Along-Path Coordinate $s$ [mm] (Primary: $0 \\to 24.6\\,\\mathrm{mm}$ | Secondary: $30 \\to 48.6\\,\\mathrm{mm}$)")
    ax_d.set_ylabel("Normalized Relative Error Indicator $\\hat{\\eta}_e^{(\\mathrm{env})}$")
    ax_d.set_title("(d) Quantitative Dual-Corridor Error Profiles: Continuous Fracture Path Coverage")
    ax_d.set_yscale("log")
    ax_d.set_ylim(0.005, 20.0)
    ax_d.grid(True, which="both", linestyle=":", alpha=0.5)
    ax_d.legend(loc="upper right", fontsize=8.5, framealpha=0.9)
    
    # Annotations on (d)
    ax_d.text(2.0, 10.0, "Notch root\n$\\hat{\\eta} = 15.71$", fontsize=8, color="#1f77b4", weight="bold")
    ax_d.text(18.0, 1.5, "Primary Ligament\n$\\bar{\\eta} = 1.59$ ($13\\times$ bg)", fontsize=8, color="#1f77b4")
    ax_d.text(38.0, 1.2, "Secondary Ligament\n$\\bar{\\eta} = 0.25$ ($2\\times$ bg)", fontsize=8, color="#d62728")

    out_png = os.path.join(FIG_DIR, "fig_f1745_case3_envelope_synthesis.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1745_case3_envelope_synthesis.pdf")
    
    plt.savefig(out_png, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    
    print("SUCCESS: Publication figures saved:")
    print("  PNG: %s" % out_png)
    print("  PDF: %s" % out_pdf)

if __name__ == '__main__':
    main()
