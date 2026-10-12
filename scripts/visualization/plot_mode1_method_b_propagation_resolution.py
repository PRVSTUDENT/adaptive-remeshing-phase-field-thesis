#!/usr/bin/env python3
"""
plot_mode1_method_b_propagation_resolution.py
---------------------------------------------
Publication-quality visualization and comparative analysis of Method B crack-propagation
spatial resolution along the forward ligament (0.5 < x <= 1.0 mm, y = 0.5 mm) for the
Pandey--Kumar Mode-I fracture benchmark.

Produces two publication figures:
1. fig_mode1_method_b_propagation_resolution.png / .pdf
   - 4-panel synthesis:
     (a) Longitudinal element size h(x) along ligament corridor vs l0 and l0/2 thresholds
     (b) Elements per phase-field length scale l0 / h(x)
     (c) Propagating phase-field damage profiles d(x, y=0.5) from numerical evidence
     (d) Global F-u curve highlighting initiation (fine) vs plateau (coarse pinning)
2. fig_mode1_method_b_propagation_ligament_zoom.png / .pdf
   - Magnified mesh corridor (0.48 <= x <= 0.85 mm, 0.44 <= y <= 0.56 mm) with
     element edges, element size color mapping, initial crack seam, and overlaid
     crack-tip progression points.
"""

import os
import sys
import math
import csv
import json
import numpy as np

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.patches as patches
from matplotlib.lines import Line2D

# File paths
REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_FINAL_1S.inp")
STATES_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_14K_matched_states_summary.csv")
LIGAMENT_PROFILES_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_14K_ligament_profiles.csv")
MB_FU_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "38_method_b_native_final_14k", "M1_MB_NATIVE_14K_fu.csv")
REF_FU_PATH = os.path.join(REPO_ROOT, "results", "pandey_kumar_mode1", "gate1_harmonized", "job_1401091_fu.csv")

OUT_DIR = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_mesh")

L0 = 0.0075  # mm (7.5 um)

def parse_abaqus_mesh(inp_path):
    nodes = {}
    quads = []
    tris = []
    
    with open(inp_path, 'r') as f:
        sec = None
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                up = l.upper()
                if up == '*NODE' or up.startswith('*NODE,'):
                    sec = 'NODE'
                elif up.startswith('*ELEMENT, TYPE=U1') or up.startswith('*ELEMENT, TYPE=CPE4') and not quads:
                    sec = 'U1'
                elif up.startswith('*ELEMENT, TYPE=U3') or up.startswith('*ELEMENT, TYPE=CPE3') and not tris:
                    sec = 'U3'
                elif up.startswith('*STEP'):
                    break
                else:
                    sec = None
            else:
                if sec == 'NODE':
                    parts = l.split(',')
                    nid = int(parts[0].strip())
                    if nid not in (999999, 1000000):
                        nodes[nid] = (float(parts[1].strip()), float(parts[2].strip()))
                elif sec == 'U1':
                    parts = l.split(',')
                    eid = int(parts[0].strip())
                    conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                    quads.append((eid, conn))
                elif sec == 'U3':
                    parts = l.split(',')
                    eid = int(parts[0].strip())
                    conn = [int(p.strip()) for p in parts[1:] if p.strip()]
                    tris.append((eid, conn))

    return nodes, quads, tris

def polygon_area(pts):
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1]
        area -= pts[j][0] * pts[i][1]
    return abs(area) / 2.0

