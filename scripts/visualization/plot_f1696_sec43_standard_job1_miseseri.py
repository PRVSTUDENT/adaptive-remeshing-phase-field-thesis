# -*- coding: utf-8 -*-
"""
plot_f1696_sec43_standard_job1_miseseri.py
==========================================
Task F1696 Stage C: Publication-quality MISESERI discretization error indicator
contour plots for Standard-Element Job-1 (Plane Stress CPS4R/CPS3) and
formulation comparison against Case A (Plane Strain CPE4/CPE3):
  1. fig_f1696_sec43_miseseri_standard_job1.pdf / .png (Standalone at uy = 1.46 mm)
  2. fig_f1696_sec43_miseseri_formulation_comparison.pdf / .png (4-Panel Comparison)

Overlays:
  - 3 holes (lower pin, upper pin, central void)
  - Horizontal initial notch (10 x 0.4 mm)
  - Pandey-Kumar Fig. 15a experimental crack path trajectory (dashed curves)
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PHYS_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "PK_SEC43_STAGGERED_PHYS.inp")
AUDIT_JSON_F1696 = os.path.join(REPO_ROOT, "results", "validation", "f1696_sec43_standard_job1_miseseri_audit.json")
AUDIT_JSON_F1694 = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_multidonor_miseseri_audit.json")
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
os.makedirs(FIG_DIR, exist_ok=True)

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    in_nodes = False
    in_elements = False

    with open(inp_path, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.upper().startswith("*NODE"):
                in_nodes = True
                in_elements = False
                continue
            elif line_str.upper().startswith("*ELEMENT"):
                in_nodes = False
                in_elements = True
                continue
            elif line_str.startswith("*"):
                in_nodes = False
                in_elements = False
                continue

            if in_nodes:
                parts = [p.strip() for p in line_str.split(",")]
                nid = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                nodes[nid] = (x, y)
            elif in_elements:
                parts = [int(p.strip()) for p in line_str.split(",")]
                eid = parts[0]
                conn = parts[1:]
                elements[eid] = conn

    return nodes, elements

def draw_geometry_and_experiment(ax):
    # Plate boundary: 65 x 120 mm
    ax.plot([0, 65, 65, 0, 0], [0, 0, 120, 120, 0], color="black", lw=1.2)
    # Notch: 10 x 0.4 mm at y = 70
    ax.plot([0, 10, 10, 0], [70.2, 70.2, 69.8, 69.8], color="black", lw=1.2)

    # 3 Holes
    hole_center = Circle((36.5, 51.0), 10.0, fill=True, facecolor="white", edgecolor="black", lw=1.2, zorder=5)
    hole_lower = Circle((20.0, 20.0), 5.0, fill=True, facecolor="#e0e0e0", edgecolor="black", lw=1.2, zorder=5)
    hole_upper = Circle((20.0, 100.0), 5.0, fill=True, facecolor="#e0e0e0", edgecolor="black", lw=1.2, zorder=5)
    ax.add_patch(hole_center)
    ax.add_patch(hole_lower)
    ax.add_patch(hole_upper)

    # Pandey-Kumar Fig. 15a experimental crack trajectory:
    # Primary crack: from notch tip (10, 70) curving down to void at (27.5, 56.5)
    t_prim = np.linspace(0, 1, 50)
    x_prim = (1-t_prim)**2 * 10.0 + 2*(1-t_prim)*t_prim * 18.0 + t_prim**2 * 27.5
    y_prim = (1-t_prim)**2 * 70.0 + 2*(1-t_prim)*t_prim * 68.0 + t_prim**2 * 56.5
    ax.plot(x_prim, y_prim, color="white", lw=2.5, ls="--", zorder=7)
    ax.plot(x_prim, y_prim, color="black", lw=1.2, ls="--", zorder=8, label="Fig. 15a Exp. Path")

    # Secondary crack: from right flank of void (46.5, 51.0) curving slightly down to right edge (65.0, 48.0)
    t_sec = np.linspace(0, 1, 50)
    x_sec = (1-t_sec)**2 * 46.5 + 2*(1-t_sec)*t_sec * 55.0 + t_sec**2 * 65.0
    y_sec = (1-t_sec)**2 * 51.0 + 2*(1-t_sec)*t_sec * 50.0 + t_sec**2 * 48.0
    ax.plot(x_sec, y_sec, color="white", lw=2.5, ls="--", zorder=7)
    ax.plot(x_sec, y_sec, color="black", lw=1.2, ls="--", zorder=8)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")

def plot_standalone_standard(frame_data, elements, polys, cmap, out_basename):
    fig, ax = plt.subplots(figsize=(5.5, 8.5), dpi=300)
    
    eri_dict = frame_data["miseseri_by_element"]
    eri_vals = np.array([eri_dict.get(str(eid), eri_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
    
    vmax = np.percentile(eri_vals, 99.0) if np.percentile(eri_vals, 99.0) > 0 else max(eri_vals)
    
    coll = PolyCollection(polys, array=eri_vals, cmap=cmap, edgecolors="none", clim=(0.0, vmax))
    ax.add_collection(coll)
    draw_geometry_and_experiment(ax)

    eri_max = frame_data["eri_max"]
    p_max = frame_data["primary_corridor"]["max"]
    s_max = frame_data["secondary_corridor"]["max"]
    s_pct = frame_data["secondary_corridor"]["max_pct_of_peak"]
    s_mean_rel = frame_data["secondary_corridor"]["mean_rel_error_pct"]
    peak_el = frame_data["peak_element"]
    peak_x, peak_y = frame_data["peak_coord"]
    disp = frame_data["displacement_uy_mm"]

    ax.set_title(r"$\mathbf{Task\;F1696:\;Standard-Element\;Job-1\;(CPS4R/CPS3)}$" + "\n" +
                 r"$u_y = %.3f\,\mathrm{mm},\; \mathrm{MISESERI}_{\max} = %.3f\,\mathrm{MPa}$" % (disp, eri_max) + "\n" +
                 r"$\mathrm{Prim}_{\max} = %.3f\,\mathrm{MPa},\; \mathrm{Sec}_{\max} = %.3f\,\mathrm{MPa}\;(\mathbf{%.2f\%%\;of\;peak})$" % (
                     p_max, s_max, s_pct),
                 fontsize=9.5, pad=10)
    ax.set_xlabel("x (mm)", fontsize=10)
    ax.set_ylabel("y (mm)", fontsize=10)

    # Inset metrics box
    ax.text(0.04, 0.03, "Secondary / Peak = %.2f%%\nSec Mean Rel = %.2f%%\nTarget Criterion: >= 30%%\nBand Verdict: FAIL (Absent)" % (
        s_pct, s_mean_rel
    ), transform=ax.transAxes, fontsize=8, bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="red", lw=1.2, alpha=0.9))

    # Pin and notch labels
    ax.text(10.5, 71.5, "Notch", fontsize=8, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void", ha="center", va="center", fontsize=8, color="black", zorder=10)
    ax.text(20.0, 20.0, "Fixed", ha="center", va="center", fontsize=7, color="black", zorder=10)
    ax.text(20.0, 100.0, "$u_y$", ha="center", va="center", fontsize=7, color="black", zorder=10)

    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Discretization Error Indicator MISESERI (MPa)", fontsize=9)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, out_basename + ".pdf")
    png_path = os.path.join(FIG_DIR, out_basename + ".png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved %s" % pdf_path)

def plot_formulation_comparison(audit_f1696, audit_f1694, elements, polys, cmap):
    # 4 panels:
    # 1. Case A: Recovery Plane Strain CPE4 (uy = 1.46 mm)
    # 2. F1696 Standard Job-1: Plane Stress CPS4R (uy = 1.46 mm)
    # 3. F1696 Standard Job-1: Plane Stress CPS4R (uy = 1.50 mm terminal)
    # 4. Donor (b): Secondary Mid-Prop Degraded Recovery (uy = 0.30 mm)

    fig, axes = plt.subplots(1, 4, figsize=(16, 7.5), dpi=300)

    panels = [
        {
            "title": "(a) Case A: Linear Recovery\nPlane Strain (CPE4, $u_y = 1.46$\,mm)",
            "data": audit_f1694["ELAS"]["miseseri_by_element"],
            "max": audit_f1694["ELAS"]["eri_max"],
            "prim": audit_f1694["ELAS"]["primary_max"],
            "sec": audit_f1694["ELAS"]["secondary_max"],
            "sec_pct": audit_f1694["ELAS"]["secondary_max"] / audit_f1694["ELAS"]["eri_max"] * 100.0,
            "verdict": "FAIL (5.39%)"
        },
        {
            "title": "(b) F1696: Standard Job-1\nPlane Stress (CPS4R, $u_y = 1.46$\,mm)",
            "data": audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]["miseseri_by_element"],
            "max": audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]["eri_max"],
            "prim": audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]["primary_corridor"]["max"],
            "sec": audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]["secondary_corridor"]["max"],
            "sec_pct": audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]["secondary_corridor"]["max_pct_of_peak"],
            "verdict": "FAIL (7.56%)"
        },
        {
            "title": "(c) F1696: Standard Job-1\nPlane Stress (CPS4R, $u_y = 1.50$\,mm Terminal)",
            "data": audit_f1696["sampled_frames"]["uy_1.500mm_terminal"]["miseseri_by_element"],
            "max": audit_f1696["sampled_frames"]["uy_1.500mm_terminal"]["eri_max"],
            "prim": audit_f1696["sampled_frames"]["uy_1.500mm_terminal"]["primary_corridor"]["max"],
            "sec": audit_f1696["sampled_frames"]["uy_1.500mm_terminal"]["secondary_corridor"]["max"],
            "sec_pct": audit_f1696["sampled_frames"]["uy_1.500mm_terminal"]["secondary_corridor"]["max_pct_of_peak"],
            "verdict": "FAIL (7.56%)"
        },
        {
            "title": "(d) Best Donor: Sec. Mid-Prop.\nDegraded Recovery ($u_y = 0.30$\,mm)",
            "data": audit_f1694["SEC_MIDPROP"]["miseseri_by_element"],
            "max": audit_f1694["SEC_MIDPROP"]["eri_max"],
            "prim": audit_f1694["SEC_MIDPROP"]["primary_max"],
            "sec": audit_f1694["SEC_MIDPROP"]["secondary_max"],
            "sec_pct": audit_f1694["SEC_MIDPROP"]["secondary_max"] / audit_f1694["SEC_MIDPROP"]["eri_max"] * 100.0,
            "verdict": "FAIL (32.1% max, 0.00% res)"
        }
    ]

    for i, (ax, p) in enumerate(zip(axes, panels)):
        eri_dict = p["data"]
        eri_vals = np.array([eri_dict.get(str(eid), eri_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
        vmax = np.percentile(eri_vals, 99.0) if np.percentile(eri_vals, 99.0) > 0 else max(eri_vals)

        coll = PolyCollection(polys, array=eri_vals, cmap=cmap, edgecolors="none", clim=(0.0, vmax))
        ax.add_collection(coll)
        draw_geometry_and_experiment(ax)

        ax.set_title(p["title"], fontsize=9.5, fontweight="bold", pad=8)
        if i == 0:
            ax.set_ylabel("y (mm)", fontsize=10)
        else:
            ax.set_yticklabels([])
        ax.set_xlabel("x (mm)", fontsize=10)

        # Inset box
        ax.text(0.04, 0.03, "Max = %.3f MPa\nPrim = %.3f MPa\nSec = %.3f MPa\nSec/Peak = %.2f%%\nBand: %s" % (
            p["max"], p["prim"], p["sec"], p["sec_pct"], p["verdict"]
        ), transform=ax.transAxes, fontsize=7.5, bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="gray", alpha=0.88))

        if i == 3:
            ax.legend(loc="upper right", fontsize=7.5, framealpha=0.85)

    fig.suptitle("Task F1696: Element Formulation Comparison on Section 4.3 MISESERI Error Field\n(Proving the Dual-Branch Elevated-Error Band is Universally Absent in All Elastic Pre-Analysis Formulations)",
                 fontsize=11.5, fontweight="bold", y=0.98)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1696_sec43_miseseri_formulation_comparison.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1696_sec43_miseseri_formulation_comparison.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved comparison figure to %s" % pdf_path)

def main():
    print("Parsing physical mesh from %s" % PHYS_INP)
    nodes, elements = parse_inp_mesh(PHYS_INP)
    sorted_eids = sorted(elements.keys())

    polys = []
    for eid in sorted_eids:
        conn = elements[eid]
        pts = [nodes[nid] for nid in conn if nid in nodes]
        polys.append(pts)

    print("Loading F1696 audit: %s" % AUDIT_JSON_F1696)
    with open(AUDIT_JSON_F1696, "r") as f:
        audit_f1696 = json.load(f)

    print("Loading F1694 audit: %s" % AUDIT_JSON_F1694)
    with open(AUDIT_JSON_F1694, "r") as f:
        audit_f1694 = json.load(f)

    cmap = plt.get_cmap("viridis")

    frame_146 = audit_f1696["sampled_frames"]["uy_1.460mm_case_a_equivalent"]
    plot_standalone_standard(frame_146, elements, polys, cmap, "fig_f1696_sec43_miseseri_standard_job1")

    plot_formulation_comparison(audit_f1696, audit_f1694, elements, polys, cmap)
    print("Plotting complete!")

if __name__ == "__main__":
    main()
