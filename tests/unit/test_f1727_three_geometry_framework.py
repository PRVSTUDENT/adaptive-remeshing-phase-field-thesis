# -*- coding: utf-8 -*-
"""
tests/unit/test_f1727_three_geometry_framework.py
=================================================
Unit tests for Task F1727: Generalized Method A Adaptive Remeshing
for Three 2D Fracture Geometries (Models A, B, and C).
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    get_geometry_adapter,
    NotchedPlateWithPinHolesAdapter,
    StraightNotchMode1Adapter,
    OffAxisHoleMode1Adapter,
    MeshQualityAuditEngine,
    ProductionDeckBuilder,
    FROZEN_UEL_SHA256
)

CONFIG_PATHS = {
    "model_a": os.path.join(REPO_ROOT, "configs", "remeshing", "model_a_sec43_notched_hole_plate.json"),
    "model_b": os.path.join(REPO_ROOT, "configs", "remeshing", "model_b_sec41_mode1_edge_crack.json"),
    "model_c": os.path.join(REPO_ROOT, "configs", "remeshing", "model_c_original_off_axis_hole.json"),
}

AUDIT_PATHS = {
    "model_a": os.path.join(REPO_ROOT, "results", "validation", "f1727_model_a_mesh_audit.json"),
    "model_b": os.path.join(REPO_ROOT, "results", "validation", "f1727_model_b_mesh_audit.json"),
    "model_c": os.path.join(REPO_ROOT, "results", "validation", "f1727_model_c_mesh_audit.json"),
}

PROD_DECKS = {
    "model_a": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_A_PROD.inp"),
    "model_b": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_B_PROD.inp"),
    "model_c": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "207_f1727_three_geometry_benchmark", "PK_F1727_MODEL_C_PROD.inp"),
}


# ==============================================================================
# 1. CONFIGURATION TESTS
# ==============================================================================
def test_configurations_load_and_validate():
    """Verify all 3 configurations load, validate, and contain expected parameters."""
    for model_id, cfg_path in CONFIG_PATHS.items():
        assert os.path.exists(cfg_path), "Missing config: %s" % cfg_path
        cfg = AdaptiveConfig.from_json(cfg_path)
        assert cfg.plate_w > 0.0
        assert cfg.plate_h > 0.0
        assert cfg.E > 0.0
        assert cfg.nu > 0.0 and cfg.nu < 0.5
        assert cfg.l0 > 0.0
        assert cfg.Gc > 0.0
        assert cfg.min_h < cfg.max_h

    # Check specific model types
    cfg_a = AdaptiveConfig.from_json(CONFIG_PATHS["model_a"])
    assert cfg_a.geometry_type == "NOTCHED_PLATE_WITH_PIN_HOLES"
    assert cfg_a.loading_type == "PIN_HOLE_PULL"
    assert cfg_a.plate_w == 65.0
    assert cfg_a.plate_h == 120.0
    assert cfg_a.notch_a == 10.0

    cfg_b = AdaptiveConfig.from_json(CONFIG_PATHS["model_b"])
    assert cfg_b.geometry_type == "STRAIGHT_NOTCH_PLATE"
    assert cfg_b.loading_type == "EDGE_PULL"
    assert cfg_b.plate_w == 1.0
    assert cfg_b.plate_h == 1.0
    assert cfg_b.notch_a == 0.5

    cfg_c = AdaptiveConfig.from_json(CONFIG_PATHS["model_c"])
    assert cfg_c.geometry_type == "OFF_AXIS_HOLE_PLATE"
    assert cfg_c.loading_type == "EDGE_PULL"
    assert cfg_c.has_hole is True
    assert cfg_c.hole_x == 0.65
    assert cfg_c.hole_y == 0.65
    assert cfg_c.hole_r == 0.10


# ==============================================================================
# 2. GEOMETRY ADAPTER TESTS
# ==============================================================================
def test_geometry_adapter_dispatch_and_properties():
    """Verify adapter instantiation, containment, and region classification."""
    # Model A:
    cfg_a = AdaptiveConfig.from_json(CONFIG_PATHS["model_a"])
    adapter_a = get_geometry_adapter(cfg_a)
    assert isinstance(adapter_a, NotchedPlateWithPinHolesAdapter)
    holes_a = adapter_a.get_hole_definitions()
    assert len(holes_a) == 3
    # Check containment: interior point (50, 80) -> True; inside central hole (36.5, 51.0) -> False; inside notch slit (5.0, 70.0) -> False
    assert adapter_a.is_inside_domain(50.0, 80.0) is True
    assert adapter_a.is_inside_domain(36.5, 51.0) is False
    assert adapter_a.is_inside_domain(5.0, 70.0) is False
    assert adapter_a.is_inside_domain(20.0, 20.0) is False
    assert adapter_a.is_inside_domain(20.0, 100.0) is False
    assert adapter_a.is_inside_domain(-1.0, 50.0) is False

    # Model B:
    cfg_b = AdaptiveConfig.from_json(CONFIG_PATHS["model_b"])
    adapter_b = get_geometry_adapter(cfg_b)
    assert isinstance(adapter_b, StraightNotchMode1Adapter)
    assert adapter_b.is_inside_domain(0.8, 0.8) is True
    assert adapter_b.is_inside_domain(0.2, 0.5) is False # In notch slit
    assert adapter_b.is_inside_domain(1.5, 0.5) is False

    # Model C:
    cfg_c = AdaptiveConfig.from_json(CONFIG_PATHS["model_c"])
    adapter_c = get_geometry_adapter(cfg_c)
    assert isinstance(adapter_c, OffAxisHoleMode1Adapter)
    assert adapter_c.is_inside_domain(0.2, 0.8) is True
    assert adapter_c.is_inside_domain(0.65, 0.65) is False # Inside hole
    assert adapter_c.is_inside_domain(0.2, 0.5) is False   # Inside notch


# ==============================================================================
# 3. MESH QUALITY & SIZING AUDIT TESTS
# ==============================================================================
def test_mesh_quality_audit_results():
    """Verify 0 non-positive Jacobians, high quad fractions, and valid dual sizing metrics."""
    for model_id, audit_path in AUDIT_PATHS.items():
        assert os.path.exists(audit_path), "Missing audit JSON: %s" % audit_path
        with open(audit_path, "r") as f:
            res = json.load(f)

        assert res["total_elements"] > 0
        assert res["quad_percent"] >= 95.0, "%s quad fraction below 95%%: %.1f%%" % (model_id, res["quad_percent"])
        assert res["non_positive_jacobians"] == 0, "%s has non-positive Jacobians: %d" % (model_id, res["non_positive_jacobians"])
        assert res["min_det_j"] > 0.0, "%s min Det(J) <= 0: %.4e" % (model_id, res["min_det_j"])
        assert res["median_aspect_ratio"] < 2.0, "%s median aspect ratio high: %.2f" % (model_id, res["median_aspect_ratio"])
        assert res["min_corner_angle_deg"] > 20.0, "%s min angle too acute: %.1f deg" % (model_id, res["min_corner_angle_deg"])
        assert res["max_corner_angle_deg"] < 160.0, "%s max angle too obtuse: %.1f deg" % (model_id, res["max_corner_angle_deg"])

        # Dual sizing metrics
        assert res["h_edge_min_mm"] > 0.0
        assert res["h_edge_max_mm"] > res["h_edge_min_mm"]
        assert res["h_area_min_mm"] > 0.0
        assert res["h_area_max_mm"] > res["h_area_min_mm"]

        # Spatial selectivity (refinement concentrated in process zone)
        if "process_zone_elements" in res and "far_field_elements" in res:
            assert res["process_zone_elements"] > 0
            assert res["far_field_elements"] > 0
            assert res["process_zone_h_area_mean_mm"] < res["far_field_h_area_mean_mm"]
            assert res["refinement_ratio_mean"] > 1.2, "%s refinement ratio too low: %.2f" % (model_id, res["refinement_ratio_mean"])


# ==============================================================================
# 4. PRODUCTION 3-LAYER UEL DECK TESTS
# ==============================================================================
def test_production_decks_exist_and_format():
    """Verify 3-layer UEL production decks match f42_mixed_uel.for ABI."""
    for model_id, deck_path in PROD_DECKS.items():
        assert os.path.exists(deck_path), "Missing production deck: %s" % deck_path
        size_kb = os.path.getsize(deck_path) / 1024.0
        assert size_kb > 100.0, "%s deck suspiciously small: %.1f KB" % (model_id, size_kb)

        with open(deck_path, "r") as f:
            content = f.read()

        # Check UEL declarations
        assert "*USER ELEMENT, TYPE=U1" in content
        assert "*USER ELEMENT, TYPE=U2" in content
        assert "ELSET=PHASE_QUAD" in content
        assert "ELSET=DISP_QUAD" in content
        assert "ELSET=UMAT_QUADS" in content
        assert "ELSET=umatelem" in content
        assert "MATERIAL=DUMMY_MAT" in content
        assert "*USER MATERIAL, CONSTANTS=" in content
        assert "*EQUATION" in content
        assert "N_RP" in content

        if model_id == "model_a":
            assert "N_LOWER_HOLE" in content
            assert "N_UPPER_HOLE" in content
        else:
            assert "N_BOTTOM" in content
            assert "N_TOP" in content
            assert "N_PIN" in content


# ==============================================================================
# 5. FIGURE ARTIFACT TESTS
# ==============================================================================
def test_figure_artifacts_exist():
    """Verify all 19 figures exist in both PNG and PDF formats."""
    expected_bases = [
        "fig_model_a_1_geometry", "fig_model_a_2_coarse_mesh", "fig_model_a_3_miseseri",
        "fig_model_a_4_adapted_mesh", "fig_model_a_5_zoom", "fig_model_a_6_size_distribution",
        "fig_model_b_1_geometry", "fig_model_b_2_coarse_mesh", "fig_model_b_3_miseseri",
        "fig_model_b_4_adapted_mesh", "fig_model_b_5_zoom", "fig_model_b_6_size_distribution",
        "fig_model_c_1_geometry", "fig_model_c_2_coarse_mesh", "fig_model_c_3_miseseri",
        "fig_model_c_4_adapted_mesh", "fig_model_c_5_zoom", "fig_model_c_6_size_distribution",
        "fig_f1727_three_model_comparison"
    ]
    fig_dir = os.path.join(REPO_ROOT, "figures", "f1727_three_geometries")
    for base in expected_bases:
        png_path = os.path.join(fig_dir, base + ".png")
        pdf_path = os.path.join(fig_dir, base + ".pdf")
        assert os.path.exists(png_path), "Missing PNG: %s" % png_path
        assert os.path.exists(pdf_path), "Missing PDF: %s" % pdf_path
        assert os.path.getsize(png_path) > 10000, "PNG too small: %s" % png_path
        assert os.path.getsize(pdf_path) > 10000, "PDF too small: %s" % pdf_path
