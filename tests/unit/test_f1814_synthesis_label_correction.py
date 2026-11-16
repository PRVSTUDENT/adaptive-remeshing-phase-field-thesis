# -*- coding: utf-8 -*-
"""
tests/unit/test_f1814_synthesis_label_correction.py
==================================================
Task F1814: Unit and regression tests verifying the two synthesis labeling corrections
carried from the independent supervisory review of Task F1813:
1. Case 1 campaign progression gate_status and crit_desc reconciliation.
2. Case 1 progression chart coverage series consistency (full-ligament series).
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "262_f1813_unified_synthesis"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1813_UNIFIED_SYNTHESIS_RECEIPT.json"
PROGRESSION_PATH = BASE_OUT_DIR / "campaign_progression_summary.json"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
REPORT_PATH = REPO_ROOT / "docs" / "validation" / "F1814_SYNTHESIS_LABEL_CORRECTION_REPORT.md"

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "4276A5DC1AF22A6A117102D8C24492789E8AA4EBFD4AF079C58EE86DBEEC7C8B"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


@pytest.fixture(scope="module")
def progression_summary():
    assert PROGRESSION_PATH.exists(), "Missing progression summary: %s" % PROGRESSION_PATH
    with open(PROGRESSION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def master_receipt():
    assert RECEIPT_PATH.exists(), "Missing master receipt: %s" % RECEIPT_PATH
    with open(RECEIPT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class TestF1814GovernanceInvariants:
    """Verifies frozen code invariants, zero new PBS submissions, and persistent master goal."""

    def test_frozen_uel_invariance(self):
        assert UEL_PATH.exists()
        assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA

    def test_frozen_framework_invariance(self):
        assert FRAMEWORK_PATH.exists()
        assert sha256_file(FRAMEWORK_PATH) == FROZEN_FRAMEWORK_SHA

    def test_cumulative_pbs_submissions_preserved(self, master_receipt):
        assert master_receipt["cumulative_pbs_submissions"] == 35
        assert master_receipt["new_pbs_submissions"] == 0

    def test_master_goal_status_open(self, master_receipt):
        assert master_receipt["master_goal_status"] == "OPEN"


class TestF1814Case1ProgressionLabelCorrection:
    """Verifies that Case 1 progression gate_status and crit_desc are correctly reconciled."""

    def test_case1_f1808_incomplete(self, progression_summary):
        f1808 = progression_summary["case_1"][0]
        assert f1808["task"] == "F1808"
        assert f1808["gate_status"] == "INCOMPLETE"
        assert "79.8%" in f1808["crit_desc"]
        assert "Incomplete" in f1808["crit_desc"]

    def test_case1_f1809_incomplete(self, progression_summary):
        f1809 = progression_summary["case_1"][1]
        assert f1809["task"] == "F1809"
        assert f1809["gate_status"] == "INCOMPLETE"
        assert "79.8%" in f1809["crit_desc"]
        assert "Incomplete" in f1809["crit_desc"]

    def test_case1_f1811_incomplete_with_tip_note(self, progression_summary):
        f1811 = progression_summary["case_1"][2]
        assert f1811["task"] == "F1811"
        assert f1811["gate_status"] == "INCOMPLETE"
        assert "100.0%" in f1811["crit_desc"]
        assert "tip" in f1811["crit_desc"].lower()
        assert "Distal 0.0%" in f1811["crit_desc"]

    def test_case1_f1812_pass(self, progression_summary):
        f1812 = progression_summary["case_1"][3]
        assert f1812["task"] == "F1812"
        assert f1812["gate_status"] == "PASS"
        assert "97.2%" in f1812["crit_desc"]


class TestF1814ProgressionFigureConsistency:
    """Verifies that the progression figure is updated with matching hashes and sizes."""

    def test_progression_figures_exist_and_hashes_match(self, master_receipt):
        fig_png = REPO_ROOT / master_receipt["published_figures"]["fig_progression_png"]["relative_path"]
        fig_pdf = REPO_ROOT / master_receipt["published_figures"]["fig_progression_pdf"]["relative_path"]
        assert fig_png.exists()
        assert fig_pdf.exists()
        assert sha256_file(fig_png) == master_receipt["published_figures"]["fig_progression_png"]["sha256"]
        assert sha256_file(fig_pdf) == master_receipt["published_figures"]["fig_progression_pdf"]["sha256"]

    def test_unified_synthesis_figures_exist_and_hashes_match(self, master_receipt):
        fig_png = REPO_ROOT / master_receipt["published_figures"]["fig_unified_synthesis_png"]["relative_path"]
        fig_pdf = REPO_ROOT / master_receipt["published_figures"]["fig_unified_synthesis_pdf"]["relative_path"]
        assert fig_png.exists()
        assert fig_pdf.exists()
        assert sha256_file(fig_png) == master_receipt["published_figures"]["fig_unified_synthesis_png"]["sha256"]
        assert sha256_file(fig_pdf) == master_receipt["published_figures"]["fig_unified_synthesis_pdf"]["sha256"]


class TestF1814ReportDocumentation:
    """Verifies that the F1814 report exists and documents the labeling corrections."""

    def test_f1814_report_exists_and_content(self):
        assert REPORT_PATH.exists()
        content = REPORT_PATH.read_text(encoding="utf-8")
        assert "F1814" in content
        assert "Full Ligament Coverage" in content
        assert "79.8%" in content
        assert "97.19%" in content
