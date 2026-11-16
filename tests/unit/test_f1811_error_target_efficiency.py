# -*- coding: utf-8 -*-
"""
tests/unit/test_f1811_error_target_efficiency.py
================================================
Unit and regression tests for Task F1811: Method A.2 Error-Target Efficiency Calibration
for Cases 2 and 3, preserving zero-regression parity on Cases 1 and 5.
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASE_OUT_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "260_f1811_error_target_calibration"
RECEIPT_PATH = BASE_OUT_DIR / "PK_F1811_ERROR_TARGET_CALIBRATION_RECEIPT.json"
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


class TestF1811GovernanceInvariants:
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


class TestF1811Case2ErrorTargetSweep:
    """Verifies the Case 2 error-target sweep, outer ligament robustness, and selected 4.0% candidate."""

    def test_case2_sweep_monotonic_element_reduction(self, master_receipt):
        sweep = master_receipt["sweeps"]["case_2"]
        targets = [item["error_target"] for item in sweep]
        counts = [item["audit"]["total_elements"] for item in sweep]
        assert targets == [2.5, 3.0, 4.0]
        # Counts must strictly decrease as error target increases
        assert counts[0] > counts[1] > counts[2]
        assert counts == [84884, 67596, 41438]

    def test_case2_all_sweep_candidates_maintain_100pct_outer_ligament(self, master_receipt):
        sweep = master_receipt["sweeps"]["case_2"]
        for item in sweep:
            crit = item["critical_metrics"]
            assert crit["combined_outer_ligament_pct_le_l0_half"] == 100.0
            assert crit["distal_pct_le_l0_half"] == 100.0
            for bin_name, bin_data in crit["bins"].items():
                assert bin_data["pct_le_l0_half"] == 100.0

    def test_case2_selected_candidate_4p0(self, master_receipt):
        c2 = master_receipt["selected_cases"]["case_2"]
        assert c2["error_target"] == 4.0
        assert c2["audit"]["total_elements"] == 41438
        # -65.1% reduction vs 118,640 F1809 baseline
        reduction_pct = (118640 - 41438) / 118640.0 * 100.0
        assert abs(reduction_pct - 65.07) < 0.1
        # Quality gates
        assert c2["audit"]["quad_percent"] >= 97.0
        assert c2["audit"]["min_signed_jacobian"] > 0
        assert c2["audit"]["max_aspect_ratio"] <= 4.0
        assert c2["audit"]["refinement_ratio_far_to_core"] >= 1.50
        assert c2["scientific_gate"] == "PASS"


class TestF1811Case3ErrorTargetSweep:
    """Verifies the Case 3 error-target sweep, Pareto boundary, and selected 3.0% candidate."""

    def test_case3_sweep_monotonic_element_reduction(self, master_receipt):
        sweep = master_receipt["sweeps"]["case_3"]
        targets = [item["error_target"] for item in sweep]
        counts = [item["audit"]["total_elements"] for item in sweep]
        assert targets == [3.0, 3.5, 4.0, 5.0, 6.0]
        assert counts[0] > counts[1] > counts[2] > counts[3] > counts[4]
        assert counts == [77779, 60521, 48584, 33048, 23275]

    def test_case3_sweep_pareto_coverage_behavior(self, master_receipt):
        sweep = master_receipt["sweeps"]["case_3"]
        coverages = [item["critical_metrics"]["secondary_pct_le_l0"] for item in sweep]
        # Coverages must strictly decrease
        assert coverages[0] > coverages[1] > coverages[2] > coverages[3] > coverages[4]
        # Only 3.0% satisfies the >= 90% scientific gate
        assert coverages[0] >= 90.0  # 93.84%
        assert coverages[1] < 90.0   # 88.83%
        assert coverages[2] < 90.0   # 80.19%
        assert coverages[3] < 90.0   # 69.59%
        assert coverages[4] < 90.0   # 57.11%

    def test_case3_selected_candidate_3p0(self, master_receipt):
        c3 = master_receipt["selected_cases"]["case_3"]
        assert c3["error_target"] == 3.0
        assert c3["audit"]["total_elements"] == 77779
        assert c3["audit"]["quad_percent"] >= 97.0
        assert c3["audit"]["min_signed_jacobian"] > 0
        assert c3["audit"]["max_aspect_ratio"] <= 4.0
        assert c3["critical_metrics"]["secondary_pct_le_l0"] >= 90.0
        assert c3["scientific_gate"] == "PASS"


class TestF1811ZeroRegressionAnchors:
    """Verifies exact zero-regression parity for Cases 1 and 5."""

    def test_case1_exact_parity(self, master_receipt):
        c1 = master_receipt["selected_cases"]["case_1"]
        assert c1["audit"]["total_elements"] == 14087
        assert c1["audit"]["quad_count"] == 13667
        assert c1["audit"]["tri_count"] == 420
        assert c1["critical_metrics"]["tip_pct_le_l0_half"] == 100.0
        assert c1["audit"]["refinement_ratio_far_to_core"] >= 2.0
        assert c1["scientific_gate"] == "PASS"

    def test_case5_exact_parity(self, master_receipt):
        c5 = master_receipt["selected_cases"]["case_5"]
        assert c5["audit"]["total_elements"] == 15466
        assert c5["audit"]["quad_count"] == 15141
        assert c5["audit"]["tri_count"] == 325
        assert c5["critical_metrics"]["upper_pct_le_l0"] >= 99.0
        assert c5["audit"]["refinement_ratio_far_to_core"] >= 2.0
        assert c5["scientific_gate"] == "PASS"


class TestF1811PhysicalMeshesAndArtifacts:
    """Verifies physical INP meshes exist on disk and have non-empty contents."""

    def test_physical_meshes_exist(self, master_receipt):
        for cid, case_data in master_receipt["selected_cases"].items():
            inp_path = Path(case_data["physical_mesh_path"])
            assert inp_path.exists(), f"Missing physical mesh for {cid}: {inp_path}"
            assert inp_path.stat().st_size > 500000

    def test_figures_exist(self):
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
            assert p.exists(), f"Missing figure: {p}"
            assert p.stat().st_size > 10000

    def test_synthesis_figure_exists(self):
        pub_dir = REPO_ROOT / "results" / "figures"
        png = pub_dir / "fig_f1811_four_benchmark_efficiency_synthesis.png"
        pdf = pub_dir / "fig_f1811_four_benchmark_efficiency_synthesis.pdf"
        assert png.exists() and png.stat().st_size > 50000
        assert pdf.exists() and pdf.stat().st_size > 10000
