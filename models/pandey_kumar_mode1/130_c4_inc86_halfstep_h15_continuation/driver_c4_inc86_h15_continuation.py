# -*- coding: utf-8 -*-
"""
Package 130: Candidate C4 Increment-86 Half-Step H15 Continuation Driver.
========================================================================
Hypothesis H15 Test Driver:
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
  - c4_inc86_h15_continuation_summary.json
"""

from __future__ import print_function, division
import os
import sys
import json
import math
import subprocess
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

# -----------------------------------------------------------------------------
# Material and Model Constants (bit-exact to Pandey-Kumar Mode-I specifications)
# -----------------------------------------------------------------------------
E_MOD = 210.0          # kN/mm^2 (210 GPa)
NU_POS = 0.3           # Poisson's ratio
E_GC = 0.0027          # kN/mm (2.7 N/mm)
E_L0 = 0.015           # mm (15.0 um)

# Plane strain Lamé constants
lam = (E_MOD * NU_POS) / ((1.0 + NU_POS) * (1.0 - 2.0 * NU_POS))
mu = E_MOD / (2.0 * (1.0 + NU_POS))

# Quadrature: standard 2x2 Gauss-Legendre
GP_COORDS = [-1.0 / math.sqrt(3.0), 1.0 / math.sqrt(3.0)]
GP_WEIGHTS = [1.0, 1.0]

def is_finite(val):
    return not (math.isnan(val) or math.isinf(val))

def get_shape_functions(xi, eta):
    N = np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ])
    dNdxi = np.array([
        [-0.25 * (1.0 - eta), 0.25 * (1.0 - eta), 0.25 * (1.0 + eta), -0.25 * (1.0 + eta)],
        [-0.25 * (1.0 - xi), -0.25 * (1.0 + xi), 0.25 * (1.0 + xi), 0.25 * (1.0 - xi)]
    ])
    return N, dNdxi

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    reading_nodes = False
    reading_elements = False

    with open(inp_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue

            if l.startswith("*"):
                l_upper = l.upper()
                reading_nodes = False
                reading_elements = False
                if l_upper.startswith("*NODE") and not l_upper.startswith("*NODE OUTPUT") and not l_upper.startswith("*NODE PRINT"):
                    reading_nodes = True
                    continue
                elif l_upper.startswith("*ELEMENT") and "TYPE=UEL" in l_upper:
                    reading_elements = True
                    continue
                else:
                    continue

            if reading_nodes:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 3:
                    nid = int(parts[0])
                    if nid != 999999:  # Skip reference point
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
            elif reading_elements:
                parts = [p.strip() for p in l.split(",")]
                if len(parts) >= 5:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:5]]
                    elements[eid] = conn

    return nodes, elements

def load_committed_history_and_d0(csv_path):
    h_committed = {}
    with open(csv_path, "r") as f:
        for line in f:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) >= 6:
                try:
                    eid = int(parts[0])
                    gp_h = [float(parts[2]), float(parts[3]), float(parts[4]), float(parts[5])]
                    h_committed[eid] = gp_h
                except ValueError:
                    continue
    return h_committed

