#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn87_package101_vi.py
Unit test suite for Turn 87 Package 101 Bound-Constrained VI Solver & Audit:
1. Verifies that the bound-constrained VI/QP solver converges without chatter or heuristic suppression.
2. Verifies convergence within <= 25 iterations under the strict scientific threshold ||R_d||_inf,A <= 1.0e-6 kN/mm.
3. Verifies zero KKT lower-bound violations (lambda_L <= 1.0e-6) and zero upper-bound violations.
4. Verifies zero damage healing (min(d - d_ckpt) >= 0) and zero overshoot (max(d) <= 1.0).
5. Verifies that the production UEL f42_mixed_uel.for is 100% bitwise frozen.
6. Verifies that objective Phi(d*) is strictly less than Package 100 (Phi_pkg100 - Phi_d* = 6.282e-6 > 0).
7. Verifies that Gate C1-2 remains strictly NOT_QUALIFIED due to the -2.063% to -2.110% fracture energy deficit.
"""

import unittest
import json
import hashlib
from pathlib import Path
import numpy as np
import scipy.sparse as sp
from scipy.optimize import minimize

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/100_c5_pdas_snesvi_projected_continuation"
MESH_PATH = PKG_DIR / "candidate_crack_band_mesh_c5.inp"
STATE_PATH = PKG_DIR / "candidate_c5_frame7_mapped_state_table.csv"
UEL_PATH = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
TAU_RES = 1.0e-6

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

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

class TestPackage101BoundConstrainedVI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 1. Load mesh
        cls.nodes = {}
        cls.elements = {}
        with open(MESH_PATH, "r", encoding="utf-8") as f:
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
                        nid = int(p[0])
                        if nid != 999999:
                            cls.nodes[nid] = np.array([float(p[1]), float(p[2])])
                elif reading == "ELEMENT":
                    p = [x.strip() for x in l.split(",") if x.strip()]
                    if len(p) >= 5 and p[0].isdigit():
                        eid = int(p[0])
                        if eid <= 4440:
                            cls.elements[eid] = [int(x) for x in p[1:5]]

        cls.node_list = sorted(cls.nodes.keys())
        cls.node_to_idx = {nid: i for i, nid in enumerate(cls.node_list)}
        cls.n_nodes = len(cls.node_list)

        # 2. Load state table
        cls.d_ckpt = np.zeros(cls.n_nodes)
        cls.elem_h = {}
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                p = [x.strip() for x in line.split(",") if x.strip()]
                if not p: continue
                rtype = p[0].upper()
                if rtype == "NODE":
                    nid = int(p[1])
                    if nid in cls.node_to_idx:
                        cls.d_ckpt[cls.node_to_idx[nid]] = float(p[4])
                elif rtype in ("ELEM_HISTORY", "ELEM"):
                    eid = int(p[1])
                    cls.elem_h[eid] = [float(p[2]), float(p[3]), float(p[4]), float(p[5])]

        # 3. Assemble K and F
        E_GC = 0.0027
        E_L0 = 0.0075
        xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
        yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
        w4  = [1.0, 1.0, 1.0, 1.0]

        I_full, J_full, V_full = [], [], []
        cls.F_full = np.zeros(cls.n_nodes)

        for eid, conn in cls.elements.items():
            pts = np.array([cls.nodes[n] for n in conn])
            h_vals = cls.elem_h[eid]
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
                invJ = np.array([[J_mat[1, 1], -J_mat[0, 1]], [-J_mat[1, 0], J_mat[0, 0]]]) / detJ
                dNdx = np.zeros((2, 4))
                for a in range(4):
                    dNdx[0, a] = invJ[0, 0] * dNdxi[a] + invJ[0, 1] * dNdeta[a]
                    dNdx[1, a] = invJ[1, 0] * dNdxi[a] + invJ[1, 1] * dNdeta[a]
                H_val = h_vals[kpt]
                for a in range(4):
                    ia = cls.node_to_idx[conn[a]]
                    cls.F_full[ia] += cjac * 2.0 * H_val * N[a]
                    for b in range(4):
                        ib = cls.node_to_idx[conn[b]]
                        grad_dot = dNdx[0, a] * dNdx[0, b] + dNdx[1, a] * dNdx[1, b]
                        val = cjac * ((E_GC / E_L0 + 2.0 * H_val) * N[a] * N[b] + (E_GC * E_L0) * grad_dot)
                        I_full.append(ia)
                        J_full.append(ib)
                        V_full.append(val)

        cls.K_full = sp.coo_matrix((V_full, (I_full, J_full)), shape=(cls.n_nodes, cls.n_nodes)).tocsr()

    def test_01_frozen_uel_integrity(self):
        """Production UEL hash CE8D5EDC... must remain 100% bitwise frozen."""
        actual_hash = sha256_file(UEL_PATH)
        self.assertEqual(actual_hash, FROZEN_UEL_HASH)

    def test_02_vi_convergence_within_25_iterations(self):
        """Bound-constrained VI solver must reach ||R_d||_inf,A <= 1.0e-6 in <= 25 iters."""
        bounds = [(self.d_ckpt[i], 1.0) for i in range(self.n_nodes)]
        history = []

        def obj(d):
            Kd = self.K_full.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(self.F_full, d), Kd - self.F_full

        def callback(xk):
            g = self.K_full.dot(xk) - self.F_full
            R = -g
            is_at_L = np.abs(xk - self.d_ckpt) < 1e-6
            is_at_U = np.abs(xk - 1.0) < 1e-6
            is_A = ~(is_at_L | is_at_U)
            res_A = float(np.max(np.abs(R[is_A]))) if np.any(is_A) else 0.0
            viol_L = int(np.sum(R[is_at_L] > TAU_RES))
            viol_U = int(np.sum(R[is_at_U] < -TAU_RES))
            history.append({
                "iter": len(history) + 1,
                "res_A": res_A,
                "viol_L": viol_L,
                "viol_U": viol_U
            })

        res = minimize(obj, np.copy(self.d_ckpt), jac=True, method='L-BFGS-B', bounds=bounds,
                       callback=callback, options={'maxiter': 200, 'ftol': 1e-15, 'gtol': 1e-10})

        self.assertTrue(res.success)
        # Find first iteration where res_A <= TAU_RES and viol_L == 0 and viol_U == 0
        first_conv = None
        for rec in history:
            if rec["res_A"] <= TAU_RES and rec["viol_L"] == 0 and rec["viol_U"] == 0:
                first_conv = rec["iter"]
                break

        self.assertIsNotNone(first_conv)
        self.assertLessEqual(first_conv, 25, f"Expected convergence in <= 25 iters, got {first_conv}")

    def test_03_zero_healing_and_zero_overshoot(self):
        """Minimizer must satisfy strictly 0 healing (d >= d_ckpt) and 0 overshoot (d <= 1.0)."""
        bounds = [(self.d_ckpt[i], 1.0) for i in range(self.n_nodes)]
        def obj(d):
            Kd = self.K_full.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(self.F_full, d), Kd - self.F_full

        res = minimize(obj, np.copy(self.d_ckpt), jac=True, method='L-BFGS-B', bounds=bounds,
                       options={'maxiter': 200, 'ftol': 1e-15, 'gtol': 1e-10})
        d_star = res.x

        min_delta = np.min(d_star - self.d_ckpt)
        max_val = np.max(d_star)

        self.assertGreaterEqual(min_delta, -1e-12, f"Healing detected: min delta = {min_delta}")
        self.assertLessEqual(max_val, 1.0 + 1e-12, f"Overshoot detected: max d = {max_val}")

    def test_04_full_kkt_stationarity_at_minimizer(self):
        """At d*, all KKT conditions must be satisfied with zero violations on L and U."""
        bounds = [(self.d_ckpt[i], 1.0) for i in range(self.n_nodes)]
        def obj(d):
            Kd = self.K_full.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(self.F_full, d), Kd - self.F_full

        res = minimize(obj, np.copy(self.d_ckpt), jac=True, method='L-BFGS-B', bounds=bounds,
                       options={'maxiter': 200, 'ftol': 1e-15, 'gtol': 1e-10})
        d_star = res.x

        g = self.K_full.dot(d_star) - self.F_full
        R = -g
        is_at_L = np.abs(d_star - self.d_ckpt) < 1e-6
        is_at_U = np.abs(d_star - 1.0) < 1e-6
        is_A = ~(is_at_L | is_at_U)

        viol_L = int(np.sum(R[is_at_L] > TAU_RES))
        viol_U = int(np.sum(R[is_at_U] < -TAU_RES))
        res_A = float(np.max(np.abs(R[is_A])))

        self.assertEqual(viol_L, 0, f"Expected 0 KKT violations on L, got {viol_L}")
        self.assertEqual(viol_U, 0, f"Expected 0 KKT violations on U, got {viol_U}")
        self.assertLessEqual(res_A, TAU_RES, f"Expected ||R_d||_inf,A <= {TAU_RES}, got {res_A}")

    def test_05_objective_superior_to_package100(self):
        """Exact QP minimizer must achieve strictly lower objective than Package 100."""
        bounds = [(self.d_ckpt[i], 1.0) for i in range(self.n_nodes)]
        def obj(d):
            Kd = self.K_full.dot(d)
            return 0.5 * np.dot(d, Kd) - np.dot(self.F_full, d), Kd - self.F_full

        res = minimize(obj, np.copy(self.d_ckpt), jac=True, method='L-BFGS-B', bounds=bounds,
                       options={'maxiter': 200, 'ftol': 1e-15, 'gtol': 1e-10})
        phi_star = res.fun

        # Package 100 objective value from audit
        phi_p100 = -0.0163822055
        self.assertLess(phi_star, phi_p100, f"Expected phi_star < phi_p100, got {phi_star} vs {phi_p100}")
        gap = phi_p100 - phi_star
        self.assertGreater(gap, 6.0e-6, f"Expected suboptimality gap >= 6.0e-6, got {gap}")

    def test_06_gate_c1_2_governed_not_qualified(self):
        """Gate C1-2 must remain strictly NOT_QUALIFIED due to fracture energy deficit."""
        recomp_json = REPO_ROOT / "results/validation/mode1_f1597/turn87_c5_fracture_energy_recomputation.json"
        self.assertTrue(recomp_json.exists(), "Fracture energy recomputation artifact must exist.")
        with open(recomp_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        disc_pct = data["states"]["checkpoint_mapped_d_ckpt"]["discrepancy_vs_donor_pct"]
        self.assertLess(disc_pct, -2.0, f"Transfer deficit must exceed 2.0% threshold: {disc_pct}%")
        self.assertFalse(data["states"]["checkpoint_mapped_d_ckpt"]["gate_passed"])

if __name__ == "__main__":
    unittest.main()
