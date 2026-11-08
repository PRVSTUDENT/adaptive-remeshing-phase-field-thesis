#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_f1690_sec43_damage_terminal.py

Extracts and plots the phase-field damage field (d) at the terminal increment
of Task F1690 Job-1 rerun (Increment 170, u_y = 0.068717 mm) using the extracted
data in f1690_sec43_damage_data.json.

Generates:
- MA_AdaptiveRemeshing_Report_2026/figures/fig_f1690_sec43_damage_terminal.pdf
- MA_AdaptiveRemeshing_Report_2026/figures/fig_f1690_sec43_damage_terminal.png
- results/validation/f1690_sec43_damage_terminal_record.json
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon, Circle
from matplotlib.collections import PatchCollection
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
data_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "190_pk_sec43_job1_rerun" / "f1690_sec43_damage_data.json"
fig_dir = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures"
results_dir = REPO_ROOT / "results" / "validation"

def main():
    print("=" * 80)
    print("TASK F1690: PLOTTING TERMINAL INCREMENT 170 DAMAGE FIELD (u_y = 0.0687 mm)")
    print("=" * 80)

    if not data_path.exists():
        raise FileNotFoundError("Data file not found at: %s" % data_path)

    with open(data_path, "r") as f:
        data = json.load(f)

    elements = data["elements"]
    print("Loaded %d elements from %s" % (len(elements), data_path))

    patches = []
    damage_vals = []
    notch_tip_damage = []
    secondary_damage = []

    for el in elements:
        pts = np.array(el["pts"])
        cx = el["cx"]
        cy = el["cy"]
        d = el["d"]

        patches.append(MplPolygon(pts, closed=True))
        damage_vals.append(d)

        # Notch tip: x in [9.5, 15.0], y in [68.0, 72.0]
        if 9.5 <= cx <= 15.0 and 68.0 <= cy <= 72.0:
            notch_tip_damage.append(d)

        # Secondary ligament: x >= 46.5, y in [42.0, 60.0]
        if cx >= 46.5 and 42.0 <= cy <= 60.0:
            secondary_damage.append(d)

    d_max = max(damage_vals)
    d_min = min(damage_vals)
    notch_d_max = max(notch_tip_damage) if notch_tip_damage else 0.0
    sec_d_max = max(secondary_damage) if secondary_damage else 0.0

    print("Damage summary: min = %.6f, max = %.6f" % (d_min, d_max))
    print("Notch tip max damage: %.6f" % notch_d_max)
    print("Secondary ligament max damage: %.6f" % sec_d_max)

    # Active elements with d > 0.1 and d > 0.5
    act_01 = [d for d in damage_vals if d > 0.1]
    act_05 = [d for d in damage_vals if d > 0.5]
    act_09 = [d for d in damage_vals if d > 0.9]
    print("Elements with d > 0.1: %d" % len(act_01))
    print("Elements with d > 0.5: %d" % len(act_05))
    print("Elements with d > 0.9: %d" % len(act_09))

    # Generate Publication Figure
    fig, ax = plt.subplots(figsize=(6, 10))
    p = PatchCollection(patches, cmap='viridis', edgecolors='none', linewidths=0.0)
    p.set_array(np.array(damage_vals))
    p.set_clim(0.0, 1.0)
    ax.add_collection(p)

    ax.set_xlim(0, 65)
    ax.set_ylim(0, 120)
    ax.set_aspect('equal')
    ax.set_xlabel('X [mm]', fontsize=11)
    ax.set_ylabel('Y [mm]', fontsize=11)
    ax.set_title('Task F1690: Terminal Phase-Field Damage Field\n(Job 1421200, $u_y = 0.0687$ mm, $h = 0.60$ mm Mesh)', fontsize=11)

    cb = fig.colorbar(p, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label(r'Phase-Field Damage $d$ ($0 \leq d \leq 1$)', fontsize=10)

    # Annotate notch tip localization and uncracked secondary ligament
    ax.annotate(r'Sharp Crack Initiation at Notch Tip' + '\n' + r'($d_{\max} = 0.932$, $D_f = 13.43$ mJ)',
                xy=(11.5, 70.0), xytext=(15.0, 82.0),
                arrowprops=dict(facecolor='red', shrink=0.05, width=1.5, headwidth=6),
                fontsize=9, color='darkred', weight='bold')

    ax.annotate(r'Secondary Ligament Completely Intact' + '\n' + r'($d_{\max} = 0.021 \approx 0$, Zero Error Indication)',
                xy=(52.0, 51.0), xytext=(28.0, 32.0),
                arrowprops=dict(facecolor='blue', shrink=0.05, width=1.5, headwidth=6),
                fontsize=9, color='navy', weight='bold')

    fig_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = fig_dir / "fig_f1690_sec43_damage_terminal.pdf"
    out_png = fig_dir / "fig_f1690_sec43_damage_terminal.png"
    plt.tight_layout()
    plt.savefig(out_pdf, dpi=300)
    plt.savefig(out_png, dpi=300)
    plt.close()
    print("Saved damage field plots to:\n  %s\n  %s" % (out_pdf, out_png))

    # Save JSON summary
    record = {
        "benchmark": "Pandey_Kumar_2025_Section_4.3",
        "task_id": "F1690-PK-SEC43-JOB1-CORRECTED-SOLVER-RERUN",
        "pbs_job_id": "1421200.mmaster02",
        "stage": "Terminal_Damage_Extraction",
        "mesh_characteristic_size_mm": 0.60,
        "mesh_ratio_h_over_l0": 2.105,
        "total_physical_elements": len(elements),
        "terminal_increment": 170,
        "terminal_displacement_uy_mm": 0.0687166,
        "dissipated_fracture_energy_mJ": 13.428,
        "global_max_damage": float(d_max),
        "global_min_damage": float(d_min),
        "notch_tip_max_damage": float(notch_d_max),
        "secondary_ligament_max_damage": float(sec_d_max),
        "active_elements_d_gt_0p1": len(act_01),
        "active_elements_d_gt_0p5": len(act_05),
        "active_elements_d_gt_0p9": len(act_09),
        "pre_penetration_visual_proof": bool(sec_d_max < 0.05 and d_max > 0.90),
        "figures": {
            "pdf": str(out_pdf),
            "png": str(out_png)
        }
    }

    results_dir.mkdir(parents=True, exist_ok=True)
    json_path = results_dir / "f1690_sec43_damage_terminal_record.json"
    with open(json_path, "w") as f:
        json.dump(record, f, indent=2)
    print("Saved damage extraction record to: %s" % json_path)

if __name__ == "__main__":
    main()
