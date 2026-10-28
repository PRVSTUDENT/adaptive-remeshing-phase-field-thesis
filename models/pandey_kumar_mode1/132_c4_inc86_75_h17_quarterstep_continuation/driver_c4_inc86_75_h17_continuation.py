# -*- coding: utf-8 -*-
"""
Package 132: Candidate C4 Increment-86.75 First Quarter-Step H17 Continuation Driver.
========================================================================
Hypothesis H16 Test Driver:
Tests whether reducing the forward displacement increment between Increment 86
and Increment 87 by 50% (from Delta u = 17.798 nm to Delta u = 8.899 nm, reaching
midpoint target u_RP = 0.001938410627 mm) permits stationary coupled convergence
on the existing C4 mesh (4,422 quads, 4,588 nodes) under the unaccelerated AM/PDAS
algorithm without altering the frozen UEL or convergence thresholds.

Initial State:
  - Authentic stationary C4 Increment-86 checkpoint (Package 127 R1).
  - Initial RP displacement: 0.001929511665 mm.
  - Midpoint target RP displacement: 0.001938410627 mm.
  - Forward displacement increment: 0.000008898962 mm (8.899 nm).

Restoration Interface:
  1. Nodal damage lower bound initialized from stage_a_all_d0_boundary_cards.inc (4,588 nodes).
  2. Element driving history and damage lower bounds loaded by UEXTERNALDB at LOP=0
     from d_lower_bounds.csv (4,423 lines, 4,422 elements x 4 GPs = 17,688 GP history values).
  3. Invariant history commitment: H_trial^(k) = max(H_committed, psi_plus(u_trial^(k))).
  4. Lower bound enforcement: d >= d_committed (zero damage healing).
  5. Stationarity criteria: Delta d_max <= 1.0e-3, |Delta RF2| <= 0.1 N.
  6. Acceptance criteria:
     - Healing violations == 0
     - Free residual <= 1.0e-6 kN/mm
     - Min active multiplier >= -1.0e-9 kN/mm
     - Note: Midpoint cross-mesh parity against Stage C1-1 donor Increment 87 is not directly
       applicable because this is a diagnostic intermediate half-step load state.

Output:
  - c4_inc86_75_h17_continuation_summary.json
"""

from __future__ import print_function, division
import os
import sys
import math
import time
import json
import shutil
import subprocess
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# Physical and material parameters (frozen benchmark)
E_MOD = 210.0      # kN/mm^2 (210 GPa)
NU = 0.3
E_GC = 0.0027      # kN/mm (2.7 N/mm)
E_L0 = 0.0075      # mm (7.5 um, strictly consistent with UEL property card)
K_DEGRAD = 1.0e-6

# Plane strain elasticity tensor
lam = E_MOD * NU / ((1.0 + NU) * (1.0 - 2.0 * NU))
mu = E_MOD / (2.0 * (1.0 + NU))
c11_0 = lam + 2.0 * mu
c12_0 = lam
c33_0 = mu

C0 = np.array([
    [c11_0, c12_0, 0.0],
    [c12_0, c11_0, 0.0],
    [0.0,   0.0,   c33_0]
])

A_GAUSS = 0.577350269189626
UEL_GP_COORDS = [
    (-A_GAUSS, -A_GAUSS),
    ( A_GAUSS, -A_GAUSS),
    ( A_GAUSS,  A_GAUSS),
    (-A_GAUSS,  A_GAUSS),
]
UEL_WEIGHTS = [1.0, 1.0, 1.0, 1.0]

def is_finite(val):
    return not (math.isinf(val) or math.isnan(val))

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
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
            elif reading == "ELEMENT":
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    c = [int(p) for p in parts[1:5]]
                    elements[eid] = c
    return nodes, elements

def load_committed_history_and_d0(bounds_csv_path):
    h_committed = {}
    with open(bounds_csv_path, "r") as f:
        header_line = f.readline().strip()
        header = [h.strip() for h in header_line.split(",")]
        h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            eid = int(parts[0])
            h_vals = [float(parts[i]) for i in h_idx]
            h_committed[eid] = h_vals
    return h_committed

