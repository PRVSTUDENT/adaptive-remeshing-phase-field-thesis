#!/usr/bin/env python3
"""Unit tests for the solver staging smoke script."""

import sys
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SMOKE_SCRIPT = ROOT / "scripts" / "validation" / "run_mode_ii_h0_endpoint_corrected_solver_staging_smoke.py"


import tempfile

class TestRunModeIIH0EndpointCorrectedSolverStagingSmoke(unittest.TestCase):
    """Unit test suite for run_mode_ii_h0_endpoint_corrected_solver_staging_smoke.py."""

    def test_smoke_pass(self):
        """Smoke script returns exit code 0 and pass classification."""
        with tempfile.TemporaryDirectory() as tmp:
            res = subprocess.run(
                [sys.executable, str(SMOKE_SCRIPT), "--evidence-dir", str(tmp)],
                cwd=str(ROOT),
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0)
            self.assertIn("stage_f_mode_ii_h0_endpoint_corrected_solver_local_staging_smoke_pass", res.stdout)


if __name__ == "__main__":
    unittest.main()
