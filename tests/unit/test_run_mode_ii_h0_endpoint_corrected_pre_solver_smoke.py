#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected pre-solver smoke script."""

import tempfile
import unittest
from pathlib import Path

from scripts.validation.run_mode_ii_h0_endpoint_corrected_pre_solver_smoke import (
    run_smoke,
    verify_evidence_bundle,
)


class TestRunModeIIH0EndpointCorrectedPreSolverSmoke(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.out_dir = Path(self.tmp_dir.name) / "smoke"

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_run_smoke_and_verify_bundle(self) -> None:
        rc, summary = run_smoke(self.out_dir)
        self.assertEqual(rc, 0)
        self.assertTrue(summary["passed"])
        self.assertEqual(
            summary["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_pre_solver_smoke_pass",
        )

        v_rc, v_res = verify_evidence_bundle(self.out_dir)
        self.assertEqual(v_rc, 0)
        self.assertEqual(
            v_res["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_smoke_evidence_complete",
        )


if __name__ == "__main__":
    unittest.main()
