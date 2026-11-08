#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_f1688_sec43_adapted_mesh.py

Plots adapted physical mesh wireframe for Pandey-Kumar Section 4.3 (65 x 120 mm).
Compares directly against Paper Figure 16b.
"""

import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from matplotlib.collections import PatchCollection
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
adapt_inp = model_dir / "PK_SEC43_METHOD_A_ADAPT_PHYS.inp"
fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"

def main():
    print("=" * 80)
    print("TASK F1688: PLOTTING ADAPTED PHYSICAL MESH (COMPARING TO FIG. 16B)")
    print("=" * 80)

    # Parse adapted INP
    nodes = {}
    elems = {}
    active_sec = None
    
    with open(adapt_inp, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                upline = line.upper()
                if upline.startswith("*NODE"):
                    active_sec = "NODE"
                elif upline.startswith("*ELEMENT") and not upline.startswith("*ELEMENT OUTPUT"):
                    active_sec = "ELEMENT"
                else:
                    active_sec = None
                continue
            if active_sec == "NODE":
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif active_sec == "ELEMENT":
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    elems[int(parts[0])] = [int(p) for p in parts[1:]]

    print(f"Loaded adapted mesh: {len(nodes)} nodes, {len(elems)} elements.")

    patches = []
    h_vals = []
    
    for eid, conn in elems.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) < 3:
            continue
        poly_pts = np.array(pts)
        x = poly_pts[:, 0]
        y = poly_pts[:, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        h_eq = np.sqrt(area)
        
        patches.append(MplPolygon(poly_pts, closed=True))
        h_vals.append(h_eq)

    fig, ax = plt.subplots(figsize=(6, 10))
    p = PatchCollection(patches, cmap='viridis_r', edgecolors='black', linewidths=0.15)
    p.set_array(np.array(h_vals))
    p.set_clim(0.10, 1.50)
    ax.add_collection(p)

    ax.set_xlim(0, 65)
    ax.set_ylim(0, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontsize=11)
    ax.set_ylabel('Y [mm]', fontsize=11)
    ax.set_title('Task F1688: Pandey-Kumar §4.3 Adapted Mesh (9,432 Elements)\n(One-Rule Method A: errorTarget=5%, min=0.143mm, max=1.5mm)', fontsize=11)

    cb = fig.colorbar(p, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(r'Equivalent Element Size $h_{\mathrm{equiv}} = \sqrt{\mathrm{Area}}$ [mm]', fontsize=10)

    # Annotations
    ax.annotate('Primary Branch Refined\n(h_min = 0.090 mm)', xy=(10, 70), xytext=(18, 78),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=4),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.7))

    ax.annotate('Secondary Branch UNREFINED\n(0.0% <= l0, h_med = 0.746 mm)', xy=(55, 51), xytext=(35, 30),
                arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=5),
                fontsize=9, fontweight='bold', color='red', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.9))

    out_pdf = fig_dir / "fig_f1688_sec43_adapted_mesh.pdf"
    out_png = fig_dir / "fig_f1688_sec43_adapted_mesh.png"
    plt.tight_layout()
    plt.savefig(out_pdf, dpi=300)
    plt.savefig(out_png, dpi=300)
    plt.close()
    print(f"Saved adapted mesh plots to:\n  {out_pdf}\n  {out_png}")

if __name__ == "__main__":
    main()
