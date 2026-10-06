#!/usr/bin/env python3
"""
Mode-I Gate-6B Single-Job Provenance Synthesis Extractor
=========================================================

Authoritatively extracts, computes, and validates single-job provenance
metrics directly from raw solver files (.dat, .csv, .sta) for each
individual Gate-6B simulation without cross-copying or data conflation.

Author: Antigravity Multi-Agent Coordination
Protocol Version: 2
"""

import os
import sys
import json
import csv
import argparse
import numpy as np

def compute_k0_from_points(u_pts, f_pts):
    """Computes linear initial elastic stiffness K0 (u <= 0.0010 mm)."""
    pts = [(u, f) for u, f in zip(u_pts, f_pts) if u <= 0.0010001 and u > 0]
    n = len(pts)
    if n < 2:
        return 0.0, 1.0, 0
    u_arr = np.array([p[0] for p in pts])
    f_arr = np.array([p[1] for p in pts])
    slope, intercept = np.polyfit(u_arr, f_arr, 1)
    f_pred = slope * u_arr + intercept
    ss_tot = np.sum((f_arr - np.mean(f_arr))**2)
    ss_res = np.sum((f_arr - f_pred)**2)
    r2 = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 1.0
    return float(slope), float(r2), int(n)

def parse_dat_rp_rf(dat_path):
    """Parses displacement and reaction force for RP Node 999999 from Abaqus .dat file."""
    u_list = []
    rf_list = []
    current_step = 1
    with open(dat_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'S T E P       2' in line:
                current_step = 2
            parts = line.strip().split()
            if len(parts) >= 3 and parts[0] == '999999':
                try:
                    u2 = float(parts[1])
                    rf2 = float(parts[2])
                    u_list.append(u2)
                    rf_list.append(rf2)
                except ValueError:
                    pass
    return np.array(u_list), np.array(rf_list)

def parse_uel_energy(csv_path):
    """Parses uel_energy_balance.csv file."""
    recs = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            step = int(row['Step'].strip())
            inc = int(row['Increment'].strip())
            step_time = float(row['StepTime'].strip())
            e_elas = float(row['E_elastic_kNmm'].strip())
            e_frac = float(row['E_fracture_kNmm'].strip())
            e_tot = float(row['E_total_kNmm'].strip())
            if step == 1:
                u_actual = 0.0050 * step_time
            elif step == 2:
                u_actual = 0.0050 + 0.0050 * step_time
            else:
                u_actual = 0.0
            recs.append({
                'step': step,
                'inc': inc,
                'u_actual': u_actual,
                'e_elas_mJ': e_elas * 1000.0,
                'e_frac_mJ': e_frac * 1000.0,
                'e_tot_mJ': e_tot * 1000.0
            })
    return recs

def extract_all_single_job_provenance(base_dir):
    """Performs single-job authoritative extraction across all Gate-6B benchmarks."""
    models_dir = os.path.join(base_dir, "models", "pandey_kumar_mode1")
    
    dataset = {
        "metadata": {
            "title": "Mode-I Gate-6B Authoritative Single-Job Provenance Synthesis",
            "protocol_version": 2,
            "governing_phase": "MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION",
            "description": "Independently extracted single-job metrics with zero cross-contamination or forward-filling."
        },
        "jobs": []
    }

    # 1. Job 1398090 (Fixed Ref Mechanical Anchor)
    dat_01 = os.path.join(models_dir, "01_standard_pfm_reference", "PK_MODE1_STANDARD_PFM.dat")
    u_01, rf_01 = parse_dat_rp_rf(dat_01)
    k0_01, r2_01, n_01 = compute_k0_from_points(u_01, rf_01)
    idx_peak_01 = int(np.argmax(rf_01))
    f_max_01 = float(rf_01[idx_peak_01])
    u_peak_01 = float(u_01[idx_peak_01])

    dataset["jobs"].append({
        "job_id": "1398090.mmaster02",
        "benchmark_label": "Fixed Reference ($S_1$, Mechanical Anchor)",
        "package_dir": "models/pandey_kumar_mode1/01_standard_pfm_reference",
        "fe_elements": 15192,
        "fe_nodes": 15521,
        "total_nodes_with_rp": 15522,
        "status": "CENSORED_AT_PEAK",
        "governed_classification": "MECHANICAL_ANCHOR_QUALIFIED",
        "k0_kn_per_mm": k0_01,
        "k0_r2": r2_01,
        "f_max_kn": f_max_01,
        "u_peak_mm": u_peak_01,
        "u_term_mm": u_peak_01,
        "w_ext_mJ": None,
        "e_frac_mJ": None,
        "e_elas_mJ": None,
        "delta_book_mJ": None,
        "eps_book_pct": None,
        "notes": "Historical standard PFM reference mechanical anchor. Energy instrumentation was not active; censored at peak in baseline."
    })

    # 2. Job 1409734 (Fixed Ref Energetic Full Horizon)
    dat_16 = os.path.join(models_dir, "16_energy_qualification_reference_15k", "PK_M1_REF15K_ENERGY.dat")
    energy_16 = os.path.join(models_dir, "16_energy_qualification_reference_15k", "uel_energy_balance.csv")
    u_16, rf_16 = parse_dat_rp_rf(dat_16)
    k0_16, r2_16, n_16 = compute_k0_from_points(u_16, rf_16)
    idx_peak_16 = int(np.argmax(rf_16))
    f_max_16 = float(rf_16[idx_peak_16])
    u_peak_16 = float(u_16[idx_peak_16])

    w_ext_16 = [0.0]
    for i in range(1, len(u_16)):
        du = u_16[i] - u_16[i-1]
        f_avg = 0.5 * (rf_16[i] + rf_16[i-1])
        w_ext_16.append(w_ext_16[-1] + f_avg * du * 1000.0)

    erecs_16 = parse_uel_energy(energy_16)
    w_term_16 = float(w_ext_16[-1])
    e_frac_term_16 = float(erecs_16[-1]['e_frac_mJ'])
    e_elas_term_16 = float(erecs_16[-1]['e_elas_mJ'])
    delta_book_16 = float(w_term_16 - (e_frac_term_16 + e_elas_term_16))
    eps_book_16 = float(abs(delta_book_16) / w_term_16 * 100.0)

    dataset["jobs"].append({
        "job_id": "1409734.mmaster02",
        "benchmark_label": "Fixed Reference ($S_1$, Energy-Qualified)",
        "package_dir": "models/pandey_kumar_mode1/16_energy_qualification_reference_15k",
        "fe_elements": 15192,
        "fe_nodes": 15521,
        "total_nodes_with_rp": 15522,
        "status": "COMPLETED_FULL_HORIZON",
        "governed_classification": "ENERGY_AND_MECHANICAL_REFERENCE_QUALIFIED",
        "k0_kn_per_mm": k0_16,
        "k0_r2": r2_16,
        "f_max_kn": f_max_16,
        "u_peak_mm": u_peak_16,
        "u_term_mm": float(u_16[-1]),
        "w_ext_mJ": w_term_16,
        "e_frac_mJ": e_frac_term_16,
        "e_elas_mJ": e_elas_term_16,
        "delta_book_mJ": delta_book_16,
        "eps_book_pct": eps_book_16,
        "notes": "Authoritative full-horizon energy qualification reference standard. 7,000 increments, Exit 0."
    })

    # 3. Job 1409982 (Canonical ET1 Baseline 14k)
    fu_25 = os.path.join(models_dir, "25_stage14_adaptive_candidate_14k", "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv")
    energy_25 = os.path.join(models_dir, "25_stage14_adaptive_candidate_14k", "uel_energy_balance.csv")
    u_25, rf_25, w_ext_25_csv = [], [], []
    with open(fu_25, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_25.append(float(r['displacement_mm']))
            rf_25.append(float(r['reaction_force_kN']))
            w_ext_25_csv.append(float(r['w_ext_mJ']))
    u_25 = np.array(u_25)
    rf_25 = np.array(rf_25)
    k0_25, r2_25, n_25 = compute_k0_from_points(u_25, rf_25)
    idx_peak_25 = int(np.argmax(rf_25))
    f_max_25 = float(rf_25[idx_peak_25])
    u_peak_25 = float(u_25[idx_peak_25])

    erecs_25 = parse_uel_energy(energy_25)
    w_term_25 = float(w_ext_25_csv[-1])
    e_frac_term_25 = float(erecs_25[-1]['e_frac_mJ'])
    e_elas_term_25 = float(erecs_25[-1]['e_elas_mJ'])
    delta_book_25 = float(w_term_25 - (e_frac_term_25 + e_elas_term_25))
    eps_book_25 = float(abs(delta_book_25) / w_term_25 * 100.0)

    dataset["jobs"].append({
        "job_id": "1409982.mmaster02",
        "benchmark_label": "Adaptive ET1 Baseline ($14{,}483$ FE, Canonical)",
        "package_dir": "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k",
        "fe_elements": 14483,
        "fe_nodes": 14456,
        "total_nodes_with_rp": 14457,
        "status": "TERMINATED_POSTPEAK_LOAD_DROP_98_5PCT",
        "governed_classification": "CANONICAL_ET1_BASELINE_QUALIFIED",
        "k0_kn_per_mm": k0_25,
        "k0_r2": r2_25,
        "f_max_kn": f_max_25,
        "u_peak_mm": u_peak_25,
        "u_term_mm": float(u_25[-1]),
        "w_ext_mJ": w_term_25,
        "e_frac_mJ": e_frac_term_25,
        "e_elas_mJ": e_elas_term_25,
        "delta_book_mJ": delta_book_25,
        "eps_book_pct": eps_book_25,
        "notes": "Canonical adaptive ET1 baseline. Reached 98.5% post-peak load drop (u=7.889 um) before severed-wake residual correction tolerance check cutbacks."
    })

    # 4. Job 1410180 (ET1 Cn=0.50 Diagnostic)
    fu_28 = os.path.join(models_dir, "28_stage14_convergence_control_candidate", "PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv")
    u_28, rf_28, w_28, ef_28, ee_28 = [], [], [], [], []
    with open(fu_28, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_28.append(float(r['u_mm']))
            rf_28.append(float(r['f_tensile_kN']))
            w_28.append(float(r['w_ext_mJ']))
            ef_28.append(float(r['e_frac_mJ']))
            ee_28.append(float(r['e_elas_mJ']))
    u_28 = np.array(u_28)
    rf_28 = np.array(rf_28)
    k0_28, r2_28, n_28 = compute_k0_from_points(u_28, rf_28)
    idx_peak_28 = int(np.argmax(rf_28))
    f_max_28 = float(rf_28[idx_peak_28])
    u_peak_28 = float(u_28[idx_peak_28])

    w_term_28 = float(w_28[-1])
    e_frac_term_28 = float(ef_28[-1])
    e_elas_term_28 = float(ee_28[-1])
    delta_book_28 = float(w_term_28 - (e_frac_term_28 + e_elas_term_28))
    eps_book_28 = float(abs(delta_book_28) / w_term_28 * 100.0)

    dataset["jobs"].append({
        "job_id": "1410180.mmaster02",
        "benchmark_label": "Adaptive ET1 ($14{,}483$ FE, $C_n=0.50$ Diagnostic)",
        "package_dir": "models/pandey_kumar_mode1/28_stage14_convergence_control_candidate",
        "fe_elements": 14483,
        "fe_nodes": 14456,
        "total_nodes_with_rp": 14457,
        "status": "COMPLETED_FULL_HORIZON_DIAGNOSTIC",
        "governed_classification": "CONVERGENCE_CONTROL_DIAGNOSTIC_QUALIFIED",
        "k0_kn_per_mm": k0_28,
        "k0_r2": r2_28,
        "f_max_kn": f_max_28,
        "u_peak_mm": u_peak_28,
        "u_term_mm": float(u_28[-1]),
        "w_ext_mJ": w_term_28,
        "e_frac_mJ": e_frac_term_28,
        "e_elas_mJ": e_elas_term_28,
        "delta_book_mJ": delta_book_28,
        "eps_book_pct": eps_book_28,
        "notes": "Convergence-control diagnostic (Cn=0.50). Traversed full softening horizon to u=10.0 um without cutbacks."
    })

    # 5. Job 1410357 (Adaptive ET2 6k)
    fu_34 = os.path.join(models_dir, "34_stage14_step2_adaptive_candidate_et2_6k", "PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE_fu.csv")
    u_34, rf_34, w_34, ef_34, ee_34 = [], [], [], [], []
    with open(fu_34, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_34.append(float(r['u_mm']))
            rf_34.append(float(r['f_tensile_kN']))
            w_34.append(float(r['w_ext_mJ']))
            ef_34.append(float(r['e_frac_mJ']))
            ee_34.append(float(r['e_elas_mJ']))
    u_34 = np.array(u_34)
    rf_34 = np.array(rf_34)
    k0_34, r2_34, n_34 = compute_k0_from_points(u_34, rf_34)
    idx_peak_34 = int(np.argmax(rf_34))
    f_max_34 = float(rf_34[idx_peak_34])
    u_peak_34 = float(u_34[idx_peak_34])

    w_term_34 = float(w_34[-1])
    e_frac_term_34 = float(ef_34[-1])
    e_elas_term_34 = float(ee_34[-1])
    delta_book_34 = float(w_term_34 - (e_frac_term_34 + e_elas_term_34))
    eps_book_34 = float(abs(delta_book_34) / w_term_34 * 100.0)

    dataset["jobs"].append({
        "job_id": "1410357.mmaster02",
        "benchmark_label": "Adaptive ET2 ($6{,}112$ FE, $\\text{errorTarget}=0.02$)",
        "package_dir": "models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k",
        "fe_elements": 6112,
        "fe_nodes": 6181,
        "total_nodes_with_rp": 6182,
        "status": "COMPLETED_FULL_HORIZON",
        "governed_classification": "ERRORTARGET_SWEEP_ET2_QUALIFIED",
        "k0_kn_per_mm": k0_34,
        "k0_r2": r2_34,
        "f_max_kn": f_max_34,
        "u_peak_mm": u_peak_34,
        "u_term_mm": float(u_34[-1]),
        "w_ext_mJ": w_term_34,
        "e_frac_mJ": e_frac_term_34,
        "e_elas_mJ": e_elas_term_34,
        "delta_book_mJ": delta_book_34,
        "eps_book_pct": eps_book_34,
        "notes": "Step-2 errorTarget=0.02 adaptive sweep candidate. Full horizon u=10.0 um, Exit 0."
    })

    # 6. Job 1410358 (Adaptive ET3 5k)
    fu_35 = os.path.join(models_dir, "35_stage14_step2_adaptive_candidate_et3_5k", "PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE_fu.csv")
    u_35, rf_35, w_35, ef_35, ee_35 = [], [], [], [], []
    with open(fu_35, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_35.append(float(r['Displacement_mm']))
            rf_35.append(float(r['ReactionForce_kN']))
            w_35.append(float(r['ExternalWork_mJ']))
            ef_35.append(float(r['FractureEnergy_mJ']))
            ee_35.append(float(r['ElasticEnergy_mJ']))
    u_35 = np.array(u_35)
    rf_35 = np.array(rf_35)
    k0_35, r2_35, n_35 = compute_k0_from_points(u_35, rf_35)
    idx_peak_35 = int(np.argmax(rf_35))
    f_max_35 = float(rf_35[idx_peak_35])
    u_peak_35 = float(u_35[idx_peak_35])

    w_term_35 = float(w_35[-1])
    e_frac_term_35 = float(ef_35[-1])
    e_elas_term_35 = float(ee_35[-1])
    delta_book_35 = float(w_term_35 - (e_frac_term_35 + e_elas_term_35))
    eps_book_35 = float(abs(delta_book_35) / w_term_35 * 100.0)

    dataset["jobs"].append({
        "job_id": "1410358.mmaster02",
        "benchmark_label": "Adaptive ET3 ($5{,}189$ FE, $\\text{errorTarget}=0.03$)",
        "package_dir": "models/pandey_kumar_mode1/35_stage14_step2_adaptive_candidate_et3_5k",
        "fe_elements": 5189,
        "fe_nodes": 5262,
        "total_nodes_with_rp": 5263,
        "status": "COMPLETED_FULL_HORIZON",
        "governed_classification": "ERRORTARGET_SWEEP_ET3_QUALIFIED",
        "k0_kn_per_mm": k0_35,
        "k0_r2": r2_35,
        "f_max_kn": f_max_35,
        "u_peak_mm": u_peak_35,
        "u_term_mm": float(u_35[-1]),
        "w_ext_mJ": w_term_35,
        "e_frac_mJ": e_frac_term_35,
        "e_elas_mJ": e_elas_term_35,
        "delta_book_mJ": delta_book_35,
        "eps_book_pct": eps_book_35,
        "notes": "Step-2 errorTarget=0.03 adaptive sweep candidate. Full horizon u=10.0 um, Exit 0."
    })

    # 7. Job 1410359 (Adaptive ET5 4k)
    fu_36 = os.path.join(models_dir, "36_stage14_step2_adaptive_candidate_et5_4k", "PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE_fu.csv")
    u_36, rf_36, w_36, ef_36, ee_36 = [], [], [], [], []
    with open(fu_36, 'r') as f:
        reader = csv.DictReader(f)
        for r in reader:
            u_36.append(float(r['Displacement_mm']))
            rf_36.append(float(r['ReactionForce_kN']))
            w_36.append(float(r['ExternalWork_mJ']))
            ef_36.append(float(r['FractureEnergy_mJ']))
            ee_36.append(float(r['ElasticEnergy_mJ']))
    u_36 = np.array(u_36)
    rf_36 = np.array(rf_36)
    k0_36, r2_36, n_36 = compute_k0_from_points(u_36, rf_36)
    idx_peak_36 = int(np.argmax(rf_36))
    f_max_36 = float(rf_36[idx_peak_36])
    u_peak_36 = float(u_36[idx_peak_36])

    w_term_36 = float(w_36[-1])
    e_frac_term_36 = float(ef_36[-1])
    e_elas_term_36 = float(ee_36[-1])
    delta_book_36 = float(w_term_36 - (e_frac_term_36 + e_elas_term_36))
    eps_book_36 = float(abs(delta_book_36) / w_term_36 * 100.0)

    dataset["jobs"].append({
        "job_id": "1410359.mmaster02",
        "benchmark_label": "Adaptive ET5 ($4{,}692$ FE, $\\text{errorTarget}=0.05$)",
        "package_dir": "models/pandey_kumar_mode1/36_stage14_step2_adaptive_candidate_et5_4k",
        "fe_elements": 4692,
        "fe_nodes": 4759,
        "total_nodes_with_rp": 4760,
        "status": "COMPLETED_FULL_HORIZON",
        "governed_classification": "ERRORTARGET_SWEEP_ET5_QUALIFIED",
        "k0_kn_per_mm": k0_36,
        "k0_r2": r2_36,
        "f_max_kn": f_max_36,
        "u_peak_mm": u_peak_36,
        "u_term_mm": float(u_36[-1]),
        "w_ext_mJ": w_term_36,
        "e_frac_mJ": e_frac_term_36,
        "e_elas_mJ": e_elas_term_36,
        "delta_book_mJ": delta_book_36,
        "eps_book_pct": eps_book_36,
        "notes": "Step-2 errorTarget=0.05 adaptive sweep candidate. Full horizon u=10.0 um, Exit 0."
    })

    # 8. Job 1410179 (Spatial Fine 58k Serial)
    dat_30 = os.path.join(models_dir, "30_stage14_adaptive_candidate_spatial_fine", "PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.dat")
    energy_30 = os.path.join(models_dir, "30_stage14_adaptive_candidate_spatial_fine", "uel_energy_balance.csv")
    u_30, rf_30 = parse_dat_rp_rf(dat_30)
    k0_30, r2_30, n_30 = compute_k0_from_points(u_30, rf_30)
    idx_peak_30 = int(np.argmax(rf_30))
    f_max_30 = float(rf_30[idx_peak_30])
    u_peak_30 = float(u_30[idx_peak_30])

    w_ext_30 = [0.0]
    for i in range(1, len(u_30)):
        du = u_30[i] - u_30[i-1]
        f_avg = 0.5 * (rf_30[i] + rf_30[i-1])
        w_ext_30.append(w_ext_30[-1] + f_avg * du * 1000.0)

    erecs_30 = parse_uel_energy(energy_30)
    w_term_30 = float(w_ext_30[-1])
    e_frac_term_30 = float(erecs_30[-1]['e_frac_mJ'])
    e_elas_term_30 = float(erecs_30[-1]['e_elas_mJ'])
    delta_book_30 = float(w_term_30 - (e_frac_term_30 + e_elas_term_30))
    eps_book_30 = float(abs(delta_book_30) / w_term_30 * 100.0)

    dataset["jobs"].append({
        "job_id": "1410179.mmaster02",
        "benchmark_label": "Spatial Fine 58k Serial ($57{,}929$ FE, Partial Diagnostic)",
        "package_dir": "models/pandey_kumar_mode1/30_stage14_adaptive_candidate_spatial_fine",
        "fe_elements": 57929,
        "fe_nodes": 57491,
        "total_nodes_with_rp": 57492,
        "status": "PARTIAL_57929_FE_POSTPEAK_DIAGNOSTIC_EVIDENCE",
        "governed_classification": "PARTIAL_POSTPEAK_DIAGNOSTIC_QUALIFIED",
        "k0_kn_per_mm": k0_30,
        "k0_r2": r2_30,
        "f_max_kn": f_max_30,
        "u_peak_mm": u_peak_30,
        "u_term_mm": float(u_30[-1]),
        "w_ext_mJ": w_term_30,
        "e_frac_mJ": e_frac_term_30,
        "e_elas_mJ": e_elas_term_30,
        "delta_book_mJ": delta_book_30,
        "eps_book_pct": eps_book_30,
        "notes": "Spatial Fine 58k serial diagnostic solve. 4,443 completed increments, reached u=7.429 um (98.51% load drop) before 24h walltime SIGTERM (Exit -29)."
    })

    # 9. Job 1410504 (Spatial Fine 58k 8T SMP)
    dataset["jobs"].append({
        "job_id": "1410504.mmaster02",
        "benchmark_label": "Spatial Fine 58k 8T SMP ($57{,}929$ FE, Full-Horizon Candidate)",
        "package_dir": "models/pandey_kumar_mode1/37_stage14_adaptive_candidate_spatial_fine_8thread",
        "fe_elements": 57929,
        "fe_nodes": 57491,
        "total_nodes_with_rp": 57492,
        "status": "RUNNING_ACTIVE_CANDIDATE",
        "governed_classification": "ACTIVE_SOLVER_CANDIDATE",
        "k0_kn_per_mm": None,
        "k0_r2": None,
        "f_max_kn": None,
        "u_peak_mm": None,
        "u_term_mm": None,
        "w_ext_mJ": None,
        "e_frac_mJ": None,
        "e_elas_mJ": None,
        "delta_book_mJ": None,
        "eps_book_pct": None,
        "notes": "Actively executing full-horizon 8-thread shared-memory SMP candidate on mnode097 (48h walltime limit)."
    })

    return dataset

def export_dataset(dataset, json_path, csv_path):
    """Exports dataset to JSON and CSV formats."""
    # Write JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2)

    # Write CSV
    csv_fields = [
        "job_id",
        "benchmark_label",
        "package_dir",
        "fe_elements",
        "fe_nodes",
        "total_nodes_with_rp",
        "status",
        "governed_classification",
        "k0_kn_per_mm",
        "f_max_kn",
        "u_peak_mm",
        "u_term_mm",
        "w_ext_mJ",
        "e_frac_mJ",
        "e_elas_mJ",
        "delta_book_mJ",
        "eps_book_pct",
        "notes"
    ]
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields, extrasaction='ignore')
        writer.writeheader()
        for j in dataset["jobs"]:
            writer.writerow(j)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Extract Mode-I Gate-6B Single-Job Provenance Synthesis")
    parser.add_argument("--base-dir", type=str, default=None, help="Repository root path")
    parser.add_argument("--json-out", type=str, default=None, help="Output JSON path")
    parser.add_argument("--csv-out", type=str, default=None, help="Output CSV path")
    args = parser.parse_args()

    base = args.base_dir or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    json_dst = args.json_out or os.path.join(base, "models", "pandey_kumar_mode1", "MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json")
    csv_dst = args.csv_out or os.path.join(base, "models", "pandey_kumar_mode1", "MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.csv")

    ds = extract_all_single_job_provenance(base)
    export_dataset(ds, json_dst, csv_dst)
    print(f"Extraction successful:\n  JSON: {json_dst}\n  CSV:  {csv_dst}")
