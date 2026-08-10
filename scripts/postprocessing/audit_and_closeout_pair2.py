#!/usr/bin/env python3
"""Comprehensive Technical, Scientific, Convergence, and Governance Audit for Mode-II Pair-2.

Audits:
- H1: Job 1386447.mmaster02 (M2REF_H1_FRACFIX)
- H2: Job 1386448.mmaster02 (M2REF_H2_FRACFIX)
- Reference Baseline: H0 (Job 1379393.mmaster02 / 1386372.mmaster02)
"""

import csv
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]

FROZEN_HASHES = {
    "H1": {
        "input": ("models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.inp",
                  "407f88694d35d86bdc321d090c0678f6c9a348a462249690b4ac2c06d708f10c"),
        "UEL": ("models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/f42_mixed_uel.for",
                "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"),
        "PBS": ("models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/M2REF_H1_FRACFIX.pbs",
                "42a640cd4afa6e44a15c174e1fc17a888635e474ae10afefd7a21515ee904039"),
        "wrapper": ("models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/submit_m2ref_h1_fracfix.sh",
                    "2d354ec6e00e09657b867d36fcadde69269f09c78b6e10dea537679d3d5c57a3"),
        "manifest": ("models/generated/mode_ii/reference_convergence/M2REF_H1_FRACFIX/PACKAGE_MANIFEST.json",
                     "94d79421a48c66e95c1c8c11e74f07a72d7331804b407ec937aedcf9bb5dcba3"),
    },
    "H2": {
        "input": ("models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.inp",
                  "c9a3f496cf2cb0daa455cfae31f5bd699b56f3b410f0a7f2a12014b2718be5b0"),
        "UEL": ("models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/f42_mixed_uel.for",
                "0bc4378179a35acd9954d20d3e07517f8e1c356ae07a23c40e7715cd7b56dce8"),
        "PBS": ("models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/M2REF_H2_FRACFIX.pbs",
                "ba16a0b64d85f069c03878a6e20f913cd6daf2f65f91e8f64c1c2046a762d32a"),
        "wrapper": ("models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/submit_m2ref_h2_fracfix.sh",
                    "dd3f85dcc62fe855f965a1a58478228d032a394b9f61573a240bd8fc8ca66053"),
        "manifest": ("models/generated/mode_ii/reference_convergence/M2REF_H2_FRACFIX/PACKAGE_MANIFEST.json",
                     "d5769188aa1ff72cb25fd1a92e1fe1a457497d519b7dcaee7df78bb1e2aa05a9"),
    }
}

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

def trapz_calc(y, x):
    y = np.asarray(y)
    x = np.asarray(x)
    return float(np.sum((y[:-1] + y[1:]) * 0.5 * np.diff(x)))

def verify_hashes():
    results = {}
    all_match = True
    print("=== RAW BYTE SHA256 VERIFICATION AGAINST P13/Q13 ===")
    for job_key, files in FROZEN_HASHES.items():
        results[job_key] = {}
        for item, (rel_path, expected_hash) in files.items():
            full_path = ROOT / rel_path
            if full_path.exists():
                actual_hash = compute_sha256(full_path)
                match = (actual_hash == expected_hash)
            else:
                actual_hash = "FILE_NOT_FOUND"
                match = False
            if not match:
                all_match = False
            print(f"[{job_key}] {item} ({rel_path}): {'MATCH' if match else 'MISMATCH'}")
            if not match:
                print(f"   Expected: {expected_hash}")
                print(f"   Actual:   {actual_hash}")
            results[job_key][item] = {
                "path": rel_path,
                "expected_hash": expected_hash,
                "actual_hash": actual_hash,
                "match": match
            }
    return results, all_match

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
    return np.array(u_list), np.array(rf_list), np.array(d_list)

