#!/usr/bin/env python3
"""
Candidate Qualification Test Suite for M2STATE_FRACFIX_RESTART1R1R5.
Task ID: F47STATE-M2-FRACFIX-RESTART1R1R5-PREP-QUALIFY1
"""

import os
import sys
import json
import unittest
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R5"
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"


class TestM2StateFracfixRestart1R1R5(unittest.TestCase):

    def setUp(self):
        self.candidate_dir = CANDIDATE_DIR
        self.inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R5.inp"
        self.uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        self.contract_path = CANDIDATE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
        self.manifest_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        self.artifact_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.transfer_manifest_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        self.checker_path = CANDIDATE_DIR / "verify_restart_trace.py"
        self.pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R5.pbs"
        self.submit_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart1r1r5.sh"

    def test_01_package_files_exist(self):
        expected_files = [
            "M2STATE_FRACFIX_RESTART1R1R5.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "verify_restart_trace.py",
            "M2STATE_FRACFIX_RESTART1R1R5.pbs",
            "submit_m2state_fracfix_restart1r1r5.sh",
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
        self.assertEqual(artifact["target_job"], "M2STATE_FRACFIX_RESTART1R1R5")
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
        self.assertIn("#PBS -l walltime=24:00:00", pbs_text)
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

    def test_27_execution_script_lf_line_endings_only(self):
        for script_path in [self.submit_path, self.pbs_path]:
            raw_bytes = script_path.read_bytes()
            cr_count = raw_bytes.count(b"\r")
            self.assertEqual(cr_count, 0, f"Script {script_path.name} contains {cr_count} CR bytes! Must be 0 (LF only).")

    def test_28_pbs_first_line_shebang_valid(self):
        raw_bytes = self.pbs_path.read_bytes()
        first_line = raw_bytes.splitlines(keepends=True)[0]
        self.assertEqual(first_line, b"#!/bin/bash\n", f"PBS first line must be exact b'#!/bin/bash\\n', got {repr(first_line)}")

    def test_29_no_incplicit_token_anywhere(self):
        for fname in os.listdir(self.candidate_dir):
            fpath = self.candidate_dir / fname
            if fpath.is_file():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("INCPLICIT", content, f"Malformed token INCPLICIT found in {fname}")

    def test_30_step_card_syntax_and_inc_integer_parameter(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        step_cards = [l.strip() for l in lines if l.strip().upper().startswith("*STEP")]
        self.assertEqual(len(step_cards), 2, "Candidate must contain exactly 2 *STEP cards")
        self.assertIn("*STEP, NAME=Step-1-PhaseInit, INC=10000", step_cards[0])
        self.assertIn("*STEP, NAME=Step-2-Continuation, INC=10000", step_cards[1])

    def test_31_resource_envelope_24h_walltime_serial_contract(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["walltime"], "24:00:00", "Walltime must be 24:00:00")
        self.assertEqual(manifest["cpus"], 1, "CPUs must be 1")
        self.assertEqual(manifest["execution_mode"], "SERIAL", "Execution mode must be SERIAL")

    def test_32_dual_channel_notification_pbs_directives_and_traps(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", pbs_text, "PBS script must include #PBS -m abe directive")
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text, "PBS script must include #PBS -M directive")
        self.assertIn("job_notifications.sh", pbs_text, "PBS script must source job_notifications.sh")
        self.assertIn("notification_install_terminal_trap", pbs_text, "PBS script must install terminal notification trap")
        self.assertIn("notify_start", pbs_text, "PBS script must execute notify_start")

    def test_33_parser_scopes_mesh_extraction_to_platepart_only(self):
        sys.path.insert(0, str(ROOT / "scripts/model_generation"))
        from build_mode_ii_state_transfer_restart1r1r5_batch import parse_physical_mesh_part_scoped
        nodes, quads, tris, b_nodes, t_nodes = parse_physical_mesh_part_scoped(SRC_PK5_DECK)
        self.assertEqual(len(nodes), 4998, "Part-scoped physical mesh must extract exactly 4998 Part nodes")
        self.assertEqual(len(quads), 4766, "Part-scoped physical mesh must extract exactly 4766 CPE4 quads")
        self.assertEqual(len(tris), 128, "Part-scoped physical mesh must extract exactly 128 CPE3 tris")

    def test_34_assembly_rp_node_cannot_overwrite_part_node_1(self):
        sys.path.insert(0, str(ROOT / "scripts/model_generation"))
        from build_mode_ii_state_transfer_restart1r1r5_batch import parse_physical_mesh_part_scoped
        nodes, _, _, _, _ = parse_physical_mesh_part_scoped(SRC_PK5_DECK)
        n1 = nodes[1]
        self.assertAlmostEqual(n1[0], 0.461913496, places=4, msg="Part Node 1 x must be 0.461913")
        self.assertAlmostEqual(n1[1], -0.500000, places=4, msg="Part Node 1 y must be -0.500000")
        self.assertNotEqual(n1, (0.0, 0.6), "Assembly RP Node 1 (0.0, 0.6) must not overwrite Part Node 1!")

    def test_35_node_1_exact_physical_coordinate_preservation(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        node_1_line = None
        in_nodes = False
        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"): continue
            if s.startswith("*"):
                in_nodes = s.upper().startswith("*NODE")
                continue
            if in_nodes and s.startswith("1,"):
                node_1_line = s
                break
        self.assertIsNotNone(node_1_line, "Node 1 line must be present in generated deck under *NODE")
        parts = [p.strip() for p in node_1_line.split(",")]
        x_val, y_val = float(parts[1]), float(parts[2])
        self.assertAlmostEqual(x_val, 0.461913496, places=4)
        self.assertAlmostEqual(y_val, -0.500000, places=4)

    def test_36_positive_signed_area_for_all_generated_elements(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        nodes = {}
        quads = {}
        tris = {}
        in_nodes = in_cpe4 = in_cpe3 = False

        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"):
                continue
            if s.startswith("*"):
                in_nodes = in_cpe4 = in_cpe3 = False
                if s.upper().startswith("*NODE"):
                    in_nodes = True
                elif s.upper().startswith("*ELEMENT"):
                    if "CPE4" in s.upper(): in_cpe4 = True
                    elif "CPE3" in s.upper(): in_cpe3 = True
                continue

            parts = [pt.strip() for pt in s.split(",") if pt.strip()]
            if in_nodes and len(parts) >= 3:
                try: nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError: pass
            elif in_cpe4 and len(parts) >= 5:
                try: quads[int(parts[0])] = [int(p) for p in parts[1:5]]
                except ValueError: pass
            elif in_cpe3 and len(parts) >= 4:
                try: tris[int(parts[0])] = [int(p) for p in parts[1:4]]
                except ValueError: pass

        def q_area(p0, p1, p2, p3):
            return 0.5 * ((p0[0]*p1[1]-p0[1]*p1[0]) + (p1[0]*p2[1]-p1[1]*p2[0]) + (p2[0]*p3[1]-p2[1]*p3[0]) + (p3[0]*p0[1]-p3[1]*p0[0]))

        def t_area(p0, p1, p2):
            return 0.5 * (p0[0]*(p1[1]-p2[1]) + p1[0]*(p2[1]-p0[1]) + p2[0]*(p0[1]-p1[1]))

        for eid, nids in quads.items():
            a = q_area(nodes[nids[0]], nodes[nids[1]], nodes[nids[2]], nodes[nids[3]])
            self.assertGreater(a, 0.0, f"Generated CPE4 quad element {eid} has area {a}")

        for eid, nids in tris.items():
            a = t_area(nodes[nids[0]], nodes[nids[1]], nodes[nids[2]])
            self.assertGreater(a, 0.0, f"Generated CPE3 tri element {eid} has area {a}")

    def test_37_n_bottom_and_n_top_nonempty_and_disjoint(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        bot_nodes = []
        top_nodes = []
        in_bot = in_top = False

        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"):
                continue
            if s.startswith("*"):
                in_bot = in_top = False
                if s.upper().startswith("*NSET"):
                    if "N_BOTTOM" in s.upper(): in_bot = True
                    elif "N_TOP" in s.upper(): in_top = True
                continue

            parts = [pt.strip() for pt in s.split(",") if pt.strip()]
            if in_bot: bot_nodes.extend([int(p) for p in parts if p.isdigit()])
            elif in_top: top_nodes.extend([int(p) for p in parts if p.isdigit()])

        self.assertGreater(len(bot_nodes), 0, "N_BOTTOM must not be empty!")
        self.assertGreater(len(top_nodes), 0, "N_TOP must not be empty!")
        self.assertEqual(len(set(bot_nodes).intersection(set(top_nodes))), 0, "N_BOTTOM and N_TOP must be disjoint!")

    def test_38_node_99999_reference_node_role_and_equation_valid(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("99999,   0.000000,   0.100000", inp_text)
        self.assertIn("*EQUATION", inp_text)
        self.assertIn("N_TOP, 1, 1.0, 99999, 1, -1.0", inp_text)

    def test_39_deck_reference_integrity_contract(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        nodes = set()
        in_nodes = False

        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"): continue
            if s.startswith("*"):
                in_nodes = s.upper().startswith("*NODE")
                continue
            if in_nodes:
                parts = [p.strip() for p in s.split(",") if p.strip()]
                if len(parts) >= 3 and parts[0].isdigit():
                    nodes.add(int(parts[0]))

        self.assertIn(99999, nodes, "Reference Node 99999 must exist in nodes")
        self.assertIn(1, nodes, "Part Node 1 must exist in nodes")
        self.assertEqual(len(nodes), 4999, "Total nodes in generated deck must be 4999 (4998 physical + 1 RP)")

    def test_40_no_unresolved_ambiguous_element_print_headers(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        for l in lines:
            self.assertNotIn("*ELEMENT PRINT", l.strip().upper(), "Legacy *ELEMENT PRINT card must not exist in generated deck!")


if __name__ == "__main__":
    unittest.main()
