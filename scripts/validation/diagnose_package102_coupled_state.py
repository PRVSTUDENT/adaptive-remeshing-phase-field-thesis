#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_package102_coupled_state.py
Comprehensive diagnostic audit of Package 102 authentic simulation outputs.
"""
import sys
import json
import csv
import numpy as np
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG102_DIR = REPO_ROOT / "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration"

def load_extracted_data():
    csv_path = PKG102_DIR / "M1_C5_PACKAGE102_STAGGERED_REEQUIL_extracted.csv"
    nodal_data = {} # nid -> (u1, u2, d_abq)
    elem_gp_data = {} # (eid, ip) -> (d, h)
    rf2 = None
    u2_rp = None
    
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row: continue
            rtype = row[0].strip().upper()
            if rtype == "RF2":
                rf2 = float(row[2]) * 1000.0 # kN to N
            elif rtype == "U2_RP":
                u2_rp = float(row[2])
            elif rtype == "NODE":
                nid = int(row[1])
                u1 = float(row[2])
                u2 = float(row[3])
                d = float(row[4])
                nodal_data[nid] = (u1, u2, d)
            elif rtype == "ELEM_GP":
                eid = int(row[1])
                ip = int(row[2])
                d = float(row[3])
                h = float(row[4])
                elem_gp_data[(eid, ip)] = (d, h)
                
    return rf2, u2_rp, nodal_data, elem_gp_data

def load_checkpoint_and_opt():
    # Checkpoint mapped state
    state_table = PKG102_DIR / "candidate_c5_frame7_mapped_state_table.csv"
    d_ckpt = {}
    with open(state_table, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if parts and parts[0].upper() == "NODE":
                d_ckpt[int(parts[1])] = float(parts[4])
                
    # d_opt
    d_opt_arr = np.load(PKG102_DIR / "turn89_c5_staggered_d_opt.npy")
    d_opt = {i + 1: float(d_opt_arr[i]) for i in range(len(d_opt_arr))}
    
    # Updated H table
    h_new = {}
    with open(PKG102_DIR / "turn89_c5_updated_h_table.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row or len(row) < 6: continue
            if row[0].strip().upper() == "ELEM_HISTORY":
                eid = int(row[1])
                for ip in range(1, 5):
                    h_new[(eid, ip)] = float(row[1 + ip])
            
    return d_ckpt, d_opt, h_new

def main():
    rf2, u2_rp, nodal_data, elem_gp_data = load_extracted_data()
    d_ckpt, d_opt, h_new = load_checkpoint_and_opt()
    
    print(f"Loaded: RF2 = {rf2:.4f} N, U2_RP = {u2_rp:.6f} mm")
    print(f"Nodes extracted: {len(nodal_data)}, Element IPs extracted: {len(elem_gp_data)}")
    
    # 1. Nodal d comparisons
    diff_d_opt = []
    diff_d_ckpt = []
    healing_nodes = []
    overshoot_nodes = []
    
    for nid, (u1, u2, d_abq) in nodal_data.items():
        if nid in d_opt:
            diff_d_opt.append(abs(d_abq - d_opt[nid]))
        if nid in d_ckpt:
            delta = d_abq - d_ckpt[nid]
            diff_d_ckpt.append(delta)
            if delta < -1e-6:
                healing_nodes.append((nid, delta))
        if d_abq > 1.0 + 1e-6:
            overshoot_nodes.append((nid, d_abq))
            
    max_diff_opt = max(diff_d_opt) if diff_d_opt else 0.0
    min_delta_ckpt = min(diff_d_ckpt) if diff_d_ckpt else 0.0
    max_d_abq = max(v[2] for v in nodal_data.values())
    
    print("\n--- NODAL PHASE FIELD (DOF 3) AUDIT ---")
    print(f"Max |d_abq - d_opt|: {max_diff_opt:.16e}")
    print(f"Min (d_abq - d_ckpt): {min_delta_ckpt:.16e}")
    print(f"Max d_abq: {max_d_abq:.8f}")
    print(f"Healing nodes count (< -1e-6): {len(healing_nodes)}")
    print(f"Overshoot nodes count (> 1.0 + 1e-6): {len(overshoot_nodes)}")
    
    # 2. History comparison
    h_diffs = []
    h_abq_vals = []
    h_new_vals = []
    diff_gp_count = 0
    
    for (eid, ip), (d_gp, h_abq) in elem_gp_data.items():
        # Note: In companion elements, eid in elem_gp is companion eid (8881..13320).
        # UEL eid is companion eid - 8880.
        uel_eid = eid - 8880 if eid > 8880 else eid
        if (uel_eid, ip) in h_new:
            h_target = h_new[(uel_eid, ip)]
            diff = h_abq - h_target
            h_diffs.append(diff)
            h_abq_vals.append(h_abq)
            h_new_vals.append(h_target)
            if abs(diff) > 1e-8:
                diff_gp_count += 1
                
    print("\n--- GAUSS-POINT HISTORY FIELD (H) AUDIT ---")
    print(f"Total matched Gauss points: {len(h_diffs)}")
    if h_diffs:
        print(f"Max (H_abq - H_new): {max(h_diffs):.10e} kN/mm^2")
        print(f"Min (H_abq - H_new): {min(h_diffs):.10e} kN/mm^2")
        print(f"Gauss points where H_abq != H_new (|diff| > 1e-8): {diff_gp_count}")
        print(f"Max H_abq: {max(h_abq_vals):.4f} kN/mm^2, Max H_new: {max(h_new_vals):.4f} kN/mm^2")
        
    # 3. Energy audit
    # Read from uel_energy_balance.csv
    energy_csv = PKG102_DIR / "uel_energy_balance.csv"
    e_frac_mj = None
    e_elas_mj = None
    e_tot_mj = None
    if energy_csv.exists():
        with open(energy_csv, "r", encoding="utf-8") as f:
            lines = [l.strip().split(",") for l in f if l.strip()]
            if len(lines) >= 2:
                last_line = lines[-1]
                e_elas_mj = float(last_line[4]) * 1000.0
                e_frac_mj = float(last_line[5]) * 1000.0
                e_tot_mj = float(last_line[6]) * 1000.0
                
    donor_rf2 = 112.97
    donor_e_frac = 0.137737
    
    rf_err = (rf2 - donor_rf2) / donor_rf2 * 100.0
    e_frac_err = (e_frac_mj - donor_e_frac) / donor_e_frac * 100.0 if e_frac_mj else 0.0
    
    print("\n--- REACTION FORCE & ENERGY CONTINUITY AUDIT ---")
    print(f"RF2: {rf2:.4f} N (Donor: {donor_rf2:.4f} N, Error: {rf_err:+.2f}%, Threshold: <= 5.0%) -> {'PASS' if abs(rf_err) <= 5.0 else 'FAIL'}")
    print(f"E_frac: {e_frac_mj:.6f} mJ (Donor: {donor_e_frac:.6f} mJ, Error: {e_frac_err:+.2f}%, Threshold: <= 2.0%) -> {'PASS' if abs(e_frac_err) <= 2.0 else 'FAIL'}")
    print(f"E_elas: {e_elas_mj:.6f} mJ")
    print(f"E_tot: {e_tot_mj:.6f} mJ")
    
    # Summary report
    diag_summary = {
        "package": "PACKAGE_102",
        "job_id": "1417164.mmaster02",
        "rf2_N": rf2,
        "donor_rf2_N": donor_rf2,
        "rf_error_pct": rf_err,
        "force_continuity_passed": bool(abs(rf_err) <= 5.0),
        "e_frac_mJ": e_frac_mj,
        "donor_e_frac_mJ": donor_e_frac,
        "e_frac_error_pct": e_frac_err,
        "fracture_energy_passed": bool(abs(e_frac_err) <= 2.0),
        "e_elas_mJ": e_elas_mj,
        "e_tot_mJ": e_tot_mj,
        "max_abs_diff_d_opt": max_diff_opt,
        "min_delta_d_ckpt": min_delta_ckpt,
        "healing_count": len(healing_nodes),
        "overshoot_count": len(overshoot_nodes),
        "gp_history_diff_count": diff_gp_count,
        "max_h_diff": max(h_diffs) if h_diffs else 0.0,
        "min_h_diff": min(h_diffs) if h_diffs else 0.0,
        "governed_gate_c1_2": "NOT_QUALIFIED"
    }
    
    out_json = REPO_ROOT / "results/validation/mode1_f1597/turn90_pkg102_detailed_diagnosis.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(diag_summary, f, indent=2)
    print(f"\nWrote detailed diagnostic summary to {out_json}")

if __name__ == "__main__":
    main()
