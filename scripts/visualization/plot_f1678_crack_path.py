# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1678_crack_path.py
=============================================
Visualizes the authentic crack propagation trajectory for M1_HOLE_F1664_METHOD_A_PROD
(20,213 physical elements, Job 1421142.mmaster02).

Demonstrates:
1. Primary crack deflection from initial notch (0.50, 0.50) into off-axis hole.
2. Crack arrest at circular hole boundary (xc=0.65, yc=0.65, r=0.10).
3. Secondary crack initiation on right hole flank and propagation to right edge (x=1.00).
"""
import os
import sys
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
import numpy as np

def plot_crack_path(crack_csv_path, out_paths):
    elements = []
    with open(crack_csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            elements.append({
                'id': int(r['phys_elem_id']),
                'x': float(r['x']),
                'y': float(r['y']),
                'd': float(r['damage'])
            })

    fig, ax = plt.subplots(figsize=(8, 8))

    # Specimen boundaries
    ax.add_patch(Rectangle((0, 0), 1.0, 1.0, fill=False, edgecolor='black', linewidth=1.5))
    # Initial notch
    ax.plot([0.0, 0.50], [0.50, 0.50], 'k-', linewidth=3.0, label='Initial Slit ($a=0.50$ mm)')
    # Off-axis circular hole
    hole = Circle((0.65, 0.65), 0.10, facecolor='white', edgecolor='black', linewidth=2.0, zorder=5)
    ax.add_patch(hole)

    # Plot broken elements
    x_vals = [e['x'] for e in elements]
    y_vals = [e['y'] for e in elements]
    d_vals = [e['d'] for e in elements]

    scatter = ax.scatter(x_vals, y_vals, c=d_vals, cmap='plasma', s=8, alpha=0.7, zorder=3,
                         vmin=0.80, vmax=1.0, label=r'Broken Elements ($d \geq 0.80$)')
    cbar = plt.colorbar(scatter, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Phase-Field Damage $d$', fontsize=12)

    # Annotations
    ax.annotate('Primary Crack Deflection', xy=(0.58, 0.56), xytext=(0.35, 0.70),
                arrowprops=dict(facecolor='blue', shrink=0.08, width=1.5, headwidth=8),
                fontsize=11, fontweight='bold', color='blue')

    ax.annotate('Crack Arrest at Hole', xy=(0.60, 0.60), xytext=(0.45, 0.85),
                arrowprops=dict(facecolor='darkgreen', shrink=0.08, width=1.5, headwidth=8),
                fontsize=11, fontweight='bold', color='darkgreen')

    ax.annotate('Secondary Crack to Boundary', xy=(0.85, 0.65), xytext=(0.60, 0.40),
                arrowprops=dict(facecolor='red', shrink=0.08, width=1.5, headwidth=8),
                fontsize=11, fontweight='bold', color='red')

    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel('Coordinate x [mm]', fontsize=12)
    ax.set_ylabel('Coordinate y [mm]', fontsize=12)
    ax.set_title('Mode-I Plate with Off-Axis Hole: Two-Stage Fracture Trajectory\nMethod A Refined (20,213 elems, Job 1421142.mmaster02)', fontsize=13)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.legend(loc='lower left', fontsize=10)
    plt.tight_layout()

    for p in out_paths:
        d = os.path.dirname(p)
        if not os.path.exists(d):
            os.makedirs(d)
        fig.savefig(p, dpi=300)
        print("Saved figure: %s" % p)
    plt.close()

if __name__ == '__main__':
    crack_csv = "results/validation/f1678_prod_crack_path.csv"
    targets = [
        "models/pandey_kumar_mode1/176_method_a_plate_with_hole/figures/f1678_method_a_crack_path.png",
        "MA_AdaptiveRemeshing_Report_2026/figures/f1678_method_a_crack_path.png",
        "MA_AdaptiveRemeshing_Report_2026/figures/f1678_method_a_crack_path.pdf",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures/f1678_method_a_crack_path.png",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures/f1678_method_a_crack_path.pdf"
    ]
    plot_crack_path(crack_csv, targets)
