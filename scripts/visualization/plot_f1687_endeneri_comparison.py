"""
scripts/visualization/plot_f1687_endeneri_comparison.py
=======================================================
Task F1687 Stage B: Generates three-panel comparison figure:
- Panel (a): Single-target Baseline E05 (21,569 elements, W90 = 197.10 um, Waste 86.52%)
- Panel (b): Primary Recommended Candidate E10 (9,164 elements, W90 = 36.81 um, Waste 65.35%)
- Panel (c): Terminal Frame ENDENERI Control (51,712 elements, W90 = 191.72 um, Waste 92.93%, H1 Falsified)
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
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 12,
        "text.usetex": False,
        "figure.dpi": 300
    })

def parse_mesh_for_plotting(inp_path):
    print(f"Reading mesh: {inp_path}")
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

    return verts, np.array(h_sizes)

def main():
    setup_style()
    cand_dir = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates"
    inp_e05 = os.path.join(cand_dir, "PK_HOLE_SEL_E05_PHYS.inp")
    inp_e10 = os.path.join(cand_dir, "PK_HOLE_SEL_E10_PHYS.inp")
    inp_end = os.path.join(cand_dir, "PK_HOLE_ENDENERI_TERM_PHYS.inp")

    cl_path = "results/validation/f1684_crack_path_centerlines.json"
    with open(cl_path, "r") as fp:
        cl_data = json.load(fp)
    prim_cl = np.array(cl_data["primary"]["points"])
    sec_cl = np.array(cl_data["secondary"]["points"])

    meshes = [
        ("Baseline E05 (Single 5% MISESERI)", inp_e05, "21,569 elements, W90 = 197.10 um\nWaste Area = 0.0601 mm2 (86.52%)\nCriterion 4: FAIL"),
        ("Candidate E10 (Differential 5%/10%)", inp_e10, "9,164 elements (57.5% drop), W90 = 36.81 um\nWaste Area = 0.0128 mm2 (65.35%)\nOverall Pass: TRUE (Primary Recommended)"),
        ("Terminal ENDENERI Control (5% Rule)", inp_end, "51,712 elements (2.4x baseline), W90 = 191.72 um\nWaste Area = 0.1672 mm2 (92.93%)\nOverall Pass: FALSE (H1 FALSIFIED)")
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.8), sharex=True, sharey=True)
    norm = Normalize(vmin=1.5, vmax=15.0) # um color scale
    cmap = plt.cm.viridis_r

    for ax, (title, inp_path, stat_txt) in zip(axes, meshes):
        verts, h_sizes = parse_mesh_for_plotting(inp_path)
        pc = PolyCollection(verts, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
        pc.set_array(h_sizes)
        ax.add_collection(pc)

        # Overlay authentic crack paths
        ax.plot(prim_cl[:, 0], prim_cl[:, 1], color="crimson", linewidth=1.8, label="Primary Crack Path")
        ax.plot(sec_cl[:, 0], sec_cl[:, 1], color="darkorange", linewidth=1.8, label="Secondary Crack Path")

        ax.set_xlim(0.35, 1.02)
        ax.set_ylim(0.40, 0.85)
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]")
        ax.set_title(title, fontweight="bold", pad=8)

        # Annotation box
        ax.text(0.37, 0.42, stat_txt, fontsize=8.5,
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", alpha=0.9, edgecolor="gray"))

    axes[0].set_ylabel("y [mm]")
    axes[0].legend(loc="upper left", framealpha=0.9, fontsize=8)

    cbar_ax = fig.add_axes([0.92, 0.18, 0.015, 0.64])
    cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax)
    cbar.set_label(r"Equivalent Element Size $h_{\mathrm{equiv}} = \sqrt{\mathrm{Area}}$ [$\mu$m]", fontsize=10)

    fig.suptitle(r"Task F1687: Native Abaqus Remeshing Selectivity Comparison — Baseline E05 vs. E10 vs. ENDENERI Control", fontsize=12, y=0.98)

    dest_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)
        pdf_path = os.path.join(d, "fig_f1687_endeneri_comparison.pdf")
        png_path = os.path.join(d, "fig_f1687_endeneri_comparison.png")
        fig.savefig(pdf_path, bbox_inches="tight", dpi=300)
        fig.savefig(png_path, bbox_inches="tight", dpi=300)
        print(f"Saved {pdf_path} and {png_path}")

    plt.close(fig)

if __name__ == "__main__":
    main()
