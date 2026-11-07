# -*- coding: utf-8 -*-
"""
tests/unit/test_reusable_2d_adaptive_framework.py
=================================================
Unit and regression tests for the reusable 2D adaptive remeshing framework
(Task F1665, mandated by ChatGPT review HND-e7c597c4a8ee).
"""

import os
import tempfile
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
import sys
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    StraightNotchMode1Adapter,
    OffAxisHoleMode1Adapter,
    get_geometry_adapter,
    MeshQualityAuditEngine,
    ProductionDeckBuilder,
    FROZEN_UEL_SHA256
)


@pytest.fixture
def straight_notch_config():
    cfg_path = REPO_ROOT / "configs" / "remeshing" / "mode1_straight_notch_benchmark.json"
    return AdaptiveConfig.from_json(str(cfg_path))


@pytest.fixture
def off_axis_hole_config():
    cfg_path = REPO_ROOT / "configs" / "remeshing" / "mode1_off_axis_hole_benchmark.json"
    return AdaptiveConfig.from_json(str(cfg_path))


def test_straight_notch_config_validation(straight_notch_config):
    cfg = straight_notch_config
    assert cfg.benchmark_name == "Mode-I Straight Notch Standard PFM"
    assert cfg.geometry_type == "STRAIGHT_NOTCH_PLATE"
    assert cfg.plate_w == 1.0
    assert cfg.plate_h == 1.0
    assert cfg.notch_a == 0.5
    assert not cfg.has_hole
    assert cfg.error_target == 5.0
    assert cfg.min_h == 0.0015
    assert cfg.max_h == 0.020


def test_off_axis_hole_config_validation(off_axis_hole_config):
    cfg = off_axis_hole_config
    assert cfg.benchmark_name == "Mode-I Off-Axis Circular Hole Benchmark"
    assert cfg.geometry_type == "OFF_AXIS_HOLE_PLATE"
    assert cfg.plate_w == 1.0
    assert cfg.plate_h == 1.0
    assert cfg.notch_a == 0.5
    assert cfg.has_hole
    assert cfg.hole_x == 0.65
    assert cfg.hole_y == 0.65
    assert cfg.hole_r == 0.10
    assert cfg.error_target == 5.0


def test_invalid_config_rejection():
    # Negative dimension
    with pytest.raises(ValueError, match="Plate dimensions"):
        AdaptiveConfig({"geometry": {"plate_width": -1.0, "plate_height": 1.0}})

    # Notch too long
    with pytest.raises(ValueError, match="Notch length"):
        AdaptiveConfig({"geometry": {"plate_width": 1.0, "plate_height": 1.0, "notch_length": 1.5}})

    # Missing hole parameters
    with pytest.raises(ValueError, match="Hole coordinates and radius"):
        AdaptiveConfig({
            "geometry": {"plate_width": 1.0, "plate_height": 1.0, "notch_length": 0.5, "has_hole": True}
        })

    # Ambiguous fractional error target
    with pytest.raises(ValueError, match="ambiguous"):
        AdaptiveConfig({
            "geometry": {"plate_width": 1.0, "plate_height": 1.0, "notch_length": 0.5},
            "remeshing_rule": {"error_target": 0.05}
        })


def test_straight_notch_geometry_adapter(straight_notch_config):
    adapter = get_geometry_adapter(straight_notch_config)
    assert isinstance(adapter, StraightNotchMode1Adapter)
    pts = adapter.get_outer_polygon_points()
    assert len(pts) == 8
    assert len(adapter.get_hole_definitions()) == 0

    # Inside domain
    assert adapter.is_inside_domain(0.8, 0.5)
    assert adapter.is_inside_domain(0.2, 0.8)

    # Outside domain
    assert not adapter.is_inside_domain(1.2, 0.5)
    assert not adapter.is_inside_domain(0.2, -0.1)

    # Inside notch slit
    assert not adapter.is_inside_domain(0.25, 0.50)


def test_off_axis_hole_geometry_adapter(off_axis_hole_config):
    adapter = get_geometry_adapter(off_axis_hole_config)
    assert isinstance(adapter, OffAxisHoleMode1Adapter)
    holes = adapter.get_hole_definitions()
    assert len(holes) == 1
    assert holes[0] == (0.65, 0.65, 0.10)

    # Inside plate domain
    assert adapter.is_inside_domain(0.2, 0.2)
    assert adapter.is_inside_domain(0.8, 0.2)

    # Inside circular hole (should return False)
    assert not adapter.is_inside_domain(0.65, 0.65)
    assert not adapter.is_inside_domain(0.65 + 0.05, 0.65)

    # Outside plate
    assert not adapter.is_inside_domain(-0.1, 0.5)

    # Inside notch slit
    assert not adapter.is_inside_domain(0.3, 0.5)


def test_frozen_uel_integrity():
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for not found"
    assert ProductionDeckBuilder.verify_uel_subroutine(str(uel_path), FROZEN_UEL_SHA256)

    # Rejection of tampered hash
    with pytest.raises(ValueError, match="integrity violation"):
        ProductionDeckBuilder.verify_uel_subroutine(str(uel_path), "0000000000000000000000000000000000000000000000000000000000000000")


def test_f1664_physical_mesh_quality():
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    assert inp_path.exists(), "Physical adapted mesh not found"

    metrics = MeshQualityAuditEngine.evaluate_mesh(str(inp_path), l0_mm=0.0075)
    assert metrics["total_elements"] == 20213
    assert metrics["total_nodes"] == 20213
    assert metrics["quad_count"] == 19644
    assert metrics["tri_count"] == 569
    assert metrics["quad_percent"] > 97.0

    # Strict FE quality gates
    assert metrics["non_positive_jacobians"] == 0, "Non-positive Jacobians detected!"
    assert metrics["min_det_j"] > 0.0
    assert metrics["distorted_elements"] == 0, "Distorted elements detected!"
    assert metrics["min_corner_angle_deg"] > 30.0
    assert metrics["median_aspect_ratio"] < 1.30

    # Resolution
    assert metrics["h_min_um"] < 1.0  # Sub-micron element size
    assert metrics["h_median_um"] < 4.0
    assert metrics["elements_le_3p75um"] >= 9000  # Elements satisfying l0/2


def test_f1664_3layer_uel_deck_verification(off_axis_hole_config):
    phys_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    prod_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1664_METHOD_A_PROD.inp"

    res = ProductionDeckBuilder.build_deck(
        str(phys_inp), str(prod_inp), "PK_HOLE_F1664_METHOD_A_PROD", off_axis_hole_config
    )
    assert res["total_physical_elements"] == 20213
    assert res["total_layered_elements"] == 60639
    assert res["total_nodes"] == 20214
    assert res["uel_hash_verified"]

    # Verify content lines of production deck
    with open(str(prod_inp), "r") as f:
        content = f.read()

    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*USER ELEMENT, TYPE=U3" in content
    assert "*USER ELEMENT, TYPE=U4" in content
    assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in content
    assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in content
    assert "*EQUATION" in content
    assert "N_BOTTOM, 2, 2" in content
    assert "N_PIN, 1, 1" in content
    assert "N_RP, 2, 2" in content
