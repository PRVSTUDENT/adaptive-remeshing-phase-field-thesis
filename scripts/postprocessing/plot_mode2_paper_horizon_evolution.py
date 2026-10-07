#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_mode2_paper_horizon_evolution.py

Publication-quality multi-frame evolution figure generator for Mode-II Gate M2-2:
1. Complete reaction force Fx vs prescribed shear displacement ux with marked snapshots.
2. 5-frame spatial evolution of MISESERI error recovery field.
3. 5-frame spatial evolution of phase-field damage d(x, y).
4. Direct overlay of Pandey & Kumar (2025) Fig. 6(b), Fig. 12, and Fig. 13(a) benchmarks.

Governing Reference: Pandey & Kumar (2025) Section 4.2.
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from matplotlib.colors import Normalize

# Digitized Fig. 6(b) / Fig. 12 trajectory points
DIGITIZED_FIG6B = np.array([
    [0.495, 0.514], [0.540, 0.460], [0.600, 0.380],
    [0.680, 0.280], [0.760, 0.180], [0.840, 0.080], [0.930, 0.000]
])

# Digitized Fig. 13(a) coarse pre-analysis force-displacement response
# [ux (mm), Fx (kN)]
DIGITIZED_FIG13A = np.array([
    [0.0000, 0.000],
    [0.0025, 0.200],
    [0.0050, 0.400],
    [0.0075, 0.600],
    [0.00936, 0.748],
    [0.01000, 0.795],
    [0.011842, 0.835], # Peak region
    [0.01400, 0.650], # Softening
    [0.01626, 0.350], # Deep post-peak
    [0.01800, 0.100],
    [0.02000, 0.005]  # Complete failure
])

TARGET_UX_LABELS = [
    ("0.00936", r"$u_x = 9.36\,\mu\text{m}$" + "\n(Pre-Peak Linear)"),
    ("0.01000", r"$u_x = 10.0\,\mu\text{m}$" + "\n(Step-1 Final)"),
    ("0.01184", r"$u_x = 11.84\,\mu\text{m}$" + "\n(Peak / Initiation)"),
    ("0.01626", r"$u_x = 16.26\,\mu\text{m}$" + "\n(Post-Peak Propagation)"),
    ("0.02000", r"$u_x = 20.0\,\mu\text{m}$" + "\n(Terminal Horizon)")
]

def load_csv_data(filepath):
    if not os.path.exists(filepath):
        return None
    try:
        return np.genfromtxt(filepath, delimiter=',', skip_header=1)
    except Exception as e:
        print(f"[WARN] Error loading {filepath}: {e}")
        return None

