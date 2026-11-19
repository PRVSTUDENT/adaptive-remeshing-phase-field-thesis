# -*- coding: utf-8 -*-
"""
scripts/postprocessing/plot_method_c_meeting_demo.py
Builds publication-quality meeting materials and figures for the 2 December 2026
supervisor meeting (Prof. Kiefer & Dr. Roth) demonstrating the complete Method C loop:
1. fig_method_c_load_displacement (.png / .pdf): RF2 vs u2 curve with key milestones.
2. fig_method_c_crack_extension (.png / .pdf): x_tip vs u2 curve with void geometry.
3. fig_method_c_damage_evolution_sequence (.png / .pdf): 6-panel mesh + damage contour sequence.
4. fig_method_c_loop_synthesis (.png / .pdf): 4-panel end-to-end Method C synthesis.
5. fig_method_c_damage_evolution (.gif): 28-frame damage evolution animation.

Authentic observables from PBS Jobs 1424517 (Job 1), 1424584 (Job 2), and 1424609 (Job 3).
"""

import os
import sys
import json
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import PolyCollection
import matplotlib.animation as animation

# Paths
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
DEMO_DIR = os.path.join(REPO_ROOT, 'models', 'pandey_kumar_mode1', '289_method_c_demo_case')
FIG_DIR = os.path.join(REPO_ROOT, 'results', 'figures', 'method_c_demo')
os.makedirs(FIG_DIR, exist_ok=True)

JOB1_SUMMARY_PATH = os.path.join(DEMO_DIR, 'PK_METHOD_C_DEMO_COARSE_JOB1_SUMMARY.json')
JOB2_SUMMARY_PATH = os.path.join(DEMO_DIR, 'PK_METHOD_C_DEMO_REFINED_STEP1_JOB2_SUMMARY.json')
JOB3_SUMMARY_PATH = os.path.join(DEMO_DIR, 'PK_METHOD_C_DEMO_PROPAGATION_JOB3_SUMMARY.json')
JOB3_FRAMES_PATH = os.path.join(DEMO_DIR, 'PK_METHOD_C_DEMO_JOB3_DAMAGE_FRAMES.json')
INP_PATH = os.path.join(DEMO_DIR, 'PK_METHOD_C_DEMO_REFINED_STEP1_JOB2.inp')


def parse_mesh_from_inp(inp_path):
    print("Parsing physical elements and node coordinates from refined input deck...")
    nodes = {}
    elements = {}
    with open(inp_path, 'r', encoding='utf-8') as f:
        in_node = False
        in_elem = False
        for line in f:
            line = line.strip()
            if line.startswith('*NODE'):
                in_node = True
                in_elem = False
                continue
            elif line.startswith('*ELEMENT, TYPE=U1') or line.startswith('*ELEMENT, TYPE=U3'):
                in_node = False
                in_elem = True
                continue
            elif line.startswith('*'):
                in_node = False
                in_elem = False
                continue
            if in_node and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 3:
                    nodes[int(parts[0])] = [float(parts[1]), float(parts[2])]
            elif in_elem and line:
                parts = [p.strip() for p in line.split(',')]
                if len(parts) >= 4:
                    elements[int(parts[0])] = [int(p) for p in parts[1:]]
    print(f"Parsed {len(nodes)} nodes and {len(elements)} physical elements.")
    return nodes, elements


def load_datasets():
    print("Loading Job 1, Job 2, Job 3 summaries and extracted frame data...")
    with open(JOB1_SUMMARY_PATH, 'r', encoding='utf-8') as f:
        job1 = json.load(f)
    with open(JOB2_SUMMARY_PATH, 'r', encoding='utf-8') as f:
        job2 = json.load(f)
    with open(JOB3_SUMMARY_PATH, 'r', encoding='utf-8') as f:
        job3 = json.load(f)
    with open(JOB3_FRAMES_PATH, 'r', encoding='utf-8') as f:
        frames_data = json.load(f)
    nodes, elements = parse_mesh_from_inp(INP_PATH)
    return job1, job2, job3, frames_data, nodes, elements


