# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1710_authentic_adaptive_mesh.py
===========================================================
Task F1710: Authentic Adaptive-Remesh Visualization and Crack-Path Correction.
Renders standalone publication-quality visualizations of the genuine 10,065-element
adapted mesh with authentic phase-field damage from Abaqus Job 1421915.mmaster02.

Deliverables:
  - fig_f1710_authentic_adaptive_mesh.pdf / .png (Full 65x120 mm specimen)
  - fig_f1710_primary_crack_mesh_zoom.pdf / .png (Primary fracture corridor zoom)
  - fig_f1710_secondary_crack_mesh_zoom.pdf / .png (Secondary fracture corridor zoom)
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors

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

def get_mesh_polys_and_centroids(nodes, elements):
    """Computes polygon vertex lists, centroids, and element IDs."""
    polys = []
    centroids = []
    eids = []
    for eid, conn in sorted(elements.items()):
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) >= 3:
            xc = sum(p[0] for p in pts) / len(pts)
            yc = sum(p[1] for p in pts) / len(pts)
            polys.append(pts)
            centroids.append((xc, yc))
            eids.append(eid)
    return polys, np.array(centroids), np.array(eids)

def plot_full_specimen(polys, eids, damage_dict, out_pdf, out_png):
    """Renders the complete 65x120 mm specimen with authentic adapted mesh and damage contours."""
    fig = plt.figure(figsize=(9, 13), dpi=300)
    ax = fig.add_axes([0.10, 0.08, 0.72, 0.86])

    ax.set_title("Authentic Adapted Finite-Element Mesh and Phase-Field Fracture State\n"
                 "(10,065 Physical Elements, Abaqus Job 1421915.mmaster02, $u_y = 1.50$ mm)",
                 fontsize=11.5, fontweight="bold", pad=12)

    ax.set_xlim(-3, 68)
    ax.set_ylim(-5, 125)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=9)

    # Damage mapping
    d_vals = np.array([damage_dict.get(str(eid), damage_dict.get(eid, 0.0)) for eid in eids])
    d_clipped = np.clip(d_vals, 0.0, 1.0)
    norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
    cmap = plt.cm.jet
    face_colors = [cmap(norm(d)) for d in d_clipped]

    # Draw mesh with visible element edges
    pc = PolyCollection(polys, facecolors=face_colors, edgecolors="#1e293b", linewidths=0.20, alpha=1.0)
    ax.add_collection(pc)

    # Outer specimen boundary
    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.5, zorder=5)
    ax.add_patch(plate)

    # Holes
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="#0f172a", linewidth=1.2, zorder=6)
    ax.add_patch(hole_c)
    hole_l = Circle((20.0, 20.0), 5.0, facecolor="white", edgecolor="#0f172a", linewidth=1.2, zorder=6)
    ax.add_patch(hole_l)
    hole_u = Circle((20.0, 100.0), 5.0, facecolor="white", edgecolor="#0f172a", linewidth=1.2, zorder=6)
    ax.add_patch(hole_u)

    # Initial horizontal notch: 10.0 x 0.4 mm at y = 70.0 mm
    notch = Rectangle((0, 69.8), 10.0, 0.4, facecolor="black", edgecolor="black", zorder=7)
    ax.add_patch(notch)

    # Grid lines
    ax.grid(True, linestyle=":", alpha=0.35, color="#64748b")

    # Colorbar
    cax = fig.add_axes([0.84, 0.15, 0.03, 0.72])
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.set_label("Phase-Field Damage $d$", fontsize=10.5, fontweight="bold")
    cb.ax.tick_params(labelsize=9.5)
    cb.set_ticks(np.linspace(0.0, 1.0, 11))

    # Inset annotations
    ax.text(20.0, 20.0, "Pin\n$R=5$", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#334155", zorder=8)
    ax.text(20.0, 100.0, "Pin\n$R=5$", ha="center", va="center", fontsize=7.5, fontweight="bold", color="#334155", zorder=8)
    ax.text(36.5, 51.0, "Void\n$R=10$", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#334155", zorder=8)

    # Save
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1710] Saved full specimen figure: %s and %s" % (out_pdf, out_png))

def plot_primary_zoom(polys, eids, damage_dict, out_pdf, out_png):
    """Renders zoomed view of the primary fracture corridor (Notch -> Curved Deflection -> Hole)."""
    fig = plt.figure(figsize=(11, 9), dpi=300)
    ax = fig.add_axes([0.10, 0.10, 0.75, 0.82])

    ax.set_title("Primary Fracture-Process Zone: Authentic Mesh and Damage Deflection\n"
                 "(Zoom: $x \\in [0, 42]$ mm, $y \\in [42, 78]$ mm; Abaqus Job 1421915, $u_y = 1.50$ mm)",
                 fontsize=11, fontweight="bold", pad=10)

    ax.set_xlim(-1, 42)
    ax.set_ylim(44, 76)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=9)

    d_vals = np.array([damage_dict.get(str(eid), damage_dict.get(eid, 0.0)) for eid in eids])
    d_clipped = np.clip(d_vals, 0.0, 1.0)
    norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
    cmap = plt.cm.jet
    face_colors = [cmap(norm(d)) for d in d_clipped]

    # Individual element edges clearly visible
    pc = PolyCollection(polys, facecolors=face_colors, edgecolors="#0f172a", linewidths=0.35, alpha=1.0)
    ax.add_collection(pc)

    # Features
    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.5, zorder=5)
    ax.add_patch(plate)
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="#0f172a", linewidth=1.4, zorder=6)
    ax.add_patch(hole_c)
    notch = Rectangle((0, 69.8), 10.0, 0.4, facecolor="black", edgecolor="black", zorder=7)
    ax.add_patch(notch)

    ax.grid(True, linestyle=":", alpha=0.4, color="#64748b")

    cax = fig.add_axes([0.87, 0.15, 0.025, 0.72])
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.set_label("Phase-Field Damage $d$", fontsize=10, fontweight="bold")
    cb.ax.tick_params(labelsize=9)

    ax.text(36.5, 51.0, "Void\n$R=10$", ha="center", va="center", fontsize=9, fontweight="bold", color="#334155", zorder=8)
    ax.annotate("Initial Notch Root\n$(10.0, 70.0)$ mm", xy=(10.0, 70.0), xytext=(3, 62),
                arrowprops=dict(facecolor="#0f172a", shrink=0.05, width=1.0, headwidth=5),
                fontsize=8.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#94a3b8"))

    ax.annotate("Curved Crack\nEnters Void", xy=(30.5, 61.5), xytext=(18, 52),
                arrowprops=dict(facecolor="#0f172a", shrink=0.05, width=1.0, headwidth=5),
                fontsize=8.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#94a3b8"))

    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1710] Saved primary crack zoom figure: %s and %s" % (out_pdf, out_png))

def plot_secondary_zoom(polys, eids, damage_dict, out_pdf, out_png):
    """Renders zoomed view of the secondary fracture corridor (Void Flank -> 18.56 mm Ligament -> Free Edge)."""
    fig = plt.figure(figsize=(12, 10), dpi=300)
    ax = fig.add_axes([0.10, 0.12, 0.75, 0.78])

    ax.set_title("Secondary Fracture-Process Zone: Authentic Mesh and Severance Path\n"
                 "(Zoom: $x \\in [33, 66]$ mm, $y \\in [42, 60]$ mm; Abaqus Job 1421915, $u_y = 1.50$ mm)",
                 fontsize=11, fontweight="bold", pad=10)

    ax.set_xlim(33, 66)
    ax.set_ylim(43, 59)
    ax.set_aspect("equal")
    ax.set_xlabel("$x$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.set_ylabel("$y$ coordinate (mm)", fontsize=10, fontweight="bold")
    ax.tick_params(labelsize=9)

    d_vals = np.array([damage_dict.get(str(eid), damage_dict.get(eid, 0.0)) for eid in eids])
    d_clipped = np.clip(d_vals, 0.0, 1.0)
    norm = mcolors.Normalize(vmin=0.0, vmax=1.0)
    cmap = plt.cm.jet
    face_colors = [cmap(norm(d)) for d in d_clipped]

    pc = PolyCollection(polys, facecolors=face_colors, edgecolors="#0f172a", linewidths=0.35, alpha=1.0)
    ax.add_collection(pc)

    plate = Rectangle((0, 0), 65, 120, fill=False, edgecolor="#0f172a", linewidth=1.5, zorder=5)
    ax.add_patch(plate)
    hole_c = Circle((36.5, 51.0), 10.0, facecolor="white", edgecolor="#0f172a", linewidth=1.4, zorder=6)
    ax.add_patch(hole_c)

    ax.grid(True, linestyle=":", alpha=0.4, color="#64748b")

    cax = fig.add_axes([0.87, 0.18, 0.025, 0.66])
    cb = plt.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax)
    cb.set_label("Phase-Field Damage $d$", fontsize=10, fontweight="bold")
    cb.ax.tick_params(labelsize=9)

    ax.text(36.5, 51.0, "Void\n$R=10$", ha="center", va="center", fontsize=9, fontweight="bold", color="#334155", zorder=8)

    ax.annotate("Secondary Nucleation\n$(46.5, 50.8)$ mm", xy=(46.5, 50.8), xytext=(36, 44.5),
                arrowprops=dict(facecolor="#0f172a", shrink=0.05, width=1.0, headwidth=5),
                fontsize=8.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#94a3b8"))

    ax.annotate("Complete Severance\n$x = 65.0$ mm", xy=(65.0, 51.8), xytext=(53, 44.5),
                arrowprops=dict(facecolor="#0f172a", shrink=0.05, width=1.0, headwidth=5),
                fontsize=8.5, fontweight="bold", bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#94a3b8"))

    plt.savefig(out_pdf, bbox_inches="tight")
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    print("[F1710] Saved secondary crack zoom figure: %s and %s" % (out_pdf, out_png))

def main():
    adapt_inp = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")
    damage_json = os.path.join(REPO_ROOT, "results", "validation", "f1709_job2_damage_field.json")

    print("[F1710] Parsing adapted mesh: %s" % adapt_inp)
    nodes, elements = parse_inp_mesh(adapt_inp)
    polys, centroids, eids = get_mesh_polys_and_centroids(nodes, elements)
    print("[F1710] Mesh parsed: %d elements, %d nodes" % (len(eids), len(nodes)))

    print("[F1710] Loading damage field: %s" % damage_json)
    with open(damage_json, "r") as f:
        job2_data = json.load(f)

    # Use fully severed state (state_4_severance, uy = 1.50 mm)
    damage_dict = job2_data["damage_states"]["state_4_severance"]["elem_damage"]

    # 1. Full specimen
    out_full_pdf = os.path.join(OUT_DIR, "fig_f1710_authentic_adaptive_mesh.pdf")
    out_full_png = os.path.join(OUT_DIR, "fig_f1710_authentic_adaptive_mesh.png")
    plot_full_specimen(polys, eids, damage_dict, out_full_pdf, out_full_png)

    # 2. Primary crack zoom
    out_prim_pdf = os.path.join(OUT_DIR, "fig_f1710_primary_crack_mesh_zoom.pdf")
    out_prim_png = os.path.join(OUT_DIR, "fig_f1710_primary_crack_mesh_zoom.png")
    plot_primary_zoom(polys, eids, damage_dict, out_prim_pdf, out_prim_png)

    # 3. Secondary crack zoom
    out_sec_pdf = os.path.join(OUT_DIR, "fig_f1710_secondary_crack_mesh_zoom.pdf")
    out_sec_png = os.path.join(OUT_DIR, "fig_f1710_secondary_crack_mesh_zoom.png")
    plot_secondary_zoom(polys, eids, damage_dict, out_sec_pdf, out_sec_png)

    print("[F1710] All figures generated successfully.")

if __name__ == "__main__":
    main()
