"""Unit tests for validate_mode_ii_h0_endpoint_corrected_staging_contract.py."""

from __future__ import annotations

import pathlib
import unittest

from scripts.validation.validate_mode_ii_h0_endpoint_corrected_staging_contract import (
    CLASSIFICATION_PASS,
    validate_staging_contract,
)


class TestValidateStagingContract(unittest.TestCase):
    def test_staging_contract_static_pass(self) -> None:
        wrapper = pathlib.Path("scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_datacheck.sh")
        pbs = pathlib.Path("scripts/hpc/stage_f/03_mode_ii_h0_endpoint_corrected_datacheck.pbs")

        ok, classification, failures = validate_staging_contract(wrapper, pbs)
        self.assertTrue(ok, msg=f"Staging contract failed: {failures}")
        self.assertEqual(classification, CLASSIFICATION_PASS)
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
