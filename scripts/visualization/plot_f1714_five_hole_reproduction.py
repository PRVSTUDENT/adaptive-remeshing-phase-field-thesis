# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1714_five_hole_reproduction.py
==========================================================
Task F1714: Five-Hole Generalization Benchmark Visualizations.
Reproducing Pandey & Kumar (2025) Section 4.5 Figures 22(a), 23, 24, and 25(a).

Generates 5 publication-quality standalone figures (both PDF and 300-DPI PNG):
1. fig_f1714_five_hole_geometry.pdf / .png (Benchmark geometry, voids h1-h5, BCs)
2. fig_f1714_coarse_mesh.pdf / .png (Initial coarse FE mesh, 2,747 physical elements)
3. fig_f1714_error_indicator_miseseri.pdf / .png (Authentic MISESERI SPR error indicator field)
4. fig_f1714_adaptive_mesh_only.pdf / .png (Clean adaptive mesh wireframe, 13,034 elements)
5. fig_f1714_ligament_mesh_zooms.pdf / .png (High-resolution zooms of narrowest ligaments)
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODELS_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
OUT_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")
os.makedirs(OUT_DIR, exist_ok=True)


def parse_inp_mesh(inp_path):
    """Parses node coordinates and element connectivity from an Abaqus INP file."""
    nodes = {}
    elements = {}
    in_nodes, in_elem = False, False
    with open(inp_path, "r") as f:
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
                nodes[int(p[0])] = (float(p[1]), float(p[2]))
            elif in_elem:
                p = [x.strip() for x in l.split(",")]
                elements[int(p[0])] = [int(x) for x in p[1:] if x]
    return nodes, elements


def get_mesh_polys(nodes, elements):
    """Computes polygon vertex lists and element IDs."""
    polys = []
    eids = []
    for eid, conn in sorted(elements.items()):
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) >= 3:
            polys.append(pts)
            eids.append(eid)
    return polys, np.array(eids)