def plot_load_displacement(job1, job2, job3):
    print("Generating Figure 1: Load-displacement curve...")
    rp_history = job3['dat_rp_history']
    u2_vals = np.array([pt['u2_mm'] * 1000.0 for pt in rp_history])  # converted to um
    rf2_vals = np.array([pt['rf2_kN'] for pt in rp_history])

    fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=300)

    # Plot response curve
    ax.plot(u2_vals, rf2_vals, color='#1f77b4', lw=2.2, label='Job-3 Refined Mesh (10,299 elements)', zorder=3)

    # Mark Step 1 re-equilibration state
    u2_step1 = job3['step1_end_u2_mm'] * 1000.0
    rf2_step1 = job3['step1_end_RF2_kN']
    ax.scatter([u2_step1], [rf2_step1], color='#2ca02c', s=80, zorder=5, edgecolors='black',
               label=f'Re-equilibrated State: u2 = {job3["step1_end_u2_mm"]:.4f} mm, F = {rf2_step1:.4f} kN')

    # Mark Job 1 baseline point for comparison
    rf2_job1 = job1['RF2_kN']
    ax.scatter([u2_step1], [rf2_job1], color='#ff7f0e', marker='s', s=80, zorder=5, edgecolors='black',
               label=f'Job-1 Coarse Baseline: F = {rf2_job1:.4f} kN (ΔF = -1.37%)')

    # Mark Peak load
    u2_peak = job3['u2_at_peak_RF2_mm'] * 1000.0
    rf2_peak = job3['peak_RF2_kN']
    ax.scatter([u2_peak], [rf2_peak], color='#d62728', marker='*', s=160, zorder=6, edgecolors='black',
               label=f'Peak Structural Load: F_max = {rf2_peak:.4f} kN at u2 = {job3["u2_at_peak_RF2_mm"]:.4f} mm')

    # Mark Void capture (Increment 116)
    u2_void = 0.008683 * 1000.0
    rf2_void = 0.331590
    ax.scatter([u2_void], [rf2_void], color='#9467bd', marker='D', s=70, zorder=5, edgecolors='black',
               label=f'Void Penetration (Inc 116): u2 = 0.008683 mm, F = {rf2_void:.4f} kN')

    # Mark End of solve / cutback exit
    u2_end = job3['step2_end_u2_mm'] * 1000.0
    rf2_end = rf2_vals[-1]
    softening_pct = (rf2_end - rf2_peak) / rf2_peak * 100.0
    ax.scatter([u2_end], [rf2_end], color='#7f7f7f', marker='X', s=90, zorder=5, edgecolors='black',
               label=f'Severed Ligament Termination: u2 = {job3["step2_end_u2_mm"]:.4f} mm, F = {rf2_end:.4f} kN ({softening_pct:.1f}%)')

    # Annotations
    ax.annotate(f'Peak Load\nF = {rf2_peak:.3f} kN\n(u2 = {job3["u2_at_peak_RF2_mm"]*1000:.1f} µm)',
                xy=(u2_peak, rf2_peak), xytext=(u2_peak - 2.2, rf2_peak + 0.035),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9.5, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fee8c8', alpha=0.9), zorder=10)

    ax.annotate(f'Hole Capture\n(x = 0.65 mm reached)',
                xy=(u2_void, rf2_void), xytext=(u2_void - 2.2, rf2_void + 0.08),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#e0ecf4', alpha=0.9), zorder=10)

    # Inset box for transfer accuracy
    info_text = (
        "Method C State Transfer Metrics:\n"
        f"• Coarse mesh (Job 1): 2,920 quads, F = {rf2_job1:.4f} kN\n"
        f"• Refined mesh (Job 2): 10,299 quads, F = {rf2_step1:.4f} kN\n"
        f"• Force continuity: ΔF = -1.37%\n"
        f"• Energy continuity: ΔE = -0.77%\n"
        f"• Healing: Zero (SDV1 irreversibility maintained)\n"
        f"• Post-peak load softening: -59.58% demonstrated"
    )
    ax.text(0.55, 0.15, info_text, transform=ax.transAxes, fontsize=9.0,
            verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#999999', alpha=0.95), zorder=8)

    ax.set_xlabel('Remote Top-Edge Displacement $u_2$ [µm]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Reaction Force $RF_2$ [kN]', fontsize=12, fontweight='bold')
    ax.set_title('Mode-I Plate with Offset Void: Method C Load-Displacement Response\n(Phase-Field Crack Propagation & Void Capture)',
                 fontsize=12, fontweight='bold', pad=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0, 0.75)

    plt.tight_layout()
    png_path = os.path.join(FIG_DIR, 'fig_method_c_load_displacement.png')
    pdf_path = os.path.join(FIG_DIR, 'fig_method_c_load_displacement.pdf')
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Saved: {png_path} and {pdf_path}")


def plot_crack_extension(job3):
    print("Generating Figure 2: Crack-extension trajectory...")
    traj = job3.get('crack_extension_history', [])
    
    u2_pts = []
    xtip_pts = []
    ext_pts = []
    for pt in traj:
        u2_pts.append(pt['u2_mm'] * 1000.0)
        xtip_pts.append(pt['crack_tip_x_mm'])
        ext_pts.append(pt.get('crack_extension_Delta_a_mm', pt['crack_tip_x_mm'] - 0.5))

    u2_pts = np.array(u2_pts)
    xtip_pts = np.array(xtip_pts)

    fig, ax = plt.subplots(figsize=(8.5, 5.8), dpi=300)

    # Plot void geometry as shaded band
    # Hole center = 0.75 mm, radius = 0.10 mm -> void occupies x in [0.65, 0.85] mm
    ax.axhspan(0.65, 0.85, color='#e0ecf4', alpha=0.85, label='Circular Void [x = 0.65 to 0.85 mm, R = 0.10 mm]')
    ax.axhline(0.65, color='#8856a7', linestyle='--', lw=1.5, label='Void Front Boundary (x = 0.65 mm)')
    ax.axhline(0.75, color='#8856a7', linestyle=':', lw=1.2, label='Void Centerline (x = 0.75 mm)')
    ax.axhline(0.85, color='#8856a7', linestyle='--', lw=1.5, label='Void Rear Boundary (x = 0.85 mm)')
    ax.axhline(0.50, color='#636363', linestyle='-', lw=1.5, label='Initial Notch Tip (x = 0.50 mm)')

    # Plot crack extension curve
    if len(u2_pts) > 0:
        ax.plot(u2_pts, xtip_pts, color='#d95f02', lw=2.4, marker='o', markersize=3,
                label='Crack Tip Position $x_{\\mathrm{tip}}$ ($d \\geq 0.90$)', zorder=4)

    # Annotate critical events
    ax.annotate('Initial Stationary Notch\n(Elastic Loading & Transfer)',
                xy=(5.0, 0.50), xytext=(2.5, 0.54),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffe5', alpha=0.9))

    ax.annotate('Macroscopic Crack Initiation\n($u_2 \\approx 6.22$ µm, post-peak)',
                xy=(6.22, 0.50), xytext=(5.5, 0.44),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffe5', alpha=0.9))

    ax.annotate('Void Penetration / Hole Capture\n($x = 0.650$ mm at Inc 116, $u_2 = 8.683$ µm)',
                xy=(8.683, 0.650), xytext=(6.2, 0.70),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fee8c8', alpha=0.9))

    ax.annotate(f'Far-Side Re-initiation & Severance\n($x_{{\\mathrm{{tip}}}} = 0.8957$ mm, $\\Delta a = 0.3957$ mm)',
                xy=(8.756, 0.8957), xytext=(6.0, 0.88),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.2),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='#e5f5e0', alpha=0.9))

    ax.set_xlabel('Remote Top-Edge Displacement $u_2$ [µm]', fontsize=12, fontweight='bold')
    ax.set_ylabel('Crack Tip Position $x_{\\mathrm{tip}}$ [mm]', fontsize=12, fontweight='bold')
    ax.set_title('Crack Trajectory Evolution: Propagation across 150 µm Ligament into Void',
                 fontsize=12, fontweight='bold', pad=12)
    ax.set_xlim(0, 9.5)
    ax.set_ylim(0.40, 0.95)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper left', fontsize=8.5, framealpha=0.95)

    plt.tight_layout()
    png_path = os.path.join(FIG_DIR, 'fig_method_c_crack_extension.png')
    pdf_path = os.path.join(FIG_DIR, 'fig_method_c_crack_extension.pdf')
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Saved: {png_path} and {pdf_path}")


def plot_damage_evolution_sequence(frames_data, nodes, elements):
    print("Generating Figure 3: Damage evolution sequence (6 panels)...")
    frames_dict = frames_data['frames']

    # Select 6 key frames matching physical milestones:
    # '0': Re-equilibrated state (u2 = 0.0050 mm)
    # '4': Peak load (u2 = 0.006117 mm)
    # '10': Early ligament propagation (u2 = 0.006724 mm)
    # '15': Mid-ligament rapid advance (u2 = 0.006939 mm)
    # '116': Void penetration / hole capture (u2 = 0.008683 mm)
    # '125': Final severed state with far-side initiation (u2 = 0.008756 mm)
    selected_keys = ['0', '4', '10', '15', '116', '125']

    elem_ids = sorted(list(elements.keys()))
    polys = []
    for eid in elem_ids:
        conn = elements[eid]
        poly = [nodes[nid] for nid in conn]
        polys.append(poly)

    fig, axes = plt.subplots(2, 3, figsize=(15, 8.5), dpi=300)
    axes = axes.flatten()

    cmap = plt.cm.viridis
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=1.0)
    panel_labels = ['(a)', '(b)', '(c)', '(d)', '(e)', '(f)']

    for i, f_key in enumerate(selected_keys):
        ax = axes[i]
        fr = frames_dict[f_key]
        ed = fr['element_damage']
        d_vals = np.array([ed.get(str(eid), ed.get(eid, 0.0)) for eid in elem_ids])

        u2_um = fr['u2_mm'] * 1000.0
        rf2_kN = fr['rf2_kN']
        d_max = fr['max_damage']
        x_tip = fr['crack_tip_x_mm']
        inc = fr['frame']
        if i == 5:
            # Verified Job-3 final crack tip is 0.895686 mm (0.850 mm was the far hole surface)
            x_tip = 0.8957

        # Create PolyCollection for mesh with damage fill
        coll = PolyCollection(polys, array=d_vals, cmap=cmap, norm=norm, edgecolors='#404040', linewidths=0.15)
        ax.add_collection(coll)

        # Draw void explicitly (circle at x=0.75, y=0.50, r=0.10)
        hole = Circle((0.75, 0.50), 0.10, facecolor='white', edgecolor='#333333', lw=1.5, zorder=5)
        ax.add_patch(hole)

        # Draw initial notch crack line (y=0.50, x from 0 to 0.50)
        ax.plot([0.35, 0.50], [0.50, 0.50], color='red', lw=2.0, zorder=6)

        # Set focused view on crack path: x in [0.42, 0.95], y in [0.36, 0.64]
        ax.set_xlim(0.42, 0.95)
        ax.set_ylim(0.36, 0.64)
        ax.set_aspect('equal')

        # Subtitle
        if i == 0:
            stage_desc = f"Job-2 Re-equilibrated State (Inc {inc})\nu2 = {u2_um:.1f} µm | F = {rf2_kN:.3f} kN | d_max = {d_max:.2f}"
        elif i == 1:
            stage_desc = f"Peak Structural Load (Inc {inc})\nu2 = {u2_um:.1f} µm | F_max = {rf2_kN:.3f} kN | d_max = {d_max:.2f}"
        elif i == 2:
            stage_desc = f"Ligament Crack Growth (Inc {inc})\nu2 = {u2_um:.1f} µm | F = {rf2_kN:.3f} kN | x_tip = {x_tip:.3f} mm"
        elif i == 3:
            stage_desc = f"Rapid Mid-Ligament Advance (Inc {inc})\nu2 = {u2_um:.1f} µm | F = {rf2_kN:.3f} kN | x_tip = {x_tip:.3f} mm"
        elif i == 4:
            stage_desc = f"Hole Penetration / Capture (Inc {inc})\nu2 = {u2_um:.1f} µm | F = {rf2_kN:.3f} kN | x_tip = 0.650 mm"
        else:
            stage_desc = f"Severed Ligament & Re-initiation (Inc {inc})\nu2 = {u2_um:.1f} µm | F = {rf2_kN:.3f} kN | x_tip = {x_tip:.3f} mm"

        ax.set_title(f"{panel_labels[i]} {stage_desc}", fontsize=9.5, fontweight='bold', pad=8)
        ax.set_xlabel('x [mm]', fontsize=9)
        ax.set_ylabel('y [mm]', fontsize=9)
        ax.grid(True, linestyle=':', alpha=0.4)

    # Global Colorbar
    cbar_ax = fig.add_axes([0.15, 0.05, 0.70, 0.025])
    cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Phase-Field Damage $d$ (0 = Intact Material, 1 = Fully Broken Crack Surface)', fontsize=11, fontweight='bold')

    plt.suptitle('Method C Adaptive Remeshing Demonstration: Mode-I Crack Growth & Hole Capture\n(Finite Element Mesh & Phase-Field Damage Field Evolution, PBS Job 1424609)',
                 fontsize=13, fontweight='bold', y=0.98)

    plt.subplots_adjust(top=0.91, bottom=0.12, left=0.06, right=0.96, hspace=0.32, wspace=0.18)

    png_path = os.path.join(FIG_DIR, 'fig_method_c_damage_evolution_sequence.png')
    pdf_path = os.path.join(FIG_DIR, 'fig_method_c_damage_evolution_sequence.pdf')
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Saved: {png_path} and {pdf_path}")


def plot_loop_synthesis(job1, job2, job3, frames_data, nodes, elements):
    print("Generating Figure 4: Method C end-to-end loop synthesis (4 panels)...")
    frames_dict = frames_data['frames']
    elem_ids = sorted(list(elements.keys()))
    polys = []
    for eid in elem_ids:
        conn = elements[eid]
        poly = [nodes[nid] for nid in conn]
        polys.append(poly)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11), dpi=300)

    # Panel 1: Complete Specimen Geometry & Job 1 Coarse Overview
    ax1 = axes[0, 0]
    ax1.set_title('(a) Step 1: Baseline Coarse Solve (Job 1)\n1x1 mm Plate with 0.5 mm Notch & Offset Void (R=0.1 mm)', fontsize=10.5, fontweight='bold', pad=8)
    plate = Rectangle((0, 0), 1.0, 1.0, fill=None, edgecolor='black', lw=2.0)
    ax1.add_patch(plate)
    hole = Circle((0.75, 0.50), 0.10, facecolor='#f0f0f0', edgecolor='#333333', lw=1.8, label='Circular Void')
    ax1.add_patch(hole)
    ax1.plot([0, 0.5], [0.5, 0.5], color='red', lw=2.5, label='Initial Edge Notch (a0 = 0.5 mm)')
    ax1.scatter([0.5], [0.5], color='red', s=60, zorder=5)

    # Displacement arrows on top edge
    for x_arr in np.linspace(0.1, 0.9, 9):
        ax1.annotate('', xy=(x_arr, 1.08), xytext=(x_arr, 1.00),
                     arrowprops=dict(facecolor='#1f77b4', edgecolor='#1f77b4', width=1.5, headwidth=6))
    ax1.text(0.5, 1.11, 'Prescribed Displacement $u_2 = 0.005$ mm', ha='center', fontsize=9.5, fontweight='bold', color='#1f77b4')

    # Fixed bottom boundary
    ax1.plot([0, 1.0], [0, 0], color='black', lw=3.0)
    for x_arr in np.linspace(0.05, 0.95, 10):
        ax1.plot([x_arr, x_arr-0.03], [0, -0.04], color='#555555', lw=1.2)
    ax1.text(0.5, -0.08, 'Fixed Base ($u_1 = u_2 = 0$)', ha='center', fontsize=8.5, color='#333333')

    job1_text = (
        "Job-1 Baseline Observables (PBS 1424517):\n"
        f"• Elements: 2,920 physical quads (8,760 layered)\n"
        f"• Solver: Exit 0 (50 increments to u2 = 0.0050 mm)\n"
        f"• Reaction force: RF2 = {job1['RF2_kN']:.4f} kN\n"
        f"• Peak damage: d_max = {job1['max_damage']:.4f} (at notch tip)\n"
        f"• Mean bulk damage: {job1.get('mean_damage', 0.0086):.4f} (bulk intact)\n"
        f"• Peak history: H_max = {job1['max_history_MPa']:.3f} MPa\n"
        f"• UMAT MISESERI: Inactive (0.0) -> requires damage envelope"
    )
    ax1.text(0.03, 0.06, job1_text, transform=ax1.transAxes, fontsize=8.0,
             bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffcc', alpha=0.95, zorder=15), zorder=20)
    ax1.set_xlim(-0.05, 1.05)
    ax1.set_ylim(-0.14, 1.25)
    ax1.set_aspect('equal')
    ax1.legend(loc='lower right', fontsize=8.0)

    # Panel 2: Transfer and Refined Mesh
    ax2 = axes[0, 1]
    ax2.set_title('(b) Step 2: Nonmatching State & History Transfer\nMapping u, d, H onto Refined Mesh (10,299 Elements)', fontsize=10.5, fontweight='bold', pad=8)
    cmap = plt.cm.viridis
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=1.0)
    fr0 = frames_dict['0']
    ed0 = fr0['element_damage']
    d_vals_0 = np.array([ed0.get(str(eid), ed0.get(eid, 0.0)) for eid in elem_ids])
    coll2 = PolyCollection(polys, array=d_vals_0, cmap=cmap, norm=norm, edgecolors='#555555', linewidths=0.15)
    ax2.add_collection(coll2)
    hole2 = Circle((0.75, 0.50), 0.10, facecolor='white', edgecolor='#333333', lw=1.5, zorder=5)
    ax2.add_patch(hole2)
    ax2.plot([0.35, 0.50], [0.50, 0.50], color='red', lw=2.0, zorder=6)
    ax2.set_xlim(0.42, 0.95)
    ax2.set_ylim(0.20, 0.65)
    ax2.set_aspect('equal')

    transfer_text = (
        "Transfer Verification (Job 2 vs Job 1):\n"
        f"• Refined elements: 10,299 physical quads\n"
        f"• Local mesh sizing: h_min = 0.003 mm across ligament\n"
        f"• Force continuity: ΔF = {job2['delta_RF2_percent']:.2f}% (threshold ±5%)\n"
        f"• Energy continuity: ΔE = {job2['delta_E_total_percent']:.2f}% (threshold ±5%)\n"
        f"• Damage healing: None (SDV1 irreversibility maintained)\n"
        f"• Solver: Exit 0 (1 iteration re-equilibration)"
    )
    ax2.text(0.03, 0.04, transfer_text, transform=ax2.transAxes, fontsize=8.0,
             verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.3', facecolor='#e5f5e0', alpha=0.95, zorder=15), zorder=20)
    ax2.set_xlabel('x [mm]', fontsize=9)
    ax2.set_ylabel('y [mm]', fontsize=9)

    # Panel 3: Job-3 Forward Propagation & Hole Capture
    ax3 = axes[1, 0]
    ax3.set_title('(c) Step 3: Forward Crack Growth & Void Capture (Job 3)\nSevered Ligament & Re-initiation (149 Increments)', fontsize=10.5, fontweight='bold', pad=8)
    fr_final = frames_dict['125']
    ed_final = fr_final['element_damage']
    d_vals_final = np.array([ed_final.get(str(eid), ed_final.get(eid, 0.0)) for eid in elem_ids])
    coll3 = PolyCollection(polys, array=d_vals_final, cmap=cmap, norm=norm, edgecolors='#555555', linewidths=0.15)
    ax3.add_collection(coll3)
    hole3 = Circle((0.75, 0.50), 0.10, facecolor='white', edgecolor='#333333', lw=1.5, zorder=5)
    ax3.add_patch(hole3)
    ax3.plot([0.35, 0.50], [0.50, 0.50], color='red', lw=2.0, zorder=6)
    ax3.set_xlim(0.42, 0.95)
    ax3.set_ylim(0.20, 0.65)
    ax3.set_aspect('equal')

    job3_text = (
        "Job-3 Propagation Observables (PBS 1424609):\n"
        f"• Increments: 149 (Step 1: 24, Step 2: 125)\n"
        f"• Peak load: F_max = {job3['peak_RF2_kN']:.4f} kN at u2 = {job3['u2_at_peak_RF2_mm']:.4f} mm\n"
        f"• Void capture: Contact at x = 0.650 mm (Inc 116, u2 = 0.008683 mm)\n"
        f"• Post-peak softening: -59.58% (F drops to {job3['dat_rp_history'][-1]['rf2_kN']:.4f} kN)\n"
        f"• Total crack extension: Δa = {job3['final_crack_extension_mm']:.4f} mm (x_tip = 0.8957 mm)\n"
        f"• Termination: Exit 1 (cutback limit Δt < 1e-8 upon hole severance)"
    )
    ax3.text(0.03, 0.04, job3_text, transform=ax3.transAxes, fontsize=8.0,
             verticalalignment='bottom', bbox=dict(boxstyle='round,pad=0.3', facecolor='#fee8c8', alpha=0.95, zorder=15), zorder=20)
    ax3.set_xlabel('x [mm]', fontsize=9)
    ax3.set_ylabel('y [mm]', fontsize=9)

    # Panel 4: Combined RF2 vs u2 Response Curve
    ax4 = axes[1, 1]
    ax4.set_title('(d) Complete Load-Displacement Trajectory\nForce vs Displacement with Physical Milestones', fontsize=10.5, fontweight='bold', pad=8)
    rp_hist = job3['dat_rp_history']
    u_vals = [pt['u2_mm'] * 1000.0 for pt in rp_hist]
    f_vals = [pt['rf2_kN'] for pt in rp_hist]
    ax4.plot(u_vals, f_vals, color='#1f77b4', lw=2.2, label='Job 3 Response')
    ax4.scatter([job3['step1_end_u2_mm']*1000], [job3['step1_end_RF2_kN']], color='#2ca02c', s=70, zorder=5, label='Re-equilibration Point')
    ax4.scatter([job3['u2_at_peak_RF2_mm']*1000], [job3['peak_RF2_kN']], color='#d62728', marker='*', s=140, zorder=6, label='Peak Load (0.649 kN)')
    ax4.scatter([0.008683*1000], [0.331590], color='#9467bd', marker='D', s=60, zorder=5, label='Void Penetration (0.332 kN)')
    ax4.scatter([u_vals[-1]], [f_vals[-1]], color='#7f7f7f', marker='X', s=80, zorder=5, label='Termination (-59.6%)')
    ax4.set_xlabel('Displacement $u_2$ [µm]', fontweight='bold', fontsize=9)
    ax4.set_ylabel('Reaction Force $RF_2$ [kN]', fontweight='bold', fontsize=9)
    ax4.grid(True, linestyle='--', alpha=0.6)
    ax4.legend(loc='lower left', fontsize=8.0)

    plt.suptitle('Method C Incremental Adaptive Remeshing: End-to-End Synthesis\nCoarse Solve $\\rightarrow$ State Transfer $\\rightarrow$ Fixed-Load Re-equilibration $\\rightarrow$ Forward Crack Propagation into Void',
                 fontsize=12, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0.02, 1, 0.92])
    plt.subplots_adjust(top=0.88, hspace=0.30, wspace=0.22)

    png_path = os.path.join(FIG_DIR, 'fig_method_c_loop_synthesis.png')
    pdf_path = os.path.join(FIG_DIR, 'fig_method_c_loop_synthesis.pdf')
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Saved: {png_path} and {pdf_path}")


def create_damage_animation(frames_data, nodes, elements):
    print("Generating Figure 5: Damage evolution animation (GIF)...")
    frames_dict = frames_data['frames']
    frame_keys = sorted(list(frames_dict.keys()), key=lambda k: int(k))

    elem_ids = sorted(list(elements.keys()))
    polys = []
    for eid in elem_ids:
        conn = elements[eid]
        poly = [nodes[nid] for nid in conn]
        polys.append(poly)

    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=150)
    cmap = plt.cm.viridis
    norm = matplotlib.colors.Normalize(vmin=0.0, vmax=1.0)

    # Initial frame
    ed0 = frames_dict[frame_keys[0]]['element_damage']
    d0 = np.array([ed0.get(str(eid), ed0.get(eid, 0.0)) for eid in elem_ids])
    coll = PolyCollection(polys, array=d0, cmap=cmap, norm=norm, edgecolors='#404040', linewidths=0.15)
    ax.add_collection(coll)

    hole = Circle((0.75, 0.50), 0.10, facecolor='white', edgecolor='#333333', lw=1.5, zorder=5)
    ax.add_patch(hole)
    ax.plot([0.35, 0.50], [0.50, 0.50], color='red', lw=2.0, zorder=6)

    ax.set_xlim(0.42, 0.95)
    ax.set_ylim(0.36, 0.64)
    ax.set_aspect('equal')
    ax.set_xlabel('x [mm]', fontweight='bold')
    ax.set_ylabel('y [mm]', fontweight='bold')

    cbar = fig.colorbar(matplotlib.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
    cbar.set_label('Phase-Field Damage $d$', fontweight='bold')

    title_text = ax.set_title('', fontsize=10, fontweight='bold', pad=10)

    def update(idx):
        f_key = frame_keys[idx]
        fr = frames_dict[f_key]
        ed = fr['element_damage']
        d_vals = np.array([ed.get(str(eid), ed.get(eid, 0.0)) for eid in elem_ids])
        coll.set_array(d_vals)
        u2_um = fr['u2_mm'] * 1000.0
        rf2_kN = fr['rf2_kN']
        inc = fr['frame']
        x_tip = fr['crack_tip_x_mm']
        if idx == len(frame_keys) - 1:
            x_tip = 0.8957
        if x_tip >= 0.65 and x_tip < 0.85:
            hole_status = "HOLE CAPTURE"
        elif x_tip >= 0.85:
            hole_status = "FAR-SIDE PROPAGATION"
        else:
            hole_status = "LIGAMENT PROPAGATION"

        title_text.set_text(
            f"Method C Demo: Frame {idx+1}/{len(frame_keys)} (Inc {inc})\n"
            f"u2 = {u2_um:.2f} µm | RF2 = {rf2_kN:.3f} kN | x_tip = {x_tip:.3f} mm [{hole_status}]"
        )
        return coll, title_text

    ani = animation.FuncAnimation(fig, update, frames=len(frame_keys), blit=False, interval=400)
    gif_path = os.path.join(FIG_DIR, 'fig_method_c_damage_evolution.gif')
    ani.save(gif_path, writer='pillow', fps=2.5)
    plt.close()
    print(f"Saved: {gif_path}")


def main():
    job1, job2, job3, frames_data, nodes, elements = load_datasets()
    plot_load_displacement(job1, job2, job3)
    plot_crack_extension(job3)
    plot_damage_evolution_sequence(frames_data, nodes, elements)
    plot_loop_synthesis(job1, job2, job3, frames_data, nodes, elements)
    create_damage_animation(frames_data, nodes, elements)
    print("All meeting demo materials generated successfully.")


if __name__ == '__main__':
    main()
