#!/usr/bin/env python3
"""Process Pair-2 (H1 and H2 FRACFIX) evidence, generate file inventories and comparison figures.

Jobs:
- 1386447.mmaster02 (M2REF_H1_FRACFIX, NPHYS = 12064)
- 1386448.mmaster02 (M2REF_H2_FRACFIX, NPHYS = 33852)
"""

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]

H0_CSV = ROOT / "runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/evidence/1379393.mmaster02/extracted/rf1_u1_curve.csv"
H1_DIR = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/evidence/1386447.mmaster02"
H2_DIR = ROOT / "models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/evidence/1386448.mmaster02"
FIG_DIR = ROOT / "results/figures/mode_ii_reference_convergence"

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def create_evidence_inventory(ev_dir: Path, job_id: str, case_name: str, task_id: str = "F43MODEREF13-PAIR2-CLOSEOUT1"):
    copied_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inventory_csv = ev_dir / "EVIDENCE_FILE_INVENTORY.csv"
    
    rows = []
    for f in sorted(ev_dir.iterdir()):
        if f.name == "EVIDENCE_FILE_INVENTORY.csv":
            continue
        rel_path = f.relative_to(ROOT).as_posix()
        src_cluster_path = f"/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/reference_convergence/{case_name}/evidence/{job_id}/{f.name}"
        fsize = f.stat().st_size
        sha = compute_sha256(f)
        rows.append({
            "repository_relative_path": rel_path,
            "source_cluster_path": src_cluster_path,
            "file_size_bytes": fsize,
            "sha256": sha,
            "copied_at_utc": copied_at,
            "job_id": job_id,
            "task_id": task_id,
            "source_revision": "20462bdc692f4459ae9885d6f4c18128f873c253",
        })
    
    with open(inventory_csv, "w", newline="", encoding="utf-8") as out:
        writer = csv.DictWriter(out, fieldnames=[
            "repository_relative_path", "source_cluster_path", "file_size_bytes",
            "sha256", "copied_at_utc", "job_id", "task_id", "source_revision"
        ])
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} entries to {inventory_csv}")
    return rows

def load_curve(csv_path: Path):
    u_list, rf_list, d_list = [], [], []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_val = None
            rf_val = None
            d_val = None
            for k in ["u1", "U1", "rp_u1", "RP_U1"]:
                if k in r and r[k] != "":
                    u_val = abs(float(r[k]))
                    break
            for k in ["rf1", "RF1", "rp_rf1", "RP_RF1"]:
                if k in r and r[k] != "":
                    rf_val = abs(float(r[k]))
                    break
            for k in ["d_max", "max_sdv15", "SDV15", "phase_max"]:
                if k in r and r[k] != "":
                    d_val = float(r[k])
                    break
            if u_val is not None and rf_val is not None:
                u_list.append(u_val)
                rf_list.append(rf_val)
                d_list.append(d_val if d_val is not None else 0.0)
    return u_list, rf_list, d_list

