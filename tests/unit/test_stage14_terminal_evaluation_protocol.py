#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14_terminal_evaluation_protocol.py
--------------------------------------------
Unit tests for Stage-14 frozen evaluation protocol, publication fidelity boundary,
and evaluator reference self-parity:
1. Verifies existence and schema of STAGE14_TERMINAL_EVALUATION_PROTOCOL.json and .md.
2. Verifies 3-category epistemological separation in STAGE14_PUBLICATION_FIDELITY_BOUNDARY.md.
3. Verifies exact K0 linear regression contract (N=400, delta_u=2.5e-6 mm).
4. Verifies reference self-parity (continuous L2 = 0.0, discrete RMS = 0.0).
5. Verifies STA telemetry parsing (cutbacks, iterations, increments).
6. Verifies 10 matched-displacement states structure and energy values.
"""

import os
import sys
import json
import unittest
import importlib.util

# Add model package dir to sys.path
_pkg_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k"
))
_eval_py = os.path.join(_pkg_dir, "evaluate_mode1_stage14_adaptive_14k.py")
_spec = importlib.util.spec_from_file_location("evaluate_mode1_stage14_adaptive_14k", _eval_py)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

MATCHED_TARGET_DISPLACEMENTS = _mod.MATCHED_TARGET_DISPLACEMENTS
CANONICAL_REFERENCE = _mod.CANONICAL_REFERENCE
evaluate_mechanical_metrics = _mod.evaluate_mechanical_metrics
compare_against_reference = _mod.compare_against_reference
parse_sta_file = _mod.parse_sta_file

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestStage14TerminalProtocol(unittest.TestCase):
    """Test suite for Stage 14 terminal evaluation protocol and boundary documents."""

    def setUp(self):
        self.protocol_json_path = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_TERMINAL_EVALUATION_PROTOCOL.json"
        )
        self.protocol_md_path = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_TERMINAL_EVALUATION_PROTOCOL.md"
        )
        self.boundary_md_path = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "STAGE14_PUBLICATION_FIDELITY_BOUNDARY.md"
        )
        self.ref_bundle_path = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k", "MODE1_REFERENCE_MATCHED_DISPLACEMENT_BUNDLE.json"
        )
        self.ref_sta_path = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k", "PK_M1_REF15K_ENERGY.sta"
        )

    def test_protocol_files_exist(self):
        """Verify that all Stage 14 protocol and boundary documents exist in the workspace."""
        self.assertTrue(os.path.exists(self.protocol_json_path))
        self.assertTrue(os.path.exists(self.protocol_md_path))
        self.assertTrue(os.path.exists(self.boundary_md_path))
        self.assertTrue(os.path.exists(self.ref_bundle_path))
        self.assertTrue(os.path.exists(self.ref_sta_path))

    def test_protocol_json_schema_and_constants(self):
        """Validate JSON schema, matched states, verdict hierarchy, and reference constants."""
        with open(self.protocol_json_path, 'r', encoding='utf-8') as f:
            proto = json.load(f)
            
        self.assertEqual(proto["protocol_id"], "GATE6B-STAGE14-TERMINAL-EVALUATION-PROTOCOL-20261003")
        self.assertEqual(len(proto["ten_matched_displacement_states_mm"]), 10)
        self.assertEqual(proto["ten_matched_displacement_states_mm"], MATCHED_TARGET_DISPLACEMENTS)
        self.assertEqual(len(proto["overall_verdict_hierarchy"]), 4)
        
        expected_verdicts = [
            "STAGE14_ADAPTIVE_MECHANICS_AND_FIELD_RESPONSE_STABLE",
            "STAGE14_ADAPTIVE_MECHANICS_STABLE_FIELD_SENSITIVE",
            "STAGE14_ADAPTIVE_RESPONSE_MESH_SENSITIVE",
            "STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED"
        ]
        self.assertEqual(proto["overall_verdict_hierarchy"], expected_verdicts)
        
        ref = proto["reference_benchmark"]
        self.assertAlmostEqual(ref["K0_kN_per_mm"], 137.945520, places=5)
        self.assertAlmostEqual(ref["Fmax_kN"], 0.757778, places=5)
        self.assertAlmostEqual(ref["u_peak_mm"], 0.005857, places=5)
        self.assertAlmostEqual(ref["W_ext_mJ"], 2.359329, places=5)
        self.assertAlmostEqual(ref["E_frac_mJ"], 2.340220, places=5)
        self.assertAlmostEqual(ref["E_elas_mJ"], 0.001161, places=5)
        self.assertAlmostEqual(ref["Delta_book_mJ"], -0.017949, places=5)
        self.assertAlmostEqual(ref["eps_book_pct"], 0.760749, places=4)
        
        anti_bias = proto["anti_bias_rules"]
        self.assertTrue(anti_bias["zero_frame_picking"])
        self.assertTrue(anti_bias["no_cosmetic_verdict_selection"])
        self.assertTrue(anti_bias["multi_quantity_synthesis_required"])
        self.assertTrue(anti_bias["cutbacks_recorded_as_telemetry_not_automatic_failure"])

    def test_publication_boundary_three_categories_and_2906_reclassification(self):
        """Verify 3-category structure and 2,906-element Category 2 reclassification."""
        with open(self.boundary_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("Category 1", content)
        self.assertIn("Published Facts", content)
        self.assertIn("Category 2", content)
        self.assertIn("Project Numerical Evidence", content)
        self.assertIn("Category 3", content)
        self.assertIn("Unresolved Literature Details", content)
        self.assertIn("PUBLISHED_FIG6A_PREANALYSIS_STATE = UNRESOLVED_REFERENCE_DETAIL", content)
        self.assertIn("TWO_STEP_JOB1_STRUCTURE_REPRODUCED__ABSOLUTE_LOADING_SEMANTICS_UNRESOLVED", content)
        self.assertIn("STAGE14_PREANALYSIS_METHOD_FIDELITY_PARTIALLY_SUPPORTED", content)
        self.assertIn("PROJECT_TARGET_LIKE_ADAPTIVE_CANDIDATE", content)
        # Verify 2,906 elements is under Category 2
        self.assertIn("2,906", content)
        self.assertIn("0.02", content)

    def test_evaluator_reference_mechanical_recovery(self):
        """Verify that evaluate_mechanical_metrics perfectly recovers reference values."""
        u_vals = [i * 2.5e-6 for i in range(1, 401)]
        f_vals = [CANONICAL_REFERENCE["K0_kN_per_mm"] * u + CANONICAL_REFERENCE["K0_intercept_kN"] for u in u_vals]
        
        u_vals.extend([0.0020, 0.0040, CANONICAL_REFERENCE["u_at_F_max_mm"], 0.0070, 0.0100])
        f_vals.extend([0.276, 0.540, CANONICAL_REFERENCE["F_max_kN"], 0.00043, CANONICAL_REFERENCE["F_final_kN"]])
        
        mech = evaluate_mechanical_metrics(u_vals, f_vals, k0_fit_max_u=0.0010, nominal_delta_u=2.5e-6)
        
        self.assertAlmostEqual(mech["K0_kN_per_mm"], CANONICAL_REFERENCE["K0_kN_per_mm"], places=4)
        self.assertEqual(mech["K0_sample_count"], 400)
        self.assertAlmostEqual(mech["F_max_kN"], CANONICAL_REFERENCE["F_max_kN"], places=5)
        self.assertAlmostEqual(mech["u_at_F_max_mm"], CANONICAL_REFERENCE["u_at_F_max_mm"], places=5)

    def test_evaluator_curve_self_parity(self):
        """Verify that compare_against_reference produces exact zero norms for identical curves."""
        u_test = [0.001, 0.002, 0.003, 0.005, 0.005857, 0.008, 0.010]
        f_test = [0.138, 0.276, 0.408, 0.662, 0.758, 0.00034, 0.00023]
        
        comp = compare_against_reference(u_test, f_test, u_test, f_test)
        self.assertAlmostEqual(comp["continuous_l2"], 0.0, places=10)
        self.assertAlmostEqual(comp["discrete_rms"], 0.0, places=10)
        self.assertAlmostEqual(comp["max_abs_diff"], 0.0, places=10)

    def test_sta_telemetry_parsing(self):
        """Verify parse_sta_file correctly parses increments, iterations, and 0 cutbacks."""
        sta = parse_sta_file(self.ref_sta_path)
        self.assertIsNotNone(sta)
        self.assertGreater(sta["total_increments"], 5000)
        self.assertGreater(sta["total_iterations"], 10000)
        self.assertEqual(sta["total_cutbacks"], 0)

    def test_matched_bundle_structure(self):
        """Verify that the 10 matched states in reference bundle match target displacements."""
        with open(self.ref_bundle_path, 'r', encoding='utf-8') as f:
            bundle = json.load(f)
            
        states = bundle.get("matched_states", [])
        self.assertEqual(len(states), 10)
        for idx, st in enumerate(states):
            self.assertAlmostEqual(st["u_target_mm"], MATCHED_TARGET_DISPLACEMENTS[idx], places=6)
            self.assertIn("reaction_force_kN", st)
            self.assertIn("e_frac_mJ", st)
            self.assertIn("e_elas_mJ", st)
            self.assertIn("delta_book_mJ", st)
            self.assertIn("eps_book_pct", st)

if __name__ == "__main__":
    unittest.main()
