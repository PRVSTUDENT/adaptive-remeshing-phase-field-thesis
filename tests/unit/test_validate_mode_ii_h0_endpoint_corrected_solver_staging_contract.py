#!/usr/bin/env python3
"""Unit tests for the static solver staging contract validator."""

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = ROOT / "scripts" / "validation" / "validate_mode_ii_h0_endpoint_corrected_solver_staging_contract.py"


class TestValidateModeIIH0EndpointCorrectedSolverStagingContract(unittest.TestCase):
    """Unit test suite for validate_mode_ii_h0_endpoint_corrected_solver_staging_contract.py."""

    def test_validator_pass(self):
        """Validator returns exit code 0 and pass classification."""
        res = subprocess.run(
            ["python", str(VALIDATOR), "--json"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0)
        self.assertIn("stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_pass", res.stdout)


if __name__ == "__main__":
    unittest.main()
