# -*- coding: utf-8 -*-
"""
plot_f1694_sec43_miseseri_series.py
===================================
Task F1694 Stage 2: Publication-quality MISESERI discretization error indicator
contour plots across 4 donor cases for Pandey-Kumar Section 4.3 benchmark:
  1. Donor (a): Secondary initiation (uy = 0.25 mm) -> fig_f1694_sec43_miseseri_sec_init.pdf
  2. Donor (b): Secondary mid-propagation (uy = 0.30 mm) -> fig_f1694_sec43_miseseri_sec_midprop.pdf
  3. Donor (c): Terminal degraded stiffness (uy = 1.46 mm) -> fig_f1694_sec43_miseseri_terminal_deg.pdf
  4. Donor (d): Intact linear elastic pre-analysis (uy = 1.46 mm) -> fig_f1694_sec43_miseseri_terminal_elas.pdf
  5. Multi-panel 4-case comparison -> fig_f1694_sec43_miseseri_multidonor_comparison.pdf

Overlays:
  - 3 holes (lower pin, upper pin, central void)
  - Horizontal initial notch (10 x 0.4 mm)
  - Pandey-Kumar Fig. 15a experimental crack path trajectory (dashed white/black curve)
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle, PathPatch
import matplotlib.path as mpath

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
PHYS_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_PHYS.inp")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_multidonor_miseseri_audit.json")
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
    # Bezier control points: P0=(10, 70), P1=(18, 68), P2=(27.5, 56.5)
    x_prim = (1-t_prim)**2 * 10.0 + 2*(1-t_prim)*t_prim * 18.0 + t_prim**2 * 27.5
    y_prim = (1-t_prim)**2 * 70.0 + 2*(1-t_prim)*t_prim * 68.0 + t_prim**2 * 56.5
    ax.plot(x_prim, y_prim, color="white", lw=2.5, ls="--", zorder=7)
    ax.plot(x_prim, y_prim, color="black", lw=1.2, ls="--", zorder=8, label="Fig. 15a Exp. Path")

    # Secondary crack: from right flank of void (46.5, 51.0) curving slightly down to right edge (65.0, 48.0)
    t_sec = np.linspace(0, 1, 50)
    # Bezier control points: P0=(46.5, 51.0), P1=(55.0, 50.0), P2=(65.0, 48.0)
    x_sec = (1-t_sec)**2 * 46.5 + 2*(1-t_sec)*t_sec * 55.0 + t_sec**2 * 65.0
    y_sec = (1-t_sec)**2 * 51.0 + 2*(1-t_sec)*t_sec * 50.0 + t_sec**2 * 48.0
    ax.plot(x_sec, y_sec, color="white", lw=2.5, ls="--", zorder=7)
    ax.plot(x_sec, y_sec, color="black", lw=1.2, ls="--", zorder=8)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")

def plot_single_donor(case_data, nodes, elements, polys, cmap, out_basename):
    fig, ax = plt.subplots(figsize=(5.5, 8.5), dpi=300)
    
    eri_dict = case_data["miseseri_by_element"]
    eri_vals = np.array([eri_dict.get(str(eid), eri_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
    
    # Scale: normalize by 98th percentile or max for clear visualization
    vmax = np.percentile(eri_vals, 99.0) if np.percentile(eri_vals, 99.0) > 0 else max(eri_vals)
    
    coll = PolyCollection(polys, array=eri_vals, cmap=cmap, edgecolors="none", clim=(0.0, vmax))
    ax.add_collection(coll)
    draw_geometry_and_experiment(ax)

    desc = case_data["description"]
    j_code = case_data["job_code"]
    eri_max = case_data["eri_max"]
    p_max = case_data["primary_max"]
    s_max = case_data["secondary_max"]
    peak_el = case_data["peak_element"]
    peak_x, peak_y = case_data["peak_coord"]

    ax.set_title(r"$\mathbf{%s}$" % desc + "\n" +
                 r"$\mathrm{MISESERI}_{\max} = %.3f,\; \mathrm{Prim}_{\max} = %.3f,\; \mathrm{Sec}_{\max} = %.3f$" % (
                     eri_max, p_max, s_max) + "\n" +
                 r"Peak at elem %d (%0.1f, %0.1f)\,mm" % (peak_el, peak_x, peak_y),
                 fontsize=9.5, pad=10)
    ax.set_xlabel("x (mm)", fontsize=10)
    ax.set_ylabel("y (mm)", fontsize=10)

    # Pin and notch labels
    ax.text(10.5, 71.5, "Notch", fontsize=8, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void", ha="center", va="center", fontsize=8, color="black", zorder=10)
    ax.text(20.0, 20.0, "Fixed", ha="center", va="center", fontsize=7, color="black", zorder=10)
    ax.text(20.0, 100.0, "$u_y$", ha="center", va="center", fontsize=7, color="black", zorder=10)

    # Legend for experimental path
    ax.legend(loc="upper right", fontsize=8, framealpha=0.85)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Discretization Error Indicator MISESERI", fontsize=9)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, out_basename + ".pdf")
    png_path = os.path.join(FIG_DIR, out_basename + ".png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved %s" % pdf_path)

def plot_comparison(audit_data, nodes, elements, polys, cmap):
    cases = ["SEC_INIT", "SEC_MIDPROP", "DEG", "ELAS"]
    titles = [
        "(a) Donor: Sec. Initiation\n$u_y = 0.250$\,mm (Degraded)",
        "(b) Donor: Sec. Mid-Prop.\n$u_y = 0.300$\,mm (Degraded)",
        "(c) Donor: Terminal Degraded\n$u_y = 1.460$\,mm (Relaxed)",
        "(d) Donor: Intact Elastic\n$u_y = 1.460$\,mm (Pre-Analysis)"
    ]

    fig, axes = plt.subplots(1, 4, figsize=(16, 7.5), dpi=300)

    for i, (ax, c_code) in enumerate(zip(axes, cases)):
        case_data = audit_data[c_code]
        eri_dict = case_data["miseseri_by_element"]
        eri_vals = np.array([eri_dict.get(str(eid), eri_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
        
        vmax = np.percentile(eri_vals, 99.0) if np.percentile(eri_vals, 99.0) > 0 else max(eri_vals)
        coll = PolyCollection(polys, array=eri_vals, cmap=cmap, edgecolors="none", clim=(0.0, vmax))
        ax.add_collection(coll)
        draw_geometry_and_experiment(ax)

        ax.set_title(titles[i], fontsize=10, fontweight="bold", pad=8)
        if i == 0:
            ax.set_ylabel("y (mm)", fontsize=10)
        else:
            ax.set_yticklabels([])
        ax.set_xlabel("x (mm)", fontsize=10)

        # Inset metrics
        ax.text(0.04, 0.03, "Max = %.3f\nPrim = %.3f\nSec = %.3f\nPeak: (%0.1f, %0.1f)" % (
            case_data["eri_max"], case_data["primary_max"], case_data["secondary_max"],
            case_data["peak_coord"][0], case_data["peak_coord"][1]
        ), transform=ax.transAxes, fontsize=8, bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="gray", alpha=0.85))

        if i == 3:
            ax.legend(loc="upper right", fontsize=7.5, framealpha=0.85)

    fig.suptitle("Pandey--Kumar Section 4.3 Multi-Donor MISESERI Error Indicator Comparison\n(Dashed Curves: Experimental Crack Trajectory from Paper Fig. 15a)",
                 fontsize=12, fontweight="bold", y=0.98)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1694_sec43_miseseri_multidonor_comparison.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1694_sec43_miseseri_multidonor_comparison.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved multi-donor comparison %s" % pdf_path)

def main():
    print("Parsing physical mesh: %s" % PHYS_INP)
    nodes, elements = parse_inp_mesh(PHYS_INP)
    sorted_eids = sorted(elements.keys())
    print("Parsed %d elements." % len(sorted_eids))

    polys = []
    for eid in sorted_eids:
        conn = elements[eid]
        pts = [nodes[nid] for nid in conn if nid in nodes]
        polys.append(pts)

    print("Loading audit data: %s" % AUDIT_JSON)
    with open(AUDIT_JSON, "r") as f:
        audit_data = json.load(f)

    cmap = plt.get_cmap("viridis")

    plot_single_donor(audit_data["SEC_INIT"], nodes, elements, polys, cmap, "fig_f1694_sec43_miseseri_sec_init")
    plot_single_donor(audit_data["SEC_MIDPROP"], nodes, elements, polys, cmap, "fig_f1694_sec43_miseseri_sec_midprop")
    plot_single_donor(audit_data["DEG"], nodes, elements, polys, cmap, "fig_f1694_sec43_miseseri_terminal_deg")
    plot_single_donor(audit_data["ELAS"], nodes, elements, polys, cmap, "fig_f1694_sec43_miseseri_terminal_elas")

    plot_comparison(audit_data, nodes, elements, polys, cmap)
    print("All MISESERI figures successfully generated.")

if __name__ == "__main__":
    main()
