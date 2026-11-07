# -*- coding: utf-8 -*-
"""
tests/unit/test_reusable_2d_adaptive_framework.py
=================================================
Unit and regression tests for the reusable 2D adaptive remeshing framework
(Task F1665, mandated by ChatGPT review HND-e7c597c4a8ee).
"""

import os
import json
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


def test_f1653_authentic_uel_and_bc_compatibility(off_axis_hole_config):
    """Verify production deck strictly matches authentic F1653 UEL property ABI and BCs."""
    prod_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1664_METHOD_A_PROD.inp"
    assert prod_inp.exists()

    with open(str(prod_inp), "r") as f:
        lines = [line.strip() for line in f]

    # 1. Verify UEL Property ABI: l0, Gc, E, nu, k, N_phys (6 properties)
    uel_prop_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("*UEL PROPERTY, ELSET=PHASE_QUAD"):
            uel_prop_idx = i
            break
    assert uel_prop_idx != -1, "PHASE_QUAD UEL PROPERTY card missing"
    props = [p.strip() for p in lines[uel_prop_idx + 1].split(",")]
    assert len(props) == 6, "Expected 6 UEL properties, got %d" % len(props)
    assert float(props[0]) == 0.0075, "PROPS(1) must be l0 (0.0075)"
    assert float(props[1]) == 0.0027, "PROPS(2) must be Gc (0.0027)"
    assert float(props[2]) == 210.0, "PROPS(3) must be E in kN/mm^2 (210.0)"
    assert float(props[3]) == 0.30, "PROPS(4) must be nu (0.3)"
    assert float(props[4]) == 1.0e-7, "PROPS(5) must be k_residual (1.0e-7)"
    assert float(props[5]) == 20213.0, "PROPS(6) must be N_phys (20213.0)"

    # 2. Verify Companion Visualizer Material: DUMMY_MAT with CONSTANTS=3 (E, nu, N_phys), DEPVAR 20
    mat_idx = -1
    for i, line in enumerate(lines):
        if line.startswith("*MATERIAL, NAME=DUMMY_MAT"):
            mat_idx = i
            break
    assert mat_idx != -1, "DUMMY_MAT material missing"
    assert lines[mat_idx + 1].startswith("*USER MATERIAL, CONSTANTS=3")
    umat_props = [p.strip() for p in lines[mat_idx + 2].split(",")]
    assert float(umat_props[0]) == 210.0
    assert float(umat_props[1]) == 0.3
    assert float(umat_props[2]) == 20213.0
    assert lines[mat_idx + 3].startswith("*DEPVAR")
    assert lines[mat_idx + 4] == "20"

    # 3. Verify SOLID SECTION applies only to All_elem (UMAT), not uelems
    assert "*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT" in lines

    # 4. Verify boundary conditions in Step 1
    step1_idx = lines.index("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000")
    step1_text = "\n".join(lines[step1_idx:step1_idx + 25])
    assert "N_BOTTOM, 2, 2, 0.0" in step1_text
    assert "N_PIN, 1, 1, 0.0" in step1_text
    assert "N_TOP, 1, 1, 0.0" in step1_text
    assert "N_RP, 2, 2, 0.0050" in step1_text
    assert "MISESERI, MISESAVG, S, E, SDV" in step1_text


def test_f1666_hybrid_mesh_off_axis_hole():
    """Verify F1666 hybrid adapted mesh quality on off-axis hole benchmark."""
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1666_HYBRID_ADAPT_PHYS.inp"
    assert inp_path.exists(), "F1666 hybrid physical mesh not found"

    metrics = MeshQualityAuditEngine.evaluate_mesh(str(inp_path), l0_mm=0.0075)
    assert metrics["total_elements"] == 73251
    assert metrics["quad_percent"] == 100.0
    assert metrics["non_positive_jacobians"] == 0, "Non-positive Jacobians detected!"
    assert metrics["min_det_j"] > 0.0
    assert metrics["h_median_um"] < 2.50
    assert metrics["elements_le_2p5um"] > 25000


def test_f1666_hybrid_mesh_straight_notch():
    """
    Verify F1666 hybrid adapted mesh quality on straight-notch benchmark.
    NOTE: As qualified in F1666/F1667, this benchmark utilizes synthetic crack-line
    sizing points (y=0.50) and serves as a SYNTHETIC_MESHER_TEST for geometric/topological
    mesh generation, not an authentic simulation-field-driven adaptive remesh.
    """
    inp_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "01_standard_pfm_reference" / "PK_MODE1_F1666_HYBRID_ADAPT_PHYS.inp"
    assert inp_path.exists(), "F1666 straight notch hybrid physical mesh not found"

    metrics = MeshQualityAuditEngine.evaluate_mesh(str(inp_path), l0_mm=0.0075)
    assert metrics["total_elements"] == 10100
    assert metrics["quad_percent"] == 100.0
    assert metrics["non_positive_jacobians"] == 0, "Non-positive Jacobians detected!"
    assert metrics["min_det_j"] > 0.0
    assert metrics["distorted_elements"] == 0
    assert metrics["h_median_um"] < 2.50
    assert metrics["elements_le_1p5um"] >= 3000


