# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1744_case3_mesh.py

Generates publication-quality figure for Task F1744 Case 3 5-State Sequential Native Remeshing:
  - Panel (a): Original Coarse Mesh (3,923 elements)
  - Panel (b): F1744 5-State Native Adapted Mesh (19,005 elements, 96.6% quads)
  - Panel (c): Spatial Resolution Map h_e / l0
  - Panel (d): 10-Station Along-Path Spatial Resolution Profiles (Primary vs Secondary Corridors)
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

from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp, compute_element_metrics

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

def build_poly_collection(nodes, elements, values=None, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.15):
    verts = []
    vals = []
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) >= 3:
            verts.append(coords)
            if values and eid in values:
                vals.append(values[eid])
            else:
                vals.append(0.0)
    
    if values is not None:
        cmap = plt.get_cmap(cmap_name)
        norm = plt.Normalize(vmin=vmin, vmax=vmax)
        colors = cmap(norm(vals))
        pc = PolyCollection(verts, facecolors=colors, edgecolors="black", linewidths=edge_lw)
    else:
        pc = PolyCollection(verts, facecolors="#d9e6f2", edgecolors="#2b4c7e", linewidths=edge_lw)
    return pc

def main():
    coarse_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp")
    adapt_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "230_f1744_case3_5state_remesh", "PK_F1744_CASE_3_ADAPT_PHYS.inp")
    audit_json = os.path.join(REPO_ROOT, "results", "validation", "f1744_case3_spatial_audit.json")
    
    print("Parsing coarse mesh: %s" % coarse_inp)
    nodes_c, elems_c, types_c = parse_abaqus_inp(coarse_inp)
    
    print("Parsing adapted mesh: %s" % adapt_inp)
    nodes_a, elems_a, types_a = parse_abaqus_inp(adapt_inp)
    l0 = 0.285  # mm
    stats_a = compute_element_metrics(nodes_a, elems_a, types_a, l0)
    
    res_ratios = {}
    for eid, nids in elems_a.items():
        coords = np.array([nodes_a[nid] for nid in nids])
        x = coords[:, 0]
        y = coords[:, 1]
        area = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
        h = math.sqrt(area)
        res_ratios[eid] = h / l0
    
    with open(audit_json, "r") as f:
        audit_data = json.load(f)
        
    fig = plt.figure(figsize=(15, 9.5))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.0, 0.75], hspace=0.30, wspace=0.25)
    
    ax_coarse = fig.add_subplot(gs[0, 0])
    ax_adapt = fig.add_subplot(gs[0, 1])
    ax_res = fig.add_subplot(gs[1, 0])
    ax_stat = fig.add_subplot(gs[1, 1])
    
    # 1. Panel (a): Coarse Mesh
    pc_c = build_poly_collection(nodes_c, elems_c, edge_lw=0.25)
    ax_coarse.add_collection(pc_c)
    ax_coarse.set_xlim(-2.0, 67.0)
    ax_coarse.set_ylim(-2.0, 122.0)
    ax_coarse.set_aspect("equal")
    ax_coarse.set_xlabel("x [mm]")
    ax_coarse.set_ylabel("y [mm]")
    ax_coarse.set_title("(a) Initial Coarse Physical Mesh\n(3,923 elements, 97.2% CPE4)")
    ax_coarse.grid(True, linestyle=":", alpha=0.5)
    
    # Annotate holes
    ax_coarse.add_patch(Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.0))
    ax_coarse.add_patch(Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    ax_coarse.add_patch(Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    
    # 2. Panel (b): F1744 5-State Adapted Mesh
    pc_a = build_poly_collection(nodes_a, elems_a, edge_lw=0.12)
    ax_adapt.add_collection(pc_a)
    ax_adapt.set_xlim(-2.0, 67.0)
    ax_adapt.set_ylim(-2.0, 122.0)
    ax_adapt.set_aspect("equal")
    ax_adapt.set_xlabel("x [mm]")
    ax_adapt.set_ylabel("y [mm]")
    ax_adapt.set_title("(b) Task F1744 5-State Native Adapted Mesh\n(%d elements, %.1f%% CPE4)" % (
        len(elems_a), audit_data["quad_percentage"]
    ))
    ax_adapt.grid(True, linestyle=":", alpha=0.5)
    ax_adapt.add_patch(Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.0))
    ax_adapt.add_patch(Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    ax_adapt.add_patch(Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    
    # 3. Panel (c): Spatial Resolution Map h_e / l0
    pc_res = build_poly_collection(nodes_a, elems_a, values=res_ratios, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.08)
    ax_res.add_collection(pc_res)
    ax_res.set_xlim(-2.0, 67.0)
    ax_res.set_ylim(-2.0, 122.0)
    ax_res.set_aspect("equal")
    ax_res.set_xlabel("x [mm]")
    ax_res.set_ylabel("y [mm]")
    ax_res.set_title("(c) Spatial Resolution Ratio Map ($h_e / \\ell_0$)\n($\\ell_0 = 0.285$ mm, $\\ell_0/2 = 0.1425$ mm)")
    ax_res.grid(True, linestyle=":", alpha=0.5)
    ax_res.add_patch(Circle((36.5, 51.0), 10.0, fill=True, color="white", ec="black", lw=1.0))
    ax_res.add_patch(Circle((20.0, 20.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    ax_res.add_patch(Circle((20.0, 100.0), 5.0, fill=True, color="white", ec="black", lw=1.0))
    
    # Add colorbar
    cmap = plt.get_cmap("viridis_r")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(vmin=0.0, vmax=3.0))
    sm.set_array([])
    cb = fig.colorbar(sm, ax=ax_res, orientation="vertical", shrink=0.85, pad=0.02)
    cb.set_label("Resolution Ratio $h_e / \\ell_0$ (capped at 3.0)")
    
    # 4. Panel (d): 10-Station Along-Path Spatial Resolution Profiles
    stations = np.arange(1, 11)
    prim_means = [s["mean_h_mm"] for s in audit_data["primary_corridor"]["stations"]]
    prim_mins = [s["min_h_mm"] for s in audit_data["primary_corridor"]["stations"]]
    sec_means = [s["mean_h_mm"] for s in audit_data["secondary_corridor"]["stations"]]
    sec_mins = [s["min_h_mm"] for s in audit_data["secondary_corridor"]["stations"]]
    
    ax_stat.plot(stations, prim_means, "o-", color="#d95f02", lw=1.8, ms=5, label="Primary Mean $h$ (Notch $\\to$ Hole)")
    ax_stat.plot(stations, prim_mins, "o--", color="#d95f02", alpha=0.5, lw=1.2, ms=4, label="Primary Min $h$")
    ax_stat.plot(stations, sec_means, "s-", color="#1b9e77", lw=1.8, ms=5, label="Secondary Mean $h$ (Hole $\\to$ Right Boundary)")
    ax_stat.plot(stations, sec_mins, "s--", color="#1b9e77", alpha=0.5, lw=1.2, ms=4, label="Secondary Min $h$")
    
    # Gate thresholds
    ax_stat.axhline(l0, color="gray", linestyle=":", lw=1.2, label="$\\ell_0 = 0.285$ mm")
    ax_stat.axhline(l0/2.0, color="red", linestyle="--", lw=1.4, label="$\\ell_0/2 = 0.1425$ mm (Gate Threshold)")
    
    ax_stat.set_xlabel("10-Station Sampling Station Index along Trajectory")
    ax_stat.set_ylabel("Element Size $h_e$ [mm]")
    ax_stat.set_title("(d) 10-Station Quantitative Along-Path Resolution Audit\n(Sequential Pass Architecture Evaluation)")
    ax_stat.set_xticks(stations)
    ax_stat.set_ylim(0.0, 1.8)
    ax_stat.grid(True, linestyle=":", alpha=0.6)
    ax_stat.legend(loc="upper right", frameon=True, fontsize=7.5)
    
    # Text box with key findings
    text_box = (
        "TASK F1744 AUDIT FINDINGS:\n"
        "• Elements: 19,005 (96.6% CPE4 quads)\n"
        "• min det(J): 0.01215 > 0 (100% positive)\n"
        "• Primary Corridor: Mean h = 0.695 mm (0.04% <= l0/2)\n"
        "• Secondary Corridor: Mean h = 0.290 mm (0.29% <= l0/2)\n"
        "• Root Cause (Pass-Memory Loss): Pass 5 (State 4)\n"
        "  coarsened primary ligament (previously 90k el in T2/T3)\n"
        "• Architectural Solution: Multi-State Error Envelope"
    )
    ax_stat.text(0.03, 0.45, text_box, transform=ax_stat.transAxes, fontsize=7.5,
                 verticalalignment="center", bbox=dict(boxstyle="round,pad=0.5", facecolor="#fff2cc", edgecolor="#d6b656", alpha=0.9))
    
    out_png = os.path.join(FIG_DIR, "fig_f1744_case3_5state_mesh_comparison.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1744_case3_5state_mesh_comparison.pdf")
    
    plt.savefig(out_png, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    
    print("Figure generated: %s" % out_png)
    print("Figure generated: %s" % out_pdf)

if __name__ == "__main__":
    main()
