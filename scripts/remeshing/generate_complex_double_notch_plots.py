"""
scripts/remeshing/generate_complex_double_notch_plots.py
========================================================
Plotting and synthesis script for Method C Complex Problem 2:
Double Notch Symmetrical Crack Coalescence (Narrow-Band Adaptive Remeshing).
Generates:
  1. fig_double_notch_progression_grid.png (composite grid of all cycles)
  2. fig_double_notch_f_u_response.png (F-u curve with cycle markers and transfer jumps)
  3. fig_double_notch_synthesis.png (4-panel synthesis: F-u, Elements, Force continuity, Tip distance/arc lengths)
  4. double_notch_progression.gif (animated progression)
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
RESULTS_DIR = REPO_ROOT / 'models' / 'complex_double_notch' / 'campaign_results'


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
    """Extract (u2, rf2) points from an Abaqus .dat file for node 999999."""
    if not dat_path.exists():
        return [], []
    u_vals, rf_vals = [], []
    lines = dat_path.read_text(encoding='utf-8', errors='ignore').splitlines()
    for line in lines:
        parts = line.strip().split()
        if len(parts) >= 3 and parts[0] == '999999':
            try:
                u = float(parts[1])
                rf = float(parts[2])
                u_vals.append(u)
                rf_vals.append(rf)
            except ValueError:
                continue
    return u_vals, rf_vals


def load_campaign_data(directory):
    """Load summaries, dat files, and checkpoints for all cycles."""
    cycles = []
    coarse_sum = directory / 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_SUMMARY.json'
    if coarse_sum.exists():
        with open(coarse_sum, 'r') as f:
            cycles.append((0, json.load(f), directory / 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1.dat'))

    for c in range(1, 15):
        sum_file = directory / f'PK_METHOD_C_DOUBLE_NOTCH_CYCLE{c}_SUMMARY.json'
        if sum_file.exists():
            with open(sum_file, 'r') as f:
                cycles.append((c, json.load(f), directory / f'PK_METHOD_C_DOUBLE_NOTCH_CYCLE{c}.dat'))

    cycles.sort(key=lambda x: x[0])
    return cycles


def generate_progression_grid(cycles, out_path):
    """Create a composite grid of all executed cycles."""
    n = len(cycles)
    if n <= 4:
        rows, cols = 1, n
        fig_w, fig_h = 6 * cols, 6
    elif n <= 6:
        rows, cols = 2, 3
        fig_w, fig_h = 18, 11
    elif n <= 8:
        rows, cols = 2, 4
        fig_w, fig_h = 22, 11
    else:
        cols = 4
        rows = int(math.ceil(n / 4.0))
        fig_w, fig_h = 22, 5.5 * rows

    fig, axes = plt.subplots(rows, cols, figsize=(fig_w, fig_h), dpi=200)
    if hasattr(axes, 'flatten'):
        axes_flat = axes.flatten()
    else:
        axes_flat = [axes]

    for idx, (c, summary, _) in enumerate(cycles):
        ax = axes_flat[idx]
        if c == 0:
            img_path = RESULTS_DIR / 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_mesh_damage.png'
            title_prefix = "Cycle 0 (Coarse Baseline)"
        else:
            img_path = RESULTS_DIR / f'PK_METHOD_C_DOUBLE_NOTCH_CYCLE{c}_mesh_damage.png'
            title_prefix = f"Cycle {c} (Adapted)"

        if img_path.exists():
            img = Image.open(img_path)
            ax.imshow(img)
        ax.axis('off')

        uy = summary.get('terminal_uy_mm', 0.0)
        rf2 = summary.get('terminal_rf2_kn', 0.0)
        elems = summary.get('mesh_elements', 0)
        dmax = summary.get('max_damage', 0.0)
        dist = summary.get('tip_distance_mm', 0.0)
        coalesced = summary.get('coalesced', False)
        gates = summary.get('gate_results', {})
        gate = gates.get('force_continuity_delta_pct', None)

        gate_str = f" | $\\Delta RF2$: {gate:+.3f}%" if gate is not None else ""
        coal_str = " | COALESCED" if coalesced else f" | Dist: {dist:.3f} mm"

        ax.set_title(
            f"{title_prefix}\n"
            f"$u_y$: {uy:.5f} mm | RF2: {rf2:.4f} kN{gate_str}\n"
            f"Elems: {elems:,} | $d_{{max}}$: {dmax:.4f}{coal_str}",
            fontsize=9, pad=4
        )

    for idx in range(len(cycles), len(axes_flat)):
        axes_flat[idx].axis('off')

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Generated progression grid: {out_path}")


def generate_fu_curve(cycles, out_path):
    """Plot global F-u response across cycles."""
    fig, ax = plt.subplots(figsize=(8, 6), dpi=200)

    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(cycles)))
    peak_rf = 0.0
    peak_u = 0.0

    for idx, (c, summary, dat_path) in enumerate(cycles):
        u_pts, rf_pts = parse_dat_file(dat_path)
        if u_pts:
            label = f"Cycle {c}" if c > 0 else "Cycle 0 (Coarse)"
            ax.plot(u_pts, rf_pts, color=colors[idx], lw=1.8, label=label)
            local_peak = max(rf_pts)
            if local_peak > peak_rf:
                peak_rf = local_peak
                peak_u = u_pts[rf_pts.index(local_peak)]

    if peak_rf > 0:
        ax.scatter([peak_u], [peak_rf], color='red', s=60, zorder=5)
        ax.annotate(f"Peak: {peak_rf:.4f} kN\nat $u_y$={peak_u:.5f} mm",
                    xy=(peak_u, peak_rf), xytext=(peak_u + 0.0003, peak_rf * 0.95),
                    arrowprops=dict(arrowstyle="->", color='red', lw=1.2),
                    fontsize=9, color='red', fontweight='bold')

    # Draw 5% load drop threshold
    if peak_rf > 0:
        thresh = 0.05 * peak_rf
        ax.axhline(thresh, color='gray', ls='--', lw=1.0, label=f"5% Peak Threshold ({thresh:.4f} kN)")

    ax.set_xlabel("Prescribed Displacement $u_y$ [mm]", fontsize=11)
    ax.set_ylabel("Reaction Force RF2 [kN]", fontsize=11)
    ax.set_title("Method C Problem 2: Double Notch Symmetrical Crack Coalescence\nReaction Force vs. Displacement Response", fontsize=12, fontweight='bold')
    ax.grid(True, ls=':', alpha=0.6)
    ax.legend(fontsize=8, loc='upper right')

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Generated F-u curve: {out_path}")


def generate_synthesis_figure(cycles, out_path):
    """Create a 4-panel publication synthesis figure."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=200)

    # Panel A: F-u Curve
    ax_a = axes[0, 0]
    colors = plt.cm.viridis(np.linspace(0.1, 0.9, len(cycles)))
    peak_rf = 0.0
    for idx, (c, summary, dat_path) in enumerate(cycles):
        u_pts, rf_pts = parse_dat_file(dat_path)
        if u_pts:
            label = f"C{c}" if c > 0 else "C0"
            ax_a.plot(u_pts, rf_pts, color=colors[idx], lw=1.6, label=label)
            local_peak = max(rf_pts)
            if local_peak > peak_rf:
                peak_rf = local_peak
    ax_a.set_xlabel("$u_y$ [mm]", fontsize=10)
    ax_a.set_ylabel("Reaction Force RF2 [kN]", fontsize=10)
    ax_a.set_title("(a) Reaction Force vs. Displacement", fontsize=11, fontweight='bold')
    ax_a.grid(True, ls=':', alpha=0.6)
    ax_a.legend(fontsize=7, loc='upper right', ncol=2)

    # Panel B: Elements and Max Damage vs Cycle
    ax_b = axes[0, 1]
    cycle_indices = [c for c, _, _ in cycles]
    elem_counts = [s.get('mesh_elements', 0) for _, s, _ in cycles]
    damages = [s.get('max_damage', 0.0) for _, s, _ in cycles]

    color_elem = 'tab:blue'
    ax_b.set_xlabel("Cycle Index", fontsize=10)
    ax_b.set_ylabel("Mesh Elements", color=color_elem, fontsize=10)
    line1 = ax_b.plot(cycle_indices, elem_counts, 'o-', color=color_elem, lw=1.8, label="Elements")
    ax_b.tick_params(axis='y', labelcolor=color_elem)
    ax_b.axhline(35000, color='red', ls='--', lw=1.0, alpha=0.7, label="Ceiling (35k)")
    ax_b.grid(True, ls=':', alpha=0.6)

    ax_b_tw = ax_b.twinx()
    color_d = 'tab:red'
    ax_b_tw.set_ylabel("Max Damage $d_{max}$", color=color_d, fontsize=10)
    line2 = ax_b_tw.plot(cycle_indices, damages, 's--', color=color_d, lw=1.8, label="$d_{max}$")
    ax_b_tw.tick_params(axis='y', labelcolor=color_d)
    ax_b_tw.set_ylim(-0.05, 1.05)
    ax_b.set_title("(b) Element Count & Damage Evolution", fontsize=11, fontweight='bold')

    # Panel C: Step 1 Force Continuity Gate
    ax_c = axes[1, 0]
    adapt_cycles = [c for c, _, _ in cycles if c > 0]
    force_jumps = [s.get('gate_results', {}).get('force_continuity_delta_pct', 0.0) for c, s, _ in cycles if c > 0]
    if adapt_cycles:
        bar_colors = ['tab:green' if abs(j) <= 5.0 else 'tab:red' for j in force_jumps]
        ax_c.bar(adapt_cycles, force_jumps, color=bar_colors, width=0.5, edgecolor='black', lw=0.8)
        ax_c.axhline(5.0, color='red', ls='--', lw=1.2, label="Acceptance Gate ($\pm$5%)")
        ax_c.axhline(-5.0, color='red', ls='--', lw=1.2)
        ax_c.axhline(0.0, color='black', lw=0.8)
        for c, j in zip(adapt_cycles, force_jumps):
            ax_c.annotate(f"{j:+.2f}%", xy=(c, j), xytext=(0, 3 if j >= 0 else -10),
                          textcoords="offset points", ha='center', fontsize=8, fontweight='bold')
    ax_c.set_xlabel("Adaptive Cycle Index", fontsize=10)
    ax_c.set_ylabel("Step 1 Force Jump $\Delta RF2$ [%]", fontsize=10)
    ax_c.set_title("(c) Step 1 Fixed-Load Re-equilibration Gate ($\pm$5%)", fontsize=11, fontweight='bold')
    ax_c.set_ylim(-6.5, 6.5)
    ax_c.grid(True, ls=':', alpha=0.6)
    ax_c.legend(fontsize=8, loc='upper right')

    # Panel D: Crack Arc Lengths and Tip Distance
    ax_d = axes[1, 1]
    s1_vals = [s.get('left_crack_arc_length_s1_mm', 0.0) for _, s, _ in cycles]
    s2_vals = [s.get('right_crack_arc_length_s2_mm', 0.0) for _, s, _ in cycles]
    dist_vals = [s.get('tip_distance_mm', 0.292893) for _, s, _ in cycles]

    ax_d.plot(cycle_indices, s1_vals, 'o-', color='tab:blue', lw=1.8, label="Left Crack $s_1$")
    ax_d.plot(cycle_indices, s2_vals, '^--', color='tab:orange', lw=1.8, label="Right Crack $s_2$")
    ax_d.set_xlabel("Cycle Index", fontsize=10)
    ax_d.set_ylabel("Crack Arc Length [mm]", fontsize=10)

    ax_d_tw = ax_d.twinx()
    ax_d_tw.plot(cycle_indices, dist_vals, 's:', color='tab:purple', lw=1.8, label="Tip Distance $\Delta x_{tips}$")
    ax_d_tw.set_ylabel("Tip Separation Distance [mm]", color='tab:purple', fontsize=10)
    ax_d_tw.tick_params(axis='y', labelcolor='tab:purple')
    ax_d_tw.axhline(0.015, color='gray', ls='--', lw=1.0, label="Coalescence Limit ($2l_0$)")

    ax_d.set_title("(d) Crack Arc Lengths ($s_1, s_2$) & Tip Separation", fontsize=11, fontweight='bold')
    ax_d.grid(True, ls=':', alpha=0.6)

    # Combined legend for panel D
    lines_d, labels_d = ax_d.get_legend_handles_labels()
    lines_dt, labels_dt = ax_d_tw.get_legend_handles_labels()
    ax_d.legend(lines_d + lines_dt, labels_d + labels_dt, fontsize=7, loc='center right')

    plt.suptitle("Method C Problem 2: Double Notch Symmetrical Crack Coalescence Campaign Synthesis",
                 fontsize=13, fontweight='bold', y=0.995)
    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Generated 4-panel synthesis figure: {out_path}")


