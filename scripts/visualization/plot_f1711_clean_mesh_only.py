# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1711_clean_mesh_only.py
===================================================
Task F1711: Clean Standalone Mesh-Only Adaptive Remesh Visualizations.
Renders publication-quality wireframe images of the authentic 10,065-element
adapted finite-element mesh from Pandey & Kumar (2025) Section 4.3.

Strictly mesh-only:
  - Clean white background
  - Thin dark element edges showing fine refinement corridors
  - White cutout holes with solid dark borders
  - Black initial notch (10.0 x 0.4 mm at y = 70.0 mm)
  - NO phase-field damage contours, NO rainbow/jet colormaps
  - NO crack-path overlay lines or artificial trajectories

Deliverables:
  - fig_f1711_adaptive_remesh_only.pdf / .png (Full 65x120 mm specimen)
  - fig_f1711_primary_mesh_zoom_only.pdf / .png (Primary notch-to-hole corridor zoom)
  - fig_f1711_secondary_mesh_zoom_only.pdf / .png (Secondary void-to-boundary corridor zoom)
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.collections import PolyCollection

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures", "pandey_kumar_fig14_16_reproduction")
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

def plot_full_mesh_only(polys, out_pdf, out_png):
    """Renders the entire 65x120 mm specimen displaying only the adapted mesh wireframe."""
    fig = plt.figure(figsize=(9, 13), dpi=300)
    ax = fig.add_axes([0.10, 0.08, 0.82, 0.86])

    ax.set_title("Authentic Adapted Finite-Element Discretization\n"
                 "(10,065 Physical Elements, Pandey & Kumar 2025 Section 4.3 Adapted Specimen)",
                 fontsize=12, fontweight="bold", pad=12)

    ax.set_xlim(-3, 68)
    ax.set_ylim(-5, 125)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.tick_params(labelsize=9.5)

    # Pure white face with thin dark element edges
    pc = PolyCollection(polys, facecolors="#ffffff", edgecolors="#1e293b", linewidths=0.25, zorder=3)
    ax.add_collection(pc)

    # Specimen outer boundary
    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.6, zorder=5)
    ax.add_patch(plate)

    # Cutout holes with crisp dark boundary
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="#ffffff", edgecolor="#0f172a", linewidth=1.5, zorder=6)
    ax.add_patch(hole_c)
    hole_l = Circle((20.0, 20.0), 5.0, facecolor="#ffffff", edgecolor="#0f172a", linewidth=1.4, zorder=6)
    ax.add_patch(hole_l)
    hole_u = Circle((20.0, 100.0), 5.0, facecolor="#ffffff", edgecolor="#0f172a", linewidth=1.4, zorder=6)
    ax.add_patch(hole_u)

    # Initial horizontal notch: 10.0 x 0.4 mm at y = 70.0 mm
    notch = Rectangle((0, 69.8), 10.0, 0.4, facecolor="#0f172a", edgecolor="#0f172a", zorder=7)
    ax.add_patch(notch)

    # Sub-labels for geometry callouts
    ax.text(20.0, 20.0, "Pin Hole\n$R=5$", ha="center", va="center", fontsize=8, fontweight="bold", color="#475569", zorder=8)
    ax.text(20.0, 100.0, "Pin Hole\n$R=5$", ha="center", va="center", fontsize=8, fontweight="bold", color="#475569", zorder=8)
    ax.text(36.5, 51.0, "Circular Void\n$R=10$", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#475569", zorder=8)

    ax.grid(True, linestyle=":", alpha=0.30, color="#94a3b8", zorder=1)

    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1711] Saved full specimen mesh-only figure: %s and %s" % (out_pdf, out_png))

