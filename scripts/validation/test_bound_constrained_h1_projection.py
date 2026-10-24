#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_bound_constrained_h1_projection.py
Solves the exact bound-constrained H^1 projection:
min 1/2 d^T A d - b^T d  subject to d_ckpt <= d <= 1.0
and checks KKT residuals, energies, reaction force, and non-healing.
"""

import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.optimize import lsq_linear

sys.path.insert(0, ".")
from scripts.validation.evaluate_c4_to_c5_l2_projection import (
    load_mesh, shape_functions, compute_energies, solve_elasticity_rf,
    E_MOD, E_NU, E_GC, E_L0, E_K, DONOR_RF2_N, DONOR_E_FRAC_MJ, U_TOP_MM
)
import csv

c4_mesh_inp = Path("models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp")
c4_nodal_csv = Path("results/validation/mode1_f1597/pkg94_step4_frame7_nodal_state.csv")
c4_nodes, c4_elements = load_mesh(c4_mesh_inp)
c4_damage_map = {int(r["node_id"]): float(r["damage"]) for r in csv.DictReader(open(c4_nodal_csv))}
c4_node_list = sorted(c4_nodes.keys())
c4_node_to_idx = {nid: i for i, nid in enumerate(c4_node_list)}
c4_d = np.array([c4_damage_map[nid] for nid in c4_node_list])

c5_mesh_inp = Path("models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_crack_band_mesh_c5.inp")
c5_nodes, c5_elements = load_mesh(c5_mesh_inp)
c5_node_list = sorted(c5_nodes.keys())
c5_node_to_idx = {nid: i for i, nid in enumerate(c5_node_list)}
n_c5_nodes = len(c5_node_list)

c5_state_table = Path("models/pandey_kumar_mode1/102_r1_c5_coupled_staggered_history_repaired/candidate_c5_frame7_mapped_state_table.csv")
d_ckpt_map = {}
for r in csv.reader(open(c5_state_table)):
    if r and r[0].strip().upper() == "NODE":
        d_ckpt_map[int(r[1])] = float(r[4])
d_ckpt = np.array([d_ckpt_map[nid] for nid in c5_node_list])

c4_x = np.array(sorted(list(set(round(p[0], 8) for p in c4_nodes.values()))))
c4_y = np.array(sorted(list(set(round(p[1], 8) for p in c4_nodes.values()))))
slit_y_idx = int(np.argmin(np.abs(c4_y - 0.050)))

def locate_c4_element(x: float, y: float, flank_type: str):
    x = max(0.0, min(0.100, x))
    y = max(0.0, min(0.100, y))
    i = int(np.searchsorted(c4_x, x)) - 1
    i = max(0, min(len(c4_x) - 2, i))
    j = int(np.searchsorted(c4_y, y)) - 1
    j = max(0, min(len(c4_y) - 2, j))
    if abs(y - 0.050) < 1e-6 and x <= 0.040 + 1e-6:
        if flank_type == "upper": j = slit_y_idx
        elif flank_type == "lower": j = slit_y_idx - 1
    eid = j * (len(c4_x) - 1) + (i + 1)
    x0, x1 = c4_x[i], c4_x[i + 1]
    y0, y1 = c4_y[j], c4_y[j + 1]
    xi = 2.0 * (x - x0) / (x1 - x0) - 1.0
    eta = 2.0 * (y - y0) / (y1 - y0) - 1.0
    return eid, float(xi), float(eta)

def eval_c4_field(x: float, y: float, flank_type: str):
    c4_eid, xi, eta = locate_c4_element(x, y, flank_type)
    conn = c4_elements[c4_eid]
    c4_indices = [c4_node_to_idx[n] for n in conn]
    d_elem = c4_d[c4_indices]
    xe = np.array([c4_nodes[n] for n in conn])
    N, dNdxi, dNdeta = shape_functions(xi, eta)
    d_val = float(np.dot(N, d_elem))
    J = np.zeros((2, 2))
    for k in range(4):
        J[0, 0] += dNdxi[k] * xe[k, 0]; J[0, 1] += dNdxi[k] * xe[k, 1]
        J[1, 0] += dNdeta[k] * xe[k, 0]; J[1, 1] += dNdeta[k] * xe[k, 1]
    detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
    invJ = np.array([[ J[1, 1], -J[0, 1]], [-J[1, 0],  J[0, 0]]]) / detJ
    dNdx = np.zeros((2, 4))
    for k in range(4):
        dNdx[0, k] = invJ[0, 0] * dNdxi[k] + invJ[0, 1] * dNdeta[k]
        dNdx[1, k] = invJ[1, 0] * dNdxi[k] + invJ[1, 1] * dNdeta[k]
    grad_d = np.dot(dNdx, d_elem)
    return d_val, grad_d

gp_coords = [
    (-1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
    ( 1.0 / np.sqrt(3.0), -1.0 / np.sqrt(3.0)),
    (-1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0)),
    ( 1.0 / np.sqrt(3.0),  1.0 / np.sqrt(3.0))
]

I_m, J_m, V_m = [], [], []
I_k, J_k, V_k = [], [], []
f_L2 = np.zeros(n_c5_nodes)
f_grad = np.zeros(n_c5_nodes)

for eid in sorted(c5_elements.keys()):
    conn = c5_elements[eid]
    elem_indices = [c5_node_to_idx[n] for n in conn]
    xe = np.array([c5_nodes[n] for n in conn])
    cy = np.mean(xe[:, 1])
    flank_type = "upper" if cy >= 0.050 else "lower"

    for xi, eta in gp_coords:
        N, dNdxi, dNdeta = shape_functions(xi, eta)
        J = np.zeros((2, 2))
        for i in range(4):
            J[0, 0] += dNdxi[i] * xe[i, 0]; J[0, 1] += dNdxi[i] * xe[i, 1]
            J[1, 0] += dNdeta[i] * xe[i, 0]; J[1, 1] += dNdeta[i] * xe[i, 1]
        detJ = J[0, 0] * J[1, 1] - J[0, 1] * J[1, 0]
        cj = detJ * 1.0
        invJ = np.array([[ J[1, 1], -J[0, 1]], [-J[1, 0],  J[0, 0]]]) / detJ
        dNdx = np.zeros((2, 4))
        for i in range(4):
            dNdx[0, i] = invJ[0, 0] * dNdxi[i] + invJ[0, 1] * dNdeta[i]
            dNdx[1, i] = invJ[1, 0] * dNdxi[i] + invJ[1, 1] * dNdeta[i]

        gp_x = float(np.dot(N, xe[:, 0]))
        gp_y = float(np.dot(N, xe[:, 1]))
        d_c4_gp, grad_d_c4_gp = eval_c4_field(gp_x, gp_y, flank_type)

        for i in range(4):
            idx_i = elem_indices[i]
            f_L2[idx_i] += cj * N[i] * d_c4_gp
            grad_N_dot_grad_d = dNdx[0, i] * grad_d_c4_gp[0] + dNdx[1, i] * grad_d_c4_gp[1]
            f_grad[idx_i] += cj * grad_N_dot_grad_d

            for j in range(4):
                idx_j = elem_indices[j]
                I_m.append(idx_i); J_m.append(idx_j); V_m.append(cj * N[i] * N[j])
                bdb = dNdx[0, i] * dNdx[0, j] + dNdx[1, i] * dNdx[1, j]
                I_k.append(idx_i); J_k.append(idx_j); V_k.append(cj * bdb)

M_c5 = sp.coo_matrix((V_m, (I_m, J_m)), shape=(n_c5_nodes, n_c5_nodes)).tocsr()
K_grad_c5 = sp.coo_matrix((V_k, (I_k, J_k)), shape=(n_c5_nodes, n_c5_nodes)).tocsr()

A_energy = (E_GC / E_L0) * M_c5 + (E_GC * E_L0) * K_grad_c5
rhs_energy = (E_GC / E_L0) * f_L2 + (E_GC * E_L0) * f_grad

print(f"A_energy assembled: {A_energy.nnz} nonzeros")

# 1. Unconstrained solve
d_unconstrained = spla.spsolve(A_energy, rhs_energy)
print(f"Unconstrained d bounds: min={np.min(d_unconstrained):.6f}, max={np.max(d_unconstrained):.6f}")

# 2. Bound-Constrained solve with Primal-Dual Active Set (PDAS)
# min 1/2 d^T A d - b^T d  s.t.  d_lower <= d <= d_upper
d_lower = d_ckpt.copy()  # Non-healing constraint: d >= d_ckpt
d_upper = np.ones(n_c5_nodes) * 1.0

# PDAS iteration for box constraints:
d_pdas = np.clip(d_unconstrained, d_lower, d_upper)
n = n_c5_nodes
c_param = 1.0  # active set parameter

for it in range(50):
    grad = A_energy.dot(d_pdas) - rhs_energy
    
    # Active sets
    act_lower = (d_pdas - d_lower) + grad / c_param < 0.0
    act_upper = (d_upper - d_pdas) - grad / c_param < 0.0
    free = ~(act_lower | act_upper)
    
    n_lower = np.sum(act_lower)
    n_upper = np.sum(act_upper)
    n_free = np.sum(free)
    
    # Solve on free set
    d_next = np.zeros(n)
    d_next[act_lower] = d_lower[act_lower]
    d_next[act_upper] = d_upper[act_upper]
    
    free_idx = np.where(free)[0]
    if len(free_idx) > 0:
        A_FF = A_energy[free_idx, :][:, free_idx]
        fixed_idx = np.where(~free)[0]
        rhs_F = rhs_energy[free_idx] - A_energy[free_idx, :][:, fixed_idx].dot(d_next[fixed_idx])
        d_F = spla.spsolve(A_FF, rhs_F)
        d_next[free_idx] = d_F
    
    diff = np.max(np.abs(d_next - d_pdas))
    d_pdas = d_next
    if diff < 1e-10:
        print(f"PDAS converged in {it+1} iterations! (Active lower: {n_lower}, Active upper: {n_upper}, Free: {n_free})")
        break

# Verify KKT conditions
grad_final = A_energy.dot(d_pdas) - rhs_energy
kkt_lower_viol = np.sum(d_pdas < d_lower - 1e-9)
kkt_upper_viol = np.sum(d_pdas > d_upper + 1e-9)
# Multiplier checks:
# At lower bound: grad >= 0
mult_lower_viol = np.sum((d_pdas <= d_lower + 1e-9) & (grad_final < -1e-6))
# At upper bound: grad <= 0
mult_upper_viol = np.sum((d_pdas >= d_upper - 1e-9) & (grad_final > 1e-6))
# Free: grad == 0
free_grad_norm = np.max(np.abs(grad_final[(d_pdas > d_lower + 1e-9) & (d_pdas < d_upper - 1e-9)])) if np.sum((d_pdas > d_lower + 1e-9) & (d_pdas < d_upper - 1e-9)) > 0 else 0.0

print(f"KKT Verification:")
print(f"  Lower bound violations (d < d_ckpt): {kkt_lower_viol}")
print(f"  Upper bound violations (d > 1.0):    {kkt_upper_viol}")
print(f"  Lower multiplier violations:         {mult_lower_viol}")
print(f"  Upper multiplier violations:         {mult_upper_viol}")
print(f"  Free gradient inf-norm:              {free_grad_norm:.6e}")
print(f"  d_pdas bounds: min={np.min(d_pdas):.6f}, max={np.max(d_pdas):.6f}")

# Compute Energies and RF2
en_pdas = compute_energies(c5_nodes, c5_elements, d_pdas)
rf_pdas, _ = solve_elasticity_rf(c5_nodes, c5_elements, d_pdas)

# Compare vs Donor
e_err_abaqus = (en_pdas["e_total_mJ"] - DONOR_E_FRAC_MJ) / DONOR_E_FRAC_MJ * 100.0
rf_err_abaqus = (rf_pdas - DONOR_RF2_N) / DONOR_RF2_N * 100.0

print(f"\nResults for Bound-Constrained H^1 Transfer (d >= d_ckpt, d <= 1.0):")
print(f"  Fracture Energy: {en_pdas['e_total_mJ']:.6f} mJ (Error vs Abaqus {DONOR_E_FRAC_MJ:.6f} mJ: {e_err_abaqus:+.4f}%)")
print(f"  Reaction Force:  {rf_pdas:.4f} N (Error vs Abaqus {DONOR_RF2_N:.4f} N: {rf_err_abaqus:+.4f}%)")
print(f"  Gate E_frac (<= 2.0%): {'PASS' if abs(e_err_abaqus) <= 2.0 else 'FAIL'}")
print(f"  Gate RF2 (<= 5.0%):    {'PASS' if abs(rf_err_abaqus) <= 5.0 else 'FAIL'}")

# Also test box constraint with d >= 0, d <= 1.0 (pure physical bounds without d >= d_ckpt)
print("\n--- Solving with Pure Physical Bounds (0 <= d <= 1.0) ---")
d_pdas_phys = np.clip(d_unconstrained, 0.0, 1.0)
for it in range(50):
    grad = A_energy.dot(d_pdas_phys) - rhs_energy
    act_lower = (d_pdas_phys - 0.0) + grad / c_param < 0.0
    act_upper = (1.0 - d_pdas_phys) - grad / c_param < 0.0
    free = ~(act_lower | act_upper)
    d_next = np.zeros(n)
    d_next[act_lower] = 0.0
    d_next[act_upper] = 1.0
    free_idx = np.where(free)[0]
    if len(free_idx) > 0:
        A_FF = A_energy[free_idx, :][:, free_idx]
        fixed_idx = np.where(~free)[0]
        rhs_F = rhs_energy[free_idx] - A_energy[free_idx, :][:, fixed_idx].dot(d_next[fixed_idx])
        d_F = spla.spsolve(A_FF, rhs_F)
        d_next[free_idx] = d_F
    diff = np.max(np.abs(d_next - d_pdas_phys))
    d_pdas_phys = d_next
    if diff < 1e-10:
        print(f"Pure physical PDAS converged in {it+1} iterations! (Active upper: {np.sum(act_upper)})")
        break

en_phys = compute_energies(c5_nodes, c5_elements, d_pdas_phys)
rf_phys, _ = solve_elasticity_rf(c5_nodes, c5_elements, d_pdas_phys)
e_err_phys = (en_phys["e_total_mJ"] - DONOR_E_FRAC_MJ) / DONOR_E_FRAC_MJ * 100.0
rf_err_phys = (rf_phys - DONOR_RF2_N) / DONOR_RF2_N * 100.0

# Check healing relative to d_ckpt
healing_nodes = np.where(d_pdas_phys < d_ckpt - 1e-5)[0]
print(f"Results for Pure Physical Bounds (0 <= d <= 1.0):")
print(f"  Healing nodes vs d_ckpt: {len(healing_nodes)} / {n_c5_nodes}")
if len(healing_nodes) > 0:
    max_heal = np.max(d_ckpt[healing_nodes] - d_pdas_phys[healing_nodes])
    print(f"  Max healing magnitude: {max_heal:.6e}")
print(f"  Fracture Energy: {en_phys['e_total_mJ']:.6f} mJ (Error vs Abaqus: {e_err_phys:+.4f}%)")
print(f"  Reaction Force:  {rf_phys:.4f} N (Error vs Abaqus: {rf_err_phys:+.4f}%)")
print(f"  Gate E_frac (<= 2.0%): {'PASS' if abs(e_err_phys) <= 2.0 else 'FAIL'}")
print(f"  Gate RF2 (<= 5.0%):    {'PASS' if abs(rf_err_phys) <= 5.0 else 'FAIL'}")
