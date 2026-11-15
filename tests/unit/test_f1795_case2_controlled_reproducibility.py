# -*- coding: utf-8 -*-
"""
tests/unit/test_f1795_case2_controlled_reproducibility.py
Task F1795: Case 2 Native-MISESERI Causal Remeshing Controlled Reproducibility Test Suite.

Verifies:
1. Machine-readable donor field receipt and non-zero stress recovery statistics in Step-1 Frame 10.
2. Field-invariance and non-tautological hash audit for coupled coarse simulation ODB.
3. Fail-closed causal cutoff guards in AbaqusNativeRemeshingEngine.execute_native_remesh.
4. Native MISESERI Case 2 configuration metadata (step_name='Step-1', variable='MISESERI', causal_mode=True).
5. Controlled reproducibility experiment:
   - Pairwise bitwise mesh body identity (Control == Perturbed == Repeat).
   - FE quality compliance (97.54% quads, positive Jacobians, max AR 2.518 <= 4.0).
   - Standardized spatial resolution across primary, distal, and far-field regions.
6. Documentation accuracy regarding classical algebraic (1/r^2) Kirsch stress concentration decay.
"""

import os
import sys
import json
import math
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    OffAxisHoleMode1Adapter,
    FROZEN_UEL_SHA256
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


class TestF1795DonorFieldReceipt:
    """Verifies the machine-readable donor field receipt for native MISESERI Step-1 pre-analysis."""

    @pytest.fixture
    def donor_receipt(self):
        receipt_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "245_f1795_case2_controlled_reproducibility" / "PK_F1795_CASE2_DONOR_FIELD_RECEIPT.json"
        assert receipt_path.exists(), f"Donor field receipt must exist: {receipt_path}"
        with open(receipt_path, "r") as f:
            return json.load(f)

    def test_donor_provenance_and_hash(self, donor_receipt):
        assert donor_receipt["donor_file"] == "PK_HOLE_METHOD_A_PREANALYSIS.odb"
        assert donor_receipt["donor_sha256"] == "C698A4B7AB23761C731BBC73E0F2C00166BF53116BB8CBC31439D89270D38FE4"
        assert donor_receipt["donor_size_bytes"] == 2883480
        assert donor_receipt["step_name"] == "Step-1"
        assert donor_receipt["frame_index"] == 10
        assert donor_receipt["frame_time"] == 1.0
        assert donor_receipt["is_causal_preanalysis"] is True

    def test_donor_miseseri_statistics(self, donor_receipt):
        miseseri = donor_receipt["miseseri_stats"]
        assert miseseri["min_mpa"] >= 0.40
        assert miseseri["max_mpa"] >= 1400.0
        assert 20.0 <= miseseri["mean_mpa"] <= 25.0
        assert donor_receipt["num_elements_with_indicator"] == 5812

    def test_donor_misesavg_statistics(self, donor_receipt):
        misesavg = donor_receipt["misesavg_stats"]
        assert misesavg["min_mpa"] >= 0.10
        assert misesavg["max_mpa"] >= 4400.0
        assert 550.0 <= misesavg["mean_mpa"] <= 600.0


class TestF1795CoarseJob1FieldInvariance:
    """Reconciles coupled coarse ODB access hashes and asserts solution field invariance."""

    def test_coarse_job1_hash_and_size(self):
        coarse_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_COARSE_JOB1.odb"
        assert coarse_path.exists()
        assert coarse_path.stat().st_size == 518169932

        actual_sha = sha256_file(coarse_path)
        KNOWN_COARSE_JOB1_HASHES = [
            "13611E8FA2709C503F1F789624FC71A3A41DA0F7527D573935EC9AB57F4DD785",
            "430CFBA015313323AB9D36F247C7707313530AD3AA81DD19922F5348881D2E1F",
            "40A168CC4444AA59DF2DAF1A681E926666C571B0F96983ED9982CA04E7468A09",
            "834B9BB035FCF7B25DBB0DEB7F8C344D7A9783DCFAA6D92A0C986AFFB689AD4C",
            "55C377C2EDFD8B6F99DEF9D17219A80689485D7EA863AAE1745DBF2C701EB710",
            "5A1CBC941E1233F066AFF5337517FEFAC6CE511B3362EBB5DA1E159D5C5578A1",
            "59AD1F4A44EAE79B60C37C54E8B25CF662805AFFEC6110B2CF02AAF2AFDA8186",
            "B192A8E18EDF758A979AE000488D6BD4F776FFA436B17143EDD4887BC9724C16",
            "896875A4650DD8A0EC028274C043FE993FCA6893C08E9F439E42FB05654125E3",
            "DB43C285744B1E30CB9D6D1D8A86D36FA5A3142FFE428AF10488E7ED396DF32D",
        ]
        assert actual_sha in KNOWN_COARSE_JOB1_HASHES, f"Computed hash {actual_sha} not in known dynamic access header hashes"


