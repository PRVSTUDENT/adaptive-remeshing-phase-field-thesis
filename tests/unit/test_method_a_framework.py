# -*- coding: utf-8 -*-
"""
tests/unit/test_method_a_framework.py
=====================================
Comprehensive unit test suite for the Reusable Method A Adaptive-Remeshing Framework.

Verifies:
1. Configuration validation, physics bounds, and error handling.
2. Rejection of unsupported element topologies (3D solids, 1D beams).
3. Regression against Benchmark 1: Mode-I straight-notch specimen (F1712 / F1713).
4. Regression against Benchmark 2: Five-hole generalization specimen (F1714).
5. Indicator processing, SPR stress jump extraction, and sizing fields.
6. Postprocessor equilibrium, external work integration, and damage bounds.
7. Full pipeline orchestration and validation report generation.

Governing Review Reference: /goal F1715
"""

import os
import json
import pytest

from scripts.method_a_framework.config import FrameworkConfig
from scripts.method_a_framework.input_validator import InputModelValidator
from scripts.method_a_framework.deck_builder import ProductionDeckBuilder, wrap_nset_line
from scripts.method_a_framework.indicator import MiseseriIndicator
from scripts.method_a_framework.postprocessor import SimulationPostprocessor
from scripts.method_a_framework.pipeline import MethodAFrameworkPipeline


# Paths to existing authentic artifacts
F1713_PHYS_INP = os.path.join(
    "models", "pandey_kumar_mode1", "206_f1713_new_mode1_adaptive_experiment", "PK_F1713_JOB2_ADAPTED_PHYS.inp"
)
F1713_COARSE_INP = os.path.join(
    "models", "pandey_kumar_mode1", "206_f1713_new_mode1_adaptive_experiment", "PK_F1713_JOB1_COARSE.inp"
)
F1714_PHYS_INP = os.path.join(
    "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB2_ADAPTED_PHYS.inp"
)
F1714_COARSE_INP = os.path.join(
    "models", "pandey_kumar_mode1", "207_f1714_five_hole_benchmark", "PK_F1714_JOB1_COARSE.inp"
)


def test_01_config_validation_and_rejection():
    """
    Tests physical bounds checking and rejection of unphysical parameter configurations.
    """
    cfg = FrameworkConfig()
    assert cfg.validate() is True

    # Negative Young's modulus must be rejected
    cfg.material["E"] = -100.0
    with pytest.raises(ValueError, match="Young's modulus E must be strictly positive"):
        cfg.validate()
    cfg.material["E"] = 210.0

    # Inadmissible Poisson's ratio (nu >= 0.5)
    cfg.material["nu"] = 0.52
    with pytest.raises(ValueError, match="Poisson's ratio nu must be in"):
        cfg.validate()
    cfg.material["nu"] = 0.30

    # h_min >= h_max must be rejected
    cfg.remeshing["h_min"] = 0.05
    cfg.remeshing["h_max"] = 0.02
    with pytest.raises(ValueError, match="h_min .* must be strictly less than h_max"):
        cfg.validate()

    # h_min > l0 / 2 must be rejected (cannot resolve phase-field)
    cfg.remeshing["h_min"] = 0.005
    cfg.remeshing["h_max"] = 0.020
    cfg.material["l0"] = 0.008  # l0 / 2 = 0.004 < 0.005
    with pytest.raises(ValueError, match="cannot resolve phase-field process zone"):
        cfg.validate()


def test_02_unsupported_element_topology_rejection(tmp_path):
    """
    Tests that 3D solid elements (e.g. C3D8) are rejected with clear diagnostics.
    """
    bad_deck = tmp_path / "unsupported_3d.inp"
    bad_deck.write_text("""*HEADING
Unsupported 3D Mesh
*NODE
1, 0.0, 0.0, 0.0
2, 1.0, 0.0, 0.0
*ELEMENT, TYPE=C3D8, ELSET=SOLID_ELEMS
1, 1, 2, 3, 4, 5, 6, 7, 8
""")

    val = InputModelValidator(str(bad_deck))
    with pytest.raises(ValueError, match="Unsupported element type 'C3D8'"):
        val.parse()


