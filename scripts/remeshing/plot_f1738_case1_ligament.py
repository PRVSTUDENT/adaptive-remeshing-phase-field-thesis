# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1738_case1_ligament.py
=============================================
Task F1738: Publication figure comparing the prior F1728 Case 1 mesh (distal under-refinement)
with the authoritative F1738 Case 1 hybrid reference mesh (continuous horizontal ligament resolution).
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp, compute_element_metrics

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.labelsize": 10,
    "axes.titlesize": 11,
    "xtick.labelsize": 8.5,
    "ytick.labelsize": 8.5,
    "figure.titlesize": 12,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

def plot_f1738_comparison():
    f1728_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "219_f1728_five_geometry_study", "PK_F1728_CASE_1_ADAPT_PHYS.inp")
    f1738_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "PK_F1738_CASE_1_ADAPT_PHYS.inp")
    
    l0 = 0.0075  # mm
    
    fig, axes = plt.subplots(1, 2, figsize=(13, 6))
    
    meshes = [
        ("Prior F1728 Automatic Mesh (14,147 Elements)", f1728_inp, axes[0], "PARTIAL: Distal Ligament Coarse (Stations 5-10 h > l0)"),
        ("Authoritative F1738 Hybrid Reference Mesh (13,960 Elements)", f1738_inp, axes[1], "QUALIFIED: Continuous Ligament Refinement (Stations 1-10 h <= l0/2)")
    ]
    
    cmap = plt.cm.viridis_r
    norm = Normalize(vmin=0.0, vmax=2.5)  # Ratio h_e / l0
    
    for title, inp_path, ax, subtitle in meshes:
        nodes, elements, elem_types = parse_abaqus_inp(inp_path)
        metrics = compute_element_metrics(nodes, elements, elem_types, ell_0=l0)
        
        polys = []
        ratios = []
        
        for eid, nids in elements.items():
            pts = [nodes[n] for n in nids]
            polys.append(pts)
            
            # Area
            if len(pts) == 4:
                area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                                 (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                                 (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                                 (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
            else:
                area = 0.5 * abs((pts[1][0]-pts[0][0])*(pts[2][1]-pts[0][1]) - (pts[2][0]-pts[0][0])*(pts[1][1]-pts[0][1]))
            h_e = math.sqrt(area)  # mm
            r = h_e / l0
            ratios.append(min(r, 2.5))
            
        pc = PolyCollection(polys, array=np.array(ratios), cmap=cmap, norm=norm, edgecolors="black", linewidths=0.15)
        ax.add_collection(pc)
        
        # Initial notch line
        ax.plot([0.0, 0.5], [0.5, 0.5], color="red", linewidth=1.8, linestyle="-", label="Initial Crack Seam")
        # Prospective fracture ligament
        ax.plot([0.5, 1.0], [0.5, 0.5], color="cyan", linewidth=1.2, linestyle="--", label="Prospective Ligament")
        
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect("equal")
        ax.set_xlabel("x [mm]")
        ax.set_ylabel("y [mm]")
        ax.set_title(f"{title}\n{subtitle}", fontsize=10.5, pad=8)
        ax.grid(True, linestyle=":", alpha=0.3)
        ax.legend(loc="upper right", fontsize=8)
        
    cbar_ax = fig.add_axes([0.92, 0.15, 0.018, 0.7])
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label(r"Spatial Resolution Ratio $h_e / \ell_0$ (capped at 2.5)", fontsize=9.5)
    
    fig.suptitle("Task F1738: Case 1 Mode-I Ligament Adaptive-Remeshing Resolution Comparison\n"
                 r"(Pandey & Kumar 2025 Section 4.1, $\Omega = 1.0 \times 1.0$ mm, $\ell_0 = 0.0075$ mm)",
                 fontsize=12, fontweight="bold", y=0.98)
    
    out_png = os.path.join(REPO_ROOT, "results", "figures", "fig_f1738_case1_ligament_comparison.png")
    out_pdf = os.path.join(REPO_ROOT, "results", "figures", "fig_f1738_case1_ligament_comparison.pdf")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    
    print(f"Figures saved:\n  PNG: {out_png}\n  PDF: {out_pdf}")

if __name__ == "__main__":
    plot_f1738_comparison()
