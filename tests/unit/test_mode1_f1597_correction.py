"""Unit tests for F1597 constrained coupled state-transfer correction prototype."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from correct_mode1_f1597_state_transfer import run_coupled_correction, TOLERANCES


class TestMode1F1597CoupledCorrection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run_coupled_correction(REPO_ROOT)

    def test_schema_and_status(self):
        res = self.result
        self.assertEqual(res["schema"], 1)
        self.assertEqual(res["status"], "PREPARATION_COMPLETE")
        self.assertTrue(res["verification_passed"])
        self.assertGreaterEqual(len(res["finding"].strip()), 20)
        self.assertIn("measurements", res)
        self.assertIn("convergence_history", res)
        self.assertIn("evidence_sources", res)

    def test_active_set_zero_healing(self):
        m = self.result["measurements"]
        # In Package 72, 291 nodes healed with min delta_d = -0.001661
        self.assertEqual(m["pkg72_unconstrained_healing_nodes"], 291)
        self.assertLess(m["pkg72_unconstrained_min_delta_d"], -0.001)

        # Under PDAS constrained solve, healing violation is zero
        self.assertLessEqual(m["coupled_final_healing_violation"], TOLERANCES["healing_violation"])
        self.assertEqual(m["coupled_final_healing_nodes"], 0)
        self.assertGreaterEqual(m["coupled_final_kkt_active_mult_min_kN"], TOLERANCES["kkt_active_multiplier_min_kN"])
        self.assertLessEqual(m["coupled_final_kkt_inactive_res_max_kN"], TOLERANCES["kkt_inactive_residual_kN"])

    def test_mechanical_free_residual(self):
        m = self.result["measurements"]
        self.assertLessEqual(m["coupled_final_free_residual_kN"], TOLERANCES["mechanical_residual_kN"])

    def test_crack_tip_strain_surge_mechanism(self):
        m = self.result["measurements"]
        # Confirms the 2.09x surge at element 336 gp 2
        self.assertAlmostEqual(m["el336_gp2_initial_strain_surge_ratio"], 2.086, places=2)
        self.assertGreater(m["coupled_final_el336_gp2_psi0_kN_mm2"], m["el336_gp2_donor_history_kN_mm2"])

    def test_governance_thresholds_offline_retention(self):
        m = self.result["measurements"]
        # Retain the 5% force and 2% fracture energy thresholds
        # Offline evidence alone must NOT claim these have passed
        self.assertGreater(abs(m["force_continuity_error_pct"]), TOLERANCES["force_continuity_threshold_pct"])
        self.assertGreater(abs(m["fracture_energy_error_pct"]), TOLERANCES["fracture_energy_threshold_pct"])

    def test_evidence_sources_integrity(self):
        sources = self.result["evidence_sources"]
        self.assertGreaterEqual(len(sources), 5)
        for rel_path, expected_hash in sources.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Missing evidence file: {rel_path}")
            self.assertLessEqual(full_path.stat().st_size, 16777216)
            actual_hash = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {rel_path}")


if __name__ == "__main__":
    unittest.main()
