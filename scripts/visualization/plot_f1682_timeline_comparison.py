# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1682_timeline_comparison.py
=======================================================
Task F1682: Publication-Quality Fracture Timeline and Crack Trajectory Comparison
Generates:
  1. MA_AdaptiveRemeshing_Report_2026/figures/f1682_timeline_comparison.pdf / .png
     - Panel A: P(u2) Load-Displacement with Annotated Fracture Stages
     - Panel B: Damage Census (Broken Elements d >= 0.80) & d_max vs Imposed Displacement
  2. MA_AdaptiveRemeshing_Report_2026/figures/f1682_crack_trajectory_comparison.pdf / .png
     - Physical specimen 2D space (x, y) comparing coarse vs refined crack paths
"""
import os
import sys
import csv
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def load_progression(csv_path):
    data = {
        "u2": [], "rf2": [], "d_max": [], "cnt_080": [], "tip_x": [], "tip_y": [], "step": []
    }
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            data["u2"].append(float(r["u2_top"]))
            data["rf2"].append(float(r["rf2_top"]))
            data["d_max"].append(float(r["d_max"]))
            data["cnt_080"].append(int(r["cnt_ge_080"]))
            data["tip_x"].append(float(r["tip_x"]))
            data["tip_y"].append(float(r["tip_y"]))
            data["step"].append(r["step_name"])
    return data

def generate_plots(coarse_csv, prod_csv, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    c_data = load_progression(coarse_csv)
    p_data = load_progression(prod_csv)

    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 13,
        "lines.linewidth": 1.8,
        "grid.alpha": 0.4
    })

    # Figure 1: Two-Panel Load-Displacement & Damage Growth Comparison
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8.5, 9.5), sharex=True)

    # Panel A: P(u2)
    ax1.plot(c_data["u2"], c_data["rf2"], color="#7f7f7f", linestyle="--", label="Coarse Donor (2,906 FEs, Job 1421063)")
    ax1.plot(p_data["u2"], p_data["rf2"], color="#d62728", linestyle="-", label="Refined Production (20,213 FEs, Job 1421142)")
    ax1.set_ylabel(r"Reaction Force $P$ [kN]")
    ax1.set_title("(a) Structural Load--Displacement Response $P(u_2)$", fontweight="bold")
    ax1.grid(True, linestyle=":")
    ax1.legend(loc="upper right", frameon=True)

    # Annotations on Panel A
    p_max_c = max(c_data["rf2"])
    p_max_p = max(p_data["rf2"])
    u_at_pmax_p = p_data["u2"][p_data["rf2"].index(p_max_p)]
    ax1.annotate(f"Coarse Peak: {p_max_c:.3f} kN\n(Artificially Stiff)",
                 xy=(0.0057, p_max_c), xytext=(0.0030, 0.68),
                 arrowprops=dict(arrowstyle="->", color="#555555", lw=1.2))
    ax1.annotate(f"Refined Peak: {p_max_p:.3f} kN\n(-18.8% Softening)",
                 xy=(u_at_pmax_p, p_max_p), xytext=(0.0068, 0.60),
                 arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2))
    ax1.annotate("Primary Hole Arrest\n($u_2 \\approx 0.0075$ mm)",
                 xy=(0.00752, 0.15), xytext=(0.0080, 0.35),
                 arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.2))
    ax1.annotate("Secondary Snap-Through\n(Ligament Severance)",
                 xy=(0.00776, 0.045), xytext=(0.0085, 0.15),
                 arrowprops=dict(arrowstyle="->", color="#2ca02c", lw=1.2))

    # Panel B: Broken Elements Census & d_max
    ax2.plot(c_data["u2"], c_data["cnt_080"], color="#7f7f7f", linestyle="--", label="Coarse Broken FEs ($d \\geq 0.80$)")
    ax2.plot(p_data["u2"], p_data["cnt_080"], color="#1f77b4", linestyle="-", label="Refined Broken FEs ($d \\geq 0.80$)")
    ax2.set_xlabel(r"Imposed Displacement $u_2$ [mm]")
    ax2.set_ylabel(r"Broken Element Count ($d \geq 0.80$)")
    ax2.set_title("(b) Evolution of Fully Fractured Elements", fontweight="bold")
    ax2.grid(True, linestyle=":")
    ax2.legend(loc="upper left", frameon=True)

    # Secondary Y-axis for d_max
    ax2_twin = ax2.twinx()
    ax2_twin.plot(c_data["u2"], c_data["d_max"], color="#9467bd", linestyle=":", alpha=0.6, label=r"Coarse $d_{\max}$")
    ax2_twin.plot(p_data["u2"], p_data["d_max"], color="#ff7f0e", linestyle="-.", alpha=0.7, label=r"Refined $d_{\max}$")
    ax2_twin.set_ylabel(r"Maximum Phase Field $d_{\max}$", color="#ff7f0e")
    ax2_twin.tick_params(axis="y", labelcolor="#ff7f0e")
    ax2_twin.set_ylim(-0.05, 1.15)

    plt.tight_layout()
    fig1_pdf = os.path.join(out_dir, "f1682_timeline_comparison.pdf")
    fig1_png = os.path.join(out_dir, "f1682_timeline_comparison.png")
    fig.savefig(fig1_pdf, dpi=300)
    fig.savefig(fig1_png, dpi=300)
    plt.close(fig)
    print(f"Generated Figure 1: {fig1_pdf} and {fig1_png}")

    # Figure 2: Crack Tip Kinematics (x, y) Trajectory
    fig2, ax = plt.subplots(figsize=(8, 6.5))

    # Specimen boundaries and hole
    ax.axhline(0.50, color="#888888", linestyle=":", label="Initial Notch Centerline ($y = 0.50$)")
    hole = plt.Circle((0.65, 0.65), 0.10, color="#cccccc", ec="#333333", lw=1.5, zorder=2, label="Off-Axis Hole ($r=0.10$)")
    ax.add_patch(hole)

    # Filter tip points that advanced beyond notch tip (x >= 0.50)
    c_tips_x = [x for x, y in zip(c_data["tip_x"], c_data["tip_y"]) if x >= 0.50]
    c_tips_y = [y for x, y in zip(c_data["tip_x"], c_data["tip_y"]) if x >= 0.50]
    p_tips_x = [x for x, y in zip(p_data["tip_x"], p_data["tip_y"]) if x >= 0.50]
    p_tips_y = [y for x, y in zip(p_data["tip_x"], p_data["tip_y"]) if x >= 0.50]

    ax.scatter(c_tips_x, c_tips_y, color="#7f7f7f", s=15, alpha=0.6, label="Coarse Donor Tip Positions")
    ax.scatter(p_tips_x, p_tips_y, color="#d62728", s=25, alpha=0.8, label="Refined Production Tip Positions")

    ax.set_xlim(0.45, 1.02)
    ax.set_ylim(0.45, 0.80)
    ax.set_xlabel(r"Horizontal Coordinate $x$ [mm]")
    ax.set_ylabel(r"Vertical Coordinate $y$ [mm]")
    ax.set_title("Crack Trajectory Kinematics & Hole Interaction", fontweight="bold")
    ax.grid(True, linestyle=":")
    ax.legend(loc="lower right", frameon=True)

    fig2_pdf = os.path.join(out_dir, "f1682_crack_trajectory_comparison.pdf")
    fig2_png = os.path.join(out_dir, "f1682_crack_trajectory_comparison.png")
    fig2.savefig(fig2_pdf, dpi=300)
    fig2.savefig(fig2_png, dpi=300)
    plt.close(fig2)
    print(f"Generated Figure 2: {fig2_pdf} and {fig2_png}")

if __name__ == "__main__":
    coarse_p = "results/validation/f1682_coarse_all_frames_progression.csv"
    prod_p = "results/validation/f1682_prod_all_frames_progression.csv"
    figs_d = "MA_AdaptiveRemeshing_Report_2026/figures"
    if os.path.exists(coarse_p) and os.path.exists(prod_p):
        generate_plots(coarse_p, prod_p, figs_d)
    else:
        print("Waiting for both progression CSV files to exist before execution.")
