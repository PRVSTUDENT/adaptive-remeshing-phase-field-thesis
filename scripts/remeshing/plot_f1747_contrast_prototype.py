# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1747_contrast_prototype.py

Generates 4-panel publication-quality figure for Task F1747:
Case 3 (Sec 4.3 Rectangular Notched Plate with Hole and Pins)
Geometry-Independent Nonlinear Indicator-Contrast Transformation Prototype.

Panels:
  (a) Unmodified 5-State Normalized Error-Indicator Envelope eta_hat_e^(env) (Base 3,923 elements)
  (b) Transformed Nonlinear Contrast Indicator eta_tilde_e (Candidate B, 79.1% Background Suppression)
  (c) Global Indicator Distribution & Predeclared Statistical Threshold Selection (tau = Median + IQR)
  (d) Dual-Corridor Along-Path Profiles: Raw vs Transformed Contrast Enhancement
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

def build_poly_collection(nodes, elements, values=None, cmap_name="inferno", vmin=0.0, vmax=2.5, edge_lw=0.15, zero_color="#e6eff8"):
    verts = []
    c_list = []
    cmap = plt.get_cmap(cmap_name)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    for eid, conn in elements.items():
        coords = [nodes[nid] for nid in conn if nid in nodes]
        if len(coords) >= 3:
            verts.append(coords)
            val = values.get(str(eid), values.get(eid, 0.0))
            if val <= 1e-6:
                c_list.append(zero_color)
            else:
                c_list.append(cmap(norm(val)))
    pc = PolyCollection(verts, facecolors=c_list, edgecolors="black", linewidths=edge_lw)
    return pc

