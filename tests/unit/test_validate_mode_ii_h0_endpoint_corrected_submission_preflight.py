#!/usr/bin/env python3
"""Unit tests for Mode-II H0 endpoint-corrected submission preflight validator."""

import json
import tempfile
import unittest
from pathlib import Path

from scripts.model_generation.build_mode_ii_h0_endpoint_corrected_serial import build_package
from scripts.validation.validate_mode_ii_h0_endpoint_corrected_submission_preflight import (
    validate_preflight,
)


class TestValidateModeIIH0EndpointCorrectedSubmissionPreflight(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.pkg_dir = Path(self.tmp_dir.name) / "pkg"
        build_package(self.pkg_dir)

        self.auth_file = Path(self.tmp_dir.name) / "AUTH.json"
        auth_data = {
            "classification": "stage_f_mode_ii_h0_endpoint_corrected_prepared_unauthorized",
            "preparation_complete": True,
            "static_validation_passed": True,
            "datacheck_authorized": False,
            "solver_authorized": False,
            "execution_authorized": False,
            "automatic_retry_authorized": False,
            "mpi_authorized": False,
            "threaded_execution_authorized": False,
            "hybrid_authorized": False,
            "h1_authorized": False,
        }
        self.auth_file.write_text(json.dumps(auth_data, indent=2), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_preflight_preparation_pass(self) -> None:
        res = validate_preflight(self.auth_file, self.pkg_dir, mode="preparation")
        self.assertTrue(res["passed"])
        self.assertEqual(
            res["classification"],
            "stage_f_mode_ii_h0_endpoint_corrected_preflight_preparation_pass",
        )

    def test_preflight_rejects_datacheck_unauthorized(self) -> None:
        res = validate_preflight(self.auth_file, self.pkg_dir, mode="datacheck")
        self.assertFalse(res["passed"])

    def test_preflight_rejects_solver_unauthorized(self) -> None:
        res = validate_preflight(self.auth_file, self.pkg_dir, mode="solver")
        self.assertFalse(res["passed"])


if __name__ == "__main__":
    unittest.main()
