# -*- coding: utf-8 -*-
"""
Unit and Regression Test Suite for Mode-I Batch Candidate Evaluator & Multi-Family Comparison
Protocol Version: 2
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

Validates:
1. REFERENCE_EXTRACTION_RULES.json availability and semantic integrity.
2. Canonical K0 half-bin tolerance window rule ((u > 0.5*delta_u) & (u <= 0.0010 + 0.5*delta_u), N=400).
3. Strict force sign convention F = -RF2_RP (rejection of bare |RF2|).
4. Zero displacement extrapolation in trapezoidal work integration W_ext.
5. SDV17/SDV18 single-value unique-element deduplication (seen = set(), preventing 4x overcount).
6. Energy bookkeeping definitions: E_model = E_elas + E_frac, Delta_book = E_model - W_ext (descriptive diagnostic).
7. Family classification and scientific scoping (Spatial vs Temporal vs Length Scale vs Adaptive).
8. Multi-family aggregation and comparative analysis routines.
"""

import os
import sys
import math
import json
import pytest
import numpy as np

from scripts.evaluation.evaluate_mode1_batch_candidate import (
    CANONICAL_REFERENCE,
    CANDIDATE_CATALOG,
    load_rules_json,
    linear_regression,
    compute_trapezoidal_work,
    deduplicate_element_sdv_sum,
    evaluate_mechanical_response,
    compute_energy_bookkeeping,
    classify_candidate,
    evaluate_candidate_data
)

from scripts.evaluation.compare_mode1_convergence_families import (
    compute_relative_difference,
    compare_spatial_convergence_family,
    compare_temporal_convergence_family,
    compare_length_scale_sensitivity_family,
    compare_adaptive_vs_reference
)


def test_reference_rules_json_integrity():
    """Verifies that REFERENCE_EXTRACTION_RULES.json is loadable and schema-compliant."""
    rules = load_rules_json()
    assert rules is not None, "Failed to load REFERENCE_EXTRACTION_RULES.json"
    assert "initial_stiffness_K0" in rules
    assert "force_sign_convention" in rules
    assert "work_integration" in rules
    assert "sdv_energy_aggregation" in rules
    assert "energy_bookkeeping_interpretation" in rules
    assert "epistemic_classification_rules" in rules
    
    k0_rules = rules["initial_stiffness_K0"]
    assert k0_rules["u_target_max_mm"] == 0.0010
    assert k0_rules["canonical_point_count_N"] == 400
    assert abs(k0_rules["canonical_reference_values"]["K0_kN_per_mm"] - 137.945520) < 1e-4


def test_linear_regression_accuracy():
    """Tests ordinary least squares linear regression helper."""
    x = [0.0, 1.0, 2.0, 3.0, 4.0]
    y = [1.0, 3.0, 5.0, 7.0, 9.0] # y = 2x + 1
    slope, intercept, r2 = linear_regression(x, y)
    assert abs(slope - 2.0) < 1e-12
    assert abs(intercept - 1.0) < 1e-12
    assert abs(r2 - 1.0) < 1e-12


def test_canonical_k0_half_bin_window():
    """
    Tests canonical K0 window selection rule:
    With delta_u = 2.5e-6 mm over 0 to 0.0020 mm (800 incs),
    the window (0.5*delta_u, 0.0010 + 0.5*delta_u] must select exactly 400 points.
    """
    delta_u = 2.5e-6
    u_vals = [i * delta_u for i in range(801)]
    # Linear force response F = 137.945520 * u
    k_true = 137.945520
    rf_vals = [-(k_true * u) for u in u_vals]
    
    res = evaluate_mechanical_response(u_vals, rf_vals, k0_fit_max_u=0.0010)
    assert res["K0_fit_points"] == 400, "Expected 400 points for canonical window, got %d" % res["K0_fit_points"]
    assert abs(res["K0_kN_per_mm"] - k_true) < 1e-6
    assert abs(res["K0_R2"] - 1.0) < 1e-8
    assert abs(res["delta_K0_pct"]) < 1e-6


def test_force_sign_convention_strict():
    """
    Verifies tensile force sign convention F = -RF2_RP.
    Rejects positive raw RF2 (which would mean compression or reversed BC).
    """
    u_vals = [0.0, 0.001, 0.002]
    rf_tensile = [0.0, -0.1379, -0.2758] # Negative RF2 under tension
    res = evaluate_mechanical_response(u_vals, rf_tensile)
    assert res["F_vals_kN"][1] > 0.0, "Tensile force must be positive"
    assert res["F_max_kN"] > 0.0
    
    # If raw RF2 were mistakenly positive, F = -RF2 is negative (not masked by abs())
    rf_mistake = [0.0, 0.1379, 0.2758]
    res_mistake = evaluate_mechanical_response(u_vals, rf_mistake)
    assert res_mistake["F_vals_kN"][1] < 0.0, "Mistaken positive RF2 must NOT be silently masked by abs()"


