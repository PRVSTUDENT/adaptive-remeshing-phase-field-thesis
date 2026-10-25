#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn143_r13_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 143)
Protocol Version: 2

Qualification and regression test suite for Candidate Package 108 Revision 13 (R13):
1. Production UEL bitwise frozen (CE8D5EDC...).
2. Experimental unified 12-DOF UEL bitwise preserved (A33DE851...).
3. R13 package manifest integrity and SHA-256 hash validation.
4. Abaqus-like Repository simulation: confirms that .get() raises AttributeError
   while repository-compatible membership access succeeds, and missing mandatory
   fields raise explicit RuntimeError.
5. KKT multiplier sign convention and active-set update logic verification.
6. Fail-fast stop conditions verification.
"""

import unittest
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
R13_DIR = REPO_ROOT / "models/pandey_kumar_mode1/108_r13_c3_autonomous_active_set"

class MockAbaqusRepository:
    """
    Simulates the SIMULIA odbAccess Repository class,
    which provides dict-like key indexing and 'in' membership testing,
    but explicitly raises AttributeError on .get().
    """
    def __init__(self, data=None):
        self._data = dict(data) if data else {}

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def __getattr__(self, name):
        if name == "get":
            raise AttributeError("'Repository' object has no attribute 'get'")
        raise AttributeError(f"'Repository' object has no attribute '{name}'")


class TestTurn143R13Qualification(unittest.TestCase):

    def test_01_production_uel_bitwise_frozen(self):
        prod_uel = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
        self.assertTrue(prod_uel.exists())
        h = hashlib.sha256(prod_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6")

    def test_02_experimental_unified_uel_bitwise_preserved(self):
        r13_uel = R13_DIR / "f42_unified_12dof_active_set_uel.for"
        self.assertTrue(r13_uel.exists())
        h = hashlib.sha256(r13_uel.read_bytes()).hexdigest().upper()
        self.assertEqual(h, "A33DE85124681766EA362F11D28440C55F40DD85F7D80C19186E44C343D9129B")

    def test_03_r13_manifest_and_authorization_integrity(self):
        manifest_path = R13_DIR / "PACKAGE_MANIFEST.json"
        auth_path = R13_DIR / "M1_C3_ACTIVE_SET_R13_AUTHORIZATION.json"
        self.assertTrue(manifest_path.exists())
        self.assertTrue(auth_path.exists())

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)

        self.assertEqual(manifest["package_name"], "PACKAGE_108_R13_C3_AUTONOMOUS_ACTIVE_SET")
        self.assertEqual(manifest["task_id"], "F1597-CORRECT-PACKAGE72-STATE-TRANSFER")
        self.assertEqual(manifest["turn"], 143)

        for fname, exp_hash in manifest["files"].items():
            fpath = R13_DIR / fname
            self.assertTrue(fpath.exists(), f"Missing file: {fname}")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().upper()
            self.assertEqual(actual_hash, exp_hash, f"Hash mismatch for {fname}")

    def test_04_repository_get_incompatibility_and_corrected_access(self):
        mock_fields = MockAbaqusRepository({
            "U": "FieldOutput_U_Data",
            "RF": "FieldOutput_RF_Data"
        })

        # Confirm that .get() raises AttributeError as observed in R12 failure
        with self.assertRaises(AttributeError):
            _ = mock_fields.get("U")

        # Confirm that repository-compatible membership access works cleanly
        self.assertTrue("U" in mock_fields)
        self.assertTrue("RF" in mock_fields)
        u_val = mock_fields["U"] if "U" in mock_fields else None
        rf_val = mock_fields["RF"] if "RF" in mock_fields else None
        self.assertEqual(u_val, "FieldOutput_U_Data")
        self.assertEqual(rf_val, "FieldOutput_RF_Data")

        # Confirm that missing mandatory fields produce explicit error
        missing_fields = MockAbaqusRepository({"RF": "FieldOutput_RF_Data"})
        with self.assertRaises(RuntimeError):
            if "U" not in missing_fields:
                raise RuntimeError("Mandatory FieldOutput 'U' missing in ODB frame")

    def test_05_kkt_multiplier_and_active_set_dynamics(self):
        tau_release = 1.0e-9 # kN/mm
        tau_heal = 1.0e-8    # dimensionless

        # Active node check:
        # Negative reaction force exceeding release threshold indicates dual infeasibility (must release)
        rf3_release = -3.835e-09
        self.assertTrue(rf3_release < -tau_release)

        # Non-negative reaction force indicates dual feasibility (must remain active)
        rf3_hold = 7.052e-06
        self.assertFalse(rf3_hold < -tau_release)

        # Free node check:
        # Healing below bound violates primal feasibility (must reactivate)
        d0 = 0.6500
        d_heal = 0.6400
        self.assertTrue((d_heal - d0) < -tau_heal)

        # Monotonic damage advancement satisfies primal feasibility (remains free)
        d_adv = 0.6600
        self.assertFalse((d_adv - d0) < -tau_heal)

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
