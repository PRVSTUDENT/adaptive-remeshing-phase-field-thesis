#!/usr/bin/env python3
"""Unit Test Suite for Mode-II Adaptive Production Packages (MM & PK5).
Task: F43ADAPT-PROD-PREP1
"""

import os
import sys
import json
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_mode_ii_adaptive_production_batch import (
    validate_production_batch,
    EXPECTED_UEL_SHA256,
    EXPECTED_CONFIGS,
    BATCH_DIR,
    sha256_file
)


class TestModeIIAdaptiveProductionBatch(unittest.TestCase):

    def test_production_batch_static_validation(self):
        """Verify that all production packages pass fail-closed static validation."""
        res = validate_production_batch()
        self.assertTrue(res["all_passed"], f"Validation failed: {res}")

    def test_uel_exact_hash(self):
        """Verify that UEL across all production packages matches the qualified FRACFIX hash."""
        for case_name in EXPECTED_CONFIGS.keys():
            uel_path = BATCH_DIR / case_name / "f42_mixed_uel.for"
            self.assertTrue(uel_path.is_file(), f"UEL missing for {case_name}")
            self.assertEqual(sha256_file(uel_path), EXPECTED_UEL_SHA256)

    def test_manifest_consistency(self):
        """Verify that package manifest files match disk state and raw hashes."""
        for case_name, exp in EXPECTED_CONFIGS.items():
            pkg_dir = BATCH_DIR / case_name
            man_path = pkg_dir / "PACKAGE_MANIFEST.json"
            self.assertTrue(man_path.is_file(), f"Manifest missing for {case_name}")

            manifest = json.loads(man_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["case_name"], case_name)
            self.assertEqual(manifest["physical_node_count"], exp["n_nodes"])
            self.assertEqual(manifest["physical_element_count"], exp["n_phys"])
            self.assertEqual(manifest["layered_element_count"], 3 * exp["n_phys"])
            self.assertEqual(manifest["memory"], exp["memory"])
            self.assertEqual(manifest["walltime"], exp["walltime"])
            self.assertEqual(manifest["queue"], exp["queue"])

            inp_path = pkg_dir / f"{case_name}.inp"
            pbs_path = pkg_dir / f"{case_name}.pbs"
            sub_path = pkg_dir / f"submit_{case_name.lower()}.sh"
            uel_path = pkg_dir / "f42_mixed_uel.for"

            self.assertEqual(manifest["inp_sha256"], sha256_file(inp_path))
            self.assertEqual(manifest["pbs_sha256"], sha256_file(pbs_path))
            self.assertEqual(manifest["submit_sh_sha256"], sha256_file(sub_path))
            self.assertEqual(manifest["uel_sha256"], sha256_file(uel_path))


if __name__ == "__main__":
    unittest.main()
