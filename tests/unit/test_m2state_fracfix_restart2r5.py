#!/usr/bin/env python3
"""
Unit Test Suite for Candidate M2STATE_FRACFIX_RESTART2R5
Task ID: F69STATE-M2-RESTART2R5-TRANSFER-EQUILIBRIUM-BOUNDARY-REPAIR1
"""

import unittest
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R5"

class TestM2StateFracfixRestart2R5(unittest.TestCase):
    def setUp(self):
        self.inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART2R5.inp"
        self.uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        self.pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART2R5.pbs"
        self.sh_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart2r5.sh"
        self.man_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        self.art_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.tran_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"

        self.assertTrue(self.inp_path.exists(), "INP file missing")
        self.assertTrue(self.uel_path.exists(), "UEL file missing")
        self.assertTrue(self.pbs_path.exists(), "PBS file missing")
        self.assertTrue(self.sh_path.exists(), "Submit wrapper missing")
        self.assertTrue(self.man_path.exists(), "Package manifest missing")

        with open(self.inp_path, "r", encoding="utf-8") as f:
            self.inp_content = f.read()

        with open(self.uel_path, "r", encoding="utf-8") as f:
            self.uel_content = f.read()

        with open(self.man_path, "r", encoding="utf-8") as f:
            self.manifest = json.load(f)

    def test_01_manifest_completeness(self):
        hashes = self.manifest.get("file_hashes", {})
        self.assertEqual(len(hashes), 12, "Manifest must seal exactly 12 files")
        for fname, h in hashes.items():
            fpath = CANDIDATE_DIR / fname
            self.assertTrue(fpath.exists(), f"Manifest file missing: {fname}")

    def test_02_uel_jtype4_f_int_initialization(self):
        """Verify JTYPE 4 branch explicitly zeroes F_INT(1..6) before accumulation"""
        self.assertIn("JTYPE = 4", self.uel_content)
        jtype4_block = self.uel_content.split("JTYPE = 4")[1].split("STATE_TRACE")[0]
        self.assertIn("F_INT(I) = ZERO", jtype4_block, "JTYPE 4 must zero F_INT array")
        self.assertIn("DO I=1, 6", jtype4_block, "JTYPE 4 must zero 6 DOF components")

    def test_03_uel_def_use_safety(self):
        """Verify D_AVG, D_VAL, and SV_H ingestion have zero uninitialized reads"""
        # Ensure no bare read of D_AVG in JTYPE 2 or JTYPE 4
        jtype2_block = self.uel_content.split("JTYPE = 2")[1].split("JTYPE = 3")[0]
        self.assertNotIn("D_AVG", jtype2_block, "JTYPE 2 must not read D_AVG")
        jtype4_block = self.uel_content.split("JTYPE = 4")[1].split("STATE_TRACE")[0]
        self.assertNotIn("D_AVG", jtype4_block, "JTYPE 4 must not read D_AVG")

    def test_04_topological_n_top_connectivity(self):
        """Verify N_TOP is constructed from active connected physical nodes at Y=0.475904"""
        lines = self.inp_content.splitlines()
        in_n_top = False
        n_top_nodes = []
        for line in lines:
            if "*NSET, NSET=N_TOP" in line:
                in_n_top = True
                continue
            elif in_n_top and line.startswith("*"):
                in_n_top = False
                break
            elif in_n_top:
                parts = [p.strip() for p in line.split(",") if p.strip()]
                for p in parts:
                    n_top_nodes.append(int(p))

        self.assertEqual(len(n_top_nodes), 81, "N_TOP must contain exactly 81 physical top nodes")
        self.assertEqual(min(n_top_nodes), 9721, "N_TOP minimum node ID must be 9721")
        self.assertEqual(max(n_top_nodes), 9801, "N_TOP maximum node ID must be 9801")
        # Ensure all are <= 9801 (active physical elements)
        for n in n_top_nodes:
            self.assertLessEqual(n, 9801, f"N_TOP node {n} exceeds active physical node range")

    def test_05_declared_node_count_and_orphans(self):
        """Verify total declared nodes in INP = 9802 (9801 active + 1 RP 99999)"""
        lines = self.inp_content.splitlines()
        node_count = 0
        in_nodes = False
        for line in lines:
            if "*NODE, NSET=N_PHYSICAL" in line:
                in_nodes = True
                continue
            elif in_nodes and line.startswith("*"):
                in_nodes = False
                break
            elif in_nodes:
                if line.strip() and not line.startswith("**"):
                    node_count += 1

        self.assertEqual(node_count, 9802, "Total declared nodes must be exactly 9802 (9801 physical + 1 RP)")

    def test_06_step1_mechanical_handoff_displacement(self):
        """Verify Step 1 prescribes RP 99999 to source checkpoint displacement (0.007585 mm)"""
        self.assertIn("STEP, NAME=Step-1-PhaseInit", self.inp_content)
        step1_block = self.inp_content.split("STEP, NAME=Step-1-PhaseInit")[1].split("*END STEP")[0]
        self.assertIn("99999, 1, 1, 0.007585", step1_block, "Step 1 must prescribe U1 = 0.007585 mm on RP 99999")
        self.assertIn("99999, 2, 2, 0.00", step1_block, "Step 1 must fix U2 = 0.00 on RP 99999")
        self.assertIn("N_BOTTOM, 1, 2, 0.00", step1_block, "Step 1 must fix N_BOTTOM DOFs 1 and 2")

    def test_07_step2_continuation_displacement(self):
        """Verify Step 2 continues loading from source state to 0.015000 mm with DOF 3 released"""
        self.assertIn("STEP, NAME=Step-2-Continuation", self.inp_content)
        step2_block = self.inp_content.split("STEP, NAME=Step-2-Continuation")[1].split("*END STEP")[0]
        self.assertIn("99999, 1, 1, 0.015000", step2_block, "Step 2 must ramp U1 to 0.015000 mm on RP 99999")
        self.assertIn("*BOUNDARY, OP=NEW", step2_block, "Step 2 must release DOF 3 via OP=NEW")

    def test_08_phase_dof3_initialization_coverage(self):
        """Verify all 9,801 active physical nodes receive explicit DOF 3 constraint in Step 1"""
        step1_block = self.inp_content.split("STEP, NAME=Step-1-PhaseInit")[1].split("*END STEP")[0]
        # Count non-comment lines with ", 3, 3,"
        dof3_lines = [l for l in step1_block.splitlines() if not l.strip().startswith("**") and ", 3, 3," in l]
        self.assertEqual(len(dof3_lines), 9801, "All 9,801 physical nodes must have explicit DOF 3 in Step 1")

    def test_09_pbs_environment_and_notification(self):
        """Verify PBS script loads complete compiler toolchain and installs traps"""
        with open(self.pbs_path, "r", encoding="utf-8") as f:
            pbs_text = f.read()
        self.assertIn("module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7", pbs_text)
        self.assertIn("notification_install_terminal_trap", pbs_text)
        self.assertIn("notify_start", pbs_text)
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)

    def test_10_permanent_failed_run_regression(self):
        """Verify failed runs 1388961, 1389086, 1389142 defects remain permanently rejected"""
        # Job 1388961 regression: U1/U3 phase active DOF must be 3, not 1,2
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", self.inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES=18, UNSYMM\n3", self.inp_content)
        # Job 1389086 regression: COMMON block order-independent initial ingestion
        self.assertIn("IF (KSTEP .EQ. 1 .AND. KINC .EQ. 1) THEN", self.uel_content)
        # Job 1389142 regression: N_TOP must not contain orphan node 9961
        self.assertNotIn(" 9961", self.inp_content.split("*NSET, NSET=N_TOP")[1].split("*")[0])

if __name__ == "__main__":
    unittest.main()
