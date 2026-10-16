import hashlib
import json
import os
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class TestMode1F1510AuditSameMeshTransferState(unittest.TestCase):
    """
    Unit test suite for Task F1510:
    Auditing same-mesh transfer state, resolving the 0.318142 vs 0.304553 damage discrepancy,
    and verifying consistent least-squares reconstruction versus lumped area-weighting.
    """

    def setUp(self):
        self.p40_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "40_method_b_corrected_propagation_14k"
        self.p49_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"
        self.state_json = self.p40_dir / "evidence_1412465" / "fine_baseline_14k_u0050_state.json"
        self.baseline_inp = self.p40_dir / "M1_MB_CORRECTED_PROPAGATION_14K.inp"
        self.samemesh_inp = self.p49_dir / "M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp"
        self.consistent_inp = self.p49_dir / "M1_MC_STAGE_C1_1_SAMEMESH_CONSISTENT_RELHOLD.inp"
        self.hpc_ledger = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"

    def test_01_baseline_odb_nodal_output_card_restriction(self):
        """Test 1: Verify baseline input deck restricts NODE OUTPUT to N_RP, explaining missing mesh U3."""
        self.assertTrue(self.baseline_inp.exists())
        text = self.baseline_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("*NODE OUTPUT, NSET=N_RP", text)

    def test_02_element_sdv14_versus_lumped_nodal_damage_discrepancy(self):
        """Test 2: Mathematically reconcile 0.318142 (element average SDV14) vs 0.304553 (lumped nodal damage)."""
        self.assertTrue(self.state_json.exists())
        with open(self.state_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        # 0.318142 is element 661 average damage stored in SDV14
        elem_661_sdv14 = data["elem_sdv"]["661"]["SDV14"]
        avg_d_661 = sum(elem_661_sdv14) / len(elem_661_sdv14)
        self.assertAlmostEqual(avg_d_661, 0.318142, places=5)

        # Surrounding elements sharing node 1384
        eids = ["661", "2393", "2498", "2589"]
        avg_surrounding = [sum(data["elem_sdv"][e]["SDV14"]) / len(data["elem_sdv"][e]["SDV14"]) for e in eids]
        mean_surrounding = sum(avg_surrounding) / len(avg_surrounding)

        # Mean of surrounding elements is ~0.30435, matching area-weighted lumped value 0.304553
        self.assertAlmostEqual(mean_surrounding, 0.30435, places=3)

        # Verify prescribed value in M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD.inp at node 1384 is 0.304553
        self.assertTrue(self.samemesh_inp.exists())
        text = self.samemesh_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("1384, 3, 3,  3.0455264e-01", text)

    def test_03_consistent_least_squares_nodal_reconstruction(self):
        """Test 3: Verify consistent least-squares reconstruction resolves crack-tip peak without attenuation."""
        self.assertTrue(self.consistent_inp.exists())
        text = self.consistent_inp.read_text(encoding="utf-8", errors="ignore")

        # Peak node 129 has un-attenuated damage 0.342331
        self.assertIn("129, 3, 3,  3.42331", text)
        # Node 1384 has consistent damage 0.319037
        self.assertIn("1384, 3, 3,  3.19037", text)

    def test_04_consistent_deck_structure_and_hashes(self):
        """Test 4: Verify consistent same-mesh deck SHA-256 and required step keywords."""
        deck_sha = hashlib.sha256(self.consistent_inp.read_bytes()).hexdigest().lower()
        self.assertEqual(deck_sha, "95001de57c6adb30077c2125f30ac44b0f788d77ceecae23ae7f6e28eab7f439")

        text = self.consistent_inp.read_text(encoding="utf-8", errors="ignore")
        self.assertIn("*STEP, NAME=Step-1-Equilibrate", text)
        self.assertIn("*STEP, NAME=Step-2-ReleaseHold", text)
        self.assertIn("*BOUNDARY, OP=NEW", text)
        self.assertIn("N_RP, 2, 2, 5.0000000000e-03", text)

    def test_05_job_1414558_preservation_in_hpc_ledger(self):
        """Test 5: Verify Job 1414558 remains recorded in HPC job ledger and is preserved."""
        self.assertTrue(self.hpc_ledger.exists())
        ledger_text = self.hpc_ledger.read_text(encoding="utf-8")
        self.assertIn("1414558.mmaster02", ledger_text)
        self.assertIn("M1_MC_STAGE_C1_1_SAMEMESH_RELHOLD", ledger_text)


if __name__ == "__main__":
    unittest.main()