def generate_evolution_figure(data_dir=".", out_fig_path="results/figures/mode2/mode2_paper_horizon_miseseri_damage_evolution.png"):
    rf_csv = os.path.join(data_dir, "mode2_j1_rf_history.csv")
    summary_json = os.path.join(data_dir, "MODE2_M2_2_TERMINAL_EXTRACTION_SUMMARY.json")

    if not os.path.exists(rf_csv) or not os.path.exists(summary_json):
        print(f"[WARN] Required extraction CSV/JSON not found in '{data_dir}'.")
        print("This script will execute once the terminal ODB extraction is complete.")
        return False

    with open(summary_json, 'r') as f:
        meta = json.load(f)

    rf_records = []
    with open(rf_csv, 'r') as f:
        f.readline()
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 7:
                try:
                    rf_records.append({
                        'step': parts[0],
                        'frame_id': int(parts[1]),
                        'inc': int(parts[2]),
                        'time': float(parts[3]),
                        'ux_nom': float(parts[4]),
                        'ux_act': float(parts[5]),
                        'fx_kN': float(parts[6])
                    })
                except ValueError:
                    continue

    ux_vals = np.array([r['ux_nom'] for r in rf_records])
    fx_vals = np.array([r['fx_kN'] for r in rf_records])

    # Setup 3-tier figure:
    # Row 0: Reaction Force vs Displacement
    # Row 1: 5 MISESERI Snapshots
    # Row 2: 5 Damage Snapshots
    fig = plt.figure(figsize=(18, 12))
    gs = GridSpec(3, 5, height_ratios=[1.2, 1.0, 1.0], hspace=0.35, wspace=0.25)

    # 1. Top Panel: Reaction Force Curve
    ax_rf = fig.add_subplot(gs[0, :])
    ax_rf.plot(ux_vals * 1e3, fx_vals, 'b-', lw=2.5, label='Mode-II Reconstructed Pre-Analysis (2,960 FEs, Miehe Split)')
    ax_rf.plot(DIGITIZED_FIG13A[:, 0] * 1e3, DIGITIZED_FIG13A[:, 1], 'k--', lw=1.8, alpha=0.7, label='Pandey & Kumar (2025) Fig. 13(a) Reference')

    colors = ['#1f77b4', '#2ca02c', '#ff7f0e', '#d62728', '#9467bd']
    for idx, (tag, label_text) in enumerate(TARGET_UX_LABELS):
        u_target = float(tag)
        nearest_idx = np.argmin(np.abs(ux_vals - u_target))
        u_pt = ux_vals[nearest_idx] * 1e3
        f_pt = fx_vals[nearest_idx]
        ax_rf.plot(u_pt, f_pt, 'o', color=colors[idx], markersize=9, zorder=5)
        ax_rf.annotate(f"State {idx+1}\n({u_target*1e3:.2f} $\\mu$m)",
                       (u_pt, f_pt), textcoords="offset points", xytext=(0, 15),
                       ha='center', fontsize=9, fontweight='bold', color=colors[idx],
                       arrowprops=dict(arrowstyle='->', color=colors[idx], lw=1.2))

    ax_rf.set_xlabel(r'Prescribed Shear Displacement $u_x$ [$\mu\text{m}$]', fontsize=12, fontweight='bold')
    ax_rf.set_ylabel(r'Reaction Force $F_x$ [$\text{kN}$]', fontsize=12, fontweight='bold')
    ax_rf.set_title(r'Mode-II Gate M2-2: Coarse Pre-Analysis Force-Displacement Response & Target Snapshot States',
                    fontsize=14, fontweight='bold', pad=10)
    ax_rf.grid(True, linestyle=':', alpha=0.6)
    ax_rf.legend(loc='upper right', frameon=True, fontsize=11)
    ax_rf.set_xlim(0.0, 20.5)

    # 2. Middle Row: MISESERI Snapshots
    for col_idx, (tag, label_text) in enumerate(TARGET_UX_LABELS):
        ax = fig.add_subplot(gs[1, col_idx])
        tag_clean = tag.replace('.', 'p')
        mises_csv = os.path.join(data_dir, f"miseseri_snapshot_ux_{tag_clean}.csv")
        
        if os.path.exists(mises_csv):
            data = load_csv_data(mises_csv) # base_eid, layer3_eid, xc, yc, miseseri
            if data is not None and len(data) > 0:
                xc = data[:, 2]
                yc = data[:, 3]
                mises = data[:, 4]
                p99 = np.percentile(mises, 99) if len(mises) > 0 and np.max(mises) > 0 else 1.0
                norm = Normalize(vmin=0.0, vmax=max(p99, 1e-12))
                sc = ax.scatter(xc, yc, c=mises, cmap='jet', s=12, norm=norm, edgecolors='none')
                
                # Overlay Fig 6b line
                ax.plot(DIGITIZED_FIG6B[:, 0], DIGITIZED_FIG6B[:, 1], 'w--', lw=1.5, alpha=0.9)
                ax.plot([0.0, 0.5], [0.5, 0.5], 'k-', lw=2.0) # Notch
                
                if col_idx == 4:
                    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
                    cbar.set_label(r'MISESERI', fontsize=10)

        ax.set_title(f"State {col_idx+1}: {label_text.splitlines()[0]}\nMISESERI Field", fontsize=10, fontweight='bold')
        ax.set_aspect('equal')
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        if col_idx == 0:
            ax.set_ylabel(r'$y$ [$\text{mm}$]', fontsize=11, fontweight='bold')
        ax.set_xlabel(r'$x$ [$\text{mm}$]', fontsize=10)

    # 3. Bottom Row: Damage Snapshots
    for col_idx, (tag, label_text) in enumerate(TARGET_UX_LABELS):
        ax = fig.add_subplot(gs[2, col_idx])
        tag_clean = tag.replace('.', 'p')
        damage_csv = os.path.join(data_dir, f"damage_snapshot_ux_{tag_clean}.csv")
        
        if os.path.exists(damage_csv):
            data = load_csv_data(damage_csv) # base_eid, layer2_eid, xc, yc, damage
            if data is not None and len(data) > 0:
                xc = data[:, 2]
                yc = data[:, 3]
                d = data[:, 4]
                sc = ax.scatter(xc, yc, c=d, cmap='hot_r', s=12, vmin=0.0, vmax=1.0, edgecolors='none')
                
                # Overlay Fig 6b line
                ax.plot(DIGITIZED_FIG6B[:, 0], DIGITIZED_FIG6B[:, 1], 'c--', lw=1.5, alpha=0.9)
                ax.plot([0.0, 0.5], [0.5, 0.5], 'k-', lw=2.0) # Notch
                
                if col_idx == 4:
                    cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
                    cbar.set_label(r'Damage $d$', fontsize=10)

        ax.set_title(f"State {col_idx+1}: {label_text.splitlines()[0]}\nPhase Damage $d$", fontsize=10, fontweight='bold')
        ax.set_aspect('equal')
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        if col_idx == 0:
            ax.set_ylabel(r'$y$ [$\text{mm}$]', fontsize=11, fontweight='bold')
        ax.set_xlabel(r'$x$ [$\text{mm}$]', fontsize=10)

    os.makedirs(os.path.dirname(out_fig_path), exist_ok=True)
    plt.savefig(out_fig_path, dpi=300, bbox_inches='tight')
    pdf_path = os.path.splitext(out_fig_path)[0] + ".pdf"
    plt.savefig(pdf_path, bbox_inches='tight')
    plt.close()
    print(f"Generated multi-frame evolution figure:\n  PNG: {out_fig_path}\n  PDF: {pdf_path}")
    return True

if __name__ == "__main__":
    d_dir = sys.argv[1] if len(sys.argv) >= 2 else "."
    f_out = sys.argv[2] if len(sys.argv) >= 3 else "results/figures/mode2/mode2_paper_horizon_miseseri_damage_evolution.png"
    generate_evolution_figure(d_dir, f_out)
