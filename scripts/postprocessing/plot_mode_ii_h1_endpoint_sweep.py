#!/usr/bin/env python3
"""Generate figures comparing all four Mode-II H1 endpoint sweep variants (u015, u020, u030, u040).
"""

import csv
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_BASE = ROOT / "runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence"
FIGURES_DIR = ROOT / "results/figures/mode_ii_h1_endpoint_sweep"

VARIANTS = [
    ("u015", "1379481.mmaster02", r"$U_1=0.015$ mm", "#1f77b4"),
    ("u020", "1379482.mmaster02", r"$U_1=0.020$ mm", "#2ca02c"),
    ("u030", "1379483.mmaster02", r"$U_1=0.030$ mm", "#ff7f0e"),
    ("u040", "1379484.mmaster02", r"$U_1=0.040$ mm", "#d62728"),
]

def main():
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)
    
    for var_name, job_id, label, color in VARIANTS:
        csv_path = EVIDENCE_BASE / job_id / "extracted/rf1_u1_curve.csv"
        if not csv_path.is_file():
            print(f"Warning: {csv_path} not found.")
            continue
            
        u1_vals = []
        rf1_vals = []
        sdv15_vals = []
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                u1_vals.append(float(r["rp_u1"]))
                rf1_vals.append(float(r["rp_rf1"]))
                sdv15_vals.append(float(r["max_sdv15"]))
                
        ax1.plot(u1_vals, rf1_vals, label=label, color=color, linewidth=1.8)
        ax2.plot(u1_vals, sdv15_vals, label=label, color=color, linewidth=1.8)
        
    # Formatting Figure 1: RF1-U1
    ax1.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
    ax1.set_ylabel(r"Reaction Force $RF_1$ [kN]", fontsize=11)
    ax1.set_title(r"Mode-II $H_1$ Endpoint Sweep: Force–Displacement", fontsize=11)
    ax1.grid(True, linestyle="--", alpha=0.6)
    ax1.legend(loc="upper right", fontsize=10)
    
    # Formatting Figure 2: SDV15 evolution
    ax2.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
    ax2.set_ylabel(r"Maximum Phase Field $\max(d)$ (SDV15)", fontsize=11)
    ax2.set_title(r"Mode-II $H_1$ Endpoint Sweep: Damage Evolution", fontsize=11)
    ax2.axhline(1.0, color="black", linestyle=":", linewidth=1.0, label="Theoretical Bound d=1.0")
    ax2.grid(True, linestyle="--", alpha=0.6)
    ax2.legend(loc="lower right", fontsize=10)
    
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "m2h1_endpoint_sweep_comparison.png", dpi=300)
    fig.savefig(FIGURES_DIR / "m2h1_endpoint_sweep_comparison.pdf")
    plt.close(fig)
    print(f"Saved comparison plot to {FIGURES_DIR / 'm2h1_endpoint_sweep_comparison.png'}")

if __name__ == "__main__":
    main()
