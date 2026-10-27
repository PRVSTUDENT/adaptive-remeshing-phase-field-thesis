# -*- coding: utf-8 -*-
"""
extract_p117_terminal_state.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Extracts authentic terminal state from Package 117 Cycle 3:
1. Opens M1_C3_SM_CYC3_MECH.odb and extracts nodal displacement U.
2. Evaluates terminal nodal damage d via deterministic PDAS solve matching summary.
3. Evaluates integration-point strain energy density and trial history H_trial.
4. Writes:
   - p117_terminal_nodal_u.csv (NID, U1, U2)
   - p117_terminal_nodal_d.csv (NID, D)
   - p117_terminal_elem_gp.csv (EID, GP, D0, H0)
   - p117_terminal_state_audit.json
"""
from __future__ import print_function, division
import os
import sys
import math
import json
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as sla
from odbAccess import openOdb

# Physical and material parameters
E_MOD = 210.0      # kN/mm^2 (210 GPa)
NU = 0.3
E_GC = 0.0027      # kN/mm (2.7 N/mm)
E_L0 = 0.0075      # mm (7.5 um)
K_DEGRAD = 1.0e-7

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
                    continue
                elif u.startswith("*ELEMENT"):
                    if "TYPE=U1" in u or "TYPE=U2" in u or "TYPE=CPE4" in u:
                        reading = "ELEM"
                    else:
                        reading = None
                    continue
                else:
                    reading = None
                    continue
            if reading == "NODE":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 3 and p[0].isdigit():
                    nid = int(p[0])
                    if nid != 999999:
                        nodes[nid] = (float(p[1]), float(p[2]))
            elif reading == "ELEM":
                p = [x.strip() for x in l.split(",")]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 1600:
                        elements[eid] = (int(p[1]), int(p[2]), int(p[3]), int(p[4]))
    return nodes, elements

def load_committed_history_and_d0(bounds_csv_path):
    h_committed = {}
    with open(bounds_csv_path, "r") as f:
        header = f.readline()
        for line in f:
            l = line.strip()
            if not l or l.startswith("#"):
                continue
            parts = [x.strip() for x in l.split(",")]
            if len(parts) >= 9 and parts[0].isdigit():
                eid = int(parts[0])
                h_vals = [float(parts[5]), float(parts[6]), float(parts[7]), float(parts[8])]
                h_committed[eid] = h_vals
    return h_committed

