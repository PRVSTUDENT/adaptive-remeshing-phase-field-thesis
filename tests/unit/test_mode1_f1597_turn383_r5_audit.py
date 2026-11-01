#!/usr/bin/env python3
"""
Unit test for Turn 383: Package 158 R5 convergence telemetry through outer iteration 9.
Verifies monotonic decrease in increments, KKT error bounds, and force/energy gate compliance.
"""

import json
import sys
import unittest
from pathlib import Path

class TestPackage158R5Turn383Audit(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.audit_script = self.repo_root / "scripts/validation/audit_package158_r5_turn383.py"
        self.turn_id = "100feefa-5fb5-4c65-b08f-10d9f8c3c394"

    def test_audit_execution(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, str(self.audit_script)],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True
        )
        self.assertEqual(result.returncode, 0, f"Audit script failed: {result.stderr}")

        prep_path = self.repo_root / f"results/validation/preparation-{self.turn_id}.json"
        self.assertTrue(prep_path.is_file(), f"Missing preparation file: {prep_path}")

        prep_data = json.loads(prep_path.read_text(encoding="utf-8"))
        self.assertEqual(prep_data["schema"], 1)
        self.assertEqual(prep_data["status"], "PREPARATION_COMPLETE")
        self.assertTrue(prep_data["verification_passed"])
        self.assertGreaterEqual(len(prep_data["finding"]), 20)

        # Measurements check
        meas = prep_data["measurements"]
        self.assertEqual(meas["outer_iterations_completed"], 9)
        self.assertTrue(meas["delta_d_monotonic_reduction"])
        self.assertTrue(meas["delta_h_monotonic_reduction"])
        self.assertTrue(meas["delta_u_monotonic_reduction"])
        self.assertTrue(meas["kkt_complementarity_satisfied"])
        self.assertTrue(meas["force_gate_passed"])
        self.assertTrue(meas["energy_gate_passed"])

        # Check values
        self.assertLess(meas["outer_9_delta_d"], 0.0021)
        self.assertLess(meas["outer_9_free_error"], 1e-7)
        self.assertLess(meas["outer_9_dual_error"], 1e-8)
        self.assertLess(meas["outer_9_force_error_pct"], 5.0)
        self.assertLess(meas["outer_9_energy_error_pct"], 2.0)

if __name__ == "__main__":
    import sys
    unittest.main()
