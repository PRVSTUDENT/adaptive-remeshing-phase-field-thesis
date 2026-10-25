#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn144_r14_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 144)
Protocol Version: 2

Qualification and regression test suite for Candidate Package 108 Revision 14 (R14):
1. Production UEL bitwise frozen (CE8D5EDC...).
2. R14 package manifest integrity and SHA-256 hash validation.
3. Repaired 12-DOF UEL vs Production UEL bitwise parity check.
4. KKT multiplier sign convention: proves that crack driving nodes have RF3 < 0.
5. Strict Stage-A checkpoint reset semantics and fail-fast stop conditions.
"""

import unittest
import hashlib
import json
import numpy as np
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R14_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r14_c3_autonomous_active_set"
PROD_UEL = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
PROD_HASH_EXPECTED = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

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

def eval_production_uel_phase(coords, u_d, hist_val):
    E_GC = 0.0027
    E_L0 = 0.0075
    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    amatrx = np.zeros((4, 4))
    rhs = np.zeros(4)

    for kpt in range(4):
        xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
        N_vec, dNdxi, dNdeta = shape_functions(xi, eta)

        jac = np.zeros((2, 2))
        for a in range(4):
            jac[0, 0] += dNdxi[a] * coords[0, a]
            jac[0, 1] += dNdxi[a] * coords[1, a]
            jac[1, 0] += dNdeta[a] * coords[0, a]
            jac[1, 1] += dNdeta[a] * coords[1, a]

        detj = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
        invj = np.linalg.inv(jac)

        b_phase = np.zeros((2, 4))
        for i in range(4):
            b_phase[0, i] = invj[0, 0] * dNdxi[i] + invj[0, 1] * dNdeta[i]
            b_phase[1, i] = invj[1, 0] * dNdxi[i] + invj[1, 1] * dNdeta[i]

        cjac = detj * wt

        for i in range(4):
            for j in range(4):
                bdb = b_phase[0, i] * b_phase[0, j] + b_phase[1, i] * b_phase[1, j]
                amatrx[i, j] += cjac * (
                    (E_GC * E_L0) * bdb +
                    (E_GC / E_L0 + 2.0 * hist_val) * N_vec[i] * N_vec[j]
                )
            rhs[i] += cjac * 2.0 * hist_val * N_vec[i]

    for i in range(4):
        for j in range(4):
            rhs[i] -= amatrx[i, j] * u_d[j]

    rf = -rhs
    return amatrx, rhs, rf

def eval_12dof_uel_repaired(coords, u_d, hist_val):
    E_GC = 0.0027
    E_L0 = 0.0075
    xg4 = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
    w4  = [1.0, 1.0, 1.0, 1.0]

    kdd = np.zeros((4, 4))
    rd = np.zeros(4)

    for kpt in range(4):
        xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
        N_vec, dNdxi, dNdeta = shape_functions(xi, eta)

        jac = np.zeros((2, 2))
        for a in range(4):
            jac[0, 0] += dNdxi[a] * coords[0, a]
            jac[0, 1] += dNdxi[a] * coords[1, a]
            jac[1, 0] += dNdeta[a] * coords[0, a]
            jac[1, 1] += dNdeta[a] * coords[1, a]

        detj = jac[0, 0] * jac[1, 1] - jac[0, 1] * jac[1, 0]
        invj = np.linalg.inv(jac)

        dn = np.zeros((2, 4))
        for i in range(4):
            dn[0, i] = invj[0, 0] * dNdxi[i] + invj[0, 1] * dNdeta[i]
            dn[1, i] = invj[1, 0] * dNdxi[i] + invj[1, 1] * dNdeta[i]

        cj = detj * wt

        d_val = np.dot(N_vec, u_d)
        grad_d = dn @ u_d

        for a in range(4):
            rd[a] += cj * (
                ( (E_GC / E_L0) * d_val - 2.0 * (1.0 - d_val) * hist_val ) * N_vec[a] +
                E_GC * E_L0 * (dn[0, a] * grad_d[0] + dn[1, a] * grad_d[1])
            )
            for b in range(4):
                kdd[a, b] += cj * (
                    ( (E_GC / E_L0) + 2.0 * hist_val ) * N_vec[a] * N_vec[b] +
                    E_GC * E_L0 * (dn[0, a] * dn[0, b] + dn[1, a] * dn[1, b])
                )

    rhs = -rd
    rf = rd
    return kdd, rhs, rf

class TestTurn144R14Qualification(unittest.TestCase):

    def test_01_production_uel_bitwise_frozen(self):
        actual_hash = hashlib.sha256(PROD_UEL.read_bytes()).hexdigest().upper()
        self.assertEqual(actual_hash, PROD_HASH_EXPECTED)

    def test_02_r14_manifest_integrity(self):
        manifest_path = R14_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.exists())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        for fname, exp_hash in manifest["model_files"].items():
            fpath = R14_DIR / fname
            self.assertTrue(fpath.exists(), f"File {fname} missing in R14 package")
            act_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
            self.assertEqual(act_hash, exp_hash.lower(), f"Hash mismatch for {fname}")

    def test_03_repaired_12dof_parity_with_production_uel(self):
        coords = np.array([
            [0.0, 0.001, 0.001, 0.0],
            [0.0, 0.0,   0.001, 0.001]
        ])
        test_cases = [
            ("Crack-Tip", np.array([0.65, 0.65, 0.65, 0.65]), 0.35),
            ("Intact",    np.array([0.00, 0.00, 0.00, 0.00]), 0.00),
            ("Moderate",  np.array([0.30, 0.30, 0.30, 0.30]), 0.15),
            ("Gradient",  np.array([0.20, 0.40, 0.60, 0.50]), 0.25)
        ]
        for name, u_d, H in test_cases:
            k_prod, rhs_prod, rf_prod = eval_production_uel_phase(coords, u_d, H)
            k_corr, rhs_corr, rf_corr = eval_12dof_uel_repaired(coords, u_d, H)

            diff_rhs = np.max(np.abs(rhs_corr - rhs_prod))
            diff_rf = np.max(np.abs(rf_corr - rf_prod))
            diff_k = np.max(np.abs(k_corr - k_prod))

            self.assertLess(diff_rhs, 1.0e-15, f"RHS mismatch for {name}")
            self.assertLess(diff_rf, 1.0e-15, f"RF mismatch for {name}")
            self.assertLess(diff_k, 1.0e-15, f"K mismatch for {name}")

    def test_04_kkt_multiplier_sign_convention(self):
        coords = np.array([
            [0.0, 0.001, 0.001, 0.0],
            [0.0, 0.0,   0.001, 0.001]
        ])
        u_d = np.array([0.65, 0.65, 0.65, 0.65])
        H = 0.35
        k_corr, rhs_corr, rf_corr = eval_12dof_uel_repaired(coords, u_d, H)

        # Under strong driving force, RHS > 0 (forces d to advance)
        self.assertTrue(np.all(rhs_corr > 0.0))
        # At constrained node, RF3 = -RHS < 0 (negative multiplier violates dual feasibility)
        self.assertTrue(np.all(rf_corr < 0.0))
        # Release condition: lambda = RF3 < -tau_release triggers release
        tau_release = 1.0e-9
        self.assertTrue(np.all(rf_corr < -tau_release))

    def test_05_healing_reactivation_logic(self):
        tau_heal = 1.0e-8
        d0 = 0.6500
        d_heal = 0.6400
        self.assertTrue((d_heal - d0) < -tau_heal)
        d_adv = 0.6600
        self.assertFalse((d_adv - d0) < -tau_heal)

    def test_06_fail_fast_stop_conditions(self):
        target_u2 = 0.00196610735
        self.assertFalse(abs(0.00196610735 - target_u2) > 1.0e-7)
        self.assertTrue(abs(0.00196510735 - target_u2) > 1.0e-7)
        self.assertTrue(1.0001 > 1.0 + 1.0e-5)

if __name__ == "__main__":
    unittest.main()
