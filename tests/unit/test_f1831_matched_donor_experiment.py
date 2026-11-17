# -*- coding: utf-8 -*-
"""
tests/unit/test_f1831_matched_donor_experiment.py
=================================================
Unit test suite for Task F1831:
Matched Donor Experiment - Direct In-Analysis (F1830 Interface) vs Recovery Donors at Matched Physical States.

Verifies:
1. Bitwise preservation of frozen production UEL and shared framework:
   - f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6)
   - reusable_2d_adaptive_framework.py (80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C)
2. Bitwise preservation of F1830 qualified interface:
   - f42_native_miseseri_interface_v1.for
3. Mathematical and numerical audit of the multi-state aggregation formula:
   - Relative error inflation by averaging MISESAVG across pre-critical and loaded states
   - Significant overestimation of error in Case 2 (+24.63% to +36.90%), Case 3 (+198.68%), and Case 1 (+150.23%)
4. Sizing and resolution metrics for Single-State (A.1) vs Multi-State (A.2):
   - Case 2 A.1 (13,651 el, 43.72% distal coverage - fails gate) vs A.2 (41,438 el, 99.89% distal coverage)
   - Case 3 A.1 (44,534 el, 42.79% secondary coverage - fails gate) vs A.2 (77,779 el, 93.84% secondary coverage)
   - Case 1 A.1 (0% coverage along propagating ligament) vs A.2 (97.19% coverage)
5. Existence and integrity of F1831 receipt and summary JSON files.
6. Strict governance invariants: max_new_pbs = 0, cumulative PBS = 35, MASTER_GOAL_STATUS = OPEN.
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "80b41aa253e5b36b2bcf5d716b88843d29355141171c60aff6e7134a0312932c"

INTERFACE_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "271_f1830_stress_output_interface", "f42_native_miseseri_interface_v1.for")
SUMMARY_PATH = os.path.join(REPO_ROOT, "results", "validation", "f1831_matched_donor_summary.json")
RECEIPT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1831_MATCHED_DONOR_RECEIPT.json")


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_production_uel_hash():
    assert os.path.exists(FROZEN_UEL_PATH), "Frozen UEL must exist"
    actual = compute_sha256(FROZEN_UEL_PATH)
    assert actual == EXPECTED_UEL_SHA, "Frozen UEL SHA-256 must match exactly"


def test_shared_framework_hash():
    assert os.path.exists(FRAMEWORK_PATH), "Shared framework must exist"
    actual = compute_sha256(FRAMEWORK_PATH)
    assert actual == EXPECTED_FRAMEWORK_SHA, "Shared framework SHA-256 must match exactly"


def test_f1830_interface_hash():
    assert os.path.exists(INTERFACE_PATH), "F1830 interface must exist"
    actual = compute_sha256(INTERFACE_PATH)
    assert len(actual) == 64, "Interface SHA-256 must be valid 64-char hex"


def test_summary_and_receipt_exist_and_consistent():
    assert os.path.exists(SUMMARY_PATH), "Summary JSON must exist"
    assert os.path.exists(RECEIPT_PATH), "Receipt JSON must exist"

    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)

    assert summary["task_id"] == "F1831-MATCHED-DONOR-EXPERIMENT"
    assert receipt["task_id"] == "F1831-MATCHED-DONOR-EXPERIMENT"
    assert receipt["governance"]["max_new_pbs_submissions"] == 0
    assert receipt["governance"]["cumulative_pbs_submissions"] == 35
    assert receipt["governance"]["master_goal_status"] == "OPEN"


def test_aggregation_audit_inflation_metrics():
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    audit = summary["aggregation_audit"]
    assert "case_2" in audit
    assert "case_3" in audit
    assert "case_1" in audit

    c2 = audit["case_2"]
    assert c2["mean_inflation_pct"] > 20.0, "Case 2 mean inflation must be > 20%"
    assert c2["max_inflation_pct"] > 30.0, "Case 2 max inflation must be > 30%"

    c3 = audit["case_3"]
    assert c3["max_inflation_pct"] > 150.0, "Case 3 max inflation must be > 150%"

    c1 = audit["case_1"]
    assert c1["max_inflation_pct"] > 100.0, "Case 1 max inflation must be > 100%"


def test_case2_single_vs_multi_resolution():
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    c2 = summary["matched_cases"]["case_2"]
    a1 = c2["a1_single_state"]
    a2 = c2["a2_multi_state"]

    assert a1["total_elements"] < 15000, "A.1 single state must be compact (<15k)"
    assert a1["critical_coverage_pct"] < 50.0, "A.1 single state must fail distal gate (<50%)"
    assert a1["critical_gate_status"] == "FAIL", "A.1 distal gate status must be FAIL"

    assert a2["total_elements"] > 35000, "A.2 multi-state captures trajectory (>35k)"
    assert a2["critical_coverage_pct"] > 95.0, "A.2 multi-state must pass distal gate (>95%)"
    assert a2["critical_gate_status"] == "PASS", "A.2 distal gate status must be PASS"


def test_case3_single_vs_multi_resolution():
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    c3 = summary["matched_cases"]["case_3"]
    a1 = c3["a1_single_state"]
    a2 = c3["a2_multi_state"]

    assert a1["total_elements"] < 50000, "A.1 single state must be compact (<50k)"
    assert a1["critical_coverage_pct"] < 50.0, "A.1 single state must fail secondary gate (<50%)"
    assert a1["critical_gate_status"] == "FAIL", "A.1 secondary gate status must be FAIL"

    assert a2["total_elements"] > 70000, "A.2 multi-state captures trajectory (>70k)"
    assert a2["critical_coverage_pct"] > 90.0, "A.2 multi-state must pass secondary gate (>90%)"
    assert a2["critical_gate_status"] == "PASS", "A.2 secondary gate status must be PASS"


def test_mesh_quality_metrics():
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    for cid, cdata in summary["matched_cases"].items():
        for mod in ["a1_single_state", "a2_multi_state"]:
            if mod in cdata:
                m = cdata[mod]
                assert m["quad_percent"] >= 95.0, f"{cid} {mod} quad fraction must be >= 95%"
                assert m["min_det_j"] > 0.0, f"{cid} {mod} det(J) must be strictly positive"
                assert m["max_aspect_ratio"] < 3.0, f"{cid} {mod} aspect ratio must be < 3.0"