def load_nodal_d0_from_inc(inc_path):
    d0_nodal = {}
    with open(inc_path, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**") or l.startswith("*"):
                continue
            parts = [p.strip() for p in l.split(",")]
            if len(parts) >= 4:
                try:
                    nid = int(parts[0])
                    d_val = float(parts[3])
                    d0_nodal[nid] = d_val
                except ValueError:
                    continue
    return d0_nodal

def write_active_set_cards(inc_path, nlist, is_active, d_prescribed):
    with open(inc_path, "w") as f:
        f.write("** Active-set phase-field Dirichlet cards for Abaqus\n")
        f.write("*Boundary, op=NEW\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_RP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.001938410627\n")
        for nid in nlist:
            if is_active[nid]:
                f.write("%d, 7, 7, %.12e\n" % (nid, d_prescribed[nid]))

def run_abaqus_solve(job_name, inp_deck, user_sub):
    cmd = "abaqus job=%s input=%s user=%s cpus=1 interactive" % (job_name, inp_deck, user_sub)
    print("[H15-HALFSTEP-DRIVER] Executing Abaqus command: %s" % cmd)
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
                rf2_rp = float(val.data[1]) * 1000.0  # kN to N
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
        coords = np.array([nodes[nid] for nid in conn])
        u_elem = np.array([u_nodal.get(nid, (0.0, 0.0)) for nid in conn])
        h_committed_elem = h_committed_dict.get(eid, [0.0, 0.0, 0.0, 0.0])

        Ke = np.zeros((4, 4))
        qe = np.zeros(4)
        gp_h_trial = []

        gp_idx = 0
        for xi in GP_COORDS:
            for eta in GP_COORDS:
                N, dNdxi = get_shape_functions(xi, eta)
                J = np.dot(dNdxi, coords)
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                dNdx = np.dot(invJ, dNdxi)

                grad_u = np.dot(dNdx, u_elem)
                eps = np.zeros((3, 3))
                eps[0, 0] = grad_u[0, 0]
                eps[1, 1] = grad_u[1, 1]
                eps[0, 1] = 0.5 * (grad_u[0, 1] + grad_u[1, 0])
                eps[1, 0] = eps[0, 1]

                tr_eps = eps[0, 0] + eps[1, 1]
                tr_eps_plus = max(0.0, tr_eps)
                dev_eps = eps.copy()
                dev_eps[0, 0] -= tr_eps / 3.0
                dev_eps[1, 1] -= tr_eps / 3.0
                dev_eps[2, 2] -= tr_eps / 3.0
                dev_sq = np.sum(dev_eps * dev_eps)

                psi_plus = 0.5 * lam_val * (tr_eps_plus ** 2) + mu_val * dev_sq
                H_k = max(h_committed_elem[gp_idx], psi_plus)
                gp_h_trial.append(H_k)

                w_detJ = 1.0 * detJ
                B_grad = dNdx
                K_grad = (gc_val * l0_val) * np.dot(B_grad.T, B_grad)
                K_mass = ((gc_val / l0_val) + 2.0 * H_k) * np.outer(N, N)

                Ke += (K_grad + K_mass) * w_detJ
                qe -= (2.0 * H_k * N) * w_detJ

                gp_idx += 1

        trial_driving_energy[eid] = gp_h_trial

        for a in range(4):
            i_global = n2idx[conn[a]]
            q_vec[i_global] += qe[a]
            for b in range(4):
                j_global = n2idx[conn[b]]
                I_k.append(i_global)
                J_k.append(j_global)
                V_k.append(Ke[a, b])

    K_mat = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_nodes, n_nodes)).tocsr()
    return K_mat, q_vec, trial_driving_energy

def solve_pdas_phase_field(K_mat, q_vec, d_lower, max_pdas_iters=30):
    n_nodes = len(d_lower)
    is_active = np.zeros(n_nodes, dtype=bool)
    d_sol = d_lower.copy()

    for it in range(max_pdas_iters):
        active_set = is_active
        free_set = ~active_set
        free_indices = np.where(free_set)[0]
        active_indices = np.where(active_set)[0]

        d_new = np.zeros(n_nodes)
        d_new[active_indices] = d_lower[active_indices]

        if len(free_indices) > 0:
            K_FF = K_mat[free_indices, :][:, free_indices]
            K_FA = K_mat[free_indices, :][:, active_indices]
            rhs_F = -q_vec[free_indices] - K_FA.dot(d_lower[active_indices])
            d_F = spla.spsolve(K_FF, rhs_F)
            d_new[free_indices] = d_F

        res_full = K_mat.dot(d_new) + q_vec
        lambda_A = -res_full[active_indices]

        new_active = np.zeros(n_nodes, dtype=bool)
        for i in range(n_nodes):
            if is_active[i]:
                if lambda_A[np.where(active_indices == i)[0][0]] < 0.0:
                    new_active[i] = False
                else:
                    new_active[i] = True
            else:
                if d_new[i] < d_lower[i]:
                    new_active[i] = True
                else:
                    new_active[i] = False

        if np.array_equal(new_active, is_active):
            return d_new, is_active, res_full

        is_active = new_active

    return d_new, is_active, res_full

