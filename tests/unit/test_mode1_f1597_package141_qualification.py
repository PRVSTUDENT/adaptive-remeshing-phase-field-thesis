# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package141_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Independent technical qualification of Package 141 (Hypothesis H38 Candidate C3-Intermediate
Continuous Donor Simulation).
"""

import hashlib
import json
import os
import unittest


class TestMode1F1597Package141Qualification(unittest.TestCase):
    """Independent technical qualification of Package 141."""

    @classmethod
    def setUpClass(cls):
        cls.repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        cls.pkg_dir = os.path.join(
            cls.repo_root, "models", "pandey_kumar_mode1", "141_c3_int_donor_monotonic"
        )
        cls.manifest_path = os.path.join(cls.pkg_dir, "PACKAGE_MANIFEST.json")
        with open(cls.manifest_path, "r") as f:
            cls.manifest = json.load(f)
        cls.auth_path = os.path.join(cls.pkg_dir, "M1_C3_INT_DONOR_MONOTONIC_AUTHORIZATION.json")
        with open(cls.auth_path, "r") as f:
            cls.auth = json.load(f)

    def test_01_frozen_uel_integrity(self):
        """Verify that the production UEL subroutine hash strictly matches frozen commit CE8D5EDC..."""
        uel_path = os.path.join(self.pkg_dir, "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path))
        with open(uel_path, "rb") as f:
            uel_sha256 = hashlib.sha256(f.read()).hexdigest().lower()
        self.assertEqual(uel_sha256, "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6")

    def test_02_deck_element_and_layer_architecture(self):
        """Verify 3-layer UEL deck structure with 2,484 quads per layer and offset 2484."""
        inp_path = os.path.join(self.pkg_dir, "M1_C3_INT_DONOR_MONOTONIC.inp")
        self.assertTrue(os.path.exists(inp_path))
        with open(inp_path, "r") as f:
            content = f.read()

        # Check UEL property definitions
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM", content)
        self.assertIn("0.0075, 0.0027, 210.0, 0.3, 1e-07, 2484", content)
        self.assertIn("210.0, 0.3, 2484.0", content)

        # Check element counts and boundary element IDs
        self.assertIn("4968, 2529, 2530, 2585, 2584", content)  # End of Layer 2
        self.assertIn("7452, 2529, 2530, 2585, 2584", content)  # End of Layer 3

    def test_03_frame77_targeting_loading_schedule(self):
        """Verify two-step continuous loading schedule targeting exact Frame-77 displacement."""
        inp_path = os.path.join(self.pkg_dir, "M1_C3_INT_DONOR_MONOTONIC.inp")
        self.assertTrue(os.path.exists(inp_path))
        with open(inp_path, "r") as f:
            content = f.read()

        # Step 1: 0.36006251 s, 0.0018003125442191958 mm
        self.assertIn("*Step, name=Step-1, nlgeom=NO, inc=2000", content)
        self.assertIn("1.0e-3, 0.36006251, 1.0e-8, 5.0e-3", content)
        self.assertIn("N_RP, 2, 2, 0.0018003125442191958", content)

        # Step 2: 0.03993749 s, 0.0020000000 mm
        self.assertIn("*Step, name=Step-2, nlgeom=NO, inc=1000", content)
        self.assertIn("1.0e-3, 0.03993749, 1.0e-8, 5.0e-3", content)
        self.assertIn("N_RP, 2, 2, 0.0020000000000000000", content)

        # Verify restart and field output frequency = 1
        self.assertIn("*Restart, write, frequency=1", content)
        self.assertIn("*Output, field, frequency=1", content)

    def test_04_dual_channel_notification_contract(self):
        """Verify PBS execution script directives, trap handlers, and dual notifications."""
        pbs_path = os.path.join(self.pkg_dir, "submit_M1_C3_INT_DONOR_MONOTONIC.pbs")
        self.assertTrue(os.path.exists(pbs_path))
        with open(pbs_path, "r") as f:
            content = f.read()

        self.assertIn("#PBS -N M1_C3_INT_DONOR", content)
        self.assertIn("#PBS -l select=1:ncpus=1:mem=16gb", content)
        self.assertIn("#PBS -l walltime=08:00:00", content)
        self.assertIn("#PBS -m abe", content)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", content)
        self.assertIn('source "${RUN_DIR}/job_notifications.sh"', content)
        self.assertIn("notification_install_terminal_trap", content)
        self.assertIn("notify_start", content)

    def test_05_manifest_and_authorization_integrity(self):
        """Verify manifest and authorization metadata consistency."""
        self.assertEqual(self.manifest["package_number"], 141)
        self.assertEqual(self.auth["batch_name"], "MODE1_PACKAGE141_C3_INT_DONOR_MONOTONIC")
        self.assertEqual(self.auth["jobs"][0]["id"], "M1_C3_INT_DONOR_MONOTONIC")
        self.assertEqual(self.auth["jobs"][0]["cpus"], 1)
        self.assertEqual(self.auth["jobs"][0]["memory_gb"], 16)
        self.assertEqual(self.auth["jobs"][0]["walltime_hours"], 8)


if __name__ == "__main__":
    unittest.main()