def build_element_records(nodes, quads, tris):
    elements = []
    for eid, conn in quads:
        pts = [nodes[n] for n in conn]
        area = polygon_area(pts)
        h = math.sqrt(area)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx = sum(xs) / 4.0
        cy = sum(ys) / 4.0
        elements.append({
            'eid': eid,
            'type': 'QUAD',
            'pts': pts,
            'area': area,
            'h_um': h * 1000.0,
            'cx': cx,
            'cy': cy,
            'l0_over_h': (L0 * 1000.0) / (h * 1000.0)
        })
    for eid, conn in tris:
        pts = [nodes[n] for n in conn]
        area = polygon_area(pts)
        h = math.sqrt(area)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx = sum(xs) / 3.0
        cy = sum(ys) / 3.0
        elements.append({
            'eid': eid,
            'type': 'TRI',
            'pts': pts,
            'area': area,
            'h_um': h * 1000.0,
            'cx': cx,
            'cy': cy,
            'l0_over_h': (L0 * 1000.0) / (h * 1000.0)
        })
    return elements

def load_ligament_profiles(csv_path):
    profiles = {}
    if not os.path.exists(csv_path):
        return profiles
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            u_act = float(row['actual_u_mm'])
            x = float(row['x_coord'])
            y = float(row['y_coord'])
            d = float(row['damage_d'])
            if abs(y - 0.5) <= 0.015:
                profiles.setdefault(round(u_act, 6), []).append((x, d))
    for u_key in profiles:
        profiles[u_key].sort(key=lambda item: item[0])
    return profiles

def load_fu_curve(csv_path):
    u_vals, f_vals = [], []
    if not os.path.exists(csv_path):
        return u_vals, f_vals
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        u_col = None
        f_col = None
        for col in reader.fieldnames:
            if 'u' in col.lower() or 'disp' in col.lower():
                u_col = col
            if 'f' in col.lower() or 'rf' in col.lower() or 'force' in col.lower():
                f_col = col
        if u_col and f_col:
            for row in reader:
                try:
                    u_vals.append(float(row[u_col]))
                    f_vals.append(float(row[f_col]))
                except ValueError:
                    continue
    return u_vals, f_vals