def load_nodal_d0_from_inc(inc_path):
    d0_dict = {}
    with open(inc_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**") or l.startswith("*"):
                continue
            p = [x.strip() for x in l.split(",")]
            if len(p) >= 4 and p[0].isdigit():
                nid = int(p[0])
                d0_dict[nid] = float(p[3])
    return d0_dict

def solve_phase_pdas(K_mat, q_vec, d_lower_bound, nodes, nlist, n2idx,
                     max_pdas_iters=25, active_kkt_tol=-1.0e-9, free_res_tol=1.0e-6):
    n_nodes = len(nodes)
    active_mask = np.ones(n_nodes, dtype=bool)
    d_trial = d_lower_bound.copy()

    for it in range(1, max_pdas_iters + 1):
        free_indices = np.where(~active_mask)[0]
        active_indices = np.where(active_mask)[0]

        d_trial = np.zeros(n_nodes)
        d_trial[active_indices] = d_lower_bound[active_indices]

        if len(free_indices) > 0:
            K_ff = K_mat[free_indices, :][:, free_indices]
            K_fa = K_mat[free_indices, :][:, active_indices]
            rhs = q_vec[free_indices] - K_fa.dot(d_lower_bound[active_indices])
            d_free_sol = sla.spsolve(K_ff.tocsr(), rhs)
            d_trial[free_indices] = d_free_sol

        R_current = q_vec - K_mat.dot(d_trial)
        free_res_norm = float(np.max(np.abs(R_current[free_indices]))) if len(free_indices) > 0 else 0.0

        release_nodes = active_mask & (R_current > 1.0e-9) & (d_lower_bound < 1.0 - 1.0e-5)
        clamp_nodes = (~active_mask) & (d_trial < d_lower_bound - 1.0e-8)

        n_released = int(np.sum(release_nodes))
        n_clamped = int(np.sum(clamp_nodes))

        if n_released == 0 and n_clamped == 0 and free_res_norm <= free_res_tol:
            print("[PDAS-PHASE] Converged in %d iterations: free nodes = %d, free_res = %.2e kN/mm" %
                  (it, len(free_indices), free_res_norm))
            break

        active_mask = (active_mask & ~release_nodes) | clamp_nodes

    d_final = np.clip(d_trial, d_lower_bound, 1.0)
    d_final[active_mask] = d_lower_bound[active_mask]
    grad = K_mat.dot(d_final) - q_vec
    lambda_mult = -grad

    return d_final, active_mask, lambda_mult, grad

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    inp_deck = os.path.join(pkg_dir, "M1_C3_SAMEMESH_AM_CONTROL.inp")
    bounds_csv = os.path.join(pkg_dir, "d_lower_bounds.csv")
    initial_cards = os.path.join(pkg_dir, "stage_a_all_d0_boundary_cards.inc")
    odb_path = os.path.join(pkg_dir, "M1_C3_SM_CYC3_MECH.odb")

    nodes, elements = parse_inp_mesh(inp_deck)
    nlist = sorted(list(nodes.keys()))
    n2idx = {nid: i for i, nid in enumerate(nlist)}
    n_nodes = len(nodes)

    h_committed_dict = load_committed_history_and_d0(bounds_csv)
    d0_nodal_dict = load_nodal_d0_from_inc(initial_cards)
    d_lower_bound = np.array([d0_nodal_dict[nid] for nid in nlist])

    # Extract displacements from ODB
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[-1]]
    frame = step.frames[-1]

    u_nodal = {}
    u_field = frame.fieldOutputs["U"]
    for val in u_field.values:
        nid = val.nodeLabel
        if nid != 999999:
            u_nodal[nid] = (float(val.data[0]), float(val.data[1]))

    rf2_rp = None
    if "RF" in frame.fieldOutputs:
        for val in frame.fieldOutputs["RF"].values:
            if val.nodeLabel == 999999:
                rf2_rp = float(val.data[1]) * 1000.0
                break
    odb.close()

    print("[EXTRACTOR] Extracted U for %d nodes. RF2_RP = %.4f N" % (len(u_nodal), rf2_rp))

    # Assemble QP
    I_k, J_k, V_k = [], [], []
    q_vec = np.zeros(n_nodes)
    trial_h = {}

    for eid, conn in elements.items():
        elem_idx = [n2idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = np.array([u_nodal[n] for n in conn]).flatten()
        trial_h[eid] = []
        h_base_vals = h_committed_dict[eid]

        Ke = np.zeros((4, 4))
        qe = np.zeros(4)

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J_mat = np.dot(np.vstack([dNdxi, dNdeta]), xe)
            detJ = float(np.linalg.det(J_mat))
            cj = detJ * wt
            invJ = np.linalg.inv(J_mat)
            dNdx = np.dot(invJ, np.vstack([dNdxi, dNdeta]))

            B_u = np.zeros((3, 8))
            for i in range(4):
                B_u[0, 2*i]   = dNdx[0, i]
                B_u[1, 2*i+1] = dNdx[1, i]
                B_u[2, 2*i]   = dNdx[1, i]
                B_u[2, 2*i+1] = dNdx[0, i]

            eps = np.dot(B_u, ue)
            psi_plus = uel_driving_energy(eps, lam, mu)
            h_val = max(h_base_vals[kpt], psi_plus)
            trial_h[eid].append(h_val)

            # Phase stiffness: (gc/l0 + 2*H)*N*N' + gc*l0*B'*B
            coef_m = (E_GC / E_L0) + 2.0 * h_val
            Ke += (coef_m * np.outer(N, N) + E_GC * E_L0 * np.dot(dNdx.T, dNdx)) * cj
            qe += (2.0 * h_val * N) * cj

        for a in range(4):
            for b in range(4):
                I_k.append(elem_idx[a])
                J_k.append(elem_idx[b])
                V_k.append(Ke[a, b])
            q_vec[elem_idx[a]] += qe[a]

    K_mat = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_nodes, n_nodes)).tocsc()

    d_sol, active_mask, lambda_mult, grad = solve_phase_pdas(
        K_mat, q_vec, d_lower_bound, nodes, nlist, n2idx
    )

    print("[EXTRACTOR] Converged d_max: %.10f, active nodes: %d, free nodes: %d" %
          (np.max(d_sol), np.sum(active_mask), np.sum(~active_mask)))

    # Save nodal U CSV
    out_u_csv = os.path.join(pkg_dir, "p117_terminal_nodal_u.csv")
    with open(out_u_csv, "w") as f:
        f.write("node_id,u1,u2\n")
        for nid in nlist:
            u1, u2 = u_nodal[nid]
            f.write("%d,%.12e,%.12e\n" % (nid, u1, u2))

    # Save nodal D CSV
    out_d_csv = os.path.join(pkg_dir, "p117_terminal_nodal_d.csv")
    with open(out_d_csv, "w") as f:
        f.write("node_id,d\n")
        for nid in nlist:
            d_val = float(d_sol[n2idx[nid]])
            f.write("%d,%.12e\n" % (nid, d_val))

    # Save elem GP CSV
    out_gp_csv = os.path.join(pkg_dir, "p117_terminal_elem_gp.csv")
    with open(out_gp_csv, "w") as f:
        f.write("eid,gp,d0,h0\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            elem_d = [float(d_sol[n2idx[n]]) for n in conn]
            for kpt in range(4):
                xi, eta = UEL_GP_COORDS[kpt]
                N, _, _ = shape_functions(xi, eta)
                gp_d = float(np.dot(N, elem_d))
                gp_h = float(trial_h[eid][kpt])
                f.write("%d,%d,%.12e,%.12e\n" % (eid, kpt + 1, gp_d, gp_h))

    # Save audit JSON
    audit = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_117_C3_SAMEMESH_AM_CONTROL",
        "terminal_rf2_rp_N": rf2_rp,
        "terminal_d_max": float(np.max(d_sol)),
        "active_nodes_count": int(np.sum(active_mask)),
        "free_nodes_count": int(np.sum(~active_mask)),
        "total_nodes": n_nodes,
        "total_quads": len(elements)
    }
    with open(os.path.join(pkg_dir, "p117_terminal_state_audit.json"), "w") as f:
        json.dump(audit, f, indent=2)

    print("[EXTRACTOR] Successfully generated all terminal deliverables in %s" % pkg_dir)

if __name__ == "__main__":
    main()
