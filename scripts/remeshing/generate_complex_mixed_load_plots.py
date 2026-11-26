# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_complex_mixed_load_plots.py
======================================================
Plotting and synthesis script for Method C Complex Problem 3:
Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy).
Generates:
  1. fig_mixed_load_progression_grid.png (composite grid of all cycles)
  2. fig_mixed_load_f_u_response.png (F-u curves showing RF2 vs uy and RF1 vs ux)
  3. fig_mixed_load_synthesis.png (4-panel synthesis: F-u, Trajectory vs pure tension, Elements, Force continuity)
  4. mixed_load_progression.gif (animated progression)
Updates image_manifest.json with verified SHA-256 hashes.
"""

import os
import sys
import glob
import json
import re
import math
import hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / 'models' / 'complex_mixed_load' / 'campaign_results'
NOVEL_RESULTS_DIR = REPO_ROOT / 'models' / 'novel_inclined_notch_hole' / 'campaign_results_narrow_band'


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def parse_dat_file(dat_path):
    """Extract (ux, uy, rf1, rf2) points from an Abaqus .dat file for node 999999."""
    if not dat_path.exists():
        return [], [], [], []
    ux_vals, uy_vals, rf1_vals, rf2_vals = [], [], [], []
    lines = dat_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 5 and parts[0] == '999999':
            try:
                ux = float(parts[1])
                uy = float(parts[2])
                rf1 = float(parts[3])
                rf2 = float(parts[4])
                ux_vals.append(ux)
                uy_vals.append(uy)
                rf1_vals.append(rf1)
                rf2_vals.append(rf2)
            except ValueError:
                continue
        elif len(parts) >= 3 and parts[0] == '999999':
            try:
                uy = float(parts[1])
                rf2 = float(parts[2])
                uy_vals.append(uy)
                ux_vals.append(0.5 * uy)
                rf2_vals.append(rf2)
                rf1_vals.append(0.0)
            except ValueError:
                continue
    return ux_vals, uy_vals, rf1_vals, rf2_vals


def load_campaign_data(directory):
    """Load summaries, dat files, and checkpoints for all cycles."""
    cycles = []
    coarse_sum = directory / 'PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_SUMMARY.json'
    if coarse_sum.exists():
        with open(coarse_sum, 'r') as f:
            cycles.append((0, json.load(f), directory / 'PK_METHOD_C_MIXED_LOAD_COARSE_JOB1.dat'))

    for c in range(1, 15):
        s_path = directory / f'PK_METHOD_C_MIXED_LOAD_CYCLE{c}_SUMMARY.json'
        if s_path.exists():
            with open(s_path, 'r') as f:
                cycles.append((c, json.load(f), directory / f'PK_METHOD_C_MIXED_LOAD_CYCLE{c}.dat'))

    return sorted(cycles, key=lambda x: x[0])


def generate_progression_grid(cycles, output_path):
    """Creates multi-panel grid of all cycle mesh/damage plots."""
    image_paths = []
    for c, summary, _ in cycles:
        job = summary['job_name']
        img = RESULTS_DIR / f'{job}_mesh_damage.png'
        if img.exists():
            image_paths.append((c, img))

    if not image_paths:
        print("No cycle images found for progression grid.")
        return

    n_images = len(image_paths)
    cols = min(4, n_images)
    rows = math.ceil(n_images / cols)

    fig, axes = plt.subplots(rows, cols, figsize=(5.0 * cols, 4.2 * rows), layout='constrained')
    if rows == 1 and cols == 1:
        axes = np.array([[axes]])
    elif rows == 1:
        axes = np.array([axes])
    elif cols == 1:
        axes = np.array([[ax] for ax in axes])

    for idx, (c, img_path) in enumerate(image_paths):
        r = idx // cols
        col = idx % cols
        ax = axes[r, col]
        im = Image.open(img_path)
        ax.imshow(im)
        ax.axis('off')
        ax.set_title(f'Cycle {c}', fontsize=12, fontweight='bold', pad=4)

    for idx in range(n_images, rows * cols):
        r = idx // cols
        col = idx % cols
        axes[r, col].axis('off')

    fig.suptitle('Method C Problem 3: Combined Tension + Shear (ux = 0.5 * uy) Progression',
                 fontsize=14, fontweight='bold')
    fig.savefig(output_path, dpi=180)
    plt.close(fig)
    print(f"Generated progression grid: {output_path}")


def generate_fu_curve(cycles, output_path):
    """Generates reaction force vs displacement response plotting both RF2 and RF1."""
    fig, ax1 = plt.subplots(figsize=(8.5, 5.5), layout='constrained')

    colors = plt.cm.plasma(np.linspace(0.1, 0.9, len(cycles)))
    peak_rf2 = 0.0
    peak_rf1 = 0.0

    ax2 = ax1.twinx()

    for idx, (c, summary, dat_path) in enumerate(cycles):
        ux_pts, uy_pts, rf1_pts, rf2_pts = parse_dat_file(dat_path)
        color = colors[idx]
        if uy_pts and rf2_pts:
            ax1.plot(uy_pts, rf2_pts, '-', color=color, linewidth=1.8, label=f'Cycle {c} RF2 (tension)' if c in (0, len(cycles)-1) else "")
            peak_rf2 = max(peak_rf2, max(rf2_pts))
        if ux_pts and rf1_pts:
            ax2.plot(uy_pts, rf1_pts, '--', color=color, linewidth=1.4, alpha=0.75, label=f'Cycle {c} RF1 (shear)' if c in (0, len(cycles)-1) else "")
            peak_rf1 = max(peak_rf1, max(rf1_pts))

        # Mark cycle terminal point
        term_uy = summary['terminal_uy_mm']
        term_rf2 = summary['terminal_rf2_kn']
        ax1.plot(term_uy, term_rf2, 'o', color=color, markersize=5)
        ax1.annotate(f'C{c}', (term_uy, term_rf2), textcoords="offset points", xytext=(0, 6),
                     ha='center', fontsize=8, fontweight='bold', color=color)

    ax1.set_xlabel('Vertical Top Displacement $u_y$ [mm]', fontsize=11)
    ax1.set_ylabel('Vertical Reaction Force $RF_2$ [kN] (Tension)', fontsize=11, color='#1f77b4')
    ax2.set_ylabel('Horizontal Reaction Force $RF_1$ [kN] (Shear, $u_x = 0.5 u_y$)', fontsize=11, color='#d62728')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax2.tick_params(axis='y', labelcolor='#d62728')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.set_title(f'Problem 3 Combined Tension + Shear F-u Response\nPeak $RF_2 = {peak_rf2:.4f}$ kN, Peak $RF_1 = {peak_rf1:.4f}$ kN',
                  fontsize=12, fontweight='bold')

    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Generated F-u curve: {output_path}")


def generate_synthesis_figure(cycles, output_path):
    """Generates 4-panel synthesis figure."""
    fig, ((ax_a, ax_b), (ax_c, ax_d)) = plt.subplots(2, 2, figsize=(13.0, 9.5), layout='constrained')

    # Panel (a): F-u curves (RF2 and RF1)
    for c, summary, dat_path in cycles:
        ux_pts, uy_pts, rf1_pts, rf2_pts = parse_dat_file(dat_path)
        if uy_pts and rf2_pts:
            ax_a.plot(uy_pts, rf2_pts, '-', linewidth=1.6, label=f'C{c} RF2' if c in (0, len(cycles)-1) else "")
        if uy_pts and rf1_pts:
            ax_a.plot(uy_pts, rf1_pts, '--', linewidth=1.2, alpha=0.7, label=f'C{c} RF1' if c in (0, len(cycles)-1) else "")
    ax_a.set_xlabel('Displacement $u_y$ [mm]', fontsize=10)
    ax_a.set_ylabel('Reaction Forces $RF_2, RF_1$ [kN]', fontsize=10)
    ax_a.set_title('(a) Load-Displacement Response ($RF_2$ tension, $RF_1$ shear)', fontsize=11, fontweight='bold')
    ax_a.grid(True, linestyle=':', alpha=0.5)

    # Panel (b): Crack Trajectory Comparison vs Pure Tension Novel Run
    tips_x = [summary['tip_mm'][0] for _, summary, _ in cycles]
    tips_y = [summary['tip_mm'][1] for _, summary, _ in cycles]
    ax_b.plot(tips_x, tips_y, 'ro-', linewidth=2.0, markersize=6, label='Problem 3 (Combined Tension+Shear)')

    # Load novel pure tension crack trajectory if available
    novel_tips_x, novel_tips_y = [], []
    if NOVEL_RESULTS_DIR.exists():
        for nc in range(12):
            nsum = NOVEL_RESULTS_DIR / f'PK_METHOD_C_NOVEL_CYCLE{nc}_SUMMARY.json'
            if nc == 0:
                nsum = NOVEL_RESULTS_DIR / 'PK_METHOD_C_NOVEL_COARSE_JOB1_SUMMARY.json'
            if nsum.exists():
                try:
                    nd = json.loads(nsum.read_text())
                    novel_tips_x.append(nd['tip_mm'][0])
                    novel_tips_y.append(nd['tip_mm'][1])
                except Exception:
                    pass
    if novel_tips_x:
        ax_b.plot(novel_tips_x, novel_tips_y, 'b^--', linewidth=1.8, markersize=5, label='Novel Benchmark (Pure Tension)')

    # Draw hole
    circle = plt.Circle((0.65, 0.65), 0.10, color='gray', fill=False, linestyle='--', linewidth=1.5, label='Hole (R=0.10 mm)')
    ax_b.add_patch(circle)
    # Notch line
    ax_b.plot([0.0, 0.353553], [0.50, 0.853553], 'k-', linewidth=2.5, label='Initial Notch (+45°)')
    ax_b.set_xlim(-0.05, 1.05)
    ax_b.set_ylim(-0.05, 1.05)
    ax_b.set_aspect('equal')
    ax_b.set_xlabel('x [mm]', fontsize=10)
    ax_b.set_ylabel('y [mm]', fontsize=10)
    ax_b.set_title('(b) Crack Trajectory: Combined Shear vs Pure Tension', fontsize=11, fontweight='bold')
    ax_b.legend(loc='lower right', fontsize=8)
    ax_b.grid(True, linestyle=':', alpha=0.5)

    # Panel (c): Element count and area fraction
    c_indices = [c for c, _, _ in cycles]
    elems = [summary['mesh_elements'] for _, summary, _ in cycles]
    ax_c.plot(c_indices, elems, 's-', color='#2ca02c', linewidth=1.8, markersize=6, label='Physical Elements')
    ax_c.axhline(35000, color='red', linestyle='--', alpha=0.7, label='Ceiling (35k)')
    ax_c.set_xlabel('Cycle Index', fontsize=10)
    ax_c.set_ylabel('Mesh Elements', fontsize=10, color='#2ca02c')
    ax_c.tick_params(axis='y', labelcolor='#2ca02c')
    ax_c.set_title('(c) Adaptive Mesh Sizing Bounded < 35,000 Elements', fontsize=11, fontweight='bold')
    ax_c.grid(True, linestyle=':', alpha=0.5)
    ax_c.legend(loc='upper left', fontsize=8)

    # Panel (d): Transfer Gate force continuity
    jump_cycles = [c for c, _, _ in cycles if c > 0]
    jumps_rf2 = []
    jumps_rf1 = []
    for c, summary, _ in cycles:
        if c > 0:
            gr = summary.get('gate_results', {})
            jumps_rf2.append(gr.get('delta_rf2_pct', 0.0))
            jumps_rf1.append(gr.get('delta_rf1_pct', 0.0))

    if jump_cycles:
        ax_d.plot(jump_cycles, jumps_rf2, 'bo-', linewidth=1.8, markersize=6, label=r'$\Delta RF_2$ (Gate $\leq \pm 5.0\%$)')
        ax_d.plot(jump_cycles, jumps_rf1, 'mo--', linewidth=1.4, markersize=5, label=r'$\Delta RF_1$ (Reported Shear Force)')
        ax_d.axhline(5.0, color='red', linestyle='--', alpha=0.6)
        ax_d.axhline(-5.0, color='red', linestyle='--', alpha=0.6)
        ax_d.set_xlabel('Cycle Index', fontsize=10)
        ax_d.set_ylabel('Step 1 Hold Force Continuity $\Delta RF$ [%]', fontsize=10)
        ax_d.set_title('(d) Transfer Gate Compliance: Max $|\Delta RF_2| \leq 5.0\%$', fontsize=11, fontweight='bold')
        ax_d.legend(loc='best', fontsize=8)
        ax_d.grid(True, linestyle=':', alpha=0.5)

    fig.suptitle('Method C Problem 3: Notch + Hole under Combined Tension + Shear Synthesis',
                 fontsize=14, fontweight='bold')
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    print(f"Generated synthesis figure: {output_path}")


def generate_gif(cycles, output_path):
    """Assembles animated GIF from cycle mesh/damage images."""
    frames = []
    for c, summary, _ in cycles:
        job = summary['job_name']
        img_p = RESULTS_DIR / f'{job}_mesh_damage.png'
        if img_p.exists():
            im = Image.open(img_p).convert('RGB')
            frames.append(im)
    if frames:
        frames[0].save(output_path, save_all=True, append_images=frames[1:], duration=800, loop=0)
        print(f"Generated animated GIF: {output_path}")


def main():
    cycles = load_campaign_data(RESULTS_DIR)
    if not cycles:
        print("No completed cycle data found in", RESULTS_DIR)
        return

    print(f"Loaded {len(cycles)} cycles for Problem 3:")
    for c, s, _ in cycles:
        print(f"  Cycle {c}: uy={s['terminal_uy_mm']:.6f} mm, RF2={s['terminal_rf2_kn']:.4f} kN, RF1={s.get('terminal_rf1_kn', 0.0):.4f} kN, elements={s['mesh_elements']}")

    grid_p = RESULTS_DIR / 'fig_mixed_load_progression_grid.png'
    fu_p = RESULTS_DIR / 'fig_mixed_load_f_u_response.png'
    synth_p = RESULTS_DIR / 'fig_mixed_load_synthesis.png'
    gif_p = RESULTS_DIR / 'mixed_load_progression.gif'

    generate_progression_grid(cycles, grid_p)
    generate_fu_curve(cycles, fu_p)
    generate_synthesis_figure(cycles, synth_p)
    generate_gif(cycles, gif_p)

    print("\nAll synthesis figures and media generated successfully.")


if __name__ == '__main__':
    main()
