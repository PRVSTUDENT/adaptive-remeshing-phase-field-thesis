# -*- coding: utf-8 -*-
import hashlib
import json
import os
import unittest


class TestMode1F1597Package140Qualification(unittest.TestCase):
    """Independent technical qualification of Package 140 (Candidate C4 Increment-92 H31 Forward Continuation)."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(
            cls.repo_root, "models", "pandey_kumar_mode1", "140_c4_inc92_h31_underrelaxed_forward_continuation"
        )
        cls.manifest_path = os.path.join(cls.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(cls.manifest_path, "r") as f:
            cls.manifest = json.load(f)

    def test_01_frozen_uel_integrity(self):
        """Verify that the production UEL subroutine hash strictly matches frozen commit AB0A5A71..."""
        uel_path = os.path.join(self.pkg_dir, "f42_unified_12dof_active_set_uel.for")
        self.assertTrue(os.path.exists(uel_path))
        with open(uel_path, "rb") as f:
            uel_sha256 = hashlib.sha256(f.read()).hexdigest().lower()
        self.assertEqual(uel_sha256, "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac")

    def test_02_checkpoint_displacements_and_bounds_authenticity(self):
        """Verify that initial nodal displacements and bounds correspond to authentic Increment-91 checkpoint."""
        disp_path = os.path.join(self.pkg_dir, "nodal_displacements_initial.csv")
        self.assertTrue(os.path.exists(disp_path))
        with open(disp_path, "r") as f:
            lines = [line.strip().split(",") for line in f if line.strip() and not line.startswith("node_id")]
        self.assertEqual(len(lines), 4588)

        # Node 4489 is on top boundary: check its initial displacement matches Inc 91
        node_4489_disp = None
        for parts in lines:
            if parts[0].strip() == "4489":
                node_4489_disp = float(parts[2].strip())
                break
        self.assertIsNotNone(node_4489_disp)
        self.assertAlmostEqual(node_4489_disp, 0.002040107500, places=8)

    def test_03_d0_h0_column_separation(self):
        """Verify that d_lower_bounds.csv has strictly separate D0 and H0 columns and valid ranges."""
        bounds_path = os.path.join(self.pkg_dir, "d_lower_bounds.csv")
        self.assertTrue(os.path.exists(bounds_path))
        with open(bounds_path, "r") as f:
            header = [h.strip() for h in f.readline().split(",")]
        self.assertEqual(len(header), 9)
        self.assertEqual(header[0], "EID")
        self.assertEqual(header[1:5], ["D0_1", "D0_2", "D0_3", "D0_4"])
        self.assertEqual(header[5:9], ["H0_1", "H0_2", "H0_3", "H0_4"])

    def test_04_exact_displacement_in_input_deck(self):
        """Verify that M1_C4_INC92_H31_CONT.inp prescribes exact donor Increment 92 displacement."""
        inp_path = os.path.join(self.pkg_dir, "M1_C4_INC92_H31_CONT.inp")
        with open(inp_path, "r") as f:
            content = f.read()
        self.assertIn("N_RP, 2, 2, 0.002065107460", content)
        self.assertIn("N_RP, 2, 2, 0.0", content)

    def test_05_driver_kinematics_and_targets(self):
        """Verify that driver uses authentic Increment 91 checkpoint and targets Increment 92."""
        driver_path = os.path.join(self.pkg_dir, "driver_c4_inc92_h31_continuation.py")
        with open(driver_path, "r") as f:
            content = f.read()
        self.assertIn("0.002040107500", content)
        self.assertIn("0.002065107460", content)
        self.assertIn("0.000024999960", content)
        self.assertIn("omega = OMEGA", content)

    def test_06_pbs_script_directives(self):
        """Verify PBS execution script directives."""
        pbs_path = os.path.join(self.pkg_dir, "submit_M1_C4_INC92_H31_CONT.pbs")
        with open(pbs_path, "r") as f:
            content = f.read()
        self.assertIn("#PBS -N M1_C4_INC92_H31_CONT", content)
        self.assertIn("#PBS -q entry_imfdfkmq", content)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", content)
        self.assertIn("#PBS -l walltime=08:00:00", content)
        self.assertIn("#PBS -r n", content)
        self.assertIn("driver_c4_inc92_h31_continuation.py", content)

    def test_07_manifest_schema_and_hashes(self):
        """Verify PACKAGE_MANIFEST.json schema and exact file SHA-256 hashes."""
        self.assertEqual(self.manifest["schema"], 1)
        self.assertEqual(self.manifest["package_name"], "140_c4_inc92_h31_underrelaxed_forward_continuation")
        self.assertEqual(self.manifest["batch_name"], "MODE1_C4_INC92_H31_CONT")
        for fname, exp_hash in self.manifest["files"].items():
            fpath = os.path.join(self.pkg_dir, fname)
            self.assertTrue(os.path.exists(fpath), "Missing manifest file: %s" % fname)
            with open(fpath, "rb") as f:
                cur_hash = hashlib.sha256(f.read()).hexdigest().lower()
            self.assertEqual(cur_hash, exp_hash, "Hash mismatch for %s" % fname)


if __name__ == "__main__":
    unittest.main()
