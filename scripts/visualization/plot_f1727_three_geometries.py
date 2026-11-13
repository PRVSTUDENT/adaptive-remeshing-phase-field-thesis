# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1727_three_geometries.py
===================================================
Task F1727: Generate Publication-Quality Figures for Three 2D Fracture Geometries
(Models A, B, and C).

Generated Figures for EACH Model:
1. Exact Geometry Diagram & Boundary Conditions (PDF + PNG)
2. Coarse Physical Mesh Wireframe (PDF + PNG)
3. Coarse Authentic MISESERI Error Indicator Contour (PDF + PNG)
4. Final Adapted Physical Mesh Wireframe (PDF + PNG)
5. High-Resolution Zoom Views of Ligaments & Notches (PDF + PNG)
6. Element-Size Distribution (h_area and h_edge) (PDF + PNG)
Plus:
- 3-Model Side-by-Side Comparative Figure (PDF + PNG)
"""

from __future__ import print_function
import os
import sys
import json
import math
import shutil
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.colors import LogNorm, Normalize

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    get_geometry_adapter,
    MeshQualityAuditEngine
)

OUT_DIR_LOCAL = "figures/f1727_three_geometries"
OUT_DIR_REPORT = "MA_AdaptiveRemeshing_Report_2026/figures/f1727_three_geometries"

os.makedirs(OUT_DIR_LOCAL, exist_ok=True)
os.makedirs(OUT_DIR_REPORT, exist_ok=True)

MODELS = [
    {
        "id": "model_a",
        "short_name": "Model A",
        "title": "Model A: Sec. 4.3 Notched Plate with Hole (65 x 120 mm)",
        "config_path": "configs/remeshing/model_a_sec43_notched_hole_plate.json",
        "coarse_inp": "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_COARSE_PHYS.inp",
        "miseseri_json": "results/validation/f1727_model_a_miseseri.json",
        "adapt_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_A_ADAPT_PHYS.inp",
        "audit_json": "results/validation/f1727_model_a_mesh_audit.json",
        "zoom_bbox": (5.0, 35.0, 40.0, 80.0), # (xmin, xmax, ymin, ymax)
        "scale_unit": "mm"
    },
    {
        "id": "model_b",
        "short_name": "Model B",
        "title": "Model B: Sec. 4.1 Mode-I Edge-Cracked Plate (1 x 1 mm)",
        "config_path": "configs/remeshing/model_b_sec41_mode1_edge_crack.json",
        "coarse_inp": "models/pandey_kumar_mode1/02_proposed_adaptive_refined/PK_PREANALYSIS_COARSE.inp",
        "miseseri_json": "results/validation/f1727_model_b_miseseri.json",
        "adapt_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_B_ADAPT_PHYS.inp",
        "audit_json": "results/validation/f1727_model_b_mesh_audit.json",
        "zoom_bbox": (0.40, 0.70, 0.40, 0.60),
        "scale_unit": "mm"
    },
    {
        "id": "model_c",
        "short_name": "Model C",
        "title": "Model C: Original Thesis Single Off-Axis Hole Plate (1 x 1 mm)",
        "config_path": "configs/remeshing/model_c_original_off_axis_hole.json",
        "coarse_inp": "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_PHYS.inp",
        "miseseri_json": "results/validation/f1727_model_c_miseseri.json",
        "adapt_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_C_ADAPT_PHYS.inp",
        "audit_json": "results/validation/f1727_model_c_mesh_audit.json",
        "zoom_bbox": (0.45, 0.85, 0.45, 0.80),
        "scale_unit": "mm"
    }
]


def save_fig(fig, base_name):
    for d in [OUT_DIR_LOCAL, OUT_DIR_REPORT]:
        png_path = os.path.join(d, base_name + ".png")
        pdf_path = os.path.join(d, base_name + ".pdf")
        fig.savefig(png_path, dpi=300, bbox_inches='tight')
        fig.savefig(pdf_path, dpi=300, bbox_inches='tight')
    print("Saved figure: %s (.png and .pdf)" % base_name)
    plt.close(fig)


# ==============================================================================
# FIGURE 1: GEOMETRY & BOUNDARY CONDITIONS
# ==============================================================================
def plot_geometry_diagram(cfg, m_info):
    fig, ax = plt.subplots(figsize=(6.5, 7.5), dpi=300)
    
    W = cfg.plate_w
    H = cfg.plate_h
    unit = m_info["scale_unit"]

    # Outer rectangle
    outer_rect = patches.Rectangle((0, 0), W, H, fill=True, facecolor="#F8F9FA", edgecolor="#212529", linewidth=2.0)
    ax.add_patch(outer_rect)

    # Slit notch
    if cfg.notch_a is not None:
        notch_w = cfg.notch_w
        notch_rect = patches.Rectangle((0, cfg.notch_y - notch_w), cfg.notch_a, 2.0 * notch_w,
                                       fill=True, facecolor="white", edgecolor="#C92A2A", linewidth=1.8, linestyle="--")
        ax.add_patch(notch_rect)
        # Notch dimension label
        ax.annotate(r"$a = %.1f\,\mathrm{%s}$" % (cfg.notch_a, unit),
                    xy=(cfg.notch_a / 2.0, cfg.notch_y + (notch_w * 4.0 if H > 10 else 0.04)),
                    ha='center', va='bottom', fontsize=10, color='#C92A2A', fontweight='bold')

    # Holes / Voids
    adapter = get_geometry_adapter(cfg)
    holes = adapter.get_hole_definitions()
    for h in holes:
        hx, hy, hr = h[0], h[1], h[2]
        circ = patches.Circle((hx, hy), hr, fill=True, facecolor="white", edgecolor="#1864AB", linewidth=1.8)
        ax.add_patch(circ)
        ax.plot(hx, hy, '+', color='#1864AB', markersize=6)
        # Label radius
        ax.text(hx, hy, r"$R = %.1f$" % hr, ha='center', va='center', fontsize=8, color='#1864AB', fontweight='bold')

    # Boundary conditions
    if cfg.loading_type == "PIN_HOLE_PULL":
        # Lower pin constrained
        lx, ly = cfg.lower_hole_center
        ax.annotate("Pinned ($u_x = u_y = 0$)", xy=(lx, ly - cfg.lower_hole_radius), xytext=(lx, ly - cfg.lower_hole_radius - 8.0),
                    ha='center', va='top', fontsize=9, fontweight='bold', color='#2B8A3E',
                    arrowprops=dict(arrowstyle="->", color='#2B8A3E', lw=1.5))
        # Upper pin pulled
        ux, uy = cfg.upper_hole_center
        ax.annotate(r"Guided Tensile Pull ($u_y = \Delta u$)", xy=(ux, uy + cfg.upper_hole_radius),
                    xytext=(ux, uy + cfg.upper_hole_radius + 8.0),
                    ha='center', va='bottom', fontsize=9, fontweight='bold', color='#E03131',
                    arrowprops=dict(arrowstyle="->", color='#E03131', lw=1.5))
    else:
        # Bottom edge rollers + pin
        ax.annotate(r"Bottom Roller ($u_y = 0$)", xy=(W/2.0, 0), xytext=(W/2.0, -0.08 * H),
                    ha='center', va='top', fontsize=9, fontweight='bold', color='#2B8A3E',
                    arrowprops=dict(arrowstyle="->", color='#2B8A3E', lw=1.5))
        ax.plot(0, 0, '^', markersize=10, color='#2B8A3E')
        ax.text(0, -0.05 * H, "Pin ($u_x=0$)", ha='center', va='top', fontsize=8, color='#2B8A3E')
        # Top edge pull
        ax.annotate(r"Tensile Pull ($u_y = \Delta u$)", xy=(W/2.0, H), xytext=(W/2.0, 1.08 * H),
                    ha='center', va='bottom', fontsize=9, fontweight='bold', color='#E03131',
                    arrowprops=dict(arrowstyle="->", color='#E03131', lw=1.5))
        for x_arr in np.linspace(0.1*W, 0.9*W, 5):
            ax.annotate("", xy=(x_arr, H + 0.05*H), xytext=(x_arr, H),
                        arrowprops=dict(arrowstyle="->", color='#E03131', lw=1.5))

    # Overall dimension annotations
    ax.text(W / 2.0, -0.15 * H if H > 10 else -0.16 * H, r"Width $W = %.1f\,\mathrm{%s}$" % (W, unit),
            ha='center', va='top', fontsize=11, fontweight='bold')
    ax.text(-0.12 * W, H / 2.0, r"Height $H = %.1f\,\mathrm{%s}$" % (H, unit),
            ha='center', va='center', rotation=90, fontsize=11, fontweight='bold')

    # Information box
    info_text = (
        "Benchmark: %s\n"
        "Loading Type: %s\n"
        "Material: E = %.0f GPa, $\\nu$ = %.2f\n"
        "Fracture: $G_c$ = %.4f kN/mm, $\\ell_0$ = %.4f mm"
    ) % (m_info["short_name"], cfg.loading_type, cfg.E / 1000.0, cfg.nu, cfg.Gc, cfg.l0)
    ax.text(0.04 * W, 0.96 * H, info_text, transform=ax.transData, fontsize=8.5,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.9, edgecolor='#CED4DA'))

    margin_x = 0.20 * W
    margin_y = 0.20 * H
    ax.set_xlim(-margin_x, W + margin_x)
    ax.set_ylim(-margin_y, H + margin_y)
    ax.set_aspect('equal')
    ax.set_xlabel(r"$x\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_ylabel(r"$y\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_title("Geometry and Boundary Conditions\n%s" % m_info["title"], fontsize=12, fontweight='bold', pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)

    save_fig(fig, "fig_%s_1_geometry" % m_info["id"])


# ==============================================================================
# FIGURE 2 & 4: MESH WIREFRAMES (COARSE & ADAPTED)
# ==============================================================================
def plot_mesh_wireframe(inp_path, title, base_name, m_info, zoom_box=None):
    nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    total_elems = len(quad_elems) + len(tri_elems)
    unit = m_info["scale_unit"]

    fig, ax = plt.subplots(figsize=(6.5, 7.5), dpi=300)
    
    verts = []
    for conn in quad_elems.values():
        verts.append([nodes[nid] for nid in conn])
    for conn in tri_elems.values():
        verts.append([nodes[nid] for nid in conn])

    poly = PolyCollection(verts, edgecolors='#343A40', facecolors='#F1F3F5', linewidths=0.35, alpha=0.9)
    ax.add_collection(poly)

    all_x = [n[0] for n in nodes.values()]
    all_y = [n[1] for n in nodes.values()]
    ax.set_xlim(min(all_x) - 0.05 * (max(all_x) - min(all_x)), max(all_x) + 0.05 * (max(all_x) - min(all_x)))
    ax.set_ylim(min(all_y) - 0.05 * (max(all_y) - min(all_y)), max(all_y) + 0.05 * (max(all_y) - min(all_y)))
    ax.set_aspect('equal')

    # Inset zoom box outline if requested
    if zoom_box:
        zx1, zx2, zy1, zy2 = zoom_box
        rect = patches.Rectangle((zx1, zy1), zx2 - zx1, zy2 - zy1,
                                 fill=False, edgecolor='#E03131', linewidth=1.8, linestyle='--')
        ax.add_patch(rect)
        ax.text(zx1 + 0.02*(zx2-zx1), zy2 - 0.05*(zy2-zy1), "Zoom Region", color='#E03131', fontsize=8, fontweight='bold')

    ax.set_xlabel(r"$x\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_ylabel(r"$y\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_title("%s\nPhysical Elements: %d (Quads: %d, Tris: %d, Nodes: %d)" % (
        title, total_elems, len(quad_elems), len(tri_elems), len(nodes)
    ), fontsize=11, fontweight='bold', pad=10)
    ax.grid(True, linestyle=':', alpha=0.4)

    save_fig(fig, base_name)


# ==============================================================================
# FIGURE 3: COARSE AUTHENTIC MISESERI CONTOUR
# ==============================================================================
def plot_miseseri_contour(miseseri_json, title, base_name, m_info):
    with open(miseseri_json, "r") as f:
        data = json.load(f)

    nodes = {int(k): v for k, v in data["nodes"].items()}
    elements = {int(k): v for k, v in data["elements"].items()}
    elem_miseseri = {int(k): v for k, v in data["elem_miseseri"].items()}
    unit = m_info["scale_unit"]

    fig, ax = plt.subplots(figsize=(7.2, 7.5), dpi=300)

    verts = []
    vals = []
    for eid, conn in elements.items():
        if eid in elem_miseseri:
            verts.append([nodes[nid] for nid in conn])
            vals.append(elem_miseseri[eid])

    vals = np.array(vals)
    v_min = max(float(np.percentile(vals, 2)), 1e-6)
    v_max = float(np.percentile(vals, 99.5))
    if v_max <= v_min:
        v_max = max(vals)

    poly = PolyCollection(verts, array=vals, cmap='viridis', norm=LogNorm(vmin=v_min, vmax=v_max),
                          edgecolors='none', linewidths=0.0)
    ax.add_collection(poly)

    all_x = [n[0] for n in nodes.values()]
    all_y = [n[1] for n in nodes.values()]
    ax.set_xlim(min(all_x) - 0.05 * (max(all_x) - min(all_x)), max(all_x) + 0.05 * (max(all_x) - min(all_x)))
    ax.set_ylim(min(all_y) - 0.05 * (max(all_y) - min(all_y)), max(all_y) + 0.05 * (max(all_y) - min(all_y)))
    ax.set_aspect('equal')

    cbar = fig.colorbar(poly, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label(r"Authentic $\mathrm{MISESERI}$ Error Indicator $[\mathrm{MPa}]$", fontsize=10, fontweight='bold')

    ax.set_xlabel(r"$x\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_ylabel(r"$y\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_title("%s\nAuthentic Coarse Error Field ($\min=%.2e, \max=%.2e\,\mathrm{MPa}$)" % (
        title, float(np.min(vals)), float(np.max(vals))
    ), fontsize=11, fontweight='bold', pad=10)
    ax.grid(True, linestyle=':', alpha=0.4)

    save_fig(fig, base_name)


# ==============================================================================
# FIGURE 5: HIGH-RESOLUTION ZOOM VIEWS
# ==============================================================================
def plot_zoom_view(inp_path, title, base_name, m_info, zoom_box):
    nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(inp_path)
    unit = m_info["scale_unit"]
    zx1, zx2, zy1, zy2 = zoom_box

    fig, ax = plt.subplots(figsize=(6.5, 6.0), dpi=300)

    # Filter elements that intersect the zoom bbox
    verts = []
    for conn in list(quad_elems.values()) + list(tri_elems.values()):
        pts = [nodes[nid] for nid in conn]
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        if max(xs) >= zx1 and min(xs) <= zx2 and max(ys) >= zy1 and min(ys) <= zy2:
            verts.append(pts)

    poly = PolyCollection(verts, edgecolors='#1864AB', facecolors='#E7F5FF', linewidths=0.55, alpha=0.95)
    ax.add_collection(poly)

    ax.set_xlim(zx1, zx2)
    ax.set_ylim(zy1, zy2)
    ax.set_aspect('equal')

    ax.set_xlabel(r"$x\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_ylabel(r"$y\,[\mathrm{%s}]$" % unit, fontsize=11)
    ax.set_title("Close-up Detail: Ligament / Notch Root Mesh\n%s" % title, fontsize=11, fontweight='bold', pad=10)
    ax.grid(True, linestyle=':', alpha=0.5)

    save_fig(fig, base_name)


# ==============================================================================
# FIGURE 6: ELEMENT-SIZE DISTRIBUTION
# ==============================================================================
def plot_size_distribution(audit_json, title, base_name, m_info, cfg):
    with open(audit_json, "r") as f:
        audit = json.load(f)

    # Parse physical inp to re-extract exact distribution arrays
    nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(m_info["adapt_inp"])
    adapter = get_geometry_adapter(cfg)

    h_area_pz = []
    h_area_ff = []
    for conn in list(quad_elems.values()) + list(tri_elems.values()):
        pts = [nodes[nid] for nid in conn]
        if len(pts) == 4:
            area = 0.5 * abs((pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                             (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                             (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                             (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1]))
        else:
            area = 0.5 * abs(pts[0][0]*(pts[1][1]-pts[2][1]) + pts[1][0]*(pts[2][1]-pts[0][1]) + pts[2][0]*(pts[0][1]-pts[1][1]))
        ha = math.sqrt(max(area, 1e-18))
        cx = sum(p[0] for p in pts) / float(len(pts))
        cy = sum(p[1] for p in pts) / float(len(pts))
        reg = adapter.classify_region(cx, cy)
        if reg in ("FAR_FIELD", "LOWER_SHIELDED_HOLES", "PIN_HOLE_ZONES"):
            h_area_ff.append(ha)
        else:
            h_area_pz.append(ha)

    unit = m_info["scale_unit"]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11.0, 4.8), dpi=300)

    # Histogram
    all_h = h_area_pz + h_area_ff
    bins = np.linspace(min(all_h), max(all_h), 40)
    ax1.hist(h_area_ff, bins=bins, color='#495057', alpha=0.6, label='Far Field ($N=%d$)' % len(h_area_ff), edgecolor='white')
    ax1.hist(h_area_pz, bins=bins, color='#E03131', alpha=0.85, label='Process Zone ($N=%d$)' % len(h_area_pz), edgecolor='white')
    
    # Vertical line for l0 and l0/2
    ax1.axvline(cfg.l0, color='#1864AB', linestyle='--', linewidth=1.5, label=r'$\ell_0 = %.4f\,\mathrm{%s}$' % (cfg.l0, unit))
    ax1.axvline(0.5 * cfg.l0, color='#2B8A3E', linestyle=':', linewidth=1.5, label=r'$\ell_0/2 = %.4f\,\mathrm{%s}$' % (0.5 * cfg.l0, unit))

    ax1.set_xlabel(r"Element Characteristic Size $h_{\mathrm{area}} = \sqrt{\mathrm{Area}}\,[\mathrm{%s}]$" % unit, fontsize=10)
    ax1.set_ylabel("Element Count", fontsize=10)
    ax1.set_title("Element Size Histogram by Zone", fontsize=11, fontweight='bold')
    ax1.legend(fontsize=8.5, loc='upper right')
    ax1.grid(True, linestyle=':', alpha=0.5)

    # Cumulative Distribution Function (CDF)
    h_pz_sorted = np.sort(h_area_pz)
    h_ff_sorted = np.sort(h_area_ff)
    cdf_pz = np.arange(1, len(h_pz_sorted) + 1) / float(len(h_pz_sorted))
    cdf_ff = np.arange(1, len(h_ff_sorted) + 1) / float(len(h_ff_sorted))

    ax2.plot(h_pz_sorted, cdf_pz, color='#E03131', linewidth=2.2, label='Process Zone CDF')
    ax2.plot(h_ff_sorted, cdf_ff, color='#495057', linewidth=2.0, linestyle='--', label='Far Field CDF')
    ax2.axvline(cfg.l0, color='#1864AB', linestyle='--', linewidth=1.2, label=r'$\ell_0$')
    ax2.axvline(0.5 * cfg.l0, color='#2B8A3E', linestyle=':', linewidth=1.2, label=r'$\ell_0/2$')

    ax2.set_xlabel(r"Element Size $h_{\mathrm{area}}\,[\mathrm{%s}]$" % unit, fontsize=10)
    ax2.set_ylabel("Cumulative Fraction", fontsize=10)
    ax2.set_title("Cumulative Size Distribution", fontsize=11, fontweight='bold')
    ax2.legend(fontsize=8.5, loc='lower right')
    ax2.grid(True, linestyle=':', alpha=0.5)

    fig.suptitle("Element Resolution & Spatial Selectivity Audit\n%s" % title, fontsize=12, fontweight='bold', y=1.02)
    plt.tight_layout()

    save_fig(fig, base_name)


# ==============================================================================
# FIGURE 7: 3-MODEL SIDE-BY-SIDE COMPARATIVE FIGURE
# ==============================================================================
def plot_three_model_comparison():
    fig, axes = plt.subplots(3, 3, figsize=(15.0, 15.0), dpi=300)

    for col, m_info in enumerate(MODELS):
        cfg = AdaptiveConfig.from_json(m_info["config_path"])
        unit = m_info["scale_unit"]

        # Row 1: Geometry diagram
        ax1 = axes[0, col]
        W, H = cfg.plate_w, cfg.plate_h
        outer_rect = patches.Rectangle((0, 0), W, H, fill=True, facecolor="#F8F9FA", edgecolor="#212529", linewidth=1.8)
        ax1.add_patch(outer_rect)
        if cfg.notch_a is not None:
            nw = cfg.notch_w
            notch_rect = patches.Rectangle((0, cfg.notch_y - nw), cfg.notch_a, 2.0 * nw,
                                           fill=True, facecolor="white", edgecolor="#C92A2A", linewidth=1.5, linestyle="--")
            ax1.add_patch(notch_rect)
        adapter = get_geometry_adapter(cfg)
        for h in adapter.get_hole_definitions():
            circ = patches.Circle((h[0], h[1]), h[2], fill=True, facecolor="white", edgecolor="#1864AB", linewidth=1.5)
            ax1.add_patch(circ)
        ax1.set_xlim(-0.15*W, 1.15*W)
        ax1.set_ylim(-0.15*H, 1.15*H)
        ax1.set_aspect('equal')
        ax1.set_title("%s\nGeometry ($W \\times H = %.1f \\times %.1f\,\mathrm{%s}$)" % (
            m_info["short_name"], W, H, unit
        ), fontsize=10, fontweight='bold')
        ax1.grid(True, linestyle=':', alpha=0.4)

        # Row 2: Coarse MISESERI contour
        ax2 = axes[1, col]
        with open(m_info["miseseri_json"], "r") as f:
            m_data = json.load(f)
        m_nodes = {int(k): v for k, v in m_data["nodes"].items()}
        m_elems = {int(k): v for k, v in m_data["elements"].items()}
        m_vals_dict = {int(k): v for k, v in m_data["elem_miseseri"].items()}
        verts = [[m_nodes[nid] for nid in conn] for eid, conn in m_elems.items() if eid in m_vals_dict]
        vals = np.array([m_vals_dict[eid] for eid in m_elems.keys() if eid in m_vals_dict])
        v_min = max(float(np.percentile(vals, 2)), 1e-6)
        v_max = float(np.percentile(vals, 99.5))
        poly2 = PolyCollection(verts, array=vals, cmap='viridis', norm=LogNorm(vmin=v_min, vmax=v_max),
                               edgecolors='none', linewidths=0.0)
        ax2.add_collection(poly2)
        ax2.set_xlim(-0.05*W, 1.05*W)
        ax2.set_ylim(-0.05*H, 1.05*H)
        ax2.set_aspect('equal')
        cbar = fig.colorbar(poly2, ax=ax2, fraction=0.046, pad=0.04)
        cbar.set_label("MISESERI [MPa]", fontsize=8)
        ax2.set_title("Coarse MISESERI Field\n($\max = %.2e\,\mathrm{MPa}$)" % float(np.max(vals)),
                      fontsize=10, fontweight='bold')
        ax2.grid(True, linestyle=':', alpha=0.4)

        # Row 3: Adapted Physical Mesh
        ax3 = axes[2, col]
        a_nodes, a_quads, a_tris = MeshQualityAuditEngine.parse_physical_inp(m_info["adapt_inp"])
        a_verts = [[a_nodes[nid] for nid in conn] for conn in list(a_quads.values()) + list(a_tris.values())]
        poly3 = PolyCollection(a_verts, edgecolors='#343A40', facecolors='#F1F3F5', linewidths=0.25, alpha=0.9)
        ax3.add_collection(poly3)
        ax3.set_xlim(-0.05*W, 1.05*W)
        ax3.set_ylim(-0.05*H, 1.05*H)
        ax3.set_aspect('equal')
        ax3.set_title("Adapted Physical Mesh\n($N = %d$ elements)" % (len(a_quads) + len(a_tris)),
                      fontsize=10, fontweight='bold')
        ax3.grid(True, linestyle=':', alpha=0.4)

    plt.tight_layout()
    save_fig(fig, "fig_f1727_three_model_comparison")


def main():
    print("=================================================================")
    print("TASK F1727: GENERATING PUBLICATION-QUALITY FIGURES")
    print("=================================================================")

    for m_info in MODELS:
        print("\n--- Generating Figures for %s ---" % m_info["short_name"])
        cfg = AdaptiveConfig.from_json(m_info["config_path"])

        # 1. Geometry diagram
        plot_geometry_diagram(cfg, m_info)

        # 2. Coarse mesh
        plot_mesh_wireframe(m_info["coarse_inp"], "Coarse Physical Mesh: %s" % m_info["short_name"],
                            "fig_%s_2_coarse_mesh" % m_info["id"], m_info)

        # 3. Coarse MISESERI contour
        plot_miseseri_contour(m_info["miseseri_json"], "Coarse MISESERI Field: %s" % m_info["short_name"],
                              "fig_%s_3_miseseri" % m_info["id"], m_info)

        # 4. Final adapted physical mesh
        plot_mesh_wireframe(m_info["adapt_inp"], "Final Adapted Physical Mesh: %s" % m_info["short_name"],
                            "fig_%s_4_adapted_mesh" % m_info["id"], m_info, zoom_box=m_info["zoom_bbox"])

        # 5. Zoom views
        plot_zoom_view(m_info["adapt_inp"], m_info["short_name"],
                       "fig_%s_5_zoom" % m_info["id"], m_info, m_info["zoom_bbox"])

        # 6. Element-size distribution
        plot_size_distribution(m_info["audit_json"], m_info["short_name"],
                               "fig_%s_6_size_distribution" % m_info["id"], m_info, cfg)

    # 7. Multi-model comparative figure
    print("\n--- Generating 3-Model Comparative Synthesis Figure ---")
    plot_three_model_comparison()

    print("\nAll figures generated and copied to both local and thesis report folders successfully!")

if __name__ == "__main__":
    main()
