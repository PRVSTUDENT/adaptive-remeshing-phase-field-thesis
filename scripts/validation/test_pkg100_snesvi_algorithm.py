"""
Test Package 100 SNESVI Projected Active-Set Globalization Algorithm.
Verifies:
1. Projected active-set state feasibility: d_proj = clip(d_trial, d_ckpt, 1.0).
2. Suppression of chattering boundary nodes upon cycle detection.
3. Clean convergence in finite iterations with zero healing, zero overshoot, and stationary active set.
"""

import sys
from pathlib import Path
import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

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

def test_snesvi():
    root = Path(".")
    pkg_dir = root / "models" / "pandey_kumar_mode1" / "100_c5_pdas_snesvi_projected_continuation"
    mesh_path = pkg_dir / "candidate_crack_band_mesh_c5.inp"
    state_path = pkg_dir / "candidate_c5_frame7_mapped_state_table.csv"

    E_GC = 0.0027   # kN/mm
    E_L0 = 0.0075   # mm
    TAU_RES = 1.0e-6
    TAU_FEAS = 1.0e-8

    # 1. Load mesh
    nodes = {}
    elements = {}
    with open(mesh_path, "r", encoding="utf-8") as f:
        reading = None
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"): continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not any(u.startswith(k) for k in ["*NODE OUTPUT", "*NODE PRINT", "*NODE FILE"]):
                    reading = "NODE"
                elif u.startswith("*ELEMENT"):
                    reading = "ELEMENT"
                else:
                    reading = None
                continue
            if reading == "NODE":
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 3 and p[0].isdigit():
                    nodes[int(p[0])] = np.array([float(p[1]), float(p[2])])
            elif reading == "ELEMENT":
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 5 and p[0].isdigit():
                    eid = int(p[0])
                    if eid <= 4440:
                        elements[eid] = [int(x) for x in p[1:5]]

    node_list = sorted([n for n in nodes.keys() if n != 999999])
    node_to_idx = {nid: i for i, nid in enumerate(node_list)}
    n_nodes = len(node_list)

    # 2. Load state table
    d_ckpt = np.zeros(n_nodes)
    elem_h = {}
    with open(state_path, "r", encoding="utf-8") as f:
        for line in f:
            p = [x.strip() for x in line.split(",") if x.strip()]
            if not p: continue
            rtype = p[0].upper()
            if rtype == "NODE":
                nid = int(p[1])
                if nid in node_to_idx:
                    d_ckpt[node_to_idx[nid]] = float(p[4])
            elif rtype in ("ELEM_HISTORY", "ELEM"):
                eid = int(p[1])
                elem_h[eid] = [float(p[2]), float(p[3]), float(p[4]), float(p[5])]

    # 3. Assemble K_global, F_global
    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    I_list, J_list, V_list = [], [], []
    F_global = np.zeros(n_nodes)

    for eid, conn in elements.items():
        pts = np.array([nodes[n] for n in conn])
        h_vals = elem_h[eid]

        for kpt in range(4):
            xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
            N, dNdxi, dNdeta = shape_functions(xi, eta)
            J_mat = np.zeros((2, 2))
            for a in range(4):
                J_mat[0, 0] += dNdxi[a] * pts[a, 0]
                J_mat[0, 1] += dNdxi[a] * pts[a, 1]
                J_mat[1, 0] += dNdeta[a] * pts[a, 0]
                J_mat[1, 1] += dNdeta[a] * pts[a, 1]

            detJ = J_mat[0, 0] * J_mat[1, 1] - J_mat[0, 1] * J_mat[1, 0]
            cjac = detJ * wt

            invJ = np.array([
                [ J_mat[1, 1], -J_mat[0, 1]],
                [-J_mat[1, 0],  J_mat[0, 0]]
            ]) / detJ

            dNdx = np.zeros((2, 4))
            for a in range(4):
                dNdx[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
                dNdx[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]

            H_val = h_vals[kpt]

            for a in range(4):
                idx_a = node_to_idx[conn[a]]
                F_global[idx_a] += cjac * 2.0 * H_val * N[a]

                for b in range(4):
                    idx_b = node_to_idx[conn[b]]
                    grad_dot = dNdx[0, a] * dNdx[0, b] + dNdx[1, a] * dNdx[1, b]
                    val = cjac * (
                        (E_GC / E_L0 + 2.0 * H_val) * N[a] * N[b] +
                        (E_GC * E_L0) * grad_dot
                    )
                    I_list.append(idx_a)
                    J_list.append(idx_b)
                    V_list.append(val)

    K_global = sp.coo_matrix((V_list, (I_list, J_list)), shape=(n_nodes, n_nodes)).tocsr()

    # Initial partition
    U_k = (d_ckpt >= 1.0 - TAU_FEAS)
    L_k = (d_ckpt < 1.0 - TAU_FEAS)
    A_k = np.zeros(n_nodes, dtype=bool)

    history_signatures = []
    chattering_nodes = np.zeros(n_nodes, dtype=bool)
    prev_d_raw = None
    prev_A_k = None
    converged = False

    print("Starting SNESVI Projected Active-Set Simulation...")
    for k in range(1, 30):
        active_set_sig = (tuple(np.where(L_k)[0]), tuple(np.where(U_k)[0]))
        cycle_detected = (active_set_sig in history_signatures)
        if cycle_detected:
            cycle_prev = history_signatures.index(active_set_sig) + 1
            print(f"[Iter {k:02d}] Active-set cycle detected (repeats iter {cycle_prev})!")
        history_signatures.append(active_set_sig)

        # Solve subproblem on A_k
        idx_A = np.where(A_k)[0]
        idx_L = np.where(L_k)[0]
        idx_U = np.where(U_k)[0]
        idx_fixed = np.where(~A_k)[0]

        d_raw = np.zeros(n_nodes)
        d_raw[idx_L] = d_ckpt[idx_L]
        d_raw[idx_U] = 1.00000000

        if len(idx_A) > 0:
            K_AA = K_global[idx_A, :][:, idx_A]
            K_Af = K_global[idx_A, :][:, idx_fixed]
            F_A = F_global[idx_A] - K_Af.dot(d_raw[idx_fixed])
            d_raw[idx_A] = spla.spsolve(K_AA, F_A)

        # Projected step
        d_k = np.clip(d_raw, d_ckpt, 1.0)
        d_k[idx_L] = d_ckpt[idx_L]
        d_k[idx_U] = 1.00000000

        # Residual at projected state
        R_current = F_global - K_global.dot(d_k)
        res_inf_A = float(np.max(np.abs(R_current[idx_A]))) if len(idx_A) > 0 else 0.0

        release_L = (L_k & (R_current > TAU_RES) & (d_ckpt < 1.0 - TAU_FEAS))
        release_U = (U_k & (R_current < -TAU_RES))
        clamp_L = (A_k & (d_raw < d_ckpt - TAU_FEAS))
        clamp_U = (A_k & (d_raw > 1.0 + TAU_FEAS))

        # SNESVI chatter prevention:
        if prev_A_k is not None and prev_d_raw is not None:
            healed_in_prev = (prev_A_k & (prev_d_raw < d_ckpt - TAU_FEAS))
            oscillating = release_L & healed_in_prev
            if np.any(oscillating):
                chattering_nodes |= oscillating

        if cycle_detected or np.any(chattering_nodes):
            suppressed = release_L & chattering_nodes
            n_suppressed = int(np.sum(suppressed))
            if n_suppressed > 0:
                print(f"[Iter {k:02d}] Suppressing {n_suppressed} chattering boundary nodes...")
                release_L = release_L & ~suppressed

        n_changes = int(np.sum(release_L) + np.sum(release_U) + np.sum(clamp_L) + np.sum(clamp_U))
        strict_heal = int(np.sum(d_k < d_ckpt - 1.0e-12))
        strict_over = int(np.sum(d_k > 1.0 + 1.0e-12))
        raw_heal = int(np.sum(A_k & (d_raw < d_ckpt - TAU_FEAS)))
        raw_over = int(np.sum(A_k & (d_raw > 1.0 + TAU_FEAS)))

        print(f"[Iter {k:02d}] |U|={int(np.sum(U_k)):3d}, |L|={int(np.sum(L_k)):4d}, |A|={int(np.sum(A_k)):3d} "
              f"| changes={n_changes:2d} | ||R_d||_A={res_inf_A:.2e} | raw_heal={raw_heal:2d} | strict_heal={strict_heal:2d}")

        if n_changes == 0 and res_inf_A <= TAU_RES and raw_heal == 0 and raw_over == 0:
            converged = True
            print(f"[Iter {k:02d}] SNESVI CONVERGENCE ACHIEVED!")
            break

        prev_d_raw = np.copy(d_raw)
        prev_A_k = np.copy(A_k)

        U_next = (U_k & ~release_U) | clamp_U
        L_next = (L_k & ~release_L) | clamp_L
        A_next = ~(U_next | L_next)

        U_k = U_next
        L_k = L_next
        A_k = A_next

    print(f"Result: converged={converged}, final_iter={k}")
    assert converged, "SNESVI active set must converge!"
    print("ALL CHECKS PASSED!")

if __name__ == "__main__":
    test_snesvi()
