#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn56_package94_transfer.py
Unit tests for Mode-I Task F1597 Turn 56 Package 94 C3 -> C4 Authentic State Transfer.
"""

import unittest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG94_DIR = REPO_ROOT / "models/pandey_kumar_mode1/94_c4_package94_authentic_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestPackage94Transfer(unittest.TestCase):
    def test_01_all_files_exist(self):
        expected_files = [
            "M1_C4_PACKAGE94_TRANSFER.inp",
            "f42_mixed_uel.for",
            "candidate_crack_band_mesh_c4.inp",
            "candidate_c4_frame6_mapped_state_table.csv",
            "job_notifications.sh",
            "submit_M1_C4_PACKAGE94_TRANSFER.pbs",
            "run_pkg94_datacheck.sh",
            "PACKAGE_MANIFEST.json",
            "M1_C4_PACKAGE94_TRANSFER_AUTHORIZATION.json"
        ]
        for f in expected_files:
            p = PKG94_DIR / f
            self.assertTrue(p.exists(), f"File missing: {f}")
            self.assertGreater(p.stat().st_size, 0, f"File is empty: {f}")

    def test_02_frozen_uel_hash(self):
        uel_path = PKG94_DIR / "f42_mixed_uel.for"
        actual_hash = sha256_file(uel_path)
        self.assertEqual(actual_hash, FROZEN_UEL_HASH, "Frozen UEL hash mismatch!")

    def test_03_shell_scripts_pure_lf(self):
        for script_name in ["submit_M1_C4_PACKAGE94_TRANSFER.pbs", "run_pkg94_datacheck.sh", "job_notifications.sh"]:
            p = PKG94_DIR / script_name
            content_bytes = p.read_bytes()
            self.assertNotIn(b"\r\n", content_bytes, f"CRLF line endings detected in {script_name}!")

    def test_04_input_deck_structure(self):
        inp_path = PKG94_DIR / "M1_C4_PACKAGE94_TRANSFER.inp"
        content = inp_path.read_text(encoding="utf-8")
        
        # Verify 4 named steps
        self.assertIn("*Step, name=STATE_INJECTION", content)
        self.assertIn("*Step, name=MECH_REEQUIL_FROZEN_DAMAGE", content)
        self.assertIn("*Step, name=STAGGERED_PHASE_SUBPROBLEM", content)
        self.assertIn("*Step, name=FORWARD_CONTINUATION", content)
        
        # Verify displacement values
        self.assertIn("2.0366930400e-03", content)  # checkpoint displacement
        self.assertIn("2.0520000000e-03", content)  # continuation displacement (+15.3 nm)
        
        # Verify companion elements
        self.assertIn("type=CPE4, elset=UMATELEM", content)
        self.assertIn("DUMMY_MAT", content)

    def test_05_manifest_and_authorization(self):
        manifest_path = PKG94_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        
        self.assertEqual(manifest["package_id"], "PACKAGE_94")
        self.assertEqual(manifest["donor_provenance"]["donor_package"], "PACKAGE_93")
        self.assertEqual(manifest["donor_provenance"]["checkpoint_frame"], 6)
        self.assertEqual(manifest["receiver_mesh"]["elements"], 4422)
        self.assertEqual(manifest["receiver_mesh"]["physical_nodes"], 4588)
        self.assertEqual(manifest["continuation"]["continuation_u_mm"], 0.00205200000)

        auth_path = PKG94_DIR / "M1_C4_PACKAGE94_TRANSFER_AUTHORIZATION.json"
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)
        
        self.assertEqual(auth["batch_name"], "MODE1_PACKAGE_94_C4_AUTHENTIC_TRANSFER")
        self.assertEqual(auth["jobs"][0]["id"], "M1_C4_PACKAGE94_TRANSFER")
        self.assertEqual(auth["jobs"][0]["queue"], "entry_imfdfkmq")

        # Verify hash match in manifest
        inp_path = PKG94_DIR / "M1_C4_PACKAGE94_TRANSFER.inp"
        self.assertEqual(manifest["files"]["M1_C4_PACKAGE94_TRANSFER.inp"], sha256_file(inp_path))

if __name__ == "__main__":
    unittest.main()