def plot_propagation_resolution_synthesis(elements, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    lig_elems = [el for el in elements if 0.48 <= el['cx'] <= 1.00 and abs(el['cy'] - 0.5) <= 0.025]
    lig_elems.sort(key=lambda el: el['cx'])
    
    xs = np.array([el['cx'] for el in lig_elems])
    hs = np.array([el['h_um'] for el in lig_elems])
    l0_hs = np.array([el['l0_over_h'] for el in lig_elems])
    
    bin_edges = np.linspace(0.48, 1.00, 53)
    bin_centers = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    h_medians, h_p10, h_p90 = [], [], []
    l0h_medians, l0h_p10, l0h_p90 = [], [], []
    
    for i in range(len(bin_centers)):
        x_lo = bin_edges[i]
        x_hi = bin_edges[i+1]
        mask = (xs >= x_lo) & (xs < x_hi)
        if np.sum(mask) > 0:
            sub_h = hs[mask]
            sub_l0h = l0_hs[mask]
            h_medians.append(np.median(sub_h))
            h_p10.append(np.percentile(sub_h, 10))
            h_p90.append(np.percentile(sub_h, 90))
            l0h_medians.append(np.median(sub_l0h))
            l0h_p10.append(np.percentile(sub_l0h, 10))
            l0h_p90.append(np.percentile(sub_l0h, 90))
        else:
            h_medians.append(np.nan)
            h_p10.append(np.nan)
            h_p90.append(np.nan)
            l0h_medians.append(np.nan)
            l0h_p10.append(np.nan)
            l0h_p90.append(np.nan)
            
    bin_centers = np.array(bin_centers)
    h_medians = np.array(h_medians)
    h_p10 = np.array(h_p10)
    h_p90 = np.array(h_p90)
    l0h_medians = np.array(l0h_medians)
    l0h_p10 = np.array(l0h_p10)
    l0h_p90 = np.array(l0h_p90)

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14.0, 10.5), dpi=300)
    plt.subplots_adjust(hspace=0.28, wspace=0.22, top=0.93, bottom=0.08, left=0.08, right=0.96)
    
    fig.suptitle("Pandey--Kumar Mode-I Benchmark: Method B Native Adapted Mesh\n"
                 "Crack-Propagation Corridor Spatial Resolution and Damage Field Audit",
                 fontsize=14, fontweight='bold', color='#1D3557', y=0.98)

    # -------------------------------------------------------------
    # Panel (a): Element Characteristic Size h(x)
    # -------------------------------------------------------------
    ax1.axvspan(0.50, 0.57, color='#E8F5E9', alpha=0.7, label=r'Well-Resolved Zone ($h \leq l_0/2$, $l_0/h \geq 2$)')
    ax1.axvspan(0.57, 0.65, color='#FFF9C4', alpha=0.7, label=r'Transition Zone ($l_0/2 < h \leq l_0$)')
    ax1.axvspan(0.65, 1.00, color='#FFEBEE', alpha=0.7, label=r'Coarse Pinning Zone ($h > l_0$, $l_0/h < 1$)')
    
    ax1.scatter(xs, hs, s=12, color='#457B9D', alpha=0.35, edgecolors='none', label=r'Adapted Finite Elements ($|y-0.5| \leq 25\ \mu\mathrm{m}$)')
    
    valid = ~np.isnan(h_medians)
    ax1.fill_between(bin_centers[valid], h_p10[valid], h_p90[valid], color='#1D3557', alpha=0.18, label='P10--P90 Sizing Band')
    ax1.plot(bin_centers[valid], h_medians[valid], color='#1D3557', linewidth=2.4, label='Median Element Size $h(x)$')
    
    ax1.axhline(7.5, color='#D90429', linestyle='--', linewidth=1.8, label=r'Phase-Field Length $l_0 = 7.5\ \mu\mathrm{m}$')
    ax1.axhline(3.75, color='#E76F51', linestyle='-.', linewidth=1.6, label=r'Fixed-Mesh Ref. $h_{\mathrm{ref}} = 3.75\ \mu\mathrm{m}$')
    ax1.axhline(2.50, color='#2A9D8F', linestyle=':', linewidth=1.5, label=r'Fine Discretization $l_0/3 = 2.5\ \mu\mathrm{m}$')
    
    stages = [
        (0.5000, "Peak: $u=0.0057$\n$h=1.92\\ \\mu\\mathrm{m}$", '#1B4332', (0.50, 4.5)),
        (0.6123, "Post-Peak: $u=0.0059$\n$h=5.16\\ \\mu\\mathrm{m}$", '#D90429', (0.61, 11.5)),
        (0.7081, "Plateau: $u=0.0070$\n$h=10.35\\ \\mu\\mathrm{m}$", '#7209B7', (0.71, 15.0))
    ]
    for x_pt, text, col, text_pos in stages:
        ax1.plot(x_pt, 7.5, marker='v', markersize=8, color=col)
        ax1.annotate(text, xy=(x_pt, 7.5), xytext=text_pos,
                     arrowprops=dict(arrowstyle="->", color=col, lw=1.2),
                     fontsize=8.5, fontweight='bold', color=col,
                     bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor=col, alpha=0.9))

    ax1.set_xlim(0.48, 1.00)
    ax1.set_ylim(0.0, 20.0)
    ax1.set_xlabel(r'Longitudinal Coordinate $x$ [mm]', fontsize=10.5, fontweight='bold')
    ax1.set_ylabel(r'Characteristic Size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=10.5, fontweight='bold')
    ax1.set_title('(a) Longitudinal Sizing Profile along Crack Propagation Corridor', fontsize=11, fontweight='bold', color='#1D3557')
    ax1.grid(True, linestyle=':', alpha=0.6)
    ax1.legend(loc='upper left', fontsize=7.5, framealpha=0.92)

    # -------------------------------------------------------------
    # Panel (b): Elements per Phase-Field Length Scale (l0 / h)
    # -------------------------------------------------------------
    ax2.axvspan(0.50, 0.57, color='#E8F5E9', alpha=0.7)
    ax2.axvspan(0.57, 0.65, color='#FFF9C4', alpha=0.7)
    ax2.axvspan(0.65, 1.00, color='#FFEBEE', alpha=0.7)
    
    ax2.scatter(xs, l0_hs, s=12, color='#2A9D8F', alpha=0.35, edgecolors='none')
    ax2.fill_between(bin_centers[valid], l0h_p10[valid], l0h_p90[valid], color='#264653', alpha=0.18)
    ax2.plot(bin_centers[valid], l0h_medians[valid], color='#264653', linewidth=2.4, label='Median $l_0 / h(x)$')
    
    ax2.axhline(3.0, color='#2A9D8F', linestyle=':', linewidth=1.5, label='Optimal Resolution ($l_0/h = 3$)')
    ax2.axhline(2.0, color='#E76F51', linestyle='-.', linewidth=1.6, label='Adequate Resolution ($l_0/h = 2$, Reference)')
    ax2.axhline(1.0, color='#D90429', linestyle='--', linewidth=1.8, label='Minimum Limit ($l_0/h = 1$, Coarse Pinning Threshold)')
    
    ax2.annotate(r"$\mathbf{l_0 / h_{tip} \approx 3.91}$" + "\n(Initiation Well-Resolved)", xy=(0.505, 3.9), xytext=(0.53, 4.3),
                 arrowprops=dict(arrowstyle="->", color='#1B4332', lw=1.2),
                 fontsize=8.5, fontweight='bold', color='#1B4332',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#1B4332', alpha=0.9))
                 
    ax2.annotate(r"$\mathbf{l_0 / h \approx 0.72}$" + "\n(Severe Under-Resolution)", xy=(0.708, 0.72), xytext=(0.73, 1.8),
                 arrowprops=dict(arrowstyle="->", color='#D90429', lw=1.2),
                 fontsize=8.5, fontweight='bold', color='#D90429',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#D90429', alpha=0.9))

    ax2.set_xlim(0.48, 1.00)
    ax2.set_ylim(0.0, 5.5)
    ax2.set_xlabel(r'Longitudinal Coordinate $x$ [mm]', fontsize=10.5, fontweight='bold')
    ax2.set_ylabel(r'Elements per Characteristic Length $l_0 / h$', fontsize=10.5, fontweight='bold')
    ax2.set_title('(b) Phase-Field Discretization Density along Forward Ligament', fontsize=11, fontweight='bold', color='#1D3557')
    ax2.grid(True, linestyle=':', alpha=0.6)
    ax2.legend(loc='upper right', fontsize=8.0, framealpha=0.92)

    # -------------------------------------------------------------
    # Panel (c): Propagating Phase-Field Damage Profiles d(x, y=0.5)
    # -------------------------------------------------------------
    profiles = load_ligament_profiles(LIGAMENT_PROFILES_PATH)
    
    key_stages = [
        (0.005000, r'Pre-Peak: $u=0.0050$ mm', '#457B9D', '--', 1.6),
        (0.005727, r'Peak Load: $u=0.0057$ mm ($F_{\mathrm{max}}=0.743$ kN)', '#1B4332', '-', 2.2),
        (0.005857, r'Post-Peak: $u=0.0059$ mm', '#E76F51', '-', 1.8),
        (0.006500, r'Propagation: $u=0.0065$ mm', '#D90429', '-', 1.8),
        (0.007000, r'Mid-Plateau: $u=0.0070$ mm', '#7209B7', '-', 2.0),
        (0.007500, r'Late Plateau: $u=0.0075$ mm', '#3A0CA3', '-', 1.8),
        (0.008000, r'Snap-Through: $u=0.0080$ mm', '#000000', ':', 1.8)
    ]
    
    ax3.axvspan(0.50, 0.57, color='#E8F5E9', alpha=0.7)
    ax3.axvspan(0.57, 0.65, color='#FFF9C4', alpha=0.7)
    ax3.axvspan(0.65, 1.00, color='#FFEBEE', alpha=0.7)
    
    for u_val, lbl, col, lstyle, lw in key_stages:
        if u_val in profiles:
            px = [pt[0] for pt in profiles[u_val] if pt[0] >= 0.49]
            pd = [pt[1] for pt in profiles[u_val] if pt[0] >= 0.49]
            ax3.plot(px, pd, label=lbl, color=col, linestyle=lstyle, linewidth=lw)

    ax3.axhline(0.90, color='#666666', linestyle=':', linewidth=1.2, label=r'Crack Threshold ($d \geq 0.90$)')
    ax3.set_xlim(0.48, 1.00)
    ax3.set_ylim(-0.02, 1.05)
    ax3.set_xlabel(r'Longitudinal Coordinate $x$ [mm]', fontsize=10.5, fontweight='bold')
    ax3.set_ylabel(r'Phase-Field Damage $d(x, y=0.5\ \mathrm{mm})$', fontsize=10.5, fontweight='bold')
    ax3.set_title('(c) Crack Front Propagation through Sizing Zones', fontsize=11, fontweight='bold', color='#1D3557')
    ax3.grid(True, linestyle=':', alpha=0.6)
    ax3.legend(loc='lower left', fontsize=7.5, framealpha=0.92)

    # -------------------------------------------------------------
    # Panel (d): Global Reaction Force vs Displacement F(u)
    # -------------------------------------------------------------
    u_mb, f_mb = load_fu_curve(MB_FU_PATH)
    u_ref, f_ref = load_fu_curve(REF_FU_PATH)
    
    if u_ref and f_ref:
        ax4.plot(np.array(u_ref)*1000.0, f_ref, color='#1D3557', linestyle='--', linewidth=2.0, label=r'Fixed-Mesh Ref. (15,192 FE, $h=3.75\ \mu\mathrm{m}$)')
    if u_mb and f_mb:
        ax4.plot(np.array(u_mb)*1000.0, f_mb, color='#D90429', linestyle='-', linewidth=2.2, label='Method B Native Adapted (14,677 FE)')
        
    ax4.axvspan(0.0, 5.8, color='#E8F5E9', alpha=0.6, label=r'Initiation Phase ($h \leq 3.75\ \mu\mathrm{m}$, $|\Delta F_{\max}| < 2\%$)')
    ax4.axvspan(5.8, 8.0, color='#FFEBEE', alpha=0.6, label=r'Propagation Plateau ($h > 7.5\ \mu\mathrm{m}$, Coarse Pinning)')
    
    ax4.annotate(r"$\mathbf{F_{\mathrm{max}} = 0.7430}$ kN" + "\n" + r"($-1.95\%$ vs Ref)" + "\n" + r"Governed by $h_{\mathrm{tip}}=1.9\ \mu\mathrm{m}$",
                 xy=(5.73, 0.743), xytext=(2.2, 0.65),
                 arrowprops=dict(arrowstyle="->", color='#1B4332', lw=1.2),
                 fontsize=8.5, fontweight='bold', color='#1B4332',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#1B4332', alpha=0.9))
                 
    ax4.annotate("Elevated Post-Peak Force\nDue to Coarse Ligament ($h > l_0$)\nPinning regularized gradient",
                 xy=(6.8, 0.54), xytext=(6.5, 0.28),
                 arrowprops=dict(arrowstyle="->", color='#D90429', lw=1.2),
                 fontsize=8.5, fontweight='bold', color='#D90429',
                 bbox=dict(boxstyle="round,pad=0.2", facecolor='white', edgecolor='#D90429', alpha=0.9))

    ax4.set_xlim(0.0, 10.0)
    ax4.set_ylim(0.0, 0.85)
    ax4.set_xlabel(r'Prescribed Displacement $u$ [$\mu$m]', fontsize=10.5, fontweight='bold')
    ax4.set_ylabel(r'Reaction Force $F$ [kN]', fontsize=10.5, fontweight='bold')
    ax4.set_title('(d) Global Structural Response: Initiation vs Propagation Sensitivity', fontsize=11, fontweight='bold', color='#1D3557')
    ax4.grid(True, linestyle=':', alpha=0.6)
    ax4.legend(loc='lower left', fontsize=7.8, framealpha=0.92)

    # Save figures
    png_path = os.path.join(out_dir, "fig_mode1_method_b_propagation_resolution.png")
    pdf_path = os.path.join(out_dir, "fig_mode1_method_b_propagation_resolution.pdf")
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Generated Figure 1: {png_path} and {pdf_path}")


def plot_propagation_ligament_zoom(elements, nodes, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    
    zoom_elems = [el for el in elements if 0.47 <= el['cx'] <= 0.85 and 0.43 <= el['cy'] <= 0.57]
    
    fig, ax = plt.subplots(figsize=(13.0, 6.5), dpi=300)
    plt.subplots_adjust(top=0.91, bottom=0.12, left=0.08, right=0.90)
    
    verts = [el['pts'] for el in zoom_elems]
    hs = np.array([el['h_um'] for el in zoom_elems])
    
    norm = matplotlib.colors.Normalize(vmin=1.5, vmax=15.0)
    cmap = plt.cm.viridis
    colors = cmap(norm(hs))
    
    pc = PolyCollection(verts, facecolors=colors, edgecolors='#222222', linewidths=0.25, alpha=0.95)
    ax.add_collection(pc)
    
    ax.plot([0.47, 0.50], [0.50, 0.50], color='#D90429', linewidth=3.2, zorder=6, label=r'Initial Crack Slit ($a_0 = 0.5$ mm)')
    ax.plot(0.50, 0.50, marker='o', markersize=7, color='#D90429', zorder=7)
    
    ax.plot([0.50, 0.85], [0.50, 0.50], color='#666666', linestyle='--', linewidth=1.2, zorder=5, label='Intended Crack Propagation Line ($y = 0.5$ mm)')
    
    tip_pts = [
        (0.5000, 0.50, r"$\mathbf{Tip\ at\ Peak}\ (u=0.0057\ \mathrm{mm})$" + "\n" + r"$h \approx 1.9\ \mu\mathrm{m},\ l_0/h \approx 3.9$", '#1B4332', (0.50, 0.535)),
        (0.6123, 0.50, r"$\mathbf{Tip\ at\ Post\text{-}Peak}\ (u=0.0059\ \mathrm{mm})$" + "\n" + r"$h \approx 5.2\ \mu\mathrm{m},\ l_0/h \approx 1.4$", '#D90429', (0.61, 0.46)),
        (0.7081, 0.50, r"$\mathbf{Tip\ at\ Plateau}\ (u=0.0070\ \mathrm{mm})$" + "\n" + r"$h \approx 10.4\ \mu\mathrm{m},\ l_0/h \approx 0.7$", '#7209B7', (0.71, 0.535))
    ]
    
    for x_tip, y_tip, label, col, txt_pos in tip_pts:
        ax.plot(x_tip, y_tip, marker='X', markersize=10, color=col, markeredgecolor='white', markeredgewidth=1.2, zorder=8)
        ax.annotate(label, xy=(x_tip, y_tip), xytext=txt_pos,
                    arrowprops=dict(arrowstyle="->", color=col, lw=1.3),
                    fontsize=8.5, fontweight='bold', color=col,
                    bbox=dict(boxstyle="round,pad=0.25", facecolor='white', edgecolor=col, alpha=0.92),
                    zorder=9)

    ax.axvline(0.57, color='#2A9D8F', linestyle=':', linewidth=1.5, zorder=6)
    ax.text(0.535, 0.555, "WELL-RESOLVED\n($l_0/h \\geq 2$)", ha='center', va='top', fontsize=8.0, fontweight='bold', color='#1B4332')
    
    ax.axvline(0.65, color='#E76F51', linestyle=':', linewidth=1.5, zorder=6)
    ax.text(0.610, 0.555, "TRANSITION\n($1 \\leq l_0/h < 2$)", ha='center', va='top', fontsize=8.0, fontweight='bold', color='#E76F51')
    ax.text(0.740, 0.555, "COARSE PINNING ZONE\n($l_0/h < 1$, $h > l_0$)", ha='center', va='top', fontsize=8.0, fontweight='bold', color='#D90429')

    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar_ax = fig.add_axes([0.915, 0.15, 0.018, 0.70])
    cbar = plt.colorbar(sm, cax=cbar_ax)
    cbar.set_label(r'Characteristic Element Size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=10.5, fontweight='bold')
    cbar.ax.axhline(7.5, color='#D90429', linestyle='--', linewidth=1.8)
    cbar.ax.text(1.2, 7.5, r'$l_0=7.5\ \mu\mathrm{m}$', color='#D90429', va='center', fontsize=8.5, fontweight='bold', transform=cbar.ax.get_yaxis_transform())
    cbar.ax.axhline(3.75, color='#E76F51', linestyle='-.', linewidth=1.6)
    cbar.ax.text(1.2, 3.75, r'$l_0/2=3.75\ \mu\mathrm{m}$', color='#E76F51', va='center', fontsize=8.5, fontweight='bold', transform=cbar.ax.get_yaxis_transform())

    ax.set_xlim(0.48, 0.82)
    ax.set_ylim(0.44, 0.56)
    ax.set_aspect('equal')
    ax.set_xlabel(r'Coordinate $x$ [mm]', fontsize=11, fontweight='bold')
    ax.set_ylabel(r'Coordinate $y$ [mm]', fontsize=11, fontweight='bold')
    ax.set_title("Method B Adapted Mesh along Forward Crack Propagation Ligament\n"
                 r"Direct Spatial Transition from Fine Tip ($h \approx 1.9\ \mu\mathrm{m}$) into Coarse Ligament ($h > 10\ \mu\mathrm{m}$)",
                 fontsize=12, fontweight='bold', color='#1D3557')
    ax.legend(loc='lower left', fontsize=9.0, framealpha=0.92)
    ax.grid(True, linestyle=':', alpha=0.4)

    png_path = os.path.join(out_dir, "fig_mode1_method_b_propagation_ligament_zoom.png")
    pdf_path = os.path.join(out_dir, "fig_mode1_method_b_propagation_ligament_zoom.pdf")
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    plt.close()
    print(f"Generated Figure 2: {png_path} and {pdf_path}")


def main():
    print("=== TASK F1428: GENERATING METHOD B PROPAGATION RESOLUTION FIGURES ===")
    nodes, quads, tris = parse_abaqus_mesh(INP_PATH)
    elements = build_element_records(nodes, quads, tris)
    print(f"Parsed {len(nodes)} nodes, {len(elements)} elements.")
    
    plot_propagation_resolution_synthesis(elements, OUT_DIR)
    plot_propagation_ligament_zoom(elements, nodes, OUT_DIR)
    print("=== FIGURE GENERATION COMPLETE ===")

def test_generate_figures():
    main()
    fig1_png = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_resolution.png")
    fig1_pdf = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_resolution.pdf")
    fig2_png = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_ligament_zoom.png")
    fig2_pdf = os.path.join(OUT_DIR, "fig_mode1_method_b_propagation_ligament_zoom.pdf")
    assert os.path.exists(fig1_png) and os.path.getsize(fig1_png) > 100000
    assert os.path.exists(fig1_pdf) and os.path.getsize(fig1_pdf) > 50000
    assert os.path.exists(fig2_png) and os.path.getsize(fig2_png) > 100000
    assert os.path.exists(fig2_pdf) and os.path.getsize(fig2_pdf) > 50000

if __name__ == '__main__':
    main()
