# -*- coding: utf-8 -*-
"""
tests/unit/test_f1753_r03_damage_classification.py
Unit tests verifying the scientific classification and forensic diagnosis of Finding F1753-R03.
Ensures quantitative verification of the decisive locus, 18 severed wake elements,
history monotonicity, crack jump correlation, and governance integrity.
"""

import os
import json
import hashlib
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RECEIPT_PATH = os.path.join(ROOT, "results", "validation", "f1753_r03_damage_violation_diagnostic.json")
REPORT_PATH = os.path.join(ROOT, "docs", "validation", "F1753_R03_DAMAGE_IRREVERSIBILITY_CLASSIFICATION_REPORT.md")
FROZEN_UEL_PATH = os.path.join(ROOT, "models", "pandey_kumar_mode1", "234_f1752_case2_continuation", "f42_mixed_uel.for")
EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

@pytest.fixture(scope="module")
def receipt():
    assert os.path.exists(RECEIPT_PATH), f"Receipt not found at {RECEIPT_PATH}"
    with open(RECEIPT_PATH, "r") as f:
        return json.load(f)

def test_r03_receipt_structure(receipt):
    """Verify receipt has all mandatory fields for Finding F1753-R03."""
    required_keys = [
        "benchmark", "investigated_transition", "frame_190_time", "frame_191_time",
        "time_increment", "min_delta_d_sdv1", "locus_element_id", "locus_integration_point",
        "locus_centroid", "locus_d_frame_190", "locus_d_frame_191", "locus_h_frame_190",
        "locus_h_frame_191", "locus_delta_h", "total_violating_ips", "total_violating_elements",
        "violating_elements_list", "all_violating_elements_severed", "history_monotonicity_strictly_satisfied",
        "crack_jump_max_element_id", "crack_jump_max_delta_d", "crack_jump_max_delta_h",
        "crack_jump_max_centroid", "distance_to_crack_front_mm", "scientific_classification"
    ]
    for key in required_keys:
        assert key in receipt, f"Missing required key '{key}' in receipt"

def test_r03_decisive_locus(receipt):
    """Verify exact quantitative identification of the decisive locus."""
    assert receipt["locus_element_id"] == 10839
    assert receipt["locus_integration_point"] == 1
    assert pytest.approx(receipt["locus_d_frame_190"], abs=1e-6) == 0.993675
    assert pytest.approx(receipt["locus_d_frame_191"], abs=1e-6) == 0.993489
    assert pytest.approx(receipt["min_delta_d_sdv1"], abs=1e-6) == -0.0001862
    
    # Coordinates in distal right ligament
    x, y = receipt["locus_centroid"]
    assert 0.78 < x < 0.79
    assert 0.635 < y < 0.645

def test_r03_history_monotonicity(receipt):
    """Verify history variable H is strictly non-decreasing at the locus."""
    assert receipt["locus_delta_h"] >= 0.0
    assert pytest.approx(receipt["locus_h_frame_190"], abs=1e-4) == 28.5122
    assert pytest.approx(receipt["locus_h_frame_191"], abs=1e-4) == 28.5122
    assert receipt["history_monotonicity_strictly_satisfied"] is True

def test_r03_spatial_confinement_to_severed_wake(receipt):
    """Verify violation is strictly confined to 18 elements in the severed crack wake."""
    assert receipt["total_violating_ips"] == 72
    assert receipt["total_violating_elements"] == 18
    assert len(receipt["violating_elements_list"]) == 18
    assert 10839 in receipt["violating_elements_list"]
    assert receipt["all_violating_elements_severed"] is True

def test_r03_crack_front_jump_correlation(receipt):
    """Verify dynamic crack jump occurrence in immediate vicinity."""
    assert receipt["crack_jump_max_element_id"] == 19633
    assert receipt["crack_jump_max_delta_d"] > 0.25
    assert receipt["crack_jump_max_delta_h"] > 1.0
    # Separation is within ~0.06 mm (~7-8 element widths)
    assert 0.04 < receipt["distance_to_crack_front_mm"] < 0.07

def test_r03_scientific_classification(receipt):
    """Verify scientific classification is POST_SEVERANCE_CRACK_WAKE_RESIDUAL_EQUILIBRIUM_OSCILLATION."""
    assert receipt["scientific_classification"] == "POST_SEVERANCE_CRACK_WAKE_RESIDUAL_EQUILIBRIUM_OSCILLATION"

def test_r03_report_existence_and_content():
    """Verify classification report exists and contains essential evidence sections."""
    assert os.path.exists(REPORT_PATH), f"Report not found at {REPORT_PATH}"
    with open(REPORT_PATH, "r") as f:
        content = f.read()
    
    assert "F1753-R03" in content
    assert "10839" in content
    assert "AUTHENTIC_BASELINE_LOCAL_DAMAGE_MONOTONICITY_VIOLATION" in content
    assert "0.993675" in content or "0.993489" in content
    assert "28.512" in content
    assert "19633" in content
    assert "F1753-R04" in content or "Nodal Degree of Freedom Extraction Limitation" in content
    assert "FAIL" in content and "strict" in content.lower()

def test_frozen_uel_sha():
    """Verify bitwise immutability of the production UEL subroutine."""
    assert os.path.exists(FROZEN_UEL_PATH)
    with open(FROZEN_UEL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_sha == EXPECTED_FROZEN_UEL_SHA
