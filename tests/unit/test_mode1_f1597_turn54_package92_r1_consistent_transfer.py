#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn54_package92_r1_consistent_transfer.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 0994c887-ba44-4c21-ba1d-9dec231dabb3
Protocol Version: 2

Unit test suite verifying Package 92-R1 consistent state transfer formulation,
donor provenance integrity, mesh structure, and frozen UEL bitwise parity.
"""

import unittest
import hashlib
import json
import csv
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG92_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/92_r1_c4_package92_r1_consistent_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestPackage92R1ConsistentTransfer(unittest.TestCase):

    def test_01_frozen_uel_bitwise_parity(self):
        uel_path = PKG92_R1_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_path.exists(), "f42_mixed_uel.for must exist in Package 92-R1")
        self.assertEqual(sha256_file(uel_path), FROZEN_UEL_HASH, "Frozen UEL hash mismatch in Package 92-R1")

    def test_02_manifest_and_authorization_integrity(self):
        manifest_path = PKG92_R1_DIR / "PACKAGE_MANIFEST.json"
        auth_path = PKG92_R1_DIR / "M1_C4_PACKAGE92_R1_TRANSFER_AUTHORIZATION.json"
        self.assertTrue(manifest_path.exists(), "Manifest must exist")
        self.assertTrue(auth_path.exists(), "Authorization JSON must exist")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        with open(auth_path, "r", encoding="utf-8") as f:
            auth = json.load(f)

        self.assertEqual(manifest["package_id"], "PACKAGE_92_R1")
        self.assertEqual(auth["batch_name"], "MODE1_PACKAGE_92_R1_C4_CONSISTENT_TRANSFER")
        self.assertEqual(auth["jobs"][0]["id"], "M1_C4_PACKAGE92_R1_TRANSFER")
        self.assertEqual(auth["jobs"][0]["queue"], "entry_imfdfkmq")
        self.assertEqual(auth["jobs"][0]["cpus"], 1)
        self.assertEqual(auth["jobs"][0]["memory_gb"], 8)
        self.assertEqual(auth["jobs"][0]["walltime_hours"], 4)
        self.assertFalse(auth["automatic_retry"])

        # Check all files in manifest exist and hashes match
        for fname, expected_hash in manifest["files"].items():
            fpath = PKG92_R1_DIR / fname
            self.assertTrue(fpath.exists(), f"File {fname} in manifest must exist on disk")
            self.assertEqual(sha256_file(fpath), expected_hash, f"Hash mismatch for {fname}")

    def test_03_donor_provenance_self_consistency(self):
        manifest_path = PKG92_R1_DIR / "PACKAGE_MANIFEST.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        donor = manifest["donor_provenance"]
        self.assertEqual(donor["donor_package"], "PACKAGE_90_R1")
        self.assertEqual(donor["donor_job"], "1416558.mmaster02")
        self.assertEqual(donor["checkpoint_frame"], 6)
        self.assertAlmostEqual(donor["rf2_target_N"], 159.159392, places=3)
        self.assertAlmostEqual(donor["d_max_donor"], 0.972955, places=3)

    def test_04_receiver_mesh_and_mapped_table(self):
        table_path = PKG92_R1_DIR / "candidate_c4_frame6_mapped_state_table.csv"
        self.assertTrue(table_path.exists(), "Mapped state table must exist")

        node_count = 0
        elem_count = 0
        d_vals = []
        h_vals = []

        with open(table_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
            self.assertEqual(header[0], "record_type")
            for row in reader:
                if row[0] == "NODE":
                    node_count += 1
                    d_vals.append(float(row[4]))
                elif row[0] == "ELEM_H":
                    elem_count += 1
                    for v in row[2:6]:
                        h_vals.append(float(v))

        self.assertEqual(node_count, 4588, "Expected 4588 receiver nodes")
        self.assertEqual(elem_count, 4422, "Expected 4422 receiver elements")
        self.assertGreaterEqual(min(d_vals), 0.0, "Damage must be >= 0")
        self.assertLessEqual(max(d_vals), 1.0, "Damage must be <= 1.0")
        self.assertGreaterEqual(min(h_vals), 0.0, "History H must be >= 0")
        self.assertGreater(max(h_vals), 50.0, "Crack-tip history H must reflect sharp stress concentration")

    def test_05_input_deck_structure_and_steps(self):
        inp_path = PKG92_R1_DIR / "M1_C4_PACKAGE92_R1_TRANSFER.inp"
        self.assertTrue(inp_path.exists(), "Input deck must exist")
        text = inp_path.read_text(encoding="utf-8")

        # Step checks
        self.assertIn("*Step, name=STATE_INJECTION", text)
        self.assertIn("*Step, name=MECH_REEQUIL_FROZEN_DAMAGE", text)
        self.assertIn("*Step, name=STAGGERED_PHASE_SUBPROBLEM", text)
        self.assertIn("*Step, name=FORWARD_CONTINUATION", text)

        # Layer checks
        self.assertIn("*Element, type=U1, elset=PHASE_QUADS", text)
        self.assertIn("*Element, type=U2, elset=MECH_QUADS", text)
        self.assertIn("*Element, type=CPE4, elset=UMATELEM", text)
        self.assertIn("*Solid Section, elset=UMATELEM, material=DUMMY_MAT", text)

        # Initial conditions check
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", text)

        # PBS script check
        pbs_path = PKG92_R1_DIR / "submit_M1_C4_PACKAGE92_R1_TRANSFER.pbs"
        self.assertTrue(pbs_path.exists())
        pbs_text = pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -N M1_C4_P92_R1", pbs_text)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)

if __name__ == "__main__":
    unittest.main()