def load_nodal_d0_from_inc(inc_path):
    d0_dict = {}
    with open(inc_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            p = [x.strip() for x in l.split(",")]
            if len(p) >= 4 and p[0].isdigit():
                nid = int(p[0])
                d0_dict[nid] = float(p[3])
    return d0_dict

def run_abaqus_solve(job_name, inp_deck, user_sub):
    cmd = "abaqus job=%s input=%s user=%s cpus=1 interactive" % (job_name, inp_deck, user_sub)
    print("[H17-QUARTERSTEP-DRIVER] Executing Abaqus command: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    return retcode

def extract_mechanical_results(odb_path):
    from odbAccess import openOdb
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB not found: %s" % odb_path)

    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[-1]]
    frame = step.frames[-1]

    u_nodal = {}
    if "U" in frame.fieldOutputs:
        u_field = frame.fieldOutputs["U"]
        for val in u_field.values:
            nid = val.nodeLabel
            if nid != 999999:
                u_nodal[nid] = (float(val.data[0]), float(val.data[1]))

    rf2_rp = None
    if "RF" in frame.fieldOutputs:
        rf_field = frame.fieldOutputs["RF"]
        for val in rf_field.values:
            if val.nodeLabel == 999999:
                rf2_rp = float(val.data[1]) * 1000.0  # Convert kN to N
                break

    odb.close()
    return u_nodal, rf2_rp

def assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_committed_dict):
    n_nodes = len(nodes)
    lam_val = lam
    mu_val = mu
    gc_val = E_GC
    l0_val = E_L0

    I_k, J_k, V_k = [], [], []
    q_vec = np.zeros(n_nodes)
    trial_driving_energy = {}

    for eid, conn in elements.items():
        elem_idx = [n2idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = np.array([u_nodal[n] for n in conn]).flatten()
        trial_driving_energy[eid] = []
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

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            pos_m = uel_driving_energy(eps, lam_val, mu_val)
            h_trial_k = max(h_base_vals[kpt], pos_m)
            trial_driving_energy[eid].append(h_trial_k)

            fac_k = (gc_val / l0_val) + 2.0 * h_trial_k
            fac_grad = gc_val * l0_val

            N_col = N.reshape(-1, 1)
            Ke += cj * (fac_k * np.dot(N_col, N_col.T) + fac_grad * np.dot(dNdx.T, dNdx))
            qe += cj * (2.0 * h_trial_k * N)

        for a in range(4):
            q_vec[elem_idx[a]] += qe[a]
            for b in range(4):
                I_k.append(elem_idx[a])
                J_k.append(elem_idx[b])
                V_k.append(Ke[a, b])

    K_mat = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_nodes, n_nodes)).tocsr()
    return K_mat, q_vec, trial_driving_energy

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
            d_free_sol = spla.spsolve(K_ff, rhs)
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

def write_active_set_cards(out_path, nlist, active_mask, d_prescribed):
    with open(out_path, "w") as f:
        f.write("** Updated Active Set Boundary Cards for Abaqus\n")
        f.write("** Format: node_id, 3, 3, d_value\n")
        for nid in nlist:
            f.write("%d, 3, 3, %.8f\n" % (nid, d_prescribed[nid]))

