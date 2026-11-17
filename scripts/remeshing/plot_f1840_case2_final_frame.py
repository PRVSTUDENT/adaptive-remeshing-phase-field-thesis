# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1840_case2_final_frame.py
=================================================
Task F1840: Generates publication-quality figures:
1. fig_f1840_case2_final_frame_mesh.png / .pdf (2-panel view of final frame mesh)
2. fig_f1840_case2_comparison.png / .pdf (side-by-side comparison between Frame 300 and Final Frame 337)
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

F300_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot", "PK_F1838_CASE_2_PILOT_PHYS.inp")
F337_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp")

OUT_FIG_DIR_1 = os.path.join(REPO_ROOT, "results", "figures")
OUT_FIG_DIR_2 = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison", "figures")

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

def parse_mesh(inp_path, l0=0.0075):
    nodes, quad_conns, tri_conns = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    all_conns = []
    for eid, conn in quad_conns.items():
        all_conns.append((eid, conn, 4))
    for eid, conn in tri_conns.items():
        all_conns.append((eid, conn, 3))

    verts = []
    h_ratios = []
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
    return verts, np.array(h_ratios), len(quad_conns), len(tri_conns)

def main():
    print("=" * 80)
    print("PLOTTING F1840 CASE 2 FINAL-FRAME MESH & COMPARISON")
    print("=" * 80)

    assert os.path.exists(F337_INP), "Missing final frame INP: %s" % F337_INP
    assert os.path.exists(F300_INP), "Missing Frame 300 INP: %s" % F300_INP

    v337, hr337, n_q337, n_t337 = parse_mesh(F337_INP)
    tot337 = n_q337 + n_t337
    q_pct337 = (n_q337 / float(tot337)) * 100.0

    v300, hr300, n_q300, n_t300 = parse_mesh(F300_INP)
    tot300 = n_q300 + n_t300
    q_pct300 = (n_q300 / float(tot300)) * 100.0

    print("Loaded Frame 337: %d elements (%d quads, %d tris, %.2f%% quads)" % (tot337, n_q337, n_t337, q_pct337))
    print("Loaded Frame 300: %d elements (%d quads, %d tris, %.2f%% quads)" % (tot300, n_q300, n_t300, q_pct300))

    cmap = plt.get_cmap("viridis_r")
    norm = matplotlib.colors.Normalize(vmin=0.1, vmax=2.5)

    # -------------------------------------------------------------
    # Figure 1: 2-Panel View of Final Frame Mesh
    # -------------------------------------------------------------
    fig1, axes1 = plt.subplots(1, 2, figsize=(13.5, 6.2), dpi=300)

    # Panel (a): Full Field
    ax1 = axes1[0]
    pc1 = PolyCollection(v337, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.08)
    pc1.set_array(hr337)
    ax1.add_collection(pc1)
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect("equal")
    ax1.set_xlabel("x [mm]", fontsize=11)
    ax1.set_ylabel("y [mm]", fontsize=11)
    ax1.set_title("(a) Full-Field Discretization & Resolution $h / \ell_0$\n"
                   "(%d elements, %.2f%% Quads, $\min\det(J) > 0$)" % (tot337, q_pct337), fontsize=11, fontweight="bold")
    ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', linewidth=1.5, label="Initial Slit ($a_0 = 0.5$ mm)")
    hole_patch1 = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='none', linestyle='--', linewidth=1.2)
    ax1.add_patch(hole_patch1)
    cbar1 = plt.colorbar(pc1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Characteristic Sizing Ratio $h / \ell_0$", fontsize=10)

    # Panel (b): Zoomed Ligament Detail
    ax2 = axes1[1]
    pc2 = PolyCollection(v337, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
    pc2.set_array(hr337)
    ax2.add_collection(pc2)
    ax2.set_xlim(0.45, 1.01)
    ax2.set_ylim(0.40, 0.90)
    ax2.set_aspect("equal")
    ax2.set_xlabel("x [mm]", fontsize=11)
    ax2.set_ylabel("y [mm]", fontsize=11)
    ax2.set_title("(b) Zoomed Detail: Notch, Off-Axis Hole & Outer Distal Ligament\n"
                   "(Final Converged Frame 337, $t = 0.6558$ s, $d_{\max} = 0.9976$)", fontsize=11, fontweight="bold")
    ax2.plot([0.45, 0.5], [0.5, 0.5], 'r-', linewidth=2.0)
    hole_patch2 = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', linestyle='-', linewidth=1.5)
    ax2.add_patch(hole_patch2)
    ax2.text(0.48, 0.52, "Notch Tip\n(0.5, 0.5)", color='darkred', fontsize=9, fontweight='bold')
    ax2.text(0.65, 0.65, "Hole\n(0.65, 0.65)", color='darkred', fontsize=9, fontweight='bold', ha='center', va='center')
    cbar2 = plt.colorbar(pc2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Characteristic Sizing Ratio $h / \ell_0$", fontsize=10)

    plt.suptitle("Task F1840: Case 2 Final-Frame Native Remeshed Physical Mesh (Paper-Reproduction Reference)\n"
                 "Untouched Native MISESERI/MISESAVG (Step-2 Frame 337, $t=0.6558$ s), Error Target 4.0%, UNIFORM_ERROR",
                 fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    png1_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1840_case2_final_frame_mesh.png")
    pdf1_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1840_case2_final_frame_mesh.pdf")
    png1_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1840_case2_final_frame_mesh.png")
    pdf1_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1840_case2_final_frame_mesh.pdf")
    fig1.savefig(png1_1, dpi=300); fig1.savefig(pdf1_1)
    fig1.savefig(png1_2, dpi=300); fig1.savefig(pdf1_2)
    plt.close(fig1)

    # -------------------------------------------------------------
    # Figure 2: Side-by-Side Comparison (Frame 300 vs Frame 337)
    # -------------------------------------------------------------
    fig2, axes2 = plt.subplots(1, 2, figsize=(14.0, 6.5), dpi=300)

    # Left: Frame 300 (Crack-Arrest Diagnostic)
    ax_l = axes2[0]
    pc_l = PolyCollection(v300, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.12)
    pc_l.set_array(hr300)
    ax_l.add_collection(pc_l)
    ax_l.set_xlim(0.45, 1.01)
    ax_l.set_ylim(0.40, 0.90)
    ax_l.set_aspect("equal")
    ax_l.set_xlabel("x [mm]", fontsize=11)
    ax_l.set_ylabel("y [mm]", fontsize=11)
    ax_l.set_title("(a) Crack-Arrest Diagnostic: Evolved Frame 300\n"
                   "$t=0.5937$ s, $d_{\max}=0.9972$ (28,165 elements total, 10,280 distal)", fontsize=11, fontweight="bold")
    ax_l.plot([0.45, 0.5], [0.5, 0.5], 'r-', linewidth=2.0)
    h_l = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', linestyle='-', linewidth=1.5)
    ax_l.add_patch(h_l)
    ax_l.text(0.65, 0.65, "Hole", color='darkred', fontsize=9, fontweight='bold', ha='center', va='center')
    cbar_l = plt.colorbar(pc_l, ax=ax_l, fraction=0.046, pad=0.04)
    cbar_l.set_label("$h / \ell_0$", fontsize=10)

    # Right: Frame 337 (Paper-Reproduction Reference)
    ax_r = axes2[1]
    pc_r = PolyCollection(v337, cmap=cmap, norm=norm, edgecolors="black", linewidths=0.12)
    pc_r.set_array(hr337)
    ax_r.add_collection(pc_r)
    ax_r.set_xlim(0.45, 1.01)
    ax_r.set_ylim(0.40, 0.90)
    ax_r.set_aspect("equal")
    ax_r.set_xlabel("x [mm]", fontsize=11)
    ax_r.set_ylabel("y [mm]", fontsize=11)
    ax_r.set_title("(b) Paper-Reproduction Reference: Final Frame 337\n"
                   "$t=0.6558$ s, $d_{\max}=0.9976$ (%d elements total)" % tot337, fontsize=11, fontweight="bold")
    ax_r.plot([0.45, 0.5], [0.5, 0.5], 'r-', linewidth=2.0)
    h_r = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', linestyle='-', linewidth=1.5)
    ax_r.add_patch(h_r)
    ax_r.text(0.65, 0.65, "Hole", color='darkred', fontsize=9, fontweight='bold', ha='center', va='center')
    cbar_r = plt.colorbar(pc_r, ax=ax_r, fraction=0.046, pad=0.04)
    cbar_r.set_label("$h / \ell_0$", fontsize=10)

    plt.suptitle("Task F1840: Case 2 Direct Comparison — Crack-Arrest Diagnostic (Frame 300) vs Final Frame (337)\n"
                 "Both remeshed via untouched native UNIFORM_ERROR 4.0% ([0.001, 0.020] mm, coarsening NOT_ALLOWED)",
                 fontsize=12, fontweight="bold", y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.93])

    png2_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1840_case2_comparison.png")
    pdf2_1 = os.path.join(OUT_FIG_DIR_1, "fig_f1840_case2_comparison.pdf")
    png2_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1840_case2_comparison.png")
    pdf2_2 = os.path.join(OUT_FIG_DIR_2, "fig_f1840_case2_comparison.pdf")
    fig2.savefig(png2_1, dpi=300); fig2.savefig(pdf2_1)
    fig2.savefig(png2_2, dpi=300); fig2.savefig(pdf2_2)
    plt.close(fig2)

    print("\nSaved Final Frame Figure:")
    for p in [png1_1, pdf1_1, png1_2, pdf1_2]:
        print("  %s (%d bytes, SHA-256: %s)" % (p, os.path.getsize(p), sha256_file(p)))

    print("\nSaved Comparison Figure:")
    for p in [png2_1, pdf2_1, png2_2, pdf2_2]:
        print("  %s (%d bytes, SHA-256: %s)" % (p, os.path.getsize(p), sha256_file(p)))

if __name__ == "__main__":
    main()