def compute_initial_stiffness(u_arr, rf_arr, u_min=0.0002, u_max=0.0020):
    mask = (u_arr >= u_min) & (u_arr <= u_max)
    u_sel = u_arr[mask]
    rf_sel = rf_arr[mask]
    if len(u_sel) < 2:
        return None, None
    poly = np.polyfit(u_sel, rf_sel, 1)
    k = float(poly[0])
    c = float(poly[1])
    res = rf_sel - (k * u_sel + c)
    ss_res = np.sum(res**2)
    ss_tot = np.sum((rf_sel - np.mean(rf_sel))**2)
    r2 = float(1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0
    return k, r2

def find_displacement_at_threshold(u_arr, d_arr, threshold):
    for u, d in zip(u_arr, d_arr):
        if d >= threshold:
            return float(u)
    return None

def compute_hausdorff_distance(pts1, pts2):
    if len(pts1) == 0 or len(pts2) == 0:
        return None
    d1 = np.max([np.min(np.linalg.norm(pts2 - p1, axis=1)) for p1 in pts1])
    d2 = np.max([np.min(np.linalg.norm(pts1 - p2, axis=1)) for p2 in pts2])
    return float(max(d1, d2))

def load_crack_points(csv_path: Path):
    pts = []
    if not csv_path.exists():
        return np.empty((0, 2))
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            for xk, yk in [("x", "y"), ("X", "Y"), ("coord_x", "coord_y"), ("COORD1", "COORD2")]:
                if xk in r and yk in r and r[xk] != "" and r[yk] != "":
                    try:
                        pts.append([float(r[xk]), float(r[yk])])
                    except ValueError:
                        pass
                    break
    return np.array(pts) if pts else np.empty((0, 2))

def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Byte verification
    hash_results, all_hashes_match = verify_hashes()
    
    # 2. Evidence inventories
    h1_inv = create_evidence_inventory(H1_DIR, "1386447.mmaster02", "M2REF_H1_FRACFIX")
    h2_inv = create_evidence_inventory(H2_DIR, "1386448.mmaster02", "M2REF_H2_FRACFIX")
    
    # 3. Load curves
    u_h0, rf_h0, d_h0 = load_curve(H0_CSV)
    u_h1, rf_h1, d_h1 = load_curve(H1_DIR / "rf1_u1_curve.csv")
    u_h2, rf_h2, d_h2 = load_curve(H2_DIR / "rf1_u1_curve.csv")
    
    # Initial stiffness
    k_h0, r2_h0 = compute_initial_stiffness(u_h0, rf_h0)
    k_h1, r2_h1 = compute_initial_stiffness(u_h1, rf_h1)
    k_h2, r2_h2 = compute_initial_stiffness(u_h2, rf_h2)
    
    # Peak forces and final states
    pk_rf_h0, u_pk_h0 = float(np.max(rf_h0)), float(u_h0[np.argmax(rf_h0)])
    pk_rf_h1, u_pk_h1 = float(np.max(rf_h1)), float(u_h1[np.argmax(rf_h1)])
    pk_rf_h2, u_pk_h2 = float(np.max(rf_h2)), float(u_h2[np.argmax(rf_h2)])
    
    fn_rf_h0, fn_u_h0 = float(rf_h0[-1]), float(u_h0[-1])
    fn_rf_h1, fn_u_h1 = float(rf_h1[-1]), float(u_h1[-1])
    fn_rf_h2, fn_u_h2 = float(rf_h2[-1]), float(u_h2[-1])
    
    dmax_h0 = float(np.max(d_h0))
    dmax_h1 = float(np.max(d_h1))
    dmax_h2 = float(np.max(d_h2))
    
    # Common displacement domain for interpolation
    u_common_max = min(float(np.max(u_h0)), float(np.max(u_h1)), float(np.max(u_h2)))
    u_common = np.linspace(0.0, u_common_max, 1000)
    
    rf_h0_interp = np.interp(u_common, u_h0, rf_h0)
    rf_h1_interp = np.interp(u_common, u_h1, rf_h1)
    rf_h2_interp = np.interp(u_common, u_h2, rf_h2)
    
    d_h0_interp = np.interp(u_common, u_h0, d_h0)
    d_h1_interp = np.interp(u_common, u_h1, d_h1)
    d_h2_interp = np.interp(u_common, u_h2, d_h2)
    
    # Curve areas on common domain
    area_h0 = trapz_calc(rf_h0_interp, u_common)
    area_h1 = trapz_calc(rf_h1_interp, u_common)
    area_h2 = trapz_calc(rf_h2_interp, u_common)
    
    # Full-curve normalized L2 errors
    norm_l2_h0 = float(np.sqrt(np.mean(rf_h0_interp**2)))
    norm_l2_h1 = float(np.sqrt(np.mean(rf_h1_interp**2)))
    
    l2_err_h1_vs_h0 = float(np.sqrt(np.mean((rf_h1_interp - rf_h0_interp)**2)) / norm_l2_h0)
    l2_err_h2_vs_h1 = float(np.sqrt(np.mean((rf_h2_interp - rf_h1_interp)**2)) / norm_l2_h1)
    l2_err_h2_vs_h0 = float(np.sqrt(np.mean((rf_h2_interp - rf_h0_interp)**2)) / norm_l2_h0)
    
    # Peak RF relative errors
    peak_err_h1_vs_h0 = float(abs(pk_rf_h1 - pk_rf_h0) / pk_rf_h0)
    peak_err_h2_vs_h1 = float(abs(pk_rf_h2 - pk_rf_h1) / pk_rf_h1)
    peak_err_h2_vs_h0 = float(abs(pk_rf_h2 - pk_rf_h0) / pk_rf_h0)
    
    # Curve area relative errors
    area_err_h1_vs_h0 = float(abs(area_h1 - area_h0) / area_h0)
    area_err_h2_vs_h1 = float(abs(area_h2 - area_h1) / area_h1)
    area_err_h2_vs_h0 = float(abs(area_h2 - area_h0) / area_h0)
    
    # Damage threshold displacements
    thresh_list = [1e-6, 1e-4, 0.01, 0.1, 0.5, 0.9]
    damage_init_h0 = {str(t): find_displacement_at_threshold(u_h0, d_h0, t) for t in thresh_list}
    damage_init_h1 = {str(t): find_displacement_at_threshold(u_h1, d_h1, t) for t in thresh_list}
    damage_init_h2 = {str(t): find_displacement_at_threshold(u_h2, d_h2, t) for t in thresh_list}
    
    # Crack path Hausdorff distance
    pts_h1 = load_crack_points(H1_DIR / "crack_path_sdv15_ge_0p5.csv")
    pts_h2 = load_crack_points(H2_DIR / "crack_path_sdv15_ge_0p5.csv")
    hausdorff_h2_vs_h1 = compute_hausdorff_distance(pts_h1, pts_h2) if (len(pts_h1) > 0 and len(pts_h2) > 0) else None
    
    # Gates:
    # 1. Peak RF gate: <= 1% (0.010)
    # 2. Curve L2 gate: <= 2% (0.020)
    # 3. Energy gate: <= 1% (0.010) [N/A / unresolvable directly from standard curve]
    # 4. Crack gate: Hausdorff <= 0.00375 mm
    
    h1_peak_gate = "PASS" if peak_err_h1_vs_h0 <= 0.010 else "FAIL"
    h1_curve_gate = "PASS" if l2_err_h1_vs_h0 <= 0.020 else "FAIL"
    h1_energy_gate = "UNRESOLVED_UNAVAILABLE"
    h1_crack_gate = "UNRESOLVED_UNAVAILABLE"
    
    h2_peak_gate = "FAIL" if peak_err_h2_vs_h1 > 0.010 else "PASS"
    h2_curve_gate = "PASS" if l2_err_h2_vs_h1 <= 0.020 else "FAIL"
    h2_energy_gate = "UNRESOLVED_UNAVAILABLE"
    h2_crack_gate = ("PASS" if (hausdorff_h2_vs_h1 is not None and hausdorff_h2_vs_h1 <= 0.00375) else 
                     ("FAIL" if hausdorff_h2_vs_h1 is not None else "UNRESOLVED_UNAVAILABLE"))
    
    rec_res = "H1_required" if l2_err_h1_vs_h0 > 0.020 or peak_err_h1_vs_h0 > 0.010 else "H0_sufficient"
    
    # 4. Plots
    # Force-displacement comparison
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.plot(u_h0 * 1000, rf_h0 * 1000, "k--", label=r"H0 Baseline ($h=0.030\,\mathrm{mm}, N=3\,930$)", linewidth=1.5)
    ax.plot(u_h1 * 1000, rf_h1 * 1000, "b-", label=r"H1 Refinement ($h=0.015\,\mathrm{mm}, N=12\,064$)", linewidth=1.8)
    ax.plot(u_h2 * 1000, rf_h2 * 1000, "r-", label=r"H2 Refinement ($h=0.0075\,\mathrm{mm}, N=33\,852$)", linewidth=1.8)
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Reaction Force $RF_x$ [$\mathrm{N}$]", fontsize=12)
    ax.set_title("Mode-II Phase-Field Uniform Mesh Convergence (FRACFIX)", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_rf1_u1_comparison.png")
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_rf1_u1_comparison.pdf")
    plt.close(fig)
    print("Saved force-displacement comparison figures.")
    
    # Damage comparison
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    ax.plot(u_h0 * 1000, d_h0, "k--", label=r"H0 Baseline ($h/l_0=2.0$)", linewidth=1.5)
    ax.plot(u_h1 * 1000, d_h1, "b-", label=r"H1 Refinement ($h/l_0=1.0$)", linewidth=1.8)
    ax.plot(u_h2 * 1000, d_h2, "r-", label=r"H2 Refinement ($h/l_0=0.5$)", linewidth=1.8)
    ax.axhline(0.5, color="gray", linestyle=":", label=r"Initiation Threshold ($d=0.5$)")
    ax.axhline(0.9, color="gray", linestyle="-.", label=r"Broken Threshold ($d=0.9$)")
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Maximum Phase Field $d_{\max}$ [-]", fontsize=12)
    ax.set_title("Mode-II Phase Field Damage Evolution Across Mesh Levels", fontsize=13, fontweight="bold")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_damage_evolution_comparison.png")
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_damage_evolution_comparison.pdf")
    plt.close(fig)
    print("Saved damage evolution comparison figures.")
    
    # Initial stiffness fit
    fig, ax = plt.subplots(figsize=(8, 6), dpi=300)
    mask_el_h0 = (u_h0 * 1000 >= 0.2) & (u_h0 * 1000 <= 2.0)
    mask_el_h1 = (u_h1 * 1000 >= 0.2) & (u_h1 * 1000 <= 2.0)
    mask_el_h2 = (u_h2 * 1000 >= 0.2) & (u_h2 * 1000 <= 2.0)
    ax.scatter(u_h0[mask_el_h0] * 1000, rf_h0[mask_el_h0] * 1000, color="black", s=30, label=f"H0 ($K_0 = {k_h0:.3f}\,\mathrm{{kN/mm}}$)")
    ax.scatter(u_h1[mask_el_h1] * 1000, rf_h1[mask_el_h1] * 1000, color="blue", marker="s", s=30, label=f"H1 ($K_0 = {k_h1:.3f}\,\mathrm{{kN/mm}}$)")
    ax.scatter(u_h2[mask_el_h2] * 1000, rf_h2[mask_el_h2] * 1000, color="red", marker="^", s=30, label=f"H2 ($K_0 = {k_h2:.3f}\,\mathrm{{kN/mm}}$)")
    ax.set_xlabel(r"Shear Displacement $u_x$ [$\mu\mathrm{m}$]", fontsize=12)
    ax.set_ylabel(r"Reaction Force $RF_x$ [$\mathrm{N}$]", fontsize=12)
    ax.set_title(r"Mode-II Initial Elastic Shear Stiffness Parity ($u_x \leq 2\,\mu\mathrm{m}$)", fontsize=13, fontweight="bold")
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(loc="upper left", fontsize=10, frameon=True)
    plt.tight_layout()
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_initial_stiffness_fit.png")
    fig.savefig(FIG_DIR / "mode_ii_h0_h1_h2_initial_stiffness_fit.pdf")
    plt.close(fig)
    print("Saved initial stiffness fit figures.")

    # 5. Build full audit record
    audit_data = {
        "task_id": "F43MODEREF13-PAIR2-CLOSEOUT1",
        "closeout_timestamp_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "H1": {
            "job_id": "1386447.mmaster02",
            "job_name": "M2REF_H1_FRACFIX",
            "scheduler_result": "FINISHED_EXIT_STATUS_1",
            "technical_result": "SOLVER_DIVERGENCE_AT_STEP2_INC1854",
            "postprocessing_result": "PASS",
            "scientific_result": "EXTRACTED_VALID_TO_U000963_MM",
            "walltime": "01:30:53",
            "cpu_time": "01:30:34",
            "peak_memory_kb": 955776,
            "peak_vmem_kb": 3337020,
            "initial_stiffness_kN_mm": k_h1,
            "r2_stiffness": r2_h1,
            "peak_rf1_kN": pk_rf_h1,
            "u1_at_peak_rf1_mm": u_pk_h1,
            "final_rf1_kN": fn_rf_h1,
            "final_u1_mm": fn_u_h1,
            "dmax": dmax_h1,
            "damage_initiation_u1_mm": damage_init_h1,
            "total_increments": 2354,
            "step2_increments": 1854,
            "n_physical_elements": 12064,
            "n_layered_elements": 24128,
            "execution_hash_match": all(v["match"] for v in hash_results["H1"].values())
        },
        "H2": {
            "job_id": "1386448.mmaster02",
            "job_name": "M2REF_H2_FRACFIX",
            "scheduler_result": "FINISHED_EXIT_STATUS_NEG29_WALLTIME_LIMIT",
            "technical_result": "PBS_WALLTIME_EXCEEDED_04_00_00_AT_STEP2_INC1743",
            "postprocessing_result": "PASS",
            "scientific_result": "EXTRACTED_VALID_TO_U000925_MM",
            "walltime": "04:01:41",
            "cpu_time": "04:00:55",
            "peak_memory_kb": 1782988,
            "peak_vmem_kb": 7551044,
            "initial_stiffness_kN_mm": k_h2,
            "r2_stiffness": r2_h2,
            "peak_rf1_kN": pk_rf_h2,
            "u1_at_peak_rf1_mm": u_pk_h2,
            "final_rf1_kN": fn_rf_h2,
            "final_u1_mm": fn_u_h2,
            "dmax": dmax_h2,
            "damage_initiation_u1_mm": damage_init_h2,
            "total_increments": 2243,
            "step2_increments": 1743,
            "n_physical_elements": 33852,
            "n_layered_elements": 67704,
            "execution_hash_match": all(v["match"] for v in hash_results["H2"].values())
        },
        "H0": {
            "job_id": "1379393.mmaster02 / 1386372.mmaster02",
            "initial_stiffness_kN_mm": k_h0,
            "peak_rf1_kN": pk_rf_h0,
            "u1_at_peak_rf1_mm": u_pk_h0,
            "final_rf1_kN": fn_rf_h0,
            "final_u1_mm": fn_u_h0,
            "dmax": dmax_h0,
            "damage_initiation_u1_mm": damage_init_h0,
            "n_physical_elements": 3930,
            "n_layered_elements": 7860
        },
        "convergence_metrics": {
            "u_common_max_mm": u_common_max,
            "peak_RF_relative_difference": {
                "H1_vs_H0": peak_err_h1_vs_h0,
                "H2_vs_H1": peak_err_h2_vs_h1,
                "H2_vs_H0": peak_err_h2_vs_h0
            },
            "full_curve_normalized_L2_error": {
                "H1_vs_H0": l2_err_h1_vs_h0,
                "H2_vs_H1": l2_err_h2_vs_h1,
                "H2_vs_H0": l2_err_h2_vs_h0
            },
            "relative_curve_area_difference": {
                "H1_vs_H0": area_err_h1_vs_h0,
                "H2_vs_H1": area_err_h2_vs_h1,
                "H2_vs_H0": area_err_h2_vs_h0
            },
            "dmax_absolute_difference": {
                "H1_vs_H0": abs(dmax_h1 - dmax_h0),
                "H2_vs_H1": abs(dmax_h2 - dmax_h1),
                "H2_vs_H0": abs(dmax_h2 - dmax_h0)
            },
            "crack_path_hausdorff_distance_mm": {
                "H2_vs_H1": hausdorff_h2_vs_h1
            }
        },
        "gates": {
            "H1_peak_gate": h1_peak_gate,
            "H2_peak_gate": h2_peak_gate,
            "H1_curve_gate": h1_curve_gate,
            "H2_curve_gate": h2_curve_gate,
            "H1_energy_gate": h1_energy_gate,
            "H2_energy_gate": h2_energy_gate,
            "H1_crack_gate": h1_crack_gate,
            "H2_crack_gate": h2_crack_gate
        },
        "computational_cost_ratios": {
            "elements_H1_over_H0": 12064 / 3930,
            "elements_H2_over_H0": 33852 / 3930,
            "elements_H2_over_H1": 33852 / 12064,
            "cpu_time_H1_over_H0": 5434 / 920,
            "cpu_time_H2_over_H0": 14455 / 920,
            "cpu_time_H2_over_H1": 14455 / 5434,
            "memory_H1_over_H0": 955776 / 380000,
            "memory_H2_over_H0": 1782988 / 380000,
            "memory_H2_over_H1": 1782988 / 955776
        },
        "governance": {
            "direct_human_authorization_message_found": False,
            "repository_cleanup_deviation_recorded": True,
            "governance_result": "HOLD_protocol_deviating_no_direct_human_chat_authorization_and_repository_cleanup_during_submission_workflow",
            "execution_hash_contract_match_H1": all(v["match"] for v in hash_results["H1"].values()),
            "execution_hash_contract_match_H2": all(v["match"] for v in hash_results["H2"].values()),
            "running_jobs_final": 0,
            "queued_jobs_final": 0,
            "execution_authorized": False,
            "submission_approved": False,
            "maximum_jobs_now": 0,
            "remaining_authorized_submissions": 0,
            "qsub_called_in_closeout": False,
            "qdel_called": False,
            "qmove_called": False,
            "automatic_retry_called": False
        },
        "recommended_reference_resolution": rec_res,
        "scientific_convergence_result": "HOLD_H1_REQUIRED_FOR_ELASTIC_POST_PEAK_REQUIRES_ADAPTIVE_STEPPING_OR_REMESHING"
    }
    
    out_json = ROOT / "models/generated/mode_ii/reference_convergence/PAIR2_CLOSEOUT_AUDIT.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Saved complete closeout audit to {out_json}")
    return audit_data

if __name__ == "__main__":
    main()