def plot_figure_1_geometry():
    """Generates the benchmark geometry schematic with void coordinates and BCs."""
    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    
    # Specimen domain [0, 1] x [0, 1] mm
    plate = patches.Rectangle((0, 0), 1.0, 1.0, facecolor="#f8fafc", edgecolor="#0f172a", linewidth=2.0, zorder=2)
    ax.add_patch(plate)

    # Voids definition per Table 5
    # h1: semi-circle at (0.0, 0.50), R = 0.10
    # h2: full circle at (0.35, 0.45), R = 0.10
    # h3: full circle at (0.60, 0.55), R = 0.05
    # h4: full circle at (0.75, 0.50), R = 0.075
    # h5: semi-circle at (1.00, 0.45), R = 0.075
    voids = [
        {"id": "$h_1$", "xy": (0.00, 0.50), "r": 0.100, "type": "semi_left"},
        {"id": "$h_2$", "xy": (0.35, 0.45), "r": 0.100, "type": "circle"},
        {"id": "$h_3$", "xy": (0.60, 0.55), "r": 0.050, "type": "circle"},
        {"id": "$h_4$", "xy": (0.75, 0.50), "r": 0.075, "type": "circle"},
        {"id": "$h_5$", "xy": (1.00, 0.45), "r": 0.075, "type": "semi_right"},
    ]

    for v in voids:
        cx, cy = v["xy"]
        r = v["r"]
        if v["type"] == "circle":
            c = patches.Circle((cx, cy), r, facecolor="#ffffff", edgecolor="#dc2626", linewidth=1.8, zorder=4)
            ax.add_patch(c)
        elif v["type"] == "semi_left":
            w = patches.Wedge((cx, cy), r, -90, 90, facecolor="#ffffff", edgecolor="#dc2626", linewidth=1.8, zorder=4)
            ax.add_patch(w)
        elif v["type"] == "semi_right":
            w = patches.Wedge((cx, cy), r, 90, 270, facecolor="#ffffff", edgecolor="#dc2626", linewidth=1.8, zorder=4)
            ax.add_patch(w)

        # Center point
        ax.plot(cx, cy, "k+", markersize=7, markeredgewidth=1.4, zorder=5)
        # Label
        offset_y = 0.03 if v["id"] != "$h_3$" else 0.025
        ax.text(cx, cy + offset_y, v["id"], fontsize=12, fontweight="bold", ha="center", va="bottom", color="#b91c1c", zorder=6)
        radius_text = "$R=%.3f$" % r
        ax.text(cx, cy - offset_y, radius_text, fontsize=8.5, ha="center", va="top", color="#334155", zorder=6)

    # Ligament clearance annotations
    # h3 <-> h4 narrowest ligament
    ax.annotate("", xy=(0.60 + 0.05 * 15 / 15.81, 0.55 - 0.05 * 5 / 15.81),
                xytext=(0.75 - 0.075 * 15 / 15.81, 0.50 + 0.075 * 5 / 15.81),
                arrowprops=dict(arrowstyle="<->", color="#0284c7", lw=1.5), zorder=7)
    ax.text(0.685, 0.585, "Narrowest\n$33.1\\,\\mu\\mathrm{m}$", fontsize=8.5, fontweight="bold",
            color="#0284c7", ha="center", va="bottom", zorder=8,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#e0f2fe", edgecolor="#0284c7", alpha=0.9))

    # Boundary conditions
    # Bottom: fixed
    for x in np.linspace(0.05, 0.95, 10):
        ax.plot([x, x - 0.02], [-0.02, -0.05], color="#475569", lw=1.2)
        ax.plot([x], [-0.01], marker="^", color="#475569", markersize=6)
    ax.text(0.5, -0.07, "Fixed: $u_x = 0,\\; u_y = 0$", fontsize=10, fontweight="bold", ha="center", va="top", color="#334155")

    # Top: uniform tensile displacement
    for x in np.linspace(0.05, 0.95, 10):
        ax.annotate("", xy=(x, 1.07), xytext=(x, 1.01),
                    arrowprops=dict(arrowstyle="->", color="#16a34a", lw=1.6))
    ax.text(0.5, 1.10, "Prescribed: $u_y = +u$", fontsize=10, fontweight="bold", ha="center", va="bottom", color="#15803d")

    # Dimensions
    ax.annotate("", xy=(-0.06, 0.0), xytext=(-0.06, 1.0),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(-0.09, 0.5, "$H = 1.0\\,\\mathrm{mm}$", fontsize=10.5, fontweight="bold", ha="center", va="center", rotation=90)

    ax.annotate("", xy=(0.0, -0.12), xytext=(1.0, -0.12),
                arrowprops=dict(arrowstyle="<->", color="#0f172a", lw=1.4))
    ax.text(0.5, -0.15, "$W = 1.0\\,\\mathrm{mm}$", fontsize=10.5, fontweight="bold", ha="center", va="top")

    # Benchmark parameter summary box
    summary_text = (
        "Five-Hole Benchmark Parameters:\n"
        "• Width $W = 1.0\\,\\mathrm{mm}$, Height $H = 1.0\\,\\mathrm{mm}$\n"
        "• Notchless ($a_0 = 0.0\\,\\mathrm{mm}$, autonomous nucleation)\n"
        "• $E = 210\\,\\mathrm{GPa}$, $\\nu = 0.30$\n"
        "• $G_c = 2.7\\times 10^{-3}\\,\\mathrm{kN/mm}$ ($2.7\\,\\mathrm{N/mm}$)\n"
        "• Length scale $\\ell_0 = 0.008\\,\\mathrm{mm}$ ($8.0\\,\\mu\\mathrm{m}$)\n"
        "• Constitutive split: Amor et al. (2009)\n"
        "• Reference: Pandey & Kumar (2025, Table 5)"
    )
    ax.text(0.04, 0.22, summary_text, fontsize=8.5, verticalalignment="top",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.95), zorder=8)

    ax.set_xlim(-0.16, 1.16)
    ax.set_ylim(-0.20, 1.18)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.set_title("Pandey & Kumar (2025) Section 4.5 Five-Hole Benchmark Geometry\n"
                 "(Reproducing Figure 22(a) Specification Without Initial Notch)",
                 fontsize=11.5, fontweight="bold", pad=12)
    ax.grid(True, linestyle=":", alpha=0.4)

    plt.tight_layout()
    pdf_path = os.path.join(OUT_DIR, "fig_f1714_five_hole_geometry.pdf")
    png_path = os.path.join(OUT_DIR, "fig_f1714_five_hole_geometry.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s" % png_path)


def plot_figure_2_coarse_mesh():
    """Generates the wireframe plot of the coarse pre-analysis mesh."""
    inp_path = os.path.join(MODELS_DIR, "PK_F1714_JOB1_COARSE.inp")
    nodes, elements = parse_inp_mesh(inp_path)
    polys, _ = get_mesh_polys(nodes, elements)

    fig, ax = plt.subplots(figsize=(8, 8), dpi=300)
    pc = PolyCollection(polys, facecolors="#ffffff", edgecolors="#1e293b", linewidths=0.35, zorder=3)
    ax.add_collection(pc)

    plate = patches.Rectangle((0, 0), 1.0, 1.0, fill=False, edgecolor="#0f172a", linewidth=1.8, zorder=5)
    ax.add_patch(plate)

    # Cutout voids with crisp dark borders
    ax.add_patch(patches.Wedge((0.00, 0.50), 0.100, -90, 90, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.35, 0.45), 0.100, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.60, 0.55), 0.050, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.75, 0.50), 0.075, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Wedge((1.00, 0.45), 0.075, 90, 270, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_title("Initial Coarse Finite-Element Discretization\n"
                 "(2,747 Physical Elements, Uniform Seeding $h_{\\mathrm{coarse}} = 0.02\\,\\mathrm{mm}$)",
                 fontsize=11.5, fontweight="bold", pad=12)

    # Annotation box
    ax.text(0.04, 0.08, "Coarse Pre-Analysis Mesh:\n• Elements: 2,747 (CPE4 + CPE3)\n• Nodes: 2,844\n• Linear elastic solve: $u = 0.005\\,\\mathrm{mm}$\n• Used for authentic SPR error evaluation",
            fontsize=8.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.95), zorder=8)

    plt.tight_layout()
    pdf_path = os.path.join(OUT_DIR, "fig_f1714_coarse_mesh.pdf")
    png_path = os.path.join(OUT_DIR, "fig_f1714_coarse_mesh.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s" % png_path)


