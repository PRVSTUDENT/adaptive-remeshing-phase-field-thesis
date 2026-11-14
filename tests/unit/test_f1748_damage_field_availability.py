# -*- coding: utf-8 -*-
"""
tests/unit/test_f1748_damage_field_availability.py
Unit test suite validating Task F1748:
- Authentic coupled phase-field damage data availability in Case 2 and Case 3
- UEL 3-layer architecture, label offsets, and SDV indexing
- Elimination of stress-recovery blindspot (100% corridor coverage, zero barriers)
- Damage-aware sizing simulation accuracy vs published targets
- Strict zero-PBS governance and accounting
"""

import os
import json
import csv
import pytest
import numpy as np

TASK_JSON_PATH = "project_coordination/ACTIVE_TASK.json"
SUMMARY_JSON_PATH = "results/validation/f1748_coupled_damage_availability_summary.json"
FIG_PNG_PATH = "results/figures/fig_f1748_damage_field_synthesis.png"
FIG_PDF_PATH = "results/figures/fig_f1748_damage_field_synthesis.pdf"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_f1748_task_identity_and_zero_pbs_governance():
    """Verify task registration and strict zero-PBS governance."""
    assert os.path.exists(TASK_JSON_PATH), f"Missing {TASK_JSON_PATH}"
    with open(TASK_JSON_PATH, "r", encoding="utf-8") as f:
        task = json.load(f)

    assert task["task_id"] in ["F1748-AUTHENTIC-COUPLED-DAMAGE-FIELD-RECOVERY-AND-INDICATOR-FEASIBILITY", "F1749-TIME-CAUSAL-DAMAGE-INDICATOR-IMPLEMENTATION-AND-VALIDATION",
            "F1750-LOCAL-NATIVE-DAMAGE-SIZING-PROBE"]
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 25
    assert task["frozen_uel_sha256"] == FROZEN_UEL_HASH
    assert len(task["historical_pbs_job_ids"]) == 25


def test_f1748_source_artifact_existence():
    """Verify all required Case 2, Case 3, and Task F1748 artifacts exist."""
    required_paths = [
        "results/validation/f1735_case2_final_frame_sdv.csv",
        "results/validation/f1735_case2_odb_summary.json",
        "results/validation/f1694_sec43_five_state_damage_record.json",
        "results/validation/f1743_extracted_transient_uel.json",
        "models/pandey_kumar_mode1/190_pk_sec43_job1_rerun/f1690_sec43_damage_data.json",
        SUMMARY_JSON_PATH,
        FIG_PNG_PATH,
        FIG_PDF_PATH
    ]
    for p in required_paths:
        assert os.path.exists(p), f"Required artifact missing: {p}"
        assert os.path.getsize(p) > 0, f"Artifact is empty: {p}"


def test_f1748_layer3_offset_and_element_mapping():
    """Verify 3-layer UEL element offsets: Layer 3 label = phys_id + 2*N_phys."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    benchmarks = summary["field_availability_matrix"]["benchmarks"]
    c2 = next(b for b in benchmarks if b["case_id"] == "Case 2")
    c3 = next(b for b in benchmarks if b["case_id"] == "Case 3")

    # Case 2: 23,965 elements
    assert c2["physical_elements"] == 23965
    assert c2["layer3_element_offset"] == 2 * 23965  # 47930
    assert c2["layer3_element_range"] == [47931, 71895]

    # Case 3 coarse: 3,923 elements
    c3_coarse = c3["coarse_base_mesh"]
    assert c3_coarse["physical_elements"] == 3923
    assert c3_coarse["layer3_element_offset"] == 2 * 3923  # 7846
    assert c3_coarse["layer3_element_range"] == [7847, 11769]

    # Case 3 fine: 24,718 elements
    c3_fine = c3["fine_reference_mesh"]
    assert c3_fine["physical_elements"] == 24718
    assert c3_fine["layer3_element_offset"] == 2 * 24718  # 49436
    assert c3_fine["layer3_element_range"] == [49437, 74154]


def test_f1748_case2_damage_and_history_metrics():
    """Verify Case 2 damage bounds and history variable statistics."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    c2_stats = summary["case2_statistics"]
    assert c2_stats["total_elements"] == 23965
    d_dist = c2_stats["damage_distribution"]
    assert 0.0 <= d_dist["min_d"] <= 1e-6
    assert 1.0 <= d_dist["max_d"] <= 1.01  # Allow tiny numerical overshoot in phase-field solver
    assert d_dist["counts"]["d_ge_050"] == 1762
    assert d_dist["counts"]["d_ge_090"] == 849

    h_dist = c2_stats["history_distribution"]
    assert h_dist["H0_threshold_kN_mm2"] == pytest.approx(0.180, abs=1e-5)
    assert h_dist["count_ge_H0"] == 1306
    assert 5.0 <= h_dist["pct_ge_H0"] <= 6.0  # Sharp localization of driving energy


def test_f1748_case3_corridor_resolution_and_zero_barriers():
    """Verify that damage indicator (d_cut = 0.05) eliminates stress error barriers."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    c3_corridors = summary["case3_statistics"]["corridor_audit_comparison"]
    prim = c3_corridors["primary_corridor"]
    sec = c3_corridors["secondary_corridor"]

    # Stress error failure modes: 15/35 elements below tau in primary, 7/21 suppressed in secondary
    assert prim["stress_error_barrier_count"] == 15
    assert prim["stress_error_barrier_span_mm"] == 4.47
    assert sec["stress_error_suppressed_count"] == 7
    assert sec["stress_error_suppressed_span_mm"] == 4.72

    # Damage indicator resolution: 100% coverage, 0 barriers
    assert prim["damage_indicator_coverage_pct"] == 100.0
    assert prim["damage_indicator_barrier_count"] == 0
    assert prim["damage_indicator_barrier_span_mm"] == 0.0

    assert sec["damage_indicator_coverage_pct"] == 100.0
    assert sec["damage_indicator_suppressed_count"] == 0
    assert sec["damage_indicator_suppressed_span_mm"] == 0.0


def test_f1748_sizing_prediction_accuracy():
    """Verify damage indicator sizing prediction matches published target within 5%."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    scans = summary["case3_statistics"]["sizing_scans"]
    scan_005 = next(s for s in scans if abs(s["d_cut"] - 0.05) < 1e-4)

    assert scan_005["active_percentage"] == pytest.approx(17.0, abs=0.1)
    assert scan_005["suppressed_percentage"] == pytest.approx(83.0, abs=0.1)
    assert scan_005["primary_corridor_coverage_pct"] == 100.0
    assert scan_005["secondary_corridor_coverage_pct"] == 100.0

    # Core sizing: 12,416 elements vs published 12,168
    assert scan_005["predicted_elements_l0_third"] == 12416
    assert scan_005["deviation_from_published_pct"] < 3.0  # Exactly 2.04%
