#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn57_c4_companion.py
Unit tests for Mode-I Task F1597 Turn 57 Package 95 C4 Companion Continuum Model.
"""

import unittest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG95_DIR = REPO_ROOT / "models/pandey_kumar_mode1/95_c4_companion_miseseri"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestC4Companion(unittest.TestCase):
    def test_01_all_files_exist(self):
        expected_files = [
            "M1_C4_COMPANION_FRAME7.inp",
            "f42_mixed_uel.for",
            "job_notifications.sh",
            "submit_M1_C4_COMPANION_FRAME7.pbs",
            "run_c4_companion_datacheck.sh",
            "PACKAGE_MANIFEST.json",
            "M1_C4_COMPANION_FRAME7_AUTHORIZATION.json"
        ]
        for f in expected_files:
            p = PKG95_DIR / f
            self.assertTrue(p.exists(), f"File missing: {f}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {f}")

    def test_02_deck_structure(self):
        inp_path = PKG95_DIR / "M1_C4_COMPANION_FRAME7.inp"
        content = inp_path.read_text(encoding="utf-8")
        
        self.assertIn("*Element, type=CPE4, elset=ALL_QUADS", content)
        self.assertIn("*Solid Section, elset=ALL_QUADS, material=STEEL", content)
        self.assertIn("MISESERI, MISESAVG, EVOL", content)
        self.assertIn("0.002052000", content)
        self.assertIn("*Step, name=STATIC_ELASTIC", content)

    def test_03_shell_scripts_pure_lf(self):
        for script_name in ["submit_M1_C4_COMPANION_FRAME7.pbs", "run_c4_companion_datacheck.sh", "job_notifications.sh"]:
            p = PKG95_DIR / script_name
            content_bytes = p.read_bytes()
            self.assertNotIn(b"\r\n", content_bytes, f"CRLF line endings detected in {script_name}!")

    def test_04_manifest_and_authorization(self):
        manifest_path = PKG95_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest["package_id"], "PACKAGE_95")
        self.assertEqual(manifest["mesh"]["quad_count"], 4422)
        self.assertEqual(manifest["mesh"]["node_count"], 4588)

        auth_path = PKG95_DIR / "M1_C4_COMPANION_FRAME7_AUTHORIZATION.json"
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)
        
        self.assertEqual(auth["batch_name"], "MODE1_PACKAGE_95_C4_COMPANION_MISESERI")
        self.assertEqual(auth["jobs"][0]["id"], "M1_C4_COMPANION_FRAME7")

if __name__ == "__main__":
    unittest.main()
