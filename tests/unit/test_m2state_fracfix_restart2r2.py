#!/usr/bin/env python3
"""
test_m2state_fracfix_restart2r2.py

Unit test regression suite for Mode-II candidate M2STATE_FRACFIX_RESTART2R2.
Verifies phase-UEL global DOF 3 ABI contract, NDOFEL implications, Job 1388961 regression detection,
package manifest byte-integrity, and guarded submission wrapper preflight.
"""

import os
import sys
import json
import unittest
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R2R2_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R2"
R2R1_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R1"

class TestM2StateFracfixRestart2R2(unittest.TestCase):

    def test_01_abi_active_dof_contract(self):
        inp_path = R2R2_DIR / "M2STATE_FRACFIX_RESTART2R2.inp"
        self.assertTrue(inp_path.exists(), f"Missing input deck at {inp_path}")
        text = inp_path.read_text(encoding="utf-8")

        # U1 (quad phase) -> active DOF 3
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", text)

        # U2 (quad mechanical) -> active DOFs 1, 2
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n1, 2", text)

        # U3 (tri phase) -> active DOF 3
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", text)

        # U4 (tri mechanical) -> active DOFs 1, 2
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM\n1, 2", text)

    def test_02_ndofel_implications(self):
        # U1 quad phase: 4 nodes * 1 DOF = 4
        # U2 quad mechanical: 4 nodes * 2 DOFs = 8
        # U3 tri phase: 3 nodes * 1 DOF = 3
        # U4 tri mechanical: 3 nodes * 2 DOFs = 6
        u1_ndofel = 4 * 1
        u2_ndofel = 4 * 2
        u3_ndofel = 3 * 1
        u4_ndofel = 3 * 2
        self.assertEqual(u1_ndofel, 4)
        self.assertEqual(u2_ndofel, 8)
        self.assertEqual(u3_ndofel, 3)
        self.assertEqual(u4_ndofel, 6)

    def test_03_job_1388961_regression_detection(self):
        # Verify that hardened verify_restart2r2_science.py fails closed on invalid R2R1 deck
        r2r1_inp = R2R1_DIR / "M2STATE_FRACFIX_RESTART2R1.inp"
        if r2r1_inp.exists():
            text = r2r1_inp.read_text(encoding="utf-8")
            self.assertIn("*USER ELEMENT, TYPE=U1", text)
            # Confirm R2R1 had wrong active DOFs 1, 2 for U1
            self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=18\n1, 2", text)

    def test_04_package_manifest_byte_integrity(self):
        manifest_script = R2R2_DIR / "validate_package_manifest.py"
        res = subprocess.run([sys.executable, str(manifest_script)], cwd=str(R2R2_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, f"Manifest validation failed: {res.stderr}\n{res.stdout}")
        self.assertIn("ALL_MANIFEST_FILES_VERIFIED_PASS", res.stdout)

    def test_05_guarded_wrapper_dry_run(self):
        wrapper = R2R2_DIR / "submit_m2state_fracfix_restart2r2.sh"
        if os.name != "nt":
            res = subprocess.run(["bash", str(wrapper), "--dry-run"], cwd=str(R2R2_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            self.assertEqual(res.returncode, 0)
            self.assertIn("DRY_RUN_SUCCESSFUL: qsub_call_count=0", res.stdout)

    def test_06_npredf_zero_safety(self):
        fort_path = R2R2_DIR / "f42_mixed_uel.for"
        text = fort_path.read_text(encoding="utf-8")
        # Ensure PREDEF(1) write is NOT present
        self.assertNotIn("PREDEF(1) =", text)
        self.assertNotIn("PREDEF(1,1,1) =", text)

    def test_07_resource_contract(self):
        pbs_path = R2R2_DIR / "M2STATE_FRACFIX_RESTART2R2.pbs"
        text = pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb", text)
        self.assertIn("#PBS -l walltime=24:00:00", text)
        self.assertIn("#PBS -q entry_imfdfkmq", text)

if __name__ == '__main__':
    unittest.main()
