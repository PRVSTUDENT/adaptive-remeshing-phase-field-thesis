# -*- coding: utf-8 -*-
"""
test_evaluate_mode1_job1_miseseri.py

Unit and Regression Test Suite for Mode-I Layered Job-1_UEL MISESERI Evaluator
Protocol Version: 2
Phase: MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

Validates:
1. 5-Region spatial boundary definitions and predicate classifications
2. Element ID mapping from companion Layer 3 (5813..8718) to physical mesh (1..2906)
3. Dataset loading, missing ID detection, and duplicate detection
4. Global statistics computation (count, sum, mean, median, std, max, peak-to-mean)
5. Normalized footprints and bounding box coordinates (dx, dy)
6. Transverse corridor width profiles w(x) across 20 longitudinal bins
7. High-error parasitic outside-corridor ratios
8. Pairwise element-by-element comparisons (delta, RMS, correlation r) and matched displacement scaling
9. Predeclared 3-branch scientific decision logic without arbitrary 5%/2% thresholds:
   - LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION
   - LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT
   - LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION
10. End-to-end evaluation and report formatting on canonical coarse mesh baseline
"""

import os
import sys
import copy
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.evaluation.evaluate_mode1_job1_miseseri import (
    REGION_DEFINITIONS,
    CANONICAL_TOTAL_ELEMENTS,
    NORMALIZED_THRESHOLDS,
    classify_element_region,
    load_canonical_coordinates,
    load_miseseri_dataset,
    compute_global_statistics,
    compute_five_region_statistics,
    compute_far_field_and_wake_share,
    compute_normalized_footprints,
    compute_outside_corridor_ratio,
    compute_transverse_corridor_widths,
    compare_layered_vs_standard,
    compare_spatial_footprint_to_publication,
    assign_scientific_decision_logic,
    execute_mode1_job1_evaluation,
    format_markdown_report
)

CANONICAL_BASELINE_CSV = os.path.join(
    "models", "pandey_kumar_mode1", "adaptive_direction_evidence_package", "miseseri_corrected_2906.csv"
)


def test_canonical_region_classification():
    """Verify that representative points in the domain classify correctly into 5 regions."""
    # Boundary points
    assert classify_element_region(0.5, 0.05) == "BOUNDARY_REGIONS"
    assert classify_element_region(0.5, 0.95) == "BOUNDARY_REGIONS"

    # Crack band (y in [0.45, 0.55])
    assert classify_element_region(0.2, 0.50) == "CRACK_WAKE"
    assert classify_element_region(0.5, 0.50) == "CRACK_TIP_CORRIDOR"
    assert classify_element_region(0.6, 0.50) == "CRACK_TIP_CORRIDOR"
    assert classify_element_region(0.8, 0.50) == "RIGHT_LIGAMENT"

    # Far field (y in [0.10, 0.45) or (0.55, 0.90])
    assert classify_element_region(0.5, 0.30) == "FAR_FIELD"
    assert classify_element_region(0.5, 0.70) == "FAR_FIELD"


