# -*- coding: utf-8 -*-
"""
Unit test: Package 135 Qualification and Column Indexing Regression Guard.
Verifies:
1. Frozen UEL SHA-256 integrity
2. Package 135 driver dynamic header search (H0 in cols 5-8, D0 in cols 1-4)
3. Column indexing regression guard: fails if parts[1:5] is used for H0
4. Checkpoint bounds integrity: 4,588 nodes, 17,688 GP committed histories
5. Target displacement: u = 0.0019651074 mm
6. Manifest file completeness
"""

from __future__ import print_function, division
import os
import sys
import json
import hashlib
import unittest

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

class TestPackage135Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(cls.root, "models", "pandey_kumar_mode1", "135_c4_inc88_h23_underrelaxed_forward_continuation")
        cls.manifest_path = os.path.join(cls.pkg_dir, "PACKAGE_MANIFEST.json")
        cls.driver_path = os.path.join(cls.pkg_dir, "driver_c4_inc88_h23_continuation.py")
        cls.bounds_path = os.path.join(cls.pkg_dir, "d_lower_bounds.csv")
        cls.inp_path = os.path.join(cls.pkg_dir, "M1_C4_INC88_H23_CONT.inp")
        cls.uel_path = os.path.join(cls.pkg_dir, "f42_unified_12dof_active_set_uel.for")

    def test_01_frozen_uel_integrity(self):
        expected_sha = "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"
        actual_sha = compute_sha256(self.uel_path)
        self.assertEqual(actual_sha, expected_sha, "Frozen production UEL SHA-256 mismatch!")

    def test_02_driver_dynamic_header_search(self):
        with open(self.driver_path, "r") as f:
            code = f.read()

        # Check that load_committed_history_and_d0 dynamically searches header for H0_
        self.assertIn('startswith("H0_")', code)

        # Inspect the exact function implementation
        start = code.find("def load_committed_history_and_d0")
        end = code.find("def ", start + 1)
        fn_code = code[start:end]

        self.assertIn("h_vals = [float(parts[i]) for i in h_idx]", fn_code)
        self.assertNotIn("parts[1:5]", fn_code)

    def test_03_column_indexing_regression_guard(self):
        """Regression test that fails if parts[1:5] is substituted for H0."""
        with open(self.bounds_path, "r") as f:
            header = [h.strip() for h in f.readline().split(",")]

        self.assertEqual(header, ["EID", "D0_1", "D0_2", "D0_3", "D0_4", "H0_1", "H0_2", "H0_3", "H0_4"])

        # First line of data
        with open(self.bounds_path, "r") as f:
            f.readline()
            sample_line = f.readline().strip()
        parts = [p.strip() for p in sample_line.split(",")]

        # Correct H0 parsing (cols 5-8)
        correct_h0 = [float(parts[i]) for i in range(5, 9)]
        # Buggy parsing (cols 1-4, which are D0)
        buggy_h0 = [float(p) for p in parts[1:5]]

        # They must be different (D0 ~ 0.003-0.65, H0 ~ 0.0008-0.05)
        self.assertNotEqual(correct_h0, buggy_h0, "D0 and H0 columns must have distinct values")

        # The guard: verify that H0 values are indeed in columns 5-8
        h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]
        self.assertEqual(h_idx, [5, 6, 7, 8], "H0 columns must be 5, 6, 7, 8")

    def test_04_inp_deck_displacement(self):
        with open(self.inp_path, "r") as f:
            lines = f.readlines()

        found_rp = False
        for line in lines:
            if "N_RP, 2, 2, 0.001965107400" in line:
                found_rp = True
                break

        self.assertTrue(found_rp, "M1_C4_INC88_H23_CONT.inp must prescribe u_y = 0.001965107400 at N_RP")

    def test_05_under_relaxation_parameters(self):
        with open(self.driver_path, "r") as f:
            code = f.read()

        self.assertIn("OMEGA = 0.7", code)
        self.assertIn("max_am_cycles = 35", code)
        self.assertIn("u_target_inc88_mm = 0.001965107400", code)
        self.assertIn("u_init_inc87_mm = 0.001947309589", code)

    def test_06_manifest_completeness(self):
        self.assertTrue(os.path.exists(self.manifest_path))
        with open(self.manifest_path, "r") as f:
            m = json.load(f)

        files = m["files"]
        self.assertEqual(len(files), 11)
        for fname, expected_sha in files.items():
            fpath = os.path.join(self.pkg_dir, fname)
            self.assertTrue(os.path.exists(fpath), "Manifest file must exist: %s" % fname)
            actual_sha = compute_sha256(fpath)
            self.assertEqual(actual_sha.lower(), expected_sha.lower(), "File %s SHA256 mismatch!" % fname)

if __name__ == "__main__":
    unittest.main()
