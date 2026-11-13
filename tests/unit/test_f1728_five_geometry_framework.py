# -*- coding: utf-8 -*-
"""
tests/unit/test_f1728_five_geometry_framework.py
=================================================
Automated Unit Regression Suite for Task F1728:
Unified Physics-Driven Method A Adaptive Remeshing — Five-Geometry Verification.

Validates:
1. Standardized JSON configuration loading and schema validation across all 5 cases.
2. Geometry adapter factory dispatch and topological feature queries (Case 1 to 5).
3. Domain containment and void exclusion logic (is_inside_domain).
4. Boundary condition specification and dispatch (EDGE_PULL vs. PIN_HOLE_PULL).
5. Standalone Finite-Element Mesh Quality Audit on physical meshes.
6. 3-Layer UEL Production Deck Builder (layers, equations, dummy modulus scaling).
7. Remeshing rule parameter integrity and constraints.
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
    StraightNotchMode1Adapter,
    OffAxisHoleMode1Adapter,
    NotchedPlateWithPinHolesAdapter,
    FiveHolePlateAdapter,
    SevenHolePlateAdapter,
    MultiHolePlateAdapter,
    MeshQualityAuditEngine,
    ProductionDeckBuilder,
    FROZEN_UEL_SHA256
)

CONFIG_FILES = {
    "case_1": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case1_mode1_edge_crack.json"),
    "case_2": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json"),
    "case_3": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json"),
    "case_4": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case4_five_hole.json"),
    "case_5": os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json"),
}


# ==============================================================================
# 1. CONFIGURATION LOADING AND SCHEMA TESTS
# ==============================================================================

def test_f1728_all_five_configurations_load():
    """Verify all 5 JSON benchmark configurations load and validate cleanly."""
    for case_key, cfg_path in CONFIG_FILES.items():
        assert os.path.exists(cfg_path), "Missing config file: %s" % cfg_path
        cfg = AdaptiveConfig.from_json(cfg_path)

        assert cfg.case_id == case_key, "case_id mismatch in %s: %s" % (cfg_path, cfg.case_id)
        assert cfg.benchmark_name is not None and len(cfg.benchmark_name) > 0
        assert cfg.geometry_type is not None
        assert cfg.l0 > 0.0
        assert cfg.width > 0.0
        assert cfg.height > 0.0
        assert cfg.thickness > 0.0
        assert cfg.E > 0.0
        assert 0.0 < cfg.nu < 0.5
        assert cfg.Gc > 0.0
        assert cfg.error_target > 0.0
        assert cfg.min_h > 0.0
        assert cfg.max_h >= cfg.min_h
        assert cfg.bc_type in ("EDGE_PULL", "PIN_HOLE_PULL")


# ==============================================================================
# 2. GEOMETRY ADAPTER FACTORY AND DISPATCH TESTS
# ==============================================================================

def test_f1728_adapter_dispatch():
    """Verify that get_geometry_adapter dispatches the correct adapter class for each case."""
    expected_classes = {
        "case_1": StraightNotchMode1Adapter,
        "case_2": OffAxisHoleMode1Adapter,
        "case_3": NotchedPlateWithPinHolesAdapter,
        "case_4": FiveHolePlateAdapter,
        "case_5": SevenHolePlateAdapter,
    }

    for case_key, exp_cls in expected_classes.items():
        cfg = AdaptiveConfig.from_json(CONFIG_FILES[case_key])
        adapter = get_geometry_adapter(cfg)
        assert isinstance(adapter, exp_cls), (
            "Expected %s for %s, got %s" % (exp_cls.__name__, case_key, type(adapter).__name__)
        )


# ==============================================================================
# 3. TOPOLOGY AND DOMAIN CONTAINMENT TESTS
# ==============================================================================

def test_f1728_case1_straight_notch_adapter():
    """Verify Case 1 (Straight Notch Mode-I) topology and containment."""
    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_1"])
    adapter = StraightNotchMode1Adapter(cfg)

    # Domain: [0, 1.0] x [0, 1.0]
    assert adapter.is_inside_domain(0.5, 0.2) is True
    assert adapter.is_inside_domain(0.8, 0.8) is True
    assert adapter.is_inside_domain(-0.1, 0.5) is False
    assert adapter.is_inside_domain(1.1, 0.5) is False

    # Check holes (Case 1 has no holes)
    assert len(adapter.get_hole_definitions()) == 0

    # Crack seam: y=0.5, 0 <= x <= 0.5 (8 vertices enclosing domain with slit)
    poly = adapter.get_outer_polygon_points()
    assert len(poly) == 8


def test_f1728_case2_off_axis_hole_adapter():
    """Verify Case 2 (Off-Axis Hole Mode-I) topology and containment."""
    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_2"])
    adapter = OffAxisHoleMode1Adapter(cfg)

    # Domain: [0, 1.0] x [0, 1.0], Hole at (0.65, 0.65), R=0.10
    assert adapter.is_inside_domain(0.2, 0.2) is True
    assert adapter.is_inside_domain(0.65, 0.65) is False  # Center of hole is excluded
    assert adapter.is_inside_domain(0.66, 0.66) is False  # Inside hole
    assert adapter.is_inside_domain(0.9, 0.9) is True

    holes = adapter.get_hole_definitions()
    assert len(holes) == 1
    # Each hole is a tuple: (hx, hy, hr)
    assert abs(holes[0][0] - 0.65) < 1e-4
    assert abs(holes[0][1] - 0.65) < 1e-4
    assert abs(holes[0][2] - 0.10) < 1e-4


def test_f1728_case3_notched_plate_pins_adapter():
    """Verify Case 3 (Notched Plate with Central Hole and Pins) topology and containment."""
    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_3"])
    adapter = NotchedPlateWithPinHolesAdapter(cfg)

    # Domain: [0, 65] x [0, 120]
    # Center hole: (36.5, 51.0), R=10.0
    # Pin 1: (20.0, 100.0), R=5.0
    # Pin 2: (20.0, 20.0), R=5.0
    assert adapter.is_inside_domain(10.0, 50.0) is True
    assert adapter.is_inside_domain(55.0, 80.0) is True

    # Inside central hole
    assert adapter.is_inside_domain(36.5, 51.0) is False
    assert adapter.is_inside_domain(36.5 + 5.0, 51.0) is False

    # Inside pin holes
    assert adapter.is_inside_domain(20.0, 100.0) is False
    assert adapter.is_inside_domain(20.0, 20.0) is False

    # Outside domain
    assert adapter.is_inside_domain(70.0, 60.0) is False
    assert adapter.is_inside_domain(-5.0, 60.0) is False

    holes = adapter.get_hole_definitions()
    assert len(holes) == 3


def test_f1728_case4_five_hole_adapter():
    """Verify Case 4 (Five-Hole Plate) topology and containment."""
    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_4"])
    adapter = FiveHolePlateAdapter(cfg)

    # 3 interior holes + 2 boundary arcs = 5 void features per Table 5
    holes = adapter.get_hole_definitions()
    assert len(holes) == 3

    # Center of Hole 1: (0.35, 0.45), R=0.10
    assert adapter.is_inside_domain(0.35, 0.45) is False
    # Center of Hole 2: (0.60, 0.55), R=0.05
    assert adapter.is_inside_domain(0.60, 0.55) is False
    # Boundary arcs excluded
    assert adapter.is_inside_domain(0.01, 0.50) is False
    assert adapter.is_inside_domain(0.99, 0.45) is False

    # Far field corner is inside
    assert adapter.is_inside_domain(0.05, 0.05) is True
    assert adapter.is_inside_domain(0.95, 0.95) is True


def test_f1728_case5_seven_hole_adapter():
    """Verify Case 5 (Seven-Hole Plate) topology and containment."""
    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_5"])
    adapter = SevenHolePlateAdapter(cfg)

    # 7 holes from Table 6
    holes = adapter.get_hole_definitions()
    assert len(holes) == 7

    # Center of Hole 1: (0.15, 0.40), R=0.10
    assert adapter.is_inside_domain(0.15, 0.40) is False
    # Center of Hole 7: (0.65, 0.35), R=0.05
    assert adapter.is_inside_domain(0.65, 0.35) is False

    # Bulk corner inside
    assert adapter.is_inside_domain(0.05, 0.05) is True
    assert adapter.is_inside_domain(0.95, 0.95) is True


# ==============================================================================
# 4. BOUNDARY CONDITION AND REGION DISPATCH TESTS
# ==============================================================================

def test_f1728_bc_dispatch():
    """Verify boundary condition dispatch conventions."""
    # Case 1, 2, 4, 5 are tensile edge displacement
    for cid in ("case_1", "case_2", "case_4", "case_5"):
        cfg = AdaptiveConfig.from_json(CONFIG_FILES[cid])
        assert cfg.bc_type == "EDGE_PULL"

    # Case 3 is pin hole pull
    cfg3 = AdaptiveConfig.from_json(CONFIG_FILES["case_3"])
    assert cfg3.bc_type == "PIN_HOLE_PULL"
    assert cfg3.top_pin_hole["center"] == [20.0, 100.0]
    assert cfg3.bottom_pin_hole["center"] == [20.0, 20.0]


# ==============================================================================
# 5. MESH QUALITY AUDIT ENGINE VERIFICATION
# ==============================================================================

def test_f1728_mesh_quality_audit_on_reference_mesh():
    """Verify MeshQualityAuditEngine on an existing reference physical mesh."""
    # Test on Seven-Hole physical mesh (Case 5)
    ref_mesh = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")
    if not os.path.exists(ref_mesh):
        pytest.skip("Seven-hole physical mesh not present locally")

    cfg5 = AdaptiveConfig.from_json(CONFIG_FILES["case_5"])
    adapter5 = SevenHolePlateAdapter(cfg5)
    audit = MeshQualityAuditEngine.evaluate_mesh(ref_mesh, l0_mm=cfg5.l0, adapter=adapter5)

    assert audit["total_physical_elements"] == 15708
    assert audit["quad_count"] == 15325
    assert audit["tri_count"] == 383
    assert audit["quad_fraction_pct"] > 97.0
    assert audit["non_positive_jacobians"] == 0
    assert audit["jacobian_status"] == "PASS"
    assert audit["max_aspect_ratio"] < 10.0
    assert audit["min_corner_angle_deg"] > 25.0


# ==============================================================================
# 6. PRODUCTION DECK BUILDER VERIFICATION
# ==============================================================================

def test_f1728_production_deck_builder_logic(tmp_path):
    """Verify that ProductionDeckBuilder properly builds 3-layer UEL decks."""
    # Create a minimal physical mesh (2 quads) in tmp_path
    inp_content = """*HEADING
