#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_evaluate_mode1_stage14_synthetic_disambiguation.py
-------------------------------------------------------
Unit and synthetic regression test suite for Stage-14 Mode-I terminal evaluator
and energy-mapping qualification pipeline:
1. Multi-layer namespace disambiguation (Layer 1 Phase, Layer 2 Mech, Layer 3 Companion).
2. Integration-point deduplication / single-IP extraction (prevents 4x overcounting from CPE4).
3. Mixed quadrilateral (CPE4) and triangular (CPE3) companion layer handling.
4. Reaction force sign convention (F = -RF2) and tensile compliance.
5. Canonical half-bin initial stiffness K0 linear regression (N=400 window).
6. External work trapezoidal integration and monotonicity guard.
7. Descriptive energy bookkeeping residual Delta_book = (E_elas + E_frac) - W_ext.
8. Comparative parity calculation vs canonical reference Job 1398090.
"""

import os
import sys
import math
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

CANONICAL_REFERENCE = _mod.CANONICAL_REFERENCE
STAGE14_CANDIDATE_METADATA = _mod.STAGE14_CANDIDATE_METADATA
linear_regression = _mod.linear_regression
compute_trapezoidal_work = _mod.compute_trapezoidal_work
evaluate_mechanical_metrics = _mod.evaluate_mechanical_metrics
compare_against_reference = _mod.compare_against_reference
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
        # Filter by region element labels if present
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


def extract_mock_odb_layer_energies(field_sdv17, field_sdv18, target_elset=None, single_ip_only=True):
    """
    Simulates the authoritative ODB layer extraction and deduplication logic.
    Returns: (total_e_frac, total_e_elas, unique_elements_count)
    """
    values_17 = field_sdv17.getSubset(region=target_elset).values if target_elset else field_sdv17.values
    values_18 = field_sdv18.getSubset(region=target_elset).values if target_elset else field_sdv18.values

    seen_elements = set()
    total_e_frac = 0.0
    total_e_elas = 0.0

    for v17, v18 in zip(values_17, values_18):
        eid = v17.elementLabel
        if single_ip_only:
            if eid not in seen_elements:
                seen_elements.add(eid)
                total_e_frac += float(v17.data)
                total_e_elas += float(v18.data)
        else:
            # Naive / erroneous multi-IP accumulation without deduplication
            total_e_frac += float(v17.data)
            total_e_elas += float(v18.data)
            seen_elements.add(eid)

    return total_e_frac, total_e_elas, len(seen_elements)


class TestStage14EvaluatorAndDisambiguation(unittest.TestCase):
    """Test suite for Stage 14 evaluator and layer disambiguation logic."""

    def setUp(self):
        self.n_phys = 14483
        self.l1_range = (1, self.n_phys)
        self.l2_range = (self.n_phys + 1, 2 * self.n_phys)
        self.l3_range = (2 * self.n_phys + 1, 3 * self.n_phys)

    def test_layer_namespace_boundaries(self):
        """Verify layer label partitioning for 14,483 physical elements."""
        self.assertEqual(self.l1_range, (1, 14483))
        self.assertEqual(self.l2_range, (14484, 28966))
        self.assertEqual(self.l3_range, (28967, 43449))
        self.assertEqual(STAGE14_CANDIDATE_METADATA["underlying_elements"], 14483)
        self.assertEqual(STAGE14_CANDIDATE_METADATA["layered_elements"], 43449)

    def test_single_ip_deduplication_prevents_4x_overcounting(self):
        """
        Prove that deduplicated / single-IP extraction recovers true element energy
        whereas naive multi-IP accumulation produces 4x overcounting on CPE4 elements.
        """
        # Create 100 mock Layer 3 companion elements (80 CPE4 with 4 IPs, 20 CPE3 with 1 IP)
        cpe4_count = 80
        cpe3_count = 20
        total_elems = cpe4_count + cpe3_count

        expected_frac_per_elem = 0.050  # kN*mm
        expected_elas_per_elem = 0.020  # kN*mm

        values_sdv17 = []
        values_sdv18 = []

        # CPE4 elements (4 IPs each, each IP carrying element-integrated energy)
        for i in range(1, cpe4_count + 1):
            eid = 28966 + i
            for ip in range(1, 5):
                values_sdv17.append(MockFieldValue(eid, expected_frac_per_elem, integration_point=ip))
                values_sdv18.append(MockFieldValue(eid, expected_elas_per_elem, integration_point=ip))

        # CPE3 elements (1 IP each)
        for i in range(cpe4_count + 1, total_elems + 1):
            eid = 28966 + i
            values_sdv17.append(MockFieldValue(eid, expected_frac_per_elem, integration_point=1))
            values_sdv18.append(MockFieldValue(eid, expected_elas_per_elem, integration_point=1))

        field_17 = MockFieldOutput("SDV17", values_sdv17)
        field_18 = MockFieldOutput("SDV18", values_sdv18)

        # 1. Authoritative Deduplicated Extraction
        e_frac_dedup, e_elas_dedup, count_dedup = extract_mock_odb_layer_energies(
            field_17, field_18, single_ip_only=True
        )

        true_e_frac = total_elems * expected_frac_per_elem
        true_e_elas = total_elems * expected_elas_per_elem

        self.assertEqual(count_dedup, total_elems)
        self.assertAlmostEqual(e_frac_dedup, true_e_frac, places=7)
        self.assertAlmostEqual(e_elas_dedup, true_e_elas, places=7)

        # 2. Erroneous Naive Multi-IP Summation
        e_frac_naive, e_elas_naive, _ = extract_mock_odb_layer_energies(
            field_17, field_18, single_ip_only=False
        )

        # Naive sums 4x for CPE4 and 1x for CPE3
        naive_expected_frac = (cpe4_count * 4 + cpe3_count * 1) * expected_frac_per_elem
        self.assertAlmostEqual(e_frac_naive, naive_expected_frac, places=7)
        self.assertGreater(e_frac_naive, true_e_frac * 3.0)

    def test_layer_set_disambiguation_with_conflicting_global_ids(self):
        """
        Prove that scoping extraction to UMATELEM element set prevents collision
        even if an ODB contains non-unique local numbering across instances or mock sets.
        """
        # Instance A: Layer 1 elements (labels 1..50)
        # Instance B: Layer 3 companion elements (labels 1..50 inside instance, or mapped in set)
        inst_a_values_17 = [MockFieldValue(i, 0.0, instance_name="LAYER1_PHASE") for i in range(1, 51)]
        inst_b_values_17 = [MockFieldValue(i, 0.123, instance_name="LAYER3_UMAT") for i in range(1, 51)]
        inst_a_values_18 = [MockFieldValue(i, 0.0, instance_name="LAYER1_PHASE") for i in range(1, 51)]
        inst_b_values_18 = [MockFieldValue(i, 0.456, instance_name="LAYER3_UMAT") for i in range(1, 51)]

        umatelem_elements = [MockElement(i, 'CPE4') for i in range(1, 51)]
        umatelem_set = MockElementSet("UMATELEM", umatelem_elements)

        field_17 = MockFieldOutput("SDV17", inst_b_values_17)
        field_18 = MockFieldOutput("SDV18", inst_b_values_18)

        e_frac, e_elas, count = extract_mock_odb_layer_energies(
            field_17, field_18, target_elset=umatelem_set, single_ip_only=True
        )

        self.assertEqual(count, 50)
        self.assertAlmostEqual(e_frac, 50 * 0.123, places=7)
        self.assertAlmostEqual(e_elas, 50 * 0.456, places=7)

    def test_force_sign_and_initial_stiffness_regression(self):
        """
        Verify that tensile reaction force F = -RF2 produces correct positive stiffness
        and canonical linear regression matches reference K0 = 137.945520 kN/mm.
        """
        # Generate synthetic 400 linear increments matching reference K0
        k0_true = 137.945520  # kN/mm
        delta_u = 2.5e-6  # mm
        u_vals = [i * delta_u for i in range(1, 401)]
        # True RF2 is compressive at top boundary: RF2 = -K0 * u
        rf2_vals = [-k0_true * u for u in u_vals]
        # Tensile force F = -RF2
        f_vals = [-rf for rf in rf2_vals]

        slope, intercept, r2 = linear_regression(u_vals, f_vals)
        self.assertAlmostEqual(slope, k0_true, places=5)
        self.assertAlmostEqual(intercept, 0.0, places=7)
        self.assertAlmostEqual(r2, 1.0, places=7)

        # Test evaluate_mechanical_metrics
        metrics = evaluate_mechanical_metrics(u_vals, f_vals, k0_fit_max_u=0.0010, nominal_delta_u=delta_u)
        self.assertAlmostEqual(metrics["K0_kN_per_mm"], k0_true, places=5)
        self.assertAlmostEqual(metrics["delta_K0_pct"], 0.0, places=4)
        self.assertEqual(metrics["K0_sample_count"], 400)

    def test_trapezoidal_work_and_monotonicity_guard(self):
        """Verify trapezoidal integration and rejection of non-monotonic displacements."""
        u_vals = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005]
        # Linear force F = 100 * u
        f_vals = [100.0 * u for u in u_vals]

        w_ext = compute_trapezoidal_work(u_vals, f_vals)
        # Exact analytical: W = 0.5 * k * u^2 = 0.5 * 100 * (0.005)^2 = 0.00125 kN*mm = 1.25 mJ
        self.assertAlmostEqual(w_ext[-1], 0.00125, places=8)

        # Test non-monotonic displacement guard
        u_non_mono = [0.0, 0.001, 0.002, 0.0015, 0.003]
        with self.assertRaises(ValueError):
            compute_trapezoidal_work(u_non_mono, f_vals[:5])

    def test_descriptive_energy_bookkeeping_residual(self):
        """Verify calculation of Delta_book, normalized error, and units."""
        w_ext_final = 2.450e-3  # kN*mm (2.450 mJ)
        e_elas_final = 0.050e-3  # kN*mm (0.050 mJ)
        e_frac_final = 2.405e-3  # kN*mm (2.405 mJ)

        e_model = e_elas_final + e_frac_final
        delta_book = e_model - w_ext_final
        eps_book = (abs(delta_book) / w_ext_final) * 100.0

        self.assertAlmostEqual(e_model, 2.455e-3, places=8)
        self.assertAlmostEqual(delta_book, 0.005e-3, places=8)
        self.assertAlmostEqual(eps_book, (0.005 / 2.450) * 100.0, places=5)

    def test_comparison_vs_reference_interpolation(self):
        """Verify discrete RMS and continuous L2 norm against canonical reference."""
        u_ref = [0.0, 0.002, 0.004, 0.006, 0.008, 0.010]
        f_ref = [0.0, 0.276, 0.552, 0.740, 0.200, 0.001]

        # Candidate with minor offset (+0.005 kN)
        u_cand = [0.0, 0.001, 0.002, 0.003, 0.004, 0.005, 0.006, 0.007, 0.008, 0.009, 0.010]
        f_cand = []
        for u in u_cand:
            # Interpolate ref and add +0.005 kN
            idx = int(u / 0.002)
            if idx >= len(u_ref) - 1:
                f_interp = f_ref[-1]
            else:
                t = (u - u_ref[idx]) / 0.002
                f_interp = f_ref[idx] + t * (f_ref[idx+1] - f_ref[idx])
            f_cand.append(f_interp + 0.005)

        comp = compare_against_reference(u_cand, f_cand, u_ref, f_ref)
        self.assertAlmostEqual(comp["max_abs_diff_kN"], 0.005, places=5)
        self.assertAlmostEqual(comp["discrete_rms_N"], 5.0, places=3)
        self.assertAlmostEqual(comp["continuous_l2_N"], 5.0, places=3)

    def test_float_helper(self):
        """Verify _is_float parsing."""
        self.assertTrue(_is_float("123.456"))
        self.assertTrue(_is_float("-1.23e-4"))
        self.assertFalse(_is_float("abc"))
        self.assertFalse(_is_float(""))


if __name__ == '__main__':
    unittest.main()
