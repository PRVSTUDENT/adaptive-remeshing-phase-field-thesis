import sys
import csv
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

sys.path.insert(0, ".")
from scripts.validation.evaluate_c4_to_c5_l2_projection import *

c4_mesh_inp = Path("models/pandey_kumar_mode1/94_c4_package94_authentic_transfer/candidate_crack_band_mesh_c4.inp")
c4_nodes, c4_elems = load_mesh(c4_mesh_inp)
c4_d = np.array([float(r["damage"]) for r in csv.DictReader(open("results/validation/mode1_f1597/pkg94_step4_frame7_nodal_state.csv"))])

node_list = sorted(c4_nodes.keys())
node_to_idx = {nid: i for i, nid in enumerate(node_list)}
n_nodes = len(node_list)
n_dofs = 2 * n_nodes

C0 = get_elasticity_c0()
gp_coords = [(-1.0/np.sqrt(3.0), -1.0/np.sqrt(3.0)), (1.0/np.sqrt(3.0), -1.0/np.sqrt(3.0)), (-1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0)), (1.0/np.sqrt(3.0), 1.0/np.sqrt(3.0))]
I_u, J_u, V_u = [], [], []

for eid in sorted(c4_elems.keys()):
    conn = c4_elems[eid]
    elem_indices = [node_to_idx[n] for n in conn]
    xe = np.array([c4_nodes[n] for n in conn])
    d_elem = c4_d[elem_indices]
    d_avg = np.mean(d_elem)
    deg = (1.0 - d_avg)**2 + E_K
    C_deg = C0 * deg

    for xi, eta in gp_coords:
        N, dNdxi, dNdeta = shape_functions(xi, eta)
        J = np.zeros((2, 2))
        for i in range(4):
            J[0, 0] += dNdxi[i]*xe[i, 0]
            J[0, 1] += dNdxi[i]*xe[i, 1]
            J[1, 0] += dNdeta[i]*xe[i, 0]
            J[1, 1] += dNdeta[i]*xe[i, 1]
        detJ = J[0, 0]*J[1, 1] - J[0, 1]*J[1, 0]
        cj = detJ * 1.0
        invJ = np.array([[J[1, 1], -J[0, 1]], [-J[1, 0], J[0, 0]]]) / detJ
        dNdx = np.zeros((2, 4))
        for i in range(4):
            dNdx[0, i] = invJ[0, 0]*dNdxi[i] + invJ[0, 1]*dNdeta[i]
            dNdx[1, i] = invJ[1, 0]*dNdxi[i] + invJ[1, 1]*dNdeta[i]
        B = np.zeros((3, 8))
        for i in range(4):
            B[0, 2*i] = dNdx[0, i]
            B[1, 2*i+1] = dNdx[1, i]
            B[2, 2*i] = dNdx[1, i]
            B[2, 2*i+1] = dNdx[0, i]
        Ke = cj * B.T.dot(C_deg).dot(B)
        elem_dofs = []
        for idx in elem_indices:
            elem_dofs.extend([2*idx, 2*idx + 1])
        for r in range(8):
            for c in range(8):
                I_u.append(elem_dofs[r])
                J_u.append(elem_dofs[c])
                V_u.append(Ke[r, c])

K_u = sp.coo_matrix((V_u, (I_u, J_u)), shape=(n_dofs, n_dofs)).tocsr()
bottom_nodes = [nid for nid in node_list if abs(c4_nodes[nid][1]) < 1e-5]
top_nodes = [nid for nid in node_list if abs(c4_nodes[nid][1] - 0.100) < 1e-5]

# Solve Case 1: Clamped top u1 = 0
p1 = {}
for nid in bottom_nodes:
    idx = node_to_idx[nid]
    p1[2*idx + 1] = 0.0
    if abs(c4_nodes[nid][0]) < 1e-5: p1[2*idx] = 0.0
for nid in top_nodes:
    idx = node_to_idx[nid]
    p1[2*idx + 1] = U_TOP_MM
    p1[2*idx] = 0.0

keys1 = np.array(sorted(p1.keys()))
vals1 = np.array([p1[k] for k in keys1])
free_mask1 = np.ones(n_dofs, dtype=bool)
free_mask1[keys1] = False
free1 = np.arange(n_dofs)[free_mask1]
u_free1 = spla.spsolve(K_u[free1, :][:, free1], -K_u[free1, :][:, keys1].dot(vals1))
u1 = np.zeros(n_dofs); u1[keys1] = vals1; u1[free1] = u_free1
rf1 = sum(K_u.dot(u1)[2*node_to_idx[nid] + 1] for nid in top_nodes) * 1000.0

# Solve Case 2: Free top u1 (Abaqus OP=NEW)
p2 = {}
for nid in bottom_nodes:
    idx = node_to_idx[nid]
    p2[2*idx + 1] = 0.0
    if abs(c4_nodes[nid][0]) < 1e-5: p2[2*idx] = 0.0
for nid in top_nodes:
    idx = node_to_idx[nid]
    p2[2*idx + 1] = U_TOP_MM
    # u1 is FREE!

keys2 = np.array(sorted(p2.keys()))
vals2 = np.array([p2[k] for k in keys2])
free_mask2 = np.ones(n_dofs, dtype=bool)
free_mask2[keys2] = False
free2 = np.arange(n_dofs)[free_mask2]
u_free2 = spla.spsolve(K_u[free2, :][:, free2], -K_u[free2, :][:, keys2].dot(vals2))
u2 = np.zeros(n_dofs); u2[keys2] = vals2; u2[free2] = u_free2
rf2 = sum(K_u.dot(u2)[2*node_to_idx[nid] + 1] for nid in top_nodes) * 1000.0

print(f"Case 1 (Clamped u1 on top): RF2 = {rf1:.4f} N (error vs Abaqus: {(rf1 - DONOR_RF2_N)/DONOR_RF2_N*100:+.2f}%)")
print(f"Case 2 (Free u1 on top):    RF2 = {rf2:.4f} N (error vs Abaqus: {(rf2 - DONOR_RF2_N)/DONOR_RF2_N*100:+.2f}%)")
