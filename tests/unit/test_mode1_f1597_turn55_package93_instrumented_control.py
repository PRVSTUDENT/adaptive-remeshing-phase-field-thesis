#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn55_package93_instrumented_control.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: b13e68ac-0d42-4db1-ae22-779415f0ae6e
Protocol Version: 2

Unit test suite validating Package 93:
- Frozen UEL hash integrity
- Dual-channel notifications integration
- Layer 3 companion elements (5301..7950, CPE4, UMATELEM)
- Exact active-set boundary conditions parity with Package 90-R1 (2,221 clamped, 548 free)
- Field output requests for companion SDVs across all steps
- PBS script syntax and pure LF formatting
- Manifest and Authorization JSON cryptographic consistency
"""

import unittest
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG93_DIR = REPO_ROOT / "models/pandey_kumar_mode1/93_c3_package93_instrumented_control"
PKG90_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestPackage93InstrumentedControl(unittest.TestCase):

    def test_01_frozen_uel_integrity(self):
        uel_path = PKG93_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.is_file(), "f42_mixed_uel.for must exist in Package 93 directory")
        actual_hash = sha256_file(uel_path)
        self.assertEqual(actual_hash, FROZEN_UEL_HASH, "Frozen UEL hash mismatch")

    def test_02_job_notifications_presence(self):
        notif_path = PKG93_DIR / "job_notifications.sh"
        self.assertTrue(notif_path.is_file(), "job_notifications.sh must exist in Package 93 directory")
        text = notif_path.read_text(encoding="utf-8")
        self.assertIn("notify_start", text)
        self.assertIn("notification_install_terminal_trap", text)

    def test_03_mesh_and_companion_elements(self):
        inp_path = PKG93_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
        self.assertTrue(inp_path.is_file(), "Package 93 input deck must exist")
        text = inp_path.read_text(encoding="utf-8")

        # Check Layer 1 quads
        self.assertIn("*Element, type=U1, elset=PHASE_QUADS", text)
        self.assertIn("1, 1, 2, 56, 55", text)
        self.assertIn("2650,", text)

        # Check Layer 2 quads
        self.assertIn("*Element, type=U2, elset=MECH_QUADS", text)
        self.assertIn("2651,", text)
        self.assertIn("5300,", text)

        # Check Layer 3 companion elements
        self.assertIn("*Element, type=CPE4, elset=UMATELEM", text)
        self.assertIn("5301, 1, 2, 56, 55", text)
        self.assertIn("7950,", text)

        # Check Companion section and material
        self.assertIn("*Solid Section, elset=UMATELEM, material=DUMMY_MAT", text)
        self.assertIn("*Material, name=DUMMY_MAT", text)
        self.assertIn("*User Material, constants=3", text)
        self.assertIn("210.0, 0.3, 2650.0", text)
        self.assertIn("*Depvar", text)

        # Check companion output requests
        self.assertIn("*Element Output, elset=UMATELEM", text)
        self.assertIn("SDV, S, E", text)

    def test_04_step4_active_set_exact_parity_with_pkg90_r1(self):
        # Read Package 90-R1 Step 4 clamped nodes
        inp_pkg90 = PKG90_R1_DIR / "M1_C3_PACKAGE90_R1_TRANSFER.inp"
        lines_90 = inp_pkg90.read_text(encoding="utf-8").splitlines()
        s4_idx_90 = -1
        for i, l in enumerate(lines_90):
            if "*Step, name=FORWARD_CONTINUATION" in l:
                s4_idx_90 = i
                break
        bcs_90 = {}
        for l in lines_90[s4_idx_90:]:
            if l.startswith("*Output"):
                break
            parts = [p.strip() for p in l.split(",")]
            if len(parts) == 4 and parts[1] == "3" and parts[2] == "3":
                bcs_90[int(parts[0])] = float(parts[3])

        # Read Package 93 Step 4 clamped nodes
        inp_pkg93 = PKG93_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
        lines_93 = inp_pkg93.read_text(encoding="utf-8").splitlines()
        s4_idx_93 = -1
        for i, l in enumerate(lines_93):
            if "*Step, name=FORWARD_CONTINUATION" in l:
                s4_idx_93 = i
                break
        bcs_93 = {}
        for l in lines_93[s4_idx_93:]:
            if l.startswith("*Output"):
                break
            parts = [p.strip() for p in l.split(",")]
            if len(parts) == 4 and parts[1] == "3" and parts[2] == "3":
                bcs_93[int(parts[0])] = float(parts[3])

        self.assertEqual(len(bcs_93), 2221, "Package 93 must clamp exactly 2,221 far-field nodes")
        self.assertEqual(len(bcs_90), 2221, "Package 90-R1 has exactly 2,221 clamped nodes")
        self.assertEqual(set(bcs_93.keys()), set(bcs_90.keys()), "Package 93 must have identical clamped node set as Package 90-R1")

        for nid in bcs_90:
            self.assertAlmostEqual(bcs_93[nid], bcs_90[nid], places=9, msg=f"Nodal damage mismatch on node {nid}")

    def test_05_pbs_and_datacheck_scripts_pure_lf(self):
        pbs_path = PKG93_DIR / "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs"
        self.assertTrue(pbs_path.is_file())
        pbs_bytes = pbs_path.read_bytes()
        self.assertNotIn(b"\r\n", pbs_bytes, "PBS script must not contain Windows CRLF")
        pbs_text = pbs_bytes.decode("utf-8")
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_text)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=8gb", pbs_text)
        self.assertIn("#PBS -l walltime=04:00:00", pbs_text)
        self.assertIn("#PBS -m abe", pbs_text)

        dc_path = PKG93_DIR / "run_pkg93_datacheck.sh"
        self.assertTrue(dc_path.is_file())
        dc_bytes = dc_path.read_bytes()
        self.assertNotIn(b"\r\n", dc_bytes, "Datacheck script must not contain Windows CRLF")

    def test_06_manifest_and_authorization_hashes(self):
        manifest_path = PKG93_DIR / "PACKAGE_MANIFEST.json"
        auth_path = PKG93_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY_AUTHORIZATION.json"
        inp_path = PKG93_DIR / "M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"
        uel_path = PKG93_DIR / "f42_mixed_uel.for"
        notif_path = PKG93_DIR / "job_notifications.sh"
        pbs_path = PKG93_DIR / "submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs"

        with open(manifest_path, "r", encoding="utf-8") as f:
            m = json.load(f)
        with open(auth_path, "r", encoding="utf-8") as f:
            a = json.load(f)

        inp_sha = sha256_file(inp_path)
        uel_sha = sha256_file(uel_path)
        notif_sha = sha256_file(notif_path)
        pbs_sha = sha256_file(pbs_path)

        self.assertEqual(m["input_deck_sha256"], inp_sha)
        self.assertEqual(m["user_subroutine_sha256"], uel_sha)
        self.assertEqual(a["files"]["M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.inp"], inp_sha.lower())
        self.assertEqual(a["files"]["f42_mixed_uel.for"], uel_sha.lower())
        self.assertEqual(a["files"]["job_notifications.sh"], notif_sha.lower())
        self.assertEqual(a["files"]["submit_M1_C3_PACKAGE93_INSTRUMENTED_REPLAY.pbs"], pbs_sha.lower())

        # Check guarded command SHA256
        job = a["jobs"][0]
        cmd = job["command"]
        cmd_sha = hashlib.sha256(cmd.encode("utf-8")).hexdigest().lower()
        self.assertEqual(job["command_sha256"], cmd_sha)

if __name__ == "__main__":
    unittest.main()