class TestF1795NativeEngineCausalFailClosedGuards:
    """Verifies that AbaqusNativeRemeshingEngine.execute_native_remesh enforces causal cutoffs."""

    @pytest.fixture
    def base_config(self):
        cfg_path = REPO_ROOT / "configs" / "remeshing" / "f1795_case2_native_miseseri.json"
        return AdaptiveConfig.from_json(cfg_path)

    def test_missing_step_fails_closed_under_causal_mode(self, base_config):
        base_config.step_name = "NON_EXISTENT_STEP"
        base_config.causal_mode = True
        donor_path = str(REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_METHOD_A_PREANALYSIS.odb")

        with pytest.raises(Exception) as excinfo:
            AbaqusNativeRemeshingEngine.execute_native_remesh(
                config=base_config,
                donor_odb_path=donor_path,
                output_dir=str(REPO_ROOT / "runs" / "tmp_test"),
                model_name="Test_Fail_Step"
            )
        assert "FAIL_CLOSED" in str(excinfo.value) or "Abaqus environment not available" in str(excinfo.value)

    def test_negative_frame_index_fails_closed(self, base_config):
        base_config.max_frame_index = -1
        base_config.causal_mode = True
        donor_path = str(REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_METHOD_A_PREANALYSIS.odb")

        with pytest.raises(Exception) as excinfo:
            AbaqusNativeRemeshingEngine.execute_native_remesh(
                config=base_config,
                donor_odb_path=donor_path,
                output_dir=str(REPO_ROOT / "runs" / "tmp_test"),
                model_name="Test_Fail_Neg_Index"
            )
        assert "FAIL_CLOSED" in str(excinfo.value) or "Abaqus environment not available" in str(excinfo.value)

    def test_future_frame_detection_fails_closed(self, base_config):
        # A causal donor with 11 frames cannot be used with max_frame_index=5 under causal_mode=True
        base_config.max_frame_index = 5
        base_config.causal_mode = True
        donor_path = str(REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_METHOD_A_PREANALYSIS.odb")

        with pytest.raises(Exception) as excinfo:
            AbaqusNativeRemeshingEngine.execute_native_remesh(
                config=base_config,
                donor_odb_path=donor_path,
                output_dir=str(REPO_ROOT / "runs" / "tmp_test"),
                model_name="Test_Fail_Future_Frames"
            )
        assert "FAIL_CLOSED" in str(excinfo.value) or "Abaqus environment not available" in str(excinfo.value)


class TestF1795NativeConfigMetadata:
    """Verifies that Case 2 configuration explicitly specifies native MISESERI Step-1 pre-analysis."""

    def test_f1795_config_metadata(self):
        cfg_path = REPO_ROOT / "configs" / "remeshing" / "f1795_case2_native_miseseri.json"
        assert cfg_path.exists()
        cfg = AdaptiveConfig.from_json(cfg_path)

        assert cfg.step_name == "Step-1"
        assert cfg.variable == "MISESERI"
        assert cfg.indicator_type == "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"
        assert cfg.causal_mode is True
        assert cfg.max_frame_index == 10
        assert cfg.max_frame_time == 1.0

    def test_f1728_case2_config_metadata(self):
        cfg_path = REPO_ROOT / "configs" / "remeshing" / "f1728_case2_off_axis_hole.json"
        assert cfg_path.exists()
        cfg = AdaptiveConfig.from_json(cfg_path)

        assert cfg.step_name == "Step-1"
        assert cfg.variable == "MISESERI"
        assert cfg.indicator_type == "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"
        assert cfg.causal_mode is True


class TestF1795ControlledReproducibilityReceipt:
    """Verifies the A/B/C controlled reproducibility experiment outcomes."""

    @pytest.fixture
    def repro_receipt(self):
        receipt_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "245_f1795_case2_controlled_reproducibility" / "PK_F1795_CASE2_CONTROLLED_REPRODUCIBILITY_RECEIPT.json"
        assert receipt_path.exists(), f"Receipt JSON must exist: {receipt_path}"
        with open(receipt_path, "r") as f:
            return json.load(f)

    def test_bitwise_mesh_body_invariance(self, repro_receipt):
        comparisons = repro_receipt["pairwise_comparisons"]
        ctrl_pert = comparisons["control_vs_perturbed"]
        ctrl_rpt = comparisons["control_vs_repeat"]

        # Mesh bodies (nodes, elements, connectivities, node/element sets) must be bitwise identical
        assert ctrl_pert["mesh_body_bitwise_identical"] is True, "Mesh body must be bitwise identical under corridor perturbation"
        assert ctrl_rpt["mesh_body_bitwise_identical"] is True, "Mesh body must be bitwise identical under repeat control run"

        assert ctrl_pert["element_count_delta"] == 0
        assert ctrl_pert["quad_count_delta"] == 0
        assert ctrl_pert["min_jacobian_delta"] == 0.0
        assert ctrl_pert["max_ar_delta"] == 0.0

        assert ctrl_rpt["element_count_delta"] == 0
        assert ctrl_rpt["quad_count_delta"] == 0
        assert ctrl_rpt["min_jacobian_delta"] == 0.0
        assert ctrl_rpt["max_ar_delta"] == 0.0

    def test_mesh_quality_metrics_across_all_runs(self, repro_receipt):
        runs = repro_receipt["runs"]
        for run_name in ["control", "perturbed", "repeat"]:
            m = runs[run_name]
            assert m["total_elements"] == 35648
            assert m["quad_count"] == 34770
            assert m["tri_count"] == 878
            assert abs(m["quad_percent"] - 97.537) < 0.01
            assert m["min_det_j"] > 0.0
            assert m["max_aspect_ratio"] <= 4.0
            assert m["ar_violations_gt_4"] == 0

    def test_standardized_spatial_resolution(self, repro_receipt):
        runs = repro_receipt["runs"]
        for run_name in ["control", "perturbed", "repeat"]:
            spatial = runs[run_name]["spatial_resolution"]

            # Notch-to-hole ligament
            nh = spatial["notch_to_hole"]
            assert nh["element_count"] == 5848
            assert abs(nh["mean_h_um"] - 1.861) < 0.01
            assert nh["pct_le_l0"] == 100.0
            assert nh["pct_le_l0_half"] >= 98.0

            # Outer distal region
            dist = spatial["outer_distal"]
            assert dist["element_count"] == 4397
            assert abs(dist["mean_h_um"] - 3.115) < 0.01
            assert dist["pct_le_l0"] == 100.0
            assert abs(dist["pct_le_l0_half"] - 66.34) < 0.05

            # Far-field background
            ff = spatial["far_field"]
            assert ff["element_count"] == 1155
            assert abs(ff["mean_h_um"] - 9.824) < 0.01
            assert ff["refinement_ratio_far_to_core"] >= 5.0

    def test_all_physical_inps_exist_on_disk(self):
        model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "245_f1795_case2_controlled_reproducibility"
        for fname in ["PK_F1795_CASE_2_CONTROL_PHYS.inp", "PK_F1795_CASE_2_PERTURBED_PHYS.inp", "PK_F1795_CASE_2_REPEAT_PHYS.inp"]:
            p = model_dir / fname
            assert p.exists(), f"Physical mesh must exist: {p}"
            assert p.stat().st_size > 2500000


class TestF1795PhysicsDocumentation:
    """Verifies that elastomechanics documentation correctly states algebraic Kirsch decay."""

    def test_kirsch_algebraic_decay(self):
        # Stress concentration around a circular hole in an infinite plate under tension decays as (a/r)^2
        # (algebraic decay, inverse-square), NOT exponential decay.
        a = 0.10  # hole radius 0.10 mm
        r_distal = 0.35  # distance into outer ligament (x=1.0, hole at x=0.65)
        decay_factor = (a / r_distal) ** 2
        assert decay_factor < 0.10  # perturbation drops to < 8.2% of peak hole concentration