Minimal 2-element test mesh
*NODE
1, 0.0, 0.0
2, 0.5, 0.0
3, 1.0, 0.0
4, 0.0, 1.0
5, 0.5, 1.0
6, 1.0, 1.0
*ELEMENT, TYPE=CPS4, ELSET=ALL_ELEM
1, 1, 2, 5, 4
2, 2, 3, 6, 5
*NSET, NSET=ALL_NODES
1, 2, 3, 4, 5, 6
*END STEP
"""
    phys_inp = str(tmp_path / "test_phys.inp")
    with open(phys_inp, "w") as f:
        f.write(inp_content)

    cfg = AdaptiveConfig.from_json(CONFIG_FILES["case_1"])
    prod_inp = str(tmp_path / "test_prod.inp")

    res = ProductionDeckBuilder.build_deck(phys_inp, prod_inp, "TEST_PROD_JOB", cfg, step1_only=True)

    assert res["status"] == "SUCCESS"
    assert res["total_layered_elements"] == 6  # 2 physical * 3 layers
    assert res["phase_elements"] == 2
    assert res["mech_elements"] == 2
    assert res["umat_elements"] == 2

    # Check deck file content
    with open(prod_inp, "r") as f:
        deck_text = f.read()

    assert "*USER ELEMENT" in deck_text
    assert "*MATERIAL, NAME=DUMMY_MAT" in deck_text
    assert "210.0" in deck_text or "E_dummy" in deck_text
    assert "f42_mixed_uel.for" in deck_text or "FROZEN_UEL" in deck_text or FROZEN_UEL_SHA256 in deck_text
