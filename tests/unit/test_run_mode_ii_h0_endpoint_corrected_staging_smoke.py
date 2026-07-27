"""Unit tests for run_mode_ii_h0_endpoint_corrected_staging_smoke.py."""

from __future__ import annotations

import pathlib
import tempfile
import unittest

from scripts.validation.run_mode_ii_h0_endpoint_corrected_staging_smoke import (
    CLASSIFICATION_PASS,
    run_staging_smoke,
)


class TestRunStagingSmoke(unittest.TestCase):
    def test_local_staging_smoke_pass(self) -> None:
        package_dir = pathlib.Path("models/generated/mode_ii/h0_endpoint_corrected_serial")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_out = pathlib.Path(tmp)
            ok, classification, failures = run_staging_smoke(package_dir, tmp_out)
            self.assertTrue(ok, msg=f"Staging smoke failed: {failures}")
            self.assertEqual(classification, CLASSIFICATION_PASS)
            self.assertEqual(failures, [])
            self.assertTrue((tmp_out / "LOCAL_STAGING_SMOKE_STATUS.json").is_file())
            self.assertTrue((tmp_out / "EVIDENCE_FILE_INVENTORY.csv").is_file())
            self.assertTrue((tmp_out / "mocked_qsub_arguments.txt").is_file())


if __name__ == "__main__":
    unittest.main()
