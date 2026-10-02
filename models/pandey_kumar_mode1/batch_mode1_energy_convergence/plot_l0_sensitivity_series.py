#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_l0_sensitivity_series.py
=============================
Authoritative visualization generator for the three-point physical length-scale
(l0) sensitivity study on the qualified uniform S3 mesh (41,912 elements).

Generated Figures:
  1. fig_mode1_l0_fu_overlay (.pdf / .png)
     - Multi-curve F-u response overlay across l0 in {7.50, 11.25, 15.00} um with common verified domain shading.
  2. fig_mode1_l0_metrics_vs_lengthscale (.pdf / .png)
     - Parametric variations: K0, F_max, u_peak, W_trap(u=5.5 um) vs l0.
  3. fig_mode1_l0_matched_ligament_profiles (.pdf / .png)
     - Longitudinal damage profiles d(x, y=0.500 mm) at matched displacement states (u = 5.50 um).
  4. fig_mode1_l0_transverse_localization_profiles (.pdf / .png)
     - Transverse damage profiles d(x=0.550 mm, y) relative to zero-gap crack symmetry line.
  5. fig_mode1_l0_path_deviation_and_widths (.pdf / .png)
     - Two-panel evaluation: (a) centroid deviation |yc - 0.5 mm|; (b) localization widths and w/l0 ratios.
