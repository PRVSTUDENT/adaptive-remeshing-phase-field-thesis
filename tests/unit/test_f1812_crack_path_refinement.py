# -*- coding: utf-8 -*-
"""
tests/unit/test_f1812_crack_path_refinement.py
=============================================
Task F1812: Unit and regression tests for Universal Framework Crack-Path Refinement
across Cases 1, 2, 3, and 5 under the shared Pandey-Kumar Method A.2 framework.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "261_f1812_crack_path_refinement"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1812_UNIVERSAL_CRACK_PATH_REFINEMENT_RECEIPT.json"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"

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
def master_receipt():
    assert RECEIPT_PATH.exists(), "Missing master receipt: %s" % RECEIPT_PATH
    with open(RECEIPT_PATH, "r") as f:
        return json.load(f)


class TestF1812GovernanceInvariants:
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

    def test_receipt_repo_relative_paths(self, master_receipt):
        for cid, cdata in master_receipt["selected_cases"].items():
            mesh_p = cdata["physical_mesh_path"]
            donor_p = cdata["donor_path"]
            assert not mesh_p.startswith("D:"), "Mesh path must be repo-relative: %s" % mesh_p
            assert not mesh_p.startswith("C:"), "Mesh path must be repo-relative: %s" % mesh_p
            assert not donor_p.startswith("D:"), "Donor path must be repo-relative: %s" % donor_p
            assert not donor_p.startswith("C:"), "Donor path must be repo-relative: %s" % donor_p
            assert (REPO_ROOT / mesh_p).exists(), "Physical mesh not found at repo-relative path: %s" % mesh_p
            assert (REPO_ROOT / donor_p).exists(), "Donor ODB not found at repo-relative path: %s" % donor_p


class TestF1812Case1CrackPathRefinement:
    """Verifies complete full-ligament refinement along the entire propagation path for Case 1."""

    def test_case1_full_ligament_resolution(self, master_receipt):
        c1 = master_receipt["selected_cases"]["case_1"]
        crit = c1["critical_metrics"]
        assert crit["ligament_pct_le_l0"] == 100.0, "Full ligament must be 100% <= l0"
        assert crit["ligament_pct_le_l0_half"] >= 95.0, "Full ligament must be >= 95% <= l0/2"
        assert crit["outer_ligament_pct_le_l0_half"] == 100.0, "Outer ligament must be 100% <= l0/2"

    def test_case1_all_bins_resolved(self, master_receipt):
        c1 = master_receipt["selected_cases"]["case_1"]
        bins = c1["critical_metrics"]["bins"]
        for b_name, b_data in bins.items():
            assert b_data["count"] > 100, "Bin %s must contain > 100 elements" % b_name
            assert b_data["pct_le_l0"] == 100.0, "Bin %s must be 100%% <= l0" % b_name
            assert b_data["pct_le_l0_half"] >= 80.0, "Bin %s must be >= 80%% <= l0/2" % b_name
            assert b_data["min_h_um"] < 3.75, "Bin %s min h must be < l0/2 (3.75 um)" % b_name

    def test_case1_quality_gates(self, master_receipt):
        c1 = master_receipt["selected_cases"]["case_1"]
        audit = c1["audit"]
        assert audit["non_positive_jacobians"] == 0
        assert audit["quad_fraction_pct"] >= 90.0
        assert audit["max_aspect_ratio"] <= 4.0
        assert audit["total_elements"] <= 30000
        assert c1["scientific_gate"] == "PASS"


class TestF1812NonRegressionCases235:
    """Verifies that Cases 2, 3, and 5 maintain their calibrated baseline performance with zero regression."""

    def test_case2_outer_ligament_preservation(self, master_receipt):
        c2 = master_receipt["selected_cases"]["case_2"]
        crit = c2["critical_metrics"]
        assert crit["combined_outer_ligament_pct_le_l0_half"] == 100.0
        assert c2["audit"]["total_elements"] == 41438
        assert c2["scientific_gate"] == "PASS"

    def test_case3_secondary_corridor_preservation(self, master_receipt):
        c3 = master_receipt["selected_cases"]["case_3"]
        crit = c3["critical_metrics"]
        assert crit["secondary_pct_le_l0"] >= 90.0
        assert c3["audit"]["total_elements"] == 77779
        assert c3["scientific_gate"] == "PASS"

    def test_case5_inter_hole_preservation(self, master_receipt):
        c5 = master_receipt["selected_cases"]["case_5"]
        crit = c5["critical_metrics"]
        assert crit["upper_pct_le_l0"] >= 95.0
        assert c5["audit"]["total_elements"] == 15466
        assert c5["scientific_gate"] == "PASS"

    def test_zero_non_positive_jacobians_all_cases(self, master_receipt):
        for cid, cdata in master_receipt["selected_cases"].items():
            assert cdata["audit"]["non_positive_jacobians"] == 0, f"Case {cid} has non-positive Jacobians"

    def test_max_aspect_ratio_le_4_all_cases(self, master_receipt):
        for cid, cdata in master_receipt["selected_cases"].items():
            ar = cdata["audit"]["max_aspect_ratio"]
            assert ar <= 4.0, f"Case {cid} aspect ratio {ar} exceeds 4.0"


class TestF1812EvidentiaryArtifacts:
    """Verifies that all required diagnostic plots, synthesis figures, and journals exist."""

    def test_all_12_diagnostic_figures_exist(self):
        fig_dir = BASE_OUT_DIR / "figures"
        assert fig_dir.exists()
        cases = ["case_1", "case_2", "case_3", "case_5"]
        suffixes = ["_mesh_full.png", "_sizing_h_l0.png", "_mesh_closeup.png"]
        for cid in cases:
            for sfx in suffixes:
                p = fig_dir / (cid + sfx)
                assert p.exists(), "Missing diagnostic figure: %s" % p
                assert p.stat().st_size > 100000, "Figure %s is unexpectedly small" % p

    def test_publication_synthesis_figure_exists(self):
        pub_png = REPO_ROOT / "results" / "figures" / "fig_f1812_four_benchmark_crack_path_synthesis.png"
        pub_pdf = REPO_ROOT / "results" / "figures" / "fig_f1812_four_benchmark_crack_path_synthesis.pdf"
        assert pub_png.exists()
        assert pub_pdf.exists()
        assert pub_png.stat().st_size > 100000
        assert pub_pdf.stat().st_size > 10000

    def test_replay_journals_exist(self):
        cases = [
            ("case1", "PK_F1812_CASE_1_abaqus.rpy"),
            ("case2", "PK_F1812_CASE_2_abaqus.rpy"),
            ("case3", "PK_F1812_CASE_3_abaqus.rpy"),
            ("case5", "PK_F1812_CASE_5_abaqus.rpy")
        ]
        for cdir, rpy_name in cases:
            rpy_p = BASE_OUT_DIR / cdir / rpy_name
            assert rpy_p.exists(), "Missing replay journal: %s" % rpy_p
