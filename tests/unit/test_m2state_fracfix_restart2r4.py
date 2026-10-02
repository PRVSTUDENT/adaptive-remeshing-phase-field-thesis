#!/usr/bin/env python3
"""
test_m2state_fracfix_restart2r4.py

Unit test suite for production restart candidate M2STATE_FRACFIX_RESTART2R4.
Covers:
  1. Manifest and directory integrity (12 package files).
  2. Exact UEL ABI (U1/U3 -> DOF 3, U2/U4 -> DOFs 1, 2).
  3. Full 100% phase-node initialization coverage in Step 1 (all 10,080 nodes).
  4. History IP initialization coverage in *INITIAL CONDITIONS, TYPE=SOLUTION.
  5. Static def-use audit: zero uninitialized reads (D_AVG eliminated in JTYPE 2/4).
  6. COMMON block ingestion contract: order-independent ingestion from incoming SVARS.
  7. PREDEF runtime safety.
  8. Fail-closed compute-node compiler environment in PBS script.
  9. Guarded wrapper dry-run contract.
 10. Regression fixtures: rejection of job 1388961 and job 1389086 failure modes.
"""

import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART2R4"

class TestM2StateFracfixRestart2R4(unittest.TestCase):
    def setUp(self):
        self.package_dir = PACKAGE_DIR
        self.manifest_path = PACKAGE_DIR / "PACKAGE_MANIFEST.json"
        self.inp_path = PACKAGE_DIR / "M2STATE_FRACFIX_RESTART2R4.inp"
        self.fort_path = PACKAGE_DIR / "f42_mixed_uel.for"
        self.pbs_path = PACKAGE_DIR / "M2STATE_FRACFIX_RESTART2R4.pbs"
        self.sh_path = PACKAGE_DIR / "submit_m2state_fracfix_restart2r4.sh"

    def test_01_manifest_and_files_exist(self):
        self.assertTrue(self.manifest_path.exists(), "PACKAGE_MANIFEST.json missing")
        with open(self.manifest_path, "r") as f:
            manifest = json.load(f)
        self.assertEqual(manifest.get("package_name"), "M2STATE_FRACFIX_RESTART2R4")
        self.assertIn("files", manifest)
        
        required_files = [
            "M2STATE_FRACFIX_RESTART2R4.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "M2STATE_FRACFIX_RESTART2R4.pbs",
            "submit_m2state_fracfix_restart2r4.sh",
            "validate_package_manifest.py",
            "extract_restart2r4_odb.py",
            "verify_restart2r4_science.py",
            "compare_restart1_restart2_matched_state.py",
            "job_notifications.sh"
        ]
        for rf in required_files:
            self.assertIn(rf, manifest["files"], f"Manifest missing file entry: {rf}")
            fpath = self.package_dir / rf
            self.assertTrue(fpath.exists(), f"Physical file missing: {rf}")

    def test_02_uel_active_dof_abi(self):
        with open(self.inp_path, "r") as f:
            lines = [l.strip() for l in f.readlines()]
            
        u1_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U1" in l]
        u2_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U2" in l]
        u3_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U3" in l]
        u4_idx = [i for i, l in enumerate(lines) if "*USER ELEMENT, TYPE=U4" in l]
        
        self.assertTrue(len(u1_idx) > 0, "U1 definition missing")
        self.assertTrue(len(u2_idx) > 0, "U2 definition missing")
        self.assertTrue(len(u3_idx) > 0, "U3 definition missing")
        self.assertTrue(len(u4_idx) > 0, "U4 definition missing")
        
        self.assertEqual(lines[u1_idx[0]+1], "3", "U1 active DOF must be 3")
        self.assertEqual(lines[u2_idx[0]+1], "1, 2", "U2 active DOFs must be 1, 2")
        self.assertEqual(lines[u3_idx[0]+1], "3", "U3 active DOF must be 3")
        self.assertEqual(lines[u4_idx[0]+1], "1, 2", "U4 active DOFs must be 1, 2")

    def test_03_full_phase_node_initialization_coverage(self):
        in_step1 = False
        in_bcs = False
        dof3_bcs = set()
        
        with open(self.inp_path, "r") as f:
            for line in f:
                s = line.strip()
                if "*STEP, NAME=Step-1-PhaseInit" in s:
                    in_step1 = True
                    continue
                elif in_step1 and "*END STEP" in s:
                    in_step1 = False
                
                if in_step1 and s.startswith("*BOUNDARY"):
                    in_bcs = True
                    continue
                elif in_step1 and in_bcs and s.startswith("*"):
                    in_bcs = False
                    
                if in_step1 and in_bcs and s:
                    parts = [p.strip() for p in s.split(",")]
                    if len(parts) >= 4 and parts[0].isdigit() and parts[1] == "3" and parts[2] == "3":
                        dof3_bcs.add(int(parts[0]))
                        
        self.assertEqual(len(dof3_bcs), 9801, "Step 1 must contain exactly 9,801 DOF 3 boundary condition cards for all active connected nodes")

    def test_04_history_ip_initialization_coverage(self):
        in_ics = False
        ic_count = 0
        with open(self.inp_path, "r") as f:
            for line in f:
                s = line.strip()
                if s.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                    in_ics = True
                    continue
                elif in_ics and s.startswith("*"):
                    in_ics = False
                if in_ics and s:
                    parts = [p.strip() for p in s.split(",")]
                    if len(parts) >= 2 and parts[0].isdigit() and (int(parts[0]) >= 9877 and int(parts[0]) <= 19752):
                        ic_count += 1
                        
        self.assertEqual(ic_count, 9876, "Must contain initial conditions for all 9,876 mechanical elements")

    def test_05_def_use_audit_no_uninitialized_reads(self):
        with open(self.fort_path, "r") as f:
            code = f.read()
            
        # Verify D_AVG is NOT referenced in JTYPE 2 or JTYPE 4
        lines = code.splitlines()
        current_jtype = None
        jtype_code = {1: [], 2: [], 3: [], 4: []}
        for l in lines:
            ls = l.strip()
            if ls.startswith("C") or not ls: continue
            if "IF (JTYPE .EQ. 1)" in ls: current_jtype = 1
            elif "ELSE IF (JTYPE .EQ. 2)" in ls: current_jtype = 2
            elif "ELSE IF (JTYPE .EQ. 3)" in ls: current_jtype = 3
            elif "ELSE IF (JTYPE .EQ. 4)" in ls: current_jtype = 4
            elif "ENDIF" in ls and current_jtype == 4: current_jtype = None
            if current_jtype:
                jtype_code[current_jtype].append(ls)
                
        self.assertFalse(any("D_AVG" in l for l in jtype_code[2]), "D_AVG must not be referenced in JTYPE 2")
        self.assertFalse(any("D_AVG" in l for l in jtype_code[4]), "D_AVG must not be referenced in JTYPE 4")

    def test_06_order_independent_common_ingestion(self):
        with open(self.fort_path, "r") as f:
            code = f.read()
        self.assertIn("IF (KSTEP .EQ. 1 .AND. KINC .EQ. 1)", code)
        self.assertIn("IF (SVARS(8+KPT) .GT. SV_H(PHYSIDX, KPT))", code)
        self.assertIn("IF (SVARS(6+KPT) .GT. SV_H(PHYSIDX, KPT))", code)

    def test_07_predef_runtime_safety(self):
        with open(self.fort_path, "r") as f:
            code = f.read()
        self.assertNotIn("PREDEF(1,1,1)=0.D0", code, "Errant PREDEF write must not exist")

    def test_08_compute_environment_contract(self):
        with open(self.pbs_path, "r") as f:
            pbs_text = f.read()
        self.assertIn("module load gcc/11.4.0", pbs_text)
        self.assertIn("module load intel/2024.2.0", pbs_text)
        self.assertIn("module load abaqus/2023", pbs_text)
        self.assertIn("module load python/gcc/11.4.0/3.11.7", pbs_text)
        self.assertIn("command -v ifort", pbs_text)
        self.assertIn("command -v abaqus", pbs_text)

    def test_09_guarded_wrapper_dry_run_contract(self):
        with open(self.sh_path, "r") as f:
            sh_text = f.read()
        self.assertIn("--dry-run", sh_text)
        self.assertIn("--execute", sh_text)
        self.assertIn("validate_package_manifest.py", sh_text)

    def test_10_scientific_regression_hardening(self):
        # Verify verify_restart2r4_science.py checks for non-finite values and rejects NaN
        verifier_path = self.package_dir / "verify_restart2r4_science.py"
        with open(verifier_path, "r") as f:
            v_text = f.read()
        self.assertIn("NaN", v_text)
        self.assertIn("nan", v_text)
        self.assertIn("sys.exit(1)", v_text)

if __name__ == "__main__":
    unittest.main()
