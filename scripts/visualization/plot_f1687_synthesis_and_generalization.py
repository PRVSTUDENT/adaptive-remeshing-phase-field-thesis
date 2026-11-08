"""
scripts/visualization/plot_f1687_synthesis_and_generalization.py
================================================================
Task F1687 Stage D: Publication synthesis and generalization figure.
- Panel (a): Mode-I Blind Generalization Adapted Mesh (11,578 physical elements)
  with color-coded h_equiv, crack trajectory overlay (y = 0.50 mm), and performance callouts.
- Panel (b): Transverse element size profile h_equiv(y) across the ligament (x = 0.75 mm)
  comparing Mode-I Blind Generalization, Hole E10, and ENDENERI Control.
- Panel (c): Quantitative performance summary table / radar comparing DOF count,
  W_90% transverse width, and relative waste area across all configurations.

Saves:
  MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_synthesis_and_generalization.pdf
  MA_AdaptiveRemeshing_Report_2026/figures/fig_f1687_synthesis_and_generalization.png
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize

def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 10,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 8.5,
        "figure.titlesize": 12,
        "text.usetex": False,
        "figure.dpi": 300
    })

def parse_mesh_for_plotting(inp_path):
    print("Reading mesh: %s" % inp_path)
    nodes = {}
    elements = []
    h_sizes = []

    in_nodes = False
    in_elements = False
    current_type = None

    with open(inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue

            if line.startswith("*"):
                in_nodes = False
                in_elements = False
                upline = line.upper()
                if upline.startswith("*NODE"):
                    in_nodes = True
                elif upline.startswith("*ELEMENT"):
                    if "CPE4" in upline or "CPS4" in upline or "CPE3" in upline or "CPS3" in upline:
                        in_elements = True
                        current_type = "ELEM"
                    else:
                        current_type = None
                continue

            parts = [p.strip() for p in line.split(",") if p.strip()]
            if in_nodes:
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif in_elements and current_type:
                try:
                    conn = [int(p) for p in parts[1:]]
                    elements.append(conn)
                except ValueError:
                    pass

    verts = []
    centroids = []
    for conn in elements:
        pts = [nodes[nid] for nid in conn]
        n_pts = len(pts)
        area = 0.0
        for i in range(n_pts):
            j = (i + 1) % n_pts
            area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
        area = 0.5 * abs(area)
        h_eq = math.sqrt(area) * 1000.0 # um
        h_sizes.append(h_eq)
        verts.append(pts)
        cx = sum([p[0] for p in pts]) / float(n_pts)
        cy = sum([p[1] for p in pts]) / float(n_pts)
        centroids.append((cx, cy))

    return verts, np.array(h_sizes), np.array(centroids)

def main():
    setup_style()
    inp_mode1 = os.path.abspath("models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_BLIND_DIFF_PHYS.inp")
    inp_e10 = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E10_PHYS.inp")
    inp_end = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_ENDENERI_TERM_PHYS.inp")

    # Load audits
    with open("results/validation/f1687_mode1_blind_audit.json", "r") as fp:
        mode1_audit = json.load(fp)
    with open("results/validation/f1687_endeneri_candidate_audit.json", "r") as fp:
        end_audit = json.load(fp)

    fig = plt.figure(figsize=(16, 5.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[1.1, 1.0, 1.0], wspace=0.30)

    # --------------------------------------------------------------------------
    # Panel (a): Mode-I Blind Generalization Mesh Map
    # --------------------------------------------------------------------------
    ax0 = fig.add_subplot(gs[0, 0])
    verts_m1, h_m1, cent_m1 = parse_mesh_for_plotting(inp_mode1)
    norm = Normalize(vmin=1.5, vmax=15.0)
    cmap = plt.cm.viridis_r

    pc = PolyCollection(verts_m1, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
    pc.set_array(h_m1)
    ax0.add_collection(pc)

    # Crack path overlay
    ax0.plot([0.50, 1.00], [0.50, 0.50], color="crimson", linewidth=2.0, linestyle="--", label="Crack Path ($y=0.50$ mm)")
    ax0.scatter([0.50], [0.50], color="crimson", s=40, zorder=5, label="Notch Tip (0.50, 0.50)")

    ax0.set_xlim(0.35, 1.02)
    ax0.set_ylim(0.20, 0.80)
    ax0.set_aspect("equal")
    ax0.set_xlabel("x [mm]")
    ax0.set_ylabel("y [mm]")
    ax0.set_title("(a) Mode-I Blind Generalization Mesh\n(Locked Differential Rule: 5% Early, 10% Terminal)", fontweight="bold")
    ax0.legend(loc="upper left", framealpha=0.9, fontsize=8)

    stat_txt = (
        "Elements: 11,578 | DOFs: 34,737\n"
        "Corridor $h_{\\mathrm{med}} = 2.25\\,\\mu$m ($\\leq \\ell_0/3$)\n"
        "% $\\leq \\ell_0/2$: 79.77% (near 80%)\n"
        "$W_{50\\%}: 15.34\\,\\mu$m (narrow core)\n"
        "$W_{90\\%}: 229.56\\,\\mu$m | Waste: 75.65%\n"
        "H2 Verdict: FALSIFIED (Untuned)"
    )
    ax0.text(0.37, 0.22, stat_txt, fontsize=8.0,
             bbox=dict(boxstyle="round,pad=0.35", facecolor="white", alpha=0.92, edgecolor="crimson"))

    # --------------------------------------------------------------------------
    # Panel (b): Transverse Resolution Profiles h_equiv(y) at x = 0.75 mm
    # --------------------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, 1])
    # Extract transverse slice at x = 0.75 mm (+/- 0.02 mm)
    x_target = 0.75
    dx = 0.025

    # Mode-I
    mask_m1 = (cent_m1[:, 0] >= x_target - dx) & (cent_m1[:, 0] <= x_target + dx)
    y_m1 = cent_m1[mask_m1, 1]
    h_m1_slice = h_m1[mask_m1]
    idx_sort_m1 = np.argsort(y_m1)
    ax1.plot(y_m1[idx_sort_m1], h_m1_slice[idx_sort_m1], "o-", color="#1f77b4", markersize=3.5, linewidth=1.2,
             label="Mode-I Blind ($x = 0.75$ mm)")

    # E10 Hole Candidate
    _, h_e10, cent_e10 = parse_mesh_for_plotting(inp_e10)
    # Secondary ligament at x = 0.85 mm
    x_sec = 0.85
    mask_e10 = (cent_e10[:, 0] >= x_sec - dx) & (cent_e10[:, 0] <= x_sec + dx)
    y_e10 = cent_e10[mask_e10, 1]
    h_e10_slice = h_e10[mask_e10]
    idx_sort_e10 = np.argsort(y_e10)
    ax1.plot(y_e10[idx_sort_e10], h_e10_slice[idx_sort_e10], "s-", color="#2ca02c", markersize=3.5, linewidth=1.2,
             label="Hole E10 Secondary ($x = 0.85$ mm)")

    # ENDENERI Control
    _, h_end, cent_end = parse_mesh_for_plotting(inp_end)
    mask_end = (cent_end[:, 0] >= x_sec - dx) & (cent_end[:, 0] <= x_sec + dx)
    y_end = cent_end[mask_end, 1]
    h_end_slice = h_end[mask_end]
    idx_sort_end = np.argsort(y_end)
    ax1.plot(y_end[idx_sort_end], h_end_slice[idx_sort_end], "^-", color="#d62728", markersize=3.0, linewidth=1.0, alpha=0.7,
             label="Hole ENDENERI ($x = 0.85$ mm)")

    ax1.axhline(3.75, color="black", linestyle="--", linewidth=1.0, label=r"$\ell_0/2 = 3.75\,\mu$m")
    ax1.axhline(2.50, color="gray", linestyle=":", linewidth=1.0, label=r"$\ell_0/3 = 2.50\,\mu$m")
    ax1.set_xlabel("Transverse Coordinate $y$ [mm]")
    ax1.set_ylabel(r"Element Size $h_{\mathrm{equiv}} = \sqrt{\mathrm{Area}}$ [$\mu$m]")
    ax1.set_title(r"(b) Transverse Discretization Profile $h_{\mathrm{equiv}}(y)$", fontweight="bold")
    ax1.set_ylim(0.0, 18.0)
    ax1.grid(True, linestyle="--", alpha=0.4)
    ax1.legend(loc="upper right", framealpha=0.9, fontsize=8)

    # --------------------------------------------------------------------------
    # Panel (c): Comparative Synthesis Bar Chart
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 2])
    models = ["Hole E05\n(Single 5%)", "Hole E10\n(Diff 5/10%)", "Hole ENDEN\n(Single 5%)", "Mode-I Blind\n(Diff 5/10%)"]
    w90_vals = [197.10, 36.81, 191.72, 229.56]
    waste_vals = [86.52, 65.35, 92.93, 75.65]

    x_pos = np.arange(len(models))
    w_bar = 0.35

    rects1 = ax2.bar(x_pos - w_bar/2, w90_vals, w_bar, label=r"$W_{90\%}$ Width [$\mu$m]", color="#1f77b4", alpha=0.85)
    rects2 = ax2.bar(x_pos + w_bar/2, waste_vals, w_bar, label="Relative Waste Area [%]", color="#ff7f0e", alpha=0.85)

    ax2.axhline(50.0, color="#1f77b4", linestyle="--", linewidth=1.0, label="Max $W_{90\%}$ (50 $\mu$m)")
    ax2.axhline(70.0, color="#ff7f0e", linestyle=":", linewidth=1.0, label="Max Waste (70%)")

    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(models, fontsize=8.5)
    ax2.set_ylabel("Metric Value [$\mu$m or %]")
    ax2.set_title("(c) Selectivity & Waste Synthesis\nAcross Benchmarks and Rules", fontweight="bold")
    ax2.set_ylim(0, 260)
    ax2.grid(True, linestyle="--", alpha=0.3, axis="y")
    ax2.legend(loc="upper left", framealpha=0.9, fontsize=8)

    for r in rects1:
        h = r.get_height()
        ax2.annotate(f"{h:.1f}", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2),
                     textcoords="offset points", ha="center", va="bottom", fontsize=7.5)
    for r in rects2:
        h = r.get_height()
        ax2.annotate(f"{h:.1f}%", xy=(r.get_x() + r.get_width()/2, h), xytext=(0, 2),
                     textcoords="offset points", ha="center", va="bottom", fontsize=7.5)

    fig.suptitle(r"Task F1687: Synthesis of Method A Multi-Step Remeshing Selectivity, History Controls, and Generalization", fontsize=12, y=0.99)

    dest_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)
        pdf_path = os.path.join(d, "fig_f1687_synthesis_and_generalization.pdf")
        png_path = os.path.join(d, "fig_f1687_synthesis_and_generalization.png")
        fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
        print("Saved %s and %s" % (pdf_path, png_path))

    plt.close(fig)

if __name__ == "__main__":
    main()