def test_baseline_dataset_loading_and_validation():
    """Verify that canonical baseline CSV loads exactly 2,906 elements with zero duplicates or missing IDs."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found at: %s" % CANONICAL_BASELINE_CSV)

    elements, validation = load_miseseri_dataset(CANONICAL_BASELINE_CSV)

    assert validation["is_complete_and_unique"] is True
    assert validation["unique_elements_loaded"] == CANONICAL_TOTAL_ELEMENTS
    assert validation["missing_ids_count"] == 0
    assert validation["duplicate_entries_detected"] == 0
    assert len(elements) == 2906
    assert "one WHOLE_ELEMENT MISESERI value per underlying finite element" in validation["element_representation"]


def test_companion_layer3_id_mapping(tmp_path):
    """Verify that companion Layer 3 element IDs (5813..8718) are correctly mapped to 1..2906."""
    coords = load_canonical_coordinates(CANONICAL_BASELINE_CSV)

    # Create dummy layered CSV with IDs starting at 5813
    dummy_csv = str(tmp_path / "dummy_layered.csv")
    with open(dummy_csv, "w") as fp:
        fp.write("element_id,miseseri\n")
        for i in range(1, CANONICAL_TOTAL_ELEMENTS + 1):
            fp.write("%d,0.01000\n" % (i + 5812))

    elements, val = load_miseseri_dataset(dummy_csv, fallback_coords=coords)
    assert val["is_complete_and_unique"] is True
    assert 1 in elements
    assert 2906 in elements
    assert elements[1]["raw_element_id"] == 5813
    assert elements[2906]["raw_element_id"] == 8718


def test_five_region_statistics_match_governed_counts():
    """Verify that canonical baseline elements partition into governed region counts."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    elements, _ = load_miseseri_dataset(CANONICAL_BASELINE_CSV)
    reg_stats = compute_five_region_statistics(elements)

    assert reg_stats["CRACK_TIP_CORRIDOR"]["element_count"] == 49
    assert reg_stats["CRACK_WAKE"]["element_count"] == 110
    assert reg_stats["RIGHT_LIGAMENT"]["element_count"] == 119
    assert reg_stats["FAR_FIELD"]["element_count"] == 2080
    assert reg_stats["BOUNDARY_REGIONS"]["element_count"] == 548

    for reg_name, s in reg_stats.items():
        assert s["count_matches_expected"] is True


def test_global_statistics_exact_values():
    """Verify global statistics on canonical baseline."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    elements, _ = load_miseseri_dataset(CANONICAL_BASELINE_CSV)
    g = compute_global_statistics(elements)

    assert g["count"] == 2906
    assert abs(g["sum_mpa"] - 28.7046) < 1e-3
    assert abs(g["max_mpa"] - 0.950009) < 1e-4
    assert abs(g["mean_mpa"] - 0.0098777) < 1e-5


def test_normalized_footprints_and_corridor_widths():
    """Verify footprint bounding boxes and transverse corridor width algorithm."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    elements, _ = load_miseseri_dataset(CANONICAL_BASELINE_CSV)
    footprints = compute_normalized_footprints(elements)

    fp_50 = next(f for f in footprints if f["threshold_pct"] == 50.0)
    assert fp_50["element_count"] == 5
    assert abs(fp_50["bounding_box"]["x_min"] - 0.4679) < 1e-3
    assert abs(fp_50["bounding_box"]["x_max"] - 0.5052) < 1e-3

    fp_10 = next(f for f in footprints if f["threshold_pct"] == 10.0)
    assert fp_10["element_count"] == 26
    assert abs(fp_10["bounding_box"]["dx"] - 0.1218) < 1e-3
    assert abs(fp_10["bounding_box"]["dy"] - 0.0930) < 1e-3

    widths = compute_transverse_corridor_widths(elements)
    assert len(widths["bin_centers"]) == 20
    assert len(widths["width_eta_10pct"]) == 20
    # Boundary widths for eta >= 10% should be zero
    assert widths["width_eta_10pct"][0] == 0.0
    assert widths["width_eta_10pct"][-1] == 0.0