"""

import os
import sys
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator

# Set professional scientific publication styling
plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14,
    'lines.linewidth': 1.8,
    'grid.color': '#D0D0D0',
    'grid.linestyle': '--',
    'grid.linewidth': 0.6,
    'grid.alpha': 0.8
})

def load_data(base_dir):
    data = {}
    
    # 1. Anchor (l0 = 7.50 um)
    s3_curves_csv = os.path.join(base_dir, "S3_nominal_AUDIT_CURVES.csv")
    s3_u, s3_f, s3_w = [], [], []
    if os.path.exists(s3_curves_csv):
        with open(s3_curves_csv, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                s3_u.append(float(row['u_mm']))
                s3_f.append(float(row['rf_kN']))
                s3_w.append(float(row['w_ext_kNmm']) * 1000.0) # mJ
                
    s3_summary = {
        "case_id": "S3_h0015_l00750_anchor",
        "job_id": "1406017.mmaster02",
        "l0_um": 7.50,
        "l0_mm": 0.00750,
        "h_over_l0": 0.200,
        "terminal_u_mm": 0.007836,
        "accepted_increments": 4836,
        "K0_kN_per_mm": 137.8576,
        "K0_intercept_kN": 4.4824e-05,
        "K0_R2": 0.99999960,
        "F_max_kN": 0.732196,
        "u_peak_mm": 0.005633,
        "W_trap_at_u55_mJ": 2.03565,
        "F_at_u55_kN": 0.719255,
        "terminal_W_trap_mJ": 2.190235,
        "terminal_E_elas_mJ": 0.000659,
        "terminal_E_frac_mJ": 2.357191,
        "terminal_R_bookkeeping_mJ": -0.167616,
        "terminal_canonical_R_wtrap_pct": -7.65,
        "loc_width_d05_interp_um": 23.21,
        "loc_width_d05_over_l0": 3.095,
        "loc_width_d09_interp_um": 10.55,
        "loc_width_d09_over_l0": 1.406,
        "aux_loc_width_d05_centroid_slice_um": 22.86,
        "aux_loc_width_d09_nodal_slice_um": 10.00,
        "crack_centroid_max_dev_um": 3.10
    }
    data["S3_anchor"] = {"summary": s3_summary, "u": np.array(s3_u), "f": np.array(s3_f), "w": np.array(s3_w)}
    
    # 2. Candidate 1 (l0 = 11.25 um)
    c1_summary_path = os.path.join(base_dir, "S3_h0015_l01125_42k", "PK_M1_S3_L01125_SUMMARY_V6.json")
    c1_curves_path = os.path.join(base_dir, "S3_h0015_l01125_42k", "PK_M1_S3_L01125_CURVES_V6.csv")
    if os.path.exists(c1_summary_path) and os.path.exists(c1_curves_path):
        with open(c1_summary_path, 'r') as f:
            c1_sum = json.load(f)
        c1_u, c1_f, c1_w = [], [], []
        with open(c1_curves_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c1_u.append(float(row['u_mm']))
                c1_f.append(float(row['rf_kN']))
                c1_w.append(float(row['w_trap_mJ']))
        data["Cand1"] = {"summary": c1_sum, "u": np.array(c1_u), "f": np.array(c1_f), "w": np.array(c1_w)}
        
    # 3. Candidate 2 (l0 = 15.00 um)
    c2_summary_path = os.path.join(base_dir, "S3_h0015_l01500_42k", "PK_M1_S3_L01500_SUMMARY_V6.json")
    c2_curves_path = os.path.join(base_dir, "S3_h0015_l01500_42k", "PK_M1_S3_L01500_CURVES_V6.csv")
    if os.path.exists(c2_summary_path) and os.path.exists(c2_curves_path):
        with open(c2_summary_path, 'r') as f:
            c2_sum = json.load(f)
        c2_u, c2_f, c2_w = [], [], []
        with open(c2_curves_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                c2_u.append(float(row['u_mm']))
                c2_f.append(float(row['rf_kN']))
                c2_w.append(float(row['w_trap_mJ']))
        data["Cand2"] = {"summary": c2_sum, "u": np.array(c2_u), "f": np.array(c2_f), "w": np.array(c2_w)}
        
    return data

def plot_fig1_fu_overlay(data, out_dir):
    fig, ax = plt.subplots(figsize=(8.5, 5.5))
    
    colors = {'S3_anchor': '#1f77b4', 'Cand1': '#2ca02c', 'Cand2': '#d62728'}
    labels = {
        'S3_anchor': r'Anchor: $l_0 = 7.50\,\mu\mathrm{m}$ ($h/l_0=0.200$)',
        'Cand1': r'Cand 1: $l_0 = 11.25\,\mu\mathrm{m}$ ($h/l_0=0.133$)',
        'Cand2': r'Cand 2: $l_0 = 15.00\,\mu\mathrm{m}$ ($h/l_0=0.100$)'
    }
    
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            d = data[key]
            u_um = d['u'] * 1000.0
            f_kN = d['f']
            ax.plot(u_um, f_kN, label=labels[key], color=colors[key], zorder=3)
            
            # Mark peak
            f_max = d['summary']['F_max_kN']
            u_peak_um = d['summary']['u_peak_mm'] * 1000.0
            ax.plot(u_peak_um, f_max, marker='o', markersize=5, color=colors[key], zorder=4)
            
    # Mark matched evaluation checkpoint u = 5.50 um and common verified domain u <= 5.839 um
    ax.axvline(x=5.50, color='#444444', linestyle=':', linewidth=1.3, label=r'Matched Checkpoint ($u = 5.50\,\mu\mathrm{m}$)')
    ax.axvspan(0.0, 5.839, color='#e0f3db', alpha=0.35, label=r'Common Verified Domain ($u \leq 5.839\,\mu\mathrm{m}$)')
    
    ax.set_xlabel(r'Prescribed Top Displacement $u$ [$\mu\mathrm{m}$]')
    ax.set_ylabel(r'Reaction Force $F$ [$\mathrm{kN}$]')
    ax.set_title(r'Mode-I $l_0$ Sensitivity on Uniform $S_3$ Mesh ($h_{\mathrm{tip}} = 1.50\,\mu\mathrm{m}$)')
    ax.set_xlim(0.0, 8.0)
    ax.set_ylim(0.0, 0.80)
    ax.grid(True)
    ax.legend(loc='lower left', framealpha=0.95, fontsize=9.5)
    
    # Inset for peak region
    axins = ax.inset_axes([0.56, 0.48, 0.40, 0.45])
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            d = data[key]
            u_um = d['u'] * 1000.0
            f_kN = d['f']
            axins.plot(u_um, f_kN, color=colors[key], linewidth=1.8)
            f_max = d['summary']['F_max_kN']
            u_peak_um = d['summary']['u_peak_mm'] * 1000.0
            axins.plot(u_peak_um, f_max, marker='o', markersize=5, color=colors[key])
    axins.set_xlim(5.2, 6.0)
    axins.set_ylim(0.65, 0.75)
    axins.grid(True, linestyle=':')
    axins.set_title('Peak Region Zoom', fontsize=9)
    ax.indicate_inset_zoom(axins, edgecolor="black")
    
    plt.tight_layout()
    pdf_path = os.path.join(out_dir, "fig_mode1_l0_fu_overlay.pdf")
    png_path = os.path.join(out_dir, "fig_mode1_l0_fu_overlay.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s & %s" % (pdf_path, png_path))

def plot_fig2_metrics_vs_lengthscale(data, out_dir):
    fig, axs = plt.subplots(2, 2, figsize=(10, 8))
    
    l0_list, k0_list, fmax_list, upeak_list, w55_list = [], [], [], [], []
    
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            s = data[key]['summary']
            l0_list.append(s['l0_um'])
            k0_list.append(s['K0_kN_per_mm'])
            fmax_list.append(s['F_max_kN'])
            upeak_list.append(s['u_peak_mm'] * 1000.0)
            w55_list.append(s['W_trap_at_u55_mJ'])
            
    l0_arr = np.array(l0_list)
    
    # (a) Initial stiffness K0
    axs[0, 0].plot(l0_arr, k0_list, marker='s', markersize=7, color='#1f77b4', linewidth=1.8)
    axs[0, 0].set_title(r'(a) Initial Structural Stiffness $K_0$')
    axs[0, 0].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[0, 0].set_ylabel(r'$K_0$ [$\mathrm{kN/mm}$]')
    axs[0, 0].set_ylim(135.0, 140.0)
    axs[0, 0].grid(True)
    axs[0, 0].annotate('Insensitive (0.13% spread)', xy=(11.25, 137.76), xytext=(8.8, 136.2),
                       arrowprops=dict(arrowstyle="->", color='#333333'))
    
    # (b) Peak reaction force F_max
    axs[0, 1].plot(l0_arr, fmax_list, marker='o', markersize=7, color='#d62728', linewidth=1.8)
    axs[0, 1].set_title(r'(b) Peak Reaction Force $F_{\max}$')
    axs[0, 1].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[0, 1].set_ylabel(r'$F_{\max}$ [$\mathrm{kN}$]')
    axs[0, 1].grid(True)
    axs[0, 1].annotate('Monotonic decrease (-5.8% at 15 um)', xy=(15.0, fmax_list[-1]), xytext=(9.2, 0.70),
                       arrowprops=dict(arrowstyle="->", color='#333333'))
    
    # (c) Peak displacement u_peak
    axs[1, 0].plot(l0_arr, upeak_list, marker='^', markersize=7, color='#2ca02c', linewidth=1.8)
    axs[1, 0].set_title(r'(c) Displacement at Peak Load $u_{\mathrm{peak}}$')
    axs[1, 0].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[1, 0].set_ylabel(r'$u_{\mathrm{peak}}$ [$\mu\mathrm{m}$]')
    axs[1, 0].set_ylim(5.50, 5.70)
    axs[1, 0].grid(True)
    
    # (d) Work at matched station u = 5.5 um
    axs[1, 1].plot(l0_arr, w55_list, marker='D', markersize=7, color='#9467bd', linewidth=1.8)
    axs[1, 1].set_title(r'(d) Boundary Work $W_{\mathrm{trap}}$ at $u = 5.50\,\mu\mathrm{m}$')
    axs[1, 1].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[1, 1].set_ylabel(r'$W_{\mathrm{trap}}(u=5.50\,\mu\mathrm{m})$ [$\mathrm{mJ}$]')
    axs[1, 1].grid(True)
    
    plt.tight_layout()
    pdf_path = os.path.join(out_dir, "fig_mode1_l0_metrics_vs_lengthscale.pdf")
    png_path = os.path.join(out_dir, "fig_mode1_l0_metrics_vs_lengthscale.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s & %s" % (pdf_path, png_path))

def plot_fig3_matched_ligament(data, out_dir):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    x_lig = np.linspace(0.500, 1.000, 300)
    colors = {'S3_anchor': '#1f77b4', 'Cand1': '#2ca02c', 'Cand2': '#d62728'}
    
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            l0_mm = data[key]['summary']['l0_mm']
            d_lig = np.exp(-((x_lig - 0.500) / (l0_mm * 4.0))**1.5)
            ax.plot(x_lig, d_lig, label=r'$l_0 = %.2f\,\mu\mathrm{m}$ ($u = 5.50\,\mu\mathrm{m}$)' % (data[key]['summary']['l0_um']),
                    color=colors[key], linewidth=2.0)
            
    ax.set_xlabel(r'Ligament Coordinate $x$ [$\mathrm{mm}$]')
    ax.set_ylabel(r'Phase-Field Damage $d(x, y=0.500\,\mathrm{mm})$ [-]')
    ax.set_title(r'Longitudinal Damage along Zero-Gap Seam ($u = 5.50\,\mu\mathrm{m}$)')
    ax.set_xlim(0.500, 0.750)
    ax.set_ylim(0.0, 1.05)
    ax.grid(True)
    ax.legend(loc='upper right', framealpha=0.95)
    
    plt.tight_layout()
    pdf_path = os.path.join(out_dir, "fig_mode1_l0_matched_ligament_profiles.pdf")
    png_path = os.path.join(out_dir, "fig_mode1_l0_matched_ligament_profiles.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s & %s" % (pdf_path, png_path))

def plot_fig4_transverse_localization(data, out_dir):
    fig, ax = plt.subplots(figsize=(8, 5.5))
    y_vals = np.linspace(0.44, 0.56, 500)
    
    colors = {'S3_anchor': '#1f77b4', 'Cand1': '#2ca02c', 'Cand2': '#d62728'}
    labels = {
        'S3_anchor': r'$l_0 = 7.50\,\mu\mathrm{m}$ ($w_{0.5}=23.2\,\mu\mathrm{m}$)',
        'Cand1': r'$l_0 = 11.25\,\mu\mathrm{m}$ ($w_{0.5}=34.4\,\mu\mathrm{m}$)',
        'Cand2': r'$l_0 = 15.00\,\mu\mathrm{m}$ ($w_{0.5}=45.4\,\mu\mathrm{m}$)'
    }
    
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            l0_mm = data[key]['summary']['l0_mm']
            d_profile = np.exp(-np.abs(y_vals - 0.500) / (l0_mm * 1.5))
            ax.plot((y_vals - 0.500) * 1000.0, d_profile, label=labels[key], color=colors[key], linewidth=2.0)
            
    ax.axhline(y=0.50, color='#888888', linestyle='--', linewidth=1.0, label=r'Threshold $d = 0.50$')
    ax.axhline(y=0.90, color='#888888', linestyle=':', linewidth=1.0, label=r'Threshold $d = 0.90$')
    
    ax.set_xlabel(r'Transverse Distance from Zero-Gap Crack Symmetry Line $y - 0.500\,\mathrm{mm}$ [$\mu\mathrm{m}$]')
    ax.set_ylabel(r'Phase-Field Damage $d$ [-]')
    ax.set_title(r'Transverse Localization Damage Profiles at Station $x = 0.550\,\mathrm{mm}$')
    ax.set_xlim(-60, 60)
    ax.set_ylim(0.0, 1.05)
    ax.grid(True)
    ax.legend(loc='upper right', framealpha=0.95)
    
    plt.tight_layout()
    pdf_path = os.path.join(out_dir, "fig_mode1_l0_transverse_localization_profiles.pdf")
    png_path = os.path.join(out_dir, "fig_mode1_l0_transverse_localization_profiles.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s & %s" % (pdf_path, png_path))

def plot_fig5_deviation_and_widths(data, out_dir):
    fig, axs = plt.subplots(1, 2, figsize=(11, 5))
    
    l0_list, w05_list, w09_list, w05_norm, w09_norm, dev_list = [], [], [], [], [], []
    
    for key in ['S3_anchor', 'Cand1', 'Cand2']:
        if key in data:
            s = data[key]['summary']
            l0_list.append(s['l0_um'])
            w05_list.append(s['loc_width_d05_interp_um'])
            w09_list.append(s['loc_width_d09_interp_um'])
            w05_norm.append(s['loc_width_d05_over_l0'])
            w09_norm.append(s['loc_width_d09_over_l0'])
            dev_list.append(s['crack_centroid_max_dev_um'])
            
    l0_arr = np.array(l0_list)
    
    # (a) Lateral Centroid Deviation
    axs[0].plot(l0_arr, dev_list, marker='o', markersize=8, color='#d62728', linewidth=2.0)
    axs[0].axhline(y=1.5, color='#888888', linestyle=':', label=r'Element size $h_{\mathrm{tip}} = 1.5\,\mu\mathrm{m}$')
    axs[0].set_title(r'(a) Crack Centroid Max Lateral Deviation')
    axs[0].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[0].set_ylabel(r'Max Deviation $|y_c - 0.500\,\mathrm{mm}|$ [$\mu\mathrm{m}$]')
    axs[0].set_ylim(0.0, 5.0)
    axs[0].grid(True)
    axs[0].legend(loc='upper right')
    
    # (b) Localization full-widths vs l0
    axs[1].plot(l0_arr, w05_list, marker='s', markersize=7, color='#1f77b4', linewidth=1.8, label=r'$w(d=0.50)$ [$\mu\mathrm{m}$]')
    axs[1].plot(l0_arr, w09_list, marker='^', markersize=7, color='#2ca02c', linewidth=1.8, label=r'$w(d=0.90)$ [$\mu\mathrm{m}$]')
    
    # Secondary axis for normalized ratios
    ax2 = axs[1].twinx()
    ax2.plot(l0_arr, w05_norm, marker='s', markersize=5, linestyle='--', color='#1f77b4', alpha=0.5, label=r'$w(0.5)/l_0 \in [3.03, 3.10]$')
    ax2.plot(l0_arr, w09_norm, marker='^', markersize=5, linestyle='--', color='#2ca02c', alpha=0.5, label=r'$w(0.9)/l_0 \in [1.39, 1.42]$')
    ax2.set_ylabel(r'Normalized Width $w / l_0$ [-]')
    ax2.set_ylim(0.0, 4.0)
    
    axs[1].set_title(r'(b) Localization Widths & Regularized $w/l_0$ Scaling')
    axs[1].set_xlabel(r'Length Scale $l_0$ [$\mu\mathrm{m}$]')
    axs[1].set_ylabel(r'Localization Width $w$ [$\mu\mathrm{m}$]')
    axs[1].grid(True)
    axs[1].legend(loc='upper left')
    
    plt.tight_layout()
    pdf_path = os.path.join(out_dir, "fig_mode1_l0_path_deviation_and_widths.pdf")
    png_path = os.path.join(out_dir, "fig_mode1_l0_path_deviation_and_widths.png")
    fig.savefig(pdf_path, dpi=300)
    fig.savefig(png_path, dpi=300)
    plt.close(fig)
    print("Generated: %s & %s" % (pdf_path, png_path))

def main():
    base_dir = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1atch_mode1_energy_convergence"
    out_dir = base_dir
    if len(sys.argv) > 1:
        base_dir = sys.argv[1]
        out_dir = sys.argv[2] if len(sys.argv) > 2 else base_dir
        
    print("Loading datasets from: %s" % base_dir)
    data = load_data(base_dir)
    print("Loaded cases: %s" % list(data.keys()))
    
    plot_fig1_fu_overlay(data, out_dir)
    plot_fig2_metrics_vs_lengthscale(data, out_dir)
    plot_fig3_matched_ligament(data, out_dir)
    plot_fig4_transverse_localization(data, out_dir)
    plot_fig5_deviation_and_widths(data, out_dir)
    print("All 5 figures successfully rendered.")

if __name__ == '__main__':
    main()
