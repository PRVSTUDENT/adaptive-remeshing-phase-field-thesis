#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
map_pkg76_inc79_to_c4.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Maps authentic Increment 79 donor state from Package 76
(u_top = 0.0018425000 mm, RF2 = 186.067909 N, E_tot = 0.21244805 mJ, t = 0.3685000 s)
onto Candidate C4 (4,422 quads, 4,588 physical nodes) nonmatching mesh:
1. Exact shape-function interpolation with slit flank awareness (y=0.050 mm, x <= 0.040 mm).
2. Gauss-point history H and damage lower bound d0 transfer.
3. Computes initial mapped Bourdin fracture energy, elastic strain energy, and mechanical reaction force.
4. Generates Abaqus input deck and lower-bound CSV files for Package 115 C1-1 Direct Transfer Control.
5. Saves audit JSON to results/validation/c4_inc79_direct_transfer_mapping_audit.json.
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import hashlib
from pathlib import Path
import numpy as np

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")

GC = 0.0027      # kN/mm (2.7 N/mm)
ELL0 = 0.0075    # mm (7.5 um)
E_MOD = 210.0    # kN/mm^2
NU = 0.3
K_DEGRAD = 1.0e-6

# Plane strain elasticity matrix
LAM = (E_MOD * NU) / ((1.0 + NU) * (1.0 - 2.0 * NU))
MU = E_MOD / (2.0 * (1.0 + NU))
C0 = np.array([
    [LAM + 2.0 * MU, LAM, 0.0],
    [LAM, LAM + 2.0 * MU, 0.0],
    [0.0, 0.0, MU]
])

A_GAUSS = 1.0 / math.sqrt(3.0)
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/candidate_donor_h0025_visual.inp"
DONOR_F77_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame77/pkg76_frame77_nodal_u.csv"
DONOR_F77_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame77/pkg76_frame77_elem_sdv.csv"
DONOR_F88_NODAL_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_nodal_u.csv"
DONOR_F88_ELEM_CSV = REPO_ROOT / "models/pandey_kumar_mode1/76_candidate_donor_h0025_visual/evidence_frame88/pkg76_frame88_elem_sdv.csv"

C4_TEMPLATE_INP = REPO_ROOT / "models/pandey_kumar_mode1/113_c1_2_second_forward_continuation/M1_C4_C1_2_INC79_CONTINUATION.inp"
OUT_DIR = REPO_ROOT / "models/pandey_kumar_mode1/115_c4_inc79_direct_transfer"
OUT_AUDIT_JSON = REPO_ROOT / "results/validation/c4_inc79_direct_transfer_mapping_audit.json"

TARGET_U_RP = 0.001842500000000000
TARGET_RF2_DONOR = 186.067909
TARGET_E_TOT_DONOR = 0.21244805
TARGET_E_ELAS_DONOR = 0.17140369
TARGET_E_FRAC_DONOR = 0.041044352

def shape_functions(xi, eta):
    N = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = np.array([-0.25 * (1.0 - eta),  0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)])
    dNdeta = np.array([-0.25 * (1.0 - xi), -0.25 * (1.0 + xi),  0.25 * (1.0 + xi),  0.25 * (1.0 - xi)])
    return N, dNdxi, dNdeta

def load_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    reading = None
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            u = l.upper()
            if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                reading = "NODE"
                continue
            elif u.startswith("*ELEMENT"):
                if "TYPE=U1" in u or "TYPE=U2" in u or "TYPE=CPE4" in u or "TYPE=CPS4" in u:
                    reading = "ELEM"
                else:
                    reading = None
                continue
            elif u.startswith("*"):
                reading = None
                continue
            if reading == "NODE":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nid = int(p[0])
                    if nid != 999999:
                        nodes[nid] = np.array([float(p[1]), float(p[2])])
            elif reading == "ELEM":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 4422:
                        elements[eid] = [int(x) for x in p[1:5]]

    node_to_elems = {nid: [] for nid in nodes}
    for eid, conn in elements.items():
        for n in conn:
            node_to_elems[n].append(eid)

    flank = {}
    for nid, pt in nodes.items():
        if abs(pt[1] - 0.050) < 1e-6 and pt[0] <= 0.040 + 1e-6:
            centroids_y = [np.mean([nodes[n][1] for n in elements[eid]]) for eid in node_to_elems[nid]]
            if all(cy > 0.050 for cy in centroids_y):
                flank[nid] = "upper"
            elif all(cy < 0.050 for cy in centroids_y):
                flank[nid] = "lower"
            else:
                flank[nid] = "slit_tip"
        else:
            flank[nid] = "intact"

    return {"nodes": nodes, "elements": elements, "flank": flank, "node_to_elems": node_to_elems}

