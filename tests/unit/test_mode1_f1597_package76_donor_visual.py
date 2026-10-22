#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package76_donor_visual.py
==========================================
Unit test verifying Package 76 instrumented candidate donor deck,
companion visualizer material assignment, state variable allocation,
and authorization manifest integrity under Task F1597.
"""

import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG76_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "76_candidate_donor_h0025_visual"
AUTH_JSON = PKG76_DIR / "CANDIDATE_DONOR_H0025_VISUAL_AUTHORIZATION.json"
MANIFEST_JSON = PKG76_DIR / "PACKAGE_MANIFEST.json"
INP_FILE = PKG76_DIR / "candidate_donor_h0025_visual.inp"
UEL_FILE = PKG76_DIR / "f42_mixed_uel.for"

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1F1597Package76DonorVisual(unittest.TestCase):
    def test_package_files_exist(self):
        for name in [
            "candidate_donor_h0025_visual.inp",
            "f42_mixed_uel.for",
            "job_notifications.sh",
            "submit_M1_CANDIDATE_DONOR_H0025_VISUAL.pbs",
            "PACKAGE_MANIFEST.json",
            "CANDIDATE_DONOR_H0025_VISUAL_AUTHORIZATION.json",
            "run_donor_dc.sh"
        ]:
            self.assertTrue((PKG76_DIR / name).is_file(), f"Missing file: {name}")

    def test_frozen_uel_hash(self):
        self.assertEqual(sha256_file(UEL_FILE), FROZEN_UEL_SHA256)

    def test_inp_companion_visualizer_setup(self):
        content = INP_FILE.read_text(encoding="utf-8")
        self.assertIn("*Solid Section, elset=umatelem, material=DUMMY_MAT", content)
        self.assertIn("*Material, name=DUMMY_MAT", content)
        self.assertIn("*User Material, constants=3", content)
        self.assertIn("210.0, 0.3, 1600.0", content)
        self.assertIn("*Depvar\n20", content)
        self.assertNotIn("DUMMY_ELASTIC", content)

    def test_inp_field_output_and_sdv_request(self):
        content = INP_FILE.read_text(encoding="utf-8")
        self.assertIn("*Output, field, frequency=1", content)
        self.assertIn("*Element Output, elset=umatelem\nSDV, S, E", content)
        self.assertIn("*Node Output\nU, RF", content)

    def test_authorization_manifest(self):
        auth = json.loads(AUTH_JSON.read_text(encoding="utf-8"))
        self.assertEqual(auth["batch_name"], "MODE1_CANDIDATE_DONOR_H0025_VISUAL")
        self.assertEqual(auth["adapter"], "mode1-qualified-batch-v2")
        self.assertEqual(auth["scientific_scope"], "MODE1")
        self.assertEqual(auth["max_submissions"], 1)
        self.assertEqual(len(auth["jobs"]), 1)

        job = auth["jobs"][0]
        self.assertEqual(job["id"], "M1_CANDIDATE_DONOR_H0025_VISUAL")
        self.assertEqual(job["input"], "candidate_donor_h0025_visual.inp")
        self.assertEqual(job["datacheck"], "M1_CANDIDATE_DONOR_H0025_VISUAL_DC.dat")
        self.assertEqual(job["queue"], "entry_imfdfkmq")
        self.assertEqual(job["cpus"], 1)
        self.assertEqual(job["memory_gb"], 8)
        self.assertEqual(job["walltime_hours"], 4)

        # Check all files hashes in authorization
        for rel_name, expected_hash in auth["files"].items():
            actual = sha256_file(PKG76_DIR / rel_name).lower()
            self.assertEqual(actual, expected_hash.lower(), f"Hash mismatch on {rel_name}")


if __name__ == "__main__":
    unittest.main()
