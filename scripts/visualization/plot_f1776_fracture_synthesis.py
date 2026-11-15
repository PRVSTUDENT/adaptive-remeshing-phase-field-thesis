# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1776_fracture_synthesis.py
======================================================
Generates publication-quality 2-panel figure synthesizing coupled phase-field
fracture response for Task F1776 on Method A adapted meshes:
Panel (a): Macroscopic Force-Displacement Response F(u)
Panel (b): Total Energy Evolution (Elastic Strain vs Dissipated Fracture Energy)

Authors: Gemini Antigravity
Date: 15 November 2026
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import sys
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)
VAL_DIR = os.path.join(REPO_ROOT, "results", "validation", "f1776_case1_case5_fracture")
FIG_DIR = os.path.join(REPO_ROOT, "results", "figures")
MA_FIG_DIR = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

from scripts.validation.parse_f1776_fracture_responses import parse_dat_file, parse_energy_csv

def main():
    case1_dat = os.path.join(VAL_DIR, "case1_fracture.dat")
    case5_dat = os.path.join(VAL_DIR, "case5_fracture.dat")
    case1_csv = os.path.join(VAL_DIR, "case1_energy_balance.csv")
    case5_csv = os.path.join(VAL_DIR, "case5_energy_balance.csv")
    
    u1, f1 = parse_dat_file(case1_dat)
    e1 = parse_energy_csv(case1_csv)
    
    u5, f5 = parse_dat_file(case5_dat)
    e5 = parse_energy_csv(case5_csv)
    
    # Unit conversions:
    # u in mm -> convert to um for plotting (u * 1000)
    # E in kN*mm = J
    u1_um = u1 * 1000.0
    u5_um = u5 * 1000.0
    
    # Energy arrays
    # e: (step, inc, tot_time, step_time, e_elas, e_frac, e_tot)
    t1 = np.array([row[2] for row in e1])
    e1_elas = np.array([row[4] for row in e1]) * 1000.0 # mJ
    e1_frac = np.array([row[5] for row in e1]) * 1000.0 # mJ
    
    t5 = np.array([row[2] for row in e5])
    e5_elas = np.array([row[4] for row in e5]) * 1000.0 # mJ
    e5_frac = np.array([row[5] for row in e5]) * 1000.0 # mJ
    
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 11,
        "axes.labelsize": 12,
        "axes.titlesize": 12,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.titlesize": 13,
        "lines.linewidth": 1.8
    })
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.8), dpi=300)
    
    # -------------------------------------------------------------
    # Panel (a): Load-Displacement Curves F(u)
    # -------------------------------------------------------------
    ax1.plot(u1_um, f1, color="#1f77b4", label="Case 1: Mode-I Notch ($N=20,232$ el)", zorder=3)
    ax1.plot(u5_um, f5, color="#d62728", label="Case 5: Seven-Hole Plate ($N=15,330$ el)", zorder=3)
    
    # Highlight Peak Loads
    f1_max = np.max(f1)
    u1_max = u1_um[np.argmax(f1)]
    f5_max = np.max(f5)
    u5_max = u5_um[np.argmax(f5)]
    
    ax1.scatter([u1_max], [f1_max], color="#1f77b4", edgecolor="black", s=60, zorder=4)
    ax1.annotate(f"Case 1 Peak: {f1_max:.4f} N\n($u = {u1_max:.2f}\\,\\mu$m)\nDrop: 99.76%",
                 xy=(u1_max, f1_max), xytext=(u1_max + 0.3, f1_max - 0.15),
                 arrowprops=dict(arrowstyle="->", color="#1f77b4", lw=1.2),
                 fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#e6f2ff", ec="#1f77b4", alpha=0.9))
    
    ax1.scatter([u5_max], [f5_max], color="#d62728", edgecolor="black", s=60, zorder=4)
    ax1.annotate(f"Case 5 Peak: {f5_max:.4f} N\n($u = {u5_max:.2f}\\,\\mu$m)\nDrop: 99.89%",
                 xy=(u5_max, f5_max), xytext=(u5_max - 2.2, f5_max - 0.28),
                 arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
                 fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="#ffe6e6", ec="#d62728", alpha=0.9))
    
    ax1.set_xlabel("Applied Prescribed Displacement $u$ [$\\mu$m]")
    ax1.set_ylabel("Total Reaction Force $F$ [N]")
    ax1.set_title("(a) Coupled Phase-Field Fracture Response $F(u)$")
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(loc="upper right", framealpha=0.95)
    ax1.set_xlim(0, max(np.max(u1_um), np.max(u5_um)) * 1.05)
    ax1.set_ylim(-0.02, max(f1_max, f5_max) * 1.12)
    
    # -------------------------------------------------------------
    # Panel (b): Total Energy Evolution E_elas vs E_frac
    # -------------------------------------------------------------
    ax2.plot(t1, e1_elas, color="#1f77b4", linestyle="--", label="Case 1: Elastic Strain Energy $E_{\\mathrm{elas}}$", zorder=3)
    ax2.plot(t1, e1_frac, color="#1f77b4", linestyle="-", label="Case 1: Dissipated Fracture Energy $E_{\\mathrm{frac}}$", zorder=3)
    
    ax2.plot(t5, e5_elas, color="#d62728", linestyle="--", label="Case 5: Elastic Strain Energy $E_{\\mathrm{elas}}$", zorder=3)
    ax2.plot(t5, e5_frac, color="#d62728", linestyle="-", label="Case 5: Dissipated Fracture Energy $E_{\\mathrm{frac}}$", zorder=3)
    
    # Vertical line separating Step 1 (elastic) and Step 2 (fracture)
    ax2.axvline(x=1.0, color="gray", linestyle=":", lw=1.5, label="Step 1 / Step 2 Interface ($t=1.0$)")
    
    ax2.set_xlabel("Total Pseudo-Time $t$ [-]")
    ax2.set_ylabel("Energy Component [mJ]")
    ax2.set_title("(b) Thermodynamic Energy Balance & Dissipation Evolution")
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(loc="upper left", framealpha=0.95, fontsize=8.5)
    ax2.set_xlim(0, max(np.max(t1), np.max(t5)) * 1.02)
    ax2.set_ylim(-0.05, max(np.max(e1_frac), np.max(e5_frac)) * 1.15)
    
    fig.suptitle("Task F1776: Coupled Phase-Field Fracture Validation on Method A Adapted Meshes\n(Frozen Shared UEL: f42_mixed_uel.for | Abaqus 2023 Classic Intel Fortran)",
                 fontsize=13, fontweight="bold", y=0.98)
    
    plt.tight_layout()
    
    # Save outputs
    png_path = os.path.join(FIG_DIR, "fig_f1776_coupled_fracture_synthesis.png")
    pdf_path = os.path.join(FIG_DIR, "fig_f1776_coupled_fracture_synthesis.pdf")
    plt.savefig(png_path, dpi=300)
    plt.savefig(pdf_path)
    
    # Also save to report directory
    ma_png_path = os.path.join(MA_FIG_DIR, "fig_f1776_coupled_fracture_synthesis.png")
    ma_pdf_path = os.path.join(MA_FIG_DIR, "fig_f1776_coupled_fracture_synthesis.pdf")
    plt.savefig(ma_png_path, dpi=300)
    plt.savefig(ma_pdf_path)
    
    print(f"Generated publication figure:\n  {png_path}\n  {pdf_path}")
    print(f"  {ma_png_path}\n  {ma_pdf_path}")

if __name__ == "__main__":
    main()
