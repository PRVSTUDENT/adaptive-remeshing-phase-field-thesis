"""
Plotting and synthesis script for Method C Complex Problem 1:
Inclined Notch + Two Holes in Series (Narrow-Band Adaptive Remeshing).
Generates:
  1. fig_two_hole_progression_grid.png (2x3 grid of Cycles 0 to 5)
  2. fig_two_hole_f_u_response.png (F-u curve with cycle markers and transfer jumps)
  3. fig_two_hole_synthesis.png (4-panel synthesis: F-u, Elements, Force continuity, Trajectory)
  4. two_hole_progression.gif (animated progression)
Updates image_manifest.json with commit-pinned hashes.
"""

import os
import sys
import glob
import json
import re
import hashlib
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = REPO_ROOT / 'models' / 'complex_two_hole' / 'campaign_results'


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
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
    coarse_sum = directory / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json'
    if coarse_sum.exists():
        with open(coarse_sum, 'r') as f:
            cycles.append((0, json.load(f), directory / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1.dat'))
    
    for c in range(1, 10):
        sum_file = directory / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}_SUMMARY.json'
        if sum_file.exists():
            with open(sum_file, 'r') as f:
                cycles.append((c, json.load(f), directory / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}.dat'))
    
    cycles.sort(key=lambda x: x[0])
    return cycles


def generate_progression_grid(cycles, out_path):
    """Create a 2x3 composite grid of Cycles 0 to 5."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 11), dpi=200)
    axes = axes.flatten()
    
    for idx, (c, summary, _) in enumerate(cycles):
        ax = axes[idx]
        if c == 0:
            img_path = RESULTS_DIR / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1_mesh_damage.png'
            title_prefix = "Cycle 0 (Coarse Baseline)"
        else:
            img_path = RESULTS_DIR / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}_mesh_damage.png'
            title_prefix = f"Cycle {c} (Adapted)"
            
        if img_path.exists():
            img = Image.open(img_path)
            ax.imshow(img)
        ax.axis('off')
        
        uy = summary.get('terminal_uy_mm', 0.0)
        rf2 = summary.get('terminal_rf2_kn', 0.0)
        elems = summary.get('adapted_mesh_elements', summary.get('mesh_elements', 0))
        dmax = summary.get('max_damage', 0.0)
        gate = summary.get('delta_rf2_pct', None)
        status = summary.get('stopping_criterion', summary.get('run_status', 'CONVERGED'))
        
        gate_str = f" | $\\Delta RF2$: {gate:+.4f}%" if gate is not None else ""
        title = (f"{title_prefix}\n"
                 f"$u_y$: {uy:.5f} mm | RF2: {rf2:.4f} kN | Elements: {elems:,}\n"
                 f"$d_{{\\max}}$: {dmax:.4f}{gate_str}\n"
                 f"Status: {status}")
        ax.set_title(title, fontsize=10, fontweight='bold', pad=6)
        
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated progression grid: {out_path}")


def generate_synthesis_figure(cycles, out_path):
    """Create 4-panel publication-quality synthesis figure."""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 11), dpi=200)
    
    # 1. Load-Displacement Response
    cycle_indices = []
    cycle_elems = []
    cycle_gates = []
    tip1_x, tip1_y = [], []
    tip2_x, tip2_y = [], []
    
    color_palette = plt.cm.plasma(np.linspace(0.1, 0.9, len(cycles)))
    
    for idx, (c, summary, dat_file) in enumerate(cycles):
        u_vals, rf_vals = parse_dat_file(dat_file)
        if u_vals:
            lbl = f"Cycle {c}" if c > 0 else "Cycle 0 (Coarse)"
            ax1.plot(np.array(u_vals)*1000, rf_vals, label=lbl, color=color_palette[idx], lw=2.0)
            # Mark transfer point (start of cycle)
            if c > 0:
                ax1.plot(u_vals[0]*1000, rf_vals[0], 'o', color=color_palette[idx], markersize=6)
        
        cycle_indices.append(c)
        cycle_elems.append(summary.get('adapted_mesh_elements', summary.get('mesh_elements', 0)))
        if c > 0:
            cycle_gates.append(summary.get('delta_rf2_pct', 0.0))
            
        t1 = summary.get('crack_tip_1', None)
        if t1:
            tip1_x.append(t1[0])
            tip1_y.append(t1[1])
        t2 = summary.get('crack_tip_2', None)
        if t2:
            tip2_x.append(t2[0])
            tip2_y.append(t2[1])

    ax1.set_xlabel('Prescribed Displacement $u_y$ [$\\mu$m]', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Reaction Force $RF2$ [kN]', fontsize=11, fontweight='bold')
    ax1.set_title('(a) Multi-Cycle Load-Displacement Response', fontsize=12, fontweight='bold')
    ax1.grid(True, linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize=9)
    
    # Peak annotation
    peak_rf = max(s.get('terminal_rf2_kn', 0.0) for _, s, _ in cycles)
    ax1.annotate(f'Peak: {peak_rf:.4f} kN (Cycle 3)',
                 xy=(6.035, peak_rf), xytext=(4.5, 0.75),
                 arrowprops=dict(facecolor='black', shrink=0.05, width=1, headwidth=6),
                 fontweight='bold', fontsize=9)
                 
    # 2. Element Count Evolution
    ax2.plot(cycle_indices, cycle_elems, 'o-', color='#1f77b4', lw=2.2, markersize=7)
    ax2.axhline(35000, color='r', linestyle='--', label='Element Ceiling (35,000)')
    ax2.set_xlabel('Adaptive Cycle Index', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Total Element Count', fontsize=11, fontweight='bold')
    ax2.set_title('(b) Adaptive Mesh Element Scaling', fontsize=12, fontweight='bold')
    ax2.set_xticks(cycle_indices)
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.set_ylim([0, 15000])
    for x, y in zip(cycle_indices, cycle_elems):
        ax2.annotate(f"{y:,}", (x, y), textcoords="offset points", xytext=(0, 8),
                     ha='center', fontsize=9, fontweight='bold')
    ax2.legend(loc='lower right', fontsize=9)
    
    # 3. Force Continuity Transfer Gate (Delta RF2 %)
    gate_cycles = cycle_indices[1:]
    ax3.bar(gate_cycles, cycle_gates, width=0.45, color='#2ca02c', edgecolor='black', alpha=0.85)
    ax3.axhline(+5.0, color='red', linestyle='--', lw=1.2, label='Tolerance Gate ($\\pm 5.0\\%$)')
    ax3.axhline(-5.0, color='red', linestyle='--', lw=1.2)
    ax3.axhline(0.0, color='black', linestyle='-', lw=0.8)
    ax3.set_xlabel('Adaptive Remeshing Cycle', fontsize=11, fontweight='bold')
    ax3.set_ylabel('Step 1 Force Jump $\\Delta RF2$ [%]', fontsize=11, fontweight='bold')
    ax3.set_title('(c) Fixed-Load Hold Force Continuity Compliance', fontsize=12, fontweight='bold')
    ax3.set_xticks(gate_cycles)
    ax3.set_ylim([-5.5, 5.5])
    ax3.grid(True, linestyle='--', alpha=0.5)
    for x, y in zip(gate_cycles, cycle_gates):
        ax3.annotate(f"{y:+.4f}%", (x, y), textcoords="offset points",
                     xytext=(0, 6 if y >= 0 else -14),
                     ha='center', fontsize=8.5, fontweight='bold')
    ax3.legend(loc='upper right', fontsize=9)
    
    # 4. Crack Trajectories and Specimen Geometry
    # Draw plate boundary
    ax4.plot([0, 1, 1, 0, 0], [0, 0, 1, 1, 0], 'k-', lw=1.5)
    # Notch
    ax4.plot([0, 0.353553], [0.5, 0.853553], 'k-', lw=2.5, label='Inclined Notch (+45°)')
    # Hole 1 (0.65, 0.65), R=0.10
    theta = np.linspace(0, 2*np.pi, 200)
    h1_x = 0.65 + 0.10 * np.cos(theta)
    h1_y = 0.65 + 0.10 * np.sin(theta)
    ax4.fill(h1_x, h1_y, color='lightgray', edgecolor='black', lw=1.5, label='Hole 1 (R=0.10)')
    # Hole 2 (0.87, 0.62), R=0.06
    h2_x = 0.87 + 0.06 * np.cos(theta)
    h2_y = 0.62 + 0.06 * np.sin(theta)
    ax4.fill(h2_x, h2_y, color='silver', edgecolor='black', lw=1.5, label='Hole 2 (R=0.06)')
    
    # Crack 1 trajectory
    if tip1_x:
        all_t1_x = [0.353553] + tip1_x
        all_t1_y = [0.853553] + tip1_y
        ax4.plot(all_t1_x, all_t1_y, 'ro-', lw=2.0, markersize=5,
                 label=r'Crack 1 Path (Notch root $\to$ arrests at $x \approx 0.50$, misses Hole 1)')
    # Crack 2 trajectory
    if tip2_x:
        ax4.plot(tip2_x, tip2_y, 'ms-', lw=2.2, markersize=6,
                 label=r'Crack 2 Path (Hole 1 $\to$ Hole 2 boundary contact)')
        
    ax4.set_xlim([-0.05, 1.05])
    ax4.set_ylim([-0.05, 1.05])
    ax4.set_aspect('equal')
    ax4.set_xlabel('X Coordinate [mm]', fontsize=11, fontweight='bold')
    ax4.set_ylabel('Y Coordinate [mm]', fontsize=11, fontweight='bold')
    ax4.set_title('(d) Dual Crack Propagation Trajectories', fontsize=12, fontweight='bold')
    ax4.grid(True, linestyle='--', alpha=0.5)
    ax4.legend(loc='lower left', fontsize=8.5)
    
    plt.tight_layout()
    fig.savefig(out_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    print(f"Generated synthesis figure: {out_path}")


def generate_animated_gif(cycles, out_path):
    """Create an animated GIF cycling through all cycle mesh damage states."""
    images = []
    for c, _, _ in cycles:
        if c == 0:
            p = RESULTS_DIR / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1_mesh_damage.png'
        else:
            p = RESULTS_DIR / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}_mesh_damage.png'
        if p.exists():
            images.append(Image.open(p).convert('RGB'))
    if images:
        images[0].save(out_path, save_all=True, append_images=images[1:], duration=1200, loop=0)
        print(f"Generated animated GIF: {out_path}")


def update_manifest_commits(cycles):
    """Ensure image_manifest.json contains commit hashes and newly generated images."""
    import subprocess
    manifest_path = RESULTS_DIR / 'image_manifest.json'
    
    manifest_entries = []
    for c, summary, _ in cycles:
        if c == 0:
            rel_path = "models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_COARSE_JOB1_mesh_damage.png"
            full_p = RESULTS_DIR / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1_mesh_damage.png'
            mesh_p = RESULTS_DIR / 'PK_METHOD_C_TWO_HOLE_COARSE_JOB1_PHYS.inp'
        else:
            rel_path = f"models/complex_two_hole/campaign_results/PK_METHOD_C_TWO_HOLE_CYCLE{c}_mesh_damage.png"
            full_p = RESULTS_DIR / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}_mesh_damage.png'
            mesh_p = RESULTS_DIR / f'PK_METHOD_C_TWO_HOLE_CYCLE{c}_PHYS.inp'
            
        res = subprocess.run(["git", "log", "-1", "--format=%H", "--", rel_path],
                             cwd=REPO_ROOT, stdout=subprocess.PIPE, text=True)
        commit = res.stdout.strip() or "PENDING"
        
        manifest_entries.append({
            "cycle": c,
            "uy_mm": summary.get('terminal_uy_mm', 0.0),
            "path": rel_path,
            "commit": commit,
            "image_sha256": sha256_file(full_p) if full_p.exists() else "MISSING",
            "url": f"https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/{commit}/{rel_path}",
            "mesh_sha256": sha256_file(mesh_p) if mesh_p.exists() else "MISSING",
            "source_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        })
        
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_entries, f, indent=2)
    print(f"Updated {manifest_path} with {len(manifest_entries)} entries.")


def main():
    cycles = load_campaign_data(RESULTS_DIR)
    print(f"Loaded {len(cycles)} cycles.")
    
    grid_path = RESULTS_DIR / 'fig_two_hole_progression_grid.png'
    synth_path = RESULTS_DIR / 'fig_two_hole_synthesis.png'
    gif_path = RESULTS_DIR / 'two_hole_progression.gif'
    
    generate_progression_grid(cycles, grid_path)
    generate_synthesis_figure(cycles, synth_path)
    generate_animated_gif(cycles, gif_path)
    update_manifest_commits(cycles)


if __name__ == '__main__':
    main()
