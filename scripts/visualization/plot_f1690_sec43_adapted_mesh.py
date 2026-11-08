#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_f1690_sec43_adapted_mesh.py

Task F1690: Plots adapted physical mesh wireframe for Pandey-Kumar Section 4.3 (65 x 120 mm)
generated from the finer coarse donor mesh (30,686 elements).
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
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "190_pk_sec43_job1_rerun"
adapt_inp = model_dir / "PK_SEC43_RERUN_ADAPT_PHYS.inp"
fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"

def main():
    print("=" * 80)
    print("TASK F1690: PLOTTING ADAPTED PHYSICAL MESH (COMPARING TO FIG. 16B)")
    print("=" * 80)

    nodes = {}
    elems = {}
    active_sec = None
    
    with open(str(adapt_inp), "r") as fp:
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

    print("Loaded adapted mesh: %d nodes, %d elements." % (len(nodes), len(elems)))

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
    p = PatchCollection(patches, cmap='viridis_r', edgecolors='black', linewidths=0.08)
    p.set_array(np.array(h_vals))
    p.set_clim(0.10, 0.70)
    ax.add_collection(p)

    ax.set_xlim(0, 65)
    ax.set_ylim(0, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontsize=11)
    ax.set_ylabel('Y [mm]', fontsize=11)
    ax.set_title('Task F1690: Pandey-Kumar §4.3 Adapted Mesh (30,686 Elements)\n(One-Rule Method A: errorTarget=5%, min=0.143mm, max=1.5mm, h_donor=0.60mm)', fontsize=10)

    cb = fig.colorbar(p, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(r'Equivalent Element Size $h_{\mathrm{equiv}} = \sqrt{\mathrm{Area}}$ [mm]', fontsize=10)

    # Annotations
    ax.annotate('Primary Branch Refined\n(h_min = 0.065 mm <= l0/4)', xy=(10, 70), xytext=(18, 78),
                arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=4),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.8))

    ax.annotate('Secondary Branch UNREFINED\n(0.0% <= l0/2, h_med = 0.510 mm)', xy=(55, 51), xytext=(28, 32),
                arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=5),
                fontsize=9, fontweight='bold', color='red', bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="red", alpha=0.9))

    out_pdf = fig_dir / "fig_f1690_sec43_adapted_mesh.pdf"
    out_png = fig_dir / "fig_f1690_sec43_adapted_mesh.png"
    plt.tight_layout()
    plt.savefig(str(out_pdf), dpi=300)
    plt.savefig(str(out_png), dpi=300)
    plt.close()
    print("Saved adapted mesh plots to:\n  %s\n  %s" % (out_pdf, out_png))

if __name__ == "__main__":
    main()