def main():
    coarse_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp")
    raw_map_json = os.path.join(REPO_ROOT, "results", "validation", "f1745_element_envelope_map.json")
    trans_map_json = os.path.join(REPO_ROOT, "results", "validation", "f1747_transformed_envelope_map.json")
    summary_json = os.path.join(REPO_ROOT, "results", "validation", "f1747_contrast_prototype_summary.json")

    print("1. Parsing coarse base mesh: %s" % coarse_inp)
    nodes_c, elems_c, types_c = parse_abaqus_inp(coarse_inp)

    with open(raw_map_json, "r", encoding="utf-8-sig") as f:
        raw_map = json.load(f)["elements"]
    eta_raw = {eid: raw_map[eid]["eta"] for eid in raw_map}

    with open(trans_map_json, "r", encoding="utf-8-sig") as f:
        trans_data = json.load(f)
    eta_trans = trans_data["elements"]
    params = trans_data["parameters"]

    with open(summary_json, "r", encoding="utf-8-sig") as f:
        summary_data = json.load(f)

    # Compute centroids for along-path sampling
    centroids = {}
    for eid, conn in elems_c.items():
        coords = [nodes_c[nid] for nid in conn if nid in nodes_c]
        cx = sum(c[0] for c in coords) / float(len(coords))
        cy = sum(c[1] for c in coords) / float(len(coords))
        centroids[eid] = (cx, cy)

    l0 = 0.285
    corridor_w = 2.0 * l0

    def sample_corridor(x1, y1, x2, y2, corridor_w, val_dict):
        dx = x2 - x1
        dy = y2 - y1
        L = math.hypot(dx, dy)
        res = []
        for eid, (cx, cy) in centroids.items():
            t = ((cx - x1)*dx + (cy - y1)*dy) / (L*L)
            if 0.0 <= t <= 1.0:
                dist = math.hypot(cx - (x1 + t*dx), cy - (y1 + t*dy))
                if dist <= corridor_w:
                    res.append((t * L, val_dict.get(str(eid), 0.0)))
        res.sort(key=lambda item: item[0])
        return res

    prim_raw = sample_corridor(10.0, 70.0, 26.5, 51.0, corridor_w, eta_raw)
    prim_trans = sample_corridor(10.0, 70.0, 26.5, 51.0, corridor_w, eta_trans)
    sec_raw = sample_corridor(46.5, 50.73, 65.0, 52.25, corridor_w, eta_raw)
    sec_trans = sample_corridor(46.5, 50.73, 65.0, 52.25, corridor_w, eta_trans)

    fig = plt.figure(figsize=(15, 10))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.0, 1.0], height_ratios=[1.0, 0.85], hspace=0.28, wspace=0.25)

    ax_a = fig.add_subplot(gs[0, 0])
    ax_b = fig.add_subplot(gs[0, 1])
    ax_c = fig.add_subplot(gs[1, 0])
    ax_d = fig.add_subplot(gs[1, 1])

    def add_holes(ax):
        for h in [
            Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
            Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5),
            Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="black", linewidth=0.8, zorder=5)
        ]:
            ax.add_patch(h)

    # Panel (a): Raw Envelope
    print("2. Rendering Panel (a): Raw envelope...")
    pc_a = build_poly_collection(nodes_c, elems_c, values=eta_raw, cmap_name="inferno", vmin=0.0, vmax=2.5, edge_lw=0.15)
    ax_a.add_collection(pc_a)
    add_holes(ax_a)
    ax_a.plot([0, 10], [70, 70], color="cyan", linewidth=1.8, zorder=6, label="Initial Notch")
    ax_a.set_xlim(-2, 67)
    ax_a.set_ylim(-2, 122)
    ax_a.set_aspect("equal")
    ax_a.set_xlabel("x [mm]")
    ax_a.set_ylabel("y [mm]")
    ax_a.set_title("(a) Unmodified Error Envelope $\\hat{\\eta}_e^{(\\mathrm{env})}$\n(Mean Background $\\bar{\\eta} = 0.122$, Noise Spreads Globally)")
    ax_a.grid(True, linestyle=":", alpha=0.5)
    cbar_a = fig.colorbar(matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=0.0, vmax=2.5), cmap="inferno"), ax=ax_a, fraction=0.046, pad=0.04)
    cbar_a.set_label("Raw Relative Error $\\hat{\\eta}_e^{(\\mathrm{env})}$")
    ax_a.text(12, 72, "Notch tip\n(10, 70)", fontsize=7.5, color="cyan", weight="bold")
    ax_a.text(36.5, 51.0, "Center\nHole", ha="center", va="center", fontsize=7.5, zorder=6)

    # Panel (b): Transformed Contrast Indicator
    print("3. Rendering Panel (b): Transformed contrast indicator...")
    pc_b = build_poly_collection(nodes_c, elems_c, values=eta_trans, cmap_name="inferno", vmin=0.0, vmax=2.5, edge_lw=0.15, zero_color="#e6eff8")
    ax_b.add_collection(pc_b)
    add_holes(ax_b)
    ax_b.plot([0, 10], [70, 70], color="crimson", linewidth=1.8, zorder=6)
    ax_b.set_xlim(-2, 67)
    ax_b.set_ylim(-2, 122)
    ax_b.set_aspect("equal")
    ax_b.set_xlabel("x [mm]")
    ax_b.set_ylabel("y [mm]")
    ax_b.set_title("(b) Transformed Contrast Indicator $\\tilde{\\eta}_e$ (Candidate B)\n(79.1% Background Suppressed to Zero, Blue = Unrefined Coarse)")
    ax_b.grid(True, linestyle=":", alpha=0.5)
    cbar_b = fig.colorbar(matplotlib.cm.ScalarMappable(norm=plt.Normalize(vmin=0.0, vmax=2.5), cmap="inferno"), ax=ax_b, fraction=0.046, pad=0.04)
    cbar_b.set_label("Transformed Error $\\tilde{\\eta}_e = \\max(0, \\hat{\\eta} - \\tau)^{1.5} / S$")
    ax_b.text(36.5, 51.0, "Center\nHole", ha="center", va="center", fontsize=7.5, zorder=6)
    ax_b.text(32, 110, "Background: $\\tilde{\\eta}=0$\n(Preserves 1.5 mm mesh)", fontsize=7.5, color="#1f77b4", weight="bold",
              bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8))
    ax_b.text(12, 66, "Active Corridor\n$\\tilde{\\eta} > 0$", fontsize=7.5, color="crimson", weight="bold")

    # Panel (c): Statistical Distribution & Threshold Selection
    print("4. Rendering Panel (c): Statistical distribution...")
    raw_vals = np.array(list(eta_raw.values()))
    tau = params["tau"]
    gamma = params["gamma"]

    # Histogram in log-scale
    bins = np.logspace(np.log10(min(raw_vals)), np.log10(max(raw_vals)), 50)
    ax_c.hist(raw_vals, bins=bins, color="#4682b4", edgecolor="black", linewidth=0.5, alpha=0.7, label="Indicator Histogram ($N=3,923$)")
    
    # Statistical markers
    q25 = summary_data["global_envelope_baseline"]["q25"]
    med = summary_data["global_envelope_baseline"]["median"]
    q75 = summary_data["global_envelope_baseline"]["q75"]
    mean_val = summary_data["global_envelope_baseline"]["mean"]

    ax_c.axvline(med, color="purple", linestyle="--", linewidth=1.5, label="Median $\\tilde{\\mu} = %.4f$" % med)
    ax_c.axvline(q75, color="darkorange", linestyle="--", linewidth=1.5, label="Q75 = %.4f" % q75)
    ax_c.axvline(tau, color="crimson", linestyle="-", linewidth=2.0, label="Predeclared Threshold $\\tau = \\tilde{\\mu} + \\mathrm{IQR} = %.4f$" % tau)
    ax_c.axvline(mean_val, color="gray", linestyle=":", linewidth=1.2, label="Mean $\\bar{\\eta} = %.4f$" % mean_val)

    ax_c.set_xscale("log")
    ax_c.set_xlabel("Relative Error Indicator $\\hat{\\eta}_e^{(\\mathrm{env})}$ (Log Scale)")
    ax_c.set_ylabel("Element Count")
    ax_c.set_title("(c) Global Indicator Distribution & Predeclared Threshold\n($\\tau = \\mathrm{Median} + \\mathrm{IQR} = 0.0457$, 79.1% Elements Below $\\tau$)")
    ax_c.grid(True, which="both", linestyle=":", alpha=0.5)
    ax_c.legend(loc="upper left", fontsize=8.0, framealpha=0.9)
    ax_c.text(0.001, 150, "Suppressed Noise Zone\n$\\hat{\\eta} \\leq \\tau \\rightarrow \\tilde{\\eta} = 0$\n(3,101 elements)", fontsize=7.5, color="purple", weight="bold")
    ax_c.text(0.20, 80, "Active Fracture Zone\n$\\hat{\\eta} > \\tau \\rightarrow \\tilde{\\eta} > 0$\n(822 elements)", fontsize=7.5, color="crimson", weight="bold")

    # Panel (d): Along-Path Profile Comparison (Raw vs Transformed)
    print("5. Rendering Panel (d): Along-path profiles...")
    s_prim = [item[0] for item in prim_raw]
    v_prim_raw = [item[1] for item in prim_raw]
    v_prim_trans = [item[1] for item in prim_trans]

    # Secondary path (offset by L_prim + 5 mm for visualization in single sequence)
    offset_sec = 30.0
    s_sec = [item[0] + offset_sec for item in sec_raw]
    v_sec_raw = [item[1] for item in sec_raw]
    v_sec_trans = [item[1] for item in sec_trans]

    ax_d.plot(s_prim, v_prim_raw, "o--", color="#1f77b4", markersize=4, linewidth=1.2, alpha=0.6, label="Primary: Raw Envelope $\\hat{\\eta}_e$")
    ax_d.plot(s_prim, v_prim_trans, "o-", color="#1f77b4", markersize=4.5, linewidth=2.0, label="Primary: Transformed $\\tilde{\\eta}_e$")

    ax_d.plot(s_sec, v_sec_raw, "s--", color="#d62728", markersize=4, linewidth=1.2, alpha=0.6, label="Secondary: Raw Envelope $\\hat{\\eta}_e$")
    ax_d.plot(s_sec, v_sec_trans, "s-", color="#d62728", markersize=4.5, linewidth=2.0, label="Secondary: Transformed $\\tilde{\\eta}_e$")

    ax_d.axhline(tau, color="black", linestyle=":", linewidth=1.2, label="Threshold $\\tau = 0.0457$ (Median + IQR)")
    # Highlight primary midspan barrier below tau
    ax_d.axvspan(4.2, 8.8, color="gray", alpha=0.2, label="Primary Midspan Barrier ($s=4.3-8.7\\,\\mathrm{mm}$)")
    # Highlight secondary outer suppressed span
    ax_d.axvspan(30.0 + 13.2, 30.0 + 18.0, color="lightcoral", alpha=0.2, label="Secondary Outer Suppression ($s=13.2-18.0\\,\\mathrm{mm}$)")
    
    ax_d.set_xlabel("Along-Path Coordinate $s$ [mm] (Primary: $0 \\to 24.6\\,\\mathrm{mm}$ | Secondary: $30 \\to 48.5\\,\\mathrm{mm}$)")
    ax_d.set_ylabel("Indicator Magnitude (Log Scale)")
    ax_d.set_title("(d) Along-Path Evaluation & Field Limitations\n(Midspan Barrier & Secondary Outer Suppression Below $\\tau$)")
    ax_d.set_yscale("log")
    ax_d.set_ylim(0.0005, 20.0)
    ax_d.grid(True, which="both", linestyle=":", alpha=0.5)
    ax_d.legend(loc="upper right", fontsize=7.2, framealpha=0.9)

    out_png = os.path.join(FIG_DIR, "fig_f1747_contrast_prototype.png")
    out_pdf = os.path.join(FIG_DIR, "fig_f1747_contrast_prototype.pdf")

    print("6. Saving publication figures: %s ..." % out_png)
    plt.savefig(out_png, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()

    print("SUCCESS: Figures saved:")
    print("  PNG: %s" % out_png)
    print("  PDF: %s" % out_pdf)

if __name__ == '__main__':
    main()