def test_matched_displacement_state_scaling():
    """Verify linear elastic displacement scaling for unmatched displacement states."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    elements, _ = load_miseseri_dataset(CANONICAL_BASELINE_CSV)

    # Simulate a run with 5x displacement (u = 0.0050 mm vs u = 0.0010 mm)
    elements_5x = copy.deepcopy(elements)
    for e in elements_5x.values():
        e["miseseri"] *= 5.0

    # Unscaled comparison gives 5x difference
    pw_unscaled = compare_layered_vs_standard(elements_5x, elements, displacement_scale_factor=1.0)
    assert pw_unscaled["matched_displacement_status"] == "MATCHED_DIRECTLY"
    assert pw_unscaled["mean_diff_mpa"] > 0.03

    # Scaled comparison (scale_factor = 5.0) recovers exact identity
    pw_scaled = compare_layered_vs_standard(elements_5x, elements, displacement_scale_factor=5.0)
    assert pw_scaled["matched_displacement_status"] == "SCALED_FOR_LINEAR_ELASTIC_PARITY"
    assert abs(pw_scaled["mean_diff_mpa"]) < 1e-12
    assert abs(pw_scaled["max_abs_diff_mpa"]) < 1e-12
    assert abs(pw_scaled["correlation_r"] - 1.0) < 1e-12


def test_predeclared_decision_logic_branches():
    """Verify that all 3 scientific decision branches trigger under objective pattern criteria."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    elements_base, _ = load_miseseri_dataset(CANONICAL_BASELINE_CSV)
    reg_base = compute_five_region_statistics(elements_base)
    fw_base = compute_far_field_and_wake_share(reg_base)

    # Branch 2: Baseline vs Baseline -> NO_MEANINGFUL_IMPROVEMENT
    pw_identity = compare_layered_vs_standard(elements_base, elements_base)
    dec_id = assign_scientific_decision_logic(pw_identity, reg_base, reg_base, fw_base, fw_base)
    assert dec_id["verdict"] == "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"

    # Branch 1: Synthetic candidate suppressing far field and enhancing crack tip -> TOWARD_TARGET_LOCALIZATION
    elements_improved = copy.deepcopy(elements_base)
    for eid, e in elements_improved.items():
        if e["region"] in ["FAR_FIELD", "CRACK_WAKE", "BOUNDARY_REGIONS"]:
            e["miseseri"] *= 0.10  # 90% error reduction in far field
        elif e["region"] == "CRACK_TIP_CORRIDOR":
            e["miseseri"] *= 1.20  # enhanced crack-tip error

    reg_imp = compute_five_region_statistics(elements_improved)
    fw_imp = compute_far_field_and_wake_share(reg_imp)
    pw_imp = compare_layered_vs_standard(elements_improved, elements_base)
    dec_imp = assign_scientific_decision_logic(pw_imp, reg_imp, reg_base, fw_imp, fw_base)
    assert dec_imp["verdict"] == "LAYERED_JOB1_TOWARD_TARGET_LOCALIZATION"

    # Branch 3: Synthetic candidate inflating far field -> AWAY_FROM_TARGET_LOCALIZATION
    elements_degraded = copy.deepcopy(elements_base)
    for eid, e in elements_degraded.items():
        if e["region"] == "FAR_FIELD":
            e["miseseri"] *= 3.0  # 3x error inflation in far field
        elif e["region"] == "CRACK_TIP_CORRIDOR":
            e["miseseri"] *= 0.50

    reg_deg = compute_five_region_statistics(elements_degraded)
    fw_deg = compute_far_field_and_wake_share(reg_deg)
    pw_deg = compare_layered_vs_standard(elements_degraded, elements_base)
    dec_deg = assign_scientific_decision_logic(pw_deg, reg_deg, reg_base, fw_deg, fw_base)
    assert dec_deg["verdict"] == "LAYERED_JOB1_AWAY_FROM_TARGET_LOCALIZATION"


def test_end_to_end_evaluation_and_report_generation(tmp_path):
    """Verify that full execution produces valid JSON results and Markdown report."""
    if not os.path.isfile(CANONICAL_BASELINE_CSV):
        pytest.skip("Canonical baseline CSV not found")

    res = execute_mode1_job1_evaluation(CANONICAL_BASELINE_CSV, CANONICAL_BASELINE_CSV,
                                        layered_disp_mm=0.0050, standard_disp_mm=0.0050)

    assert "metadata" in res
    assert "scientific_decision_verdict" in res
    assert "item1b_matched_displacement_state" in res
    assert res["scientific_decision_verdict"]["verdict"] == "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT"
    assert res["metadata"]["element_representation"] == "one WHOLE_ELEMENT MISESERI value per underlying finite element"

    report_text = format_markdown_report(res)
    assert "# Terminal Evaluation Report" in report_text
    assert "LAYERED_JOB1_NO_MEANINGFUL_IMPROVEMENT" in report_text
    assert "CRACK_TIP_CORRIDOR" in report_text
    assert "FAR_FIELD" in report_text
    assert "Matched Displacement Provenance" in report_text
