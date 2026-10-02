#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
generate_gate6_resolution_and_divergence_figures.py
----------------------------------------------------
Generates two authoritative thesis/supervisor figures for Gate-6 Priority-A Post-Peak Audit:
1. figure_gate6_postpeak_resolution_vs_damage.png:
   - Panel (a): Mesh characteristic size h(x) and h/l0 along ligament y = 0.50 mm.
   - Panel (b): Phase-field damage profiles d(x) at checkpoints u = 0.0050, 0.0055, 0.00575, 0.0060, 0.0062 mm overlaid with crack-tip advance into coarse mesh.
2. figure_gate6_force_divergence_vs_crack_advance.png:
   - Panel (a): Load-displacement curves (1404933 vs 1404454 vs 1398090) and Delta F(u) force divergence vs Reference.
   - Panel (b): Multi-quantity checkpoint telemetry table & crack-tip position vs local h/l0.
"""

import os
import sys
import json
import math
import csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

def polygon_area(pts):
    n = len(pts)
    if n < 3:
        return 0.0
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    return abs(area) * 0.5

def load_mesh_ligament_elements(inp_path, l0=0.0075, y_band=0.015):
    nodes = {}
    elements = []
    in_node = False
    in_elem = False
    elem_type = 'CPE4'

    with open(inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_node = False
                in_elem = False
                l_up = l.upper()
                if l_up.startswith('*NODE'):
                    in_node = True
                elif l_up.startswith('*ELEMENT'):
                    in_elem = True
                    elem_type = 'CPE4'
                    parts = [p.strip() for p in l.split(',')]
                    for p in parts:
                        if p.upper().startswith('TYPE='):
                            elem_type = p.split('=')[1].strip().upper()
                continue
            
            if in_node:
                parts = [p.strip() for p in l.split(',')]
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elem:
                parts = [p.strip() for p in l.split(',')]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:] if p]
                        elements.append((eid, elem_type, conn))
                    except ValueError:
                        pass

    lig_elems = []
    for eid, etype, conn in elements:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) < 3:
            continue
        xc = sum(p[0] for p in pts) / float(len(pts))
        yc = sum(p[1] for p in pts) / float(len(pts))
        if abs(yc - 0.50) <= y_band:
            area = polygon_area(pts)
            h = math.sqrt(area) if len(pts) == 4 else math.sqrt(2.0 * area)
            lig_elems.append({
                'eid': eid, 'type': 'Q4' if len(pts) == 4 else 'T3',
                'xc': xc, 'yc': yc, 'area': area, 'h': h, 'hl0': h / l0
            })
    return lig_elems

def load_csv_curve(csv_path):
    u_vals, f_vals = [], []
    if not os.path.exists(csv_path):
        return np.array([]), np.array([])
    with open(csv_path, 'r') as f:
        reader = csv.reader(f)
        header = None
        u_col, f_col = 0, 1
        for row in reader:
            if not row or not any(c.strip() for c in row):
                continue
            if header is None:
                try:
                    float(row[0].strip())
                except ValueError:
                    header = [c.strip().lower() for c in row]
                    if 'u2_mm' in header and 'rf2_kn' in header:
                        u_col, f_col = header.index('u2_mm'), header.index('rf2_kn')
                    elif 'displacement_mm' in header and 'reaction_force_kn' in header:
                        u_col, f_col = header.index('displacement_mm'), header.index('reaction_force_kn')
                    continue
            try:
                u_vals.append(float(row[u_col]))
                f_vals.append(float(row[f_col]))
            except (ValueError, IndexError):
                continue
    paired = sorted(zip(u_vals, f_vals), key=lambda x: x[0])
    u_c, f_c = [], []
    for u, f in paired:
        if not u_c or abs(u - u_c[-1]) > 1e-12:
            u_c.append(u)
            f_c.append(f)
    return np.array(u_c), np.array(f_c)

def main():
    inp_path = 'ModeI_Supervisor_Report_Reproduction_Package/03_miseseri_native_refinement/refined_mesh/PK_MODE1_PROPOSED_PFM_PHYS_1PCT_71320.inp'
    json_path = 'docs/supervisor_reports/gate6_1404933_authoritative_evaluation.json'
    curve_933_path = 'results/pandey_kumar_mode1/master_fracture_curves/curve_1404933_extracted.csv'
    curve_454_path = 'ModeI_Supervisor_Report_Reproduction_Package/03_miseseri_native_refinement/nominal_1pct_requalification_71320/curve_1404306_extracted.csv'
    curve_ref_path = 'results/pandey_kumar_mode1/master_fracture_curves/curve_standard_1398090.csv'

    l0 = 0.0075 # mm

    print("Loading mesh and evaluation data...")
    lig_elems = load_mesh_ligament_elements(inp_path, l0=l0)
    with open(json_path, 'r') as f:
        eval_data = json.load(f)

    u_933, f_933 = load_csv_curve(curve_933_path)
    u_454, f_454 = load_csv_curve(curve_454_path)
    u_ref, f_ref = load_csv_curve(curve_ref_path)

    # -------------------------------------------------------------------------
    # FIGURE 1: Phase-Field Damage vs Local Ligament Mesh Resolution
    # -------------------------------------------------------------------------
    fig1, (ax1_top, ax1_bot) = plt.subplots(2, 1, figsize=(12, 10), dpi=300, sharex=True)
    plt.subplots_adjust(hspace=0.15)

    lig_sorted = sorted(lig_elems, key=lambda e: e['xc'])
    xs = np.array([e['xc'] for e in lig_sorted])
    hs_um = np.array([e['h'] * 1000.0 for e in lig_sorted])
    hl0s = np.array([e['hl0'] for e in lig_sorted])

    x_bins = np.linspace(0.40, 1.00, 61)
    bin_centers = 0.5 * (x_bins[:-1] + x_bins[1:])
    bin_hl0_mean = []
    bin_hl0_min = []
    bin_hl0_max = []
    for i in range(len(x_bins) - 1):
        mask = (xs >= x_bins[i]) & (xs < x_bins[i+1])
        if np.any(mask):
            bin_hl0_mean.append(np.mean(hl0s[mask]))
            bin_hl0_min.append(np.min(hl0s[mask]))
            bin_hl0_max.append(np.max(hl0s[mask]))
        else:
            bin_hl0_mean.append(np.nan)
            bin_hl0_min.append(np.nan)
            bin_hl0_max.append(np.nan)

    # Panel (a): Mesh Resolution & Sizing along Ligament
    ax1_top.scatter(xs, hl0s, color='tab:gray', alpha=0.3, s=8, label='Individual Element $h/\\ell_0$')
    ax1_top.plot(bin_centers, bin_hl0_mean, color='black', linewidth=2.0, label='Mean $h/\\ell_0$ Profile')
    ax1_top.fill_between(bin_centers, bin_hl0_min, bin_hl0_max, color='gray', alpha=0.2, label='Min-Max Range')

    ax1_top.axhline(0.40, color='tab:green', linestyle='--', linewidth=1.5, label='Recommended Limit ($h/\\ell_0 \\leq 0.40$)')
    ax1_top.axhline(1.00, color='tab:red', linestyle=':', linewidth=1.5, label='Critical Inadequacy Boundary ($h = \\ell_0$)')
    ax1_top.axvline(0.50, color='black', linestyle=':', linewidth=1.0, label='Initial Slit Tip ($x=0.50$ mm)')

    ax1_top.axvspan(0.80, 0.98, color='tab:red', alpha=0.08, label='Downstream Coarsened Zone ($x > 0.80$ mm)')
    ax1_top.plot(0.941, 0.70, 'r*', markersize=12, label='Later 1404454 Failure Site (Node 61805, $x=0.941$)')

    ax1_top.set_ylabel('Discretization Ratio $h/\\ell_0$ [-]', fontsize=11, fontweight='bold')
    ax1_top.set_title('(a) Local Mesh Resolution $h/\\ell_0$ along Ligament ($|y - 0.50| \\leq 0.015$ mm)', fontsize=12, fontweight='bold')
    ax1_top.set_ylim(0.0, 1.25)
    ax1_top.grid(True, linestyle=':', alpha=0.6)
    ax1_top.legend(loc='upper left', fontsize=8.5, framealpha=0.9, ncol=2)

    # Panel (b): Damage Evolution Profiles d(x) at Checkpoints
    cps = ['0.005000', '0.005500', '0.005750', '0.006000', '0.006200']
    colors = ['tab:blue', 'tab:cyan', 'tab:orange', 'tab:red', 'tab:purple']
    labels = [
        '$u = 5.00\\ \\mu\\mathrm{m}$ (Elastic, $d_{\\max}=0.31$, Tip at $x=0.50$)',
        '$u = 5.50\\ \\mu\\mathrm{m}$ (Nonlinear, $d_{\\max}=0.44$, Tip at $x=0.50$)',
        '$u = 5.75\\ \\mu\\mathrm{m}$ (Peak Load, $d_{\\max}=0.62$, Tip at $x=0.50$)',
        '$u = 6.00\\ \\mu\\mathrm{m}$ (Post-Peak, $d_{\\max}=1.00$, Front $x=0.795$ mm)',
        '$u = 6.20\\ \\mu\\mathrm{m}$ (Truncated, $d_{\\max}=1.00$, Front $x=0.811$ mm)'
    ]

    for cp_k, col, lbl in zip(cps, colors, labels):
        if cp_k in eval_data['damage_field_checkpoints']:
            cp_data = eval_data['damage_field_checkpoints'][cp_k]
            ridge = cp_data.get('ridge_points', [])
            if ridge:
                rx = [p['x'] for p in ridge]
                rd = [p['d'] for p in ridge]
                ax1_bot.plot(rx, rd, '.-', color=col, linewidth=1.6, markersize=5, label=lbl)

    ax1_bot.axhline(0.90, color='gray', linestyle='--', linewidth=1.0, label='Crack Tip Threshold ($d=0.90$)')
    ax1_bot.axvline(0.50, color='black', linestyle=':', linewidth=1.0)
    ax1_bot.axvspan(0.80, 0.98, color='tab:red', alpha=0.08)

    ax1_bot.set_xlabel('Ligament Coordinate $x$ [mm] (along $y = 0.50$ mm)', fontsize=11, fontweight='bold')
    ax1_bot.set_ylabel('Phase-Field Damage $d$ [-]', fontsize=11, fontweight='bold')
    ax1_bot.set_title('(b) Phase-Field Spatial Damage Evolution $d(x)$ across Checkpoints', fontsize=12, fontweight='bold')
    ax1_bot.set_xlim(0.40, 1.00)
    ax1_bot.set_ylim(-0.05, 1.08)
    ax1_bot.grid(True, linestyle=':', alpha=0.6)
    ax1_bot.legend(loc='upper right', fontsize=8.5, framealpha=0.9)

    out_fig1 = 'docs/thesis/figures/figure_gate6_postpeak_resolution_vs_damage.png'
    out_fig1_rep = 'docs/supervisor_reports/figure_gate6_postpeak_resolution_vs_damage.png'
    os.makedirs(os.path.dirname(out_fig1), exist_ok=True)
    os.makedirs(os.path.dirname(out_fig1_rep), exist_ok=True)
    fig1.savefig(out_fig1, dpi=300)
    fig1.savefig(out_fig1_rep, dpi=300)
    plt.close(fig1)
    print("Saved Figure 1 to:\n  - %s\n  - %s" % (out_fig1, out_fig1_rep))

    # -------------------------------------------------------------------------
    # FIGURE 2: Force Divergence vs Crack-Tip Advance & Resolution
    # -------------------------------------------------------------------------
    fig2, (ax2_top, ax2_bot) = plt.subplots(2, 1, figsize=(12, 10), dpi=300)
    plt.subplots_adjust(hspace=0.28)

    ax2_top.plot(u_ref * 1000, f_ref, color='black', linewidth=2.0, label='Fixed Reference 1398090 ($15,192$ elem, $K_0=137.95$)')
    ax2_top.plot(u_454 * 1000, f_454, color='tab:green', linewidth=1.6, alpha=0.7, label='Production 1404454 ($71,320$ elem)')
    ax2_top.plot(u_933 * 1000, f_933, color='tab:blue', linestyle=':', linewidth=2.2, label='Strict Diagnostic Twin 1404933 (Trunc. $u=6.2\\ \\mu\\mathrm{m}$)')

    cp_u_arr = [0.0050, 0.0055, 0.00575, 0.0060, 0.0062]
    cp_f_arr = [0.661366, 0.719700, 0.745325, 0.351167, 0.335775]
    ax2_top.plot(np.array(cp_u_arr) * 1000, cp_f_arr, 'ro', markersize=6, label='SDV14 Checkpoints ($u=5.0, 5.5, 5.75, 6.0, 6.2\\ \\mu\\mathrm{m}$)')

    ax2_top.set_xlabel('Prescribed Displacement $u$ [$\\mu\\mathrm{m}$]', fontsize=11, fontweight='bold')
    ax2_top.set_ylabel('Reaction Force $F$ [kN]', fontsize=11, fontweight='bold')
    ax2_top.set_title('(a) Global Load-Displacement Response & Checkpoint Displacements', fontsize=12, fontweight='bold')
    ax2_top.set_xlim(0, 8.0)
    ax2_top.set_ylim(0, 0.85)
    ax2_top.grid(True, linestyle=':', alpha=0.6)
    ax2_top.legend(loc='lower left', fontsize=8.5, framealpha=0.9)

    ax2_inset = ax2_top.inset_axes([0.55, 0.45, 0.42, 0.45])
    u_common = u_933[u_933 <= min(u_933[-1], u_ref[-1])]
    f_cand = f_933[u_933 <= min(u_933[-1], u_ref[-1])]
    f_ref_interp = np.interp(u_common, u_ref, f_ref)
    delta_F_N = (f_cand - f_ref_interp) * 1000.0

    ax2_inset.plot(u_common * 1000, delta_F_N, color='tab:red', linewidth=1.5, label='$F_{\\mathrm{adapt}} - F_{\\mathrm{ref}}$ [N]')
    ax2_inset.axhline(0, color='black', linestyle='--', linewidth=0.8)
    ax2_inset.set_title('Force Difference vs Ref [N]', fontsize=8.5, fontweight='bold')
    ax2_inset.set_xlabel('$u$ [$\\mu\\mathrm{m}$]', fontsize=7.5)
    ax2_inset.set_ylabel('$\\Delta F$ [N]', fontsize=7.5)
    ax2_inset.tick_params(labelsize=7)
    ax2_inset.grid(True, linestyle=':', alpha=0.5)

    ax2_bot.axis('off')
    
    table_data = [
        ['Checkpoint Metric', 'u = 5.00 um', 'u = 5.50 um', 'u = 5.75 um (Peak)', 'u = 6.00 um', 'u = 6.20 um (Trunc.)'],
        ['Reaction Force F [kN]', '0.6614', '0.7197', '0.7453', '0.3512', '0.3358'],
        ['Delta F vs Ref 1398090 [N]', '-0.24 N (-0.04%)', '-0.54 N (-0.08%)', '-4.81 N (-0.64%)', '-272.32 N (-43.7%)', '-127.41 N (-27.5%)'],
        ['Peak Damage d_max', '0.3124', '0.4390', '0.6201', '1.0022', '1.0024'],
        ['Crack-Tip Position x (d>=0.90)', 'Slit (x=0.500 mm)', 'Slit (x=0.501 mm)', 'Slit (x=0.501 mm)', 'x = 0.7955 mm', 'x = 0.8109 mm'],
        ['Local h/l0 at Active Tip', '0.236 (h = 1.77 um)', '0.236 (h = 1.77 um)', '0.236 (h = 1.77 um)', '0.537 (h = 4.03 um)', '0.787 (h = 5.90 um)'],
        ['Elements in 2*l0 Zone', '8.5 elems', '8.5 elems', '8.5 elems', '3.7 elems', '2.5 elems'],
        ['Localization Width FWHM (x=0.55)', '0.060 mm (Diffuse)', '0.055 mm (Diffuse)', '0.050 mm (Diffuse)', '0.021 mm (2.8 l0)', '0.021 mm (2.8 l0)'],
        ['Max Path Deviation |Dy|_max', '0.0013 mm', '0.0014 mm', '0.0014 mm', '0.0046 mm', '0.0071 mm (< l0)'],
        ['Downstream State (x > 0.80)', 'Far-field (d < 0.02)', 'Far-field (d < 0.02)', 'Far-field (d < 0.02)', 'Crack tip arriving', 'Crack tip advancing']
    ]

    table = ax2_bot.table(
        cellText=table_data, 
        loc='center', 
        cellLoc='center',
        colWidths=[0.24, 0.15, 0.15, 0.16, 0.15, 0.15]
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8.2)
    table.scale(1.0, 1.8)

    for i in range(6):
        cell = table[(0, i)]
        cell.set_facecolor('#2c3e50')
        cell.set_text_props(color='white', fontweight='bold')
    
    for j in range(6):
        table[(5, j)].set_facecolor('#fdedec')
        table[(6, j)].set_facecolor('#fdedec')

    ax2_bot.set_title('(b) Multi-Quantity Telemetry & Crack-Tip Resolution Audit across Checkpoints', fontsize=12, fontweight='bold', pad=15)

    out_fig2 = 'docs/thesis/figures/figure_gate6_force_divergence_vs_crack_advance.png'
    out_fig2_rep = 'docs/supervisor_reports/figure_gate6_force_divergence_vs_crack_advance.png'
    os.makedirs(os.path.dirname(out_fig2), exist_ok=True)
    os.makedirs(os.path.dirname(out_fig2_rep), exist_ok=True)
    fig2.savefig(out_fig2, dpi=300)
    fig2.savefig(out_fig2_rep, dpi=300)
    plt.close(fig2)
    print("Saved Figure 2 to:\n  - %s\n  - %s" % (out_fig2, out_fig2_rep))

if __name__ == '__main__':
    main()
