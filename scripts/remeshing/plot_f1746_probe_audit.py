# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1746_probe_audit.py

Generates 4-panel publication-quality figure for Task F1746:
Case 3 (Sec 4.3 Rectangular Notched Plate with Hole and Pins)
Single-Pass 5-State Error-Indicator Envelope Native Remeshing Probe Audit.

Panels:
  (a) Base Coarse Mesh (3,923 elements) with 5-State Error-Indicator Envelope eta_hat_e^(env)
  (b) Probe Adapted Mesh (120,554 elements) with Spatial Resolution Ratio R_e = h_e / l0
  (c) Primary Corridor 10-Station Longitudinal Mean Resolution Profile Comparison (F1741 vs F1744 vs F1746 Probe)
  (d) Secondary Corridor 10-Station Longitudinal Mean Resolution Profile Comparison (F1741 vs F1744 vs F1746 Probe)
"""

import os
import sys
import math
import json
import time
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

def build_poly_collection(nodes, elements, values=None, cmap_name="viridis_r", vmin=0.0, vmax=3.0, edge_lw=0.1, edge_color="black"):
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
        pc = PolyCollection(verts, facecolors=c_list, edgecolors=edge_color, linewidths=edge_lw)
    else:
        for eid, conn in elements.items():
            coords = [nodes[nid] for nid in conn if nid in nodes]
            if len(coords) >= 3:
                verts.append(coords)
        pc = PolyCollection(verts, facecolors="#d9e6f2", edgecolors="#2b4c7e", linewidths=edge_lw)
    return pc

def main():
    t0 = time.time()
    coarse_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp")
    probe_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "231_f1746_case3_envelope_remesh", "PK_F1746_PROBE_TRIAL.inp")
    map_json = os.path.join(REPO_ROOT, "results", "validation", "f1745_element_envelope_map.json")
    f1741_json = os.path.join(REPO_ROOT, "results", "validation", "f1741_case3_multistate_summary.json")
    f1744_json = os.path.join(REPO_ROOT, "results", "validation", "f1744_case3_spatial_audit.json")
    f1746_json = os.path.join(REPO_ROOT, "results", "validation", "f1746_probe_spatial_audit.json")
    
    print("1. Parsing coarse base mesh: %s" % coarse_inp)
    nodes_c, elems_c, types_c = parse_abaqus_inp(coarse_inp)
    with open(map_json, "r", encoding="utf-8-sig") as f:
        elem_map = json.load(f)["elements"]
    eta_vals = {eid: elem_map[eid]["eta"] for eid in elem_map}

    print("2. Parsing 120k probe adapted mesh: %s" % probe_inp)
    nodes_p, elems_p, types_p = parse_abaqus_inp(probe_inp)
    print("   Parsed %d nodes, %d elements in %.2fs" % (len(nodes_p), len(elems_p), time.time() - t0))

    l0 = 0.285  # mm
    print("3. Computing element sizes and resolution ratios for probe mesh...")
    res_ratios = {}
    for eid, conn in elems_p.items():
        coords = np.array([nodes_p[nid] for nid in conn if nid in nodes_p])
        if len(coords) >= 3:
            x = coords[:, 0]
            y = coords[:, 1]
            area = 0.5 * abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y))
            h = math.sqrt(area)
            res_ratios[eid] = h / l0

    print("4. Loading station audit JSON summaries...")
    with open(f1741_json, "r", encoding="utf-8-sig") as f:
        data_f1741 = json.load(f)["mesh_metrics"]
    with open(f1744_json, "r", encoding="utf-8-sig") as f:
        data_f1744 = json.load(f)
    with open(f1746_json, "r", encoding="utf-8-sig") as f:
        data_f1746 = json.load(f)

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.0, 0.85], hspace=0.28, wspace=0.25)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    # Holes definition helper
    def add_holes(ax):
        for h in [
            Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
            Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
            Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
        ]:
            ax.add_patch(h)

    # Panel (a): Base Mesh with 5-State Error Envelope
    print("5. Rendering Panel (a): Base coarse mesh with 5-state envelope...")
    pc_a = build_poly_collection(nodes_c, elems_c, values=eta_vals, cmap_name="inferno", vmin=0.0, vmax=2.5, edge_lw=0.15)
    ax_a.add_collection(pc_a)
    add_holes(ax_a)
    ax_a.plot([0, 10], [70, 70], color="cyan", linewidth=1.8, zorder=6, label="Initial Notch")
    ax_a.set_xlim(-2, 67)
    ax_a.set_ylim(-2, 122)
    ax_a.set_aspect("equal")
    ax_a.set_xlabel("x [mm]")
    ax_a.set_ylabel("y [mm]")
    ax_a.set_title("(a) Base Mesh (3,923 el) with 5-State Envelope $\\hat{\\eta}_e^{(\\mathrm{env})}$\nDual-Corridor Activation (Primary: $13\\times$ bg, Secondary: $2\\times$ bg)")
    ax_a.grid(True, linestyle=":", alpha=0.5)
    cbar_a = fig.colorbar(matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=0.0, vmax=2.5), cmap="inferno"), ax=ax_a, fraction=0.046, pad=0.04)
    cbar_a.set_label("Normalized Relative Error $\\hat{\\eta}_e^{(\\mathrm{env})}$")
    ax_a.text(12, 72, "Notch tip\n(10, 70)", fontsize=7.5, color="cyan", weight="bold")
    ax_a.text(36.5, 51.0, "Center\nHole", ha="center", va="center", fontsize=7.5, zorder=6)
    ax_a.text(20.0, 100.0, "Top\nPin", ha="center", va="center", fontsize=7.0, zorder=6)
    ax_a.text(20.0, 20.0, "Bottom\nPin", ha="center", va="center", fontsize=7.0, zorder=6)

    # Panel (b): Probe Adapted Mesh with Resolution Ratio R_e = h_e / l0
    print("6. Rendering Panel (b): 120k probe adapted mesh...")
    pc_b = build_poly_collection(nodes_p, elems_p, values=res_ratios, cmap_name="viridis_r", vmin=0.0, vmax=2.0, edge_lw=0.05, edge_color="none")
    ax_b.add_collection(pc_b)
    add_holes(ax_b)
    ax_b.plot([0, 10], [70, 70], color="crimson", linewidth=1.8, zorder=6)
    ax_b.set_xlim(-2, 67)
    ax_b.set_ylim(-2, 122)
    ax_b.set_aspect("equal")
    ax_b.set_xlabel("x [mm]")
    ax_b.set_ylabel("y [mm]")
    ax_b.set_title("(b) Single-Pass Envelope Probe Mesh (120,554 el, 97.4% Quads)\nSpatial Resolution Ratio $R_e = h_e / \\ell_0$ (Capped at 2.0)")
    ax_b.grid(True, linestyle=":", alpha=0.5)
    cbar_b = fig.colorbar(matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=0.0, vmax=2.0), cmap="viridis_r"), ax=ax_b, fraction=0.046, pad=0.04)
    cbar_b.set_label("Resolution Ratio $R_e = h_e / \\ell_0$ ($h_e \\leq \\ell_0/2 \\rightarrow R_e \\leq 0.5$)")
    ax_b.text(36.5, 51.0, "Center\nHole", ha="center", va="center", fontsize=7.5, zorder=6)
    ax_b.text(20.0, 100.0, "Top\nPin", ha="center", va="center", fontsize=7.0, zorder=6)
    ax_b.text(20.0, 20.0, "Bottom\nPin", ha="center", va="center", fontsize=7.0, zorder=6)
    ax_b.text(12, 66, "Primary: $h_{\\mathrm{min}}=0.087\\,\\mathrm{mm}$ ($\\ell_0/3.3$)", fontsize=7.5, color="white", weight="bold",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.6))
    ax_b.text(47, 44, "Secondary: $h_{\\mathrm{min}}=0.107\\,\\mathrm{mm}$ ($\\ell_0/2.7$)", fontsize=7.5, color="white", weight="bold",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="black", alpha=0.6))

    # Panel (c): Primary Corridor 10-Station Longitudinal Mean Resolution Profile
    print("7. Rendering Panel (c): Primary corridor profile comparison...")
    stations = np.arange(1, 11)
    # Extract mean h / l0 for primary corridor
    h_f1741_p = [s["mean_h_mm"] / l0 for s in data_f1741["primary_corridor"]["stations"]]
    h_f1744_p = [s["mean_h_mm"] / l0 for s in data_f1744["primary_corridor"]["stations"]]
    h_f1746_p = [s["mean_h_mm"] / l0 for s in data_f1746["primary_corridor"]["stations"]]

    ax_c.plot(stations, h_f1741_p, "s--", color="#ff7f0e", linewidth=1.5, markersize=5, label="F1741: 2-Pass Sequential (S2 $\\to$ S4, 28k el)")
    ax_c.plot(stations, h_f1744_p, "^-.", color="#d62728", linewidth=1.5, markersize=5, label="F1744: 5-Pass Sequential (Pass-Memory Loss, 19k el)")
    ax_c.plot(stations, h_f1746_p, "o-", color="#1f77b4", linewidth=2.0, markersize=6, label="F1746 Probe: 1-Pass 5-State Envelope (120k el)")

    # Reference lines
    ax_c.axhline(1.0, color="darkgray", linestyle=":", linewidth=1.2, label="Resolution Limit $h = \\ell_0$ ($0.285\\,\\mathrm{mm}$)")
    ax_c.axhline(0.5, color="forestgreen", linestyle="--", linewidth=1.2, label="Target Resolution $h = \\ell_0/2$ ($0.1425\\,\\mathrm{mm}$)")
    ax_c.axhline(1.0/3.0, color="purple", linestyle="--", linewidth=1.0, label="Fine Resolution $h = \\ell_0/3$ ($0.0950\\,\\mathrm{mm}$)")

    ax_c.set_xlabel("Longitudinal Station Along Primary Corridor (Notch Tip $\\to$ Center Hole)")
    ax_c.set_ylabel("Normalized Element Size $\\bar{h} / \\ell_0$")
    ax_c.set_title("(c) Primary Corridor: 10-Station Mean Resolution Profile\n(Notch Root at Station 1 $\\to$ Approach to Hole at Station 10)")
    ax_c.set_xticks(stations)
    ax_c.set_ylim(0.0, 4.5)
    ax_c.grid(True, linestyle=":", alpha=0.5)
    ax_c.legend(loc="upper left", fontsize=8.0, framealpha=0.9)
    ax_c.text(8.0, 3.8, "F1744 Pass-Memory Loss\n($h \\approx 2.5 - 4.5\\,\\ell_0$)", fontsize=7.5, color="#d62728", ha="center")
    ax_c.text(5.0, 0.85, "F1746 Probe: Continuous Across All Stations\n($h \\approx 0.6 - 1.0\\,\\ell_0$, $h_{\\mathrm{min}} \\leq \\ell_0/3$)", fontsize=7.5, color="#1f77b4", weight="bold")

    # Panel (d): Secondary Corridor 10-Station Longitudinal Mean Resolution Profile
    print("8. Rendering Panel (d): Secondary corridor profile comparison...")
    h_f1741_s = [s["mean_h_mm"] / l0 for s in data_f1741["secondary_corridor"]["stations"]]
    h_f1744_s = [s["mean_h_mm"] / l0 for s in data_f1744["secondary_corridor"]["stations"]]
    h_f1746_s = [s["mean_h_mm"] / l0 for s in data_f1746["secondary_corridor"]["stations"]]

    ax_d.plot(stations, h_f1741_s, "s--", color="#ff7f0e", linewidth=1.5, markersize=5, label="F1741: 2-Pass Sequential (S2 $\\to$ S4, 28k el)")
    ax_d.plot(stations, h_f1744_s, "^-.", color="#d62728", linewidth=1.5, markersize=5, label="F1744: 5-Pass Sequential (Pass-Memory Loss, 19k el)")
    ax_d.plot(stations, h_f1746_s, "o-", color="#1f77b4", linewidth=2.0, markersize=6, label="F1746 Probe: 1-Pass 5-State Envelope (120k el)")

    # Reference lines
    ax_d.axhline(1.0, color="darkgray", linestyle=":", linewidth=1.2, label="Resolution Limit $h = \\ell_0$ ($0.285\\,\\mathrm{mm}$)")
    ax_d.axhline(0.5, color="forestgreen", linestyle="--", linewidth=1.2, label="Target Resolution $h = \\ell_0/2$ ($0.1425\\,\\mathrm{mm}$)")
    ax_d.axhline(1.0/3.0, color="purple", linestyle="--", linewidth=1.0, label="Fine Resolution $h = \\ell_0/3$ ($0.0950\\,\\mathrm{mm}$)")

    ax_d.set_xlabel("Longitudinal Station Along Secondary Corridor (Center Hole $\\to$ Right Boundary)")
    ax_d.set_ylabel("Normalized Element Size $\\bar{h} / \\ell_0$")
    ax_d.set_title("(d) Secondary Corridor: 10-Station Mean Resolution Profile\n(Right Hole Flank at Station 1 $\\to$ Outer Boundary at Station 10)")
    ax_d.set_xticks(stations)
    ax_d.set_ylim(0.0, 2.0)
    ax_d.grid(True, linestyle=":", alpha=0.5)
    ax_d.legend(loc="upper right", fontsize=8.0, framealpha=0.9)
    ax_d.text(3.5, 0.40, "F1741 reaches $\\ell_0/2$\n(Stations 2-4)", fontsize=7.5, color="#ff7f0e", ha="center")
    ax_d.text(7.5, 1.05, "F1746 Probe: $\\bar{h} \\approx 0.8 - 1.0\\,\\ell_0$\n($h_{\\mathrm{min}} = 0.107\\,\\mathrm{mm} \\leq \\ell_0/2$)", fontsize=7.5, color="#1f77b4", weight="bold")

    out_png = os.path.join(FIG_DIR, "fig_f1746_probe_audit.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1746_probe_audit.pdf")

    print("9. Saving high-resolution figures: %s ..." % out_png)
    plt.savefig(out_png, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()

    print("SUCCESS: Figure saved in %.2fs" % (time.time() - t0))
    print("  PNG: %s" % out_png)
    print("  PDF: %s" % out_pdf)

if __name__ == '__main__':
    main()
