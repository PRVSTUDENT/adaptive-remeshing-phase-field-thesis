# -*- coding: utf-8 -*-
"""
scripts/remeshing/plot_f1753_continuation_results.py

Generates publication-quality 4-panel diagnostic figure for Task F1753:
Case 2 Method A Controlled Continuation Production Simulation (Job 1423552.mmaster02):
  (a) Reaction Force vs Displacement F(u) Comparison (Baseline Job 1423271 vs Rerun Job 1423552).
  (b) Bottleneck Detail at Inc 190-205 showing breakthrough of 1e-8 limit down to 6e-11.
  (c) History Monotonicity (100% PASS, min Delta H = 0.0 MPa) vs Damage Irreversibility.
  (d) Comprehensive 5-Gate Acceptance Matrix and Scientific Evaluation.
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.remeshing.audit_f1753_continuation_odb import parse_rf_u_from_dat

def main():
    dat_base = 'results/validation/f1735_case2_fracture_evidence/PK_F1735_CASE_2_FRAC.dat'
    dat_rerun = 'models/pandey_kumar_mode1/234_f1752_case2_continuation/PK_F1752_CASE_2_CONTINUATION.dat'
    audit_json = 'results/validation/f1753_case2_continuation_audit.json'

    pts_base = parse_rf_u_from_dat(dat_base)
    pts_rerun = parse_rf_u_from_dat(dat_rerun)

    with open(audit_json, 'r') as f:
        audit_data = json.load(f)

    fig, axes = plt.subplots(2, 2, figsize=(14, 11))
    plt.subplots_adjust(wspace=0.28, hspace=0.32)

    # ----------------------------------------------------
    # Panel (a): F-u Curve Comparison
    # ----------------------------------------------------
    ax = axes[0, 0]
    u_base = [p['u2_mm'] * 1000.0 for p in pts_base]
    rf_base = [p['rf2_N'] for p in pts_base]
    u_rerun = [p['u2_mm'] * 1000.0 for p in pts_rerun]
    rf_rerun = [p['rf2_N'] for p in pts_rerun]

    ax.plot(u_base, rf_base, 'b-', linewidth=2.2, label='Baseline (Job 1423271, 252 incs, dt_min=1e-8)')
    ax.plot(u_rerun, rf_rerun, 'r--', linewidth=1.8, label='Rerun (Job 1423552, 255 incs, dt_min=1e-11)')

    # Markers
    ax.scatter([u_base[96]], [rf_base[96]], color='darkblue', s=70, zorder=5,
               label=r'Peak Force $F_{\mathrm{max}} = 571.7\,\mathrm{N}$')
    ax.scatter([u_base[-1]], [rf_base[-1]], color='blue', marker='s', s=70, zorder=5,
               label=r'Predecessor End ($F = 244.4\,\mathrm{N}$)')
    ax.scatter([u_rerun[-1]], [rf_rerun[-1]], color='darkred', marker='^', s=80, zorder=6,
               label=r'F1753 Terminal ($F = 229.4\,\mathrm{N}$)')

    ax.set_title('(a) Global Load-Displacement Response $F(u_y)$', fontsize=12, fontweight='bold')
    ax.set_xlabel(r'Applied Displacement $u_y$ [$\mu\mathrm{m}$]', fontsize=11)
    ax.set_ylabel(r'Reaction Force $RF_y$ [$\mathrm{N}$]', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='lower left', fontsize=9, framealpha=0.9)
    ax.set_xlim(0, 8.5)
    ax.set_ylim(0, 620)

    # ----------------------------------------------------
    # Panel (b): Time Step Evolution around Bottleneck
    # ----------------------------------------------------
    ax = axes[0, 1]
    incs = [p['increment'] for p in pts_rerun if p['increment'] >= 190]
    dt_vals = []
    for i in range(1, len(pts_rerun)):
        if pts_rerun[i]['increment'] >= 190:
            dt = pts_rerun[i]['total_time'] - pts_rerun[i-1]['total_time']
            dt_vals.append(max(dt, 1e-12))

    ax.semilogy(incs[:len(dt_vals)], dt_vals, 'mo-', linewidth=1.8, markersize=5, label=r'Rerun $\Delta t$ (Job 1423552)')
    ax.axhline(1.0e-8, color='k', linestyle=':', linewidth=1.5, label=r'Predecessor Limit $\Delta t_{\mathrm{min}} = 1.0\times 10^{-8}\,\mathrm{s}$')
    ax.axhline(1.0e-11, color='g', linestyle='--', linewidth=1.5, label=r'F1753 Relaxed Limit $\Delta t_{\mathrm{min}} = 1.0\times 10^{-11}\,\mathrm{s}$')

    # Annotate breakthrough
    ax.annotate('Breakthrough:\nIncs 202-204 solve\nbelow 1e-8 down to 6e-11',
                xy=(203, 6.445e-10), xytext=(193, 1e-10),
                arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
                fontsize=9, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.8))

    ax.set_title(r'(b) Solver Time Increment $\Delta t$ at Hole Breach', fontsize=12, fontweight='bold')
    ax.set_xlabel('Step 2 Increment Number', fontsize=11)
    ax.set_ylabel(r'Time Increment $\Delta t$ [$\mathrm{s}$]', fontsize=11)
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)
    ax.set_ylim(1e-12, 1e-2)

    # ----------------------------------------------------
    # Panel (c): Damage Violation Spatial Breakdown
    # ----------------------------------------------------
    ax = axes[1, 0]
    regimes = [r'Severed Wake' + '\n' + r'($d \geq 0.95$)',
               r'Process Zone' + '\n' + r'($0.05 \leq d < 0.95$)',
               r'Elastic Bulk' + '\n' + r'($d < 0.05$)']
    counts = [1610, 175, 20]
    pcts = [c / 93865.0 * 100.0 for c in counts]
    colors = ['#d95f02', '#7570b3', '#1b9e77']

    bars = ax.bar(regimes, counts, color=colors, edgecolor='black', width=0.55)
    for bar, count, pct in zip(bars, counts, pcts):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 30,
                f'{count:,} IPs\n({pct:.3f}%)',
                ha='center', va='bottom', fontsize=9, fontweight='bold')

    ax.set_title(r'(c) Non-Monotonic Damage Increment Scope ($\Delta d < -10^{-5}$)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Number of Integration Points (Total: 93,865)', fontsize=11)
    ax.set_ylim(0, 2000)
    ax.grid(True, axis='y', linestyle='--', alpha=0.6)

    # Text box for history monotonicity
    ax.text(0.55, 0.65,
            r"History Monotonicity ($\Delta\mathcal{H} \geq 0$):" + "\n"
            "  100.000% SATISFIED\n"
            r"  min $\Delta\mathcal{H} = 0.000000\,\mathrm{MPa}$" + "\n"
            "  Zero negative violations\n"
            "  across all 93,865 IPs.",
            transform=ax.transAxes, fontsize=9.5, verticalalignment='top',
            bbox=dict(boxstyle='round,pad=0.4', facecolor='#e6f5d0', edgecolor='#4dac26', linewidth=1.5))

    # ----------------------------------------------------
    # Panel (d): 5-Gate Acceptance Evaluation Matrix
    # ----------------------------------------------------
    ax = axes[1, 1]
    ax.axis('off')

    table_data = [
        ["Gate", "Target Criterion", "Observed Value", "Status"],
        ["G1: Checkpoint Parity", "|dF|/F <= 0.01% at Inc 251", "0.000000% (Bitwise 100%)", "PASS"],
        ["G2: Continuation", "uy > 0.007677 mm (t > 0.5677s)", "uy = 0.007677 mm (3 new incs)", "PARTIAL*"],
        ["G3: Damage Irreversibility", "min Delta d >= -1.0e-5", "min Delta d = -1.064e-3", "FAIL"],
        ["G4: History Monotonicity", "min Delta H >= 0.0 MPa", "min Delta H = 0.000000 MPa", "PASS"],
        ["G5: Wake Residual Diag.", "min_{d>0.95} Delta d >= -2.5e-4", "min wake Delta d = -1.064e-3", "FAIL**"]
    ]

    col_widths = [0.26, 0.38, 0.26, 0.14]
    tab = ax.table(cellText=table_data, colWidths=col_widths, loc='center', cellLoc='center')
    tab.auto_set_font_size(False)
    tab.set_fontsize(9.5)
    tab.scale(1.0, 1.7)

    # Style header
    for j in range(4):
        tab[(0, j)].set_facecolor('#2b5c8f')
        tab[(0, j)].set_text_props(color='white', fontweight='bold')

    # Color status cells
    status_colors = {
        "PASS": '#c7e9c0',
        "PARTIAL*": '#fff7bc',
        "FAIL": '#fcae91',
        "FAIL**": '#fcae91'
    }
    for row_idx in range(1, 6):
        status_text = table_data[row_idx][3]
        tab[(row_idx, 3)].set_facecolor(status_colors.get(status_text, 'white'))
        tab[(row_idx, 3)].set_text_props(fontweight='bold')
        for col_idx in range(3):
            tab[(row_idx, col_idx)].set_facecolor('#f7f7f7' if row_idx % 2 == 1 else 'white')

    ax.set_title('(d) Task F1753 Authoritative Gate Evaluation Matrix', fontsize=12, fontweight='bold', pad=15)

    # Footnote
    ax.text(0.0, 0.08,
            "*Solver broke through 1e-8 bottleneck solving Incs 202-204, but pinned at 1e-11 limit without secondary ligament traversal.\n"
            "**Wake equilibrium adjustments confirmed as characteristic of unprojected structural Newton-Raphson solve.",
            transform=ax.transAxes, fontsize=8, style='italic', color='#555555')

    # Save outputs
    out_png = 'results/figures/fig_f1753_continuation_response.png'
    out_pdf = 'results/figures/fig_f1753_continuation_response.pdf'
    plt.savefig(out_png, dpi=300, bbox_inches='tight')
    plt.savefig(out_pdf, bbox_inches='tight')
    plt.close()
    print("Saved publication figures:")
    print("  %s" % out_png)
    print("  %s" % out_pdf)

if __name__ == '__main__':
    main()
