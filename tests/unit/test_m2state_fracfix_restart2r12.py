#!/usr/bin/env python3
"""
Unit Regression Test Suite for Candidate: M2STATE_FRACFIX_RESTART2R12
Task ID: F101STATE-M2-CORRECTED-RESTART2-R2R12-PREP-AND-QUALIFICATION1
"""

import unittest
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R12"

class TestM2StateFracfixRestart2R12(unittest.TestCase):

    def sha256_file(self, filepath):
        h = hashlib.sha256()
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def test_01_package_directory_exists(self):
        self.assertTrue(PKG_DIR.exists(), f"Package directory missing: {PKG_DIR}")

    def test_02_package_manifest_integrity(self):
        manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
        self.assertTrue(manifest_path.exists(), "PACKAGE_MANIFEST.json missing")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        
        for rel_fn, exp_sha in manifest["file_hashes"].items():
            fp = PKG_DIR / rel_fn
            self.assertTrue(fp.exists(), f"Manifest listed file missing: {rel_fn}")
            act_sha = self.sha256_file(fp)
            self.assertEqual(act_sha.lower(), exp_sha.lower(), f"SHA256 mismatch for {rel_fn}")

    def test_03_uel_property_abi_and_dofs(self):
        inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART2R12.inp"
        text = inp_path.read_text(encoding="utf-8")
        
        # Verify 6-property card
        self.assertIn("0.015, 0.0027, 210.0, 0.3, 1e-07, 9612", text)
        
        # Verify mechanical UEL requests DOFs 1, 2, 3
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0", text)
        self.assertIn("1, 2, 3", text)

    def test_04_fortran_uel_phase_consumption_repair(self):
        uel_path = PKG_DIR / "f42_mixed_uel.for"
        text = uel_path.read_text(encoding="utf-8")
        
        # Check that JTYPE=2/4 reads U(3*I) for phase d
        self.assertIn("D_NODE(I) = U(3*I)", text)
        self.assertIn("DEG = (1.0D0 - D_GP)**2 + K_RES", text)
        self.assertIn("MECH_MAP_QUAD", text)

    def test_05_step1_boundary_conditions(self):
        inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART2R12.inp"
        lines = inp_path.read_text(encoding="utf-8").splitlines()
        
        step1_found = False
        controls_found = False
        u1_found = False
        
        for l in lines:
            if "*STEP, NAME=Step-1-PhaseInit" in l:
                step1_found = True
            if step1_found and "*CONTROLS, PARAMETERS=FIELD" in l:
                controls_found = True
            if step1_found and "99999, 1, 1, 0.010000" in l:
                u1_found = True
                
        self.assertTrue(step1_found, "Step 1 missing")
        self.assertTrue(controls_found, "*CONTROLS missing in Step 1")
        self.assertTrue(u1_found, "u1 = 0.010000 mm missing in Step 1")

    def test_06_state_transfer_artifact(self):
        art_path = PKG_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.assertTrue(art_path.exists(), "STATE_TRANSFER_ARTIFACT.json missing")
        art = json.loads(art_path.read_text(encoding="utf-8"))
        
        self.assertEqual(art["candidate"], "M2STATE_FRACFIX_RESTART2R12")
        self.assertEqual(art["source_job_id"], "1389278.mmaster02")
        self.assertEqual(art["target_mesh"], "PK10R1")

if __name__ == "__main__":
    unittest.main()