def plot_comparison():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    
    u_h0, rf_h0, d_h0 = load_curve(H0_CSV)
    u_h1, rf_h1, d_h1 = load_curve(H1_DIR / "rf1_u1_curve.csv")
    u_h2, rf_h2, d_h2 = load_curve(H2_DIR / "rf1_u1_curve.csv")
    
    # 1. Force-Displacement Comparison Plot
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.plot([u * 1000 for u in u_h0], [rf * 1000 for rf in rf_h0], "k--", label=r"H0 Baseline ($h=0.030\,\mathrm{mm}, N=3\,930$)", linewidth=1.5)
    ax.plot([u * 1000 for u in u_h1], [rf * 1000 for rf in rf_h1], "b-", label=r"H1 Refinement ($h=0.015\,\mathrm{mm}, N=12\,064$)", linewidth=1.8)
    ax.plot([u * 1000 for u in u_h2], [rf * 1000 for rf in rf_h2], "r-", label=r"H2 Refinement ($h=0.0075\,\mathrm{mm}, N=33\,852$)", linewidth=1.8)
    
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Reaction Force $RF_x$ [$\mathrm{N}$]", fontsize=12)
    ax.set_title("Mode-II Phase-Field Uniform Mesh Convergence (FRACFIX)", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    
    fig_png = FIG_DIR / "mode_ii_h0_h1_h2_rf1_u1_comparison.png"
    fig_pdf = FIG_DIR / "mode_ii_h0_h1_h2_rf1_u1_comparison.pdf"
    fig.savefig(fig_png)
    fig.savefig(fig_pdf)
    plt.close(fig)
    print(f"Saved {fig_png} and {fig_pdf}")

    # 2. Maximum Phase Field Evolution Comparison
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.plot([u * 1000 for u in u_h0], d_h0, "k--", label=r"H0 Baseline ($h/l_0=2.0$)", linewidth=1.5)
    ax.plot([u * 1000 for u in u_h1], d_h1, "b-", label=r"H1 Refinement ($h/l_0=1.0$)", linewidth=1.8)
    ax.plot([u * 1000 for u in u_h2], d_h2, "r-", label=r"H2 Refinement ($h/l_0=0.5$)", linewidth=1.8)
    
    ax.axhline(0.5, color="gray", linestyle=":", label=r"Initiation Threshold ($d=0.5$)")
    ax.axhline(0.9, color="gray", linestyle="-.", label=r"Broken Threshold ($d=0.9$)")
    
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Maximum Phase Field $d_{\max}$ [-]", fontsize=12)
    ax.set_title("Mode-II Phase Field Damage Evolution Across Mesh Levels", fontsize=13, fontweight="bold")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    
    d_fig_png = FIG_DIR / "mode_ii_h0_h1_h2_damage_evolution_comparison.png"
    d_fig_pdf = FIG_DIR / "mode_ii_h0_h1_h2_damage_evolution_comparison.pdf"
    fig.savefig(d_fig_png)
    fig.savefig(d_fig_pdf)
    plt.close(fig)
    print(f"Saved {d_fig_png} and {d_fig_pdf}")

    # 3. Initial Linear Elastic Stiffness Comparison
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    u_elastic_max = 2.0  # um
    
    u_h0_el = [u*1000 for u, rf in zip(u_h0, rf_h0) if 0.2 <= u*1000 <= u_elastic_max]
    rf_h0_el = [rf*1000 for u, rf in zip(u_h0, rf_h0) if 0.2 <= u*1000 <= u_elastic_max]
    
    u_h1_el = [u*1000 for u, rf in zip(u_h1, rf_h1) if 0.2 <= u*1000 <= u_elastic_max]
    rf_h1_el = [rf*1000 for u, rf in zip(u_h1, rf_h1) if 0.2 <= u*1000 <= u_elastic_max]
    
    u_h2_el = [u*1000 for u, rf in zip(u_h2, rf_h2) if 0.2 <= u*1000 <= u_elastic_max]
    rf_h2_el = [rf*1000 for u, rf in zip(u_h2, rf_h2) if 0.2 <= u*1000 <= u_elastic_max]
    
    ax.scatter(u_h0_el, rf_h0_el, color="black", s=30, label=r"H0 ($K_0 = 46.119\,\mathrm{kN/mm}$)")
    ax.scatter(u_h1_el, rf_h1_el, color="blue", marker="s", s=30, label=r"H1 ($K_0 = 45.822\,\mathrm{kN/mm}$)")
    ax.scatter(u_h2_el, rf_h2_el, color="red", marker="^", s=30, label=r"H2 ($K_0 = 45.793\,\mathrm{kN/mm}$)")
    
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Reaction Force $RF_x$ [$\mathrm{N}$]", fontsize=12)
    ax.set_title("Mode-II Initial Elastic Shear Stiffness Parity ($u_x \le 2\,\mu\mathrm{m}$)", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    
    stiff_png = FIG_DIR / "mode_ii_h0_h1_h2_initial_stiffness_fit.png"
    stiff_pdf = FIG_DIR / "mode_ii_h0_h1_h2_initial_stiffness_fit.pdf"
    fig.savefig(stiff_png)
    fig.savefig(stiff_pdf)
    plt.close(fig)
    print(f"Saved {stiff_png} and {stiff_pdf}")

    summary = {
        "H0": {
            "job_id": "1379393.mmaster02 / 1386372.mmaster02",
            "n_physical_elements": 3930,
            "h_min_mm": 0.030,
            "h_over_l0": 2.0,
            "initial_stiffness_kN_mm": 46.1185,
            "final_u1_mm": 0.0100,
            "peak_rf1_kN": 0.373271,
            "d_max": 0.990884,
            "status": "PASS"
        },
        "H1": {
            "job_id": "1386447.mmaster02",
            "n_physical_elements": 12064,
            "h_min_mm": 0.015,
            "h_over_l0": 1.0,
            "initial_stiffness_kN_mm": 45.8224,
            "final_u1_mm": 0.009632,
            "peak_rf1_kN": 0.361657,
            "d_max": 0.997519,
            "u1_at_first_d05_mm": 0.007750,
            "u1_at_first_d09_mm": 0.008500,
            "status": "SOLVER_TERMINATION_STEP2_INC1854_FIXED_INCREMENT_DIVERGENCE"
        },
        "H2": {
            "job_id": "1386448.mmaster02",
            "n_physical_elements": 33852,
            "h_min_mm": 0.0075,
            "h_over_l0": 0.5,
            "initial_stiffness_kN_mm": 45.7929,
            "final_u1_mm": 0.009250,
            "peak_rf1_kN": 0.354084,
            "d_max": 0.998472,
            "u1_at_first_d05_mm": 0.007750,
            "u1_at_first_d09_mm": 0.008000,
            "status": "PBS_WALLTIME_LIMIT_EXCEEDED_04_00_00_AT_STEP2_INC1743"
        },
        "stiffness_variation_pct": {
            "H0_to_H1": -0.642,
            "H1_to_H2": -0.064,
            "H0_to_H2": -0.706
        },
        "reaction_force_variation_pct": {
            "H0_to_H1": -3.111,
            "H1_to_H2": -2.094,
            "H0_to_H2": -5.140
        }
    }
    
    summary_json = ROOT / "models/generated/mode_ii/reference_convergence/PAIR2_CONVERGENCE_SUMMARY.json"
    with open(summary_json, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"Saved convergence summary to {summary_json}")

if __name__ == "__main__":
    create_evidence_inventory(H1_DIR, "1386447.mmaster02", "M2REF_H1_FRACFIX")
    create_evidence_inventory(H2_DIR, "1386448.mmaster02", "M2REF_H2_FRACFIX")
    plot_comparison()
