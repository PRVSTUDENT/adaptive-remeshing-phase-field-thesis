#!/usr/bin/env python3
"""Generate individual publication-quality figures for each Mode-II H1 endpoint sweep job.
"""

import csv
import matplotlib.pyplot as plt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_BASE = ROOT / "runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence"
FIGURES_BASE = ROOT / "results/figures/mode_ii_h1_endpoint_sweep"

JOBS = [
    ("1379481.mmaster02", "u015", "0.015"),
    ("1379482.mmaster02", "u020", "0.020"),
    ("1379483.mmaster02", "u030", "0.030"),
    ("1379484.mmaster02", "u040", "0.040"),
]

def main():
    for job_id, var_name, target_u1 in JOBS:
        job_fig_dir = FIGURES_BASE / job_id
        job_fig_dir.mkdir(parents=True, exist_ok=True)
        
        curve_csv = EVIDENCE_BASE / job_id / "extracted/rf1_u1_curve.csv"
        if not curve_csv.is_file():
            print(f"Skipping {job_id}, missing {curve_csv}")
            continue
            
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
        ax.plot(u1_vals, rf1_vals, color="#1f77b4", linewidth=2.0, label=f"Mode-II H1 {var_name} ($U_1={target_u1}$ mm)")
        
        max_rf1 = max(rf1_vals)
        max_idx = rf1_vals.index(max_rf1)
        max_u1 = u1_vals[max_idx]
        
        ax.plot(max_u1, max_rf1, "ro", markersize=6, label=f"Peak: {max_rf1:.4f} kN @ {max_u1:.4f} mm")
        
        ax.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
        ax.set_ylabel(r"Reaction Force $RF_1$ [kN]", fontsize=11)
        ax.set_title(f"Mode-II Pure Shear Response ({var_name}, Job {job_id})", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="upper right", fontsize=10)
        
        fig.tight_layout()
        fig.savefig(job_fig_dir / "rf1_u1_response.png", dpi=300)
        fig.savefig(job_fig_dir / "rf1_u1_response.pdf")
        plt.close(fig)
        
        # Figure 2: Phase-field SDV15 vs U1
        fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)
        ax.plot(u1_vals, sdv15_vals, color="#d62728", linewidth=2.0, label=r"Max Phase Field $\max(d)$ (SDV15)")
        ax.axhline(0.5, color="black", linestyle=":", linewidth=1.2, label=r"Damage Threshold $d = 0.5$")
        ax.axhline(1.0, color="gray", linestyle="--", linewidth=1.0, label=r"Upper Bound $d = 1.0$")
        
        ax.set_xlabel(r"Applied Shear Displacement $U_1$ [mm]", fontsize=11)
        ax.set_ylabel(r"Maximum Phase Field $d$", fontsize=11)
        ax.set_title(f"Mode-II Phase-Field Evolution ({var_name}, Job {job_id})", fontsize=11)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.legend(loc="lower right", fontsize=10)
        
        fig.tight_layout()
        fig.savefig(job_fig_dir / "phase_field_sdv15_evolution.png", dpi=300)
        fig.savefig(job_fig_dir / "phase_field_sdv15_evolution.pdf")
        plt.close(fig)
        
        print(f"Generated figures for {job_id} ({var_name}) in {job_fig_dir}")

if __name__ == "__main__":
    main()
