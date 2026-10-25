import json
import numpy as np
from pathlib import Path
import pandas as pd
import sys

sys.path.append('scripts/validation')
from evaluate_corrected_c3_coupled_transfer_and_increment import (
    C3_MESH_INP, parse_mesh, compute_plane_strain_c0, shape_functions,
    UEL_GP_COORDS, UEL_WEIGHTS, K_DEGRAD, uel_driving_energy,
    assemble_at2_system
)

# 1. Load C3 Mesh
nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
n_nodes = len(nlist_c3)

# 2. Load authentic Abaqus Stage-A state
with open("models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/r6_extracted_states.json", "r") as f:
    abq_data = json.load(f)

stage_a = abq_data["steps"]["Stage-A"]
rf2_abq = stage_a["rp_rf2_N"]
u_dict = stage_a["nodes_u"]

# Build u vector (n_nodes x 2) and d vector (n_nodes)
u_vec = np.zeros((n_nodes, 2))
d_vec = np.zeros(n_nodes)

for nid_str, vals in u_dict.items():
    nid = int(nid_str)
    if nid in n2idx_c3:
        idx = n2idx_c3[nid]
        u_vec[idx, 0] = vals[0]
        u_vec[idx, 1] = vals[1]
        if len(vals) > 2:
            d_vec[idx] = vals[2]

# 3. Load transferred lower bounds (d0, H0)
df_bounds = pd.read_csv("models/pandey_kumar_mode1/108_r6_c3_multi_increment_continuation/d_lower_bounds.csv", skipinitialspace=True)
d0_dict = {}
h0_dict = {}
for _, row in df_bounds.iterrows():
    eid = int(row['EID'])
    d0_dict[eid] = [row['D0_1'], row['D0_2'], row['D0_3'], row['D0_4']]
    h0_dict[eid] = [row['H0_1'], row['H0_2'], row['H0_3'], row['H0_4']]

# Also map nodal d0 lower bounds
d0_nodal = np.zeros(n_nodes)
for eid, conn in elements_c3.items():
    if eid in d0_dict:
        for k in range(4):
            nid = conn[k]
            idx = n2idx_c3[nid]
            d0_nodal[idx] = max(d0_nodal[idx], d0_dict[eid][k])

# If nodal U3 was not exported in ODB field outputs, use transferred d0_nodal
if np.all(d_vec == 0.0):
    d_vec = np.copy(d0_nodal)

# 4. Compute mechanical internal force vector F_int
C0, lam, mu = compute_plane_strain_c0()
F_int = np.zeros((n_nodes, 2))

elem_H_strain = {}
max_pos_m_mesh = 0.0
max_pos_m_eid = -1

for eid, conn in elements_c3.items():
    elem_indices = [n2idx_c3[n] for n in conn]
    xe = np.array([nodes_c3[n] for n in conn])
    ue = u_vec[elem_indices, :].flatten()
    de = d_vec[elem_indices]
    d_avg = np.mean(de)
    deg = (1.0 - d_avg)**2 + K_DEGRAD
    c_mech = C0 * deg

    elem_H_strain[eid] = []

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
        sig = c_mech.dot(eps)
        f_int_kpt = detJ * wt * B.T.dot(sig)

        for i in range(4):
            nid_idx = elem_indices[i]
            F_int[nid_idx, 0] += f_int_kpt[2*i]
            F_int[nid_idx, 1] += f_int_kpt[2*i+1]

        pos_m = uel_driving_energy(eps, lam, mu)
        elem_H_strain[eid].append(pos_m)
        if pos_m > max_pos_m_mesh:
            max_pos_m_mesh = pos_m
            max_pos_m_eid = eid

