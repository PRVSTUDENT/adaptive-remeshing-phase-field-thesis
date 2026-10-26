# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn210_package114_qualification.py
===================================================
Independent qualification and verification test suite for Package 114
(Mode-I Candidate C4 Exact Increment-79 Companion MISESERI Diagnostic).

Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 210)
"""
import os
import json
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG114_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "114_c4_inc79_companion_miseseri")
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def get_sha256(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest().upper()

class TestPackage114Qualification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest_path = os.path.join(PKG114_DIR, "PACKAGE_MANIFEST.json")
        auth_path = os.path.join(PKG114_DIR, "M1_C4_INC79_COMPANION_AUTHORIZATION.json")
        audit_path = os.path.join(REPO_ROOT, "results", "validation", "audit_package114_companion_formulation.json")

        with open(manifest_path, "r") as f:
            cls.manifest = json.load(f)
        with open(auth_path, "r") as f:
            cls.auth = json.load(f)
        with open(audit_path, "r") as f:
            cls.audit = json.load(f)

    def test_01_file_existence_and_hashes(self):
        """Verify all Package 114 files exist and match manifest hashes."""
        files = self.manifest["files"]
        self.assertEqual(len(files), 5)
        for fname, exp_hash in files.items():
            fpath = os.path.join(PKG114_DIR, fname)
            self.assertTrue(os.path.exists(fpath), "Missing: %s" % fpath)
            act_hash = get_sha256(fpath)
            self.assertEqual(act_hash, exp_hash, "Hash mismatch for %s" % fname)

        # Verify frozen UEL matches frozen hash
        uel_path = os.path.join(PKG114_DIR, "f42_mixed_uel.for")
        self.assertEqual(get_sha256(uel_path), FROZEN_UEL_HASH)

    def test_02_mesh_topology_and_element_count(self):
        """Verify exact Candidate C4 mesh topology: 4,422 CPE4 quads and 4,588 nodes."""
        mesh_info = self.manifest["mesh"]
        self.assertEqual(mesh_info["name"], "Candidate C4")
        self.assertEqual(mesh_info["quad_count"], 4422)
        self.assertEqual(mesh_info["node_count"], 4588)
        self.assertEqual(mesh_info["element_type"], "CPE4")
        self.assertAlmostEqual(mesh_info["process_zone_h_fine_mm"], 0.000606, places=6)

    def test_03_exact_increment79_loading(self):
        """Verify prescribed displacement exactly matches Increment 79 (u_RP = 0.001842500 mm)."""
        loading = self.manifest["loading"]
        self.assertAlmostEqual(loading["prescribed_u2_mm"], 0.0018425, places=8)

        # Check in actual input deck text
        inp_path = os.path.join(PKG114_DIR, "M1_C4_INC79_COMPANION.inp")
        with open(inp_path, "r") as f:
            inp_text = f.read()
        self.assertIn("999999, 2, 2, 0.001842500", inp_text)
        self.assertNotIn("0.002052000", inp_text)

    def test_04_native_abaqus_miseseri_output(self):
        """Verify native Abaqus MISESERI and MISESAVG output requests."""
        outputs = self.manifest["outputs_requested"]
        self.assertIn("MISESERI", outputs)
        self.assertIn("MISESAVG", outputs)
        self.assertIn("S", outputs)
        self.assertIn("EVOL", outputs)

        inp_path = os.path.join(PKG114_DIR, "M1_C4_INC79_COMPANION.inp")
        with open(inp_path, "r") as f:
            inp_text = f.read()
        self.assertIn("S, MISESERI, MISESAVG, EVOL", inp_text)

    def test_05_phase_field_length_consistency(self):
        """Verify constitutive phase-field length scale l0 = 0.0075 mm = 7.5 um."""
        l0_audit = self.audit["phase_field_length_audit"]
        self.assertAlmostEqual(l0_audit["model_parameter_l0_mm"], 0.0075, places=5)
        self.assertAlmostEqual(l0_audit["model_parameter_l0_um"], 7.5, places=2)
        self.assertEqual(l0_audit["status"], "VERIFIED_L0_EQUALS_7P5_MICRONS")

    def test_06_companion_representation_validity(self):
        """Verify companion linear-elastic representation preserves 99.8% stiffness retention at Inc 79."""
        rep = self.audit["companion_representation_validity"]
        self.assertAlmostEqual(rep["prescribed_displacement_inc79_mm"], 0.0018425, places=7)
        self.assertAlmostEqual(rep["actual_pfm_reaction_force_N"], 187.3915, delta=0.01)
        self.assertGreater(rep["stiffness_retention_inc79_ratio"], 0.99)
        # Verify Package 95 had severe softening (only ~54% retention)
        self.assertLess(rep["stiffness_retention_pkg95_ratio"], 0.60)

    def test_07_pbs_and_notification_directives(self):
        """Verify PBS script has required mail directives and notification shell traps."""
        pbs_path = os.path.join(PKG114_DIR, "submit_M1_C4_INC79_COMPANION.pbs")
        with open(pbs_path, "r") as f:
            pbs_text = f.read()
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("notification_load_config", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)
        self.assertIn("abaqus job=M1_C4_INC79_COMPANION", pbs_text)

    def test_08_authorization_manifest_integrity(self):
        """Verify authorization manifest meets standing batch contract."""
        self.assertEqual(self.auth["batch_name"], "MODE1_PACKAGE_114_C4_INC79_COMPANION_MISESERI")
        self.assertEqual(self.auth["adapter"], "mode1-qualified-batch-v2")
        self.assertEqual(self.auth["max_submissions"], 1)
        self.assertEqual(len(self.auth["jobs"]), 1)
        job = self.auth["jobs"][0]
        self.assertEqual(job["id"], "M1_C4_INC79_COMPANION")
        self.assertEqual(job["cpus"], 1)
        self.assertEqual(job["memory_gb"], 8)
        self.assertEqual(job["walltime_hours"], 1)

if __name__ == "__main__":
    unittest.main()
