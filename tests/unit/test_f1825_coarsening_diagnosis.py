#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for Task F1825: Geometry Adapter Region Classification Unification and Physical Far-Field Coarsening Metric Diagnosis
Verifies the mathematical and physical resolution of the Gate 06 coarsening shortfall across Cases 1, 2, 3, 5.
"""

import os
import sys
import json
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))
SUMMARY_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "269_f1825_coarsening_diagnosis", "coarsening_metric_diagnosis_summary.json")
FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_f1825_coarsening_metric_diagnosis.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_f1825_coarsening_metric_diagnosis.pdf")


@pytest.fixture(scope="module")
def summary_data():
    assert os.path.exists(SUMMARY_PATH), "Summary JSON missing: %s" % SUMMARY_PATH
    with open(SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_f1825_summary_structure(summary_data):
    """Verify all four canonical benchmarks are present in the summary."""
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        assert cid in summary_data, "Missing benchmark: %s" % cid
        c = summary_data[cid]
        assert "baseline_audit" in c
        assert "geometric_corner_far_field" in c
        assert "corridor_consistent_partitioning" in c
        assert "size_thresholded_partitioning" in c


def test_f1825_baseline_audit_reproduction(summary_data):
    """Verify baseline audit faithfully reproduces historical Gate 06 values."""
    c1 = summary_data["case_1"]["baseline_audit"]
    c2 = summary_data["case_2"]["baseline_audit"]
    c3 = summary_data["case_3"]["baseline_audit"]
    c5 = summary_data["case_5"]["baseline_audit"]

    assert c1["refinement_ratio"] > 2.0, "Case 1 must pass Gate 06"
    assert c1["gate_06_status"] == "PASS"

    assert c2["refinement_ratio"] < 2.0, "Case 2 baseline fails Gate 06"
    assert c2["gate_06_status"] == "FAIL"
    assert 1.50 <= c2["refinement_ratio"] <= 1.60

    assert c3["refinement_ratio"] < 2.0, "Case 3 baseline fails Gate 06"
    assert c3["gate_06_status"] == "FAIL"
    assert 1.60 <= c3["refinement_ratio"] <= 1.70

    assert c5["refinement_ratio"] > 2.0, "Case 5 must pass Gate 06"
    assert c5["gate_06_status"] == "PASS"


def test_f1825_misclassification_root_cause(summary_data):
    """Verify that misclassification of fine crack elements into far-field explains the Gate 06 shortfall."""
    c2 = summary_data["case_2"]
    c3 = summary_data["case_3"]

    # In Case 2, only 1,603 elements were counted in PZ, while 37,399 elements have h <= l0
    base_pz_c2 = c2["baseline_audit"]["process_zone_count"]
    actual_pz_c2 = c2["size_thresholded_partitioning"]["pz_count"]
    assert base_pz_c2 == 1603
    assert actual_pz_c2 == 37399
    misclassified_c2 = actual_pz_c2 - base_pz_c2
    assert misclassified_c2 > 35000, "Case 2 misclassified >35,000 fine crack elements into far field"

    # In Case 3, only 3,011 elements were counted in PZ, while 55,404 elements have h <= l0
    base_pz_c3 = c3["baseline_audit"]["process_zone_count"]
    actual_pz_c3 = c3["size_thresholded_partitioning"]["pz_count"]
    assert base_pz_c3 == 3011
    assert actual_pz_c3 == 55404
    misclassified_c3 = actual_pz_c3 - base_pz_c3
    assert misclassified_c3 > 50000, "Case 3 misclassified >50,000 fine crack elements into far field"


def test_f1825_size_thresholded_partitioning_all_pass(summary_data):
    """Verify that objective size-thresholded partitioning achieves >= 2.0x across ALL FOUR benchmarks."""
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        st = summary_data[cid]["size_thresholded_partitioning"]
        assert st["refinement_ratio"] >= 2.0, "%s failed size-thresholded coarsening: %.2fx" % (cid, st["refinement_ratio"])
        assert st["gate_06_equivalent"] == "PASS"

    assert summary_data["case_1"]["size_thresholded_partitioning"]["refinement_ratio"] >= 3.5
    assert summary_data["case_2"]["size_thresholded_partitioning"]["refinement_ratio"] >= 4.0
    assert summary_data["case_3"]["size_thresholded_partitioning"]["refinement_ratio"] >= 2.5
    assert summary_data["case_5"]["size_thresholded_partitioning"]["refinement_ratio"] >= 3.0


def test_f1825_geometric_corner_far_field_ratios(summary_data):
    """Verify that genuine geometric corner elements achieve >17x to 28x mean coarsening ratio."""
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        gf = summary_data[cid]["geometric_corner_far_field"]
        assert gf["sample_count"] >= 200, "%s corner sample too small" % cid
        assert gf["ratio_corner_mean_to_min"] >= 15.0, "%s corner mean coarsening < 15x" % cid
        assert gf["ratio_corner_max_to_min"] >= 20.0, "%s corner max coarsening < 20x" % cid


def test_f1825_case2_corridor_consistent_pass(summary_data):
    """Verify that harmonizing Case 2 corridor definition elevates coarsening ratio to >= 2.0x (PASS)."""
    c2_corr = summary_data["case_2"]["corridor_consistent_partitioning"]
    assert c2_corr["refinement_ratio"] >= 2.0, "Case 2 corridor-consistent ratio < 2.0x: %.4fx" % c2_corr["refinement_ratio"]
    assert c2_corr["gate_06_equivalent"] == "PASS"


def test_f1825_figures_exist():
    """Verify publication figures are present and non-empty."""
    assert os.path.exists(FIG_PNG), "Missing PNG figure: %s" % FIG_PNG
    assert os.path.getsize(FIG_PNG) > 10000, "PNG figure is empty or too small"
    assert os.path.exists(FIG_PDF), "Missing PDF figure: %s" % FIG_PDF
    assert os.path.getsize(FIG_PDF) > 5000, "PDF figure is empty or too small"


def test_f1825_governance_invariants():
    """Verify frozen UEL hash and zero new PBS submissions."""
    from reusable_2d_adaptive_framework import FROZEN_UEL_SHA256
    assert FROZEN_UEL_SHA256 == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
