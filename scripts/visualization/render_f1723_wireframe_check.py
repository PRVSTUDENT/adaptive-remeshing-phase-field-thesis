# -*- coding: utf-8 -*-
"""
scripts/visualization/render_f1723_wireframe_check.py
=====================================================
Render high-resolution wireframe of PK_F1720_ADAPTED_PHYS.inp alongside Fig 23(b)
and plot detailed zooms into all 4 ligaments.
"""
import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from PIL import Image

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PHYS.inp")
FIG23B_PATH = os.path.join(REPO_ROOT, "references", "derived", "pandey_kumar_2025_figures", "fig23b_panel_1.png")
OUT_DIR = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# Parse mesh
nodes = {}
elements = []

with open(INP_PATH, "r") as f:
    reading_nodes = False
    reading_elems = False
    for line in f:
        line = line.strip()
        if not line or line.startswith("**"):
            continue
        u = line.upper()
        if u.startswith("*NODE"):
            reading_nodes = True
            reading_elems = False
            continue
        elif u.startswith("*ELEMENT") and "OUTPUT" not in u and ("TYPE" in u or "," in u):
            reading_nodes = False
            reading_elems = True
            continue
        elif u.startswith("*"):
            reading_nodes = False
            reading_elems = False
            continue

        if reading_nodes:
            parts = line.split(",")
            nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
        elif reading_elems:
            parts = line.split(",")
            elements.append((int(parts[0]), [int(p) for p in parts[1:]]))

polys = []
elem_sizes = []
for eid, conn in elements:
    pts = [nodes[n] for n in conn]
    polys.append(pts)
    n_pts = len(pts)
    poly_x = [p[0] for p in pts]
    poly_y = [p[1] for p in pts]
    area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
    elem_sizes.append(math.sqrt(area))

print("Parsed %d nodes, %d elements. Sizing range: %.4f to %.4f mm" %
      (len(nodes), len(elements), min(elem_sizes), max(elem_sizes)))

# Figure 1: Full-domain side-by-side comparison
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))

# Panel 1: Published Fig 23(b)
if os.path.exists(FIG23B_PATH):
    img = Image.open(FIG23B_PATH)
    ax1.imshow(img)
    ax1.axis("off")
    ax1.set_title("(a) Published Pandey & Kumar (2025) Fig. 23(b)\nBenchmark Discretization: 12,944 Elements",
                  fontsize=12, fontweight="bold", pad=10)

# Panel 2: F1720 Wireframe
pc = PolyCollection(polys, facecolors="white", edgecolors="#0f172a", linewidths=0.25, zorder=2)
ax2.add_collection(pc)
ax2.set_xlim(-0.02, 1.02)
ax2.set_ylim(-0.02, 1.02)
ax2.set_aspect("equal")
ax2.set_title("(b) Baseline F1720 Native Adapted Mesh\n13,163 Elements (+1.69% Parity vs 12,944)",
              fontsize=12, fontweight="bold", pad=10)
ax2.set_xlabel("X [mm]", fontsize=11)
ax2.set_ylabel("Y [mm]", fontsize=11)
ax2.grid(True, linestyle=":", alpha=0.3)

out_fig1 = os.path.join(OUT_DIR, "f1723_fig23b_vs_f1720_side_by_side.png")
fig.tight_layout()
fig.savefig(out_fig1, dpi=300)
plt.close(fig)
print("Saved %s" % out_fig1)

# Figure 2: Detailed 4-ligament zoom comparison
fig, axes = plt.subplots(2, 2, figsize=(16, 14))

# Zooms
zooms = [
    ("Zoom A: Ligament 1 ($h_1 \\leftrightarrow h_2$, Clearance $158.1\\,\\mu\\mathrm{m}$)",
     0.05, 0.38, 0.38, 0.58, axes[0, 0]),
    ("Zoom B: Ligament 2 ($h_2 \\leftrightarrow h_3$, Clearance $141.4\\,\\mu\\mathrm{m}$)",
     0.38, 0.62, 0.38, 0.62, axes[0, 1]),
    ("Zoom C: Ligament 3 ($h_3 \\leftrightarrow h_4$, Clearance $33.1\\,\\mu\\mathrm{m}$ - Narrowest)",
     0.58, 0.78, 0.46, 0.58, axes[1, 0]),
    ("Zoom D: Ligament 4 ($h_4 \\leftrightarrow h_5$, Clearance $111.8\\,\\mu\\mathrm{m}$)",
     0.72, 1.00, 0.38, 0.56, axes[1, 1]),
]

for title, xmin, xmax, ymin, ymax, ax in zooms:
    pc_zoom = PolyCollection(polys, facecolors="white", edgecolors="#1e293b", linewidths=0.4, zorder=2)
    ax.add_collection(pc_zoom)
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.set_xlabel("X [mm]", fontsize=10)
    ax.set_ylabel("Y [mm]", fontsize=10)
    ax.grid(True, linestyle=":", alpha=0.4)

fig.suptitle("Task F1723: Baseline F1720 Mesh (13,163 Elements) — 4-Ligament Inter-Hole Resolution Audit",
             fontsize=14, fontweight="bold", y=0.98)
out_fig2 = os.path.join(OUT_DIR, "f1723_four_ligament_zooms_f1720.png")
fig.tight_layout()
fig.savefig(out_fig2, dpi=300)
plt.close(fig)
print("Saved %s" % out_fig2)
