# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1719_coarse_miseseri_and_mesh.py
============================================================
Task F1719 Phase 9:
High-Resolution Publication Figure Generation (Figures A through H)
at 300 DPI (both PNG and vector PDF).

Figure Sets:
  - Figure A: fig_f1719_figure_a_undamaged_vs_initiation_miseseri.pdf / .png
              (State 0 undamaged uy=0.0030mm vs State 1 damage initiation uy=0.0035mm)
  - Figure B: fig_f1719_figure_b_miseseri_multistate_evolution.pdf / .png
              (4-panel continuous evolution across States 0, 1, 2, 3 showing autonomous localization)
  - Figure C: fig_f1719_figure_c_published_fig25a_vs_coarse_companion.pdf / .png
              (Published Fig 25(a) with authentic legend vs authentic coarse recovery dummy/phys scales)
  - Figure D: fig_f1719_figure_d_coarse_vs_adapted_mesh.pdf / .png
              (Coarse 2,747-element initial mesh vs authentic F1719 adapted 11,871-element mesh)
  - Figure E: fig_f1719_figure_e_published_fig23b_vs_f1719_adapted.pdf / .png
              (Published Fig 23(b) mesh panel vs authentic F1719 adapted mesh)
  - Figure F: fig_f1719_figure_f_ligament_wireframe_zooms.pdf / .png
              (High-resolution zooms of critical process zones in Ligament h3-h4 and h4-h5)
  - Figure G: fig_f1719_figure_g_quantitative_indicators_and_sizes.pdf / .png
              (4-panel quantitative analysis: ligament error evolution, damage vs MISESERI correlation, element size distribution, parity summary)
  - Figure H: fig_f1719_figure_h_f1714_f1718_f1719_adaptive_mesh_comparison.pdf / .png
              (Methodological evolution: F1714 pure-elastic halos vs F1718 fine-mesh damage mapping vs F1719 autonomous coarse phase-field remeshing)
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
COARSE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.inp")
F1714_ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB2_ADAPTED_PHYS.inp")
F1718_ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "209_f1718_five_hole_recovery", "PK_F1718_JOB2_ADAPTED_PHYS.inp")
F1719_ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm", "PK_F1719_ADAPTED_STATE2.inp")
F1719_PARITY_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm", "PK_F1719_ADAPTED_STATE2_PARITY288.inp")
F1719_MULTI_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm", "PK_F1719_ADAPTED_MULTISTATE.inp")

RECOVERY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_recovered_miseseri_multistate.json")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_miseseri_evolution_audit.json")
METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1719_adapted_mesh_metrics.json")

PUB_FIG23B_PANEL1 = os.path.join(REPO_ROOT, "references", "derived", "pandey_kumar_2025_figures", "fig23b_panel_1.png")
PUB_FIG25A_WITH_LEGEND = os.path.join(REPO_ROOT, "references", "derived", "pandey_kumar_2025_figures", "p29_fig25a_with_legend.png")

OUT_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")
os.makedirs(OUT_DIR, exist_ok=True)

VOIDS = [
    {"id": "$h_1$", "center": (0.00, 0.50), "radius": 0.100, "type": "wedge", "theta": (-90, 90)},
    {"id": "$h_2$", "center": (0.35, 0.45), "radius": 0.100, "type": "circle"},
    {"id": "$h_3$", "center": (0.60, 0.55), "radius": 0.050, "type": "circle"},
    {"id": "$h_4$", "center": (0.75, 0.50), "radius": 0.075, "type": "circle"},
    {"id": "$h_5$", "center": (1.00, 0.45), "radius": 0.075, "type": "wedge", "theta": (90, 270)},
]


def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    in_nodes, in_elem = False, False
    with open(inp_path, "r", encoding="utf-8") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(k in u for k in ["PRINT", "FILE", "OUTPUT"]):
                in_nodes, in_elem = True, False
                continue
            elif u.startswith("*ELEMENT") and "OUTPUT" not in u:
                in_nodes, in_elem = False, True
                continue
            elif l.startswith("*"):
                in_nodes, in_elem = False, False
                continue
            if in_nodes:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elem:
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 4 and p[0].isdigit():
                    elements[int(p[0])] = [int(x) for x in p[1:] if x]
    return nodes, elements