def test_f1668_three_way_controlled_comparison_meshes():
    """Verify F1668 Case A, Case B, and Case C meshes strictly satisfy quality and FE parity."""
    base_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"

    # Case A: Stress-Only (64,032 elements)
    case_a_phys = base_dir / "PK_HOLE_F1668_CASE_A_STRESS_ONLY_PHYS.inp"
    assert case_a_phys.exists()
    m_a = MeshQualityAuditEngine.evaluate_mesh(str(case_a_phys), l0_mm=0.0075)
    assert m_a["total_elements"] == 64032
    assert m_a["non_positive_jacobians"] == 0
    assert m_a["min_det_j"] > 0.0
    assert m_a["elements_le_1p5um"] > 25000

    # Case B: Damage-Only (8,237 elements) - Leanest Adaptive Mesh
    case_b_phys = base_dir / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PHYS.inp"
    assert case_b_phys.exists()
    m_b = MeshQualityAuditEngine.evaluate_mesh(str(case_b_phys), l0_mm=0.0075)
    assert m_b["total_elements"] == 8237
    assert m_b["non_positive_jacobians"] == 0
    assert m_b["distorted_elements"] == 0
    assert m_b["min_det_j"] > 0.0
    assert m_b["h_median_um"] < 2.50
    assert m_b["elements_le_1p5um"] > 2000

    # Case C: Combined Synergistic (64,746 elements)
    case_c_phys = base_dir / "PK_HOLE_F1668_CASE_C_COMBINED_PHYS.inp"
    assert case_c_phys.exists()
    m_c = MeshQualityAuditEngine.evaluate_mesh(str(case_c_phys), l0_mm=0.0075)
    assert m_c["total_elements"] == 64746
    assert m_c["non_positive_jacobians"] == 0
    assert m_c["min_det_j"] > 0.0
    assert m_c["elements_le_1p5um"] > 27000


def test_f1668_production_decks_frozen_uel():
    """Verify all three F1668 production decks have exact 3x layered parity and verified UEL."""
    base_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole"
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"

    decks = [
        (base_dir / "PK_HOLE_F1668_CASE_A_STRESS_ONLY_PROD.inp", 64032, 192096),
        (base_dir / "PK_HOLE_F1668_CASE_B_DAMAGE_ONLY_PROD.inp", 8237, 24711),
        (base_dir / "PK_HOLE_F1668_CASE_C_COMBINED_PROD.inp", 64746, 194238)
    ]

    for deck_path, n_phys, n_layered in decks:
        assert deck_path.exists(), "Deck %s not found" % deck_path
        with open(str(deck_path), "r") as f:
            content = f.read()
        assert "*USER ELEMENT, TYPE=U1" in content
        assert "*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD" in content
        assert "*ELEMENT, TYPE=U2, ELSET=DISP_QUAD" in content
        assert "*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS" in content
        assert ProductionDeckBuilder.verify_uel_subroutine(str(uel_path), FROZEN_UEL_SHA256)


def test_f1669_case_b_qualification_audit():
    """Verify F1669 comprehensive Case B qualification audit and evidence reconciliation."""
    audit_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1669_CASE_B_QUALIFICATION_AUDIT.json"
    assert audit_json.exists(), "F1669 qualification audit JSON not found"

    with open(str(audit_json), "r") as f:
        data = json.load(f)

    assert data["scientific_qualification_verdict"] == "CASE_B_READY_FOR_SEPARATELY_AUTHORIZED_DATACHECK"
    assert data["reconciled_comparative_metrics"]["CASE_B_DAMAGE_ONLY"]["distorted_elements_count"] == 0
    assert data["reconciled_comparative_metrics"]["CASE_B_DAMAGE_ONLY"]["total_elements"] == 8237
    assert data["case_b_production_deck_audit"]["slit_flanks_verified"]["is_fully_separated"] is True
    assert data["case_b_production_deck_audit"]["slit_flanks_verified"]["top_flank_nodes"] == 29
    assert data["case_b_production_deck_audit"]["slit_flanks_verified"]["bottom_flank_nodes"] == 29
    assert data["case_b_production_deck_audit"]["frozen_uel_sha256_match"] == FROZEN_UEL_SHA256


