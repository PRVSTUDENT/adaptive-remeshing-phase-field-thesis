#!/usr/bin/env python3
"""
Unit tests for Mode-II PK10R1 Control Batch:
1. PK10R1_CONTINUOUS_U050
2. PK10R1_IDENTITY_RESTART_U050
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent.parent.parent
CONTROL_BATCH_DIR = ROOT / "models/generated/mode_ii/production_control_batch"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

class TestPK10R1ControlBatch(unittest.TestCase):
    def test_manifest_validation(self):
        for name in ["PK10R1_CONTINUOUS_U050", "PK10R1_IDENTITY_RESTART_U050"]:
            pkg_dir = CONTROL_BATCH_DIR / name
            manifest_path = pkg_dir / "PACKAGE_MANIFEST.json"
            self.assertTrue(manifest_path.exists(), f"Missing manifest for {name}")
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            for rel_p, exp_hash in manifest.get("file_hashes", {}).items():
                fp = pkg_dir / rel_p
                self.assertTrue(fp.exists(), f"File {rel_p} missing in {name}")
                self.assertEqual(sha256_file(fp), exp_hash, f"Hash mismatch for {rel_p} in {name}")

    def test_uel_integrity(self):
        for name in ["PK10R1_CONTINUOUS_U050", "PK10R1_IDENTITY_RESTART_U050"]:
            uel_path = CONTROL_BATCH_DIR / name / "f42_mixed_uel.for"
            self.assertTrue(uel_path.exists())
            code = uel_path.read_text(encoding="utf-8")
            self.assertIn("RHS(I,1) = -F_INT(I)", code)
            self.assertIn("SUBROUTINE UMAT", code)
            self.assertIn("N_PHYS", code)

    def test_continuous_inp_structure(self):
        inp_path = CONTROL_BATCH_DIR / "PK10R1_CONTINUOUS_U050/PK10R1_CONTINUOUS_U050.inp"
        self.assertTrue(inp_path.exists())
        content = inp_path.read_text(encoding="utf-8")
        self.assertIn("*STEP, NAME=ShearStep", content)
        self.assertIn("0.050000", content)
        self.assertNotIn("*INITIAL CONDITIONS", content)
        self.assertNotIn("PhaseInit", content)
        self.assertNotIn("*BOUNDARY, OP=NEW", content)

    def test_identity_restart_inp_structure(self):
        inp_path = CONTROL_BATCH_DIR / "PK10R1_IDENTITY_RESTART_U050/PK10R1_IDENTITY_RESTART_U050.inp"
        self.assertTrue(inp_path.exists())
        content = inp_path.read_text(encoding="utf-8")
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", content)
        self.assertIn("Step-1-PhaseInit", content)
        self.assertIn("Step-2-Continuation", content)
        self.assertIn("*BOUNDARY, OP=NEW", content)
        self.assertIn("0.050000", content)

    def test_pbs_directives(self):
        for name in ["PK10R1_CONTINUOUS_U050", "PK10R1_IDENTITY_RESTART_U050"]:
            pbs_path = CONTROL_BATCH_DIR / name / f"{name}.pbs"
            self.assertTrue(pbs_path.exists())
            text = pbs_path.read_text(encoding="utf-8")
            self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", text)
            self.assertIn("#PBS -l walltime=24:00:00", text)
            self.assertIn("#PBS -q entry_imfdfkmq", text)
            self.assertIn("#PBS -m abe", text)
            self.assertIn("job_notifications.sh", text)

if __name__ == "__main__":
    unittest.main()

