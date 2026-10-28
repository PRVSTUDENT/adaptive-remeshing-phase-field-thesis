# -*- coding: utf-8 -*-
from __future__ import print_function, division
import os
import json
import hashlib
import unittest

class TestMode1F1597Package137Qualification(unittest.TestCase):
    """
    Qualification test suite for Package 137 (Candidate C4 Exact Donor Increment-89 Continuation).
    """

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(cls.repo_root, "models", "pandey_kumar_mode1", "137_c4_donor_inc89_h27_exact_frame_continuation")
        cls.manifest_path = os.path.join(cls.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(cls.manifest_path, "r") as f:
            cls.manifest = json.load(f)

    def test_01_frozen_uel_integrity(self):
        """Verify that the production UEL is 100% bit-exact to the frozen standard."""
        uel_path = os.path.join(self.pkg_dir, "f42_unified_12dof_active_set_uel.for")
        with open(uel_path, "rb") as f:
            uel_sha = hashlib.sha256(f.read()).hexdigest().lower()
        expected = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
        self.assertEqual(uel_sha, expected, "Production UEL hash mismatch")

    def test_02_checkpoint_displacements_and_bounds_authenticity(self):
        """Verify that initial nodal displacements match Package 136 checkpoint (4,588 nodes, u2 = 0.0019829052 mm)."""
        disp_path = os.path.join(self.pkg_dir, "nodal_displacements_initial.csv")
        with open(disp_path, "r") as f:
            lines = f.readlines()
        # header + 4588 physical nodes
        self.assertEqual(len(lines), 4589, "Must have header + 4588 physical nodes")
        # Check top boundary node displacement (e.g. node 4489)
        top_node_found = False
        for l in lines:
            parts = [p.strip() for p in l.split(",")]
            if parts[0] == "4489":
                top_node_found = True
                u2 = float(parts[2])
                self.assertAlmostEqual(u2, 0.0019829052, places=7)
        self.assertTrue(top_node_found, "Top boundary node 4489 must exist in initial displacements")

    def test_03_d0_h0_column_separation(self):
        """Verify that d_lower_bounds.csv has correct separation of D0 (cols 1-4) and H0 (cols 5-8)."""
        bounds_path = os.path.join(self.pkg_dir, "d_lower_bounds.csv")
        with open(bounds_path, "r") as f:
            lines = f.readlines()
        header = [h.strip() for h in lines[0].split(",")]
        self.assertEqual(header[0], "EID")
        self.assertEqual(header[1:5], ["D0_1", "D0_2", "D0_3", "D0_4"])
        self.assertEqual(header[5:9], ["H0_1", "H0_2", "H0_3", "H0_4"])
        self.assertEqual(len(lines), 4423, "Must have header + 4422 quad elements")

        # Check values in first data row
        vals = [float(x) for x in lines[1].split(",")]
        for d in vals[1:5]:
            self.assertGreaterEqual(d, 0.0)
            self.assertLessEqual(d, 1.0)
        for h in vals[5:9]:
            self.assertGreaterEqual(h, 0.0)

    def test_04_exact_displacement_in_input_deck(self):
        """Verify that M1_C4_INC89_H27_CONT.inp prescribes exact donor Increment 89 displacement."""
        inp_path = os.path.join(self.pkg_dir, "M1_C4_INC89_H27_CONT.inp")
        with open(inp_path, "r") as f:
            content = f.read()
        self.assertIn("N_RP, 2, 2, 0.001990107350", content)

    def test_05_driver_kinematics_and_targets(self):
        """Verify driver parameters: omega=0.70, cap=35, target u=0.001990107350 mm, donor targets."""
        driver_path = os.path.join(self.pkg_dir, "driver_c4_donor_inc89_h27_continuation.py")
        with open(driver_path, "r") as f:
            code = f.read()
        self.assertIn("OMEGA = 0.70", code)
        self.assertIn("max_am_cycles = 35", code)
        self.assertIn("u_target_inc89_mm = 0.001990107350", code)
        self.assertIn("u_init_inc89_mm = 0.001982905200", code)
        self.assertIn("delta_u_target_mm = 0.000007202150", code)

    def test_06_pbs_script_directives(self):
        """Verify PBS script directives: queue, resources, walltime, notifications."""
        pbs_path = os.path.join(self.pkg_dir, "submit_M1_C4_INC89_H27_CONT.pbs")
        with open(pbs_path, "r") as f:
            pbs = f.read()
        self.assertIn("#PBS -N M1_C4_INC89_H27_CONT", pbs)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", pbs)
        self.assertIn("#PBS -l walltime=08:00:00", pbs)
        self.assertIn("#PBS -m abe", pbs)
        self.assertIn("pr21vyci@mailserver.tu-freiberg.de", pbs)
        self.assertIn("notification_install_terminal_trap", pbs)

    def test_07_manifest_schema_and_hashes(self):
        """Verify that all manifest entries correspond to actual files on disk with matching hashes."""
        for fname, expected_hash in self.manifest["files"].items():
            fpath = os.path.join(self.pkg_dir, fname)
            self.assertTrue(os.path.exists(fpath), "Missing file: %s" % fname)
            with open(fpath, "rb") as f:
                actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
            self.assertEqual(actual_hash, expected_hash.lower(), "Hash mismatch for %s" % fname)

if __name__ == "__main__":
    unittest.main()
