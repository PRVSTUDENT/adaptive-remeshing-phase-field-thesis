# -*- coding: utf-8 -*-
"""
plot_f1692_sec43_load_displacement.py
=====================================
Plots comparative load-displacement curves for Pandey-Kumar Section 4.3 benchmark:
- Task F1688 (Monolithic Newton, h = 5.26 l0): Diverged at Inc 64 (uy = 0.081 mm)
- Task F1690 (Monolithic Newton, h = 2.11 l0): Diverged at Inc 170 (uy = 0.0687 mm)
- Task F1692 (Staggered Operator Split): Solved to uy = 1.500 mm (Exit 0, 4,500 incs)
"""

import os
import sys
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")
F1692_CSV = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "f1692_staggered_rf2_history.csv")

def main():
    u_f1692 = []
    rf_f1692 = []

    with open(F1692_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_f1692.append(float(r["u2_mm"]))
            rf_f1692.append(float(r["rf2_kN"]))

    fig, ax = plt.subplots(figsize=(7.0, 4.8), dpi=300)

    # Plot F1692 Staggered curve
    ax.plot(u_f1692, rf_f1692, color="#1f77b4", lw=2.0, label="Task F1692: Staggered Operator Split (Exit 0 to $u_y = 1.5$ mm)")

    # Highlight initial peak and load collapse
    p_max = max(rf_f1692)
    idx_pmax = rf_f1692.index(p_max)
    u_pmax = u_f1692[idx_pmax]
    ax.scatter([u_pmax], [p_max], color="#d62728", s=50, zorder=5)
    ax.annotate(r"$P_{\max} = 6.47$ kN ($u_y = 0.095$ mm)",
                xy=(u_pmax, p_max), xytext=(u_pmax + 0.12, p_max - 0.5),
                arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
                fontsize=9, fontweight="bold", color="#d62728")

    # Mark divergence endpoints of predecessors
    # F1688: u_y = 0.081 mm, P ~ 5.95 kN
    ax.scatter([0.0810], [5.949], marker="X", color="#2ca02c", s=80, zorder=6,
               label=r"Task F1688 Monolithic Divergence ($u_y = 0.081$ mm, Inc 64)")

    # F1690: u_y = 0.0687 mm, P ~ 5.25 kN
    ax.scatter([0.0687], [5.250], marker="X", color="#ff7f0e", s=80, zorder=6,
               label=r"Task F1690 Monolithic Divergence ($u_y = 0.0687$ mm, Inc 170)")

    # Mark complete primary ligament severance
    ax.annotate("Primary Ligament Severance\n($RF_2 < 2$ N, 99.98% load drop)",
                xy=(0.73, 0.002), xytext=(0.55, 1.8),
                arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.2),
                fontsize=8.5, color="#1f77b4")

    # Mark secondary crack propagation across right ligament
    ax.annotate("Secondary Crack Growth\nAcross Right Ligament to Edge",
                xy=(1.25, 0.0015), xytext=(0.95, 3.2),
                arrowprops=dict(arrowstyle="->", color="#333333", lw=1.2),
                fontsize=8.5, color="#333333")

    ax.set_xlim(-0.02, 1.55)
    ax.set_ylim(-0.2, 7.2)
    ax.set_xlabel(r"Applied Pin Displacement $u_y$ (mm)", fontsize=11)
    ax.set_ylabel(r"Tensile Reaction Force $RF_2$ (kN)", fontsize=11)
    ax.set_title("Pandey--Kumar Section 4.3 Plate with Hole Benchmark\nStructural Load--Displacement Response and Solver Divergence Comparison",
                 fontsize=11, fontweight="bold", pad=10)

    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", fontsize=8.5)

    plt.tight_layout()
    pdf_path = os.path.join(FIG_DIR, "fig_f1692_sec43_load_displacement.pdf")
    png_path = os.path.join(FIG_DIR, "fig_f1692_sec43_load_displacement.png")
    fig.savefig(pdf_path, bbox_inches="tight")
    fig.savefig(png_path, bbox_inches="tight")
    plt.close(fig)

    print("Saved publication load-displacement figures:")
    print("  %s" % pdf_path)
    print("  %s" % png_path)

if __name__ == "__main__":
    main()
