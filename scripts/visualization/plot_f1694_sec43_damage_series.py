# -*- coding: utf-8 -*-
"""
plot_f1694_sec43_damage_series.py
=================================
Plots publication-quality damage field figures for the 5 key physical states of
the Pandey-Kumar Section 4.3 staggered fracture simulation:
  (a) Initiation: Step-1, Frame 20 (uy = 0.100 mm, RF = 6.377 kN)
  (b) Primary propagation: Step-1, Frame 40 (uy = 0.200 mm, RF = 1.966 kN)
  (c) Secondary initiation: Step-1, Frame 50 (uy = 0.250 mm, RF = 2.207 kN)
  (d) Secondary mid-propagation: Step-1, Frame 60 (uy = 0.300 mm, RF = 1.893 kN)
  (e) Terminal severance: Step-2, Frame 250 (uy = 1.500 mm, RF = 0.001 kN)

Generates:
  - 5 individual state PDFs and PNGs
  - 1 combined 5-panel series PDF and PNG (fig_f1694_sec43_damage_frame_series.pdf)
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
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
PHYS_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_PHYS.inp")
RECORD_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1694_sec43_five_state_damage_record.json")
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

def draw_geometry(ax):
    # Plate boundary: 65 x 120 mm
    ax.plot([0, 65, 65, 0, 0], [0, 0, 120, 120, 0], color="black", lw=1.0)
    # Notch: 10 x 0.4 mm at y = 70
    ax.plot([0, 10, 10, 0], [70.2, 70.2, 69.8, 69.8], color="black", lw=1.0)

    # 3 Holes
    hole_center = Circle((36.5, 51.0), 10.0, fill=True, facecolor="white", edgecolor="black", lw=1.0, zorder=5)
    hole_lower = Circle((20.0, 20.0), 5.0, fill=True, facecolor="#e0e0e0", edgecolor="black", lw=1.0, zorder=5)
    hole_upper = Circle((20.0, 100.0), 5.0, fill=True, facecolor="#e0e0e0", edgecolor="black", lw=1.0, zorder=5)
    ax.add_patch(hole_center)
    ax.add_patch(hole_lower)
    ax.add_patch(hole_upper)

    ax.set_xlim(-2.0, 67.0)
    ax.set_ylim(-2.0, 122.0)
    ax.set_aspect("equal")

def plot_single_state(state, nodes, elements, polys, cmap, out_basename):
    fig, ax = plt.subplots(figsize=(5.5, 8.5), dpi=300)
    
    dmg_dict = state["damage_by_element"]
    d_vals = np.array([dmg_dict.get(str(eid), dmg_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
    
    coll = PolyCollection(polys, array=d_vals, cmap=cmap, edgecolors="none", clim=(0.0, 1.0))
    ax.add_collection(coll)
    draw_geometry(ax)

    # State title and annotation
    name = state["name"]
    uy = state["uy_mm"]
    rf = state["rf2_kN"]
    d_max = state["max_damage_global"]
    p_max = state["max_damage_primary"]
    s_max = state["max_damage_secondary"]

    ax.set_title(r"$\mathbf{%s}$" % name.replace(":", r"\colon") + "\n" +
                 r"$u_y = %.3f\,\mathrm{mm},\; RF_2 = %.3f\,\mathrm{kN},\; d_{\max} = %.3f$" % (uy, rf, d_max) + "\n" +
                 r"$(d_{\mathrm{prim}} = %.3f,\; d_{\mathrm{sec}} = %.3f)$" % (p_max, s_max),
                 fontsize=10, pad=10)
    ax.set_xlabel("x (mm)", fontsize=10)
    ax.set_ylabel("y (mm)", fontsize=10)

    # Pin and notch labels
    ax.text(10.5, 71.5, "Notch", fontsize=8, fontweight="bold", color="black", zorder=10)
    ax.text(36.5, 51.0, "Void\n$R=10$", ha="center", va="center", fontsize=7.5, color="black", zorder=10)
    ax.text(20.0, 20.0, "Fixed", ha="center", va="center", fontsize=7, color="black", zorder=10)
    ax.text(20.0, 100.0, "$u_y$", ha="center", va="center", fontsize=7, color="black", zorder=10)

    cbar = plt.colorbar(coll, ax=ax, fraction=0.035, pad=0.04)
    cbar.set_label("Phase-Field Damage $d$", fontsize=9)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, out_basename + ".pdf")
    png_path = os.path.join(FIG_DIR, out_basename + ".png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved %s" % pdf_path)

def plot_series(states, nodes, elements, polys, cmap):
    fig, axes = plt.subplots(1, 5, figsize=(18, 7.5), dpi=300)

    for i, (ax, state) in enumerate(zip(axes, states)):
        dmg_dict = state["damage_by_element"]
        d_vals = np.array([dmg_dict.get(str(eid), dmg_dict.get(eid, 0.0)) for eid in sorted(elements.keys())])
        
        coll = PolyCollection(polys, array=d_vals, cmap=cmap, edgecolors="none", clim=(0.0, 1.0))
        ax.add_collection(coll)
        draw_geometry(ax)

        short_names = [
            r"(a) Initiation" + "\n" + r"$u_y = 0.100\,\mathrm{mm}$",
            r"(b) Primary Prop." + "\n" + r"$u_y = 0.200\,\mathrm{mm}$",
            r"(c) Sec. Initiation" + "\n" + r"$u_y = 0.250\,\mathrm{mm}$",
            r"(d) Sec. Mid-Prop." + "\n" + r"$u_y = 0.300\,\mathrm{mm}$",
            r"(e) Terminal Sever." + "\n" + r"$u_y = 1.500\,\mathrm{mm}$"
        ]
        
        ax.set_title(short_names[i], fontsize=10, fontweight="bold", pad=8)
        if i == 0:
            ax.set_ylabel("y (mm)", fontsize=10)
        else:
            ax.set_yticklabels([])
        ax.set_xlabel("x (mm)", fontsize=10)

        # Annotations on key panels
        if i == 0:
            ax.text(10.5, 71.5, "Notch", fontsize=7.5, fontweight="bold", zorder=10)
        elif i == 1:
            ax.text(22.0, 62.0, "Primary\ncrack", fontsize=7.5, fontweight="bold", color="darkred", zorder=10)
        elif i == 2:
            ax.text(46.0, 52.0, "Secondary\ninitiation", fontsize=7.5, fontweight="bold", color="darkred", zorder=10)
        elif i == 3:
            ax.text(50.0, 48.0, "Secondary\nmid-prop", fontsize=7.5, fontweight="bold", color="darkred", zorder=10)
        elif i == 4:
            ax.text(52.0, 48.0, "Severed", fontsize=7.5, fontweight="bold", color="darkred", zorder=10)

        # Inset text with RF and max damage
        ax.text(0.04, 0.03, "RF = %.2f kN\n$d_{\\mathrm{prim}} = %.2f$\n$d_{\\mathrm{sec}} = %.2f$" % (
            state["rf2_kN"], state["max_damage_primary"], state["max_damage_secondary"]
        ), transform=ax.transAxes, fontsize=8, bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="gray", alpha=0.85))

    # Single colorbar on right
    fig.subplots_adjust(right=0.91, wspace=0.15)
    cbar_ax = fig.add_axes([0.92, 0.18, 0.015, 0.65])
    cbar = fig.colorbar(coll, cax=cbar_ax)
    cbar.set_label("Phase-Field Damage $d$", fontsize=10)

    fig.suptitle("Pandey--Kumar Section 4.3 Staggered Simulation: 5-State Physical Damage Field Evolution",
                 fontsize=12, fontweight="bold", y=0.98)

    pdf_path = os.path.join(FIG_DIR, "fig_f1694_sec43_damage_frame_series.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1694_sec43_damage_frame_series.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)
    print("Saved combined series %s" % pdf_path)

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

    print("Loading 5-state damage record: %s" % RECORD_JSON)
    with open(RECORD_JSON, "r") as f:
        data = json.load(f)
    states = data["states"]

    cmap = plt.get_cmap("inferno")

    state_basenames = [
        "fig_f1694_sec43_damage_state_a_initiation",
        "fig_f1694_sec43_damage_state_b_primary_prop",
        "fig_f1694_sec43_damage_state_c_secondary_init",
        "fig_f1694_sec43_damage_state_d_secondary_midprop",
        "fig_f1694_sec43_damage_state_e_terminal"
    ]

    for state, base in zip(states, state_basenames):
        plot_single_state(state, nodes, elements, polys, cmap, base)

    plot_series(states, nodes, elements, polys, cmap)
    print("All damage figures successfully generated.")

if __name__ == "__main__":
    main()
