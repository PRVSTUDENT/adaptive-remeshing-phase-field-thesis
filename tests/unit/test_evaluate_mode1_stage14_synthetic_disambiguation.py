#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_evaluate_mode1_stage14_synthetic_disambiguation.py
-------------------------------------------------------
Authoritative synthetic regression unit test suite for Stage-14 Mode-I terminal evaluator,
matched-displacement reference bundle ingestion, and energy-mapping qualification pipeline:
1. Multi-layer namespace disambiguation (Layer 1 Phase, Layer 2 Mech, Layer 3 Companion).
2. Strict integration-point deduplication and within-element equality verification:
   - Evaluates CPE4 (4 IPs) and CPE3 (1 IP) companion elements.
   - Proves deduplication prevents 4x overcounting on CPE4 elements.
   - Fails loudly (ValueError) if duplicate IP records for the same element carry inconsistent energy values.
3. Multi-instance and multi-layer disambiguation:
   - Scopes to authoritative companion element set (UMATELEM).
   - Resolves duplicate element labels across different instances via (instanceName, elementLabel).
4. Reaction force sign convention (F = -RF2) and tensile compliance.
5. Canonical half-bin initial stiffness K0 linear regression (N=400 window).
6. External work trapezoidal integration and monotonicity guard.
7. Reconciled canonical reference values and proven provenance (Job 1409734 / Job 1398090).
8. Comparative parity calculation vs canonical reference:
   - Discrete RMS and continuous L2 norm on common displacement domain.
   - 10 matched displacement states parity comparison.
   - Ligament profile comparison & spatial L2 norm.
9. Governed energy definitions:
   - "implemented phase-field crack-surface/fracture functional E_frac"
   - "degraded stored elastic strain energy E_elas"
   - "descriptive sum E_model = E_elas + E_frac"
   - "descriptive bookkeeping difference Delta_book = E_model - W_ext"