def generate_animated_gif(cycles, out_path):
    """Generate animated GIF progression across all cycles."""
    images = []
    for c, _, _ in cycles:
        if c == 0:
            p = RESULTS_DIR / 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_mesh_damage.png'
        else:
            p = RESULTS_DIR / f'PK_METHOD_C_DOUBLE_NOTCH_CYCLE{c}_mesh_damage.png'
        if p.exists():
            images.append(Image.open(p))

    if images:
        images[0].save(
            out_path,
            save_all=True,
            append_images=images[1:],
            duration=1200,
            loop=0
        )
        print(f"Generated animated GIF: {out_path}")


def update_manifest_file_shas():
    """Ensure image_manifest.json contains exact summary file SHA-256 hashes."""
    manifest_path = RESULTS_DIR / 'image_manifest.json'
    if not manifest_path.exists():
        return

    with open(manifest_path, 'r') as f:
        manifest = json.load(f)

    for entry in manifest:
        cycle = entry.get('cycle')
        if cycle == 0:
            sum_path = RESULTS_DIR / 'PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_SUMMARY.json'
        else:
            sum_path = RESULTS_DIR / f'PK_METHOD_C_DOUBLE_NOTCH_CYCLE{cycle}_SUMMARY.json'

        if sum_path.exists():
            entry['summary_file_sha256'] = sha256_file(sum_path)

    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)
    print("Updated image_manifest.json with summary file SHA-256 hashes.")


def main():
    cycles = load_campaign_data(RESULTS_DIR)
    if not cycles:
        print("No campaign data found in:", RESULTS_DIR)
        return

    print(f"Loaded {len(cycles)} cycles for Problem 2 plotting.")

    grid_path = RESULTS_DIR / 'fig_double_notch_progression_grid.png'
    fu_path = RESULTS_DIR / 'fig_double_notch_f_u_response.png'
    synth_path = RESULTS_DIR / 'fig_double_notch_synthesis.png'
    gif_path = RESULTS_DIR / 'double_notch_progression.gif'

    generate_progression_grid(cycles, grid_path)
    generate_fu_curve(cycles, fu_path)
    generate_synthesis_figure(cycles, synth_path)
    generate_animated_gif(cycles, gif_path)
    update_manifest_file_shas()


if __name__ == '__main__':
    main()
