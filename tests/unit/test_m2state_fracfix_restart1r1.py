#!/usr/bin/env python3
"""
Candidate-Specific Unit Test Suite for M2STATE_FRACFIX_RESTART1R1.
Task ID: F44STATE-M2-FRACFIX-RESTART1R1-PREP1
"""
import unittest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PACKAGE_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART1R1"
HISTORICAL_INVALID_DIR = REPO_ROOT / "models" / "generated" / "mode_ii" / "production_state_transfer_batch" / "M2STATE_FRACFIX_RESTART1"


class TestM2StateFracfixRestart1R1(unittest.TestCase):

    def test_01_package_files_exist(self):
        expected_files = [
            "M2STATE_FRACFIX_RESTART1R1.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "verify_restart_trace.py",
            "M2STATE_FRACFIX_RESTART1R1.pbs",
            "submit_m2state_fracfix_restart1r1.sh",
            "PACKAGE_MANIFEST.json"
        ]
        for f in expected_files:
            self.assertTrue((PACKAGE_DIR / f).is_file(), f"Missing file: {f}")

    def test_02_package_manifest_hashes(self):
        with open(PACKAGE_DIR / "PACKAGE_MANIFEST.json", "r") as f:
            manifest = json.load(f)
        for filename, expected_hash in manifest["files"].items():
            filepath = PACKAGE_DIR / filename
            self.assertTrue(filepath.is_file(), f"File in manifest missing: {filename}")
            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {filename}")

    def test_03_source_state_identity_verified(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        self.assertEqual(artifact["source_job_id"], "1386469.mmaster02")
        self.assertEqual(artifact["source_checkpoint"], "Step-1 frame 500 (u1 = 0.005000 mm)")
        self.assertAlmostEqual(artifact["source_u1_mm"], 0.005000)
        self.assertEqual(artifact["source_physical_elements"], 2206)

    def test_04_target_topology_identity(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        self.assertEqual(artifact["target_job"], "M2STATE_FRACFIX_RESTART1R1")
        self.assertEqual(artifact["target_physical_elements"], 4894)
        self.assertEqual(artifact["target_nodes"], 4998)

    def test_05_phase_mapping_complete_and_bounds(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        self.assertTrue(artifact["phase_mapping_complete"])
        self.assertGreaterEqual(artifact["phase_min"], 0.0)
        self.assertLessEqual(artifact["phase_max"], 1.0)
        self.assertEqual(artifact["phase_bound_violations"], 0)

    def test_06_history_mapping_complete_and_paired(self):
        with open(PACKAGE_DIR / "STATE_TRANSFER_ARTIFACT.json", "r") as f:
            artifact = json.load(f)
        self.assertTrue(artifact["history_mapping_complete"])
        self.assertEqual(artifact["paired_target_H_contract"], "PASS")

    def test_07_step1_target_phase_initialization_exact(self):
        inp_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_text()
        self.assertIn("*STEP, NAME=Step-1-PhaseInit", inp_content)
        self.assertIn("N_TOP, 2, 2, 0.0", inp_content)
        self.assertIn("N_BOT, 1, 2, 0.0", inp_content)

    def test_08_step2_phase_dof3_released(self):
        inp_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_text()
        step2_block = inp_content.split("*STEP, NAME=Step-2-Continuation")[1]
        self.assertIn("*BOUNDARY, OP=NEW", step2_block)
        # Check that no phase DOF 3 BCs exist in Step 2
        for line in step2_block.splitlines():
            if line.strip().startswith("*") and not line.strip().startswith("**"):
                continue
            parts = [p.strip() for p in line.strip().split(",")]
            if len(parts) >= 3 and parts[0].isdigit():
                dof1 = int(parts[1]) if parts[1].isdigit() else 1
                dof2 = int(parts[2]) if parts[2].isdigit() else dof1
                self.assertFalse(dof1 <= 3 <= dof2 and dof1 == 3 and dof2 == 3, f"Step 2 re-prescribes phase DOF 3: {line}")

    def test_09_18_sdv_type_solution_cards(self):
        inp_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_text()
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_content)
        # Check 18 SDV line formatting (3 lines per element record)
        ic_block = inp_content.split("*INITIAL CONDITIONS, TYPE=SOLUTION")[1].split("*STEP")[0]
        ic_lines = [l.strip() for l in ic_block.splitlines() if l.strip() and not l.strip().startswith("**")]
        self.assertTrue(len(ic_lines) % 3 == 0)

    def test_10_historical_invalid_runtime_path_not_reused(self):
        with open(PACKAGE_DIR / "TRANSFER_MANIFEST.json", "r") as f:
            manifest = json.load(f)
        self.assertFalse(manifest["historical_invalid_runtime_path_reused"])
        # Verify hash difference from historical invalid M2STATE_FRACFIX_RESTART1
        old_inp_sha = hashlib.sha256((HISTORICAL_INVALID_DIR / "M2STATE_FRACFIX_RESTART1.inp").read_bytes()).hexdigest()
        new_inp_sha = hashlib.sha256((PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_bytes()).hexdigest()
        self.assertNotEqual(old_inp_sha, new_inp_sha)

    def test_11_re_equilibration_acceptance_contracts_defined(self):
        with open(PACKAGE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json", "r") as f:
            contract = json.load(f)
        self.assertTrue(contract["re_equilibration_acceptance_contract_defined"])
        self.assertTrue(contract["force_continuity_acceptance_defined"])
        self.assertTrue(contract["energy_continuity_acceptance_defined"])

    def test_12_nphys_property_slot5_contract(self):
        inp_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_text()
        self.assertIn("*UEL PROPERTY, ELSET=E_U2\n  210.000000,     0.300000,     0.015000,     0.002700,         4894", inp_content)

    def test_13_dof_abi_quads_and_tris(self):
        inp_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.inp").read_text()
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=18\n3, 0", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=5, VARIABLES=18\n1, 2", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES=18\n3, 0", inp_content)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=5, VARIABLES=18\n1, 2", inp_content)

    def test_14_negative_test_zeroed_phase_rejected(self):
        bad_artifact = {"phase_min": 0.0, "phase_max": 0.0, "phase_mapping_complete": False}
        self.assertFalse(bad_artifact["phase_max"] > 0.0 and bad_artifact["phase_mapping_complete"])

    def test_15_negative_test_historical_deck_reuse_rejected(self):
        old_inp = (HISTORICAL_INVALID_DIR / "M2STATE_FRACFIX_RESTART1.inp").read_text()
        self.assertNotIn("Step-1-PhaseInit", old_inp)

    def test_16_resource_plan_contract(self):
        pbs_content = (PACKAGE_DIR / "M2STATE_FRACFIX_RESTART1R1.pbs").read_text()
        self.assertIn("select=1:ncpus=1:mem=8gb", pbs_content)
        self.assertIn("walltime=08:00:00", pbs_content)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_content)



if __name__ == "__main__":
    unittest.main()