def test_work_integration_monotonicity_and_zero_extrapolation():
    """Tests trapezoidal work integration with strict monotonicity and zero extrapolation."""
    u_vals = [0.0, 0.001, 0.002, 0.003]
    f_vals = [0.0, 1.0, 2.0, 3.0] # Linear force: W = 0.5 * F * u = 0.5 * 3 * 0.003 = 0.0045 kN*mm
    w_ext = compute_trapezoidal_work(u_vals, f_vals)
    assert len(w_ext) == 4
    assert abs(w_ext[-1] - 0.0045) < 1e-12
    
    # Non-monotonic displacement must raise ValueError
    u_nonmono = [0.0, 0.002, 0.001, 0.003]
    with pytest.raises(ValueError, match="Non-monotonic displacement"):
        compute_trapezoidal_work(u_nonmono, f_vals)


def test_sdv_single_value_deduplication():
    """
    Tests SDV17/18 single-value deduplication.
    Simulates 4 Gauss points per element for 100 elements (400 records total).
    The deduplication must yield exactly 100 elements and avoid 4x overcounting.
    """
    pairs = []
    for eid in range(1, 101):
        for gp in range(4): # 4 Gauss points per element
            pairs.append((eid, 0.010, 0.005)) # SDV17=0.010, SDV18=0.005
            
    assert len(pairs) == 400
    e_frac_sum, e_elas_sum, n_unique = deduplicate_element_sdv_sum(pairs)
    assert n_unique == 100
    assert abs(e_frac_sum - (100 * 0.010)) < 1e-12
    assert abs(e_elas_sum - (100 * 0.005)) < 1e-12


def test_energy_bookkeeping_metrics():
    """Tests global energy bookkeeping calculation and descriptive diagnostic classification."""
    e_elas = [0.0, 0.001, 0.002]
    e_frac = [0.0, 0.005, 0.010]
    w_ext = [0.0, 0.006, 0.0121] # Slight residual Delta_book = (0.002 + 0.010) - 0.0121 = -0.0001
    
    records = compute_energy_bookkeeping(e_elas, e_frac, w_ext)
    assert len(records) == 3
    rec2 = records[2]
    assert abs(rec2["e_model_kNmm"] - 0.0120) < 1e-12
    assert abs(rec2["delta_book_kNmm"] - (-0.0001)) < 1e-12
    assert abs(rec2["signed_reldiff_pct"] - ((-0.0001 / 0.0121) * 100.0)) < 1e-6
    assert abs(rec2["eps_book_abs_pct"] - ((0.0001 / 0.0121) * 100.0)) < 1e-6


def test_candidate_family_classification():
    """Tests formal scientific classification across all 4 families."""
    for cid, exp_family in [
        ("S1", "SPATIAL_CONVERGENCE"),
        ("S2", "SPATIAL_CONVERGENCE"),
        ("S3", "SPATIAL_CONVERGENCE"),
        ("T1", "TEMPORAL_CONVERGENCE"),
        ("T2", "TEMPORAL_CONVERGENCE"),
        ("T3", "TEMPORAL_CONVERGENCE"),
        ("L1", "LENGTH_SCALE_CHARACTERIZATION"),
        ("L2", "LENGTH_SCALE_CHARACTERIZATION"),
        ("L3", "LENGTH_SCALE_CHARACTERIZATION"),
        ("ADAPT_13K", "ADAPTIVE_REFINEMENT")
    ]:
        res = classify_candidate(cid)
        assert res["family"] == exp_family
        if exp_family == "LENGTH_SCALE_CHARACTERIZATION":
            assert "REGULARIZATION" in res["scientific_interpretation"] or "NOT numerical mesh convergence" in res["scientific_interpretation"]


def _make_mock_candidate_report(cid, elements, k0, f_max, u_peak, w_ext_final, e_frac_final, e_elas_final):
    """Helper to construct synthetic candidate evaluation report for aggregation testing."""
    e_model = e_frac_final + e_elas_final
    d_book = e_model - w_ext_final
    eps_book = (abs(d_book) / max(abs(w_ext_final), abs(e_model))) * 100.0
    return {
        "candidate_id": cid,
        "job_telemetry": {
            "job_id": "MOCK_" + cid,
            "job_name": CANDIDATE_CATALOG.get(cid, {}).get("name", cid),
            "finite_elements": elements,
            "layered_elements": elements * 3,
            "solver_exit_status": 0
        },
        "mechanical_response": {
            "K0_kN_per_mm": k0,
            "K0_R2": 0.9999996,
            "delta_K0_vs_S1_ref_pct": compute_relative_difference(137.945520, k0),
            "F_max_kN": f_max,
            "u_at_F_max_mm": u_peak,
            "delta_F_max_vs_S1_ref_pct": compute_relative_difference(0.757778, f_max),
            "delta_u_peak_vs_S1_ref_pct": compute_relative_difference(0.005857, u_peak),
            "u_final_mm": 0.0100,
            "F_final_kN": 0.0002,
            "W_ext_final_mJ": w_ext_final
        },
        "energy_balance": {
            "has_sdv_energies": True,
            "final_e_elas_mJ": e_elas_final,
            "final_e_frac_mJ": e_frac_final,
            "final_e_model_mJ": e_model,
            "final_w_ext_mJ": w_ext_final,
            "final_delta_book_mJ": d_book,
            "final_signed_reldiff_pct": (d_book / w_ext_final) * 100.0,
            "final_eps_book_abs_pct": eps_book
        }
    }