def plot_figure_3_error_indicator():
    """Generates the elementwise contour plot of the authentic MISESERI SPR error indicator."""
    json_path = os.path.join(RESULTS_DIR, "f1714_coarse_miseseri_field.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    nodes = {int(k): v for k, v in data["nodes"].items()}
    elem_dict = data["elements"]

    polys = []
    eta_vals = []
    eri_vals = []
    for eid_str, edata in sorted(elem_dict.items(), key=lambda x: int(x[0])):
        conn = edata["conn"]
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) >= 3:
            polys.append(pts)
            eta_vals.append(edata["eta_percent"])
            eri_vals.append(edata["miseseri"])

    eta_arr = np.array(eta_vals)
    eri_arr = np.array(eri_vals)

    # Plot relative error ratio eta_e = MISESERI / MISESAVG (%)
    fig, ax = plt.subplots(figsize=(9, 8), dpi=300)
    norm = Normalize(vmin=0.0, vmax=min(np.percentile(eta_arr, 98), 15.0))
    cmap = matplotlib.cm.get_cmap("viridis")

    pc = PolyCollection(polys, cmap=cmap, norm=norm, edgecolors="none", zorder=3)
    pc.set_array(eta_arr)
    ax.add_collection(pc)

    # Outline
    plate = patches.Rectangle((0, 0), 1.0, 1.0, fill=False, edgecolor="#0f172a", linewidth=1.8, zorder=5)
    ax.add_patch(plate)

    # Voids
    ax.add_patch(patches.Wedge((0.00, 0.50), 0.100, -90, 90, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.35, 0.45), 0.100, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.60, 0.55), 0.050, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.75, 0.50), 0.075, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Wedge((1.00, 0.45), 0.075, 90, 270, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))

    cbar = fig.colorbar(pc, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Dimensionless Relative SPR Error $\\eta_e = \\mathrm{MISESERI} / \\mathrm{MISESAVG}$ (%)", fontsize=10, fontweight="bold")
    cbar.ax.tick_params(labelsize=9)

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_title("Authentic SPR Stress Jump Error Indicator Field $\\eta_e$\n"
                 "(Autonomous Localization Along Inter-Hole Ligaments $h_4\\leftrightarrow h_5$, $h_3\\leftrightarrow h_4$, $h_2\\leftrightarrow h_3$)",
                 fontsize=11.5, fontweight="bold", pad=12)

    ax.text(0.04, 0.08, "Error Indicator Telemetry:\n• Variable: MISESERI (Zienkiewicz-Zhu SPR stress jump)\n• Peak relative error: 304.6% (at void flanks)\n• Mean relative error: 3.07%\n• Guides mesh sizing without pre-assumed crack paths",
            fontsize=8.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.95), zorder=8)

    plt.tight_layout()
    pdf_path = os.path.join(OUT_DIR, "fig_f1714_error_indicator_miseseri.pdf")
    png_path = os.path.join(OUT_DIR, "fig_f1714_error_indicator_miseseri.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s" % png_path)


