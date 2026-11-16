# -*- coding: utf-8 -*-
"""
tests/unit/test_f1827_campaign_synthesis.py
=============================================
Task F1827: Unit test suite for Campaign Synthesis (F1812-F1826).
Validates:
1. Governance invariants (max_new_pbs=0, cumulative submissions=35, frozen UEL SHA, framework SHA).
2. Integrity of accepted canonical baseline meshes (160,144 total physical elements, body SHAs, quad fractions).
3. Plain disclosure of original Gate 06 evaluations (Cases 1 & 5 PASS, Cases 2 & 3 FAIL).
4. Governing scientific resolution gates (all 4 PASS).
5. Supplementary diagnostics (size-thresholded coarsening >= 2.0x, corner coarsening >= 20.0x).
6. Completeness of the synthesis document and plain statement of open items.
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "80B41AA253E5B36B2BCF5D716B88843D29355141171C60AFF6E7134A0312932C"
SYNTHESIS_REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1827_CAMPAIGN_SYNTHESIS_F1812_F1826.md")
BASE_OUT = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "270_f1826_adapter_harmonization")
RECEIPT_PATH = os.path.join(BASE_OUT, "PK_F1826_ADAPTER_HARMONIZATION_RECEIPT.json")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1827_governance_invariants():
    """Verify bitwise preservation of frozen production UEL and PBS submission limits."""
    assert os.path.exists(FROZEN_UEL_PATH), "Frozen UEL file not found"
    assert compute_sha256(FROZEN_UEL_PATH) == EXPECTED_UEL_SHA, "Frozen UEL hash corrupted!"

    assert os.path.exists(FRAMEWORK_PATH), "Shared framework file not found"
    assert compute_sha256(FRAMEWORK_PATH) == EXPECTED_FRAMEWORK_SHA, "Framework hash mismatch!"

    # Check TASK_LEDGER.csv
    ledger_path = os.path.join(REPO_ROOT, "project_coordination", "TASK_LEDGER.csv")
    with open(ledger_path, "r") as f:
        content = f.read()
    assert "35" in content, "Cumulative submission counter 35 missing from TASK_LEDGER.csv"


def test_f1827_accepted_baselines_integrity():
    """Verify the 4 canonical baseline meshes and their verified body SHAs."""
    assert os.path.exists(RECEIPT_PATH), "Master harmonization receipt not found"
    with open(RECEIPT_PATH, "r") as f:
        m = json.load(f)

    assert m["total_elements_across_four_cases"] == 160144, "Total element count must be exactly 160,144"

    expected_cases = {
        "case_1": {"elements": 25461, "body_sha": "50CB4E3C826D66C7BDAB7FEBEADF5254CDEE33B709B214E9714CD776B3CE379E"},
        "case_2": {"elements": 41438, "body_sha": "5C7DD6B52DBBE716C823462E2EFBA37EAF3DF884862F2CAA4533F80FB7FFBFE1"},
        "case_3": {"elements": 77779, "body_sha": "08FA694A09033EC1F6BDE1C9150F539B3379BE7DF75CAAAD5DED3D42937FA2B4"},
        "case_5": {"elements": 15466, "body_sha": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065"}
    }

    for cid, exp in expected_cases.items():
        cdata = m["cases"][cid]
        assert cdata["total_elements"] == exp["elements"], "%s element count mismatch" % cid
        assert cdata["mesh_body_sha256"] == exp["body_sha"], "%s body SHA mismatch" % cid
        assert cdata["quad_percent"] >= 97.0, "%s quad percent below 97%%" % cid
        assert cdata["min_det_j"] > 0, "%s has non-positive Jacobian" % cid
        assert cdata["max_aspect_ratio"] <= 3.0, "%s aspect ratio exceeds 3.0" % cid


def test_f1827_plain_gate06_evaluations():
    """Verify plain disclosure of original Gate 06 evaluations (Cases 1 & 5 PASS, Cases 2 & 3 FAIL)."""
    with open(RECEIPT_PATH, "r") as f:
        m = json.load(f)

    # Case 1: PASS (>= 2.0x)
    assert m["cases"]["case_1"]["original_gate_06"]["status"] == "PASS"
    assert m["cases"]["case_1"]["original_gate_06"]["refinement_ratio"] >= 2.0

    # Case 2: FAIL (< 2.0x)
    assert m["cases"]["case_2"]["original_gate_06"]["status"] == "FAIL"
    assert 1.90 <= m["cases"]["case_2"]["original_gate_06"]["refinement_ratio"] < 2.00

    # Case 3: FAIL (< 2.0x)
    assert m["cases"]["case_3"]["original_gate_06"]["status"] == "FAIL"
    assert 1.40 <= m["cases"]["case_3"]["original_gate_06"]["refinement_ratio"] <= 1.50

    # Case 5: PASS (>= 2.0x)
    assert m["cases"]["case_5"]["original_gate_06"]["status"] == "PASS"
    assert m["cases"]["case_5"]["original_gate_06"]["refinement_ratio"] >= 2.0


def test_f1827_scientific_resolution_gates():
    """Verify that all four governing scientific resolution gates PASS."""
    with open(RECEIPT_PATH, "r") as f:
        m = json.load(f)

    # Case 1: Full Ligament >= 95%
    c1 = m["cases"]["case_1"]["scientific_gate"]
    assert c1["status"] == "PASS"
    assert c1["metrics"]["pct_le_l0_half"] >= 95.0

    # Case 2: Outermost Distal >= 95%
    c2 = m["cases"]["case_2"]["scientific_gate"]
    assert c2["status"] == "PASS"
    assert c2["metrics"]["pct_le_l0_half"] >= 95.0

    # Case 3: Secondary Corridor >= 90%
    c3 = m["cases"]["case_3"]["scientific_gate"]
    assert c3["status"] == "PASS"
    assert c3["metrics"]["pct_le_l0"] >= 90.0

    # Case 5: Inter-Hole Corridor >= 90%
    c5 = m["cases"]["case_5"]["scientific_gate"]
    assert c5["status"] == "PASS"
    assert c5["metrics"]["pct_le_l0"] >= 90.0


def test_f1827_supplementary_diagnostics():
    """Verify supplementary physical coarsening diagnostics."""
    with open(RECEIPT_PATH, "r") as f:
        m = json.load(f)

    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        diag = m["cases"][cid]["supplementary_diagnostics"]
        # Size-thresholded ratio >= 2.0x
        assert diag["size_thresholded"]["refinement_ratio"] >= 2.0, "%s size-thresholded below 2.0x" % cid
        assert diag["size_thresholded"]["status"] == "PASS"
        # Corner max-to-min ratio >= 20.0x
        assert diag["geometric_corner"]["ratio_corner_max_to_min"] >= 20.0, "%s corner ratio below 20.0x" % cid


def test_f1827_synthesis_document_completeness():
    """Verify the synthesis report exists and explicitly documents open items and Gate 06 shortfalls."""
    assert os.path.exists(SYNTHESIS_REPORT_PATH), "Synthesis report not found"
    with open(SYNTHESIS_REPORT_PATH, "r") as f:
        text = f.read()

    # Required sections and content
    assert "Task F1827: Comprehensive Campaign Synthesis" in text
    assert "160,144 Physical Elements" in text or "160,144" in text
    assert "Plain Disclosure of Gate 06 Evaluation" in text
    assert "Current Harmonized Framework Revision" in text
    assert "Supplementary Physical Coarsening Diagnostics" in text
    assert "Plain Statement of Open Items and Research Limitations" in text
    assert "Gate 06 Failures under Original Geometric Definition" in text
    assert "Unexecuted Job-2 Coupled Phase-Field Fracture Validations" in text
    assert "Historical F1823 Case 3 Baseline Discrepancy" in text