def compute_energies(nodes, elements, n2idx, u_nodal, d_field):
    lam_val = lam
    mu_val = mu
    gc_val = E_GC
    l0_val = E_L0

    e_elas_total = 0.0
    e_frac_total = 0.0

    for eid, conn in elements.items():
        coords = np.array([nodes[nid] for nid in conn])
        u_elem = np.array([u_nodal.get(nid, (0.0, 0.0)) for nid in conn])
        d_elem = np.array([d_field[n2idx[nid]] for nid in conn])

        for xi in GP_COORDS:
            for eta in GP_COORDS:
                N, dNdxi = get_shape_functions(xi, eta)
                J = np.dot(dNdxi, coords)
                detJ = np.linalg.det(J)
                invJ = np.linalg.inv(J)
                dNdx = np.dot(invJ, dNdxi)

                grad_u = np.dot(dNdx, u_elem)
                eps = np.zeros((3, 3))
                eps[0, 0] = grad_u[0, 0]
                eps[1, 1] = grad_u[1, 1]
                eps[0, 1] = 0.5 * (grad_u[0, 1] + grad_u[1, 0])
                eps[1, 0] = eps[0, 1]

                tr_eps = eps[0, 0] + eps[1, 1]
                tr_eps_plus = max(0.0, tr_eps)
                tr_eps_minus = min(0.0, tr_eps)
                dev_eps = eps.copy()
                dev_eps[0, 0] -= tr_eps / 3.0
                dev_eps[1, 1] -= tr_eps / 3.0
                dev_eps[2, 2] -= tr_eps / 3.0
                dev_sq = np.sum(dev_eps * dev_eps)

                psi_plus = 0.5 * lam_val * (tr_eps_plus ** 2) + mu_val * dev_sq
                psi_minus = 0.5 * lam_val * (tr_eps_minus ** 2)

                d_val = np.dot(N, d_elem)
                d_val = min(1.0, max(0.0, d_val))
                grad_d = np.dot(dNdx, d_elem)
                grad_d_sq = np.dot(grad_d, grad_d)

                g_d = ((1.0 - d_val) ** 2) + 1.0e-7
                psi_total = g_d * psi_plus + psi_minus
                gamma_d = 0.5 * ((d_val ** 2) / l0_val + l0_val * grad_d_sq)

                w_detJ = 1.0 * detJ
                e_elas_total += psi_total * w_detJ
                e_frac_total += (gc_val * gamma_d) * w_detJ

    return e_elas_total, e_frac_total

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    inp_deck = os.path.join(pkg_dir, "M1_C4_INC86_H15_CONTINUATION.inp")
    user_sub = os.path.join(pkg_dir, "f42_unified_12dof_active_set_uel.for")
    bounds_csv = os.path.join(pkg_dir, "d_lower_bounds.csv")
    active_cards = os.path.join(pkg_dir, "active_set_boundary_cards.inc")
    initial_cards = os.path.join(pkg_dir, "stage_a_all_d0_boundary_cards.inc")
    summary_path = os.path.join(pkg_dir, "c4_inc86_h15_continuation_summary.json")

    print("[H15-HALFSTEP-DRIVER] Parsing mesh from: %s" % inp_deck)
    nodes, elements = parse_inp_mesh(inp_deck)
    nlist = sorted(list(nodes.keys()))
    n2idx = {nid: i for i, nid in enumerate(nlist)}
    n_nodes = len(nodes)
    print("[H15-HALFSTEP-DRIVER] Loaded mesh: %d physical nodes, %d quad elements" % (n_nodes, len(elements)))

    print("[H15-HALFSTEP-DRIVER] Loading committed step history H_committed from: %s" % bounds_csv)
    h_committed_dict = load_committed_history_and_d0(bounds_csv)
    d0_nodal_dict = load_nodal_d0_from_inc(initial_cards)
    d_lower_bound = np.array([d0_nodal_dict[nid] for nid in nlist])
    d_current = d_lower_bound.copy()

    prev_rf2 = None
    d_next_latest = None
    u_nodal_latest = None
    history_log = []

    # Midpoint configuration
    u_target_midpoint_mm = 0.001938410627
    u_init_inc86_mm = 0.001929511665
    delta_u_target_mm = 0.000008898962

    max_am_cycles = 25           # Original 25-cycle cap to test half-step contraction
    STATIONARITY_TOL_DELTA_D = 1.0e-3
    STATIONARITY_TOL_DELTA_RF2_N = 0.1
    FREE_RESIDUAL_TOL = 1.0e-6
    MIN_LAMBDA_TOL = -1.0e-9

    converged_status = "ITERATION_CAP_REACHED"

    for cycle in range(1, max_am_cycles + 1):
        print("\n" + "=" * 80)
        print("[H15-HALFSTEP-DRIVER] STARTING RECONSTRUCTION AM CYCLE %d / %d" % (cycle, max_am_cycles))
        print("=" * 80)

        d_prescribed_dict = {nid: d_current[n2idx[nid]] for nid in nlist}
        write_active_set_cards(active_cards, nlist, np.ones(n_nodes, dtype=bool), d_prescribed_dict)

        job_name = "M1_C4_INC86_H15_CYC%d_MECH" % cycle
        retcode = run_abaqus_solve(job_name, inp_deck, user_sub)
        if retcode != 0:
            print("[H15-HALFSTEP-DRIVER] Abaqus mechanical solve failed in cycle %d! Retcode: %d" % (cycle, retcode))
            converged_status = "MECHANICAL_SOLVE_FAILED"
            break

        odb_path = job_name + ".odb"
        u_nodal, rf2_rp = extract_mechanical_results(odb_path)
        u_nodal_latest = u_nodal

        delta_rf2_prev = abs(rf2_rp - prev_rf2) if prev_rf2 is not None else 999.0
        print("[H15-HALFSTEP-DRIVER] Cycle %d Mechanical Solve: RF2 = %.4f N, Delta RF2 = %.4f N" %
              (cycle, rf2_rp, delta_rf2_prev))

        K_mat, q_vec, latest_h_trial = assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_committed_dict)
        d_next, is_active, res_full = solve_pdas_phase_field(K_mat, q_vec, d_lower_bound)
        d_next_latest = d_next

        healing_violations = np.sum(d_next < (d_lower_bound - 1.0e-8))
        max_delta_d = float(np.max(np.abs(d_next - d_current)))
        active_count = int(np.sum(is_active))
        free_count = n_nodes - active_count

        free_indices = np.where(~is_active)[0]
        free_res_max = float(np.max(np.abs(res_full[free_indices]))) if len(free_indices) > 0 else 0.0
        active_indices = np.where(is_active)[0]
        lambda_A = -res_full[active_indices] if len(active_indices) > 0 else np.array([0.0])
        min_lambda = float(np.min(lambda_A)) if len(active_indices) > 0 else 0.0

        e_elas, e_frac = compute_energies(nodes, elements, n2idx, u_nodal, d_next)
        e_tot = e_elas + e_frac

        cycle_stat = {
            "cycle": cycle,
            "job_name": job_name,
            "rf2_rp_N": rf2_rp,
            "delta_rf2_prev_cycle_N": delta_rf2_prev,
            "max_delta_d": max_delta_d,
            "d_max": float(np.max(d_next)),
            "active_nodes": active_count,
            "free_nodes": free_count,
            "healing_violations": int(healing_violations),
            "free_res_max_kN_mm": free_res_max,
            "min_lambda_kN_mm": min_lambda,
            "e_elas_mJ": e_elas,
            "e_frac_mJ": e_frac,
            "e_tot_mJ": e_tot
        }
        history_log.append(cycle_stat)

        print("[H15-HALFSTEP-DRIVER] Cycle %d Results: d_max = %.5f, Delta d = %.6f, Free Nodes = %d, E_tot = %.6f mJ" %
              (cycle, cycle_stat["d_max"], max_delta_d, cycle_stat["free_nodes"], e_tot))

        is_stationary = (max_delta_d <= STATIONARITY_TOL_DELTA_D and delta_rf2_prev <= STATIONARITY_TOL_DELTA_RF2_N)
        if cycle >= 2 and is_stationary:
            print("\n" + "*" * 80)
            print("[H15-HALFSTEP-DRIVER] EQUILIBRIUM CONFIRMED AT CYCLE %d!" % cycle)
            print("[H15-HALFSTEP-DRIVER] Delta d = %.6f <= %.1e, Delta RF2 = %.4f N <= %.1f N" %
                  (max_delta_d, STATIONARITY_TOL_DELTA_D, delta_rf2_prev, STATIONARITY_TOL_DELTA_RF2_N))
            print("*" * 80)
            converged_status = "CONVERGED_STATIONARY_STATE"
            break

        d_current = d_next.copy()
        prev_rf2 = rf2_rp

    final_entry = history_log[-1] if history_log else {}

    h15_pass = (
        converged_status == "CONVERGED_STATIONARY_STATE" and
        final_entry.get("healing_violations", 1) == 0 and
        final_entry.get("free_res_max_kN_mm", 1.0) <= 1.0e-6 and
        final_entry.get("min_lambda_kN_mm", -1.0) >= -1.0e-9
    )

    summary_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_130_C4_INC86_HALFSTEP_H15_CONTINUATION",
        "hypothesis": "H15_HALFSTEP_AM_CONTINUATION",
        "status": converged_status,
        "h15_verdict": "H15_PASSED_MIDPOINT" if h15_pass else "H15_FAILED_NONSTATIONARY",
        "cycles_completed": len(history_log),
        "initial_u_rp_mm": u_init_inc86_mm,
        "target_u_rp_midpoint_mm": u_target_midpoint_mm,
        "forward_increment_mm": delta_u_target_mm,
        "history": history_log,
        "final_state": final_entry
    }

    with open(summary_path, "w") as f:
        json.dump(summary_data, f, indent=2)
    print("\n[H15-HALFSTEP-DRIVER] Summary saved to: %s" % summary_path)

if __name__ == "__main__":
    main()