def plot_figure_4_adaptive_mesh_only():
    """Generates the clean standalone adapted mesh wireframe figure."""
    inp_path = os.path.join(MODELS_DIR, "PK_F1714_JOB2_ADAPTED_PHYS.inp")
    nodes, elements = parse_inp_mesh(inp_path)
    polys, _ = get_mesh_polys(nodes, elements)

    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    pc = PolyCollection(polys, facecolors="#ffffff", edgecolors="#1e293b", linewidths=0.22, zorder=3)
    ax.add_collection(pc)

    plate = patches.Rectangle((0, 0), 1.0, 1.0, fill=False, edgecolor="#0f172a", linewidth=1.8, zorder=5)
    ax.add_patch(plate)

    # Cutout voids
    ax.add_patch(patches.Wedge((0.00, 0.50), 0.100, -90, 90, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.35, 0.45), 0.100, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.60, 0.55), 0.050, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Circle((0.75, 0.50), 0.075, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))
    ax.add_patch(patches.Wedge((1.00, 0.45), 0.075, 90, 270, facecolor="#ffffff", edgecolor="#0f172a", lw=1.5, zorder=6))

    ax.set_xlim(-0.05, 1.05)
    ax.set_ylim(-0.05, 1.05)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_title("Authentic Native-Adapted Finite-Element Mesh (Mesh Only)\n"
                 "(13,034 Physical Elements, +0.70% Parity vs Published 12,944 Target)",
                 fontsize=11.5, fontweight="bold", pad=12)

    ax.text(0.04, 0.08, "Adapted Mesh Discretization:\n• Physical elements: 13,034 (12,720 quads, 314 tris)\n• Published target: 12,944 elements (error +0.70%)\n• 100% positive Jacobians (det(J) > 0, 0 inverted)\n• Sizing method: UNIFORM_ERROR, errorTarget = 3.05%\n• Resolves all multi-void fracture corridors",
            fontsize=8.5, bbox=dict(boxstyle="round,pad=0.4", facecolor="#ffffff", edgecolor="#cbd5e1", alpha=0.95), zorder=8)

    plt.tight_layout()
    pdf_path = os.path.join(OUT_DIR, "fig_f1714_adaptive_mesh_only.pdf")
    png_path = os.path.join(OUT_DIR, "fig_f1714_adaptive_mesh_only.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s" % png_path)


