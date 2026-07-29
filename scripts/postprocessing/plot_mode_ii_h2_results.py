#!/usr/bin/env python
"""Generate result figures for Mode-II H2 uniform reference job 1379578.mmaster02."""

from __future__ import print_function

import csv
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def main():
    csv_path = os.path.join(REPO_ROOT, "runs", "hpc", "stage_f", "mode_ii_h2", "evidence", "1379578.mmaster02", "extracted", "rf1_u1_curve.csv")
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "mode_ii_h2", "1379578.mmaster02")
    if not os.path.exists(fig_dir):
        os.makedirs(fig_dir)

    if not os.path.exists(csv_path):
        print("ERROR: CSV not found at %s" % csv_path, file=sys.stderr)
        return 1

    u1_vals = []
    rf1_vals = []
    dmax_vals = []

    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u1_vals.append(float(r["u1"]))
            rf1_vals.append(float(r["rf1"]))
            dmax_vals.append(float(r["d_max"]))

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        # 1. RF1 vs U1 Response Curve
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(u1_vals, rf1_vals, "b-", linewidth=2, label="H2 Uniform Reference (33,852 elements)")
        ax.plot(u1_vals[-1], rf1_vals[-1], "ro", markersize=7, label=f"Endpoint: U1={u1_vals[-1]:.4f} mm, RF1={rf1_vals[-1]:.4f} kN")
        ax.set_title("Mode-II H2 Reference Shear Response (Job 1379578.mmaster02)")
        ax.set_xlabel("Displacement U1 (mm)")
        ax.set_ylabel("Shear Reaction Force RF1 (kN)")
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper left")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "01_rf1_u1_response.png"), dpi=200)
        plt.close(fig)

        # 2. Phase-field Max Damage vs U1
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.plot(u1_vals, dmax_vals, "r-", linewidth=2, label="Max Phase-Field Damage d_max")
        ax.set_title("Mode-II H2 Phase-Field Damage Evolution")
        ax.set_xlabel("Displacement U1 (mm)")
        ax.set_ylabel("Max Damage d_max")
        ax.set_ylim(-0.05, 1.05)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper left")
        plt.tight_layout()
        fig.savefig(os.path.join(fig_dir, "02_damage_max_evolution.png"), dpi=200)
        plt.close(fig)

        print("Successfully generated 2 figures in %s" % fig_dir)
    except Exception as exc:
        print("WARN: Plotting failed: %s" % exc, file=sys.stderr)

    return 0

if __name__ == "__main__":
    sys.exit(main())
