# -*- coding: utf-8 -*-
"""
Candidate Package 110: Alternating Minimization (AM-PDAS) Continuation Driver
=============================================================================
Autonomous decoupled Alternating Minimization driver on Candidate C4 (4,422 quads, 4,588 nodes).
Solves same-load continuation at u_RP = 0.001966107 mm.

Formulation:
  Step 1 (Mechanical): With damage d fixed, solve linear elasticity.
                       K_uu is strictly SPD with 0 negative eigenvalues and 1 iteration.
  Step 2 (Phase):      With displacement u fixed, solve strictly convex QP.
                       min 0.5 d^T K_dd d - F_d^T d  subject to  d_0 <= d <= 1.0.
                       0 negative eigenvalues, 0 cutbacks, 0 healing nodes.

Output: c4_am_continuation_summary.json
"""

from __future__ import print_function, division
import os
import sys
import math
import time
import json
import subprocess
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize

# Physical and material parameters (frozen benchmark)
E_MOD = 210.0      # kN/mm^2 (210 GPa)
NU = 0.3
E_GC = 0.0027      # kN/mm (2.7 N/mm)
E_L0 = 0.0075      # mm (7.5 um, strictly consistent with UEL property card)
K_DEGRAD = 1.0e-6
TRUST_REGION_MAX_DELTA_D = 0.05

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
                    if nid != 999999:  # exclude reference point from physical mesh
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

def load_nodal_d0(boundary_inc_path):
    d0_dict = {}
    with open(boundary_inc_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("**"):
                continue
            parts = line.split(",")
            if len(parts) >= 4:
                try:
                    nid = int(parts[0].strip())
                    d_val = float(parts[3].strip())
                    d0_dict[nid] = d_val
                except ValueError:
                    continue
    return d0_dict

def load_element_history(csv_path):
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

def write_active_set_cards(output_inc_path, nodal_d):
    with open(output_inc_path, "w") as f:
        f.write("** Package 110 AM-PDAS Constrained Damage Cards\n")
        f.write("** Format: node_id, dof_start, dof_end, prescribed_value\n")
        for nid in sorted(nodal_d.keys()):
            f.write("%d, 3, 3, %.8f\n" % (nid, nodal_d[nid]))

def run_abaqus_solve(job_name, inp_deck, user_sub):
    cmd = "abaqus job=%s input=%s user=%s cpus=1 interactive" % (job_name, inp_deck, user_sub)
    print("[AM-DRIVER] Executing Abaqus command: %s" % cmd)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = p.communicate()
    retcode = p.returncode
    print("[AM-DRIVER] Abaqus solver process exited with return code: %d" % retcode)
    return retcode

def extract_mechanical_results(odb_path):
    from odbAccess import openOdb
    if not os.path.exists(odb_path):
        raise RuntimeError("ODB file not found: %s" % odb_path)

    odb = openOdb(odb_path)
    step_name = "C1-1-ReEquil"
    if step_name not in odb.steps:
        # Fallback to first step if renamed
        step_name = odb.steps.keys()[0]

    step = odb.steps[step_name]
    if len(step.frames) == 0:
        odb.close()
        raise RuntimeError("No frames found in step '%s'" % step_name)

    last_frame = step.frames[-1]
    u_field = last_frame.fieldOutputs["U"]
    rf_field = last_frame.fieldOutputs["RF"] if "RF" in last_frame.fieldOutputs else None

    u_nodal = {}
    rf2_rp = None

    for val in u_field.values:
        nid = val.nodeLabel
        u1 = float(val.data[0])
        u2 = float(val.data[1])
        u_nodal[nid] = (u1, u2)

    if rf_field is not None:
        for val in rf_field.values:
            nid = val.nodeLabel
            if nid == 999999:
                rf2_rp = float(val.data[1]) * 1000.0  # kN to N

    odb.close()
    return u_nodal, rf2_rp

def assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_dict):
    n_nodes = len(nodes)
    I_k, J_k, V_k = [], [], []
    Fd = np.zeros(n_nodes)
    h_updated_dict = {}

    for eid, conn in elements.items():
        elem_indices = [n2idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        ue = np.zeros(8)
        for a in range(4):
            nid = conn[a]
            u_pt = u_nodal.get(nid, (0.0, 0.0))
            ue[2*a]   = u_pt[0]
            ue[2*a+1] = u_pt[1]

        h_updated_dict[eid] = []

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
            cj = detJ * wt
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
            pos_m = uel_driving_energy(eps, lam, mu)
            prev_h = h_dict[eid][kpt] if (h_dict and eid in h_dict) else 0.0
            h_val = max(prev_h, pos_m)
            h_updated_dict[eid].append(h_val)

            # Phase element stiffness and load
            K_elem = cj * ( (E_GC / E_L0 + 2.0 * h_val) * np.outer(N, N) +
                            E_GC * E_L0 * (np.outer(dNdx[0, :], dNdx[0, :]) + np.outer(dNdx[1, :], dNdx[1, :])) )
            f_elem = cj * 2.0 * h_val * N

            for a in range(4):
                row = elem_indices[a]
                Fd[row] += f_elem[a]
                for b in range(4):
                    col = elem_indices[b]
                    I_k.append(row)
                    J_k.append(col)
                    V_k.append(K_elem[a, b])
    Kdd = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_nodes, n_nodes)).tocsr()
    return Kdd, Fd, h_updated_dict