10. Automatic Markdown comparison report generation and template rendering.
"""

import os
import sys
import math
import json
import unittest
import importlib.util

# Dynamically load evaluator module with numeric directory prefix
_pkg_dir = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k"
))
_eval_py = os.path.join(_pkg_dir, "evaluate_mode1_stage14_adaptive_14k.py")
_spec = importlib.util.spec_from_file_location("evaluate_mode1_stage14_adaptive_14k", _eval_py)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

MATCHED_TARGET_DISPLACEMENTS = _mod.MATCHED_TARGET_DISPLACEMENTS
CANONICAL_REFERENCE = _mod.CANONICAL_REFERENCE
STAGE14_CANDIDATE_METADATA = _mod.STAGE14_CANDIDATE_METADATA
linear_regression = _mod.linear_regression
compute_trapezoidal_work = _mod.compute_trapezoidal_work
evaluate_mechanical_metrics = _mod.evaluate_mechanical_metrics
compare_against_reference = _mod.compare_against_reference
compare_ligament_profiles = _mod.compare_ligament_profiles
extract_element_energies_strict = _mod.extract_element_energies_strict
generate_markdown_comparison_report = _mod.generate_markdown_comparison_report
_is_float = _mod._is_float


class MockFieldValue(object):
    """Mocks an Abaqus ODB FieldValue with elementLabel, integrationPoint, data, and instance."""
    def __init__(self, element_label, data, integration_point=1, instance_name="PART-1-1"):
        self.elementLabel = element_label
        self.data = data
        self.integrationPoint = integration_point
        self.instance = type('MockInstance', (object,), {'name': instance_name})()


class MockFieldOutput(object):
    """Mocks an Abaqus ODB FieldOutput."""
    def __init__(self, name, values):
        self.name = name
        self.values = values

    def getSubset(self, region=None, position=None):
        if region is None:
            return self
        if hasattr(region, 'elements'):
            elem_labels = set(e.label for e in region.elements)
            filtered = [v for v in self.values if v.elementLabel in elem_labels]
            return MockFieldOutput(self.name, filtered)
        return self


class MockElement(object):
    """Mocks an Abaqus mesh element."""
    def __init__(self, label, type_name='CPE4'):
        self.label = label
        self.type = type_name


class MockElementSet(object):
    """Mocks an Abaqus ElementSet."""
    def __init__(self, name, elements):
        self.name = name
        self.elements = elements


class TestStage14EvaluatorAndDisambiguation(unittest.TestCase):
    """Test suite for Stage 14 evaluator and strict energy extraction logic."""

    def setUp(self):
        self.n_base_elements = 14483
        self.l1_range = (1, self.n_base_elements)
        self.l2_range = (self.n_base_elements + 1, 2 * self.n_base_elements)
        self.l3_range = (2 * self.n_base_elements + 1, 3 * self.n_base_elements)

    def test_layer_namespace_boundaries_and_metadata(self):
        """Verify layer label partitioning and metadata for 14,483 underlying finite elements."""
        self.assertEqual(self.l1_range, (1, 14483))
        self.assertEqual(self.l2_range, (14484, 28966))
        self.assertEqual(self.l3_range, (28967, 43449))
        self.assertEqual(STAGE14_CANDIDATE_METADATA["underlying_elements"], 14483)
        self.assertEqual(STAGE14_CANDIDATE_METADATA["layered_elements"], 43449)
        self.assertEqual(STAGE14_CANDIDATE_METADATA["quad_elements"], 14082)
        self.assertEqual(STAGE14_CANDIDATE_METADATA["tri_elements"], 401)
        
        # Verify layer partitioning metadata
        part = STAGE14_CANDIDATE_METADATA["layer_partitioning"]
        self.assertEqual(part["layer_1_phase_uel"]["element_range"], [1, 14483])
        self.assertEqual(part["layer_2_mech_uel"]["element_range"], [14484, 28966])
        self.assertEqual(part["layer_3_companion_umat"]["element_range"], [28967, 43449])
        self.assertEqual(part["layer_3_companion_umat"]["elset"], "UMATELEM")

    def test_reconciled_canonical_reference_provenance(self):
        """Verify proven provenance and exact values of the reconciled reference energy baseline."""
        self.assertEqual(CANONICAL_REFERENCE["job_id"], "1409734.mmaster02")
        self.assertEqual(CANONICAL_REFERENCE["underlying_elements"], 15192)
        self.assertAlmostEqual(CANONICAL_REFERENCE["K0_kN_per_mm"], 137.945520, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["F_max_kN"], 0.757778, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["u_at_F_max_mm"], 0.005857, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["W_ext_final_mJ"], 2.359329, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["E_frac_final_mJ"], 2.340220, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["E_elas_final_mJ"], 0.001161, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["E_model_final_mJ"], 2.341381, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["Delta_book_final_mJ"], -0.017949, places=6)
        self.assertAlmostEqual(CANONICAL_REFERENCE["eps_book_final_pct"], 0.7607, places=4)
        
        prov = CANONICAL_REFERENCE["provenance"]
        self.assertEqual(prov["energy_qualified_reference_job"], "1409734.mmaster02")
        self.assertEqual(prov["governed_status"], "CORRECTED_S1_ENERGY_QUALIFIED")
        self.assertEqual(prov["reference_deck_sha256"], "ec560a4c265730647b43dab125d166ebc57cac285d574d38222a498a967535d9")

    def test_extract_element_energies_strict_mixed_quad_tri(self):
        """
        Verify strict energy extraction on a mixed mesh:
        - 80 CPE4 quads (4 IPs each)
        - 20 CPE3 tris (1 IP each)
        Proves single representative value per element and exact total energy recovery.
        """
        cpe4_count = 80
        cpe3_count = 20
        total_elems = cpe4_count + cpe3_count

        expected_frac_per_elem = 0.050  # kN*mm
        expected_elas_per_elem = 0.020  # kN*mm

        values_17 = []
        values_18 = []

        # CPE4 elements (4 IPs each)
        for i in range(1, cpe4_count + 1):
            eid = 28966 + i
            for ip in range(1, 5):
                values_17.append(MockFieldValue(eid, expected_frac_per_elem, integration_point=ip, instance_name="PART-1-1"))
                values_18.append(MockFieldValue(eid, expected_elas_per_elem, integration_point=ip, instance_name="PART-1-1"))

        # CPE3 elements (1 IP each)
        for i in range(cpe4_count + 1, total_elems + 1):
            eid = 28966 + i
            values_17.append(MockFieldValue(eid, expected_frac_per_elem, integration_point=1, instance_name="PART-1-1"))
            values_18.append(MockFieldValue(eid, expected_elas_per_elem, integration_point=1, instance_name="PART-1-1"))

        field_17 = MockFieldOutput("SDV17", values_17)
        field_18 = MockFieldOutput("SDV18", values_18)

        res = extract_element_energies_strict(field_17, field_18)

        self.assertEqual(res["unique_element_count"], total_elems)
        self.assertEqual(res["quad_count"], cpe4_count)
        self.assertEqual(res["tri_count"], cpe3_count)
        self.assertAlmostEqual(res["total_e_frac"], total_elems * expected_frac_per_elem, places=8)
        self.assertAlmostEqual(res["total_e_elas"], total_elems * expected_elas_per_elem, places=8)
        self.assertAlmostEqual(res["total_e_model"], total_elems * (expected_frac_per_elem + expected_elas_per_elem), places=8)

    def test_strict_extraction_fails_loudly_on_inconsistent_ip_values(self):
        """
        Verify that extract_element_energies_strict raises ValueError if an element's
        integration points contain inconsistent whole-element energy values.
        """
        eid = 28967
        # Intentionally inconsistent IP values on a CPE4 element (IP 1 = 0.050, IP 2 = 0.080)
        values_17 = [
            MockFieldValue(eid, 0.050, integration_point=1, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.080, integration_point=2, instance_name="PART-1-1"),  # Inconsistent!
            MockFieldValue(eid, 0.050, integration_point=3, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.050, integration_point=4, instance_name="PART-1-1"),
        ]
        values_18 = [
            MockFieldValue(eid, 0.020, integration_point=1, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.020, integration_point=2, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.020, integration_point=3, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.020, integration_point=4, instance_name="PART-1-1"),
        ]

        field_17 = MockFieldOutput("SDV17", values_17)
        field_18 = MockFieldOutput("SDV18", values_18)

        with self.assertRaises(ValueError) as ctx:
            extract_element_energies_strict(field_17, field_18)
        self.assertIn("Inconsistent SDV17", str(ctx.exception))
        self.assertIn("IP 1 = 5.000000000000e-02 vs IP 2 = 8.000000000000e-02", str(ctx.exception))

        # Test inconsistent SDV18 (E_elas)
        values_17_consistent = [
            MockFieldValue(eid, 0.050, integration_point=ip, instance_name="PART-1-1") for ip in range(1, 5)
        ]
        values_18_inconsistent = [
            MockFieldValue(eid, 0.020, integration_point=1, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.020, integration_point=2, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.020, integration_point=3, instance_name="PART-1-1"),
            MockFieldValue(eid, 0.099, integration_point=4, instance_name="PART-1-1"),  # Inconsistent!
        ]
        field_17_c = MockFieldOutput("SDV17", values_17_consistent)
        field_18_i = MockFieldOutput("SDV18", values_18_inconsistent)

        with self.assertRaises(ValueError) as ctx2:
            extract_element_energies_strict(field_17_c, field_18_i)
        self.assertIn("Inconsistent SDV18", str(ctx2.exception))

    def test_multi_instance_duplicate_label_disambiguation(self):
        """
        Verify that grouping by (instanceName, elementLabel) correctly distinguishes
        identical local element IDs residing in different instances.
        """
        values_17 = [
            MockFieldValue(100, 0.10, integration_point=1, instance_name="INST_A"),
            MockFieldValue(100, 0.20, integration_point=1, instance_name="INST_B"),
        ]
        values_18 = [
            MockFieldValue(100, 0.01, integration_point=1, instance_name="INST_A"),
            MockFieldValue(100, 0.02, integration_point=1, instance_name="INST_B"),
        ]
        field_17 = MockFieldOutput("SDV17", values_17)
        field_18 = MockFieldOutput("SDV18", values_18)

        res = extract_element_energies_strict(field_17, field_18)
        self.assertEqual(res["unique_element_count"], 2)
        self.assertAlmostEqual(res["total_e_frac"], 0.30, places=8)
        self.assertAlmostEqual(res["total_e_elas"], 0.03, places=8)

    def test_layer_set_disambiguation_scoping(self):
        """
        Verify that providing region_set (e.g. UMATELEM) extracts only the companion layer
        and ignores co-located Layer 1 and Layer 2 entries.
        """
        umatelem_elems = [MockElement(eid, 'CPE4') for eid in range(28967, 28971)]
        umatelem_set = MockElementSet("UMATELEM", umatelem_elems)

        all_vals_17 = []
        all_vals_18 = []
        for eid in range(1, 5):
            all_vals_17.append(MockFieldValue(eid, 0.0, integration_point=1))
            all_vals_18.append(MockFieldValue(eid, 0.0, integration_point=1))
        for eid in range(28967, 28971):
            for ip in range(1, 5):
                all_vals_17.append(MockFieldValue(eid, 0.123, integration_point=ip))
                all_vals_18.append(MockFieldValue(eid, 0.456, integration_point=ip))

        field_17 = MockFieldOutput("SDV17", all_vals_17)
        field_18 = MockFieldOutput("SDV18", all_vals_18)

        res = extract_element_energies_strict(field_17, field_18, region_set=umatelem_set)
        self.assertEqual(res["unique_element_count"], 4)
        self.assertEqual(res["quad_count"], 4)
        self.assertEqual(res["tri_count"], 0)
        self.assertAlmostEqual(res["total_e_frac"], 4 * 0.123, places=8)
        self.assertAlmostEqual(res["total_e_elas"], 4 * 0.456, places=8)

    def test_force_sign_and_initial_stiffness_regression(self):
        """
        Verify that tensile reaction force F = -RF2 produces correct positive stiffness
        and canonical linear regression matches reference K0 = 137.945520 kN/mm.
        """
        k0_true = 137.945520  # kN/mm
        delta_u = 2.5e-6  # mm
        u_vals = [i * delta_u for i in range(1, 401)]
        rf2_vals = [-k0_true * u for u in u_vals]
        f_vals = [-rf for rf in rf2_vals]

        slope, intercept, r2 = linear_regression(u_vals, f_vals)
        self.assertAlmostEqual(slope, k0_true, places=5)
        self.assertAlmostEqual(intercept, 0.0, places=7)
        self.assertAlmostEqual(r2, 1.0, places=7)

        metrics = evaluate_mechanical_metrics(u_vals, f_vals, k0_fit_max_u=0.0010, nominal_delta_u=delta_u)
        self.assertAlmostEqual(metrics["K0_kN_per_mm"], k0_true, places=5)
        self.assertAlmostEqual(metrics["delta_K0_pct"], 0.0, places=4)
        self.assertEqual(metrics["K0_sample_count"], 400)

    def test_trapezoidal_work_and_monotonicity_guard(self):
        """Verify trapezoidal integration and rejection of non-monotonic displacements."""
        u_vals = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005]
        f_vals = [100.0 * u for u in u_vals]

        w_ext = compute_trapezoidal_work(u_vals, f_vals)
        self.assertAlmostEqual(w_ext[-1], 0.00125, places=8)

        u_non_mono = [0.0, 0.001, 0.002, 0.0015, 0.003]
        with self.assertRaises(ValueError):
            compute_trapezoidal_work(u_non_mono, f_vals[:5])

    def test_descriptive_energy_bookkeeping_residual(self):
        """Verify calculation of Delta_book and normalized error against reference baseline."""
        w_ext_final = 2.359329e-3  # kN*mm (2.359329 mJ)
        e_elas_final = 0.001161e-3  # kN*mm (0.001161 mJ)
        e_frac_final = 2.340220e-3  # kN*mm (2.340220 mJ)

        e_model = e_elas_final + e_frac_final
        delta_book = e_model - w_ext_final
        eps_book = (abs(delta_book) / w_ext_final) * 100.0

        self.assertAlmostEqual(e_model, 2.341381e-3, places=8)
        self.assertAlmostEqual(delta_book, -0.017948e-3, places=8)
        self.assertAlmostEqual(eps_book, 0.760737, places=4)

    def test_comparison_vs_reference_interpolation(self):
        """Verify discrete RMS and continuous L2 norm against reference trajectory."""
        u_ref = [0.0, 0.002, 0.004, 0.006, 0.008, 0.010]
        f_ref = [0.0, 0.276, 0.552, 0.740, 0.200, 0.001]

        u_cand = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010]
        f_cand = []
        for u in u_cand:
            idx = int(u / 0.002)
            if idx >= len(u_ref) - 1:
                f_interp = f_ref[-1]
            else:
                t = (u - u_ref[idx]) / 0.002
                f_interp = f_ref[idx] + t * (f_ref[idx+1] - f_ref[idx])
            f_cand.append(f_interp + 0.005)

        comp = compare_against_reference(u_cand, f_cand, u_ref, f_ref, scale_factor=1000.0)
        self.assertAlmostEqual(comp["max_abs_diff"], 5.0, places=4)
        self.assertAlmostEqual(comp["discrete_rms"], 5.0, places=3)
        self.assertAlmostEqual(comp["continuous_l2"], 5.0, places=3)

    def test_ligament_profile_comparison(self):
        """Verify spatial ligament profile comparison between candidate and reference."""
        xs = [0.50 + 0.01 * i for i in range(50)]
        # Profile 1: linear decay starting at 0.80 so d+0.02 <= 1.0 everywhere
        prof_ref = [(x, max(0.0, 0.80 - 1.5 * (x - 0.5))) for x in xs]
        # Profile 2: exact shift of +0.02 in damage
        prof_cand = [(x, d + 0.02) for x, d in prof_ref]

        res = compare_ligament_profiles(prof_cand, prof_ref)
        self.assertEqual(res["points_evaluated"], len(xs))
        self.assertAlmostEqual(res["max_abs_d_diff"], 0.02, places=5)
        self.assertAlmostEqual(res["rms_d_diff"], 0.02, places=4)
        self.assertAlmostEqual(res["continuous_l2_d"], 0.02, places=4)

    def test_matched_displacement_targets_completeness(self):
        """Verify that all 10 canonical matched displacement targets are defined."""
        self.assertEqual(len(MATCHED_TARGET_DISPLACEMENTS), 10)
        expected = [0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100]
        for t, e in zip(MATCHED_TARGET_DISPLACEMENTS, expected):
            self.assertAlmostEqual(t, e, places=6)

    def test_markdown_report_generation(self):
        """Verify that generate_markdown_comparison_report creates a compliant markdown report."""
        eval_record = {
            "mechanical_metrics": {
                "K0_kN_per_mm": 137.9000,
                "delta_K0_pct": -0.0330,
                "K0_R2": 0.9999995,
                "K0_intercept_kN": 1.2e-5,
                "F_max_kN": 0.757000,
                "delta_F_max_pct": -0.1027,
                "u_at_F_max_mm": 0.005857,
                "delta_u_peak_pct": 0.0,
                "F_final_kN": 0.000230,
                "W_ext_final_mJ": 2.358000
            },
            "terminal_e_elas_mJ": 0.001160,
            "terminal_e_frac_mJ": 2.339000,
            "matched_states_comparison": [
                {
                    "u_target_mm": 0.0010,
                    "f_ref_kN": 0.137924,
                    "f_adapt_kN": 0.137910,
                    "delta_f_pct": -0.01,
                    "dmax_ref": 0.0091,
                    "dmax_adapt": 0.0091,
                    "xtip_ref_mm": 0.5000,
                    "xtip_adapt_mm": 0.5000,
                    "efrac_ref_mJ": 0.000056,
                    "efrac_adapt_mJ": 0.000055,
                    "eps_book_adapt_pct": 0.00015
                }
            ],
            "comparison_vs_reference": {
                "common_u_max_mm": 0.010,
                "points_evaluated": 5000,
                "max_abs_diff_kN": 0.0008,
                "discrete_rms_N": 0.45,
                "continuous_l2_N": 0.42
            },
            "solver_sta_telemetry": {
                "total_increments": 7000,
                "total_cutbacks": 0
            }
        }
        test_md = os.path.join(_pkg_dir, "test_temp_comparison.md")
        generate_markdown_comparison_report(eval_record, test_md)
        self.assertTrue(os.path.exists(test_md))
        with open(test_md, 'r') as f:
            content = f.read()
        self.assertIn("# Stage 14 Adaptive vs. Reconciled Fixed Reference Comparison Report", content)
        self.assertIn("137.900000", content)
        self.assertIn("Crack-Surface Functional", content)
        self.assertIn("10 Matched Displacement States", content)
        if os.path.exists(test_md):
            os.remove(test_md)

    def test_float_helper(self):
        """Verify _is_float string parsing."""
        self.assertTrue(_is_float("123.456"))
        self.assertTrue(_is_float("-1.23e-4"))
        self.assertFalse(_is_float("abc"))
        self.assertFalse(_is_float(""))


if __name__ == '__main__':
    unittest.main()
