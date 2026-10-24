#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_fracture_energy_decomposition.py
Decomposes Bourdin AT2 fracture energy into local and gradient terms on mesh C5.
"""
import csv
import numpy as np
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG102_DIR = REPO_ROOT / "models/pandey_kumar_mode1/102_c5_coupled_staggered_reequilibration"

def shape_functions(xi, eta):
    N = 0.25 * np.array([
        (1.0 - xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 - eta),
        (1.0 + xi) * (1.0 + eta),
        (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = 0.25 * np.array([
        -(1.0 - eta),  (1.0 - eta),  (1.0 + eta), -(1.0 + eta)
    ])
    dNdeta = 0.25 * np.array([
        -(1.0 - xi), -(1.0 + xi),  (1.0 + xi),  (1.0 - xi)
    ])
    return N, dNdxi, dNdeta

def compute_decomposed_energies(d_dict, G_C=0.0027, L_0=0.0075):
    mesh_inp = PKG102_DIR / "candidate_crack_band_mesh_c5.inp"
    nodes = {}
    elements = {}
    with open(mesh_inp, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"): continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT"):
                    reading = "ELEMENT"
                else:
                    reading = None
                continue
            if reading == "NODE":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(parts[1]), float(parts[2])])
            elif reading == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    if eid <= 4440:
                        elements[eid] = [int(p) for p in parts[1:5]]

    gauss_pts = [-1.0 / np.sqrt(3.0), 1.0 / np.sqrt(3.0)]
    weights = [1.0, 1.0]

    e_local_tot = 0.0
    e_grad_tot = 0.0

    for eid, conn in elements.items():
        xe = np.array([nodes[nid] for nid in conn])
        de = np.array([d_dict.get(nid, 0.0) for nid in conn])

        for xi, wx in zip(gauss_pts, weights):
            for eta, wy in zip(gauss_pts, weights):
                N, dNdxi, dNdeta = shape_functions(xi, eta)
                J = np.vstack([dNdxi, dNdeta]) @ xe
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                dNdx = invJ @ np.vstack([dNdxi, dNdeta])
                dV = detJ * wx * wy

                d_pt = float(N @ de)
                grad_d = dNdx @ de
                grad_sq = float(grad_d @ grad_d)

                psi_local = (G_C / (2.0 * L_0)) * (d_pt ** 2)
                psi_grad = (G_C * L_0 / 2.0) * grad_sq

                e_local_tot += psi_local * dV
                e_grad_tot += psi_grad * dV

    return e_local_tot, e_grad_tot, e_local_tot + e_grad_tot

def main():
    # Load d_ckpt
    state_table = PKG102_DIR / "candidate_c5_frame7_mapped_state_table.csv"
    d_ckpt = {}
    with open(state_table, "r", encoding="utf-8") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if parts and parts[0].upper() == "NODE":
                d_ckpt[int(parts[1])] = float(parts[4])

    # Load d_abq
    extracted_csv = PKG102_DIR / "M1_C5_PACKAGE102_STAGGERED_REEQUIL_extracted.csv"
    d_abq = {}
    with open(extracted_csv, "r", encoding="utf-8") as f:
        for row in csv.reader(f):
            if not row: continue
            if row[0].strip().upper() == "NODE":
                d_abq[int(row[1])] = float(row[4])

    loc_ckpt, grad_ckpt, tot_ckpt = compute_decomposed_energies(d_ckpt)
    loc_abq, grad_abq, tot_abq = compute_decomposed_energies(d_abq)

    # Convert to mJ (kN*mm * 1000)
    loc_ckpt_mj, grad_ckpt_mj, tot_ckpt_mj = loc_ckpt * 1000, grad_ckpt * 1000, tot_ckpt * 1000
    loc_abq_mj, grad_abq_mj, tot_abq_mj = loc_abq * 1000, grad_abq * 1000, tot_abq * 1000
    donor_tot_mj = 0.137737

    print("--- FRACTURE ENERGY DECOMPOSITION (AT2 MODEL) ---")
    print(f"Transferred Checkpoint d_ckpt:")
    print(f"  E_local:    {loc_ckpt_mj:.6f} mJ")
    print(f"  E_gradient: {grad_ckpt_mj:.6f} mJ")
    print(f"  E_fracture: {tot_ckpt_mj:.6f} mJ (Error vs donor {donor_tot_mj:.6f} mJ: {(tot_ckpt_mj - donor_tot_mj)/donor_tot_mj*100:+.2f}%)")
    print(f"Package 102 Authentic d_abq:")
    print(f"  E_local:    {loc_abq_mj:.6f} mJ")
    print(f"  E_gradient: {grad_abq_mj:.6f} mJ")
    print(f"  E_fracture: {tot_abq_mj:.6f} mJ (Error vs donor {donor_tot_mj:.6f} mJ: {(tot_abq_mj - donor_tot_mj)/donor_tot_mj*100:+.2f}%)")
    print(f"Energy Changes (d_abq - d_ckpt):")
    print(f"  Delta E_local:    {loc_abq_mj - loc_ckpt_mj:+.6f} mJ ({(loc_abq_mj - loc_ckpt_mj)/loc_ckpt_mj*100:+.2f}%)")
    print(f"  Delta E_gradient: {grad_abq_mj - grad_ckpt_mj:+.6f} mJ ({(grad_abq_mj - grad_ckpt_mj)/grad_ckpt_mj*100:+.2f}%)")
    print(f"  Delta E_fracture: {tot_abq_mj - tot_ckpt_mj:+.6f} mJ ({(tot_abq_mj - tot_ckpt_mj)/tot_ckpt_mj*100:+.2f}%)")

if __name__ == "__main__":
    main()
