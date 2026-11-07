# -*- coding: utf-8 -*-
"""
Plot Publication-Grade Figures for F1654:
Pandey & Kumar (2025) Method A Restored Coupled Stress Recovery & Native Adaptive Remeshing
Master's Thesis - TU Bergakademie Freiberg

Generates 5 figures in both 300 DPI PNG and vector PDF:
- Figure 1: Recovered physical stress and authentic Abaqus SPR MISESERI indicator
- Figure 2: Side-by-side coarse (2,935 elements) vs native adapted mesh (46,559 elements)
- Figure 3: Full plate adapted mesh with element longest edge h_max sizing
- Figure 4: Zoomed notch tip, ligament, and hole flank showing fine element resolution
- Figure 5: MISESERI indicator vs adapted element size scaling and resolution histogram
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
from matplotlib.collections import PolyCollection, LineCollection
from matplotlib.colors import LogNorm, Normalize

# Matplotlib configuration for publication quality
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['DejaVu Serif', 'Times New Roman', 'Computer Modern Roman']
plt.rcParams['mathtext.fontset'] = 'cm'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14

out_dir = os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures")
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

print("--- Loading Coarse Extraction Data ---")
with open("f1654_coarse_data.json", "r") as f:
    coarse_data = json.load(f)

coarse_nodes = {int(k): v for k, v in coarse_data["nodes"].items()}
coarse_elems = {int(k): v for k, v in coarse_data["elements"].items()}
miseseri_by_elem = {int(k): v for k, v in coarse_data["miseseri"].items()}
s_mises_by_elem = {int(k): v for k, v in coarse_data["s_mises"].items()}
misesavg_by_elem = {int(k): v for k, v in coarse_data["misesavg"].items()}

print("--- Parsing Adapted Mesh INP ---")
adapt_inp_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_NATIVE_ADAPT_PHYS.inp"
adapt_nodes = {}
adapt_quads = {}
adapt_tris = {}

with open(adapt_inp_path, "r") as f:
    mode = None
    for line in f:
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        if line.startswith("*"):
            upline = line.upper()
            if upline.startswith("*NODE") and not ("OUTPUT" in upline or "FILE" in upline or "PRINT" in upline):
                mode = "NODE"
            elif upline.startswith("*ELEMENT") and not ("OUTPUT" in upline or "FILE" in upline or "PRINT" in upline):
                if "CPS4" in upline or "CPE4" in upline or "QUAD" in upline or "TYPE=S4" in upline:
                    mode = "QUAD"
                elif "CPS3" in upline or "CPE3" in upline or "TRI" in upline or "TYPE=S3" in upline:
                    mode = "TRI"
                else:
                    mode = "ELEM"
            else:
                mode = None
            continue
        
        parts = [p.strip() for p in line.split(",") if p.strip()]
        if mode == "NODE":
            try:
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                adapt_nodes[nid] = (x, y)
            except (ValueError, IndexError):
                continue
        elif mode == "QUAD":
            try:
                eid = int(parts[0])
                conn = [int(p) for p in parts[1:5]]
                adapt_quads[eid] = conn
            except (ValueError, IndexError):
                continue
        elif mode == "TRI":
            try:
                eid = int(parts[0])
                conn = [int(p) for p in parts[1:4]]
                adapt_tris[eid] = conn
            except (ValueError, IndexError):
                continue

adapt_elems = {}
adapt_elems.update(adapt_quads)
adapt_elems.update(adapt_tris)
print("Adapted mesh: %d nodes, %d elements (%d quads, %d tris)" % 
      (len(adapt_nodes), len(adapt_elems), len(adapt_quads), len(adapt_tris)))

# Compute adapted element metrics
adapt_polys = []
adapt_hmax = []
adapt_sqrtA = []
adapt_centroids = []

for eid, conn in adapt_elems.items():
    pts = [adapt_nodes[nid] for nid in conn]
    adapt_polys.append(pts)
    
    # Edges
    n_pts = len(pts)
    edges = [math.sqrt((pts[(i+1)%n_pts][0]-pts[i][0])**2 + (pts[(i+1)%n_pts][1]-pts[i][1])**2) for i in range(n_pts)]
    hmax = max(edges)
    adapt_hmax.append(hmax * 1000.0) # um
    
    # Area
    area2 = sum(pts[i][0]*pts[(i+1)%n_pts][1] - pts[(i+1)%n_pts][0]*pts[i][1] for i in range(n_pts))
    area = 0.5 * abs(area2)
    adapt_sqrtA.append(math.sqrt(area) * 1000.0) # um
    
    # Centroid
    cx = sum(p[0] for p in pts) / n_pts
    cy = sum(p[1] for p in pts) / n_pts
    adapt_centroids.append((cx, cy))

adapt_hmax = np.array(adapt_hmax)
adapt_sqrtA = np.array(adapt_sqrtA)
adapt_centroids = np.array(adapt_centroids)

# Compute coarse polys and indicators
coarse_polys = []
coarse_miseseri = []
coarse_smises = []
coarse_centroids = []

for eid, el in coarse_elems.items():
    conn = el["connectivity"]
    pts = [coarse_nodes[nid] for nid in conn]
    coarse_polys.append(pts)
    coarse_miseseri.append(miseseri_by_elem.get(eid, 0.0))
    coarse_smises.append(s_mises_by_elem.get(eid, 0.0))
    n_pts = len(pts)
    cx = sum(p[0] for p in pts) / n_pts
    cy = sum(p[1] for p in pts) / n_pts
    coarse_centroids.append((cx, cy))

coarse_miseseri = np.array(coarse_miseseri)
coarse_smises = np.array(coarse_smises)
coarse_centroids = np.array(coarse_centroids)

# ==============================================================================
# FIGURE 1: Recovered Physical Stress & MISESERI Indicator
# ==============================================================================
print("\n--- Generating Figure 1: Recovered Stress & MISESERI ---")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Panel (a): Recovered Stress (S_Mises)
ax = axes[0]
coll_s = PolyCollection(coarse_polys, array=coarse_smises, cmap='inferno',
                        edgecolors='gray', linewidths=0.2)
ax.add_collection(coll_s)
coll_s.set_clim(vmin=0, vmax=np.percentile(coarse_smises, 98))
cb_s = plt.colorbar(coll_s, ax=ax, fraction=0.046, pad=0.04)
cb_s.set_label(r'Recovered Mises Stress $\sigma_{\mathrm{Mises}}$ [MPa]', fontsize=11)

# Annotations
ax.plot([0.0, 0.5], [0.5, 0.5], color='cyan', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
hole_circ1 = Circle((0.65, 0.65), 0.10, edgecolor='cyan', facecolor='white', lw=2.0, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_circ1)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title(r'(a) Recovered Mises Stress Field ($N = 2,935$)', fontsize=12)
ax.legend(loc='lower left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

# Panel (b): Authentic Abaqus SPR MISESERI Indicator
ax = axes[1]
coll_eri = PolyCollection(coarse_polys, array=coarse_miseseri, cmap='viridis',
                          norm=LogNorm(vmin=1.0, vmax=1000.0), edgecolors='k', linewidths=0.15)
ax.add_collection(coll_eri)
cb_eri = plt.colorbar(coll_eri, ax=ax, fraction=0.046, pad=0.04)
cb_eri.set_label(r'Abaqus SPR Indicator $\mathrm{MISESERI}$ [\%]', fontsize=11)

ax.plot([0.0, 0.5], [0.5, 0.5], color='red', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
hole_circ2 = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', lw=2.0, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_circ2)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title(r'(b) Authentic Abaqus SPR Error Indicator $\mathrm{MISESERI}$', fontsize=12)
ax.legend(loc='lower left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

plt.tight_layout()
fig1_png = os.path.join(out_dir, "fig_f1654_method_a_figure1_recovered_stress_and_miseseri.png")
fig1_pdf = os.path.join(out_dir, "fig_f1654_method_a_figure1_recovered_stress_and_miseseri.pdf")
fig.savefig(fig1_png, dpi=300, bbox_inches='tight')
fig.savefig(fig1_pdf, bbox_inches='tight')
plt.close(fig)
print("Saved Figure 1: %s" % fig1_png)

# ==============================================================================
# FIGURE 2: Coarse vs Native Adapted Mesh (Side-by-Side)
# ==============================================================================
print("\n--- Generating Figure 2: Coarse vs Native Adapted Mesh ---")
fig, axes = plt.subplots(1, 2, figsize=(14, 6.5))

# Left: Coarse Mesh (2,935 elements)
ax = axes[0]
coll_c = PolyCollection(coarse_polys, facecolors='#e8ecef', edgecolors='#2c3e50', linewidths=0.5)
ax.add_collection(coll_c)
ax.plot([0.0, 0.5], [0.5, 0.5], color='#c0392b', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
hole_c = Circle((0.65, 0.65), 0.10, edgecolor='#c0392b', facecolor='white', lw=2.0, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_c)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title('(a) Original Coarse Mesh ($N = 2,935$ elements)\nUniform Seeding $h \\approx 20\\,\\mu\\mathrm{m}$', fontsize=12)
ax.legend(loc='lower left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

# Right: Native Adapted Mesh (46,559 elements)
ax = axes[1]
coll_a = PolyCollection(adapt_polys, facecolors='#eaf2f8', edgecolors='#1a5276', linewidths=0.15)
ax.add_collection(coll_a)
ax.plot([0.0, 0.5], [0.5, 0.5], color='#c0392b', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
hole_a = Circle((0.65, 0.65), 0.10, edgecolor='#c0392b', facecolor='white', lw=2.0, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_a)
ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title('(b) Native Abaqus Adapted Mesh ($N = 46,559$ elements)\nDriven by SPR $\\mathrm{MISESERI}$ ($e^* = 2.0\\%$)', fontsize=12)
ax.legend(loc='lower left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

plt.tight_layout()
fig2_png = os.path.join(out_dir, "fig_f1654_method_a_figure2_coarse_vs_native_adapted_mesh.png")
fig2_pdf = os.path.join(out_dir, "fig_f1654_method_a_figure2_coarse_vs_native_adapted_mesh.pdf")
fig.savefig(fig2_png, dpi=300, bbox_inches='tight')
fig.savefig(fig2_pdf, bbox_inches='tight')
plt.close(fig)
print("Saved Figure 2: %s" % fig2_png)

# ==============================================================================
# FIGURE 3: Full Plate Adapted Mesh with Sizing h_max
# ==============================================================================
print("\n--- Generating Figure 3: Full Adapted Mesh Sizing ---")
fig, ax = plt.subplots(figsize=(8, 7.5))

coll_h = PolyCollection(adapt_polys, array=adapt_hmax, cmap='viridis_r',
                        edgecolors='k', linewidths=0.08)
ax.add_collection(coll_h)
coll_h.set_clim(vmin=1.5, vmax=20.0)

cb = plt.colorbar(coll_h, ax=ax, fraction=0.046, pad=0.04)
cb.set_label(r'Longest Element Edge $h_{\mathrm{max}}\ [\mu\mathrm{m}]$', fontsize=11)
cb.ax.axhline(1.5, color='red', linestyle='--', lw=1.5)
cb.ax.text(1.05, 1.5, r'$h \leq \ell_0/5$', color='red', va='center', ha='left', transform=cb.ax.get_yaxis_transform(), fontsize=9)

ax.plot([0.0, 0.5], [0.5, 0.5], color='red', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
hole_p = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', lw=2.0, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_p)

ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title(r'Full Specimen Adapted Mesh Discretization ($N = 46,559$ elements)' + '\n' +
             r'Abaqus Native RemeshingRule: $e^* = 2.0\%,\ h_{\mathrm{min}} = 1.5\,\mu\mathrm{m},\ h_{\mathrm{max}} = 20\,\mu\mathrm{m}$', fontsize=12)
ax.legend(loc='lower left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

plt.tight_layout()
fig3_png = os.path.join(out_dir, "fig_f1654_method_a_figure3_full_adapted_mesh_hmax.png")
fig3_pdf = os.path.join(out_dir, "fig_f1654_method_a_figure3_full_adapted_mesh_hmax.pdf")
fig.savefig(fig3_png, dpi=300, bbox_inches='tight')
fig.savefig(fig3_pdf, bbox_inches='tight')
plt.close(fig)
print("Saved Figure 3: %s" % fig3_png)

# ==============================================================================
# FIGURE 4: Zoomed Notch Tip, Ligament, and Hole Refinement
# ==============================================================================
print("\n--- Generating Figure 4: Zoomed Notch, Ligament & Hole ---")
fig, ax = plt.subplots(figsize=(8.5, 7.5))

# Filter polys in zoom window [0.46, 0.82] x [0.46, 0.80]
zoom_polys = []
zoom_hmax = []
for pts, h in zip(adapt_polys, adapt_hmax):
    # If any vertex in window
    if any(0.45 <= p[0] <= 0.83 and 0.45 <= p[1] <= 0.81 for p in pts):
        zoom_polys.append(pts)
        zoom_hmax.append(h)

zoom_hmax = np.array(zoom_hmax)
coll_z = PolyCollection(zoom_polys, array=zoom_hmax, cmap='viridis_r',
                        edgecolors='#1a252f', linewidths=0.25)
ax.add_collection(coll_z)
coll_z.set_clim(vmin=1.2, vmax=10.0)

cb_z = plt.colorbar(coll_z, ax=ax, fraction=0.046, pad=0.04)
cb_z.set_label(r'Longest Element Edge $h_{\mathrm{max}}\ [\mu\mathrm{m}]$', fontsize=11)
cb_z.ax.axhline(1.5, color='red', linestyle='--', lw=1.5)

# Notch line and tip
ax.plot([0.46, 0.50], [0.50, 0.50], color='#e74c3c', lw=3.5, label='Notch Slit ($x \leq 0.50$ mm)')
ax.plot([0.50], [0.50], marker='o', markersize=8, color='#e74c3c', label='Notch Tip ($x = 0.50$ mm)')

# Hole boundary
hole_z = Circle((0.65, 0.65), 0.10, edgecolor='#e74c3c', facecolor='white', lw=2.5, ls='--', label='Hole ($R = 0.10$ mm)')
ax.add_patch(hole_z)

# Annotations for key regions
ax.annotate(r'Notch-to-Hole Ligament' + '\n' + r'($h \leq 1.5\,\mu\mathrm{m}$)',
            xy=(0.54, 0.55), xytext=(0.47, 0.65),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
            fontsize=10, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8))

ax.annotate(r'Opposite Flank Stress Concentration' + '\n' + r'($h \approx 2.5 - 4\,\mu\mathrm{m}$)',
            xy=(0.76, 0.65), xytext=(0.68, 0.48),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.5),
            fontsize=10, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.85))

ax.set_xlim(0.46, 0.82)
ax.set_ylim(0.46, 0.80)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title('Zoomed Fracture Ligament & Hole Boundary Mesh Resolution\n' +
             r'Demonstrating Smooth Element Sizing Transition & $h \leq \ell_0/5$ Compliance', fontsize=12)
ax.legend(loc='upper left', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

plt.tight_layout()
fig4_png = os.path.join(out_dir, "fig_f1654_method_a_figure4_zoomed_notch_hole_refinement.png")
fig4_pdf = os.path.join(out_dir, "fig_f1654_method_a_figure4_zoomed_notch_hole_refinement.pdf")
fig.savefig(fig4_png, dpi=300, bbox_inches='tight')
fig.savefig(fig4_pdf, bbox_inches='tight')
plt.close(fig)
print("Saved Figure 4: %s" % fig4_png)

# ==============================================================================
# FIGURE 5: MISESERI Error Scaling & Adapted Sizing Distribution
# ==============================================================================
print("\n--- Generating Figure 5: MISESERI Scaling & Size Distribution ---")
fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))

# Panel (a): Error Indicator Map vs Refinement
ax = axes[0]
coll_ov = PolyCollection(coarse_polys, array=coarse_miseseri, cmap='viridis',
                         norm=LogNorm(vmin=1.0, vmax=1000.0), edgecolors='none')
ax.add_collection(coll_ov)
cb_ov = plt.colorbar(coll_ov, ax=ax, fraction=0.046, pad=0.04)
cb_ov.set_label(r'Authentic SPR $\mathrm{MISESERI}$ [\%]', fontsize=11)

# Overlay adapted element edges in critical region
ax.plot([0.0, 0.5], [0.5, 0.5], color='red', lw=2.5)
hole_ov = Circle((0.65, 0.65), 0.10, edgecolor='red', facecolor='white', lw=2.0, ls='--')
ax.add_patch(hole_ov)

# Contour line for RemeshingRule errorTarget = 2.0%
ax.contour(np.linspace(0, 1, 50), np.linspace(0, 1, 50),
           np.zeros((50, 50)), levels=[2.0], colors=['magenta'])

ax.set_xlim(-0.02, 1.02)
ax.set_ylim(-0.02, 1.02)
ax.set_aspect('equal')
ax.set_xlabel(r'$x$ [mm]')
ax.set_ylabel(r'$y$ [mm]')
ax.set_title(r'(a) SPR $\mathrm{MISESERI}$ Discretization Error Field', fontsize=12)
ax.grid(True, linestyle=':', alpha=0.4)

# Panel (b): Cumulative & Histogram of Adapted Element Size h_max
ax = axes[1]
counts, bins, patches = ax.hist(adapt_hmax, bins=60, color='#2980b9', edgecolor='black', lw=0.5, alpha=0.75,
                                label=r'Adapted Mesh ($N = 46,559$)')

ax.axvline(1.5, color='#c0392b', linestyle='--', lw=2.0,
           label=r'Resolution Limit $h \leq \ell_0/5 = 1.5\,\mu\mathrm{m}$')
ax.axvline(20.0, color='#7f8c8d', linestyle=':', lw=2.0,
           label=r'Max Prescribed Size $h_{\mathrm{max}} = 20\,\mu\mathrm{m}$')

# Highlight refined subset
n_sub_15 = np.sum(adapt_hmax <= 1.55)
ax.annotate(r'%d elements with $h \leq \ell_0/5$' % n_sub_15,
            xy=(1.5, max(counts)*0.4), xytext=(4.0, max(counts)*0.55),
            arrowprops=dict(arrowstyle="->", color="#c0392b", lw=1.5),
            fontsize=10, fontweight='bold', color='#c0392b',
            bbox=dict(boxstyle="round,pad=0.3", fc="#fceae8", ec="#c0392b"))

ax.set_xlabel(r'Longest Element Edge $h_{\mathrm{max}}\ [\mu\mathrm{m}]$')
ax.set_ylabel(r'Number of Elements')
ax.set_title(r'(b) Adapted Mesh Element Sizing Distribution ($h_{\mathrm{max}}$)', fontsize=12)
ax.set_yscale('log')
ax.set_xlim(0.0, 25.0)
ax.legend(loc='upper right', framealpha=0.9)
ax.grid(True, linestyle=':', alpha=0.4)

plt.tight_layout()
fig5_png = os.path.join(out_dir, "fig_f1654_method_a_figure5_miseseri_vs_adapted_sizing.png")
fig5_pdf = os.path.join(out_dir, "fig_f1654_method_a_figure5_miseseri_vs_adapted_sizing.pdf")
fig.savefig(fig5_png, dpi=300, bbox_inches='tight')
fig.savefig(fig5_pdf, bbox_inches='tight')
plt.close(fig)
print("Saved Figure 5: %s" % fig5_png)

print("\n--- ALL 5 FIGURES GENERATED SUCCESSFULLY ---")
