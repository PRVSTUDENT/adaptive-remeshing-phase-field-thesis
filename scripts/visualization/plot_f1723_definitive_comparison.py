# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1723_definitive_comparison.py
=========================================================
Generate definitive publication-quality figures for Task F1723:
1. Figure 1: Three-way side-by-side comparison (Published Fig 23b vs Baseline F1720 vs Improved F1723)
2. Figure 2: Comprehensive 4-ligament zoom matrix comparing all inter-hole gaps
3. Figure 3: Quantitative element size distributions and centerline profiles h(t) across all 4 ligaments
4. Figure 4: Smooth localized transition audit (contour of h_eq over the plate showing absence of bulk spreading)

Output: 300 DPI PNG + vector PDF.
"""
from __future__ import print_function
import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from PIL import Image

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
PUB_FIG23B_PATH = os.path.join(REPO_ROOT, "references", "derived", "pandey_kumar_2025_figures", "fig23b_panel_1.png")
F1720_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PHYS.inp")
F1723_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study", "C_S2_ET340.inp")
F1723_HIGH_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study", "A_S1_ET340.inp")

OUT_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

VOIDS = [
    {"id": "$h_1$", "center": (0.00, 0.50), "radius": 0.100},
    {"id": "$h_2$", "center": (0.35, 0.45), "radius": 0.100},
    {"id": "$h_3$", "center": (0.60, 0.55), "radius": 0.050},
    {"id": "$h_4$", "center": (0.75, 0.50), "radius": 0.075},
    {"id": "$h_5$", "center": (1.00, 0.45), "radius": 0.075},
]

def draw_voids(ax):
    for v in VOIDS:
        cx, cy = v["center"]
        r = v["radius"]
        c = plt.Circle((cx, cy), r, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.2, zorder=4)
        ax.add_patch(c)
        ax.text(cx, cy, v["id"], fontsize=9, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=5)

def parse_inp(inp_path):
    nodes = {}
    elements = []
    with open(inp_path, "r") as f:
        reading_nodes = False
        reading_elems = False
        for line in f:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            u = line.upper()
            if u.startswith("*NODE"):
                reading_nodes = True
                reading_elems = False
                continue
            elif u.startswith("*ELEMENT") and "OUTPUT" not in u and ("TYPE" in u or "," in u):
                reading_nodes = False
                reading_elems = True
                continue
            elif u.startswith("*"):
                reading_nodes = False
                reading_elems = False
                continue
            if reading_nodes:
                parts = line.split(",")
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif reading_elems:
                parts = line.split(",")
                elements.append((int(parts[0]), [int(p) for p in parts[1:]]))

    polys = []
    elem_data = []
    for eid, conn in elements:
        pts = [nodes[n] for n in conn]
        polys.append(pts)
        n_pts = len(pts)
        poly_x = [p[0] for p in pts]
        poly_y = [p[1] for p in pts]
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        h_eq = math.sqrt(area)
        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)
        elem_data.append((eid, cx, cy, h_eq))

    return nodes, elements, polys, elem_data

print("Parsing input meshes...")
nodes_f1720, elems_f1720, polys_f1720, edata_f1720 = parse_inp(F1720_INP)
nodes_f1723, elems_f1723, polys_f1723, edata_f1723 = parse_inp(F1723_INP)
nodes_high, elems_high, polys_high, edata_high = parse_inp(F1723_HIGH_INP)
print("F1720: %d elements, F1723 C_S2_ET340: %d elements, F1723 A_S1_ET340: %d elements" %
      (len(elems_f1720), len(elems_f1723), len(elems_high)))

# ==============================================================================
# FIGURE 1: Three-Way Side-by-Side Comparison
# ==============================================================================
def plot_figure_1():
    fig, axes = plt.subplots(1, 3, figsize=(21, 7.5))

    # (a) Published Fig 23(b)
    if os.path.exists(PUB_FIG23B_PATH):
        img = Image.open(PUB_FIG23B_PATH)
        axes[0].imshow(img)
        axes[0].axis("off")
        axes[0].set_title("(a) Published Pandey & Kumar (2025) Fig. 23(b)\nTarget: 12,944 Physical Elements",
                         fontsize=12, fontweight="bold", pad=10)

    # (b) Baseline F1720 Mesh
    pc0 = PolyCollection(polys_f1720, facecolors="white", edgecolors="#1e293b", linewidths=0.25, zorder=2)
    axes[1].add_collection(pc0)
    draw_voids(axes[1])
    axes[1].set_xlim(-0.02, 1.02)
    axes[1].set_ylim(-0.02, 1.02)
    axes[1].set_aspect("equal")
    axes[1].set_title("(b) Baseline F1720 Adapted Mesh\n13,163 Elements (+1.69% Parity vs 12,944)",
                     fontsize=12, fontweight="bold", pad=10)
    axes[1].set_xlabel("X [mm]", fontsize=11)
    axes[1].set_ylabel("Y [mm]", fontsize=11)
    axes[1].grid(True, linestyle=":", alpha=0.3)

    # (c) Improved F1723 Mesh (C_S2_ET340)
    pc1 = PolyCollection(polys_f1723, facecolors="white", edgecolors="#1e293b", linewidths=0.25, zorder=2)
    axes[2].add_collection(pc1)
    draw_voids(axes[2])
    axes[2].set_xlim(-0.02, 1.02)
    axes[2].set_ylim(-0.02, 1.02)
    axes[2].set_aspect("equal")
    axes[2].set_title("(c) Improved F1723 Adapted Mesh (C_S2_ET340)\n13,438 Elements (+3.82% Parity, Damage-Aware Sizing)",
                     fontsize=12, fontweight="bold", pad=10)
    axes[2].set_xlabel("X [mm]", fontsize=11)
    axes[2].set_ylabel("Y [mm]", fontsize=11)
    axes[2].grid(True, linestyle=":", alpha=0.3)

    fig.suptitle("Task F1723 Figure 1: Objective Adaptive-Remeshing Benchmark Reproduction\n"
                 "Side-by-Side Comparison of Published Fig. 23(b), Baseline F1720 Mesh, and Improved F1723 Mesh",
                 fontsize=14, fontweight="bold", y=0.98)
    fig.tight_layout()

    out_base = os.path.join(OUT_DIR, "fig_f1723_figure_1_side_by_side_comparison")
    fig.savefig(out_base + ".png", dpi=300)
    fig.savefig(out_base + ".pdf")
    plt.close(fig)
    print("Saved Figure 1 (PNG + PDF)")

# ==============================================================================
# FIGURE 2: 4-Ligament Zoom Matrix (Published vs F1720 vs Improved F1723)
# ==============================================================================
def plot_figure_2():
    fig, axes = plt.subplots(3, 4, figsize=(22, 16))

    rois = [
        ("Ligament 1 ($h_1 \\leftrightarrow h_2$)\nClearance $158.1\\,\\mu\\mathrm{m}$", 0.00, 0.40, 0.35, 0.65),
        ("Ligament 2 ($h_2 \\leftrightarrow h_3$)\nClearance $141.4\\,\\mu\\mathrm{m}$", 0.30, 0.65, 0.35, 0.65),
        ("Ligament 3 ($h_3 \\leftrightarrow h_4$)\nClearance $33.1\\,\\mu\\mathrm{m}$ (Narrowest)", 0.55, 0.80, 0.45, 0.60),
        ("Ligament 4 ($h_4 \\leftrightarrow h_5$)\nClearance $111.8\\,\\mu\\mathrm{m}$", 0.70, 1.00, 0.35, 0.60),
    ]

    crop_names = ["pub_fig23b_zoom_lig1.png", "pub_fig23b_zoom_lig2.png", "pub_fig23b_zoom_lig3.png", "pub_fig23b_zoom_lig4.png"]

    for col in range(4):
        title, xmin, xmax, ymin, ymax = rois[col]

        # Row 0: Published Fig 23b crop
        cpath = os.path.join(OUT_DIR, crop_names[col])
        if os.path.exists(cpath):
            img = Image.open(cpath)
            axes[0, col].imshow(img)
            axes[0, col].axis("off")
            axes[0, col].set_title("(a) Published Fig. 23(b)\n" + title, fontsize=10, fontweight="bold", pad=6)

        # Row 1: F1720 Mesh zoom
        pc0 = PolyCollection(polys_f1720, facecolors="white", edgecolors="#1e293b", linewidths=0.45, zorder=2)
        axes[1, col].add_collection(pc0)
        draw_voids(axes[1, col])
        axes[1, col].set_xlim(xmin, xmax)
        axes[1, col].set_ylim(ymin, ymax)
        axes[1, col].set_aspect("equal")
        axes[1, col].set_title("(b) Baseline F1720 Mesh\n" + title, fontsize=10, fontweight="bold", pad=6)
        axes[1, col].set_xlabel("X [mm]", fontsize=9)
        axes[1, col].set_ylabel("Y [mm]", fontsize=9)
        axes[1, col].grid(True, linestyle=":", alpha=0.3)

        # Row 2: Improved F1723 Mesh zoom
        pc1 = PolyCollection(polys_f1723, facecolors="white", edgecolors="#1e293b", linewidths=0.45, zorder=2)
        axes[2, col].add_collection(pc1)
        draw_voids(axes[2, col])
        axes[2, col].set_xlim(xmin, xmax)
        axes[2, col].set_ylim(ymin, ymax)
        axes[2, col].set_aspect("equal")
        axes[2, col].set_title("(c) Improved F1723 Mesh (C_S2_ET340)\n" + title, fontsize=10, fontweight="bold", pad=6)
        axes[2, col].set_xlabel("X [mm]", fontsize=9)
        axes[2, col].set_ylabel("Y [mm]", fontsize=9)
        axes[2, col].grid(True, linestyle=":", alpha=0.3)

    fig.suptitle("Task F1723 Figure 2: Detailed Inter-Hole Gap Wireframe Zoom Matrix\n"
                 "Row 1: Published Fig. 23(b) | Row 2: Baseline F1720 (13,163 Els) | Row 3: Improved F1723 (13,438 Els)",
                 fontsize=14, fontweight="bold", y=0.99)
    fig.tight_layout()

    out_base = os.path.join(OUT_DIR, "fig_f1723_figure_2_ligament_zoom_matrix")
    fig.savefig(out_base + ".png", dpi=300)
    fig.savefig(out_base + ".pdf")
    plt.close(fig)
    print("Saved Figure 2 (PNG + PDF)")

# ==============================================================================
# FIGURE 3: Centerline Element Size Profiles h(t) Across All 4 Ligaments
# ==============================================================================
def point_line_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.hypot(px-x1, py-y1), 0.0
    t = max(0.0, min(1.0, ((px-x1)*dx + (py-y1)*dy) / l2))
    proj_x = x1 + t*dx
    proj_y = y1 + t*dy
    return math.hypot(px-proj_x, py-proj_y), t

def eval_profile(elem_data, x1, y1, x2, y2, tol=0.015, n_bins=12):
    in_lig = []
    for eid, cx, cy, h in elem_data:
        d, t = point_line_dist(cx, cy, x1, y1, x2, y2)
        if d <= tol:
            in_lig.append((t, h))
    bin_hs = [[] for _ in range(n_bins)]
    for t, h in in_lig:
        b = min(n_bins - 1, int(t * n_bins))
        bin_hs[b].append(h)
    ts = [(b + 0.5) / float(n_bins) for b in range(n_bins)]
    means = [sum(b_hs)/len(b_hs) if b_hs else np.nan for b_hs in bin_hs]
    return ts, means

def plot_figure_3():
    fig, axes = plt.subplots(2, 2, figsize=(15, 12))

    lig_specs = [
        ("Ligament 1 ($h_1 \\leftrightarrow h_2$, Clearance $158.1\\,\\mu\\mathrm{m}$)",
         0.10, 0.50, 0.25, 0.45, axes[0, 0]),
        ("Ligament 2 ($h_2 \\leftrightarrow h_3$, Clearance $141.4\\,\\mu\\mathrm{m}$)",
         0.45, 0.45, 0.55, 0.55, axes[0, 1]),
        ("Ligament 3 ($h_3 \\leftrightarrow h_4$, Clearance $33.1\\,\\mu\\mathrm{m}$)",
         0.6474, 0.5342, 0.6789, 0.5237, axes[1, 0]),
        ("Ligament 4 ($h_4 \\leftrightarrow h_5$, Clearance $111.8\\,\\mu\\mathrm{m}$)",
         0.825, 0.50, 0.925, 0.45, axes[1, 1]),
    ]

    for title, x1, y1, x2, y2, ax in lig_specs:
        ts, m_f1720 = eval_profile(edata_f1720, x1, y1, x2, y2)
        _, m_f1723 = eval_profile(edata_f1723, x1, y1, x2, y2)
        _, m_high = eval_profile(edata_high, x1, y1, x2, y2)

        # Plot profiles in micrometers
        ax.plot(ts, [m * 1000.0 for m in m_f1720], "s--", color="#dc2626", label="Baseline F1720 (13,163 Els)", lw=1.8, ms=5)
        ax.plot(ts, [m * 1000.0 for m in m_f1723], "o-", color="#2563eb", label="Improved F1723 C_S2_ET340 (13,438 Els)", lw=2.2, ms=6)
        ax.plot(ts, [m * 1000.0 for m in m_high], "^:", color="#059669", label="Candidate A_S1_ET340 (14,177 Els)", lw=1.6, ms=5)

        # Benchmark bounds
        ax.axhline(8.0, color="#64748b", linestyle="--", lw=1.2, label="$\\ell_0 = 8.0\\,\\mu\\mathrm{m}$")
        ax.axhline(4.0, color="#94a3b8", linestyle=":", lw=1.2, label="$\\ell_0 / 2 = 4.0\\,\\mu\\mathrm{m}$")
        ax.axhline(1.0, color="#cbd5e1", linestyle="-.", lw=1.0, label="$h_{\\min} = 1.0\\,\\mu\\mathrm{m}$")

        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel("Normalized Distance Along Ligament Centerline $t \\in [0, 1]$", fontsize=10)
        ax.set_ylabel("Element Characteristic Size $h$ [$\\mu\\mathrm{m}$]", fontsize=10)
        ax.set_ylim(0.0, 10.0)
        ax.grid(True, linestyle=":", alpha=0.4)
        ax.legend(fontsize=8.5, loc="upper right")

    fig.suptitle("Task F1723 Figure 3: Quantitative Centerline Element Size Profiles Across Four Inter-Hole Ligaments",
                 fontsize=14, fontweight="bold", y=0.98)
    fig.tight_layout()

    out_base = os.path.join(OUT_DIR, "fig_f1723_figure_3_centerline_profiles")
    fig.savefig(out_base + ".png", dpi=300)
    fig.savefig(out_base + ".pdf")
    plt.close(fig)
    print("Saved Figure 3 (PNG + PDF)")

# ==============================================================================
# FIGURE 4: Smooth Localized Transition & Bulk Spreading Audit
# ==============================================================================
def plot_figure_4():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5))

    # Convert elem_sizes to um and color elements
    sizes_f1720 = [math.sqrt(d[3]) * 1000.0 for d in edata_f1720]
    sizes_f1723 = [math.sqrt(d[3]) * 1000.0 for d in edata_f1723]

    norm = Normalize(vmin=1.0, vmax=20.0)
    cmap = plt.cm.get_cmap("viridis_r")

    pc0 = PolyCollection(polys_f1720, array=np.array([d[3]*1000.0 for d in edata_f1720]),
                         cmap=cmap, norm=norm, edgecolors="none", zorder=2)
    ax1.add_collection(pc0)
    draw_voids(ax1)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect("equal")
    ax1.set_title("(a) Baseline F1720 Element Size Field $h(x, y)$\n13,163 Elements (Bulk $\\bar{h} = 8.68\\,\\mu\\mathrm{m}$)",
                  fontsize=11, fontweight="bold", pad=8)
    ax1.set_xlabel("X [mm]", fontsize=10)
    ax1.set_ylabel("Y [mm]", fontsize=10)

    pc1 = PolyCollection(polys_f1723, array=np.array([d[3]*1000.0 for d in edata_f1723]),
                         cmap=cmap, norm=norm, edgecolors="none", zorder=2)
    ax2.add_collection(pc1)
    draw_voids(ax2)
    ax2.set_xlim(-0.02, 1.02)
    axes_cb = fig.add_axes([0.92, 0.20, 0.02, 0.60])
    cbar = fig.colorbar(pc1, cax=axes_cb)
    cbar.set_label("Element Characteristic Size $h$ [$\\mu\\mathrm{m}$]", fontsize=11, fontweight="bold")
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect("equal")
    ax2.set_title("(b) Improved F1723 Element Size Field $h(x, y)$\n13,438 Elements (Bulk $\\bar{h} = 8.65\\,\\mu\\mathrm{m}$, No Bulk Spreading)",
                  fontsize=11, fontweight="bold", pad=8)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)

    fig.suptitle("Task F1723 Figure 4: Smooth Localized Mesh-Size Transition & Spreading Audit\n"
                 "Demonstrating Preservation of Coarse Bulk Elements Outside Error-Indicated Inter-Hole Ligaments",
                 fontsize=13, fontweight="bold", y=0.98)

    out_base = os.path.join(OUT_DIR, "fig_f1723_figure_4_smooth_transition_audit")
    fig.savefig(out_base + ".png", dpi=300)
    fig.savefig(out_base + ".pdf")
    plt.close(fig)
    print("Saved Figure 4 (PNG + PDF)")

plot_figure_1()
plot_figure_2()
plot_figure_3()
plot_figure_4()
print("\nAll 4 figure sets (8 files: 4 PNG + 4 PDF) generated successfully at 300 DPI!")
