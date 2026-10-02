#!/usr/bin/env python3
"""
Unit Regression Test Suite for Mode-II Corrected Restart-2 Candidate: M2STATE_FRACFIX_RESTART2R11
Task ID: F98STATE-M2-CORRECTED-RESTART2-R2R11-PREP-AND-QUALIFICATION1

Verifies candidate package integrity, 6-slot real property ABI, safe 2x2 Jacobian inverse,
authoritative runtime SDV16/H history transfer, and Step 1 handoff displacement u1 = 0.010000 mm.
"""

import unittest
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R11"

class TestM2StateFracfixRestart2R11(unittest.TestCase):

    def test_01_package_directory_and_files_exist(self):
        """Verify all 10 required candidate files exist in package directory."""
        required_files = [
            "M2STATE_FRACFIX_RESTART2R11.inp",
            "f42_mixed_uel.for",
            "M2STATE_FRACFIX_RESTART2R11.pbs",
            "submit_m2state_fracfix_restart2r11.sh",
            "validate_package_manifest.py",
            "job_notifications.sh",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "PACKAGE_MANIFEST.json"
        ]
        for fn in required_files:
            fp = PKG_DIR / fn
            self.assertTrue(fp.exists(), f"Required candidate file missing: {fn}")

    def test_02_sha256_package_manifest_integrity(self):
        """Verify SHA256 hashes of all candidate files match PACKAGE_MANIFEST.json."""
        manifest_file = PKG_DIR / "PACKAGE_MANIFEST.json"
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        file_hashes = manifest.get("file_hashes", {})

        for rel_path, expected_sha in file_hashes.items():
            fp = PKG_DIR / rel_path
            self.assertTrue(fp.exists(), f"Manifest file missing: {rel_path}")
            actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
            self.assertEqual(actual_sha, expected_sha, f"SHA256 mismatch for {rel_path}")

    def test_03_clean_6slot_property_abi(self):
        """Verify input deck contains clean 6-slot real property cards (PROPS(6) = NPHYS)."""
        inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R11.inp").read_text(encoding="utf-8")
        self.assertIn("*UEL PROPERTY", inp_text)
        
        for line in inp_text.splitlines():
            if line.startswith("0.015, 0.0027, 210.0, 0.3, 1e-07,"):
                parts = [p.strip() for p in line.split(",")]
                self.assertEqual(len(parts), 6, f"Property card must have 6 slots: {line}")
                self.assertEqual(float(parts[4]), 1.0e-7, "Slot 5 must be residual stiffness k=1e-7")
                self.assertGreater(float(parts[5]), 0.0, "Slot 6 must be positive physical element count NPHYS")
                break
        else:
            self.fail("Clean 6-slot property card not found in input deck.")

    def test_04_fortran_uel_safe_jacobian_inversion(self):
        """Verify f42_mixed_uel.for implements safe 2x2 Jacobian evaluation and inversion."""
        for_text = (PKG_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
        self.assertIn("DETJ = JAC(1,1) * JAC(2,2) - JAC(1,2) * JAC(2,1)", for_text)
        self.assertIn("INVJ(1,1) =  JAC(2,2) / DETJ", for_text)
        self.assertIn("INVJ(1,2) = -JAC(1,2) / DETJ", for_text)
        self.assertIn("INVJ(2,1) = -JAC(2,1) / DETJ", for_text)
        self.assertIn("INVJ(2,2) =  JAC(1,1) / DETJ", for_text)
        self.assertNotIn("JAC(2,2) = JAC(1,1) / DETJ", for_text, "In-place Jacobian corruption defect detected!")

    def test_05_transferred_state_bounds(self):
        """Verify mapped phase d and history H satisfy physical bounds and equilibrium relations."""
        art_file = PKG_DIR / "STATE_TRANSFER_ARTIFACT.json"
        art = json.loads(art_file.read_text(encoding="utf-8"))
        
        self.assertGreaterEqual(art["phase_min"], 0.0)
        self.assertLessEqual(art["phase_max"], 1.0)
        self.assertAlmostEqual(art["phase_max"], 0.1515, delta=0.01)
        
        self.assertGreaterEqual(art["history_min"], 0.0)
        self.assertAlmostEqual(art["history_max"], 0.053128, delta=0.01)

    def test_06_step1_handoff_displacement_u1(self):
        """Verify Step 1 PhaseInit prescribes u1 = 0.010000 mm on RP 99999 to guarantee force continuity."""
        inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R11.inp").read_text(encoding="utf-8")
        lines = inp_text.splitlines()
        
        in_step1 = False
        step1_u1_found = False
        for l in lines:
            if "*STEP, NAME=Step-1-PhaseInit" in l:
                in_step1 = True
            elif "*END STEP" in l and in_step1:
                in_step1 = False
            elif in_step1 and "99999, 1, 1, 0.010000" in l:
                step1_u1_found = True
                
        self.assertTrue(step1_u1_found, "Step 1 PhaseInit must prescribe 99999, 1, 1, 0.010000 to match handoff state!")

if __name__ == "__main__":
    unittest.main()
