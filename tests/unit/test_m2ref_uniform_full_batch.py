#!/usr/bin/env python3
"""
Unit Tests for M2REF_H1_FULL_U050 and M2REF_H2_FULL_U050
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
H1_DIR = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H1_FULL_U050"
H2_DIR = ROOT / "models/generated/mode_ii/production_verification_batch/M2REF_H2_FULL_U050"

class TestUniformFullBatch(unittest.TestCase):

    def test_h1_package_manifest_integrity(self):
        manifest_fp = H1_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_fp.exists(), "H1 manifest missing")
        manifest = json.loads(manifest_fp.read_text(encoding="utf-8"))
        for fn, exp_sha in manifest["files"].items():
            fp = H1_DIR / fn
            self.assertTrue(fp.exists(), f"H1 file missing: {fn}")
            act_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
            self.assertEqual(act_sha, exp_sha, f"H1 SHA mismatch for {fn}")

    def test_h2_package_manifest_integrity(self):
        manifest_fp = H2_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_fp.exists(), "H2 manifest missing")
        manifest = json.loads(manifest_fp.read_text(encoding="utf-8"))
        for fn, exp_sha in manifest["files"].items():
            fp = H2_DIR / fn
            self.assertTrue(fp.exists(), f"H2 file missing: {fn}")
            act_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
            self.assertEqual(act_sha, exp_sha, f"H2 SHA mismatch for {fn}")

    def test_uel_residual_formulation(self):
        for pkg_dir in [H1_DIR, H2_DIR]:
            for_fp = pkg_dir / "f42_mixed_uel.for"
            self.assertTrue(for_fp.exists())
            content = for_fp.read_text(encoding="utf-8")
            self.assertIn("RHS(I,1) = -F_INT(I)", content, f"Out-of-loop residual missing in {pkg_dir.name}")
            self.assertIn("SV_H(PHYSIDX, KPT) = SVARS(8+KPT)", content)

    def test_h1_inp_properties_and_loading(self):
        inp_fp = H1_DIR / "M2REF_H1_FULL_U050.inp"
        self.assertTrue(inp_fp.exists())
        content = inp_fp.read_text(encoding="utf-8")
        self.assertIn("0.015, 0.0027, 210.0, 0.3, 1.0e-7, 12064.0", content)
        self.assertIn("RP, 1, 1, 0.050000", content)

    def test_h2_inp_properties_and_loading(self):
        inp_fp = H2_DIR / "M2REF_H2_FULL_U050.inp"
        self.assertTrue(inp_fp.exists())
        content = inp_fp.read_text(encoding="utf-8")
        self.assertIn("0.015, 0.0027, 210.0, 0.3, 1.0e-7, 33852.0", content)
        self.assertIn("RP, 1, 1, 0.050000", content)

    def test_pbs_and_resources(self):
        pbs_h1 = (H1_DIR / "M2REF_H1_FULL_U050.pbs").read_text(encoding="utf-8")
        self.assertIn("#PBS -l select=1:ncpus=1:mem=8gb", pbs_h1)
        self.assertIn("#PBS -l walltime=12:00:00", pbs_h1)
        self.assertIn("#PBS -m abe", pbs_h1)

        pbs_h2 = (H2_DIR / "M2REF_H2_FULL_U050.pbs").read_text(encoding="utf-8")
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs_h2)
        self.assertIn("#PBS -l walltime=24:00:00", pbs_h2)
        self.assertIn("#PBS -m abe", pbs_h2)

if __name__ == '__main__':
    unittest.main()
