#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
compute_pkg90_r1_consistent_history.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Evaluates 100% self-consistent Gauss-point strain energy history H for Package 90-R1 Frame 6
directly from authentic nodal displacements and deck initial history conditions using the exact
constitutive equations from production UEL f42_mixed_uel.for.

Constitutive formulation in f42_mixed_uel.for (lines 411-414, 513-531):
  C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))
  C12_0 = E_MOD*E_NU/((ONE + E_NU)*(ONE - TWO*E_NU))
  C33_0 = E_MOD/(TWO*(ONE + E_NU))
  E11 = eps_11, E22 = eps_22, E12 = 0.5 * gamma_12
  tr_E = E11 + E22
  E_POS = max(0.0, tr_E)
  POS_M = 0.5 * C12_0 * (E_POS**2) + C33_0 * (E11**2 + E22**2 + 2.0 * E12**2)
  H = max(H_initial, POS_M)
"""

import os
import sys
import math
import csv
import json
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

# Physical constants from frozen deck
E_MOD = 210.0      # kN/mm^2 (210 GPa)
E_NU = 0.3
C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

PKG90_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer"
C3_MESH_INP = PKG90_R1_DIR / "candidate_crack_band_mesh_c3.inp"
PKG90_R1_INP = PKG90_R1_DIR / "M1_C3_PACKAGE90_R1_TRANSFER.inp"
PKG90_R1_NODAL_CSV = REPO_ROOT / "results/validation/mode1_f1597/pkg90_r1_frame6_nodal_state.csv"

OUT_CSV = REPO_ROOT / "results/validation/mode1_f1597/pkg90_r1_frame6_consistent_gauss_point_history.csv"
OUT_SUMMARY_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg90_r1_consistent_history_summary.json"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def parse_initial_history(inp_path: Path):
    """Extracts H_initial for all elements from INITIAL CONDITIONS in input deck."""
    print(f"Parsing initial conditions from {inp_path}...")
    elem_h_init = {}
    with open(inp_path, "r", encoding="utf-8") as f:
        in_init = False
        current_eid = None
        state = 0
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if "*INITIAL CONDITIONS" in u and "TYPE=SOLUTION" in u:
                    in_init = True
                    state = 0
                    continue
                elif in_init:
                    # New keyword encountered, exit INITIAL CONDITIONS
                    break
            if in_init:
                parts = [p.strip() for p in l.split(",")]
                if state == 0:
                    # Line 1: eid, 8 values
                    if parts[0].isdigit():
                        current_eid = int(parts[0])
                        state = 1
                elif state == 1:
                    # Line 2: H1, H2, H3, H4, 4 values
                    h_vals = [float(p) for p in parts[:4]]
                    elem_h_init[current_eid] = h_vals
                    state = 2
                elif state == 2:
                    # Line 3: 2 values
                    state = 0
    print(f"Extracted initial history for {len(elem_h_init)} elements.")
    return elem_h_init

def parse_mesh_and_displacements():
    """Parses C3 nodes, elements, and Frame 6 displacements."""
    nodes = {}
    with open(C3_MESH_INP, "r", encoding="utf-8") as f:
        reading = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                    reading = True
                else:
                    reading = False
                continue
            if reading:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3 and parts[0].isdigit():
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(parts[1]), float(parts[2])])

    elements = {}
    with open(C3_MESH_INP, "r", encoding="utf-8") as f:
        reading = False
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*ELEMENT") and "TYPE=U1" in u:
                    reading = True
                else:
                    reading = False
                continue
            if reading:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 5 and parts[0].isdigit():
                    eid = int(parts[0])
                    elements[eid] = [int(p) for p in parts[1:5]]

    nodal_disp = {}
    with open(PKG90_R1_NODAL_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            nid = int(row["node_id"])
            nodal_disp[nid] = np.array([float(row["u1"]), float(row["u2"])])

    print(f"Parsed {len(nodes)} nodes, {len(elements)} quads, {len(nodal_disp)} nodal displacements.")
    return nodes, elements, nodal_disp

def compute_consistent_history():
    nodes, elements, nodal_disp = parse_mesh_and_displacements()
    elem_h_init = parse_initial_history(PKG90_R1_INP)

    gp_coord = 1.0 / math.sqrt(3.0)
    xg4 = [-gp_coord, gp_coord, gp_coord, -gp_coord]
    yg4 = [-gp_coord, -gp_coord, gp_coord, gp_coord]

    results = []
    h_values = []
    pos_m_values = []
    updated_count = 0

    for eid in sorted(elements.keys()):
        conn = elements[eid]
        elem_coords = np.array([nodes[n] for n in conn])  # 4x2
        elem_disp = np.array([nodal_disp[n] for n in conn])  # 4x2
        u_vec = np.zeros(8)
        for i in range(4):
            u_vec[2*i] = elem_disp[i, 0]
            u_vec[2*i+1] = elem_disp[i, 1]

        h_init_elem = elem_h_init.get(eid, [0.0, 0.0, 0.0, 0.0])

        for kpt in range(4):
            xi = xg4[kpt]
            eta = yg4[kpt]

            d_n = np.zeros((2, 4))
            d_n[0, 0] = -0.25 * (1.0 - eta)
            d_n[0, 1] =  0.25 * (1.0 - eta)
            d_n[0, 2] =  0.25 * (1.0 + eta)
            d_n[0, 3] = -0.25 * (1.0 + eta)

            d_n[1, 0] = -0.25 * (1.0 - xi)
            d_n[1, 1] = -0.25 * (1.0 + xi)
            d_n[1, 2] =  0.25 * (1.0 + xi)
            d_n[1, 3] =  0.25 * (1.0 - xi)

            jac = d_n @ elem_coords  # 2x2
            detj = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 2] if False else np.linalg.det(jac)
            assert detj > 0.0, f"Non-positive Jacobian in element {eid}"

            invj = np.linalg.inv(jac)
            dNdx = invj @ d_n  # 2x4

            # B matrix (3x8)
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[0, 2*i+1] = 0.0
                B[1, 2*i]   = 0.0
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]

            strain = B @ u_vec
            e11 = strain[0]
            e22 = strain[1]
            e12 = 0.5 * strain[2]

            tr_e = e11 + e22
            e_pos = max(0.0, tr_e)

            # Exact UEL formula (lines 524-525)
            pos_m = 0.5 * C12_0 * (e_pos ** 2) + C33_0 * (e11**2 + e22**2 + 2.0 * (e12**2))

            h_prior = h_init_elem[kpt]
            h_final = max(h_prior, pos_m)

            if pos_m > h_prior:
                updated_count += 1

            h_values.append(h_final)
            pos_m_values.append(pos_m)

            # Gauss point coordinates
            N = 0.25 * np.array([
                (1.0 - xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 + eta),
                (1.0 - xi) * (1.0 + eta)
            ])
            gp_x = float(np.dot(N, elem_coords[:, 0]))
            gp_y = float(np.dot(N, elem_coords[:, 1]))

            results.append({
                "phys_eid": eid,
                "integration_point": kpt + 1,
                "x_mm": gp_x,
                "y_mm": gp_y,
                "H_init": h_prior,
                "psi0_pos": pos_m,
                "H": h_final
            })

    print(f"Evaluated {len(results)} Gauss points.")
    print(f"Points where psi0 > H_init (history advanced): {updated_count} / {len(results)} ({100*updated_count/len(results):.2f}%)")
    print(f"H range: [{min(h_values):.6e}, {max(h_values):.6e}], mean: {np.mean(h_values):.6e}")

    # Write CSV
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["phys_eid", "integration_point", "x_mm", "y_mm", "H_init", "psi0_pos", "H"])
        writer.writeheader()
        writer.writerows(results)

    csv_hash = sha256_file(OUT_CSV)
    print(f"Saved: {OUT_CSV} (SHA-256: {csv_hash})")

    summary = {
        "status": "PKG90_R1_CONSISTENT_HISTORY_EVALUATED",
        "total_elements": len(elements),
        "total_gauss_points": len(results),
        "updated_gauss_points": updated_count,
        "h_min": float(min(h_values)),
        "h_max": float(max(h_values)),
        "h_mean": float(np.mean(h_values)),
        "psi0_max": float(max(pos_m_values)),
        "donor_source": "Package 90-R1 Frame 6 (u2=0.0020367 mm, RF2=159.16 N)",
        "constitutive_source": "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for",
        "output_csv": str(OUT_CSV.relative_to(REPO_ROOT)).replace("\\", "/"),
        "sha256": csv_hash
    }

    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"Saved: {OUT_SUMMARY_JSON}")
    return summary

if __name__ == "__main__":
    compute_consistent_history()
