#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plot_mode2_f1375_independent_validation.py

Generates the authoritative 4-panel publication figure for Task F1375:
- Panel (a): Node-Adjacency vs Edge-Adjacency remaining ligament evolution (h_lig)
             with element centroid vs nodal boundary discretization uncertainty bands.
- Panel (b): Verified crack propagation kinetics (da/du_x) superimposed on reaction force RF_1,
             demonstrating the 14-22x post-peak propagation deceleration.
- Panel (c): Coarse Step-2 MISESERI error evolution across 2,002 frames, tracking corridor concentration
             jumping from ~19% (Step 1) to 73.1% (terminal Step 2).
- Panel (d): Multi-increment cumulative MISESERI sizing envelope mechanism, demonstrating why
             outputFrequency=ALL_INCREMENTS generates a continuous crack-path refinement corridor.

Authoritative data drawn from:
- models/pandey_kumar_mode2/f1375_independent_validation_results.json
- models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/m2_corrected_remesh/job2_rf_active_history.csv
- models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j1_coarse_retest_rf_history.csv
"""

import os
import json
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, AutoMinorLocator

def load_rf_csv(path, ux_idx=2, rf_idx=4):
    ux, rf = [], []
    with open(path, 'r') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) > max(ux_idx, rf_idx):
                try:
                    ux.append(float(row[ux_idx]))
                    rf.append(float(row[rf_idx]))
                except ValueError:
                    pass
    return np.array(ux), np.array(rf)

def main():
    json_path = 'models/pandey_kumar_mode2/f1375_independent_validation_results.json'
    rf_et3_path = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/m2_corrected_remesh/job2_rf_active_history.csv'
    rf_coarse_path = 'models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/mode2_j1_coarse_retest_rf_history.csv'

    with open(json_path, 'r') as f:
        val_data = json.load(f)

    # 1. Extract Coarse & ET3 frame records
    et3_frames = val_data['et3']['results_by_frame']
    coarse_frames = val_data['coarse']['results_by_frame']
    miseseri_frames = val_data['coarse']['miseseri_audit']['frames']

    # ET3 data
    et3_ux = np.array([f['ux_um'] for f in et3_frames])
    et3_node_hlig = np.array([f['thresholds']['0.9']['node_graph']['h_ligament_centroid_mm'] * 1000.0 for f in et3_frames])
    et3_edge_hlig = np.array([f['thresholds']['0.9']['edge_graph']['h_ligament_centroid_mm'] * 1000.0 for f in et3_frames])
    et3_ymin = np.array([f['thresholds']['0.9']['edge_graph']['tip_elem_ymin_mm'] * 1000.0 for f in et3_frames])
    et3_ymax = np.array([f['thresholds']['0.9']['edge_graph']['tip_elem_ymax_mm'] * 1000.0 for f in et3_frames])
    et3_tip_x = np.array([f['thresholds']['0.9']['edge_graph']['tip_centroid_x_mm'] for f in et3_frames])
    et3_tip_y = np.array([f['thresholds']['0.9']['edge_graph']['tip_centroid_y_mm'] for f in et3_frames])

    # Coarse data
    coarse_ux = np.array([f['ux_um'] for f in coarse_frames])
    coarse_node_hlig = np.array([f['thresholds']['0.9']['node_graph']['h_ligament_centroid_mm'] * 1000.0 for f in coarse_frames])
    coarse_edge_hlig = np.array([f['thresholds']['0.9']['edge_graph']['h_ligament_centroid_mm'] * 1000.0 for f in coarse_frames])
    coarse_ymin = np.array([f['thresholds']['0.9']['edge_graph']['tip_elem_ymin_mm'] * 1000.0 for f in coarse_frames])
    coarse_ymax = np.array([f['thresholds']['0.9']['edge_graph']['tip_elem_ymax_mm'] * 1000.0 for f in coarse_frames])

    # Crack advance a(u_x) and kinetics da/du_x for ET3
    notch_x, notch_y = 0.5, 0.5
    a_et3 = np.sqrt((et3_tip_x - notch_x)**2 + (et3_tip_y - notch_y)**2) * 1000.0 # um

    # Central difference da/du_x (mm/mm)
    # ux is in um, a is in um, so da/du_x in um/um == mm/mm
    da_dux = np.zeros_like(a_et3)
    for i in range(len(a_et3)):
        if i == 0:
            da_dux[i] = (a_et3[1] - a_et3[0]) / (et3_ux[1] - et3_ux[0])
        elif i == len(a_et3) - 1:
            da_dux[i] = (a_et3[-1] - a_et3[-2]) / (et3_ux[-1] - et3_ux[-2])
        else:
            da_dux[i] = (a_et3[i+1] - a_et3[i-1]) / (et3_ux[i+1] - et3_ux[i-1])

    # Reaction forces
    ux_rf_et3, rf_et3 = load_rf_csv(rf_et3_path)
    ux_rf_coarse, rf_coarse = load_rf_csv(rf_coarse_path)

    # MISESERI audit data
    mis_ux = np.array([f['ux_um'] for f in miseseri_frames])
    mis_corridor_pct = np.array([f['err_corridor_pct'] for f in miseseri_frames])
    mis_tip_pct = np.array([f['err_tip_pct'] for f in miseseri_frames])
    mis_base_pct = np.array([f['err_base_pct'] for f in miseseri_frames])
    mis_mean = np.array([f['mean'] for f in miseseri_frames])
    mis_max = np.array([f['max'] for f in miseseri_frames])

    # -------------------------------------------------------------
    # PLOTTING
    # -------------------------------------------------------------
    plt.rcParams.update({
        'font.size': 9,
        'font.family': 'sans-serif',
        'axes.labelsize': 10,
        'axes.titlesize': 10,
        'xtick.labelsize': 8.5,
        'ytick.labelsize': 8.5,
        'legend.fontsize': 8,
        'lines.linewidth': 1.6,
        'figure.titlesize': 11
    })

    fig, axes = plt.subplots(2, 2, figsize=(13.0, 9.5))
    fig.subplots_adjust(hspace=0.28, wspace=0.28, top=0.93, bottom=0.08, left=0.08, right=0.93)

    # -------------------------------------------------------------
    # PANEL (a): Node vs Edge Connectivity & Discretization Uncertainty
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    ax_a.set_title(r"$\mathbf{(a)}$ Node vs. Edge Graph Connectivity & Ligament Uncertainty ($d \geq 0.90$)", loc='left')

    # Uncertainty bands
    ax_a.fill_between(et3_ux, et3_ymin, et3_ymax, color='#1f77b4', alpha=0.18,
                      label=r'ET3 Element Discretization Band $[y_{\min}, y_{\max}]$ ($\Delta h \approx 4.9\,\mu\mathrm{m}$)')
    ax_a.fill_between(coarse_ux, coarse_ymin, coarse_ymax, color='#d62728', alpha=0.15,
                      label=r'Coarse Element Band $[y_{\min}, y_{\max}]$ ($\Delta h \approx 26.6\,\mu\mathrm{m}$)')

    # Ligament curves
    ax_a.plot(coarse_ux, coarse_node_hlig, 'r--', marker='s', markersize=3.5, label='Coarse Node-Adjacency (Centroid)')
    ax_a.plot(coarse_ux, coarse_edge_hlig, 'r-', marker='o', markersize=3.0, label='Coarse Edge-Adjacency (Centroid)')
    ax_a.plot(et3_ux, et3_node_hlig, 'b--', marker='^', markersize=3.5, label='ET3 Node-Adjacency (Centroid)')
    ax_a.plot(et3_ux, et3_edge_hlig, 'b-', marker='d', markersize=3.0, label='ET3 Edge-Adjacency (Centroid)')

    # Reference / Boundary lines
    ax_a.axhline(0, color='black', linestyle=':', linewidth=1.0)
    ax_a.annotate(r'Earlier flawed claim: $h_{\mathrm{lig}} = 0$ (FULLY REFUTED)',
                  xy=(12.0, 0.0), xytext=(10.5, 40.0),
                  arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.0),
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffdddd', edgecolor='red', alpha=0.9),
                  fontsize=8, fontweight='bold', color='darkred')

    # Annotate terminal values
    ax_a.annotate(f'ET3 Terminal:\n$h_{{\\mathrm{{lig}}}} = {et3_edge_hlig[-1]:.1f}\\,\\mu\\mathrm{{m}}$ (Centroid)\n$y_{{\\min}} = {et3_ymin[-1]:.1f}\\,\\mu\\mathrm{{m}}$ (Nodal Min)',
                  xy=(et3_ux[-1], et3_edge_hlig[-1]), xytext=(14.2, 85.0),
                  arrowprops=dict(facecolor='#1f77b4', arrowstyle='->', lw=1.2),
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6f2ff', edgecolor='#1f77b4', alpha=0.9),
                  fontsize=7.5)

    ax_a.annotate(f'Coarse Terminal:\n$h_{{\\mathrm{{lig}}}} = {coarse_edge_hlig[-1]:.1f}\\,\\mu\\mathrm{{m}}$ (Centroid)\n$y_{{\\min}} = {coarse_ymin[-1]:.1f}\\,\\mu\\mathrm{{m}}$ (Nodal Min)',
                  xy=(coarse_ux[-1], coarse_edge_hlig[-1]), xytext=(13.5, 230.0),
                  arrowprops=dict(facecolor='#d62728', arrowstyle='->', lw=1.2),
                  bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff0f0', edgecolor='#d62728', alpha=0.9),
                  fontsize=7.5)

    ax_a.set_xlabel(r'Prescribed Shear Displacement $u_x$ [$\mu\mathrm{m}$]')
    ax_a.set_ylabel(r'Remaining Intact Ligament $h_{\mathrm{lig}}$ [$\mu\mathrm{m}$]')
    ax_a.set_xlim(8.0, 20.5)
    ax_a.set_ylim(-15, 520)
    ax_a.grid(True, linestyle=':', alpha=0.5)
    ax_a.legend(loc='upper right', framealpha=0.92, fontsize=7.2)

    # -------------------------------------------------------------
    # PANEL (b): Crack Kinetics (da/du_x) & Reaction Force Correlation
    # -------------------------------------------------------------
    ax_b1 = axes[0, 1]
    ax_b1.set_title(r"$\mathbf{(b)}$ Verified Crack Kinetics ($da/du_x$) & Force Correlation", loc='left')

    color_kin = '#2ca02c' # Green
    color_rf = '#1f77b4'  # Blue

    # RF on secondary axis
    ax_b2 = ax_b1.twinx()
    l_rf = ax_b2.plot(ux_rf_et3 * 1000.0, rf_et3, color=color_rf, linestyle='-', linewidth=1.5, label='ET3 Reaction Force $RF_1(u_x)$')
    ax_b2.set_ylabel(r'Shear Reaction Force $RF_1$ [$\mathrm{N}$]', color=color_rf)
    ax_b2.tick_params(axis='y', labelcolor=color_rf)
    ax_b2.set_ylim(0, 520)

    # Kinetics on primary axis
    l_kin = ax_b1.plot(et3_ux, da_dux, color=color_kin, marker='o', markersize=4.0, linewidth=1.8, label=r'ET3 Propagation Rate $da/du_x$ [$\mathrm{mm/mm}$]')
    ax_b1.set_xlabel(r'Prescribed Shear Displacement $u_x$ [$\mu\mathrm{m}$]')
    ax_b1.set_ylabel(r'Crack Propagation Rate $da/du_x$ [$\mathrm{mm/mm}$]', color=color_kin)
    ax_b1.tick_params(axis='y', labelcolor=color_kin)
    ax_b1.set_xlim(8.0, 20.5)
    ax_b1.set_ylim(0, 210)
    ax_b1.grid(True, linestyle=':', alpha=0.5)

    # Annotate peak and terminal deceleration
    peak_idx = np.argmax(da_dux)
    peak_ux = et3_ux[peak_idx]
    peak_rate = da_dux[peak_idx]
    term_rate = da_dux[-1]
    min_rate = np.min(da_dux[et3_ux >= 12.0])
    ratio_term = peak_rate / term_rate
    ratio_trough = peak_rate / min_rate

    ax_b1.annotate(f'Peak Rate:\n${peak_rate:.1f}\\,\\mathrm{{mm/mm}}$\n(at $u_x = {peak_ux:.1f}\\,\\mu\\mathrm{{m}}$)',
                   xy=(peak_ux, peak_rate), xytext=(peak_ux + 1.2, peak_rate - 25),
                   arrowprops=dict(facecolor=color_kin, arrowstyle='->', lw=1.2),
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#eef9ee', edgecolor=color_kin, alpha=0.9),
                   fontsize=7.8)

    ax_b1.annotate(f'Terminal Deceleration:\nRate: ${term_rate:.1f}\\,\\mathrm{{mm/mm}}$\nRatio: $\\mathbf{{{ratio_term:.1f}\\times\\;\\mathrm{{reduction}}}}$\n(Peak/Trough: ${ratio_trough:.1f}\\times$)',
                   xy=(et3_ux[-1], term_rate), xytext=(13.8, 45),
                   arrowprops=dict(facecolor=color_kin, arrowstyle='->', lw=1.2),
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#eef9ee', edgecolor=color_kin, alpha=0.9),
                   fontsize=7.8, fontweight='bold')

    lines = l_kin + l_rf
    labels = [l.get_label() for l in lines]
    ax_b1.legend(lines, labels, loc='upper center', framealpha=0.92, fontsize=7.5)

    # -------------------------------------------------------------
    # PANEL (c): Step-2 MISESERI Error Evolution Across 2,002 Frames
    # -------------------------------------------------------------
    ax_c1 = axes[1, 0]
    ax_c1.set_title(r"$\mathbf{(c)}$ Coarse Pre-Analysis Step-2 MISESERI Error Concentration", loc='left')

    ax_c1.plot(mis_ux, mis_corridor_pct, color='#d62728', linewidth=1.8, label='Crack Corridor Concentration (%)')
    ax_c1.plot(mis_ux, mis_tip_pct, color='#ff7f0e', linestyle='--', linewidth=1.5, label='Notch Tip Zone (%)')
    ax_c1.plot(mis_ux, mis_base_pct, color='#7f7f7f', linestyle=':', linewidth=1.3, label='Base Boundary Zone (%)')

    ax_c1.set_xlabel(r'Prescribed Shear Displacement $u_x$ [$\mu\mathrm{m}$]')
    ax_c1.set_ylabel(r'MISESERI Error Concentration [%]', color='#d62728')
    ax_c1.tick_params(axis='y', labelcolor='#d62728')
    ax_c1.set_xlim(0, 20.5)
    ax_c1.set_ylim(-2, 85)
    ax_c1.grid(True, linestyle=':', alpha=0.5)

    # Secondary axis for mean error magnitude
    ax_c2 = ax_c1.twinx()
    ax_c2.semilogy(mis_ux, mis_mean, color='#9467bd', linestyle='-.', linewidth=1.4, label='Mean MISESERI Magnitude')
    ax_c2.set_ylabel(r'Mean MISESERI Error Magnitude', color='#9467bd')
    ax_c2.tick_params(axis='y', labelcolor='#9467bd')
    ax_c2.set_ylim(1e-17, 1e-13)

    # Annotate Step 1 vs Step 2 transition and terminal concentration
    ax_c1.axvline(10.0, color='gray', linestyle='--', linewidth=1.0)
    ax_c1.text(9.7, 72, 'Step 1\n(Elastic / Early)', ha='right', fontsize=7.5, color='dimgray')
    ax_c1.text(10.3, 72, 'Step 2\n(Shear / Fracture)', ha='left', fontsize=7.5, color='dimgray')

    term_corr = mis_corridor_pct[-1]
    peak_corr = np.max(mis_corridor_pct)
    ax_c1.annotate(f'Peak Corridor:\n${peak_corr:.1f}\\%$ at $u_x = 16.6\\,\\mu\\mathrm{{m}}$\n(Terminal: ${term_corr:.1f}\\%$)',
                   xy=(16.6, peak_corr), xytext=(12.0, 52),
                   arrowprops=dict(facecolor='#d62728', arrowstyle='->', lw=1.2),
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='#fff5f5', edgecolor='#d62728', alpha=0.9),
                   fontsize=7.8)

    h1, l1 = ax_c1.get_legend_handles_labels()
    h2, l2 = ax_c2.get_legend_handles_labels()
    ax_c1.legend(h1 + h2, l1 + l2, loc='upper left', framealpha=0.92, fontsize=7.2)

    # -------------------------------------------------------------
    # PANEL (d): Multi-Increment Cumulative Sizing Envelope Mechanism
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    ax_d.set_title(r"$\mathbf{(d)}$ Native Sizing Mechanism: Multi-Increment Error Envelope", loc='left')

    # Illustrate the concept of outputFrequency=ALL_INCREMENTS
    s = np.linspace(0, 1, 300)
    frames_s = [0.1, 0.3, 0.5, 0.7, 0.9]
    colors = plt.cm.plasma(np.linspace(0.1, 0.85, len(frames_s)))

    envelope_err = np.zeros_like(s)
    for idx, (s_k, c) in enumerate(zip(frames_s, colors)):
        err_k = np.exp(-((s - s_k) / 0.12)**2)
        envelope_err = np.maximum(envelope_err, err_k)
        ax_d.plot(s, err_k, color=c, linestyle=':', linewidth=1.2,
                  label=f'Frame {idx+1} Error Peak ($u_x = {10 + s_k*10:.0f}\\,\\mu\\mathrm{{m}}$)')

    # Cumulative envelope
    ax_d.plot(s, envelope_err, color='#b2182b', linewidth=2.4,
              label=r'Cumulative Envelope: $\mathcal{E}_{\max}(\mathbf{x}) = \max_{k} \eta_k(\mathbf{x})$')

    # Resulting target element size h_target(s) propto 1 / E_max
    h_nominal = 0.050 # mm
    h_refined = 0.005 # mm
    h_size = h_nominal - (h_nominal - h_refined) * envelope_err

    ax_d2 = ax_d.twinx()
    ax_d2.plot(s, h_size * 1000.0, color='#2166ac', linewidth=2.2, linestyle='--',
               label=r'Target Element Size $h_{\mathrm{target}}(\mathbf{x})$ [$\mu\mathrm{m}$]')
    ax_d2.set_ylabel(r'Target Element Size $h_{\mathrm{target}}$ [$\mu\mathrm{m}$]', color='#2166ac')
    ax_d2.tick_params(axis='y', labelcolor='#2166ac')
    ax_d2.set_ylim(0, 60)

    ax_d.set_xlabel(r'Normalized Position Along Crack Path $s = \|\mathbf{x} - \mathbf{x}_{\mathrm{notch}}\| / L_{\mathrm{path}}$')
    ax_d.set_ylabel(r'Normalized Error Indicator $\eta / \eta_{\max}$')
    ax_d.set_xlim(0, 1.0)
    ax_d.set_ylim(-0.05, 1.25)
    ax_d.grid(True, linestyle=':', alpha=0.5)

    # Explanatory annotation
    ax_d.annotate(r'$\mathbf{outputFrequency=ALL\_INCREMENTS}$:' + '\n' +
                  r'Abaqus evaluates error across all Step-2 frames' + '\n' +
                  r'and takes the upper envelope $\max_k \eta_k(\mathbf{x})$.' + '\n' +
                  r'Result: Continuous diagonal corridor refined' + '\n' +
                  r'ahead of crack, NOT just a local spot!',
                  xy=(0.5, 1.02), xytext=(0.08, 0.45),
                  arrowprops=dict(facecolor='#b2182b', arrowstyle='->', lw=1.2),
                  bbox=dict(boxstyle='round,pad=0.35', facecolor='#fffbe6', edgecolor='#b2182b', alpha=0.95),
                  fontsize=7.8)

    h_d1, l_d1 = ax_d.get_legend_handles_labels()
    h_d2, l_d2 = ax_d2.get_legend_handles_labels()
    ax_d.legend(h_d1 + h_d2, l_d1 + l_d2, loc='lower center', framealpha=0.92, fontsize=6.8, ncol=2)

    # Save outputs
    out_dir = 'results/figures/mode2'
    os.makedirs(out_dir, exist_ok=True)
    pdf_path = os.path.join(out_dir, 'fig_mode2_f1375_independent_connectivity_and_miseseri_audit.pdf')
    png_path = os.path.join(out_dir, 'fig_mode2_f1375_independent_connectivity_and_miseseri_audit.png')

    plt.savefig(pdf_path, dpi=300)
    plt.savefig(png_path, dpi=300)
    plt.close()

    print(f"Successfully generated:")
    print(f"  PDF: {pdf_path}")
    print(f"  PNG: {png_path}")

if __name__ == '__main__':
    main()
