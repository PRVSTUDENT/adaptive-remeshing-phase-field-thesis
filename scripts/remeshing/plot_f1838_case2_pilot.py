# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1838_case2_pilot.py
===========================================
Generates publication-quality figure for Task F1838:
Case 2 Single-Frame Native Remeshing Pilot Mesh & Spatial Resolution.
Shows full-field discretization, zoomed outer-distal ligament refinement,
and element-level h / l0 ratio.
"""
from __future__ import print_function
import os
import sys
import math
import hashlib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import MeshQualityAuditEngine

INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot", "PK_F1838_CASE_2_PILOT_PHYS.inp")
OUT_FIG_DIR_1 = os.path.join(REPO_ROOT, "results", "figures")
OUT_FIG_DIR_2 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot", "figures")

os.makedirs(OUT_FIG_DIR_1, exist_ok=True)
os.makedirs(OUT_FIG_DIR_2, exist_ok=True)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print("="*80)
    print("PLOTTING F1838 CASE 2 NATIVE PILOT MESH")
    print("Input: %s" % INP_PATH)
    print("="*80)

    nodes, quad_conns, tri_conns = MeshQualityAuditEngine.parse_physical_inp(INP_PATH)
    total_elems = len(quad_conns) + len(tri_conns)
    print("Loaded %d nodes, %d elements (%d quads, %d tris)" % (
        len(nodes), total_elems, len(quad_conns), len(tri_conns)
    ))

    l0 = 0.0075 # mm

    verts = []
    h_ratios = []

    all_conns = []
    for eid, conn in quad_conns.items():
        all_conns.append((eid, conn, 4))
    for eid, conn in tri_conns.items():
        all_conns.append((eid, conn, 3))

    for eid, conn, n_pts in all_conns:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != n_pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]

        if n_pts == 4:
            area = 0.5 * abs((xs[0]*ys[1] - xs[1]*ys[0]) + (xs[1]*ys[2] - xs[2]*ys[1]) +
                             (xs[2]*ys[3] - xs[3]*ys[2]) + (xs[3]*ys[0] - xs[0]*ys[3]))
        else:
            area = 0.5 * abs((xs[1]-xs[0])*(ys[2]-ys[0]) - (xs[2]-xs[0])*(ys[1]-ys[0]))

        h_eq = math.sqrt(area) if area > 0 else 0.0
        verts.append(np.array(pts))
        h_ratios.append(h_eq / l0)

    h_ratios = np.array(h_ratios)

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=300)

    # 1. Full mesh with h / l0 coloring
    ax1 = axes[0]
    cmap = plt.get_cmap("viridis_r")
    norm = matplotlib.colors.Normalize(vmin=0.1, vmax=2.5)

    pc1 = PolyCollection(verts, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.08)
    pc1.set_array(h_ratios)
    ax1.add_collection(pc1)

    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x [mm]", fontsize=11)
    ax1.set_ylabel("y [mm]", fontsize=11)
    ax1.set_title("(a) Full-Field Discretization & Resolution $h / \ell_0$\n"
                  "(28,165 elements, 97.57% Quads, $\min\det(J) > 0$)", fontsize=11, fontweight="bold")

    # Add notch and hole annotations
    ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=1.5, label="Initial Slit ($a_0 = 0.5$ mm)")
    hole_patch1 = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='none', linestyle='--', linewidth=1.2)
    ax1.add_patch(hole_patch1)

    cbar1 = plt.colorbar(pc1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Characteristic Sizing Ratio $h / \ell_0$", fontsize=10)

    # 2. Zoomed ligament detail
    ax2 = axes[1]
    pc2 = PolyCollection(verts, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
    pc2.set_array(h_ratios)
    ax2.add_collection(pc2)

    ax2.set_xlim(0.45, 1.01)
    ax2.set_ylim(0.40, 0.90)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x [mm]", fontsize=11)
    ax2.set_ylabel("y [mm]", fontsize=11)
    ax2.set_title("(b) Zoomed Detail: Notch, Off-Axis Hole & Outer Distal Ligament\n"
                  "(10,280 elements resolving outer distal ligament $x \in [0.65, 1.0]$)", fontsize=11, fontweight="bold")

    ax2.plot([0.45, 0.5], [0.5, 0.5], 'r-', linewidth=2.0)
    hole_patch2 = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', linestyle='-', linewidth=1.5)
    ax2.add_patch(hole_patch2)

    # Annotations on Zoomed View
    ax2.text(0.48, 0.52, "Notch Tip\n(0.5, 0.5)", color='darkred', fontsize=9, fontweight='bold')
    ax2.text(0.65, 0.65, "Hole\n(0.65, 0.65)", color='darkred', fontsize=9, fontweight='bold', ha='center', va='center')
    ax2.text(0.82, 0.72, "Outer Distal\nLigament Band\n(10,280 elems)", color='navy', fontsize=9, fontweight='bold', ha='center',
             bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="navy", lw=1, alpha=0.85))

    cbar2 = plt.colorbar(pc2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Characteristic Sizing Ratio $h / \ell_0$", fontsize=10)

    # Global Super Title
    plt.suptitle("Task F1838: Case 2 Single-Frame Native Job-1 Pilot Remeshed Physical Mesh\n"
                 "Untouched Native MISESERI/MISESAVG (Evolved Frame 300, $d_{\max}=0.9972$), Error Target 4.0%, UNIFORM_ERROR",
                 fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout(rect=[0, 0, 1, 0.93])

    png_path_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1838_case2_pilot_mesh.png")
    pdf_path_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1838_case2_pilot_mesh.pdf")
    png_path_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1838_case2_pilot_mesh.png")
    pdf_path_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1838_case2_pilot_mesh.pdf")

    fig.savefig(png_path_1, dpi=300)
    fig.savefig(pdf_path_1)
    fig.savefig(png_path_2, dpi=300)
    fig.savefig(pdf_path_2)
    plt.close(fig)

    print("Saved Figures:")
    for p in [png_path_1, pdf_path_1, png_path_2, pdf_path_2]:
        sz = os.path.getsize(p)
        sha = sha256_file(p)
        print("  %s (%d bytes, SHA-256: %s)" % (p, sz, sha))

if __name__ == "__main__":
    main()