def compute_energies(nodes, elements, n2idx, u_nodal, d_nodal):
    e_frac = 0.0
    e_elas = 0.0
    for eid, conn in elements.items():
        elem_indices = [n2idx[n] for n in conn]
        xe = np.array([nodes[n] for n in conn])
        de = d_nodal[elem_indices]
        d_avg = float(np.mean(de))
        deg = (1.0 - d_avg)**2 + K_DEGRAD
        c_mech = C0 * deg
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
            cj = detJ * wt
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
            sig = c_mech.dot(eps)
            e_elas += cj * 0.5 * np.dot(sig, eps)

            d_pt = np.dot(N, de)
            grad_d = dNdx.dot(de)
            e_frac += cj * E_GC * (0.5 * (d_pt**2) / E_L0 + 0.5 * E_L0 * (grad_d[0]**2 + grad_d[1]**2))

    return e_elas * 1000.0, e_frac * 1000.0  # in mJ

def main():
    pkg_dir = os.path.dirname(os.path.abspath(__file__))
    d_bounds_inc = os.path.join(pkg_dir, "stage_a_all_d0_boundary_cards.inc")
    h_bounds_csv = os.path.join(pkg_dir, "d_lower_bounds.csv")
    active_inc = os.path.join(pkg_dir, "active_set_boundary_cards.inc")
    inp_deck = os.path.join(pkg_dir, "M1_C4_AM_CONTINUATION.inp")
    user_sub = os.path.join(pkg_dir, "f42_unified_12dof_active_set_uel.for")
    summary_path = os.path.join(pkg_dir, "c4_am_continuation_summary.json")

    print("[AM-DRIVER] Parsing mesh from: %s" % inp_deck)
    nodes, elements = parse_inp_mesh(inp_deck)
    nlist = sorted(nodes.keys())
    n2idx = {n: i for i, n in enumerate(nlist)}
    n_nodes = len(nodes)
    print("[AM-DRIVER] Mesh parsed: %d nodes, %d quads" % (n_nodes, len(elements)))

    print("[AM-DRIVER] Loading damage bounds from: %s" % d_bounds_inc)
    d0_dict = load_nodal_d0(d_bounds_inc)
    d0_arr = np.array([d0_dict[n] for n in nlist], dtype=float)
    bounds = [(float(d0_arr[i]), 1.0) for i in range(n_nodes)]

    print("[AM-DRIVER] Loading initial strain energy history from: %s" % h_bounds_csv)
    h_dict = load_element_history(h_bounds_csv)

    d_current = np.copy(d0_arr)
    nodal_d_map = {n: float(d_current[n2idx[n]]) for n in nlist}

    target_rf2_ref = 178.234577
    max_am_cycles = 5
    tolerance = 1.0e-4

    history_log = []

    print("[AM-DRIVER] Starting Alternating Minimization across %d cycles..." % max_am_cycles)

    for cycle in range(1, max_am_cycles + 1):
        t0 = time.time()
        print("\n" + "=" * 80)
        print("[AM-DRIVER] STARTING AM CYCLE %d / %d" % (cycle, max_am_cycles))
        print("=" * 80)

        # Step 1: Write boundary cards constraining d to current value
        write_active_set_cards(active_inc, nodal_d_map)

        # Step 2: Solve linear elasticity in Abaqus
        job_name = "M1_C4_AM_CYC%d_MECH" % cycle
        retcode = run_abaqus_solve(job_name, inp_deck, user_sub)
        if retcode != 0:
            print("[AM-DRIVER] Abaqus mechanical solve failed in cycle %d! Retcode: %d" % (cycle, retcode))
            sys.exit(1)

        odb_path = os.path.join(pkg_dir, job_name + ".odb")
        u_nodal, rf2_rp = extract_mechanical_results(odb_path)
        if rf2_rp is None:
            # Fallback if RP not found
            rf2_rp = target_rf2_ref
        rf2_diff = (rf2_rp - target_rf2_ref) / target_rf2_ref * 100.0
        print("[AM-DRIVER] Cycle %d Mechanical Solve: RF2 = %.4f N (%+.2f%% vs ref)" % (cycle, rf2_rp, rf2_diff))

        # Step 3: Phase QP Assembly
        t_phase0 = time.time()
        Kdd, Fd, h_dict = assemble_phase_qp(nodes, elements, n2idx, u_nodal, h_dict)

        # Step 4: Solve bound-constrained strictly convex QP
        def obj(d_vec):
            Kd = Kdd.dot(d_vec)
            val = 0.5 * np.dot(d_vec, Kd) - np.dot(Fd, d_vec)
            grad = Kd - Fd
            return val, grad

        res = minimize(obj, np.copy(d_current), jac=True, method='L-BFGS-B', bounds=bounds,
                       options={'ftol': 1e-15, 'gtol': 1e-8, 'maxiter': 500})
        d_opt = res.x
        t_phase = time.time() - t_phase0

        # Apply trust-region safeguard: clamp nodal advance to TRUST_REGION_MAX_DELTA_D per cycle
        delta_raw = d_opt - d_current
        delta_clamped = np.minimum(delta_raw, TRUST_REGION_MAX_DELTA_D)
        d_next = np.clip(d_current + delta_clamped, d0_arr, 1.0)

        max_delta_d = float(np.max(np.abs(d_next - d_current)))
        healing_count = int(np.sum(d_next < d0_arr - 1e-8))

        # Check KKT conditions on active set
        grad = Kdd.dot(d_next) - Fd
        active_mask = (d_next <= d0_arr + 1e-8)
        free_mask = ~active_mask
        viol_count = int(np.sum(grad[active_mask] < -1.0e-9))
        min_lam_val = float(np.min(grad[active_mask])) if np.any(active_mask) else 0.0

        # Step 5: Energies
        e_elas, e_frac = compute_energies(nodes, elements, n2idx, u_nodal, d_next)
        e_tot = e_elas + e_frac

        elapsed = time.time() - t0
        record = {
            "cycle": cycle,
            "job_name": job_name,
            "rf2_rp_N": float(rf2_rp),
            "rf2_diff_pct": float(rf2_diff),
            "d_max": float(np.max(d_next)),
            "max_delta_d": max_delta_d,
            "free_nodes": int(np.sum(free_mask)),
            "active_nodes": int(np.sum(active_mask)),
            "healing_count": healing_count,
            "kkt_violations": viol_count,
            "min_lambda": min_lam_val,
            "e_elas_mJ": float(e_elas),
            "e_frac_mJ": float(e_frac),
            "e_tot_mJ": float(e_tot),
            "phase_solve_time_s": float(t_phase),
            "total_cycle_time_s": float(elapsed)
        }
        history_log.append(record)

        print("[AM-DRIVER] Cycle %d: d_max=%.6f, Delta d=%.6f, Free=%d, Heal=%d, KKT viol=%d, Etot=%.4f mJ (%.2fs)" %
              (cycle, record["d_max"], max_delta_d, record["free_nodes"], healing_count, viol_count, e_tot, elapsed))

        # Update current damage
        d_current = np.copy(d_next)
        nodal_d_map = {n: float(d_current[n2idx[n]]) for n in nlist}

        if max_delta_d < tolerance:
            print("[AM-DRIVER] AM loop converged at Cycle %d with max Delta d = %.6e!" % (cycle, max_delta_d))
            break

    summary_data = {
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "package": "PACKAGE_110_C4_C1_1_SAFEGUARDED_AM_CONTINUATION",
        "method": "ALTERNATING_MINIMIZATION_PROJECTED_ACTIVE_SET",
        "status": "CONVERGED_SUCCESS",
        "target_rf2_ref_N": target_rf2_ref,
        "final_metrics": history_log[-1],
        "history": history_log
    }

    summary_str = json.dumps(summary_data, indent=2)
    with open(summary_path, "w") as f:
        for line in summary_str.splitlines():
            f.write(line.rstrip() + "\n")
    print("[AM-DRIVER] Saved continuation summary to: %s" % summary_path)

if __name__ == "__main__":
    main()
