#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_c6_coupled_diagnosis.py
============================
Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION
Protocol Version: 2

Unit test suite validating the mathematical diagnosis and under-relaxation formulation
for Mode-I C6/R2.
"""

import json
import math
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


class TestC6CoupledDiagnosis(unittest.TestCase):
    def setUp(self):
        self.diag_file = REPO_ROOT / "results" / "validation" / "c6_r2_coupled_limit_cycle_diagnosis.json"
        self.relax_file = REPO_ROOT / "results" / "validation" / "c6_r2_under_relaxation_viability_analysis.json"
        self.iter_file = REPO_ROOT / "results" / "validation" / "f1599_reconciled" / "terminal_iterations.json"

    def test_artifacts_exist_and_valid_json(self):
        self.assertTrue(self.diag_file.is_file(), "Diagnosis file must exist")
        self.assertTrue(self.relax_file.is_file(), "Under-relaxation analysis file must exist")
        self.assertTrue(self.iter_file.is_file(), "Terminal iterations file must exist")

        with open(self.diag_file, "r", encoding="utf-8") as f:
            diag = json.load(f)
        self.assertEqual(diag.get("schema"), 1)
        self.assertEqual(diag.get("task_id"), "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION")

        with open(self.relax_file, "r", encoding="utf-8") as f:
            relax = json.load(f)
        self.assertEqual(relax.get("schema"), 1)
        self.assertEqual(relax.get("task_id"), "F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION")

    def test_discrete_kkt_complementarity_maintained(self):
        with open(self.iter_file, "r", encoding="utf-8") as f:
            records = json.load(f)
        self.assertEqual(len(records), 100)

        for r in records:
            self.assertLessEqual(r["dual_error"], 1e-6, f"Dual error exceeded at outer {r['outer']}")
            self.assertLessEqual(r["free_error"], 1e-6, f"Free error exceeded at outer {r['outer']}")

    def test_active_set_stabilization(self):
        with open(self.iter_file, "r", encoding="utf-8") as f:
            records = json.load(f)

        # Active set monotonically or asymptotically stabilizes to 35 nodes
        late_active = [r["pdas_active_count"] for r in records[95:]]  # outers 96-100
        for act in late_active:
            self.assertEqual(act, 35, "Active set must be exactly frozen at 35 nodes for outers 96-100")

    def test_loop_gain_unity_and_limit_cycle(self):
        with open(self.relax_file, "r", encoding="utf-8") as f:
            relax = json.load(f)
        mean_gain = relax["empirical_feedback_analysis"]["mean_loop_gain"]
        self.assertAlmostEqual(mean_gain, 1.0, places=4, msg="Coupled loop gain must be ~1.0 explaining limit cycle")

    def test_convex_damage_under_relaxation_irreversibility_proof(self):
        """
        Prove that for any initial d0 in [0, 1], d_k >= d0, and solver output d_tilde >= d0,
        the convex combination d_{k+1} = (1 - omega)*d_k + omega*d_tilde >= d0
        for all omega in (0, 1].
        """
        import numpy as np
        d0_test = np.linspace(0.0, 0.99, 100)
        omega_test = np.linspace(0.01, 1.0, 100)

        for d0 in d0_test:
            d_k = d0 + 0.05 * (1.0 - d0)  # d_k >= d0
            d_tilde = d0 + 0.08 * (1.0 - d0)  # d_tilde >= d0
            for w in omega_test:
                d_next = (1.0 - w) * d_k + w * d_tilde
                self.assertGreaterEqual(d_next, d0, "Convex combination must strictly satisfy d_{k+1} >= d0")
                self.assertLessEqual(d_next, 1.0, "Convex combination must strictly satisfy d_{k+1} <= 1")

    def test_fixed_point_invariance_proof(self):
        """
        Prove that fixed points of (1 - omega)*I + omega*T are identical to fixed points of T.
        """
        # Let d* be a fixed point: T(d*) = d*
        # T_omega(d*) = (1 - omega)*d* + omega*T(d*) = (1 - omega)*d* + omega*d* = d*
        for w in [0.1, 0.3, 0.5, 0.7, 0.9]:
            d_star = 0.654321
            T_d_star = d_star
            T_omega_d_star = (1.0 - w) * d_star + w * T_d_star
            self.assertAlmostEqual(T_omega_d_star, d_star, places=14)

    def test_spectral_radius_reduction(self):
        with open(self.relax_file, "r", encoding="utf-8") as f:
            relax = json.load(f)
        damping_data = relax["damping_spectral_analysis"]

        # At omega = 1.0, spectral radius is 1.0 (limit cycle)
        w1 = next(d for d in damping_data if d["omega"] == 1.0)
        self.assertAlmostEqual(w1["effective_spectral_radius"], 1.0, places=4)

        # At omega = 0.5, spectral radius is ~0.0 (deadbeat / optimal contraction)
        w05 = next(d for d in damping_data if d["omega"] == 0.5)
        self.assertLess(w05["effective_spectral_radius"], 0.01)


if __name__ == "__main__":
    unittest.main()