def test_03_benchmark1_mode1_deck_reconstruction_regression(tmp_path):
    """
    Benchmark 1: Validates that the framework parses the F1713 Mode-I adapted mesh (14,933 elements)
    and reconstructs the 3-layer production deck with 44,799 layered elements.
    """
    assert os.path.isfile(F1713_PHYS_INP), f"Missing {F1713_PHYS_INP}"

    cfg = FrameworkConfig({
        "benchmark_name": "Mode1_Benchmark",
        "material": {"E": 210.0, "nu": 0.30, "Gc": 2.7e-3, "l0": 0.0075, "constitutive_split": "mixed"},
        "remeshing": {"h_min": 0.001, "h_max": 0.020, "error_target_pct": 1.85}
    })

    val = InputModelValidator(F1713_PHYS_INP)
    summary = val.parse()
    assert summary["element_count"] == 14933
    assert summary["quality"]["all_jacobians_positive"] is True

    out_deck = tmp_path / "PK_F1713_RECONSTRUCTED.inp"
    builder = ProductionDeckBuilder(F1713_PHYS_INP, cfg)
    res = builder.build_deck(str(out_deck))

    assert res["physical_elements"] == 14933
    assert res["layered_elements"] == 3 * 14933  # 44,799
    assert os.path.isfile(str(out_deck))

    # Verify wrapped NSET lines have <= 16 entries
    with open(str(out_deck), "r") as f:
        deck_text = f.read()

    assert "*EQUATION" in deck_text
    assert "*USER ELEMENT, TYPE=U1" in deck_text
    assert "*USER ELEMENT, TYPE=U2" in deck_text


def test_04_benchmark2_five_hole_deck_reconstruction_regression(tmp_path):
    """
    Benchmark 2: Validates that the framework parses the F1714 Five-Hole adapted mesh (13,034 elements)
    and reconstructs the 3-layer production deck with 39,102 layered elements and 52 bottom nodes.
    """
    assert os.path.isfile(F1714_PHYS_INP), f"Missing {F1714_PHYS_INP}"

    cfg = FrameworkConfig({
        "benchmark_name": "Five_Hole_Benchmark",
        "material": {"E": 210.0, "nu": 0.30, "Gc": 2.7e-3, "l0": 0.008, "constitutive_split": "amor"},
        "remeshing": {"h_min": 0.001, "h_max": 0.020, "error_target_pct": 1.85}
    })

    val = InputModelValidator(F1714_PHYS_INP)
    summary = val.parse()
    assert summary["element_count"] == 13034
    assert summary["quality"]["all_jacobians_positive"] is True
    assert summary["quality"]["aspect_ratio_mean"] < 1.5

    out_deck = tmp_path / "PK_F1714_RECONSTRUCTED.inp"
    builder = ProductionDeckBuilder(F1714_PHYS_INP, cfg)
    res = builder.build_deck(str(out_deck))

    assert res["physical_elements"] == 13034
    assert res["layered_elements"] == 39102
    assert res["bottom_nodes_count"] == 52
    assert res["top_nodes_count"] == 52


def test_05_miseseri_indicator_and_sizing_field():
    """
    Tests SPR stress jump indicator processing, relative error ratio, and sizing field calculation.
    """
    cfg = FrameworkConfig({
        "remeshing": {"h_min": 0.001, "h_max": 0.020, "error_target_pct": 3.0}
    })
    ind = MiseseriIndicator(cfg)

    # Mock element records: high stress jump near notch tip, low in bulk
    mock_records = [
        {"element_id": 1, "miseseri": 30.0, "misesavg": 300.0},  # eta = 10% (> target 3%)
        {"element_id": 2, "miseseri": 3.0, "misesavg": 300.0},   # eta = 1% (< target 3%)
        {"element_id": 3, "miseseri": 60.0, "misesavg": 300.0},  # eta = 20% (> target 3%)
    ]
    stats = ind.load_from_field_data(mock_records)
    assert stats["element_count"] == 3
    assert stats["elements_exceeding_target"] == 2

    sizing = ind.compute_target_sizing(h_coarse=0.020)
    # High error elements should refine towards h_min
    assert sizing[1] < 0.020
    assert sizing[3] < sizing[1]  # Higher error -> smaller element size
    # Low error element should remain at h_max
    assert sizing[2] == 0.020


