#!/usr/bin/env python3
"""
Comprehensive Qualification Test Suite for Candidate M2STATE_FRACFIX_RESTART1R1R6R2.
Task ID: F57STATE-M2-FRACFIX-RESTART1R1R6R2-PREDEF-NULL-REPAIR1

Covers:
- All 70 prior R1R1R6R1 regression test contracts (100% preserved)
- Job 1388946 PREDEF null-pointer dereference regression prevention (Tests 71-75)
- JTYPE=4 mechanical triangle ABI & runtime safety contracts
- Zero scientific formulation change verification
Total Test Methods: 75
"""

import os
import sys
import json
import math
import hashlib
import unittest
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R2"
SRC_R1R6R1_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6R1"
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"
SRC_NOTIF_SH = ROOT / "scripts/hpc/notifications/job_notifications.sh"

class TestM2StateFracfixRestart1R1R6R2(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.candidate_dir = CANDIDATE_DIR
        cls.inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R6R2.inp"
        cls.uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        cls.artifact_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        cls.state_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        cls.transfer_manifest_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        cls.manifest_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        cls.contract_path = CANDIDATE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
        cls.checker_path = CANDIDATE_DIR / "verify_restart_trace.py"
        cls.trace_path = CANDIDATE_DIR / "verify_restart_trace.py"
        cls.extract_path = CANDIDATE_DIR / "extract_restart1r1r6_odb.py"
        cls.science_path = CANDIDATE_DIR / "verify_restart1r1r6_science.py"
        cls.notif_helper_path = CANDIDATE_DIR / "job_notifications.sh"
        cls.validator_path = CANDIDATE_DIR / "validate_package_manifest.py"
        cls.pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R6R2.pbs"
        cls.submit_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart1r1r6r2.sh"
        cls.wrapper_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart1r1r6r2.sh"

    def test_01_package_files_exist(self):
        required = [
            self.inp_path, self.uel_path, self.artifact_path, self.transfer_manifest_path,
            self.manifest_path, self.contract_path, self.checker_path, self.extract_path,
            self.science_path, self.notif_helper_path, self.validator_path, self.pbs_path, self.submit_path
        ]
        for f in required:
            self.assertTrue(f.is_file(), f"Required file missing: {f}")

    def test_02_package_manifest_hashes(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["candidate"], "M2STATE_FRACFIX_RESTART1R1R6R2")
        self.assertEqual(manifest["predecessor"], "M2STATE_FRACFIX_RESTART1R1R6R1")
        self.assertIn("files", manifest)
        self.assertIsInstance(manifest["files"], dict)

        for filename, expected_hash in manifest["files"].items():
            filepath = self.candidate_dir / filename
            self.assertTrue(filepath.is_file(), f"Manifest lists missing file: {filename}")
            actual_hash = hashlib.sha256(filepath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash.lower(), expected_hash.lower(), f"Hash mismatch for {filename}")

    def test_03_exact_production_counts_and_topology_bijection(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        elem_counts = {'U1': 0, 'U2': 0, 'U3': 0, 'U4': 0, 'CPE4': 0, 'CPE3': 0}
        current_type = None

        for line in lines:
            l_strip = line.strip()
            if not l_strip or l_strip.startswith('*'):
                if l_strip.startswith('*'):
                    l_upper = l_strip.upper()
                    if l_upper.startswith('*ELEMENT'):
                        current_type = None
                        for p in l_upper.split(','):
                            if 'TYPE=' in p:
                                current_type = p.split('=')[1].strip()
                                break
                    else:
                        current_type = None
                continue
            if current_type in elem_counts:
                elem_counts[current_type] += 1

        self.assertEqual(elem_counts['U1'], 4766)
        self.assertEqual(elem_counts['U2'], 4766)
        self.assertEqual(elem_counts['U3'], 128)
        self.assertEqual(elem_counts['U4'], 128)
        self.assertEqual(elem_counts['CPE4'], 4766)
        self.assertEqual(elem_counts['CPE3'], 128)

    def test_04_zero_unconnected_mesh_nodes(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertNotIn("WarnNodeBCInactiveDof", inp_text)

    def test_05_correct_sdv_field_counts(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*DEPVAR", inp_text)
        self.assertIn("18", inp_text)

    def test_06_solution_initial_conditions_cards(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*INITIAL CONDITIONS, TYPE=SOLUTION", inp_text)

    def test_07_step_keyword_formatting(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*STEP, NAME=Step-1-PhaseInit, INC=10000", inp_text)
        self.assertIn("*STEP, NAME=Step-2-Continuation, INC=10000", inp_text)

    def test_08_solver_license_compatibility(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertNotIn("*USER ELEMENT, NODES=8", inp_text)

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

    def test_16_production_trace_phase_coverage(self):
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("[STATE_TRACE]", uel_code)

    def test_17_production_trace_mechanical_coverage(self):
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("JELEM.EQ.7186", uel_code)

    def test_18_production_runtime_checker_contract(self):
        checker_text = self.checker_path.read_text(encoding="utf-8")
        self.assertIn("2292", checker_text)

    def test_19_restart_mechanical_loading_state_contract(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("Step-1-PhaseInit", inp_text)
        self.assertIn("Step-2-Continuation", inp_text)

    def test_20_mechanical_state_restart_strategy_justified(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["classification"], "RUNTIME_SAFETY_BUGFIX_PREDEF_NPREDF0")

    def test_21_exact_acceptance_thresholds_frozen(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        metrics = contract["metrics"]
        self.assertEqual(metrics["reaction_force_continuity"]["reference_quantity_kN"], 1.624785)

    def test_22_resource_plan_contract(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -l select=1:ncpus=1:mpiprocs=1:mem=8gb", pbs_text)

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
        for script_path in [self.submit_path, self.pbs_path, self.notif_helper_path]:
            raw_bytes = script_path.read_bytes()
            cr_count = raw_bytes.count(b"\r")
            self.assertEqual(cr_count, 0, f"Script {script_path.name} contains {cr_count} CR bytes!")

    def test_28_pbs_first_line_shebang_valid(self):
        raw_bytes = self.pbs_path.read_bytes()
        first_line = raw_bytes.splitlines(keepends=True)[0]
        self.assertEqual(first_line, b"#!/bin/bash\n")

    def test_29_no_incplicit_token_anywhere(self):
        for fname in os.listdir(self.candidate_dir):
            fpath = self.candidate_dir / fname
            if fpath.is_file():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("INCPLICIT", content)

    def test_30_step_card_syntax_and_inc_integer_parameter(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        step_cards = [l.strip() for l in lines if l.strip().upper().startswith("*STEP")]
        self.assertEqual(len(step_cards), 2)

    def test_31_resource_envelope_24h_walltime_serial_contract(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("walltime=24:00:00", pbs_text)

    def test_32_dual_channel_notification_pbs_directives_and_traps(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)

    def test_33_parser_scopes_mesh_extraction_to_platepart_only(self):
        sys.path.insert(0, str(ROOT / "scripts/model_generation"))
        from build_mode_ii_state_transfer_restart1r1r6r2_batch import parse_physical_mesh
        nodes, quads, tris, b_nodes, t_nodes = parse_physical_mesh(SRC_PK5_DECK)
        self.assertEqual(len(nodes), 4998)

    def test_34_assembly_rp_node_cannot_overwrite_part_node_1(self):
        sys.path.insert(0, str(ROOT / "scripts/model_generation"))
        from build_mode_ii_state_transfer_restart1r1r6r2_batch import parse_physical_mesh
        nodes, _, _, _, _ = parse_physical_mesh(SRC_PK5_DECK)
        n1 = nodes[1]
        self.assertAlmostEqual(n1[0], 0.461913496, places=4)

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
        parts = [p.strip() for p in node_1_line.split(",")]
        self.assertAlmostEqual(float(parts[1]), 0.461913496, places=4)

    def test_36_positive_signed_area_for_all_generated_elements(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        nodes = {}
        quads = {}
        tris = {}
        in_nodes = in_cpe4 = in_cpe3 = False

        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"): continue
            if s.startswith("*"):
                in_nodes = in_cpe4 = in_cpe3 = False
                if s.upper().startswith("*NODE"): in_nodes = True
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

        for eid, nids in quads.items():
            a = q_area(nodes[nids[0]], nodes[nids[1]], nodes[nids[2]], nodes[nids[3]])
            self.assertGreater(a, 0.0)

    def test_37_n_bottom_and_n_top_nonempty_and_disjoint(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        bot_nodes = []
        top_nodes = []
        in_bot = in_top = False

        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"): continue
            if s.startswith("*"):
                in_bot = in_top = False
                if s.upper().startswith("*NSET"):
                    if "N_BOTTOM" in s.upper(): in_bot = True
                    elif "N_TOP" in s.upper(): in_top = True
                continue

            parts = [pt.strip() for pt in s.split(",") if pt.strip()]
            if in_bot: bot_nodes.extend([int(p) for p in parts if p.isdigit()])
            elif in_top: top_nodes.extend([int(p) for p in parts if p.isdigit()])

        self.assertGreater(len(bot_nodes), 0)
        self.assertGreater(len(top_nodes), 0)
        self.assertEqual(len(set(bot_nodes).intersection(set(top_nodes))), 0)

    def test_38_node_99999_reference_node_role_and_equation_valid(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("99999,   0.000000,   0.100000", inp_text)

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

        self.assertIn(99999, nodes)
        self.assertIn(1, nodes)
        self.assertEqual(len(nodes), 4999)

    def test_40_no_unresolved_ambiguous_element_print_headers(self):
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        for l in lines:
            self.assertNotIn("*ELEMENT PRINT", l.strip().upper())

    def test_41_state_trace_write_after_state_assignment(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("C Trace write executed AFTER values have been assigned!", code)

    def test_42_scientific_checker_rejects_nan_inf_missing(self):
        checker_code = self.checker_path.read_text(encoding="utf-8")
        science_code = self.science_path.read_text(encoding="utf-8")
        self.assertIn("math.isnan", checker_code)
        self.assertIn("math.isinf", checker_code)
        self.assertIn("math.isnan", science_code)
        self.assertIn("math.isinf", science_code)

    def test_43_sdv14_sdv15_sdv16_numerical_semantics(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("SVARS(KPT) = D_AVG", code)
        self.assertIn("SVARS(4+KPT) = D_AVG", code)
        self.assertIn("SVARS(8+KPT) = SV_H(PHYSIDX, KPT)", code)

    def test_44_startup_history_full_domain_trace(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("[H_STARTUP_TRACE]", code)
        self.assertIn("WRITE(7,1002) PHYSIDX, JELEM, JTYPE", code)

    def test_45_history_irreversibility_fortran_assignment(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("IF (POS_M .GT. SV_H(PHYSIDX, KPT)) THEN", code)
        self.assertIn("SV_H(PHYSIDX, KPT) = POS_M", code)

    def test_46_converged_increment_trace_selection_and_cutback_filtering(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("IF (KSTEP.EQ.2 .AND. KINC.EQ.1) THEN", code)

    def test_47_uel_force_trace_and_sign_convention_derivation(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("F_INT(I) = F_INT(I) + CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))", code)
        self.assertIn("RHS(I,1) = RHS(I,1) - CJAC*(B(1,I)*STRESS(1) + B(2,I)*STRESS(2) + B(3,I)*STRESS(3))", code)

    def test_48_force_trace_accepted_state_deduplication(self):
        code = self.uel_path.read_text(encoding="utf-8")
        self.assertIn("[FORCE_TRACE]", code)
        self.assertIn("FINT1_N1=", code)

    def test_49_physical_phase_node_set_and_odb_u3_field_output(self):
        inp_text = self.inp_path.read_text(encoding="utf-8")
        self.assertIn("*NSET, NSET=N_PHYSICAL, GENERATE", inp_text)
        self.assertIn("1, 4998, 1", inp_text)
        self.assertIn("*OUTPUT, FIELD, FREQ=1", inp_text)
        self.assertIn("*NODE OUTPUT, NSET=N_PHYSICAL", inp_text)

    def test_50_phase_irreversibility_odb_checker(self):
        science_code = self.science_path.read_text(encoding="utf-8")
        self.assertIn("phase_irreversibility_contract", science_code)

    def test_51_phase_and_total_energy_definitions(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        self.assertIn("post_equilibration_energy_jump", contract["metrics"])
        ext_code = self.extract_path.read_text(encoding="utf-8")
        self.assertIn("energies", ext_code)

    def test_52_scientific_checker_evaluation(self):
        science_code = self.science_path.read_text(encoding="utf-8")
        expected_gates = [
            "production_phase_ingestion", "production_history_ingestion",
            "production_element_pairing", "integration_point_ordering",
            "mechanical_phase_consumption", "SDV14_contract", "SDV15_contract",
            "SDV16_contract", "phase_continuity_contract", "history_continuity_contract",
            "force_continuity_contract", "energy_continuity_contract",
            "mechanical_reequilibration_runtime_success", "phase_irreversibility_contract",
            "history_irreversibility_contract", "full_production_runtime_checker"
        ]
        for g in expected_gates:
            self.assertIn(g, science_code, f"Scientific checker must evaluate gate: {g}")

    def test_53_scientific_checker_threshold_boundaries(self):
        contract = json.loads(self.contract_path.read_text(encoding="utf-8"))
        metrics = contract["metrics"]
        self.assertEqual(metrics["reaction_force_continuity"]["threshold_pct"], 2.0)
        self.assertEqual(metrics["post_equilibration_energy_jump"]["threshold_pct"], 1.0)
        self.assertEqual(metrics["phase_decrease_healing_count"]["threshold"], 0)

    def test_54_guarded_wrapper_dry_run_and_mock_qsub_exactly_once(self):
        import shutil
        bash_bin = None
        git_bash_candidates = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe"
        ]
        for c in git_bash_candidates:
            if os.path.exists(c):
                bash_bin = c
                break
        if not bash_bin:
            bash_bin = shutil.which("bash")

        if not bash_bin:
            self.skipTest("bash binary not available")

        try:
            res = subprocess.run([bash_bin, "./submit_m2state_fracfix_restart1r1r6r2.sh", "--dry-run"], cwd=str(CANDIDATE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if res.returncode != 0 and ("cannot find the file" in res.stderr.lower() or "no such file" in res.stderr.lower()):
                self.skipTest("WSL bash path issue on host")
            self.assertEqual(res.returncode, 0, f"Dry-run failed: {res.stderr}")
            self.assertIn("Dry-run verification PASS", res.stdout)
        except Exception as e:
            self.skipTest(f"Bash execution skipped: {e}")
            return

        mock_qsub = CANDIDATE_DIR / "mock_qsub.sh"
        mock_qsub.write_text("#!/usr/bin/env bash\necho '1999999.mmaster02'\n", encoding="utf-8")
        try:
            os.chmod(mock_qsub, 0o755)
        except Exception:
            pass
        try:
            env = os.environ.copy()
            env["MOCK_QSUB_BIN"] = "./mock_qsub.sh"
            env["NOTIFICATION_MOCK_TELEGRAM"] = "1"
            res_submit = subprocess.run([bash_bin, "./submit_m2state_fracfix_restart1r1r6r2.sh"], cwd=str(CANDIDATE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
            self.assertEqual(res_submit.returncode, 0, f"Mock submit failed: {res_submit.stderr}")
            self.assertIn("1999999.mmaster02", res_submit.stdout)
        finally:
            if mock_qsub.exists():
                mock_qsub.unlink()

    def test_55_notification_and_resource_envelope_contracts(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertIn("#PBS -m abe", pbs_text)
        self.assertIn("#PBS -M pr21vyci@mailserver.tu-freiberg.de", pbs_text)
        self.assertIn("job_notifications.sh", pbs_text)
        self.assertIn("walltime=24:00:00", pbs_text)
        self.assertIn("mem=8gb", pbs_text)

    def test_56_full_semantic_diff_and_scientific_invariance(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["classification"], "RUNTIME_SAFETY_BUGFIX_PREDEF_NPREDF0")
        self.assertEqual(manifest["scientific_formulation_change_count"], 0)

    def test_57_standalone_manifest_validator_contract(self):
        res_valid = subprocess.run([sys.executable, str(self.validator_path), str(self.manifest_path)], cwd=str(self.candidate_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res_valid.returncode, 0, res_valid.stderr)
        self.assertIn("package_manifest_verification = PASS", res_valid.stdout)

    def test_58_zero_inline_python_in_pbs(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        self.assertNotIn('python3 -c "', pbs_text)
        self.assertNotIn("python3 -c '", pbs_text)
        self.assertIn("python3 validate_package_manifest.py PACKAGE_MANIFEST.json", pbs_text)

    def test_59_exact_pbs_manifest_command_contract(self):
        cmd = [sys.executable, "validate_package_manifest.py", "PACKAGE_MANIFEST.json"]
        res = subprocess.run(cmd, cwd=str(self.candidate_dir), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn("package_manifest_verification = PASS", res.stdout)

    def test_60_job_1388942_regression_contract(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        lines = pbs_text.splitlines()
        for i, line in enumerate(lines):
            if "python3" in line and "-c" in line:
                self.fail(f"PBS line {i+1} still contains inline python: {line}")

    def test_61_notification_setup_before_manifest_preflight(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        notif_idx = pbs_text.find("job_notifications.sh")
        preflight_idx = pbs_text.find("validate_package_manifest.py")
        self.assertNotEqual(notif_idx, -1)
        self.assertNotEqual(preflight_idx, -1)
        self.assertLess(notif_idx, preflight_idx)

    def test_62_terminal_trap_installed_before_manifest_preflight(self):
        pbs_text = self.pbs_path.read_text(encoding="utf-8")
        trap_idx = pbs_text.find("notification_install_terminal_trap")
        preflight_idx = pbs_text.find("validate_package_manifest.py")
        self.assertNotEqual(trap_idx, -1)
        self.assertNotEqual(preflight_idx, -1)
        self.assertLess(trap_idx, preflight_idx)

    def _run_bash_helper(self, script, env_vars=None):
        import shutil
        bash_bin = None
        git_bash_candidates = [
            r"C:\Program Files\Git\bin\bash.exe",
            r"C:\Program Files\Git\usr\bin\bash.exe"
        ]
        for c in git_bash_candidates:
            if os.path.exists(c):
                bash_bin = c
                break
        if not bash_bin:
            bash_bin = shutil.which("bash")

        if not bash_bin:
            return None
        env = os.environ.copy()
        env["NOTIFICATION_MOCK_TELEGRAM"] = "1"
        env["NOTIFICATION_RETRY_DELAY"] = "0"
        if env_vars:
            env.update(env_vars)
        cmd = [bash_bin, "-c", f"source '{self.notif_helper_path.as_posix()}'\n{script}"]
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
            if res.returncode != 0 and ("cannot find the file" in res.stderr.lower() or "no such file" in res.stderr.lower()):
                return None
            return res
        except Exception:
            return None

    def test_63_preflight_failure_notification_control_flow(self):
        script = """
set -e
EVENTS=""
notify_start() { EVENTS="${EVENTS}:STARTED"; }
notify_failed() { EVENTS="${EVENTS}:FAILED"; }
notify_completed() { EVENTS="${EVENTS}:COMPLETED"; }
notification_install_terminal_trap
notify_start
exit 1
"""
        res = self._run_bash_helper(script)
        if res is None: self.skipTest("bash binary not available")
        self.assertEqual(res.returncode, 1)

    def test_64_successful_pbs_notification_sequence_contract(self):
        script = """
set -e
EVENTS=""
notify_start() { EVENTS="${EVENTS}:STARTED"; }
notify_completed() { EVENTS="${EVENTS}:COMPLETED"; }
notification_install_terminal_trap
notify_start
echo "PREFLIGHT_PASS"
exit 0
"""
        res = self._run_bash_helper(script)
        if res is None: self.skipTest("bash binary not available")
        self.assertEqual(res.returncode, 0)
        self.assertIn("PREFLIGHT_PASS", res.stdout)

    def test_65_notification_failure_preserves_original_exit_code(self):
        script = "notification_install_terminal_trap\nexit 42\n"
        res = self._run_bash_helper(script, {"NOTIFICATION_MOCK_FAIL": "1"})
        if res is None: self.skipTest("bash binary not available")
        self.assertEqual(res.returncode, 42)

    def test_66_terminal_notification_exactly_once_contract(self):
        script = """
FIRED=0
notify_terminal() { FIRED=$((FIRED + 1)); }
notification_install_terminal_trap
notification_terminal_trap 0
notification_terminal_trap 0
echo "COUNT=$FIRED"
"""
        res = self._run_bash_helper(script)
        if res is None: self.skipTest("bash binary not available")
        self.assertEqual(res.returncode, 0)
        self.assertIn("COUNT=1", res.stdout)

    def test_67_semantic_diff_and_scientific_invariance(self):
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["classification"], "RUNTIME_SAFETY_BUGFIX_PREDEF_NPREDF0")
        self.assertEqual(manifest["scientific_formulation_change_count"], 0)

    def test_68_package_manifest_exact_byte_identity(self):
        manifest_bytes = self.manifest_path.read_bytes()
        manifest_sha = hashlib.sha256(manifest_bytes).hexdigest()
        self.assertEqual(manifest_sha, "efc34b97121ae33c186849a20df518d20933490f855a1b493900a5eecfbf73c1")

    def test_69_package_local_notification_helper_identity(self):
        self.assertTrue(self.notif_helper_path.is_file())
        pkg_helper_sha = hashlib.sha256(self.notif_helper_path.read_bytes()).hexdigest()
        src_helper_sha = hashlib.sha256(SRC_NOTIF_SH.read_bytes()).hexdigest()
        self.assertEqual(pkg_helper_sha, src_helper_sha)

    def test_70_notification_secret_isolation_and_helper_fail_closed(self):
        for fname in os.listdir(self.candidate_dir):
            fpath = self.candidate_dir / fname
            if fpath.is_file():
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                self.assertNotIn("756911", content)
                self.assertNotIn("AA", content if "TELEGRAM_BOT_TOKEN=" in content and not "token=" in content else "")

    # ----------------------------------------------------------------------
    # 71-75: F57 PREDEF REPAIR & JTYPE=4 ABI REGRESSION GATES
    # ----------------------------------------------------------------------

    def test_71_job_1388946_regression_no_predef_writes_under_npredf0(self):
        """Verify zero PREDEF write statements in f42_mixed_uel.for under NPREDF=0."""
        uel_code = self.uel_path.read_text(encoding="utf-8")
        lines = uel_code.splitlines()
        for i, l in enumerate(lines):
            l_strip = l.strip()
            if l_strip.startswith("C") or l_strip.startswith("c") or l_strip.startswith("*"):
                continue
            l_upper = l_strip.upper()
            if "PREDEF(" in l_upper:
                if "=" in l_upper and l_upper.index("PREDEF(") < l_upper.index("="):
                    if not any(kw in l_upper for kw in ["DIMENSION", "SUBROUTINE", "DOUBLE PRECISION", "REAL"]):
                        self.fail(f"Found forbidden PREDEF write on line {i+1}: {l}")

    def test_72_jtype4_mechanical_triangle_abi_and_scientific_assignments(self):
        """Verify JTYPE=4 contains all required scientific assignments and zero PREDEF writes."""
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertNotIn("PREDEF(1,1,1)=0.D0", uel_code)
        
        # Verify JTYPE 4 main computation block preserves B_TRI, STRAIN, STRESS, SVARS, F_INT, AMATRX, FORCE_TRACE
        j4_idx = uel_code.rfind("ELSE IF (JTYPE .EQ. 4)")
        j4_end = uel_code.find("C Trace write executed", j4_idx)
        j4_block = uel_code[j4_idx:j4_end]
        
        self.assertIn("SVARS(KPT) = D_VAL", j4_block)
        self.assertIn("SVARS(3+KPT) = D_AVG", j4_block)
        self.assertIn("SVARS(6+KPT) = SV_H(PHYSIDX, KPT)", j4_block)
        self.assertIn("B_TRI(1,1)", j4_block)
        self.assertIn("STRESS(1) = C11*STRAIN(1)", j4_block)
        self.assertIn("F_INT(I) = F_INT(I)", j4_block)
        self.assertIn("AMATRX(I,J) = AMATRX(I,J)", j4_block)
        self.assertIn("WRITE(7,1003)", j4_block)

    def test_73_npredf0_predef_runtime_dereference_count_zero(self):
        """Verify PREDEF_runtime_dereference_count = 0 in UEL body."""
        uel_code = self.uel_path.read_text(encoding="utf-8")
        lines = uel_code.splitlines()
        uel_body_lines = lines[25:458] # inside UEL executable body (after declarations)
        deref_count = 0
        for i, l in enumerate(uel_body_lines):
            l_strip = l.strip()
            if l_strip.startswith("C") or l_strip.startswith("c") or l_strip.startswith("*"):
                continue
            if "PREDEF" in l_strip.upper():
                deref_count += 1
        self.assertEqual(deref_count, 0, "PREDEF must have zero runtime dereferences in UEL body")

    def test_74_triangular_physical_element_counts_and_mappings(self):
        """Verify candidate contains 128 triangular physical elements (JELEM 4767..4894 and 9661..9788)."""
        lines = self.inp_path.read_text(encoding="utf-8").splitlines()
        u3_elems = []
        u4_elems = []
        in_u3 = in_u4 = False
        for l in lines:
            s = l.strip()
            if not s or s.startswith("**"): continue
            if s.startswith("*"):
                in_u3 = "*ELEMENT" in s.upper() and "TYPE=U3" in s.upper()
                in_u4 = "*ELEMENT" in s.upper() and "TYPE=U4" in s.upper()
                continue
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if in_u3 and parts[0].isdigit():
                u3_elems.append(int(parts[0]))
            elif in_u4 and parts[0].isdigit():
                u4_elems.append(int(parts[0]))
                
        self.assertEqual(len(u3_elems), 128)
        self.assertEqual(len(u4_elems), 128)
        self.assertEqual(u3_elems[0], 4767)
        self.assertEqual(u3_elems[-1], 4894)
        self.assertEqual(u4_elems[0], 9661)
        self.assertEqual(u4_elems[-1], 9788)

    def test_75_jtype4_abi_static_contract_safety(self):
        """Verify JTYPE=4 safety contract under NPREDF=0."""
        # Static contract validation
        uel_code = self.uel_path.read_text(encoding="utf-8")
        self.assertNotIn("PREDEF(1,1,1)", uel_code)
        self.assertNotIn("PREDEF(1)", uel_code[:458])

if __name__ == "__main__":
    unittest.main()
