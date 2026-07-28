#!/usr/bin/env python3
"""Generate publication-quality figures for Mode-II H1 uniform-reference serial solver run 1379433.mmaster02.
"""

import os
import csv
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_DIR = ROOT / "runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02"
FIGURES_DIR = ROOT / "results/figures/mode_ii_h1/1379433.mmaster02"

def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    curve_csv = EVIDENCE_DIR / "extracted/rf1_u1_curve.csv"
    if not curve_csv.is_file():
        print(f"Error: {curve_csv} not found.")
        return
        
    u1_vals = []
    rf1_vals = []
    sdv15_vals = []
    
    with open(curve_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u1_vals.append(float(r["rp_u1"]))
            rf1_vals.append(float(r["rp_rf1"]))
            sdv15_vals.append(float(r["max_sdv15"]))
            
    # Figure 1: RF1 vs U1
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
    ax.plot(u1_vals, rf1_vals, color="#1f77b4", linewidth=2.0, label=r"Mode-II $H_1$ Uniform ($N_{\mathrm{elem}}=12064$)")
    
    max_rf1 = max(rf1_vals)
    max_idx = rf1_vals.index(max_rf1)
    max_u1 = u1_vals[max_idx]
    
    ax.plot(max_u1, max_rf1, "ro", markersize=6, label=f"Peak: {max_rf1:.4f} kN @ {max_u1:.4f} mm")
    
    ax.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
    ax.set_ylabel(r"Reaction Force $RF_1$ [kN]", fontsize=11)
    ax.set_title(r"Mode-II Pure Shear Reference Response ($H_1$ Uniform)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10)
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "rf1_u1_response.png", dpi=300)
    fig.savefig(FIGURES_DIR / "rf1_u1_response.pdf")
    plt.close(fig)
    print(f"Saved RF1-U1 plot to {FIGURES_DIR / 'rf1_u1_response.png'}")
    
    # Figure 2: Phase-field SDV15 vs U1
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
    ax.plot(u1_vals, sdv15_vals, color="#d62728", linewidth=2.0, label=r"Max Phase Field $\max(d)$ (SDV15)")
    ax.axhline(0.5, color="black", linestyle=":", linewidth=1.2, label=r"Damage Threshold $d = 0.5$")
    
    ax.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
    ax.set_ylabel(r"Maximum Phase Field $d$", fontsize=11)
    ax.set_title(r"Mode-II Phase-Field Damage Evolution ($H_1$ Uniform)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10)
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "phase_field_sdv15_evolution.png", dpi=300)
    fig.savefig(FIGURES_DIR / "phase_field_sdv15_evolution.pdf")
    plt.close(fig)
    print(f"Saved SDV15 plot to {FIGURES_DIR / 'phase_field_sdv15_evolution.png'}")

if __name__ == "__main__":
    main()