def get_mesh_polys(nodes, elements):
    polys = []
    eids = []
    areas = []
    centroids = []
    for eid, conn in sorted(elements.items()):
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) >= 3:
            polys.append(pts)
            eids.append(eid)
            n_pts = len(pts)
            poly_x = [pt[0] for pt in pts]
            poly_y = [pt[1] for pt in pts]
            area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
            areas.append(area)
            centroids.append((sum(poly_x)/float(n_pts), sum(poly_y)/float(n_pts)))
    return polys, eids, areas, centroids


def draw_voids(ax, fill=True, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.2, zorder=5):
    for v in VOIDS:
        cx, cy = v["center"]
        r = v["radius"]
        if v["type"] == "circle":
            patch = patches.Circle((cx, cy), r, facecolor=facecolor if fill else "none",
                                   edgecolor=edgecolor, linewidth=lw, zorder=zorder)
            ax.add_patch(patch)
        elif v["type"] == "wedge":
            theta1, theta2 = v["theta"]
            patch = patches.Wedge((cx, cy), r, theta1, theta2, facecolor=facecolor if fill else "none",
                                  edgecolor=edgecolor, linewidth=lw, zorder=zorder)
            ax.add_patch(patch)


def save_fig(fig, base_name):
    png_path = os.path.join(OUT_DIR, f"{base_name}.png")
    pdf_path = os.path.join(OUT_DIR, f"{base_name}.pdf")
    fig.savefig(png_path, dpi=300, bbox_inches="tight")
    fig.savefig(pdf_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {png_path} ({os.path.getsize(png_path)} bytes)")
    print(f"Saved: {pdf_path} ({os.path.getsize(pdf_path)} bytes)")


# ==============================================================================
# FIGURE A: Undamaged Elastic (State 0) vs Damage Initiation (State 1)
# ==============================================================================
def plot_figure_a(rec_data, coarse_polys, coarse_eids):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5))
    cmap = matplotlib.colormaps["turbo"]

    s0_fields = rec_data["states"]["STATE0"]["scales"]["physical"]["element_fields"]
    s1_fields = rec_data["states"]["STATE1"]["scales"]["physical"]["element_fields"]

    vals0 = np.array([float(s0_fields.get(str(eid), {}).get("miseseri", 0.0)) for eid in coarse_eids])
    vals1 = np.array([float(s1_fields.get(str(eid), {}).get("miseseri", 0.0)) for eid in coarse_eids])

    norm1 = Normalize(vmin=0.0, vmax=250.0)

    # State 0
    pc1 = PolyCollection(coarse_polys, cmap=cmap, norm=norm1, edgecolors="none")
    pc1.set_array(vals0)
    ax1.add_collection(pc1)
    draw_voids(ax1, fill=True, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.2)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect("equal")
    ax1.set_title("(a) State 0: Undamaged Elastic ($u_y = 0.0030\\,\\mathrm{mm}$, $d_{\\max} = 0.0498$)\nCircumferential Concentrations Near Boundary Flanks (Max 204.6 MPa)",
                  fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("X [mm]", fontsize=10)
    ax1.set_ylabel("Y [mm]", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.4)
    cb1 = fig.colorbar(pc1, ax=ax1, fraction=0.046, pad=0.04)
    cb1.set_label("Recovered $\\mathrm{MISESERI}$ [MPa]", fontsize=10)

    # State 1
    pc2 = PolyCollection(coarse_polys, cmap=cmap, norm=norm1, edgecolors="none")
    pc2.set_array(vals1)
    ax2.add_collection(pc2)
    draw_voids(ax2, fill=True, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.2)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect("equal")
    ax2.set_title("(b) State 1: Damage Initiation ($u_y = 0.0035\\,\\mathrm{mm}$, $d_{\\max} = 0.0696$)\nPeak Shifts Into Narrowest Ligament $h_3 \\leftrightarrow h_4$ (Max 238.6 MPa)",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.4)
    cb2 = fig.colorbar(pc2, ax=ax2, fraction=0.046, pad=0.04)
    cb2.set_label("Recovered $\\mathrm{MISESERI}$ [MPa]", fontsize=10)

    for ax in [ax1, ax2]:
        for v in VOIDS:
            cx, cy = v["center"]
            ax.text(cx, cy, v["id"], fontsize=9, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure A: Autonomous Error Shift from Elastic Flank Concentration to Ligament Localization",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_a_undamaged_vs_initiation_miseseri")


# ==============================================================================
# FIGURE B: 4-Panel MISESERI Evolution Across Coarse Loading States
# ==============================================================================
def plot_figure_b(rec_data, coarse_polys, coarse_eids):
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    cmap = matplotlib.colormaps["turbo"]
    states_to_plot = [
        ("STATE0", axes[0, 0], "(a) State 0: Undamaged ($u_y = 0.0030\\,\\mathrm{mm}$)\n$d_{\\max} = 0.050$, $\\mathrm{MISESERI}_{\\max} = 204.6\\,\\mathrm{MPa}$"),
        ("STATE1", axes[0, 1], "(b) State 1: Initiation ($u_y = 0.0035\\,\\mathrm{mm}$)\n$d_{\\max} = 0.070$, $\\mathrm{MISESERI}_{\\max} = 238.6\\,\\mathrm{MPa}$"),
        ("STATE2", axes[1, 0], "(c) State 2: Early Localization ($u_y = 0.004965\\,\\mathrm{mm}$)\n$d_{\\max} = 0.160$, $\\mathrm{MISESERI}_{\\max} = 375.7\\,\\mathrm{MPa}$"),
        ("STATE3", axes[1, 1], "(d) State 3: Advanced Softening ($u_y = 0.0062\\,\\mathrm{mm}$)\n$d_{\\max} = 0.336$, $\\mathrm{MISESERI}_{\\max} = 457.2\\,\\mathrm{MPa}$")
    ]

    for skey, ax, title in states_to_plot:
        s_fields = rec_data["states"][skey]["scales"]["physical"]["element_fields"]
        vals = np.array([float(s_fields.get(str(eid), {}).get("miseseri", 0.0)) for eid in coarse_eids])
        norm = Normalize(vmin=0.0, vmax=float(np.max(vals)))

        pc = PolyCollection(coarse_polys, cmap=cmap, norm=norm, edgecolors="none")
        pc.set_array(vals)
        ax.add_collection(pc)
        draw_voids(ax, fill=True, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.2)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
        ax.set_xlabel("X [mm]", fontsize=9)
        ax.set_ylabel("Y [mm]", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.3)
        cb = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
        cb.set_label("$\\mathrm{MISESERI}$ [MPa]", fontsize=9)

        for v in VOIDS:
            cx, cy = v["center"]
            ax.text(cx, cy, v["id"], fontsize=8, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure B: Continuous Evolution of SPR Stress Jump Indicator Across Coarse Phase-Field Solve",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_b_miseseri_multistate_evolution")


# ==============================================================================
# FIGURE C: Published Fig 25(a) vs Authentic Coarse Companion Recovery
# ==============================================================================
def plot_figure_c(rec_data, coarse_polys, coarse_eids):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5))

    # Left: Published Fig 25(a)
    if os.path.exists(PUB_FIG25A_WITH_LEGEND):
        img_pub = Image.open(PUB_FIG25A_WITH_LEGEND)
        ax1.imshow(img_pub)
        ax1.axis("off")
        ax1.set_title("(a) Published Pandey & Kumar (2025) Fig. 25(a)\nAuthentic Legend: Max $2.20 \\times 10^{-12}$ to Min $6.08 \\times 10^{-19}$",
                      fontsize=11, fontweight="bold", pad=10)
    else:
        ax1.text(0.5, 0.5, "Published Fig 25(a) not found", ha="center", va="center")

    # Right: Authentic F1719 Coarse Companion Recovery (Dummy Modulus 10^-11 kN/mm^2)
    s2_dummy = rec_data["states"]["STATE2"]["scales"]["dummy"]["element_fields"]
    vals_dummy = np.array([float(s2_dummy.get(str(eid), {}).get("miseseri", 0.0)) for eid in coarse_eids])

    cmap = matplotlib.colormaps["turbo"]
    norm = Normalize(vmin=0.0, vmax=float(np.max(vals_dummy)))
    pc = PolyCollection(coarse_polys, cmap=cmap, norm=norm, edgecolors="none")
    pc.set_array(vals_dummy)
    ax2.add_collection(pc)
    draw_voids(ax2, fill=True, facecolor="#f8fafc", edgecolor="#0f172a", lw=1.2)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect("equal")
    ax2.set_title("(b) Authentic F1719 Coarse Companion Recovery ($E_{\\mathrm{dummy}} = 10^{-11}\\,\\mathrm{kN/mm}^2$)\nMax $1.789 \\times 10^{-11}$, Min $6.08 \\times 10^{-19}\\,\\mathrm{MPa}$ (Zero Fine-Mesh Leakage)",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.4)
    cb = fig.colorbar(pc, ax=ax2, fraction=0.046, pad=0.04)
    cb.set_label("Companion $\\mathrm{MISESERI}$ [MPa]", fontsize=10)

    for v in VOIDS:
        cx, cy = v["center"]
        ax2.text(cx, cy, v["id"], fontsize=9, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure C: Equivalence with Published Fig. 25(a) Inter-Hole Localization and Legend Scale",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_c_published_fig25a_vs_coarse_companion")


