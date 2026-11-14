# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1741_case3_mesh.py

Generates publication-quality figure for Task F1741 Case 3 Controlled Multi-State Native Remeshing:
  - Panel (a): Original Coarse Mesh (3,923 elements)
  - Panel (b): Multi-State Native Adapted Mesh (28,933 elements, 96.9% quads)
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
    adapt_inp = os.path.join(REPO_ROOT, "results", "validation", "f1741_case3_multistate_evidence", "PK_F1741_CASE_3_ADAPT_PHYS.inp")
    audit_json = os.path.join(REPO_ROOT, "results", "validation", "f1741_case3_multistate_evidence", "f1741_case3_spatial_audit.json")
    
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
    ax_coarse.set_xlim(-2, 67)
    ax_coarse.set_ylim(-2, 122)
    ax_coarse.set_aspect("equal")
    ax_coarse.set_title("(a) Case 3 Coarse Donor Mesh\n3,923 elements (3,814 CPE4, 109 CPE3)", fontweight="bold")
    ax_coarse.set_xlabel("x [mm]")
    ax_coarse.set_ylabel("y [mm]")
    ax_coarse.grid(True, linestyle=":", alpha=0.4)
    
    # Holes
    for (cx, cy, r) in [(36.5, 51.0, 10.0), (20.0, 20.0, 5.0), (20.0, 100.0, 5.0)]:
        ax_coarse.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="black", lw=0.8, zorder=5))
        ax_adapt.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="black", lw=0.8, zorder=5))
        ax_res.add_patch(Circle((cx, cy), r, facecolor="white", edgecolor="black", lw=0.8, zorder=5))
    
    # 2. Panel (b): Adapted Mesh
    pc_a = build_poly_collection(nodes_a, elems_a, edge_lw=0.08)
    ax_adapt.add_collection(pc_a)
    ax_adapt.set_xlim(-2, 67)
    ax_adapt.set_ylim(-2, 122)
    ax_adapt.set_aspect("equal")
    ax_adapt.set_title("(b) Task F1741 Multi-State Adapted Mesh\n28,933 physical elements (96.91% CPE4, 100% det(J) > 0)", fontweight="bold")
    ax_adapt.set_xlabel("x [mm]")
    ax_adapt.set_ylabel("y [mm]")
    ax_adapt.grid(True, linestyle=":", alpha=0.4)
    
    # 3. Panel (c): Resolution Ratio h_e / l0
    pc_r = build_poly_collection(nodes_a, elems_a, values=res_ratios, cmap_name="viridis_r", vmin=0.0, vmax=2.5, edge_lw=0.05)
    ax_res.add_collection(pc_r)
    ax_res.set_xlim(-2, 67)
    ax_res.set_ylim(-2, 122)
    ax_res.set_aspect("equal")
    ax_res.set_title(r"(c) Spatial Resolution Ratio $h_e / \ell_0$ ($\ell_0 = 0.285\,\mathrm{mm}$)" + "\n" + r"[Yellow $\leq 0.5$, Purple $\geq 2.5$]", fontweight="bold")
    ax_res.set_xlabel("x [mm]")
    ax_res.set_ylabel("y [mm]")
    ax_res.grid(True, linestyle=":", alpha=0.4)
    
    cbar = fig.colorbar(pc_r, ax=ax_res, orientation="vertical", shrink=0.75, pad=0.02)
    cbar.set_label(r"Resolution Ratio $h_e / \ell_0$")
    
    # 4. Panel (d): 10-Station Along-Path Spatial Profiles
    stations = list(range(1, 11))
    pri_means = [s['mean_h_mm'] for s in audit_data['primary_corridor']['stations']]
    pri_mins = [s['min_h_mm'] for s in audit_data['primary_corridor']['stations']]
    sec_means = [s['mean_h_mm'] for s in audit_data['secondary_corridor']['stations']]
    sec_mins = [s['min_h_mm'] for s in audit_data['secondary_corridor']['stations']]
    
    ax_stat.plot(stations, pri_means, "s-", color="#c0392b", lw=1.8, label=r"Primary Corridor Mean $h$ (Notch $\to$ Hole)")
    ax_stat.plot(stations, pri_mins, "s--", color="#e74c3c", lw=1.0, alpha=0.7, label=r"Primary Corridor Min $h$")
    ax_stat.plot(stations, sec_means, "o-", color="#2980b9", lw=1.8, label=r"Secondary Corridor Mean $h$ (Hole $\to$ Edge)")
    ax_stat.plot(stations, sec_mins, "o--", color="#3498db", lw=1.0, alpha=0.7, label=r"Secondary Corridor Min $h$")
    
    ax_stat.axhline(l0 / 2.0, color="green", linestyle="--", lw=1.5, label=r"Physical Acceptance Target $\ell_0/2 = 0.1425\,\mathrm{mm}$")
    ax_stat.axhline(l0, color="orange", linestyle=":", lw=1.5, label=r"Characteristic Length $\ell_0 = 0.285\,\mathrm{mm}$")
    
    ax_stat.set_xlim(0.5, 10.5)
    ax_stat.set_xticks(stations)
    ax_stat.set_xlabel("Along-Path Discretization Station (1 = Origin, 10 = Destination)")
    ax_stat.set_ylabel("Element Size $h$ [mm]")
    ax_stat.set_title("(d) 10-Station Quantitative Corridor Resolution\nPrimary (Notch $\to$ Hole) vs Secondary (Hole $\to$ Edge)", fontweight="bold")
    ax_stat.grid(True, linestyle=":", alpha=0.5)
    ax_stat.legend(loc="upper left", fontsize=8, framealpha=0.9)
    
    ax_stat.text(0.98, 0.45, "TASK F1741 SPATIAL AUDIT:\n"
                              "- Primary Corridor: FAIL (Stations 2-10 coarse, barrier=True)\n"
                              "- Secondary Corridor: FAIL (Distal stations coarse, barrier=True)\n"
                              "- Central Hole Boundary: FAIL (mean h = 0.322 mm > l0/2)\n"
                              "CLASSIFICATION: SPATIAL QUALIFICATION FAILED",
                 transform=ax_stat.transAxes, fontsize=8, verticalalignment='center', horizontalalignment='right',
                 bbox=dict(boxstyle='round,pad=0.5', facecolor='#fce4e4', edgecolor='#c0392b', lw=1.2))
    
    fig.suptitle("Task F1741: Case 3 Notched Plate with Hole and Pins Multi-State Native Remeshing Synthesis\n"
                 "[STATUS: SPATIAL QUALIFICATION FAILED (FAIL) — Primary 2.13% Area <= l0/2, Secondary 14.22% Area <= l0/2]\n"
                 "(HPC Execution Job 1423438.mmaster02, Compute Node mnode097.cluster, 28,933 Elements, Datacheck Exit 0)",
                 fontsize=12, fontweight="bold", color="#900C3F", y=0.99)
    
    png_path = os.path.join(FIG_DIR, "fig_f1741_case3_mesh_comparison.png")
    pdf_path = os.path.join(FIG_DIR, "fig_f1741_case3_mesh_comparison.pdf")
    
    plt.savefig(png_path, dpi=300, bbox_inches="tight")
    plt.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close()
    
    print("Saved publication figure: %s" % png_path)
    print("Saved vector figure: %s" % pdf_path)

if __name__ == "__main__":
    main()
