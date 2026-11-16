# -*- coding: utf-8 -*-
"""
tests/unit/test_f1809_multistate_sequential.py
==============================================
Unit and regression tests for Task F1809: Method A.2 Multi-State Sequential Recovery
for Case 2 Outer Distal Ligament and Case 3 Secondary Corridor across Cases 1, 2, 3, and 5.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "259_f1809_multistate_recovery"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1809_MULTISTATE_SEQUENTIAL_RECEIPT.json"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def get_body_sha(filepath):
    h = hashlib.sha256()
    with open(filepath, "r") as f:
        for line in f:
            if not line.startswith("**"):
                h.update(line.strip().encode("utf-8"))
                h.update(b"\n")
    return h.hexdigest().upper()


@pytest.fixture(scope="module")
def master_receipt():
    assert RECEIPT_PATH.exists(), f"Missing master receipt: {RECEIPT_PATH}"
    with open(RECEIPT_PATH, "r") as f:
        return json.load(f)


class TestF1809GovernanceInvariants:
    """Verifies frozen code invariants, zero new PBS submissions, and persistent master goal."""

    def test_frozen_uel_invariance(self):
        assert UEL_PATH.exists()
        assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA

    def test_frozen_framework_invariance(self):
        assert FRAMEWORK_PATH.exists()
        assert sha256_file(FRAMEWORK_PATH) == FROZEN_FRAMEWORK_SHA

    def test_pbs_and_goal_invariants(self, master_receipt):
        assert master_receipt["cumulative_pbs_submissions"] == 35
        assert master_receipt["new_pbs_submissions"] == 0
        assert master_receipt["master_goal_status"] == "OPEN"
        assert master_receipt["task_id"] == "F1809-METHOD-A2-MULTISTATE-SEQUENTIAL-RECOVERY"


class TestF1809MultiStateDonors:
    """Verifies existence, integrity, and non-empty size of synthesized multi-state recovery donors."""

    def test_case2_multistate_donor(self):
        c2_odb = BASE_OUT_DIR / "case2" / "PK_HOLE_MULTISTATE_RECOVERY.odb"
        assert c2_odb.exists()
        assert c2_odb.stat().st_size > 7000000

    def test_case3_multistate_donor(self):
        c3_odb = BASE_OUT_DIR / "case3" / "SEC43_MULTISTATE_RECOVERY.odb"
        assert c3_odb.exists()
        assert c3_odb.stat().st_size > 9000000


class TestF1809Case2OuterDistalElevation:
    """Verifies dramatic resolution elevation in Case 2 outer distal ligament under Method A.2."""

    def test_case2_resolution_and_scientific_gate(self, master_receipt):
        c2 = master_receipt["cases"]["case_2"]
        audit = c2["audit"]
        crit = c2["critical_metrics"]

        assert audit["total_elements"] == 118640
        assert audit["quad_count"] == 115712
        assert audit["tri_count"] == 2928
        assert audit["quad_percent"] >= 97.5
        assert audit["non_positive_jacobians"] == 0
        assert audit["max_aspect_ratio"] <= 3.0

        # Core scientific metric: outer ligament coverage <= l0/2
        outer_cov = crit["combined_outer_ligament_pct_le_l0_half"]
        assert outer_cov >= 99.0, f"Expected outer coverage >= 99%, got {outer_cov}%"
        assert c2["scientific_gate"] == "PASS"

        # Check bins 1 through 5
        bins = crit["bins"]
        for b_name in ["bin_1", "bin_2", "bin_3", "bin_4", "bin_5"]:
            assert bins[b_name]["pct_le_l0_half"] >= 99.0


class TestF1809Case3SecondaryCorridorElevation:
    """Verifies resolution elevation in Case 3 secondary corridor under Method A.2."""

    def test_case3_resolution_and_scientific_gate(self, master_receipt):
        c3 = master_receipt["cases"]["case_3"]
        audit = c3["audit"]
        crit = c3["critical_metrics"]

        assert audit["total_elements"] == 77779
        assert audit["quad_count"] == 75708
        assert audit["tri_count"] == 2071
        assert audit["quad_percent"] >= 97.0
        assert audit["non_positive_jacobians"] == 0
        assert audit["max_aspect_ratio"] <= 3.0

        # Core scientific metric: secondary corridor coverage <= l0
        sec_cov = crit["secondary_pct_le_l0"]
        assert sec_cov >= 90.0, f"Expected secondary coverage >= 90%, got {sec_cov}%"
        assert c3["scientific_gate"] == "PASS"


class TestF1809Case1AndCase5ZeroRegression:
    """Verifies that anchor benchmarks Case 1 and Case 5 maintain zero-regression parity."""

    def test_case1_zero_regression(self, master_receipt):
        c1 = master_receipt["cases"]["case_1"]
        audit = c1["audit"]
        crit = c1["critical_metrics"]

        assert audit["total_elements"] == 14087
        assert audit["quad_count"] == 13667
        assert audit["tri_count"] == 420
        assert audit["quad_percent"] >= 97.0
        assert audit["non_positive_jacobians"] == 0
        assert audit["max_aspect_ratio"] <= 3.0
        assert crit["tip_pct_le_l0_half"] >= 99.0
        assert all(v == "PASS" for k, v in c1["gates"].items() if k.startswith("GATE_"))

    def test_case5_zero_regression(self, master_receipt):
        c5 = master_receipt["cases"]["case_5"]
        audit = c5["audit"]
        crit = c5["critical_metrics"]

        assert audit["total_elements"] == 15466
        assert audit["quad_count"] == 15141
        assert audit["tri_count"] == 325
        assert audit["quad_percent"] >= 97.5
        assert audit["non_positive_jacobians"] == 0
        assert audit["max_aspect_ratio"] <= 2.5
        assert crit["upper_pct_le_l0"] >= 98.0
        assert all(v == "PASS" for k, v in c5["gates"].items() if k.startswith("GATE_"))


class TestF1809ArtifactsAndFigures:
    """Verifies existence and non-zero size of all generated figures and receipts."""

    def test_figures_and_synthesis_exist(self):
        fig_dir = BASE_OUT_DIR / "figures"
        assert fig_dir.exists()

        expected_figs = [
            "case_1_mesh_full.png", "case_1_h_over_l0.png", "case_1_mesh_closeup.png",
            "case_2_mesh_full.png", "case_2_h_over_l0.png", "case_2_mesh_closeup.png",
            "case_3_mesh_full.png", "case_3_h_over_l0.png", "case_3_mesh_closeup.png",
            "case_5_mesh_full.png", "case_5_h_over_l0.png", "case_5_mesh_closeup.png"
        ]
        for f in expected_figs:
            p = fig_dir / f
            assert p.exists()
            assert p.stat().st_size > 50000

        pub_png = REPO_ROOT / "results" / "figures" / "fig_f1809_four_benchmark_multistate_synthesis.png"
        pub_pdf = REPO_ROOT / "results" / "figures" / "fig_f1809_four_benchmark_multistate_synthesis.pdf"
        assert pub_png.exists()
        assert pub_png.stat().st_size > 100000
        assert pub_pdf.exists()
        assert pub_pdf.stat().st_size > 10000