def plot_primary_zoom_mesh_only(polys, out_pdf, out_png):
    """Renders zoomed view of the primary fracture corridor (Notch -> Curved Deflection -> Hole), mesh only."""
    fig = plt.figure(figsize=(11, 9), dpi=300)
    ax = fig.add_axes([0.10, 0.10, 0.82, 0.82])

    ax.set_title("Primary Fracture-Process Zone: Adapted Mesh Wireframe\n"
                 "(Zoom: $x \\in [0, 42]$ mm, $y \\in [44, 76]$ mm; Refinement $h \\leq \\ell_0/2 = 0.143$ mm)",
                 fontsize=11.5, fontweight="bold", pad=12)

    ax.set_xlim(-1, 42)
    ax.set_ylim(44, 76)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.tick_params(labelsize=9.5)

    # Clean white face with prominent element boundaries
    pc = PolyCollection(polys, facecolors="#ffffff", edgecolors="#0f172a", linewidths=0.40, zorder=3)
    ax.add_collection(pc)

    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.6, zorder=5)
    ax.add_patch(plate)
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="#ffffff", edgecolor="#0f172a", linewidth=1.5, zorder=6)
    ax.add_patch(hole_c)
    notch = Rectangle((0, 69.8), 10.0, 0.4, facecolor="#0f172a", edgecolor="#0f172a", zorder=7)
    ax.add_patch(notch)

    ax.text(36.5, 51.0, "Circular Void\n$R=10$", ha="center", va="center", fontsize=9, fontweight="bold", color="#475569", zorder=8)
    ax.annotate("Initial Notch Root\n$(10.0, 70.0)$ mm", xy=(10.0, 70.0), xytext=(2, 60),
                arrowprops=dict(facecolor="#0f172a", shrink=0.06, width=1.0, headwidth=5),
                fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#94a3b8"))

    ax.annotate("Primary Refinement Corridor\n($h_{\\min} = 0.100$ mm $\\leq \\ell_0/2$)", xy=(25.0, 67.5), xytext=(12, 50),
                arrowprops=dict(facecolor="#0f172a", shrink=0.06, width=1.0, headwidth=5),
                fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#94a3b8"))

    ax.grid(True, linestyle=":", alpha=0.35, color="#94a3b8", zorder=1)

    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1711] Saved primary mesh zoom figure: %s and %s" % (out_pdf, out_png))

def plot_secondary_zoom_mesh_only(polys, out_pdf, out_png):
    """Renders zoomed view of the secondary fracture corridor (Void Flank -> Ligament -> Free Edge), mesh only."""
    fig = plt.figure(figsize=(12, 11), dpi=300)
    ax = fig.add_axes([0.10, 0.10, 0.82, 0.82])

    ax.set_title("Secondary Fracture-Process Zone: Adapted Mesh Wireframe\n"
                 "(Zoom: $x \\in [33, 66]$ mm, $y \\in [43, 59]$ mm; Refinement $h \\leq \\ell_0/5 = 0.051$ mm)",
                 fontsize=11.5, fontweight="bold", pad=12)

    ax.set_xlim(33, 66)
    ax.set_ylim(43, 59)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10.5, fontweight="bold")
    ax.tick_params(labelsize=9.5)

    pc = PolyCollection(polys, facecolors="#ffffff", edgecolors="#0f172a", linewidths=0.40, zorder=3)
    ax.add_collection(pc)

    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.6, zorder=5)
    ax.add_patch(plate)
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="#ffffff", edgecolor="#0f172a", linewidth=1.5, zorder=6)
    ax.add_patch(hole_c)

    ax.text(36.5, 51.0, "Circular Void\n$R=10$", ha="center", va="center", fontsize=9, fontweight="bold", color="#475569", zorder=8)

    ax.annotate("Secondary Flank Nucleation\n$(46.5, 50.8)$ mm", xy=(46.5, 50.8), xytext=(35, 45.0),
                arrowprops=dict(facecolor="#0f172a", shrink=0.06, width=1.0, headwidth=5),
                fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#94a3b8"))

    ax.annotate("18.56 mm Ligament Refinement\n($h_{\\min} = 0.051$ mm $\\leq \\ell_0/5$)", xy=(55.0, 51.5), xytext=(48, 45.0),
                arrowprops=dict(facecolor="#0f172a", shrink=0.06, width=1.0, headwidth=5),
                fontsize=9, fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="#94a3b8"))

    ax.grid(True, linestyle=":", alpha=0.35, color="#94a3b8", zorder=1)

    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1711] Saved secondary mesh zoom figure: %s and %s" % (out_pdf, out_png))

def main():
    adapt_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")

    print("[F1711] Parsing authentic adapted mesh: %s" % adapt_inp)
    nodes, elements = parse_inp_mesh(adapt_inp)
    polys, eids = get_mesh_polys(nodes, elements)
    print("[F1711] Mesh parsed: %d physical elements, %d nodes" % (len(eids), len(nodes)))

    # 1. Full specimen mesh only
    out_full_pdf = os.path.join(OUT_DIR, "fig_f1711_adaptive_remesh_only.pdf")
    out_full_png = os.path.join(OUT_DIR, "fig_f1711_adaptive_remesh_only.png")
    plot_full_mesh_only(polys, out_full_pdf, out_full_png)

    # 2. Primary process-zone zoom
    out_prim_pdf = os.path.join(OUT_DIR, "fig_f1711_primary_mesh_zoom_only.pdf")
    out_prim_png = os.path.join(OUT_DIR, "fig_f1711_primary_mesh_zoom_only.png")
    plot_primary_zoom_mesh_only(polys, out_prim_pdf, out_prim_png)

    # 3. Secondary process-zone zoom
    out_sec_pdf = os.path.join(OUT_DIR, "fig_f1711_secondary_mesh_zoom_only.pdf")
    out_sec_png = os.path.join(OUT_DIR, "fig_f1711_secondary_mesh_zoom_only.png")
    plot_secondary_zoom_mesh_only(polys, out_sec_pdf, out_sec_png)

    print("[F1711] All clean mesh-only figures generated successfully.")

if __name__ == "__main__":
    main()