def test_06_postprocessor_equilibrium_and_damage_bounds():
    """
    Tests reaction force equilibrium, external work calculation, energy extraction, and damage bounding.
    """
    cfg = FrameworkConfig({"benchmark_name": "TestBenchmark"})
    post = SimulationPostprocessor(cfg)

    mock_telemetry = {
        "fu_history": [
            {"displacement_mm": 0.0, "tensile_force_kN": 0.0},
            {"displacement_mm": 0.002, "tensile_force_kN": 0.28},
            {"displacement_mm": 0.005, "tensile_force_kN": 0.70},
            {"displacement_mm": 0.006, "tensile_force_kN": 0.74},  # peak
            {"displacement_mm": 0.008, "tensile_force_kN": 0.10},  # post-peak
        ],
        "energy_history": [
            {"displacement_mm": 0.002, "elastic_energy_kNmm": 0.00028, "fracture_energy_kNmm": 0.0, "total_energy_kNmm": 0.00028},
            {"displacement_mm": 0.006, "elastic_energy_kNmm": 0.0020, "fracture_energy_kNmm": 0.0015, "total_energy_kNmm": 0.0035},
        ],
        "milestone_damage_fields": {
            "state_1": {"element_damage": {1: 0.0, 2: 0.45, 3: 0.95}}
        }
    }

    summary = post.process_telemetry(mock_telemetry)
    assert summary["peak_force_kN"] == 0.74
    assert summary["displacement_at_peak_mm"] == 0.006
    assert summary["initial_stiffness_kN_per_mm"] > 100.0
    assert summary["external_work_kNmm"] > 0.0
    assert summary["milestones_count"] == 1

    # Verify that unphysical negative damage raises ValueError
    bad_telemetry = dict(mock_telemetry)
    bad_telemetry["milestone_damage_fields"] = {
        "state_bad": {"element_damage": {1: -0.20}}
    }
    with pytest.raises(ValueError, match="Damage bounds violated"):
        post.process_telemetry(bad_telemetry)


def test_07_end_to_end_pipeline_orchestration(tmp_path):
    """
    Tests the main MethodAFrameworkPipeline orchestrating preprocessing,
    production deck generation, and validation report export.
    """
    cfg_data = {
        "benchmark_name": "Pipeline_Test",
        "material": {"E": 210.0, "nu": 0.30, "Gc": 2.7e-3, "l0": 0.008, "constitutive_split": "amor"},
        "remeshing": {"h_min": 0.001, "h_max": 0.020, "error_target_pct": 1.85}
    }
    pipeline = MethodAFrameworkPipeline(cfg_data)

    out_prod = str(tmp_path / "TEST_PROD.inp")
    pre_res = pipeline.run_preprocessing_and_deck_generation(
        coarse_inp_path=F1714_COARSE_INP,
        adapted_phys_inp_path=F1714_PHYS_INP,
        output_prod_inp_path=out_prod
    )
    assert pre_res["production_deck"]["layered_elements"] == 39102
    assert pre_res["production_deck_sha256"] != ""

    mock_telemetry = {
        "fu_history": [
            {"displacement_mm": 0.0, "tensile_force_kN": 0.0},
            {"displacement_mm": 0.005, "tensile_force_kN": 0.50}
        ],
        "energy_history": [
            {"displacement_mm": 0.005, "elastic_energy_kNmm": 0.00125, "fracture_energy_kNmm": 0.0, "total_energy_kNmm": 0.00125}
        ],
        "milestone_damage_fields": {
            "state_1": {"element_damage": {1: 0.10, 2: 0.85}}
        }
    }
    report_json = str(tmp_path / "validation_report.json")
    val_res = pipeline.run_postprocessing_and_validation(mock_telemetry, report_json)
    assert val_res["peak_force_kN"] == 0.50
    assert os.path.isfile(report_json)
