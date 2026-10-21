"""Unit test for Package 72 state transfer root cause evaluation script."""
import json
import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from evaluate_mode1_f1597_root_cause import evaluate_state_transfer_defect


class TestMode1F1597RootCause(unittest.TestCase):
    def test_root_cause_evaluation(self):
        res = evaluate_state_transfer_defect(REPO_ROOT)
        self.assertEqual(res["schema"], 1)
        self.assertEqual(res["status"], "PREPARATION_COMPLETE")
        self.assertTrue(res["verification_passed"])
        self.assertGreaterEqual(len(res["finding"].strip()), 20)
        self.assertIn("evidence_sources", res)
        self.assertGreaterEqual(len(res["evidence_sources"]), 5)

        # Check evidence sources exist and match
        import hashlib
        for rel_path, expected_hash in res["evidence_sources"].items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Missing file: {rel_path}")
            self.assertLessEqual(full_path.stat().st_size, 16777216)
            with open(full_path, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest()
            self.assertEqual(actual_hash.upper(), expected_hash, f"Hash mismatch for {rel_path}")

        m = res["measurements"]
        self.assertAlmostEqual(m["force_deficit_vs_donor_pct"], -77.73263699317796, places=4)
        self.assertEqual(m["healing_node_count"], 291)
        self.assertGreater(m["el336_mechanical_history_gp2_kN_mm2"], m["el336_initial_history_gp2_kN_mm2"])
        self.assertGreater(m["el336_delta_phase"], 0.0)


if __name__ == "__main__":
    unittest.main()
