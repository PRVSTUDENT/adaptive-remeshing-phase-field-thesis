#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
diagnose_c4_c5_energy_transfer.py
Analyzes the exact spatial and component breakdown of the fracture energy deficit
between Donor C4 (Package 94 Step 4 Frame 7) and Mapped C5 (Package 96).
"""

import sys
import math
from pathlib import Path
import numpy as np
import csv

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
GC = 0.0027      # kN/mm
ELL0 = 0.0075    # mm

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

def load_mesh_and_damage(mesh_inp, nodal_csv, is_mapped_csv=False):
    nodes = {}
    elems = {}
    with open(mesh_inp, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                    reading = "NODE"
                elif u.startswith("*ELEMENT") and "TYPE=U1" in u:
                    reading = "U1"
                elif u.startswith("*"):
                    reading = None
                continue
            parts = [p.strip() for p in l.split(",")]
            if reading == "NODE" and len(parts) >= 3 and parts[0].isdigit():
                nid = int(parts[0])
                if nid != 999999:
                    nodes[nid] = np.array([float(parts[1]), float(parts[2])])
            elif reading == "U1" and len(parts) >= 5 and parts[0].isdigit():
                elems[int(parts[0])] = [int(p) for p in parts[1:5]]

    damage = {}
    with open(nodal_csv, "r", encoding="utf-8") as f:
        if is_mapped_csv:
            reader = csv.reader(f)
            header = next(reader)
            for r in reader:
                if len(r) >= 5 and r[0] == "NODE":
                    damage[int(r[1])] = float(r[4])
        else:
            reader = csv.DictReader(f)
            for r in reader:
                damage[int(r["node_id"])] = float(r["damage"])

    return nodes, elems, damage

def compute_fracture_energy(nodes, elems, damage):
    gp_coord = 1.0 / math.sqrt(3.0)
    gauss_pts = [(-gp_coord, -gp_coord), (gp_coord, -gp_coord), (gp_coord, gp_coord), (-gp_coord, gp_coord)]

    e_frac_total = 0.0
    e_pot_total = 0.0
    e_grad_total = 0.0

    elem_energies = {}

    for eid, conn in elems.items():
        elem_pts = np.array([nodes[n] for n in conn])
        elem_d = np.array([damage[n] for n in conn])

        elem_frac = 0.0
        elem_pot = 0.0
        elem_grad = 0.0

        for xi, eta in gauss_pts:
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.vstack([
                np.dot(dNdxi, elem_pts),
                np.dot(dNdeta, elem_pts)
            ])
            detJ = np.linalg.det(J)
            invJ = np.linalg.inv(J)

            # dNdX
            dNdX = np.dot(invJ, np.vstack([dNdxi, dNdeta])) # 2x4

            d_pt = np.dot(N, elem_d)
            grad_d = np.dot(dNdX, elem_d) # 2
            grad_d_sq = np.sum(grad_d**2)

            psi_pot = GC * 0.5 * (d_pt**2) / ELL0
            psi_grad = GC * 0.5 * ELL0 * grad_d_sq

            cjac = detJ * 1.0 # weight = 1.0, thickness = 1.0
            elem_pot += cjac * psi_pot
            elem_grad += cjac * psi_grad
            elem_frac += cjac * (psi_pot + psi_grad)

        e_pot_total += elem_pot
        e_grad_total += elem_grad
        e_frac_total += elem_frac
        elem_energies[eid] = elem_frac

    return {
        "e_total": e_frac_total,
        "e_pot": e_pot_total,
        "e_grad": e_grad_total,
        "elem_energies": elem_energies
    }

def main():
    c4_mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp"
    c4_nodal_csv = REPO_ROOT / "results/validation/mode1_f1597/pkg94_step4_frame7_nodal_state.csv"

    c5_mesh_inp = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_crack_band_mesh_c5.inp"
    c5_mapped_csv = REPO_ROOT / "models/pandey_kumar_mode1/96_c5_package96_authentic_transfer/candidate_c5_frame7_mapped_state_table.csv"

    print("Computing C4 donor energy...")
    c4_nodes, c4_elems, c4_damage = load_mesh_and_damage(c4_mesh_inp, c4_nodal_csv, is_mapped_csv=False)
    c4_res = compute_fracture_energy(c4_nodes, c4_elems, c4_damage)

    print("Computing C5 mapped energy...")
    c5_nodes, c5_elems, c5_damage = load_mesh_and_damage(c5_mesh_inp, c5_mapped_csv, is_mapped_csv=True)
    c5_res = compute_fracture_energy(c5_nodes, c5_elems, c5_damage)

    print("\n=== FRACTURE ENERGY BREAKDOWN ===")
    print(f"C4 Donor Total:  {c4_res['e_total']:.10e} kN*mm")
    print(f"  Potential:     {c4_res['e_pot']:.10e} kN*mm ({c4_res['e_pot']/c4_res['e_total']*100:.2f}%)")
    print(f"  Gradient:      {c4_res['e_grad']:.10e} kN*mm ({c4_res['e_grad']/c4_res['e_total']*100:.2f}%)")

    print(f"\nC5 Mapped Total: {c5_res['e_total']:.10e} kN*mm")
    print(f"  Potential:     {c5_res['e_pot']:.10e} kN*mm ({c5_res['e_pot']/c5_res['e_total']*100:.2f}%)")
    print(f"  Gradient:      {c5_res['e_grad']:.10e} kN*mm ({c5_res['e_grad']/c5_res['e_total']*100:.2f}%)")

    diff_tot = (c5_res['e_total'] - c4_res['e_total']) / c4_res['e_total'] * 100.0
    diff_pot = (c5_res['e_pot'] - c4_res['e_pot']) / c4_res['e_pot'] * 100.0
    diff_grad = (c5_res['e_grad'] - c4_res['e_grad']) / c4_res['e_grad'] * 100.0

    print(f"\nDiscrepancy:")
    print(f"  Total:     {diff_tot:+.4f}%")
    print(f"  Potential: {diff_pot:+.4f}%")
    print(f"  Gradient:  {diff_grad:+.4f}%")

if __name__ == "__main__":
    main()
