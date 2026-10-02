#!/usr/bin/env python3
"""
Candidate Qualification Test Suite for M2STATE_FRACFIX_RESTART1R1R2.
Task ID: F44STATE-M2-FRACFIX-RESTART1R1R2-FINAL-QUALIFICATION-CLOSURE1
"""

import os
import sys
import json
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R2"


class TestM2StateFracfixRestart1R1R2(unittest.TestCase):

    def setUp(self):
        self.candidate_dir = CANDIDATE_DIR
        self.inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R2.inp"
        self.uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        self.contract_path = CANDIDATE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
        self.manifest_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        self.artifact_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.transfer_manifest_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        self.checker_path = CANDIDATE_DIR / "verify_restart_trace.py"
        self.pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R2.pbs"
        self.submit_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart1r1r2.sh"

    def test_01_package_files_exist(self):
        expected_files = [
            "M2STATE_FRACFIX_RESTART1R1R2.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "verify_restart_trace.py",
            "M2STATE_FRACFIX_RESTART1R1R2.pbs",
            "submit_m2state_fracfix_restart1r1r2.sh",
            "PACKAGE_MANIFEST.json"
        ]
        for f in expected_files:
            p = self.candidate_dir / f
            self.assertTrue(p.exists(), f"Missing package file: {f}")

    def test_02_package_manifest_hashes(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        for fname, exp_hash in manifest["file_hashes"].items():
            fpath = self.candidate_dir / fname
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, exp_hash, f"Hash mismatch for {fname}")

    def test_03_exact_production_counts_and_topology_bijection(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        elem_counts = {'U1': 0, 'U2': 0, 'U3': 0, 'U4': 0, 'CPE4': 0, 'CPE3': 0}
        current_type = None
        in_sol_ic = False
        current_eid = None
        sol_ic_card_counts = {}

        for line in lines:
            l_strip = line.strip()
            if not l_strip:
                continue
            if l_strip.startswith('*'):
                l_upper = l_strip.upper()
                if l_upper.startswith('*ELEMENT'):
                    in_sol_ic = False
                    current_eid = None
                    parts = l_upper.split(',')
                    current_type = None
                    for p in parts:
                        if 'TYPE=' in p:
                            current_type = p.split('=')[1].strip()
                            break
                elif l_upper.startswith('*INITIAL CONDITIONS') and 'TYPE=SOLUTION' in l_upper:
                    in_sol_ic = True
                    current_type = None
                    current_eid = None
                elif l_upper.startswith('*'):
                    in_sol_ic = False
                    current_type = None
                    current_eid = None
            else:
                if current_type is not None:
                    if current_type in elem_counts:
                        elem_counts[current_type] += 1
                elif in_sol_ic:
                    parts = [p.strip() for p in l_strip.split(',') if p.strip()]
                    if len(parts) == 8 and '.' not in parts[0] and 'E+' not in parts[0] and 'E-' not in parts[0]:
                        try:
                            current_eid = int(parts[0])
                            sol_ic_card_counts[current_eid] = len(parts) - 1
                        except ValueError:
                            current_eid = None
                    elif current_eid is not None:
                        sol_ic_card_counts[current_eid] += len(parts)

        self.assertEqual(elem_counts['U1'], 4766, "Quad U1 count must be 4766")
        self.assertEqual(elem_counts['U2'], 4766, "Quad U2 count must be 4766")
        self.assertEqual(elem_counts['U3'], 128, "Tri U3 count must be 128")
        self.assertEqual(elem_counts['U4'], 128, "Tri U4 count must be 128")
        self.assertEqual(elem_counts['CPE4'], 4766, "CPE4 quad count must be 4766")
        self.assertEqual(elem_counts['CPE3'], 128, "CPE3 tri count must be 128")

        total_uel = elem_counts['U1'] + elem_counts['U2'] + elem_counts['U3'] + elem_counts['U4']
        total_phys = elem_counts['CPE4'] + elem_counts['CPE3']

        self.assertEqual(total_phys, 4894, "Physical element count must be 4894")
        self.assertEqual(total_uel, 9788, "Total UEL count must be 9788")
        self.assertEqual(len(sol_ic_card_counts), 9788, "All 9788 UELs must be initialized in TYPE=SOLUTION")

        for eid, cnt in sol_ic_card_counts.items():
            self.assertEqual(cnt, 18, f"Element {eid} must have exactly 18 initialized SDVs")

    def test_04_source_state_identity_verified(self):
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["source_job_id"], "1386469.mmaster02")
        self.assertEqual(artifact["source_job"], "M2ADAPT_MM_FRACFIX_PROD")
        self.assertAlmostEqual(artifact["source_u1_mm"], 0.005000)
        self.assertAlmostEqual(artifact["source_dmax"], 0.124500)
        self.assertEqual(artifact["target_physical_elements"], 4894)

    def test_05_target_topology_identity(self):
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["target_job"], "M2STATE_FRACFIX_RESTART1R1R2")
        self.assertEqual(artifact["target_nodes"], 4998)
        self.assertEqual(artifact["target_physical_elements"], 4894)

    def test_06_phase_mapping_complete_and_bounds(self):
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.assertTrue(artifact["phase_mapping_complete"])
        self.assertEqual(artifact["phase_bound_violations"], 0)
        self.assertGreaterEqual(artifact["phase_min"], 0.0)
        self.assertLessEqual(artifact["phase_max"], 1.0)

    def test_07_history_mapping_complete_and_paired(self):
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.assertTrue(artifact["history_mapping_complete"])
        self.assertEqual(artifact["paired_target_H_contract"], "PASS")

    def test_08_step1_target_phase_initialization_exact(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("Step-1-PhaseInit", inp_text)
        self.assertIn("*BOUNDARY", inp_text)
        self.assertIn("3, 3,", inp_text)

    def test_09_step2_phase_dof3_released(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("Step-2-Continuation", inp_text)
        self.assertIn("*BOUNDARY, OP=NEW", inp_text)

    def test_10_18_sdv_type_solution_cards(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_text)

    def test_11_historical_invalid_runtime_path_not_reused(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertNotIn("M2STATE_FRACFIX_RESTART1.odb", inp_text)

    def test_12_re_equilibration_acceptance_contracts_defined(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        self.assertTrue(contract["re_equilibration_acceptance_contract_defined"])
        self.assertTrue(contract["force_continuity_acceptance_defined"])
        self.assertTrue(contract["energy_continuity_acceptance_defined"])

    def test_13_nphys_property_slot5_contract(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*UEL PROPERTY, ELSET=E_U2", inp_text)
        self.assertIn("4894", inp_text)

    def test_14_dof_abi_quads_and_tris(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*USER ELEMENT, TYPE=U1, NODES=4", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U2, NODES=4", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U3, NODES=3", inp_text)
        self.assertIn("*USER ELEMENT, TYPE=U4, NODES=3", inp_text)

    def test_15_production_trace_representative_set_defined(self):
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("JELEM.EQ.2292", uel_code)
        self.assertIn("JELEM.EQ.7186", uel_code)
        self.assertIn("JELEM.EQ.100", uel_code)
        self.assertIn("JELEM.EQ.4994", uel_code)
        self.assertIn("JELEM.EQ.1500", uel_code)
        self.assertIn("JELEM.EQ.6394", uel_code)
        self.assertIn("JELEM.EQ.4862", uel_code)
        self.assertIn("JELEM.EQ.9756", uel_code)

    def test_16_production_trace_phase_coverage(self):
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("[INGEST_TRACE]", uel_code)
        self.assertIn("JTYPE=", uel_code)

    def test_17_production_trace_mechanical_coverage(self):
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("JELEM.EQ.7186", uel_code)
        self.assertIn("JELEM.EQ.4994", uel_code)
        self.assertIn("JELEM.EQ.6394", uel_code)
        self.assertIn("JELEM.EQ.9756", uel_code)

    def test_18_production_runtime_checker_contract(self):
        checker_text = self.checker_path.read_text(encoding="utf-8")
        self.assertIn("2292", checker_text)
        self.assertIn("7186", checker_text)
        self.assertIn("100", checker_text)
        self.assertIn("4994", checker_text)
        self.assertIn("1500", checker_text)
        self.assertIn("6394", checker_text)
        self.assertIn("4862", checker_text)
        self.assertIn("9756", checker_text)

    def test_19_restart_mechanical_loading_state_contract(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("Step-1-PhaseInit", inp_text)
        self.assertIn("99999, 1, 1, 0.005000", inp_text)
        self.assertIn("Step-2-Continuation", inp_text)
        self.assertIn("*BOUNDARY, OP=NEW", inp_text)
        self.assertIn("99999, 1, 1, 0.010000", inp_text)

    def test_20_mechanical_state_restart_strategy_justified(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["execution_mode"], "SERIAL")

    def test_21_exact_acceptance_thresholds_frozen(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        metrics = contract["metrics"]
        self.assertEqual(metrics["reaction_force_continuity"]["reference_quantity_kN"], 1.624785)
        self.assertEqual(metrics["post_equilibration_energy_jump"]["reference_quantity_kN_mm"], 0.00384962)
        self.assertEqual(metrics["reaction_force_continuity"]["threshold_pct"], 2.0)
        self.assertEqual(metrics["post_equilibration_energy_jump"]["threshold_pct"], 1.0)
        self.assertEqual(metrics["phase_decrease_healing_count"]["threshold"], 0)
        self.assertEqual(metrics["history_decrease_count"]["threshold"], 0)

    def test_22_resource_plan_contract(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb", pbs_text)
        self.assertIn("#PBS -l walltime=04:00:00", pbs_text)
        self.assertIn("#PBS -q entry_imfdfkmq", pbs_text)

    def test_23_negative_test_zeroed_phase_rejected(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        self.assertIn("mapped_startup_phase_continuity", contract["metrics"])

    def test_24_negative_test_historical_deck_reuse_rejected(self):
        t_manifest = json.loads(self.transfer_manifest_path.read_text(encoding="utf-8"))
        self.assertIn("builder_script_sha256", t_manifest)

    def test_25_negative_test_untraced_production_element_rejected(self):
        checker_text = self.checker_path.read_text(encoding="utf-8")
        self.assertIn("EXPECTED_REPRESENTATIVES", checker_text)

    def test_26_negative_test_wrong_source_frame_rejected(self):
        artifact = json.loads(self.artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["source_checkpoint"], "Step-1, frame 500")


if __name__ == "__main__":
    unittest.main()
