# -*- coding: utf-8 -*-
"""
extract_and_audit_am_cycles.py
Extract displacement fields from cycles 1, 3, 5, 10, 15 and compute:
1. True driving energy psi+(u^(k)) at each GP
2. Comparison against H_donor: pos_m vs H_donor vs H_accumulated
3. Mechanical residual and phase residual
"""

from __future__ import print_function, division
import os
import sys
import json
import numpy as np
from odbAccess import openOdb

RUN_DIR = "/scratch9/pr21vyci/runs/mode1_c4_am_dynamic_continuation"
E_MOD = 210.0
NU = 0.3
E_GC = 0.0027
E_L0 = 0.0075
K_DEGRAD = 1.0e-6

lam = E_MOD * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
mu = E_MOD / (2.0 * (1.0 + NU))

A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

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

def uel_driving_energy(eps, lam_val, mu_val):
    e11 = eps[0]
    e22 = eps[1]
    e12 = 0.5 * eps[2]
    tr_e = e11 + e22
    e_pos = max(0.0, tr_e)
    pos_m = 0.5 * lam_val * (e_pos**2) + mu_val * (e11**2 + e22**2 + 2.0 * (e12**2))
    return float(pos_m)

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    reading = None
    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT"):
                    reading = "ELEMENT"
                elif u.startswith("*"):
                    reading = None
                continue
            if reading == "NODE":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    if nid != 999999:
                        nodes[nid] = (float(parts[1]), float(parts[2]))
            elif reading == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    elements[eid] = [int(p) for p in parts[1:5]]
    return nodes, elements

def load_donor_history(csv_path):
    h_dict = {}
    with open(csv_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("EID") or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 9:
                try:
                    eid = int(parts[0])
                    h_vals = [float(parts[5]), float(parts[6]), float(parts[7]), float(parts[8])]
                    h_dict[eid] = h_vals
                except ValueError:
                    continue
    return h_dict

def extract_u_nodal(odb_path):
    odb = openOdb(odb_path)
    step = odb.steps[odb.steps.keys()[0]]
    last_frame = step.frames[-1]
    u_field = last_frame.fieldOutputs["U"]
    u_nodal = {}
    u_rp = None
    for val in u_field.values:
        nid = val.nodeLabel
        u1 = float(val.data[0])
        u2 = float(val.data[1])
        if nid == 999999:
            u_rp = (u1, u2)
        else:
            u_nodal[nid] = (u1, u2)
    odb.close()
    return u_nodal, u_rp

def main():
    inp_path = os.path.join(RUN_DIR, "M1_C4_AM_CONTINUATION.inp")
    h_csv_path = os.path.join(RUN_DIR, "d_lower_bounds.csv")
    nodes, elements = parse_inp_mesh(inp_path)
    donor_h = load_donor_history(h_csv_path)

    cycles_to_audit = [1, 2, 3, 5, 7, 10, 15]
    results = {}

    for cyc in cycles_to_audit:
        odb_path = os.path.join(RUN_DIR, "M1_C4_AM_CYC%d_MECH.odb" % cyc)
        if not os.path.exists(odb_path):
            print("ODB missing: %s" % odb_path)
            continue
        u_nodal, u_rp = extract_u_nodal(odb_path)

        # Compute pos_m across all elements and GPs
        pos_m_vals = []
        pos_m_exceeding_donor = 0
        total_gps = len(elements) * 4
        max_pos_m = 0.0
        max_ratio = 0.0

        for eid, conn in elements.items():
            xe = np.array([nodes[n] for n in conn])
            ue = np.zeros(8)
            for a in range(4):
                u_pt = u_nodal.get(conn[a], (0.0, 0.0))
                ue[2*a]   = u_pt[0]
                ue[2*a+1] = u_pt[1]

            for kpt in range(4):
                xi, eta = UEL_GP_COORDS[kpt]
                wt = UEL_WEIGHTS[kpt]
                N, dNdxi, dNdeta = shape_functions(xi, eta)
                J_mat = np.zeros((2, 2))
                for i in range(4):
                    J_mat[0, 0] += dNdxi[i] * xe[i, 0]
                    J_mat[0, 1] += dNdxi[i] * xe[i, 1]
                    J_mat[1, 0] += dNdeta[i] * xe[i, 0]
                    J_mat[1, 1] += dNdeta[i] * xe[i, 1]
                detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
                invJ = np.array([[ J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0],  J_mat[0, 0]]]) / detJ
                dNdx = np.zeros((2, 4))
                for i in range(4):
                    dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
                    dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]
                B = np.zeros((3, 8))
                for i in range(4):
                    B[0, 2*i]   = dNdx[0, i]
                    B[1, 2*i+1] = dNdx[1, i]
                    B[2, 2*i]   = dNdx[1, i]
                    B[2, 2*i+1] = dNdx[0, i]
                eps = B.dot(ue)
                pm = uel_driving_energy(eps, lam, mu)
                pos_m_vals.append(pm)
                if pm > max_pos_m:
                    max_pos_m = pm
                dh = donor_h.get(eid, [0.0]*4)[kpt]
                if pm > dh + 1e-8:
                    pos_m_exceeding_donor += 1
                    if dh > 1e-8:
                        r = pm / dh
                        if r > max_ratio:
                            max_ratio = r

        results[cyc] = {
            "cycle": cyc,
            "u_rp": u_rp,
            "max_pos_m_MPa": max_pos_m * 1000.0,
            "mean_pos_m_MPa": np.mean(pos_m_vals) * 1000.0,
            "gps_exceeding_donor_h": pos_m_exceeding_donor,
            "total_gps": total_gps,
            "pct_gps_exceeding": pos_m_exceeding_donor / float(total_gps) * 100.0,
            "max_ratio_pos_m_over_donor_h": max_ratio
        }
        print("Cycle %2d: u_rp=%s, max_psi+=%.2f MPa, GPs exceeding H_donor: %d / %d (%.2f%%)" %
              (cyc, str(u_rp), max_pos_m * 1000.0, pos_m_exceeding_donor, total_gps, pos_m_exceeding_donor / float(total_gps) * 100.0))

    out_json = os.path.join(RUN_DIR, "c4_am_driving_energy_audit.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
    print("Saved audit to: %s" % out_json)

if __name__ == "__main__":
    main()