# ==============================================================================
# FIGURE D: Coarse Mesh vs New Adapted Mesh
# ==============================================================================
def plot_figure_d(nodes_coarse, elems_coarse, nodes_adapt, elems_adapt):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5))

    # Left: Coarse mesh
    polys_c, _, _, _ = get_mesh_polys(nodes_coarse, elems_coarse)
    pc1 = PolyCollection(polys_c, facecolors="white", edgecolors="#1e293b", linewidths=0.45, zorder=2)
    ax1.add_collection(pc1)
    draw_voids(ax1, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.2, zorder=3)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect("equal")
    ax1.set_title(f"(a) Initial Coarse Phase-Field Mesh\n{len(elems_coarse):,} Elements ($h = 0.020\\,\\mathrm{{mm}}$ Uniform Seed)",
                  fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("X [mm]", fontsize=10)
    ax1.set_ylabel("Y [mm]", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.3)

    # Right: Adapted mesh
    polys_a, _, _, _ = get_mesh_polys(nodes_adapt, elems_adapt)
    pc2 = PolyCollection(polys_a, facecolors="white", edgecolors="#1e293b", linewidths=0.35, zorder=2)
    ax2.add_collection(pc2)
    draw_voids(ax2, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.2, zorder=3)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect("equal")
    ax2.set_title(f"(b) F1719 Genuine Indicator-Driven Adapted Mesh\n{len(elems_adapt):,} Physical Elements ($\\mathrm{{errorTarget}} = 3.05\\%$, 100% Positive Jacobians)",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.3)

    for ax in [ax1, ax2]:
        for v in VOIDS:
            cx, cy = v["center"]
            ax.text(cx, cy, v["id"], fontsize=9, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure D: Pre-Analysis Coarse Mesh vs Predictive Adapted Discretization",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_d_coarse_vs_adapted_mesh")


# ==============================================================================
# FIGURE E: Published Figure 23(b) Mesh Panel vs F1719 Adapted Mesh
# ==============================================================================
def plot_figure_e(nodes_adapt, elems_adapt):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.5))

    # Left: Published Fig 23(b)
    if os.path.exists(PUB_FIG23B_PANEL1):
        img_pub = Image.open(PUB_FIG23B_PANEL1)
        ax1.imshow(img_pub)
        ax1.axis("off")
        ax1.set_title("(a) Published Pandey & Kumar (2025) Fig. 23(b)\nTarget Discretization: 12,944 Physical Elements",
                      fontsize=11, fontweight="bold", pad=10)
    else:
        ax1.text(0.5, 0.5, "Published Fig 23(b) not found", ha="center", va="center")

    # Right: F1719 Adapted Mesh
    polys_a, _, _, _ = get_mesh_polys(nodes_adapt, elems_adapt)
    pc = PolyCollection(polys_a, facecolors="white", edgecolors="#1e293b", linewidths=0.35, zorder=2)
    ax2.add_collection(pc)
    draw_voids(ax2, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.2, zorder=3)
    ax2.set_xlim(-0.02, 1.02)
    ax2.set_ylim(-0.02, 1.02)
    ax2.set_aspect("equal")
    ax2.set_title(f"(b) F1719 Coarse Phase-Field Adapted Mesh\n{len(elems_adapt):,} Physical Elements ($\\bar{{h}}_{{\\mathrm{{lig}}}} = 2.08\\,\\mu\\mathrm{{m}}$, Zero Priors)",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.3)

    for v in VOIDS:
        cx, cy = v["center"]
        ax2.text(cx, cy, v["id"], fontsize=9, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure E: Benchmark Verification — Published Fig. 23(b) vs F1719 Adapted Mesh",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_e_published_fig23b_vs_f1719_adapted")


