# -*- coding: utf-8 -*-
"""
tests/unit/test_f1808_four_case_reproducibility.py
==================================================
Unit and regression tests for Task F1808: Four-Case Native-MISESERI
Reproducibility Investigation and Regression Audit across Cases 1, 2, 3, and 5.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "258_f1808_four_case_reproducibility"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1808_FOUR_CASE_REPRODUCIBILITY_RECEIPT.json"
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


class TestF1808GovernanceInvariants:
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
        assert master_receipt["task_id"] == "F1808-FOUR-CASE-NATIVE-MISESERI-REPRODUCIBILITY-AND-REGRESSION"


class TestF1808Case2ReproducibilityRootCause:
    """Audits and verifies the resolution of the F1806 vs F1807 Case 2 element count discrepancy."""

    def test_case2_configuration_reconciliation(self):
        cfg_1806_path = REPO_ROOT / "configs" / "remeshing" / "f1806_case2_native_miseseri.json"
        cfg_1807_path = REPO_ROOT / "configs" / "remeshing" / "f1807_case2_native_miseseri.json"
        cfg_1808_path = REPO_ROOT / "configs" / "remeshing" / "f1808_case2_native_miseseri.json"

        with open(cfg_1806_path) as f:
            c1806 = json.load(f)
        with open(cfg_1807_path) as f:
            c1807 = json.load(f)
        with open(cfg_1808_path) as f:
            c1808 = json.load(f)

        # F1806 baseline had notch_length = 0.5
        assert c1806["geometry"]["notch_length"] == 0.5
        # F1807 erroneous config had notch_length = 0.4
        assert c1807["geometry"]["notch_length"] == 0.4
        # F1808 reconciled config restores notch_length = 0.5
        assert c1808["geometry"]["notch_length"] == 0.5

    def test_case2_mesh_parity_and_bitwise_body_match(self, master_receipt):
        c2 = master_receipt["cases"]["case_2"]
        audit = c2["audit"]
        assert audit["total_elements"] == 22924
        assert audit["quad_count"] == 22346
        assert audit["tri_count"] == 578
        assert audit["quad_percent"] >= 97.4

        # Verify bitwise mesh body match against F1806 baseline
        f1806_mesh_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "256_f1806_case2_distal_1p8pct" / "PK_F1806_CASE_2_ADAPT_PHYS.inp"
        f1808_mesh_path = BASE_OUT_DIR / "case2" / "PK_F1808_CASE_2_ADAPT_PHYS.inp"

        assert f1808_mesh_path.exists()
        body_sha_1808 = get_body_sha(f1808_mesh_path)
        assert body_sha_1808 == c2["physical_mesh_body_sha256"]
        if f1806_mesh_path.exists():
            body_sha_1806 = get_body_sha(f1806_mesh_path)
            assert body_sha_1808 == body_sha_1806 == "35178C924EB5652DD57991AAD34C4CCB436D5C6F6F132E3704B7D9AFF2F1955A"


class TestF1808FourCaseMeshQualityGates:
    """Verifies that all four adapted physical meshes satisfy standard Gates 01-07."""

    def test_standard_quality_gates(self, master_receipt):
        for cid in ["case_1", "case_2", "case_3", "case_5"]:
            case_data = master_receipt["cases"][cid]
            audit = case_data["audit"]
            gates = case_data["gates"]

            # Gate 01: Zero nonpositive Jacobians
            assert audit["non_positive_jacobians"] == 0
            assert audit["min_det_j"] > 0
            assert gates["GATE_01_ZERO_NONPOSITIVE_JACOBIANS"] == "PASS"

            # Gate 02: Quad fraction >= 90%
            assert audit["quad_percent"] >= 90.0
            assert gates["GATE_02_QUAD_FRACTION_GE_90PCT"] == "PASS"

            # Gate 03: Aspect ratio <= 4.0
            assert audit["max_aspect_ratio"] <= 4.0
            assert gates["GATE_03_MAX_ASPECT_RATIO_LE_4"] == "PASS"

            # Gate 04: Corner angles in [20, 160] deg
            assert audit["min_corner_angle_deg"] >= 20.0
            assert audit["max_corner_angle_deg"] <= 160.0
            assert gates["GATE_04_CORNER_ANGLES_20_TO_160_DEG"] == "PASS"

            # Gate 06: Far-field coarsening ratio >= 2.0x
            assert audit["refinement_ratio_far_to_core"] >= 2.0
            assert gates["GATE_06_FAR_FIELD_COARSENING_GE_2X"] == "PASS"

            # Gate 07: Total elements <= 30,000
            assert audit["total_elements"] <= 30000
            assert gates["GATE_07_TOTAL_ELEMENTS_LE_30000"] == "PASS"


class TestF1808ScientificAssessments:
    """Verifies scientific evaluations, gate fails/incompleteness, and critical region metrics."""

    def test_case1_tip_resolution(self, master_receipt):
        c1 = master_receipt["cases"]["case_1"]
        crit = c1["critical_metrics"]
        assert crit["tip_pct_le_l0_half"] == 100.0
        assert c1["scientific_gate"] == "PASS"

    def test_case2_distal_and_outer_gate_retention(self, master_receipt):
        c2 = master_receipt["cases"]["case_2"]
        crit = c2["critical_metrics"]
        assert crit["distal_pct_le_l0_half"] >= 89.0
        # Combined outer ligament is 28.02% < 50.0% threshold -> Scientific Gate is strictly FAIL
        assert crit["combined_outer_ligament_pct_le_l0_half"] < 50.0
        assert c2["scientific_gate"] == "FAIL"
        assert c2["gates"]["SCIENTIFIC_GATE_OUTER_DISTAL"] == "FAIL"

    def test_case3_secondary_corridor_evaluation(self, master_receipt):
        c3 = master_receipt["cases"]["case_3"]
        crit = c3["critical_metrics"]
        # Secondary corridor is partially resolved (58.32% <= l0) but incomplete (< 90%)
        assert 50.0 <= crit["secondary_pct_le_l0"] < 90.0
        assert crit["secondary_min_h_mm"] < 0.285 / 2.0  # local h_min < l0/2
        assert c3["scientific_gate"] == "INCOMPLETE_RESOLUTION"
        assert c3["gates"]["SCIENTIFIC_GATE_SECONDARY_CORRIDOR"] == "INCOMPLETE_RESOLUTION"

    def test_case5_inter_hole_resolution(self, master_receipt):
        c5 = master_receipt["cases"]["case_5"]
        crit = c5["critical_metrics"]
        assert crit["upper_pct_le_l0"] >= 98.0
        assert crit["lower_pct_le_l0"] >= 90.0
        assert c5["scientific_gate"] == "PASS"


class TestF1808InspectableArtifacts:
    """Verifies that all physical meshes, execution journals, and diagnostic figures exist."""

    def test_all_physical_meshes_exist(self):
        for cid, num in [("case1", 1), ("case2", 2), ("case3", 3), ("case5", 5)]:
            inp = BASE_OUT_DIR / cid / f"PK_F1808_CASE_{num}_ADAPT_PHYS.inp"
            assert inp.exists(), f"Missing physical mesh: {inp}"
            assert inp.stat().st_size > 500000

    def test_all_journals_exist(self):
        for cid, num in [("case1", 1), ("case2", 2), ("case3", 3), ("case5", 5)]:
            rpy = BASE_OUT_DIR / cid / f"case_{num}_abaqus.rpy"
            assert rpy.exists(), f"Missing journal: {rpy}"

    def test_all_diagnostic_figures_exist(self):
        fig_dir = BASE_OUT_DIR / "figures"
        assert fig_dir.exists()
        for cid in ["case_1", "case_2", "case_3", "case_5"]:
            assert (fig_dir / f"{cid}_mesh_full.png").exists()
            assert (fig_dir / f"{cid}_h_over_l0.png").exists()
            assert (fig_dir / f"{cid}_mesh_closeup.png").exists()

        pub_png = REPO_ROOT / "results" / "figures" / "fig_f1808_four_benchmark_regression_synthesis.png"
        pub_pdf = REPO_ROOT / "results" / "figures" / "fig_f1808_four_benchmark_regression_synthesis.pdf"
        assert pub_png.exists()
        assert pub_pdf.exists()