def test_f1670_damage_core_and_quality_metric_reconciliation():
    """Verify F1670 damage core reconciliation and quality metric harmonization."""
    f1670_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1670_DAMAGE_CORE_RECONCILIATION.json"
    f1668_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1668_THREE_WAY_COMPARISON_METRICS.json"
    f1669_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1669_CASE_B_QUALIFICATION_AUDIT.json"

    assert f1670_json.exists(), "F1670 reconciliation JSON not found"
    assert f1668_json.exists(), "F1668 metrics JSON not found"
    assert f1669_json.exists(), "F1669 audit JSON not found"

    with open(str(f1670_json), "r") as f:
        d1670 = json.load(f)
    with open(str(f1668_json), "r") as f:
        d1668 = json.load(f)
    with open(str(f1669_json), "r") as f:
        d1669 = json.load(f)

    # 1. Mathematical Subset Proof
    root_cause = d1670["damage_core_discrepancy_root_cause"]
    assert root_cause["mathematical_relationship"]["is_d80_subset_of_d70"] is True
    assert root_cause["mathematical_relationship"]["difference_element_count"] == 407
    assert root_cause["threshold_d_0p70"]["case_b_elements_within_2l0"] == 4931
    assert root_cause["threshold_d_0p80"]["case_b_elements_within_2l0"] == 4524

    # 2. Harmonized Metrics in F1668 JSON
    case_b_1668 = d1668["CASE_B_DAMAGE_ONLY"]
    assert "crack_core_count" not in case_b_1668["overall_quality"], "Placeholder crack_core_count: 0 not removed!"
    assert case_b_1668["regional_sizing"]["damage_support_d_ge_0p70"]["total_elements"] == 4931
    assert case_b_1668["regional_sizing"]["damage_support_d_ge_0p70"]["count_le_2p5um"] == 4236
    assert case_b_1668["regional_sizing"]["damage_support_d_ge_0p70"]["count_le_3p75um"] == 4601
    assert case_b_1668["regional_sizing"]["severe_crack_core_d_ge_0p80"]["total_elements"] == 4524
    assert case_b_1668["regional_sizing"]["severe_crack_core_d_ge_0p80"]["count_le_2p5um"] == 3904
    assert case_b_1668["regional_sizing"]["severe_crack_core_d_ge_0p80"]["count_le_3p75um"] == 4241

    # 3. Quality Metrics Harmonization
    quality = d1670["element_quality_reconciliation"]
    assert quality["standard_code_criterion"]["distorted_elements"] == 0
    assert quality["strict_screening_criterion"]["distorted_elements"] == 17
    assert d1670["final_reconciliation_verdict"] == "COMPLETE_AND_SYNCHRONIZED"


def test_f1671_case_b_datacheck_manifest():
    """Verify F1671 Case B Abaqus datacheck manifest integrity and offline qualification."""
    manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1671_DATACHECK_MANIFEST.json"
    assert manifest_path.exists(), "F1671 datacheck manifest not found"

    with open(str(manifest_path), "r") as f:
        data = json.load(f)

    assert data["manifest_version"] == "1.0"
    assert data["governed_provenance"]["verified_github_commit"] == "576ea81c70fde60eeff4faf24a99a95677c3b9c4"
    assert data["target_model"]["case_id"] == "CASE_B_DAMAGE_ONLY"

    deck_info = data["target_model"]["input_deck"]
    assert deck_info["total_physical_elements"] == 8237
    assert deck_info["total_layered_elements"] == 24711
    assert deck_info["sha256"] == "D1D71B2033B7172DD8B126D287AFB24772D489622D47910072B92F902733CC32"

    uel_info = data["target_model"]["user_subroutine"]
    assert uel_info["sha256"] == FROZEN_UEL_SHA256
    assert uel_info["frozen_hash_match"] is True

    struct = data["deck_structural_verification"]
    assert struct["slit_topology"]["top_flank_nodes"] == 29
    assert struct["slit_topology"]["bottom_flank_nodes"] == 29
    assert struct["slit_topology"]["shared_nodes"] == 0
    assert struct["slit_topology"]["separation_verdict"] == "100_PERCENT_DISCONNECTED"

    spec = data["datacheck_execution_specification"]
    assert spec["job_name"] == "M1_HOLE_CASE_B_DATACHECK"
    assert spec["duplication_safeguard"]["is_duplicate_in_ledger"] is False
    assert spec["datacheck_mode_only"] is True
    assert spec["zero_equilibrium_increments"] is True

    ops = data["operational_boundaries"]
    assert ops["max_new_pbs_submissions"] == 0
    assert ops["actual_hpc_submission"] == "HALTED_AWAITING_SEPARATE_AUTHORIZATION"
    assert ops["full_fracture_solve"] == "NOT_AUTHORIZED"