# ==============================================================================
# FIGURE F: High-Resolution Zoom of Critical Inter-Hole Process Zones
# ==============================================================================
def plot_figure_f(nodes_adapt, elems_adapt):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7.0))
    polys_a, _, _, _ = get_mesh_polys(nodes_adapt, elems_adapt)

    # Left: Ligament h3 <-> h4 (Narrowest ligament: 33.1 um clearance)
    pc1 = PolyCollection(polys_a, facecolors="white", edgecolors="#1e293b", linewidths=0.45, zorder=2)
    ax1.add_collection(pc1)
    draw_voids(ax1, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.5, zorder=3)
    ax1.set_xlim(0.58, 0.78)
    ax1.set_ylim(0.46, 0.60)
    ax1.set_aspect("equal")
    ax1.set_title("Critical Ligament $h_3 \\leftrightarrow h_4$ (Clearance $33.1\\,\\mu\\mathrm{m} = 4.14\\,\\ell_0$)\n751 Elements in Corridor, $h_{\\min} = 0.85\\,\\mu\\mathrm{m} \\approx \\ell_0 / 10$",
                  fontsize=11, fontweight="bold", pad=10)
    ax1.set_xlabel("X [mm]", fontsize=10)
    ax1.set_ylabel("Y [mm]", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.4)
    ax1.annotate("$h_3$", xy=(0.60, 0.55), xytext=(0.585, 0.55), fontsize=11, fontweight="bold", color="#0f172a")
    ax1.annotate("$h_4$", xy=(0.75, 0.50), xytext=(0.74, 0.50), fontsize=11, fontweight="bold", color="#0f172a")

    # Right: Ligament h4 <-> h5 (Clearance 175 um)
    pc2 = PolyCollection(polys_a, facecolors="white", edgecolors="#1e293b", linewidths=0.45, zorder=2)
    ax2.add_collection(pc2)
    draw_voids(ax2, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.5, zorder=3)
    ax2.set_xlim(0.70, 0.98)
    ax2.set_ylim(0.38, 0.56)
    ax2.set_aspect("equal")
    ax2.set_title("Ligament $h_4 \\leftrightarrow h_5$ (Clearance $175\\,\\mu\\mathrm{m} = 21.9\\,\\ell_0$)\nSmooth Refinement Transition Across Secondary Fracture Corridor",
                  fontsize=11, fontweight="bold", pad=10)
    ax2.set_xlabel("X [mm]", fontsize=10)
    ax2.set_ylabel("Y [mm]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.4)
    ax2.annotate("$h_4$", xy=(0.75, 0.50), xytext=(0.735, 0.50), fontsize=11, fontweight="bold", color="#0f172a")
    ax2.annotate("$h_5$", xy=(1.00, 0.45), xytext=(0.95, 0.45), fontsize=11, fontweight="bold", color="#0f172a")

    fig.suptitle("Task F1719 Figure F: High-Resolution Process-Zone Refinement Across Inter-Hole Ligaments",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_f_ligament_wireframe_zooms")


# ==============================================================================
# FIGURE G: Quantitative MISESERI Localization, Damage Correlation, and Sizing
# ==============================================================================
def plot_figure_g(rec_data, audit_data, metrics_data, nodes_adapt, elems_adapt):
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))

    # 1. Ligament Error Evolution
    states = ["STATE0", "STATE1", "STATE2", "STATE3", "STATE4"]
    u_vals = [rec_data["states"][s]["uy_mm"] * 1000.0 for s in states] # um
    l3_errs = [audit_data["state_evolution"][s]["ligaments"]["L3_h3_to_h4_narrowest"]["miseseri_max"] for s in states]
    l2_errs = [audit_data["state_evolution"][s]["ligaments"]["L2_h1_to_h2"]["miseseri_max"] for s in states]
    l1_errs = [audit_data["state_evolution"][s]["ligaments"]["L1_left_to_h1"]["miseseri_max"] for s in states]
    l4_errs = [audit_data["state_evolution"][s]["ligaments"]["L4_h4_to_right"]["miseseri_max"] for s in states]

    ax1.plot(u_vals, l3_errs, "o-", color="#ef4444", lw=2, label="Ligament 3 ($h_3 \\leftrightarrow h_4$, 33.1 $\\mu$m)")
    ax1.plot(u_vals, l2_errs, "s--", color="#3b82f6", lw=1.5, label="Ligament 2 ($h_1 \\leftrightarrow h_2$)")
    ax1.plot(u_vals, l1_errs, "^:", color="#10b981", lw=1.5, label="Ligament 1 (Left flank)")
    ax1.plot(u_vals, l4_errs, "d:", color="#f59e0b", lw=1.5, label="Ligament 4 (Right flank)")
    ax1.set_title("(a) Regional Peak MISESERI Evolution Across Ligaments", fontsize=11, fontweight="bold")
    ax1.set_xlabel("Prescribed Displacement $u_y$ [$\\mu$m]", fontsize=10)
    ax1.set_ylabel("Peak $\\mathrm{MISESERI}$ [MPa]", fontsize=10)
    ax1.grid(True, linestyle=":", alpha=0.4)
    ax1.legend(loc="upper left", fontsize=9)

    # 2. Damage vs MISESERI Correlation in State 2
    s2_data = rec_data["states"]["STATE2"]
    s2_fields = s2_data["scales"]["physical"]["element_fields"]
    elem_dmg = s2_data["element_data"]
    eids = sorted([int(k) for k in s2_fields.keys()])
    dmgs = [elem_dmg[str(e)]["damage"] for e in eids]
    errs = [s2_fields[str(e)]["miseseri"] for e in eids]

    ax2.scatter(dmgs, errs, color="#3b82f6", alpha=0.5, s=15, edgecolors="none")
    # Linear fit
    p = np.polyfit(dmgs, errs, 1)
    d_fit = np.linspace(min(dmgs), max(dmgs), 100)
    ax2.plot(d_fit, np.polyval(p, d_fit), color="#ef4444", lw=2,
             label=f"Trend (Pearson r = {audit_data['state_evolution']['STATE2']['pearson_r_damage_vs_miseseri']:.3f})")
    ax2.set_title("(b) Element Damage vs Stress Jump Error (State 2, $u_y = 4.965\\,\\mu\\mathrm{m}$)", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Coarse Phase-Field Damage $d$", fontsize=10)
    ax2.set_ylabel("Recovered $\\mathrm{MISESERI}$ [MPa]", fontsize=10)
    ax2.grid(True, linestyle=":", alpha=0.4)
    ax2.legend(loc="upper left", fontsize=9)

    # 3. Element Size Distribution in Adapted Mesh
    _, _, _, _ = get_mesh_polys(nodes_adapt, elems_adapt)
    # Compute h for all adapted elements
    h_vals = []
    l0 = 0.008 # mm = 8 um
    for el in elems_adapt.values():
        pts = [nodes_adapt[n] for n in el if n in nodes_adapt]
        if len(pts) >= 3:
            px = [pt[0] for pt in pts]
            py = [pt[1] for pt in pts]
            np_ = len(pts)
            a = 0.5 * abs(sum([px[i]*py[(i+1)%np_] - py[i]*px[(i+1)%np_] for i in range(np_)]))
            h_vals.append(math.sqrt(a) * 1000.0) # um

    ax3.hist(h_vals, bins=45, color="#10b981", edgecolor="#047857", alpha=0.75)
    ax3.axvline(l0 * 1000.0, color="#ef4444", linestyle="--", lw=2, label="$\\ell_0 = 8\\,\\mu\\mathrm{m}$")
    ax3.axvline(l0 * 500.0, color="#f59e0b", linestyle=":", lw=2, label="$\\ell_0 / 2 = 4\\,\\mu\\mathrm{m}$")
    ax3.set_title("(c) Adapted Mesh Element Size Distribution ($h = \\sqrt{A}$)", fontsize=11, fontweight="bold")
    ax3.set_xlabel("Equivalent Element Size $h$ [$\\mu$m]", fontsize=10)
    ax3.set_ylabel("Element Count", fontsize=10)
    ax3.grid(True, linestyle=":", alpha=0.4)
    ax3.legend(loc="upper right", fontsize=9)

    # 4. Parity Summary Across Candidates
    cand_names = [
        "Primary (State 2)",
        "Parity (2.88%)",
        "Multi-State",
        "Adv. (State 3)",
        "Published (Target)"
    ]
    cand_counts = [
        metrics_data["candidates"]["primary_state2"]["num_elements"],
        metrics_data["candidates"]["parity_state2_288"]["num_elements"],
        metrics_data["candidates"]["multistate_state1_state3"]["num_elements"],
        metrics_data["candidates"]["advanced_state3"]["num_elements"],
        12944
    ]
    colors = ["#3b82f6", "#10b981", "#8b5cf6", "#f59e0b", "#ef4444"]

    bars = ax4.bar(cand_names, cand_counts, color=colors, edgecolor="#1e293b", alpha=0.85)
    ax4.axhline(12944, color="#ef4444", linestyle="--", lw=1.5, label="Target: 12,944")
    ax4.set_title("(d) Mesh Discretization Parity Comparison", fontsize=11, fontweight="bold")
    ax4.set_ylabel("Physical Element Count", fontsize=10)
    ax4.set_ylim(10000, 14000)
    ax4.grid(True, linestyle=":", alpha=0.4, axis="y")
    for bar in bars:
        h = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2.0, h + 80, f"{h:,}", ha="center", va="bottom", fontsize=8.5, fontweight="bold")
    ax4.tick_params(axis="x", rotation=15)

    fig.suptitle("Task F1719 Figure G: Quantitative Indicator Localization, Damage Correlation, and Mesh Parity",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_g_quantitative_indicators_and_sizes")


# ==============================================================================
# FIGURE H: Comparison of Previous F1714/F1718 Adaptive Meshes vs New Candidate
# ==============================================================================
def plot_figure_h(nodes_1714, elems_1714, nodes_1718, elems_1718, nodes_1719, elems_1719):
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 6.5))

    panels = [
        (ax1, nodes_1714, elems_1714,
         f"(a) F1714: Linear Elastic Pre-Analysis\n{len(elems_1714):,} Els (+0.70%)\nPure Stress Halos Around Voids",
         "#3b82f6"),
        (ax2, nodes_1718, elems_1718,
         f"(b) F1718: Mapped Forward Damage\n{len(elems_1718):,} Els (-8.38%)\nFine-Mesh Telemetry Data Leakage",
         "#f59e0b"),
        (ax3, nodes_1719, elems_1719,
         f"(c) F1719: Autonomous Coarse Phase-Field\n{len(elems_1719):,} Els (-8.29%)\nZero Priors, Autonomous Bridging",
         "#10b981")
    ]

    for ax, nodes, elems, title, badge_color in panels:
        polys, _, _, _ = get_mesh_polys(nodes, elems)
        pc = PolyCollection(polys, facecolors="white", edgecolors="#1e293b", linewidths=0.35, zorder=2)
        ax.add_collection(pc)
        draw_voids(ax, fill=True, facecolor="#cbd5e1", edgecolor="#0f172a", lw=1.2, zorder=3)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=10.5, fontweight="bold", pad=8)
        ax.set_xlabel("X [mm]", fontsize=9)
        ax.set_ylabel("Y [mm]", fontsize=9)
        ax.grid(True, linestyle=":", alpha=0.3)

        for v in VOIDS:
            cx, cy = v["center"]
            ax.text(cx, cy, v["id"], fontsize=8, fontweight="bold", ha="center", va="center", color="#0f172a", zorder=6)

    fig.suptitle("Task F1719 Figure H: Methodological Progression — From Circumferential Halos to Autonomous Adaptive Refinement",
                 fontsize=13, fontweight="bold", y=0.98)
    save_fig(fig, "fig_f1719_figure_h_f1714_f1718_f1719_adaptive_mesh_comparison")