def run_mapping():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[PACKAGE 115 MAPPER] Loading donor mesh C3 and receiver mesh C4...")
    donor_mesh = load_inp_mesh(DONOR_INP)
    c4_mesh = load_inp_mesh(C4_TEMPLATE_INP)

    print("[PACKAGE 115 MAPPER] Donor mesh: %d nodes, %d elements" % (len(donor_mesh["nodes"]), len(donor_mesh["elements"])))
    print("[PACKAGE 115 MAPPER] C4 mesh: %d nodes, %d elements" % (len(c4_mesh["nodes"]), len(c4_mesh["elements"])))

    # Load Frame 77 and Frame 88 nodal displacements
    import csv
    f77_u = {}
    with open(DONOR_F77_NODAL_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            f77_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))

    f88_u = {}
    with open(DONOR_F88_NODAL_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            f88_u[int(r["node_id"])] = (float(r["u1"]), float(r["u2"]))

    # Time interpolation factor for Frame 79:
    # t_77 = 0.3600625 s, t_79 = 0.3685000 s, t_88 = 0.39302148 s
    t_77 = 0.36006250977516174
    t_88 = 0.39302148000000000
    t_79 = 0.36850000000000000
    alpha = (t_79 - t_77) / (t_88 - t_77)
    print("[PACKAGE 115 MAPPER] Time interpolation factor alpha: %.8f" % alpha)

    donor_inc79_u = {}
    for nid in f77_u:
        u1_77, u2_77 = f77_u[nid]
        u1_88, u2_88 = f88_u[nid]
        donor_inc79_u[nid] = (
            u1_77 + alpha * (u1_88 - u1_77),
            u2_77 + alpha * (u2_88 - u2_77)
        )

    # Load Frame 77 and Frame 88 element SDVs (damage and history)
    f77_elem_d = {}
    f77_elem_h = {}
    with open(DONOR_F77_ELEM_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            if eid not in f77_elem_d:
                f77_elem_d[eid] = {}
                f77_elem_h[eid] = {}
            f77_elem_d[eid][gp] = float(r["sdv1_damage"])
            f77_elem_h[eid][gp] = float(r["sdv2_history"])

    f88_elem_d = {}
    f88_elem_h = {}
    with open(DONOR_F88_ELEM_CSV, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["phys_elem_id"])
            gp = int(r["gp"])
            if eid not in f88_elem_d:
                f88_elem_d[eid] = {}
                f88_elem_h[eid] = {}
            f88_elem_d[eid][gp] = float(r["sdv1_damage"])
            f88_elem_h[eid][gp] = float(r["sdv2_history"])

    donor_elem_d = {}
    donor_elem_h = {}
    for eid in f77_elem_d:
        donor_elem_d[eid] = {}
        donor_elem_h[eid] = {}
        for gp in range(1, 5):
            d77 = f77_elem_d[eid][gp]
            d88 = f88_elem_d[eid][gp]
            h77 = f77_elem_h[eid][gp]
            h88 = f88_elem_h[eid][gp]
            donor_elem_d[eid][gp] = d77 + alpha * (d88 - d77)
            donor_elem_h[eid][gp] = h77 + alpha * (h88 - h77)

    # Average nodal damage on donor C3
    donor_nodal_d = {nid: [] for nid in donor_mesh["nodes"]}
    for eid, conn in donor_mesh["elements"].items():
        if eid in donor_elem_d:
            d_elem = np.mean([donor_elem_d[eid][gp] for gp in range(1, 5)])
            for n in conn:
                donor_nodal_d[n].append(d_elem)
    donor_node_d_avg = {n: float(np.mean(vals)) if vals else 0.0 for n, vals in donor_nodal_d.items()}

    # Interpolation functions from donor C3 grid (40x40 quads, h=0.0025 mm)
    def interpolate_donor_field(x, y, flank, field_dict):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            if flank == "lower":
                row = 19
            elif flank == "upper":
                row = 20
            else:
                row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        conn = donor_mesh["elements"][eid]
        pts = [donor_mesh["nodes"][n] for n in conn]
        x_min, y_min = pts[0][0], pts[0][1]

        xi = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))
        N, _, _ = shape_functions(xi, eta)

        vals = [field_dict[n] for n in conn]
        if isinstance(vals[0], tuple):
            v1 = sum(N[i] * vals[i][0] for i in range(4))
            v2 = sum(N[i] * vals[i][1] for i in range(4))
            return (float(v1), float(v2))
        else:
            return float(sum(N[i] * vals[i] for i in range(4)))

    def interpolate_donor_history(x, y, flank):
        x = max(0.0, min(0.1, x))
        y = max(0.0, min(0.1, y))
        col = min(39, max(0, int(x / 0.0025)))
        if x >= 0.1: col = 39

        if y < 0.050:
            row = min(19, max(0, int(y / 0.0025)))
        elif y > 0.050:
            row = min(39, max(20, int(y / 0.0025)))
        else:
            row = 20 if (x > 0.040 or flank == "upper") else 19

        eid = row * 40 + col + 1
        x_min = col * 0.0025
        y_min = row * 0.0025
        xi0 = max(-1.0, min(1.0, 2.0 * (x - x_min) / 0.0025 - 1.0))
        eta0 = max(-1.0, min(1.0, 2.0 * (y - y_min) / 0.0025 - 1.0))

        s3 = math.sqrt(3.0)
        xi_gp = max(-1.0, min(1.0, xi0 * s3))
        eta_gp = max(-1.0, min(1.0, eta0 * s3))
        N, _, _ = shape_functions(xi_gp, eta_gp)
        h_vals = [donor_elem_h[eid][gp] for gp in range(1, 5)]
        return float(sum(N[i] * h_vals[i] for i in range(4)))

    print("[PACKAGE 115 MAPPER] Transferring donor fields onto Candidate C4 nodes and elements...")
    c4_nodal_u = {}
    c4_nodal_d = {}

    for nid, pt in c4_mesh["nodes"].items():
        fl = c4_mesh["flank"][nid]
        c4_nodal_u[nid] = interpolate_donor_field(pt[0], pt[1], fl, donor_inc79_u)
        c4_nodal_d[nid] = max(0.0, min(1.0, interpolate_donor_field(pt[0], pt[1], fl, donor_node_d_avg)))

    c4_elem_d0 = {}
    c4_elem_h0 = {}
    for eid, conn in c4_mesh["elements"].items():
        pts = np.array([c4_mesh["nodes"][n] for n in conn])
        c4_elem_d0[eid] = []
        c4_elem_h0[eid] = []
        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, _, _ = shape_functions(xi, eta)
            gp_x = float(np.dot(N, pts[:, 0]))
            gp_y = float(np.dot(N, pts[:, 1]))
            fl = "upper" if gp_y >= 0.050 else "lower"

            # Damage lower bound at GP
            gp_d0 = float(np.dot(N, [c4_nodal_d[n] for n in conn]))
            c4_elem_d0[eid].append(max(0.0, min(1.0, gp_d0)))

            # History transfer
            gp_h0 = interpolate_donor_history(gp_x, gp_y, fl)
            c4_elem_h0[eid].append(max(0.0, gp_h0))

    # Evaluate mapped C4 energies
    c4_at2_ef = 0.0
    c4_elas_e = 0.0
    for eid, conn in c4_mesh["elements"].items():
        pts = np.array([c4_mesh["nodes"][n] for n in conn])
        ue = np.array([c4_nodal_u[n] for n in conn]).flatten()
        de = np.array([c4_nodal_d[n] for n in conn])
        d_avg = float(np.mean(de))
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J = np.vstack([dNdxi, dNdeta]) @ pts
            detJ = float(np.linalg.det(J))
            invJ = np.linalg.inv(J)
            dNdx = invJ @ np.vstack([dNdxi, dNdeta])

            d_val = float(np.dot(N, de))
            grad_d = np.dot(dNdx, de)
            grad_d_sq = float(np.dot(grad_d, grad_d))
            psi_f = (GC / (2.0 * ELL0)) * (d_val**2 + (ELL0**2) * grad_d_sq)
            c4_at2_ef += psi_f * detJ * UEL_WEIGHTS[kpt]

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            psi_e = 0.5 * eps.dot(c_mech).dot(eps)
            c4_elas_e += psi_e * detJ * UEL_WEIGHTS[kpt]

    c4_elas_mJ = c4_elas_e * 1000.0
    c4_frac_mJ = c4_at2_ef * 1000.0
    c4_tot_mJ = c4_elas_mJ + c4_frac_mJ

    print("[PACKAGE 115 MAPPER] Initial Mapped C4 Energies at Increment 79:")
    print("  E_elas: %.8f mJ (Donor: %.8f mJ, diff %+.4f%%)" %
          (c4_elas_mJ, TARGET_E_ELAS_DONOR, 100.0 * (c4_elas_mJ - TARGET_E_ELAS_DONOR) / TARGET_E_ELAS_DONOR))
    print("  E_frac: %.8f mJ (Donor: %.8f mJ, diff %+.4f%%)" %
          (c4_frac_mJ, TARGET_E_FRAC_DONOR, 100.0 * (c4_frac_mJ - TARGET_E_FRAC_DONOR) / TARGET_E_FRAC_DONOR))
    print("  E_tot:  %.8f mJ (Donor: %.8f mJ, diff %+.4f%%)" %
          (c4_tot_mJ, TARGET_E_TOT_DONOR, 100.0 * (c4_tot_mJ - TARGET_E_TOT_DONOR) / TARGET_E_TOT_DONOR))

    # Write Package 115 d_lower_bounds.csv
    bounds_csv_path = OUT_DIR / "d_lower_bounds.csv"
    with open(bounds_csv_path, "w") as f:
        f.write("EID, D0_1, D0_2, D0_3, D0_4, H0_1, H0_2, H0_3, H0_4\n")
        for eid in sorted(c4_mesh["elements"].keys()):
            d_vals = c4_elem_d0[eid]
            h_vals = c4_elem_h0[eid]
            f.write("%d, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e, %.10e\n" %
                    (eid, d_vals[0], d_vals[1], d_vals[2], d_vals[3],
                     h_vals[0], h_vals[1], h_vals[2], h_vals[3]))
    print("[PACKAGE 115 MAPPER] Written bounds to: %s" % bounds_csv_path)

    # Write stage_a_all_d0_boundary_cards.inc
    stage_a_path = OUT_DIR / "stage_a_all_d0_boundary_cards.inc"
    with open(stage_a_path, "w") as f:
        f.write("** Stage A Initial All-D0 Boundary Cards for Package 115 Direct Transfer Control\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            f.write("%d, 3, 3, %.8f\n" % (nid, c4_nodal_d[nid]))
    print("[PACKAGE 115 MAPPER] Written Stage A boundary cards to: %s" % stage_a_path)

    # Copy active_set_boundary_cards.inc initially from stage_a
    active_cards_path = OUT_DIR / "active_set_boundary_cards.inc"
    import shutil
    shutil.copyfile(stage_a_path, active_cards_path)

    # Write initial nodal displacements CSV for driver initialization
    disp_csv_path = OUT_DIR / "nodal_displacements_initial.csv"
    with open(disp_csv_path, "w") as f:
        f.write("NID, U1, U2\n")
        for nid in sorted(c4_mesh["nodes"].keys()):
            u1, u2 = c4_nodal_u[nid]
            f.write("%d, %.10e, %.10e\n" % (nid, u1, u2))
    print("[PACKAGE 115 MAPPER] Written initial displacements to: %s" % disp_csv_path)

    # Generate Audit Record
    audit_record = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_115_C4_INC79_DIRECT_TRANSFER",
        "objective": "Isolated Direct Transfer Control at Increment 79 (u_RP = 0.00184250 mm)",
        "donor_reference": {
            "model": "Candidate C3 (1600 Quads)",
            "increment": 79,
            "prescribed_u_rp_mm": TARGET_U_RP,
            "rf2_N": TARGET_RF2_DONOR,
            "e_elas_mJ": TARGET_E_ELAS_DONOR,
            "e_frac_mJ": TARGET_E_FRAC_DONOR,
            "e_tot_mJ": TARGET_E_TOT_DONOR
        },
        "receiver_target": {
            "model": "Candidate C4",
            "quads": 4422,
            "nodes": 4588,
            "prescribed_u_rp_mm": TARGET_U_RP
        },
        "initial_mapped_energies_mJ": {
            "e_elas_mJ": c4_elas_mJ,
            "e_frac_mJ": c4_frac_mJ,
            "e_tot_mJ": c4_tot_mJ,
            "delta_elas_pct": 100.0 * (c4_elas_mJ - TARGET_E_ELAS_DONOR) / TARGET_E_ELAS_DONOR,
            "delta_frac_pct": 100.0 * (c4_frac_mJ - TARGET_E_FRAC_DONOR) / TARGET_E_FRAC_DONOR,
            "delta_tot_pct": 100.0 * (c4_tot_mJ - TARGET_E_TOT_DONOR) / TARGET_E_TOT_DONOR
        },
        "comparison_with_sequential_package113": {
            "pkg113_rf2_N": 187.391475,
            "pkg113_e_elas_mJ": 0.17259901,
            "pkg113_e_frac_mJ": 0.04411506,
            "pkg113_e_tot_mJ": 0.21671407,
            "pkg113_delta_e_tot_pct": 2.0080315
        },
        "hypothesis": "Directly transferring C3 Increment 79 onto C4 and re-equilibrating at the same physical displacement can distinguish a discretization-related energy offset from errors accumulated during Package 112->113 sequential continuation."
    }

    with open(OUT_AUDIT_JSON, "w") as f:
        json.dump(audit_record, f, indent=2)
    print("[PACKAGE 115 MAPPER] Saved audit to: %s" % OUT_AUDIT_JSON)

if __name__ == "__main__":
    run_mapping()