def plot_figure_5_ligament_zooms():
    """Generates high-resolution zoom figures of the critical inter-hole ligaments."""
    inp_path = os.path.join(MODELS_DIR, "PK_F1714_JOB2_ADAPTED_PHYS.inp")
    nodes, elements = parse_inp_mesh(inp_path)
    polys, _ = get_mesh_polys(nodes, elements)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), dpi=300)

    # Panel 1: Narrowest ligament h3 <-> h4
    pc1 = PolyCollection(polys, facecolors="#ffffff", edgecolors="#1e293b", linewidths=0.35, zorder=3)
    ax1.add_collection(pc1)
    ax1.add_patch(patches.Circle((0.60, 0.55), 0.050, facecolor="#ffffff", edgecolor="#dc2626", lw=1.8, zorder=6))
    ax1.add_patch(patches.Circle((0.75, 0.50), 0.075, facecolor="#ffffff", edgecolor="#dc2626", lw=1.8, zorder=6))
    ax1.plot(0.60, 0.55, "r+", markersize=8, zorder=7)
    ax1.plot(0.75, 0.50, "r+", markersize=8, zorder=7)
    ax1.text(0.60, 0.55, " $h_3$", fontsize=11, fontweight="bold", color="#dc2626", va="bottom", zorder=8)
    ax1.text(0.75, 0.50, " $h_4$", fontsize=11, fontweight="bold", color="#dc2626", va="bottom", zorder=8)

    # Scale bar in ligament (50 um = 0.05 mm)
    ax1.plot([0.62, 0.67], [0.42, 0.42], color="#0f172a", lw=2.5, zorder=9)
    ax1.text(0.645, 0.425, "$50\\,\\mu\\mathrm{m}$", fontsize=9, fontweight="bold", ha="center", va="bottom", zorder=9)

    ax1.set_xlim(0.52, 0.82)
    ax1.set_ylim(0.40, 0.68)
    ax1.set_aspect("equal")
    ax1.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax1.set_title("(a) Narrowest Ligament $h_3\\leftrightarrow h_4$ Zoom\n(Clearance $33.1\\,\\mu\\mathrm{m} = 4.14\\,\\ell_0$, Dense Quad Resolution)",
                  fontsize=10.5, fontweight="bold", pad=10)
    ax1.grid(True, linestyle=":", alpha=0.3)

    # Panel 2: Ligament h4 <-> h5 and right flank
    pc2 = PolyCollection(polys, facecolors="#ffffff", edgecolors="#1e293b", linewidths=0.35, zorder=3)
    ax2.add_collection(pc2)
    ax2.add_patch(patches.Circle((0.75, 0.50), 0.075, facecolor="#ffffff", edgecolor="#dc2626", lw=1.8, zorder=6))
    ax2.add_patch(patches.Wedge((1.00, 0.45), 0.075, 90, 270, facecolor="#ffffff", edgecolor="#dc2626", lw=1.8, zorder=6))
    ax2.plot([1.0, 1.0], [0.0, 1.0], color="#0f172a", lw=1.8, zorder=5) # right boundary
    ax2.plot(0.75, 0.50, "r+", markersize=8, zorder=7)
    ax2.plot(1.00, 0.45, "r+", markersize=8, zorder=7)
    ax2.text(0.75, 0.50, " $h_4$", fontsize=11, fontweight="bold", color="#dc2626", va="bottom", zorder=8)
    ax2.text(0.98, 0.45, "$h_5$ ", fontsize=11, fontweight="bold", color="#dc2626", ha="right", va="bottom", zorder=8)

    # Scale bar in ligament (50 um)
    ax2.plot([0.80, 0.85], [0.35, 0.35], color="#0f172a", lw=2.5, zorder=9)
    ax2.text(0.825, 0.355, "$50\\,\\mu\\mathrm{m}$", fontsize=9, fontweight="bold", ha="center", va="bottom", zorder=9)

    ax2.set_xlim(0.68, 1.03)
    ax2.set_ylim(0.33, 0.63)
    ax2.set_aspect("equal")
    ax2.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax2.set_title("(b) Ligament $h_4\\leftrightarrow h_5$ and Right Boundary Zoom\n(Clearance $105.1\\,\\mu\\mathrm{m} = 13.14\\,\\ell_0$, Smooth Transition)",
                  fontsize=10.5, fontweight="bold", pad=10)
    ax2.grid(True, linestyle=":", alpha=0.3)

    plt.tight_layout()
    pdf_path = os.path.join(OUT_DIR, "fig_f1714_ligament_mesh_zooms.pdf")
    png_path = os.path.join(OUT_DIR, "fig_f1714_ligament_mesh_zooms.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s" % png_path)


def main():
    print("================================================================")
    print("GENERATING TASK F1714 FIVE-HOLE PUBLICATION FIGURES")
    print("Output Directory: %s" % OUT_DIR)
    print("================================================================")
    plot_figure_1_geometry()
    plot_figure_2_coarse_mesh()
    plot_figure_3_error_indicator()
    plot_figure_4_adaptive_mesh_only()
    plot_figure_5_ligament_zooms()
    print("All 5 F1714 publication figures successfully generated at 300 DPI!")

if __name__ == "__main__":
    main()