def main():
    print("=" * 80)
    print("TASK F1719 PHASE 9: HIGH-RESOLUTION PUBLICATION FIGURE GENERATION")
    print("=" * 80)

    # 1. Load meshes
    print("Loading meshes...")
    nodes_coarse, elems_coarse = parse_inp_mesh(COARSE_INP)
    coarse_polys, coarse_eids, _, _ = get_mesh_polys(nodes_coarse, elems_coarse)

    nodes_1714, elems_1714 = parse_inp_mesh(F1714_ADAPTED_INP)
    nodes_1718, elems_1718 = parse_inp_mesh(F1718_ADAPTED_INP)
    nodes_1719, elems_1719 = parse_inp_mesh(F1719_ADAPTED_INP)
    print(f"Loaded: Coarse ({len(elems_coarse)} els), F1714 ({len(elems_1714)} els), F1718 ({len(elems_1718)} els), F1719 ({len(elems_1719)} els)")

    # 2. Load recovery and audit JSONs
    print("Loading data JSONs...")
    with open(RECOVERY_JSON, "r") as f:
        rec_data = json.load(f)
    with open(AUDIT_JSON, "r") as f:
        audit_data = json.load(f)
    with open(METRICS_JSON, "r") as f:
        metrics_data = json.load(f)

    # 3. Generate figures
    print("\nGenerating Figure A...")
    plot_figure_a(rec_data, coarse_polys, coarse_eids)

    print("\nGenerating Figure B...")
    plot_figure_b(rec_data, coarse_polys, coarse_eids)

    print("\nGenerating Figure C...")
    plot_figure_c(rec_data, coarse_polys, coarse_eids)

    print("\nGenerating Figure D...")
    plot_figure_d(nodes_coarse, elems_coarse, nodes_1719, elems_1719)

    print("\nGenerating Figure E...")
    plot_figure_e(nodes_1719, elems_1719)

    print("\nGenerating Figure F...")
    plot_figure_f(nodes_1719, elems_1719)

    print("\nGenerating Figure G...")
    plot_figure_g(rec_data, audit_data, metrics_data, nodes_1719, elems_1719)

    print("\nGenerating Figure H...")
    plot_figure_h(nodes_1714, elems_1714, nodes_1718, elems_1718, nodes_1719, elems_1719)

    print("\nSUCCESS: All 8 figure sets (16 files: 8 PNG + 8 PDF) successfully generated at 300 DPI!")


if __name__ == "__main__":
    main()