# Mechanical boundary conditions: bottom y=0, pin x=0, top y=0.00196510735, x=0
is_mech_free = np.ones((n_nodes, 2), dtype=bool)
for nid in nlist_c3:
    idx = n2idx_c3[nid]
    pt = nodes_c3[nid]
    if abs(pt[1] - 0.0) < 1e-9: # bottom
        is_mech_free[idx, 1] = False
    if abs(pt[1] - 0.10) < 1e-9: # top
        is_mech_free[idx, 0] = False
        is_mech_free[idx, 1] = False
    if abs(pt[0] - 0.0) < 1e-9 and abs(pt[1] - 0.0) < 1e-9: # pin
        is_mech_free[idx, 0] = False

# Compute max free mechanical residual (kN)
max_mech_res_kN = float(np.max(np.abs(F_int[is_mech_free])))

# 5. Evaluate Phase-Field Residual
# History field in UEL: H_eff = max(H0, pos_m)
elem_H_eff = {}
for eid in elements_c3:
    h0 = h0_dict.get(eid, [0.0]*4)
    h_strain = elem_H_strain[eid]
    elem_H_eff[eid] = [max(h0[k], h_strain[k]) for k in range(4)]

K_d, F_d = assemble_at2_system(nodes_c3, elements_c3, n2idx_c3, elem_H_eff)
R_phase = K_d.dot(d_vec) - F_d # Grad E(d)

# Classify free vs active/constrained phase nodes
# Free nodes: d > d0 + 1e-5 and d < 1.0 - 1e-5
diff_d = d_vec - d0_nodal
is_phase_free = (diff_d > 1e-5) & (d_vec < 0.999)
is_phase_bound = (diff_d <= 1e-5)

free_phase_res_max = float(np.max(np.abs(R_phase[is_phase_free]))) if np.any(is_phase_free) else 0.0
all_phase_res_max = float(np.max(np.abs(R_phase)))

# KKT Check: on bound nodes, d = d0 -> lambda = -R_phase >= 0 (meaning R_phase <= 0)
kkt_violations = int(np.sum((diff_d <= 1e-5) & (R_phase > 1e-6)))

# Healing Check: d >= d0 - 1e-8
min_healing = float(np.min(diff_d))

# History escalation check:
max_h0 = max(max(h) for h in h0_dict.values())
max_heff = max(max(h) for h in elem_H_eff.values())

# Stationarity Verdict
# Stationarity thresholds:
# 1. Mechanical residual <= 1e-4 kN (Abaqus convergence)
# 2. Free-phase residual <= 1e-6 kN/mm
# 3. KKT violations == 0
# 4. Healing >= -1e-8
mech_pass = max_mech_res_kN <= 1e-4
phase_pass = free_phase_res_max <= 1e-6
kkt_pass = kkt_violations == 0
healing_pass = min_healing >= -1e-8

is_coupled_stationary = mech_pass and phase_pass and kkt_pass and healing_pass

result = {
    "schema": 1,
    "task": "F1597-STAGE-A-STATIONARITY-AUDIT",
    "stage_a_telemetry": {
        "rf2_abq_N": rf2_abq,
        "max_mech_residual_kN": max_mech_res_kN,
        "mech_residual_pass": bool(mech_pass),
        "free_phase_residual_kN_mm": free_phase_res_max,
        "free_phase_residual_pass": bool(phase_pass),
        "all_phase_residual_max_kN_mm": all_phase_res_max,
        "kkt_violations": kkt_violations,
        "kkt_pass": bool(kkt_pass),
        "min_healing": min_healing,
        "healing_pass": bool(healing_pass),
        "max_h0_donor_MPa": max_h0,
        "max_pos_m_stage_a_MPa": max_pos_m_mesh,
        "max_pos_m_eid": max_pos_m_eid,
        "max_heff_stage_a_MPa": max_heff,
        "num_free_phase_nodes": int(np.sum(is_phase_free)),
        "is_coupled_stationary": bool(is_coupled_stationary)
    }
}

print(json.dumps(result, indent=2))

with open("results/validation/mode1_f1597/stage_a_stationarity_audit.json", "w") as f:
    json.dump(result, f, indent=2)

print("\nAudit written to results/validation/mode1_f1597/stage_a_stationarity_audit.json")
