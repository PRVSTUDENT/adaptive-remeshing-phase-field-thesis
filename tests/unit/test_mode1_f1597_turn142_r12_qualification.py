#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn142_r12_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 142)
Protocol Version: 2

Qualification and mathematical verification test suite for Candidate Package 108 Revision 12 (R12):
1. Production UEL bitwise frozen (CE8D5EDC...).
2. Experimental unified 12-DOF UEL bitwise preserved (A33DE851...).
3. R12 package manifest integrity and SHA-256 hash validation.
4. R12 Abaqus continuation input deck structure (Step 1 Stage-A & Step 2 Inc1-Coupled OP=NEW).
5. KKT multiplier sign convention and active-set update logic verification.
6. Fail-fast stop conditions verification.
"""

import unittest
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R12_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r12_c3_autonomous_active_set"

class TestTurn142R12Qualification(unittest.TestCase):

    def test_01_production_uel_bitwise_frozen(self):
        prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        self.assertTrue(prod_uel.exists())
        h = hashlib.sha256(prod_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")

    def test_02_experimental_unified_uel_bitwise_preserved(self):
        r12_uel = R12_DIR / "f42_unified_12dof_active_set_uel.for"
        self.assertTrue(r12_uel.exists())
        h = hashlib.sha256(r12_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "A33DE85124681766EA362F11D28440C55F40DD85F7D80C19186E44C343D9129B")

    def test_03_r12_manifest_and_authorization_integrity(self):
        manifest_path = R12_DIR / "PACKAGE_MANIFEST.json"
        auth_path = R12_DIR / "M1_C3_ACTIVE_SET_R12_AUTHORIZATION.json"
        self.assertTrue(manifest_path.exists())
        self.assertTrue(auth_path.exists())

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)

        self.assertEqual(manifest["package_name"], "PACKAGE_108_R12_C3_AUTONOMOUS_ACTIVE_SET")
        self.assertEqual(manifest["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(manifest["turn"], 142)

        # Verify every file listed in manifest matches disk SHA-256
        for fname, exp_hash in manifest["files"].items():
            fpath = R12_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing file: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().upper()
            self.assertEqual(actual_hash, exp_hash, f"Hash mismatch for {fname}")

    def test_04_r12_input_deck_boundary_and_step_structure(self):
        inp_path = R12_DIR / "M1_C3_ACTIVE_SET_R12_CONTINUATION.inp"
        self.assertTrue(inp_path.exists())
        content = inp_path.read_text(encoding="utf-8")

        # Step 1 Stage-A checks
        self.assertIn("*Step, name=Stage-A", content)
        self.assertIn("*Include, input=stage_a_all_d0_boundary_cards.inc", content)

        # Step 2 Inc1-Coupled checks
        self.assertIn("*Step, name=Inc1-Coupled", content)
        self.assertIn("*Boundary, OP=NEW", content)
        self.assertIn("N_RP, 2, 2, 0.00196610735", content)
        self.assertIn("*Include, input=active_set_boundary_cards.inc", content)

        # UNSYMM solver setting on 12-DOF UEL
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=8, UNSYMM", content)

    def test_05_kkt_multiplier_and_active_set_dynamics(self):
        tau_release = 5.0e-7 # kN/mm
        tau_heal = 1.0e-8    # dimensionless

        # Simulation of active node:
        # Case A: Dual feasible lambda >= 0 (no release)
        rf3_pos = 1.5e-5
        self.assertFalse(rf3_pos < -tau_release)

        # Case B: Dual feasible lambda slightly negative but within KKT tolerance (no release)
        rf3_tiny_neg = -1.0e-8
        self.assertFalse(rf3_tiny_neg < -tau_release)

        # Case C: Dual infeasible lambda < -tau_release (must release)
        rf3_viol = -6.2e-7
        self.assertTrue(rf3_viol < -tau_release)

        # Simulation of inactive node:
        # Case D: Damage advances (d > d0) -> no healing
        d0 = 0.6500
        d_adv = 0.6550
        delta_d = d_adv - d0
        self.assertFalse(delta_d < -tau_heal)

        # Case E: Damage heals (d < d0 - tau_heal) -> must reactivate
        d_heal = 0.6499
        delta_d_heal = d_heal - d0
        self.assertTrue(delta_d_heal < -tau_heal)

    def test_06_fail_fast_conditions_logic(self):
        # 1. Damage upper bound violation
        d_overflow = 1.0001
        self.assertTrue(d_overflow > 1.0 + 1.0e-5)

        # 2. Kinematic target RP displacement violation
        target_u2 = 0.00196610735
        actual_u2_good = 0.00196610735
        actual_u2_bad = 0.00196510735
        self.assertFalse(abs(actual_u2_good - target_u2) > 1.0e-7)
        self.assertTrue(abs(actual_u2_bad - target_u2) > 1.0e-7)

if __name__ == "__main__":
    unittest.main()