def compute_energies_and_residuals(nodes, elements, nlist, n2idx, u_nodal, d_nodal, h_dict):
    c4_at2_ef = 0.0
    c4_elas_e = 0.0
    gc_val = E_GC
    l0_val = E_L0

    for eid, conn in elements.items():
        xe = np.array([nodes[n] for n in conn])
        ue = np.array([u_nodal[n] for n in conn]).flatten()
        de = np.array([d_nodal[n2idx[n]] for n in conn])

        for kpt in range(4):
            xi, eta = UEL_GP_COORDS[kpt]
            wt = UEL_WEIGHTS[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J_mat = np.dot(np.vstack([dNdxi, dNdeta]), xe)
            detJ = float(np.linalg.det(J_mat))
            cj = detJ * wt
            invJ = np.linalg.inv(J_mat)
            dNdx = np.dot(invJ, np.vstack([dNdxi, dNdeta]))

            d_k = float(np.dot(N, de))
            grad_d_k = np.dot(dNdx, de)
            grad_d_sq = float(np.dot(grad_d_k, grad_d_k))

            gamma_d = 0.5 * (d_k**2 / l0_val + l0_val * grad_d_sq)
            psi_frac = gc_val * gamma_d
            c4_at2_ef += psi_frac * cj

            g_d = (1.0 - d_k)**2 + K_DEGRAD
            c_mech = g_d * C0

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
            eps = B.dot(ue)
            psi_e = 0.5 * eps.dot(c_mech).dot(eps)
            c4_elas_e += psi_e * cj

    e_tot = c4_elas_e + c4_at2_ef
    return c4_elas_e * 1000.0, c4_at2_ef * 1000.0, e_tot * 1000.0

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    inp_deck = os.path.join(pkg_dir, "M1_C4_INC86_75_H17_QUARTERSTEP_CONTINUATION.inp")
    user_sub = os.path.join(pkg_dir, "f42_unified_12dof_active_set_uel.for")
    bounds_csv = os.path.join(pkg_dir, "d_lower_bounds.csv")
    active_cards = os.path.join(pkg_dir, "active_set_boundary_cards.inc")
    initial_cards = os.path.join(pkg_dir, "stage_a_all_d0_boundary_cards.inc")
    summary_path = os.path.join(pkg_dir, "c4_inc86_75_h17_continuation_summary.json")

    print("[H17-QUARTERSTEP-DRIVER] Parsing mesh from: %s" % inp_deck)
    nodes, elements = parse_inp_mesh(inp_deck)
    nlist = sorted(list(nodes.keys()))
    n2idx = {nid: i for i, nid in enumerate(nlist)}
    n_nodes = len(nodes)
    print("[H17-QUARTERSTEP-DRIVER] Loaded mesh: %d physical nodes, %d quad elements" % (n_nodes, len(elements)))

    print("[H17-QUARTERSTEP-DRIVER] Loading committed step history H_committed from: %s" % bounds_csv)
    h_committed_dict = load_committed_history_and_d0(bounds_csv)
    d0_nodal_dict = load_nodal_d0_from_inc(initial_cards)
    d_lower_bound = np.array([d0_nodal_dict[nid] for nid in nlist])

    shutil.copyfile(initial_cards, active_cards)

    d_current = d_lower_bound.copy()
    history_log = []

    # Midpoint configuration
    u_target_inc87_mm = 0.001942860108
    u_init_inc86_5_mm = 0.001938410627
    delta_u_target_mm = 0.000004449481

    max_am_cycles = 25           # Original 25-cycle cap to test half-step contraction
    STATIONARITY_TOL_DELTA_D = 1.0e-3
    STATIONARITY_TOL_DELTA_RF2_N = 0.1
    FREE_RESIDUAL_TOL = 1.0e-6
    ACTIVE_KKT_TOL = -1.0e-9

    prev_d = d_current.copy()
    prev_rf2 = None
    converged_status = "ITERATION_CAP_REACHED"
    latest_h_trial = None
    u_nodal_latest = {}
    d_next_latest = None

    for cycle in range(1, max_am_cycles + 1):
        print("\n" + "=" * 80)
        print("[H17-QUARTERSTEP-DRIVER] STARTING RECONSTRUCTION AM CYCLE %d / %d" % (cycle, max_am_cycles))
        print("=" * 80)

        d_prescribed_dict = {nid: d_current[n2idx[nid]] for nid in nlist}
        write_active_set_cards(active_cards, nlist, np.ones(n_nodes, dtype=bool), d_prescribed_dict)

        job_name = "M1_C4_INC86_75_H17_CYC%d_MECH" % cycle
        retcode = run_abaqus_solve(job_name, inp_deck, user_sub)
        if retcode != 0:
            print("[H17-QUARTERSTEP-DRIVER] Abaqus mechanical solve failed in cycle %d! Retcode: %d" % (cycle, retcode))
            converged_status = "MECHANICAL_SOLVE_FAILED"
            break

        odb_path = job_name + ".odb"
        u_nodal, rf2_rp = extract_mechanical_results(odb_path)
        u_nodal_latest = u_nodal

        delta_rf2_prev = abs(rf2_rp - prev_rf2) if prev_rf2 is not None else 999.0

        print("[H17-QUARTERSTEP-DRIVER] Cycle %d Mechanical Solve: RF2 = %.4f N, Delta RF2 = %.4f N" %
              (cycle, rf2_rp, delta_rf2_prev))

        K_mat, q_vec, latest_h_trial = assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_committed_dict)

        d_next, active_mask, lambda_mult, grad = solve_phase_pdas(
            K_mat, q_vec, d_lower_bound, nodes, nlist, n2idx,
            max_pdas_iters=25, active_kkt_tol=ACTIVE_KKT_TOL, free_res_tol=FREE_RESIDUAL_TOL
        )
        d_next_latest = d_next

        healing_violations = np.sum(d_next < d_lower_bound - 1.0e-8)
        max_delta_d = float(np.max(np.abs(d_next - prev_d)))
        free_indices = np.where(~active_mask)[0]
        free_res_norm = float(np.max(np.abs(grad[free_indices]))) if len(free_indices) > 0 else 0.0
        min_lambda = float(np.min(grad[active_mask])) if np.sum(active_mask) > 0 else 0.0

        e_elas, e_frac, e_tot = compute_energies_and_residuals(
            nodes, elements, nlist, n2idx, u_nodal, d_next, latest_h_trial
        )

        cycle_stat = {
            "cycle": cycle,
            "job_name": job_name,
            "rf2_rp_N": rf2_rp,
            "delta_rf2_prev_cycle_N": delta_rf2_prev,
            "d_max": float(np.max(d_next)),
            "max_delta_d": max_delta_d,
            "free_nodes": int(len(free_indices)),
            "active_nodes": int(np.sum(active_mask)),
            "free_res_max_kN_mm": free_res_norm,
            "min_lambda_kN_mm": min_lambda,
            "healing_violations": int(healing_violations),
            "e_elas_mJ": e_elas,
            "e_frac_mJ": e_frac,
            "e_tot_mJ": e_tot
        }
        history_log.append(cycle_stat)

        print("[H17-QUARTERSTEP-DRIVER] Cycle %d Results: d_max = %.5f, Delta d = %.6f, Free Nodes = %d, E_tot = %.6f mJ" %
              (cycle, cycle_stat["d_max"], max_delta_d, cycle_stat["free_nodes"], e_tot))

        is_stationary = (max_delta_d <= STATIONARITY_TOL_DELTA_D and delta_rf2_prev <= STATIONARITY_TOL_DELTA_RF2_N)
        if cycle >= 2 and is_stationary:
            print("\n" + "*" * 80)
            print("[H17-QUARTERSTEP-DRIVER] EQUILIBRIUM CONFIRMED AT CYCLE %d!" % cycle)
            print("[H17-QUARTERSTEP-DRIVER] Delta d = %.6f <= %.1e, Delta RF2 = %.4f N <= %.1f N" %
                  (max_delta_d, STATIONARITY_TOL_DELTA_D, delta_rf2_prev, STATIONARITY_TOL_DELTA_RF2_N))
            print("*" * 80)
            converged_status = "CONVERGED_STATIONARY_STATE"
            break

        prev_d = d_next.copy()
        d_current = d_next.copy()
        prev_rf2 = rf2_rp

    final_entry = history_log[-1] if history_log else {}

    h17_pass = (
        converged_status == "CONVERGED_STATIONARY_STATE" and
        final_entry.get("healing_violations", 1) == 0 and
        final_entry.get("free_res_max_kN_mm", 1.0) <= 1.0e-6 and
        final_entry.get("min_lambda_kN_mm", -1.0) >= -1.0e-9
    )

    summary_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_132_C4_INC86_75_H17_QUARTERSTEP_CONTINUATION",
        "hypothesis": "H17_QUARTERSTEP_AM_CONTINUATION",
        "status": converged_status,
        "h17_verdict": "H17_PASSED_QUARTERSTEP" if h17_pass else "H17_FAILED_NONSTATIONARY",
        "cycles_completed": len(history_log),
        "initial_u_rp_mm": u_init_inc86_5_mm,
        "target_u_rp_mm": u_target_inc87_mm,
        "forward_increment_mm": delta_u_target_mm,
        "history": history_log,
        "final_state": final_entry
    }

    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    print("\n[H17-QUARTERSTEP-DRIVER] Summary saved to: %s" % summary_path)

if __name__ == "__main__":
    main()
