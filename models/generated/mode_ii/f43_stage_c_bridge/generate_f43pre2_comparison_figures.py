#!/usr/bin/env python3
"""
Generate Scientific Comparison Figures for F43PRE2_GEOM (1385392) vs F43PRE1 (1384674).
"""

import os
import sys
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def generate_figures(summary_path, evidence_dir, out_dir):
    with open(summary_path, 'r') as f:
        summary = json.load(f)

    # 1. Load-Displacement RF1-U1 old vs new
    csv_new = os.path.join(evidence_dir, "F43PRE2_1385392_RF1_U1.csv")
    csv_old = os.path.join(evidence_dir, "F43PRE1_1384674_RF1_U1.csv")

    data_new = np.genfromtxt(csv_new, delimiter=',', skip_header=1)
    data_old = np.genfromtxt(csv_old, delimiter=',', skip_header=1)

    u_new = data_new[:, 2]
    rf_new_n = data_new[:, 3]

    u_old = data_old[:, 2]
    rf_old_n = data_old[:, 3] * 1000.0  # Convert old kN raw values to N

    plt.figure(figsize=(7, 5))
    plt.plot(u_old, rf_old_n, 'b--', label='Reference F43PRE1 (1384674, Orphan Mesh, Converted from kN)', linewidth=2)
    plt.plot(u_new, rf_new_n, 'r-', label='Geometry F43PRE2_GEOM (1385392, Native CAE)', linewidth=1.5)
    plt.xlabel(r'Prescribed Shear Displacement $U_1$ (mm)', fontsize=11)
    plt.ylabel(r'Shear Reaction Force $RF_1$ (N)', fontsize=11)
    plt.title('Load-Displacement Response ($U_1 - RF_1$ in N)', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper left', frameon=True)
    plt.tight_layout()
    fig1_path = os.path.join(out_dir, "f43pre2_vs_1384674_rf1_u1_comparison.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print("Saved Figure 1: " + fig1_path)

    # 2. Histogram / Distribution of MISESERI
    old_stats = summary["miseseri_statistics"]["old"]
    new_stats = summary["miseseri_statistics"]["new"]

    plt.figure(figsize=(7, 5))
    bins = np.linspace(0, 10, 50)
    plt.hist(np.clip(summary["miseseri_statistics"]["new"]["mean"], 0, 10), bins=bins, alpha=0.7, color='crimson', label='F43PRE2_GEOM (1385392)')
    plt.xlabel('MISESERI Error Indicator Value', fontsize=11)
    plt.ylabel('Element Count', fontsize=11)
    plt.title('MISESERI Error Indicator Value Distribution', fontsize=12, fontweight='bold')
    plt.grid(True, linestyle=':', alpha=0.6)
    plt.legend(loc='upper right')
    plt.tight_layout()
    fig5_path = os.path.join(out_dir, "f43pre2_miseseri_distribution.png")
    plt.savefig(fig5_path, dpi=300)
    plt.close()
    print("Saved Figure 5: " + fig5_path)

    print("All comparison figures generated successfully.")

if __name__ == "__main__":
    evidence_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    summary_path = os.path.join(evidence_dir, "F43PRE2_VS_1384674_COMPARISON_SUMMARY.json")
    out_dir = sys.argv[2] if len(sys.argv) > 2 else evidence_dir
    generate_figures(summary_path, evidence_dir, out_dir)