def test_spatial_family_comparison_aggregation():
    """Tests spatial convergence family aggregator (S1 -> S2 -> S3)."""
    reports = {
        "S1": _make_mock_candidate_report("S1", 15192, 137.945520, 0.757778, 0.005857, 2.359329, 2.340220, 0.001161),
        "S2": _make_mock_candidate_report("S2", 32184, 137.950000, 0.758000, 0.005858, 2.361000, 2.342000, 0.001150),
        "S3": _make_mock_candidate_report("S3", 41912, 137.952000, 0.758100, 0.005859, 2.362000, 2.343000, 0.001140)
    }
    comp = compare_spatial_convergence_family(reports)
    assert comp["family"] == "SPATIAL_CONVERGENCE"
    assert len(comp["summary_table"]) == 3
    assert "S1_to_S2" in comp["successive_differences"]
    assert "S2_to_S3" in comp["successive_differences"]
    assert comp["successive_differences"]["S1_to_S2"]["elements_change_pct"] > 100.0


def test_temporal_family_comparison_aggregation():
    """Tests temporal convergence family aggregator (T1 -> T2 -> T3) with T2 anchor reuse."""
    reports = {
        "T1": _make_mock_candidate_report("T1", 15192, 137.940000, 0.756500, 0.005850, 2.355000, 2.338000, 0.001200),
        "S1": _make_mock_candidate_report("S1", 15192, 137.945520, 0.757778, 0.005857, 2.359329, 2.340220, 0.001161), # Reused as T2
        "T3": _make_mock_candidate_report("T3", 15192, 137.946000, 0.757900, 0.005858, 2.360000, 2.341000, 0.001155)
    }
    comp = compare_temporal_convergence_family(reports)
    assert comp["family"] == "TEMPORAL_CONVERGENCE"
    assert len(comp["summary_table"]) == 3
    assert "T1_to_T2" in comp["successive_differences"]
    assert "T2_to_T3" in comp["successive_differences"]


def test_length_scale_sensitivity_family_aggregation():
    """Tests length scale characterization family aggregator (L1 -> L2 -> L3) with L1 anchor reuse."""
    reports = {
        "S3": _make_mock_candidate_report("S3", 41912, 137.952000, 0.758100, 0.005859, 2.362000, 2.343000, 0.001140), # Reused as L1 (l0=0.0075)
        "L2": _make_mock_candidate_report("L2", 41912, 137.950000, 0.620000, 0.006200, 2.380000, 2.360000, 0.001100), # l0=0.01125
        "L3": _make_mock_candidate_report("L3", 41912, 137.948000, 0.540000, 0.006500, 2.400000, 2.380000, 0.001050)  # l0=0.01500
    }
    comp = compare_length_scale_sensitivity_family(reports)
    assert comp["family"] == "LENGTH_SCALE_CHARACTERIZATION"
    assert len(comp["summary_table"]) == 3
    assert comp["scaling_trends"]["F_max_trend"] == "DECREASING_WITH_LARGER_L0"


def test_adaptive_vs_reference_comparison():
    """Tests adaptive candidate vs S1 reference comparison."""
    s1_rep = _make_mock_candidate_report("S1", 15192, 137.945520, 0.757778, 0.005857, 2.359329, 2.340220, 0.001161)
    ad_rep = _make_mock_candidate_report("ADAPT_13K", 13897, 137.820000, 0.752000, 0.005860, 2.355000, 2.338000, 0.001150)
    
    comp = compare_adaptive_vs_reference(s1_rep, ad_rep)
    assert comp["element_comparison"]["reference_elements"] == 15192
    assert comp["element_comparison"]["adaptive_elements"] == 13897
    assert abs(comp["element_comparison"]["element_reduction_pct"] - 8.5242) < 0.01
    assert abs(comp["mechanical_parity"]["delta_K0_pct"]) < 0.20
    assert abs(comp["mechanical_parity"]["delta_F_max_pct"]) < 1.00
