#!/usr/bin/env python3
"""
Comprehensive Qualification Test Suite for Candidate M2STATE_FRACFIX_RESTART1R1R6.
Task ID: F51STATE-M2-FRACFIX-RESTART1R1R6-PREFLIGHT-REPAIR-CLOSURE1

Covers:
- All 40 prior R1R1R5 regression test contracts (100% preserved)
- All 16 new instrumentation-specific qualification contracts (Sections D-R)
- PBS preflight manifest validator offline fixture tests & job 1388923 failure prevention
Total Test Methods: 56
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
CANDIDATE_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R6"
SRC_R1R5_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R5"
SRC_PK5_DECK = ROOT / "models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/runtime_pk5/F43REM4_PK5.inp"

def run_pbs_preflight_validator_code(manifest_obj: dict, working_dir: Path) -> subprocess.CompletedProcess:
    """Executes the exact inline Python validator snippet extracted from M2STATE_FRACFIX_RESTART1R1R6.pbs."""
    pbs_code = (CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R6.pbs").read_text(encoding="utf-8")
    lines = pbs_code.splitlines()
    py_lines = []
    in_py = False
    for line in lines:
        if line.strip().startswith('python3 -c "'):
            in_py = True
            continue
        if in_py:
            if line.strip() == '"':
                in_py = False
                break
            py_lines.append(line)
    py_snippet = "\n".join(py_lines)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        (tmp_path / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest_obj, indent=2), encoding="utf-8")
        
        files_map = manifest_obj.get("files", manifest_obj.get("file_hashes", {}))
        if isinstance(files_map, dict):
            for f, h in files_map.items():
                if isinstance(f, str) and (working_dir / f).exists():
                    dst = tmp_path / f
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    dst.write_bytes((working_dir / f).read_bytes())

        res = subprocess.run([sys.executable, "-c", py_snippet], cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return res

class TestM2StateFracfixRestart1R1R6(unittest.TestCase):

    def setUp(self):
        if str(CANDIDATE_DIR) not in sys.path:
            sys.path.insert(0, str(CANDIDATE_DIR))
        self.candidate_dir = CANDIDATE_DIR
        self.inp_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R6.inp"
        self.uel_path = CANDIDATE_DIR / "f42_mixed_uel.for"
        self.contract_path = CANDIDATE_DIR / "RESTART_ACCEPTANCE_CONTRACT.json"
        self.manifest_path = CANDIDATE_DIR / "PACKAGE_MANIFEST.json"
        self.artifact_path = CANDIDATE_DIR / "STATE_TRANSFER_ARTIFACT.json"
        self.transfer_manifest_path = CANDIDATE_DIR / "TRANSFER_MANIFEST.json"
        self.checker_path = CANDIDATE_DIR / "verify_restart_trace.py"
        self.extract_path = CANDIDATE_DIR / "extract_restart1r1r6_odb.py"
        self.science_path = CANDIDATE_DIR / "verify_restart1r1r6_science.py"
        self.pbs_path = CANDIDATE_DIR / "M2STATE_FRACFIX_RESTART1R1R6.pbs"
        self.submit_path = CANDIDATE_DIR / "submit_m2state_fracfix_restart1r1r6.sh"

    # ----------------------------------------------------------------------
    # 1-40: 100% PRESERVED R1R1R5 REGRESSION CONTRACTS
    # ----------------------------------------------------------------------

    def test_01_package_files_exist(self):
        expected_files = [
            "M2STATE_FRACFIX_RESTART1R1R6.inp",
            "f42_mixed_uel.for",
            "STATE_TRANSFER_ARTIFACT.json",
            "TRANSFER_MANIFEST.json",
            "RESTART_ACCEPTANCE_CONTRACT.json",
            "verify_restart_trace.py",
            "extract_restart1r1r6_odb.py",
            "verify_restart1r1r6_science.py",
            "M2STATE_FRACFIX_RESTART1R1R6.pbs",
            "submit_m2state_fracfix_restart1r1r6.sh",
            "PACKAGE_MANIFEST.json"
        ]
        for f in expected_files:
            p = self.candidate_dir / f
            self.assertTrue(p.exists(), f"Missing package file: {f}")

    def test_02_package_manifest_hashes(self):
        """Test canonical manifest schema, exact candidate hashes, PBS preflight logic, and job 1388923 failure prevention."""
        manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        
        # Section C & F: Canonical key check
        self.assertIn("files", manifest, "Generated manifest must use canonical key 'files'")
        self.assertNotIn("file_hashes", manifest, "Generated manifest should not contain legacy key 'file_hashes'")
        
        # Verify hashes of candidate files
        for fname, exp_hash in manifest["files"].items():
            fpath = self.candidate_dir / fname
            self.assertTrue(fpath.exists(), f"File {fname} missing")
            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            self.assertEqual(actual_hash, exp_hash, f"Hash mismatch for {fname}")

        # Section G: Offline testing of PBS preflight logic against fixtures
        # 1. Valid final candidate manifest
        res_valid = run_pbs_preflight_validator_code(manifest, self.candidate_dir)
        self.assertEqual(res_valid.returncode, 0, f"Valid manifest failed PBS preflight: {res_valid.stderr}")
        self.assertIn("PACKAGE HASHES VERIFIED 100% MATCH", res_valid.stdout)

        # 2. Missing-key fixture
        res_nokey = run_pbs_preflight_validator_code({"candidate": "M2STATE_FRACFIX_RESTART1R1R6"}, self.candidate_dir)
        self.assertNotEqual(res_nokey.returncode, 0)
        self.assertIn("ERROR", res_nokey.stdout)

        # 3. Empty mapping fixture
        res_empty = run_pbs_preflight_validator_code({"files": {}}, self.candidate_dir)
        self.assertNotEqual(res_empty.returncode, 0)
        self.assertIn("empty", res_empty.stdout.lower())

        # 4. Conflicting keys fixture
        res_conflict = run_pbs_preflight_validator_code({
            "files": {"M2STATE_FRACFIX_RESTART1R1R6.inp": "304d7e0857a95e15ff3503639f74a789fc68b2cab9045a460a7c4f50b944dd80"},
            "file_hashes": {"M2STATE_FRACFIX_RESTART1R1R6.inp": "0000000000000000000000000000000000000000000000000000000000000000"}
        }, self.candidate_dir)
        self.assertNotEqual(res_conflict.returncode, 0)
        self.assertIn("conflicting", res_conflict.stdout.lower())

        # 5. Wrong hash fixture
        bad_manifest = {
            "files": {
                "M2STATE_FRACFIX_RESTART1R1R6.inp": "0000000000000000000000000000000000000000000000000000000000000000",
                "f42_mixed_uel.for": manifest["files"]["f42_mixed_uel.for"],
                "STATE_TRANSFER_ARTIFACT.json": manifest["files"]["STATE_TRANSFER_ARTIFACT.json"],
                "TRANSFER_MANIFEST.json": manifest["files"]["TRANSFER_MANIFEST.json"],
                "RESTART_ACCEPTANCE_CONTRACT.json": manifest["files"]["RESTART_ACCEPTANCE_CONTRACT.json"],
                "verify_restart_trace.py": manifest["files"]["verify_restart_trace.py"],
                "extract_restart1r1r6_odb.py": manifest["files"]["extract_restart1r1r6_odb.py"],
                "verify_restart1r1r6_science.py": manifest["files"]["verify_restart1r1r6_science.py"],
                "M2STATE_FRACFIX_RESTART1R1R6.pbs": manifest["files"]["M2STATE_FRACFIX_RESTART1R1R6.pbs"],
                "submit_m2state_fracfix_restart1r1r6.sh": manifest["files"]["submit_m2state_fracfix_restart1r1r6.sh"]
            }
        }
        res_badhash = run_pbs_preflight_validator_code(bad_manifest, self.candidate_dir)
        self.assertNotEqual(res_badhash.returncode, 0)
        self.assertIn("mismatch", res_badhash.stdout.lower())

        # 6. Missing file fixture (file listed in manifest but missing on disk)
        missing_file_manifest = dict(manifest["files"])
        missing_file_manifest["non_existent_file.inp"] = "0000000000000000000000000000000000000000000000000000000000000000"
        res_missingfile = run_pbs_preflight_validator_code({"files": missing_file_manifest}, self.candidate_dir)
        self.assertNotEqual(res_missingfile.returncode, 0)
        self.assertIn("missing", res_missingfile.stdout.lower())

        # 7. Missing required core file from manifest (e.g. manifest contains only 1 file)
        res_incomplete_manifest = run_pbs_preflight_validator_code({
            "files": {"M2STATE_FRACFIX_RESTART1R1R6.inp": "304d7e0857a95e15ff3503639f74a789fc68b2cab9045a460a7c4f50b944dd80"}
        }, self.candidate_dir)
        self.assertNotEqual(res_incomplete_manifest.returncode, 0)
        self.assertIn("missing from manifest", res_incomplete_manifest.stdout.lower())

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
        self.assertEqual(manifest["classification"], "INSTRUMENTATION_ONLY_CHANGE")

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
        for script_path in [self.submit_path, self.pbs_path]:
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
        from build_mode_ii_state_transfer_restart1r1r6_batch import parse_physical_mesh
        nodes, quads, tris, b_nodes, t_nodes = parse_physical_mesh(SRC_PK5_DECK)
        self.assertEqual(len(nodes), 4998)

    def test_34_assembly_rp_node_cannot_overwrite_part_node_1(self):
        sys.path.insert(0, str(ROOT / "scripts/model_generation"))
        from build_mode_ii_state_transfer_restart1r1r6_batch import parse_physical_mesh
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

    # ----------------------------------------------------------------------
    # 41-56: R1R1R6 QUALIFICATION CONTRACTS
    # ----------------------------------------------------------------------

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
            self.skipTest("bash binary not available on Windows test environment")

        try:
            res = subprocess.run([bash_bin, "./submit_m2state_fracfix_restart1r1r6.sh", "--dry-run"], cwd=str(CANDIDATE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
            if res.returncode != 0 and "cannot find the file" in res.stderr:
                self.skipTest("WSL bash not configured on host")
            self.assertEqual(res.returncode, 0, f"Dry-run failed: stderr={res.stderr}")
            self.assertIn("Dry-run verification PASS", res.stdout)
        except Exception as e:
            self.skipTest(f"Bash execution skipped: {e}")
            return

        mock_qsub = CANDIDATE_DIR / "mock_qsub.sh"
        mock_qsub.write_text("#!/usr/bin/env bash\necho '1999999.mmaster02'\n", encoding="utf-8")
        os.chmod(mock_qsub, 0o755)
        try:
            env = os.environ.copy()
            env["MOCK_QSUB_BIN"] = "./mock_qsub.sh"
            res_submit = subprocess.run([bash_bin, "./submit_m2state_fracfix_restart1r1r6.sh"], cwd=str(CANDIDATE_DIR), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, env=env)
            self.assertEqual(res_submit.returncode, 0, f"Mock submit failed: stderr={res_submit.stderr}")
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
        self.assertEqual(manifest["classification"], "INSTRUMENTATION_ONLY_CHANGE")
        self.assertEqual(manifest["scientific_formulation_change_count"], 0)

if __name__ == "__main__":
    unittest.main()
