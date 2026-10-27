#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package122_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite for Package 122 (Candidate C4 State Transfer from Re-equilibrated C3 Increment 88):
1. Verifies existence of all Package 122 files.
2. Asserts exact C4 mesh topology (4,422 quads, 4,588 nodes).
3. Asserts frozen UEL bitwise match (AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC).
4. Asserts material properties card [0.0075, 0.0027, 210.0, 0.3, 1.0E-07] in INP and driver (K_DEGRAD = 1e-7).
5. Asserts prescribed displacement u_RP = 0.001965107396 mm matching authentic Increment 88.
6. Asserts donor source RF2 = 185.04463136 N and donor E_tot = 0.23528389 mJ from converged Package 121.
7. Asserts PACKAGE_MANIFEST.json and M1_C4_INC88_TRANSFER_AUTHORIZATION.json integrity and hash consistency.
"""

import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
PKG_DIR = os.path.join(REPO_ROOT, "models/pandey_kumar_mode1/122_c4_inc88_from_p121_transfer")
EXPECTED_UEL_HASH = "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestPackage122Qualification(unittest.TestCase):

    def setUp(self):
        self.assertTrue(os.path.isdir(PKG_DIR), f"Package directory must exist: {PKG_DIR}")
        self.manifest_path = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
        self.auth_path = os.path.join(PKG_DIR, "M1_C4_INC88_TRANSFER_AUTHORIZATION.json")
        self.assertTrue(os.path.isfile(self.manifest_path), "PACKAGE_MANIFEST.json must exist")
        self.assertTrue(os.path.isfile(self.auth_path), "M1_C4_INC88_TRANSFER_AUTHORIZATION.json must exist")
        with open(self.manifest_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)
        with open(self.auth_path, "r", encoding="utf-8") as f:
            self.auth = json.load(f)

    def test_package122_files_exist(self):
        expected_files = [
            "active_set_boundary_cards.inc",
            "d_lower_bounds.csv",
            "driver_c4_inc88_transfer.py",
            "f42_unified_12dof_active_set_uel.for",
            "job_notifications.sh",
            "M1_C4_INC88_TRANSFER.inp",
            "M1_C4_INC88_TRANSFER_AUTHORIZATION.json",
            "nodal_displacements_initial.csv",
            "PACKAGE_MANIFEST.json",
            "run_c4_inc88_transfer_datacheck.sh",
            "stage_a_all_d0_boundary_cards.inc",
            "submit_M1_C4_INC88_TRANSFER.pbs"
        ]
        for f in expected_files:
            p = os.path.join(PKG_DIR, f)
            self.assertTrue(os.path.isfile(p), f"Missing file: {f}")

    def test_frozen_uel_sha256(self):
        uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
        self.assertEqual(sha256_file(uel_path), EXPECTED_UEL_HASH)

    def test_inp_deck_properties(self):
        inp_path = os.path.join(PKG_DIR, "M1_C4_INC88_TRANSFER.inp")
        with open(inp_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("0.0075, 0.0027, 210.0, 0.3, 1.0E-07", content)
        self.assertIn("0.001965107396", content)
        self.assertIn("*Step, name=P121-Transfer-Inc88", content)
        self.assertIn("*Include, input=active_set_boundary_cards.inc", content)

    def test_driver_parameters(self):
        driver_path = os.path.join(PKG_DIR, "driver_c4_inc88_transfer.py")
        with open(driver_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("K_DEGRAD = 1.0e-7", content)
        self.assertIn("target_rf2_ref = 185.04463136", content)
        self.assertIn("authentic_donor_energy_mJ = 0.23528389", content)
        self.assertIn("M1_C4_INC88_TRANSFER.inp", content)
        self.assertIn("c4_inc88_from_p121_summary.json", content)
        self.assertIn("max_am_cycles = 15", content)

    def test_c4_mesh_topology(self):
        bounds_csv = os.path.join(PKG_DIR, "d_lower_bounds.csv")
        disp_csv = os.path.join(PKG_DIR, "nodal_displacements_initial.csv")
        cards_inc = os.path.join(PKG_DIR, "stage_a_all_d0_boundary_cards.inc")

        with open(bounds_csv, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip() and not l.startswith("EID")]
            self.assertEqual(len(lines), 4422, "Candidate C4 must contain exactly 4,422 quad elements")

        with open(disp_csv, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip() and not l.startswith("NID")]
            self.assertEqual(len(lines), 4588, "Candidate C4 must contain exactly 4,588 nodes")

        with open(cards_inc, "r", encoding="utf-8") as f:
            lines = [l for l in f if l.strip() and not l.startswith("**") and not l.startswith("*")]
            self.assertEqual(len(lines), 4588, "Must contain boundary cards for 4,588 nodes")

    def test_manifest_and_authorization_integrity(self):
        self.assertEqual(self.manifest["package_name"], "PACKAGE_122_C4_INC88_FROM_P121_TRANSFER")
        self.assertEqual(self.auth["package_name"], "122_c4_inc88_from_p121_transfer")
        self.assertEqual(self.auth["adapter"], "mode1-experimental-12dof-v1")
        self.assertEqual(len(self.auth["jobs"]), 1)
        self.assertEqual(self.auth["jobs"][0]["id"], "M1_C4_INC88_TRANSFER")

        # Verify all files in auth["files"] match their actual SHA-256
        for fname, exp_hash in self.auth["files"].items():
            fpath = os.path.join(PKG_DIR, fname)
            self.assertTrue(os.path.isfile(fpath), f"File {fname} in auth must exist")
            actual_hash = sha256_file(fpath).lower()
            self.assertEqual(actual_hash, exp_hash.lower(), f"Hash mismatch for {fname}")

    def test_mapping_audit_record(self):
        audit_path = os.path.join(REPO_ROOT, "results/validation/c4_inc88_from_p121_mapping_audit.json")
        self.assertTrue(os.path.isfile(audit_path), "Mapping audit JSON must exist")
        with open(audit_path, "r", encoding="utf-8") as f:
            audit = json.load(f)
        self.assertEqual(audit["package"], "PACKAGE_122_C4_INC88_FROM_P121_TRANSFER")
        self.assertAlmostEqual(audit["donor_reference"]["re_equilibrated_rf2_N"], 185.04463136, places=4)
        self.assertAlmostEqual(audit["donor_reference"]["re_equilibrated_e_tot_mJ"], 0.23528389, places=6)
        self.assertEqual(audit["receiver_target"]["quads"], 4422)
        self.assertEqual(audit["receiver_target"]["nodes"], 4588)


if __name__ == "__main__":
    unittest.main()
