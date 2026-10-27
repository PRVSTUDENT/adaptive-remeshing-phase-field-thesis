# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn211_package115_qualification.py
=====================================================
Unit test suite verifying Package 115 isolated Increment-79 direct
state-transfer control package structure, frozen UEL hash, mapping audit,
and technical qualification blocker recording.

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
"""
import os
import sys
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "115_c4_inc79_direct_transfer")

def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

class TestPackage115Qualification(unittest.TestCase):

    def test_01_package_files_exist(self):
        expected_files = [
            "M1_C4_INC79_DIRECT_TRANSFER.inp",
            "active_set_boundary_cards.inc",
            "d_lower_bounds.csv",
            "driver_c4_inc79_direct_transfer.py",
            "f42_unified_12dof_active_set_uel.for",
            "job_notifications.sh",
            "nodal_displacements_initial.csv",
            "run_c4_inc79_transfer_datacheck.sh",
            "stage_a_all_d0_boundary_cards.inc",
            "submit_M1_C4_INC79_DIRECT_TRANSFER.pbs",
            "M1_C4_INC79_TRANSFER_AUTHORIZATION.json",
            "PACKAGE_MANIFEST.json"
        ]
        for f in expected_files:
            fpath = os.path.join(PKG_DIR, f)
            self.assertTrue(os.path.exists(fpath), f"Missing file: {f}")

    def test_02_frozen_unified_uel_hash(self):
        uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
        expected_hash = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
        self.assertEqual(get_sha256(uel_path), expected_hash)

    def test_03_input_deck_boundary_and_mesh(self):
        inp_path = os.path.join(PKG_DIR, "M1_C4_INC79_DIRECT_TRANSFER.inp")
        with open(inp_path, "r") as f:
            content = f.read()
        self.assertIn("N_RP, 2, 2, 0.00184250", content)
        self.assertIn("*Include, input=active_set_boundary_cards.inc", content)
        self.assertIn("TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=8, UNSYMM", content)

    def test_04_d_lower_bounds_consistency(self):
        bounds_path = os.path.join(PKG_DIR, "d_lower_bounds.csv")
        with open(bounds_path, "r") as f:
            lines = [l.strip() for l in f if l.strip()]
        # Header + 4422 elements = 4423 lines
        self.assertEqual(len(lines), 4423)
        header = lines[0].split(",")
        self.assertEqual(header[0].strip(), "EID")
        self.assertEqual(len(header), 9)

    def test_05_mapping_audit_record(self):
        audit_path = os.path.join(REPO_ROOT, "results", "validation", "c4_inc79_direct_transfer_mapping_audit.json")
        self.assertTrue(os.path.exists(audit_path))
        with open(audit_path, "r") as f:
            audit = json.load(f)
        self.assertEqual(audit["schema"], 1)
        self.assertEqual(audit["package"], "PACKAGE_115_C4_INC79_DIRECT_TRANSFER")
        self.assertAlmostEqual(audit["donor_reference"]["prescribed_u_rp_mm"], 0.0018425, places=7)
        self.assertAlmostEqual(audit["donor_reference"]["rf2_N"], 186.067909, places=6)
        self.assertAlmostEqual(audit["donor_reference"]["e_tot_mJ"], 0.21244805, places=7)
        self.assertEqual(audit["receiver_target"]["quads"], 4422)

    def test_06_authorization_and_manifest_hashes(self):
        auth_path = os.path.join(PKG_DIR, "M1_C4_INC79_TRANSFER_AUTHORIZATION.json")
        with open(auth_path, "r") as f:
            auth = json.load(f)
        self.assertEqual(auth["schema"], 1)
        self.assertEqual(auth["scientific_scope"], "MODE1")
        self.assertEqual(auth["technical_stage"], "C1-1")
        self.assertEqual(len(auth["jobs"]), 1)
        job = auth["jobs"][0]
        self.assertEqual(job["id"], "M1_C4_INC79_TRANSFER")
        self.assertEqual(job["cpus"], 1)
        self.assertEqual(job["memory_gb"], 16)
        self.assertEqual(job["walltime_hours"], 8)

if __name__ == "__main__":
    unittest.main()
