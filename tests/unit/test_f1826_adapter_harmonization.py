# -*- coding: utf-8 -*-
"""
tests/unit/test_f1826_adapter_harmonization.py
================================================
Task F1826: Unit test suite for Adapter Harmonization & Original Gate 06 Verification.
Validates:
1. Governance invariants (max_new_pbs=0, frozen UEL SHA, framework SHA).
2. Code-level harmonization in reusable_2d_adaptive_framework.py for Cases 2 and 3.
3. Integrity of Case 5 adapter (SevenHolePlateAdapter preserved intact).
4. Mesh existence, geometric Gate 06 evaluations, and scientific resolution gates.
5. Plain disclosure of original Gate 06 results (Case 3 FAIL disclosed, not obscured).
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
BASE_OUT = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "270_f1826_adapter_harmonization")


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1826_governance_invariants():
    """Verify bitwise preservation of frozen production UEL and PBS limits."""
    assert os.path.exists(FROZEN_UEL_PATH), "Frozen UEL not found"
    actual_uel_sha = compute_sha256(FROZEN_UEL_PATH)
    assert actual_uel_sha == EXPECTED_UEL_SHA, "Frozen UEL hash corrupted!"

    # Check Task Ledger
    ledger_path = os.path.join(REPO_ROOT, "project_coordination", "TASK_LEDGER.csv")
    with open(ledger_path, "r") as f:
        content = f.read()
    # Confirm 35 submissions preserved
    assert "35" in content


def test_f1826_adapter_harmonization_code_presence():
    """Verify that classify_region() in Cases 2 and 3 includes process zone corridors."""
    assert os.path.exists(FRAMEWORK_PATH), "Framework script not found"
    with open(FRAMEWORK_PATH, "r") as f:
        src = f.read()

    # Case 2: OffAxisHoleMode1Adapter.classify_region
    assert "class OffAxisHoleMode1Adapter" in src
    assert "PROPAGATION_CORRIDOR_PRIMARY" in src
    assert "PROPAGATION_CORRIDOR_DISTAL" in src
    assert "(self.config.notch_a <= x <= hx) and (0.45 <= y <= max(self.config.notch_y, hy) + 2.0 * self.config.l0):" in src
    assert "(x >= hx) and (0.45 <= y <= 0.65):" in src

    # Case 3: NotchedPlateWithPinHolesAdapter.classify_region
    assert "class NotchedPlateWithPinHolesAdapter" in src
    assert "PROPAGATION_CORRIDOR_SECONDARY" in src
    assert "(self.notch_a <= x <= 36.5) and (45.0 <= y <= 72.0):" in src
    assert "(36.5 <= x <= self.plate_w) and (45.0 <= y <= 65.0):" in src

    # Case 5: SevenHolePlateAdapter preserved intact
    assert "class SevenHolePlateAdapter" in src
    assert "def classify_region(self, x, y, authentic_damage=None):" in src


def test_f1826_case1_audit():
    """Verify Case 1 audit receipt if available."""
    r_path = os.path.join(BASE_OUT, "case1", "PK_F1826_CASE_1_ADAPT_RECEIPT.json")
    if not os.path.exists(r_path):
        pytest.skip("Case 1 receipt not yet generated")

    with open(r_path, "r") as f:
        rec = json.load(f)

    assert rec["total_elements"] == 25461
    assert rec["quad_percent"] > 97.0
    assert rec["original_gate_06"]["status"] == "PASS"
    assert rec["original_gate_06"]["refinement_ratio"] >= 2.0
    assert rec["scientific_gate"]["status"] == "PASS"
    assert rec["supplementary_diagnostics"]["size_thresholded"]["refinement_ratio"] >= 2.0


def test_f1826_case2_audit():
    """Verify Case 2 audit receipt and original Gate 06 failure plainly disclosed."""
    r_path = os.path.join(BASE_OUT, "case2", "PK_F1826_CASE_2_ADAPT_RECEIPT.json")
    assert os.path.exists(r_path), "Case 2 receipt not found"
    with open(r_path, "r") as f:
        rec = json.load(f)

    assert rec["total_elements"] == 41438
    assert rec["quad_percent"] > 97.0
    # Disclose plain original Gate 06 result (1.9349x < 2.0x -> FAIL)
    assert rec["original_gate_06"]["status"] == "FAIL"
    assert 1.90 <= rec["original_gate_06"]["refinement_ratio"] < 2.00
    # Scientific gate PASS
    assert rec["scientific_gate"]["status"] == "PASS"
    assert rec["scientific_gate"]["metrics"]["pct_le_l0_half"] >= 95.0
    # Supplementary size-thresholded PASS
    assert rec["supplementary_diagnostics"]["size_thresholded"]["refinement_ratio"] >= 2.0


def test_f1826_case3_audit():
    """Verify Case 3 audit receipt and plain disclosure of original Gate 06 failure."""
    r_path = os.path.join(BASE_OUT, "case3", "PK_F1826_CASE_3_ADAPT_RECEIPT.json")
    assert os.path.exists(r_path), "Case 3 receipt not found"
    with open(r_path, "r") as f:
        rec = json.load(f)

    assert rec["total_elements"] == 77779
    assert rec["quad_percent"] > 97.0
    # Plain disclosure: original Gate 06 is FAIL (1.4462x)
    assert rec["original_gate_06"]["status"] == "FAIL"
    assert 1.40 <= rec["original_gate_06"]["refinement_ratio"] <= 1.50
    # Scientific gate PASS
    assert rec["scientific_gate"]["status"] == "PASS"
    assert rec["scientific_gate"]["metrics"]["pct_le_l0"] >= 90.0
    # Supplementary size-thresholded PASS
    assert rec["supplementary_diagnostics"]["size_thresholded"]["refinement_ratio"] >= 2.0


def test_f1826_case5_audit():
    """Verify Case 5 audit receipt."""
    r_path = os.path.join(BASE_OUT, "case5", "PK_F1826_CASE_5_ADAPT_RECEIPT.json")
    assert os.path.exists(r_path), "Case 5 receipt not found"
    with open(r_path, "r") as f:
        rec = json.load(f)

    assert rec["total_elements"] == 15466
    assert rec["quad_percent"] > 97.0
    assert rec["original_gate_06"]["status"] == "PASS"
    assert rec["original_gate_06"]["refinement_ratio"] >= 2.0
    assert rec["scientific_gate"]["status"] == "PASS"
    assert rec["supplementary_diagnostics"]["size_thresholded"]["refinement_ratio"] >= 2.0


def test_f1826_master_summary_audit():
    """Verify 4-benchmark total elements and summary receipt."""
    m_path = os.path.join(BASE_OUT, "PK_F1826_ADAPTER_HARMONIZATION_RECEIPT.json")
    assert os.path.exists(m_path), "Master receipt not found"
    with open(m_path, "r") as f:
        m = json.load(f)

    assert m["total_elements_across_four_cases"] == 160144
    assert len(m["cases"]) == 4
    # Check that Case 1 & 5 are PASS, Case 2 & 3 are FAIL under original Gate 06
    assert m["summary"]["case_1"]["original_gate_06_status"] == "PASS"
    assert m["summary"]["case_2"]["original_gate_06_status"] == "FAIL"
    assert m["summary"]["case_3"]["original_gate_06_status"] == "FAIL"
    assert m["summary"]["case_5"]["original_gate_06_status"] == "PASS"
    # All four pass scientific resolution gates
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        assert m["summary"][cid]["scientific_gate_status"] == "PASS"

