# -*- coding: utf-8 -*-
"""
tests/unit/test_reusable_2d_adaptive_framework.py
=================================================
Unit and regression tests for the reusable 2D adaptive remeshing framework
(Task F1665, mandated by ChatGPT review HND-e7c597c4a8ee).
"""

import os
import json
import csv
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
    assert ops["max_new_pbs_submissions"] in (0, 1)
    assert "AUTHORIZED" in ops["actual_hpc_submission"] or ops["actual_hpc_submission"] == "HALTED_AWAITING_SEPARATE_AUTHORIZATION"
    assert ops["full_fracture_solve"] == "NOT_AUTHORIZED"


def test_f1673_zero_miseseri_root_cause_audit():
    """Verify Task F1673 audit of zero-MISESERI defect and recovery qualification."""
    audit_path = (
        REPO_ROOT
        / "models"
        / "pandey_kumar_mode1"
        / "176_method_a_plate_with_hole"
        / "PK_HOLE_F1673_ROOT_CAUSE_AUDIT.json"
    )
    assert audit_path.exists(), "F1673 root cause audit JSON not found"

    with open(str(audit_path), "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["task_id"] == "F1673-DIRECT-UEL-UMAT-STRESS-TRANSFER-AND-ROOT-CAUSE-QUALIFICATION"
    assert meta["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert meta["frozen_uel_verified"] is True

    rc = data["root_cause_diagnosis"]
    assert "lines 876-882" in rc["source_location"]
    assert rc["common_block_audit"]["stress_tensor_transferred"] is False

    evals = data["comparative_evaluation_of_approaches"]
    assert "UNFEASIBLE" in evals["approach_a_direct_uel_umat_forward_transfer"]["technical_feasibility"]
    assert "FEASIBLE" in evals["approach_b_non_feedback_replay"]["technical_feasibility"]
    assert "QUALIFIED" in evals["approach_c_auxiliary_usdfld_recovery"]["technical_feasibility"]

    strat = data["strategic_selection_and_six_day_roadmap"]
    assert strat["selected_strategy"] == "APPROACH_B_AND_C_NON_FEEDBACK_RECOVERY"


def test_f1674_stress_replay_and_miseseri_qualification():
    """Verify Task F1674 authentic stress replay and MISESERI qualification."""
    audit_path = (
        REPO_ROOT
        / "models"
        / "pandey_kumar_mode1"
        / "176_method_a_plate_with_hole"
        / "PK_HOLE_F1674_STRESS_REPLAY_QUALIFICATION.json"
    )
    assert audit_path.exists(), "F1674 stress replay qualification JSON not found"

    with open(str(audit_path), "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["metadata"]
    assert meta["task_id"] == "F1674-AUTHENTIC-COUPLED-STATE-STRESS-REPLAY-AND-MISESERI-QUALIFICATION"
    assert meta["donor_job_id"] == "1421063.mmaster02"
    assert meta["max_new_pbs_submissions"] == 0

    proc = data["procedural_distinction"]
    assert "Procedure A" in proc["procedure_a_prescribed_displacement_replay"]["name"]
    assert "Procedure B" in proc["procedure_b_auxiliary_equilibrium_recovery"]["name"]
    assert "NOT_EQUILIBRATED" in proc["procedure_a_prescribed_displacement_replay"]["equilibrium_status"]
    assert "EXACT_STATIC_EQUILIBRIUM" in proc["procedure_b_auxiliary_equilibrium_recovery"]["equilibrium_status"]

    mesh = data["mesh_transfer_audit"]
    assert mesh["donor_mesh"]["total_physical_elements"] == 2906
    assert mesh["recovery_mesh"]["total_elements"] == 2935
    assert mesh["recovery_mesh"]["slit_separation"] == "100_PERCENT_DISCONNECTED"
    assert mesh["recovery_mesh"]["max_ip_coordinate_error_nm"] < 1.0  # < 1 nm

    stress = data["stress_parity_metrics"]
    assert stress["global_stress_parity"]["pearson_r"] > 0.95
    assert stress["global_stress_parity"]["nrmse_pct"] < 5.0
    assert stress["regime_stress_parity"]["intact_far_field_d_lt_0p10"]["pearson_r"] > 0.97
    assert stress["regime_stress_parity"]["active_softening_0p10_le_d_lt_0p80"]["pearson_r"] > 0.90

    miseseri = data["miseseri_field_audit"]
    assert miseseri["status"] == "QUALIFIED_AUTHENTIC_AND_NONZERO"
    assert miseseri["element_count"] == 2935
    assert miseseri["raw_miseseri_statistics_MPa"]["median"] > 2.0
    assert miseseri["raw_miseseri_statistics_MPa"]["max"] > 1000.0

    synth = data["synthesis"]
    assert synth["qualification_verdict"] == "RECOVERY_STRESS_FIELD_AND_MISESERI_QUALIFIED"
    assert synth["gate_3_readiness"]["remeshing_rule_parameters"]["errorTarget"] == 0.05
    assert synth["gate_3_readiness"]["established_adapted_mesh_baseline"]["total_elements"] == 20213


def test_f1675_method_a_deck_qualification_manifest():
    """Verify Task F1675/F1675R Method A refined production deck qualification manifest."""
    manifest_path = (
        REPO_ROOT
        / "models"
        / "pandey_kumar_mode1"
        / "176_method_a_plate_with_hole"
        / "PK_HOLE_F1675_DATACHECK_MANIFEST.json"
    )
    assert manifest_path.exists(), "F1675 datacheck manifest not found"

    with open(str(manifest_path), "r", encoding="utf-8") as f:
        data = json.load(f)

    meta = data["task_id"]
    assert "F1675" in meta

    corr = data["reconciled_historical_facts"]
    assert corr["coarse_donor_composition"]["cps4r_quads"] == 2832
    assert corr["coarse_donor_composition"]["cps3_tris"] == 74
    assert corr["coarse_donor_composition"]["total_physical_elements"] == 2906
    assert corr["remeshing_rule_error_target"]["abaqus_cae_api_value"] == 5.0
    assert corr["f1664_recovery_odb"]["filename"] == "PK_HOLE_F1661_RECOVERY.odb"
    assert corr["pbs_queue"]["queue_name"] == "entry_imfdfkmq"

    deck = data["target_model"]["input_deck"]
    assert deck["total_physical_elements"] == 20213
    assert deck["total_layered_elements"] == 60639
    assert deck["total_deck_nodes"] == 20214
    assert deck["physical_nodes"] == 20213
    assert deck["master_reference_node"] == 999999
    assert deck["sha256"] == "B6FB9AD2C16293E78E0940C00C65D9D54C3921E8234CEB770956117D6B39D99B"

    mesh = data["target_model"]["physical_mesh"]
    assert mesh["non_positive_jacobians"] == 0
    assert mesh["distorted_elements"] == 0
    assert mesh["quad_count"] == 19644
    assert mesh["tri_count"] == 569

    struct = data["card_by_card_structural_verification"]
    assert struct["notch_geometry"]["top_flank_nodes"] == 28
    assert struct["notch_geometry"]["bottom_flank_nodes"] == 29
    assert struct["notch_geometry"]["shared_flank_nodes"] == 0
    assert struct["notch_geometry"]["flank_separation"] == "100_PERCENT_DISCONNECTED"
    assert struct["boundary_conditions_and_ties"]["rigid_top_tying_equations"] == 83
    assert struct["boundary_conditions_and_ties"]["reference_node"] == 999999

    uel = data["target_model"]["user_subroutine"]
    assert uel["sha256"] == FROZEN_UEL_SHA256
    assert uel["frozen_hash_match"] is True

    ops = data["operational_boundaries"]
    assert ops["max_new_pbs_submissions"] in (0, 1)
    assert "AUTHORIZED" in ops["actual_hpc_submission"] or ops["actual_hpc_submission"] == "HALTED_AWAITING_SEPARATE_AUTHORIZATION"


def test_f1675r_direct_card_by_card_deck_verification():
    """Verify Task F1675R card-by-card deck parsing directly against frozen UEL ABI."""
    from scripts.validation.validate_f1675r_method_a_production_deck import audit_and_generate_f1675r_manifest
    manifest = audit_and_generate_f1675r_manifest()
    assert manifest["task_id"] == "F1675R-METHOD-A-PRODUCTION-DECK-CORRECTION-AND-GATE"
    assert manifest["target_model"]["input_deck"]["deck_integrity"] == "100_PERCENT_VALID_ZERO_DEFECTS"


def test_f1676_datacheck_qualification():
    """Verify Task F1676 Abaqus datacheck execution, fail-closed checks, and all 7 acceptance criteria."""
    from scripts.validation.evaluate_f1676_datacheck_qualification import evaluate_datacheck
    report = evaluate_datacheck()
    assert report["qualification_verdict"] == "FAIL_CLOSED_DATACHECK_QUALIFICATION_PASS"
    assert report["execution_telemetry"]["execution_mode"] == "INTERACTIVE_LOGIN_NODE_PREPROCESSOR_DATACHECK"
    assert report["warnings_classification"]["total_warnings"] == 8
    assert report["warnings_classification"]["verdict"] == "NON_FATAL_INFORMATIONAL_ONLY_ZERO_OUTPUTS_SUPPRESSED"
    assert report["model_problem_size"]["total_elements"] == 60639
    assert report["model_problem_size"]["total_nodes"] == 20214
    assert report["solver_memory_accounting"]["preprocessor_estimates"]["minimum_memory_required_mb"] == 51
    assert report["solver_memory_accounting"]["preprocessor_estimates"]["memory_to_minimize_io_mb"] == 151
    assert all(c["status"] == "PASS" for c in report["acceptance_criteria_verification"].values())


def test_f1677_method_a_production_fracture_manifest():
    """Verify Task F1677/F1677R Method A production fracture execution manifest and staging."""
    manifest_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "PK_HOLE_F1677_FRACTURE_MANIFEST.json"
    assert manifest_path.exists(), f"Missing manifest: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["manifest_version"] == "1.1"
    assert data["task_id"] == "F1677R-METHOD-A-PRODUCTION-FRACTURE-MANIFEST-REVISED"
    assert data["production_job"]["job_name"] == "M1_HOLE_F1664_METHOD_A_PROD"
    assert data["production_job"]["input_deck"]["sha256"] == "B6FB9AD2C16293E78E0940C00C65D9D54C3921E8234CEB770956117D6B39D99B"
    assert data["production_job"]["user_subroutine"]["sha256"] == FROZEN_UEL_SHA256

    hpc = data["hpc_resource_and_scheduler_evidence"]
    assert hpc["pbs_queue"] == "entry_imfdfkmq"
    assert hpc["requested_walltime"] == "08:00:00"
    assert hpc["requested_cpus"] == 1
    assert hpc["requested_memory_gb"] == 16

    storage = data["storage_and_scratch_quota_budget"]
    assert storage["scratch_filesystem"] == "/scratch9"
    assert storage["user_quota_evidence"]["soft_limit_gb"] == "unlimited"

    loading = data["model_discretization_and_loading"]["loading_schedule"]
    assert loading["step_1"]["target_displacement_mm"] == 0.0050
    assert loading["step_2"]["target_displacement_mm"] == 0.0120

    plan = data["output_extraction_and_reconstruction_plan"]
    assert "SDV1" in plan["phase_field_damage"]["components"]
    assert "E_elastic_kNmm" in plan["energy_balance_reconstruction"]["uel_csv_columns"]

    crit = data["physics_based_acceptance_criteria"]
    assert len(crit) == 7

    ops = data["operational_boundaries"]
    assert ops["max_new_pbs_submissions"] == 0
    assert ops["actual_hpc_submission"] == "HALTED_AWAITING_SEPARATE_AUTHORIZATION"


def test_f1678_method_a_production_fracture_qualification():
    """Verify Task F1678 Method A production fracture simulation execution, convergence, and physical metrics."""
    summary_path = REPO_ROOT / "results" / "validation" / "f1678_prod_summary.json"
    assert summary_path.exists(), f"Missing summary JSON: {summary_path}"
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["model_name"] == "M1_HOLE_F1664_METHOD_A_PROD"
    assert data["pbs_job_id"] == "1421142.mmaster02"
    assert data["status"] == "COMPLETED_EXIT_0"
    assert data["n_physical_elements"] == 20213
    assert data["n_layered_elements"] == 60639
    assert data["total_increments"] >= 550

    # Force and displacement
    assert 0.58 <= data["peak_reaction_force_kN"] <= 0.80
    assert 0.0050 <= data["peak_displacement_mm"] <= 0.0070
    assert data["final_displacement_mm"] == 0.0120000001
    assert data["final_reaction_force_kN"] < 0.010  # Complete post-peak softening

    # Energy balance
    assert data["final_e_elastic_kNmm"] < 1.0e-5  # Complete relaxation of elastic energy
    assert 0.0025 <= data["final_e_fracture_kNmm"] <= 0.0030  # Monotonic fracture dissipation plateau
    assert data["energy_balance_discrepancy_pct"] < 2.0  # Exceptional energy balance (1.489%)

    # Two-stage crack trajectory
    traj = data["trajectory"]
    assert traj["deflection_toward_hole_verified"] is True
    assert traj["right_flank_initiation"] is True
    assert traj["total_broken_elements"] >= 8000
    assert traj["max_x_crack"] >= 0.99  # Propagated to right boundary

    # Extraction artifacts existence
    rf_csv = REPO_ROOT / "results" / "validation" / "f1678_prod_rf_u.csv"
    crack_csv = REPO_ROOT / "results" / "validation" / "f1678_prod_crack_path.csv"
    energy_csv = REPO_ROOT / "results" / "validation" / "uel_energy_balance.csv"
    assert rf_csv.exists()
    assert crack_csv.exists()
    assert energy_csv.exists()

    # Publication figures existence
    fig1 = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1678_method_a_crack_path.png"
    fig2 = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1678_method_a_load_displacement_comparison.png"
    fig3 = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1678_method_a_energy_balance.png"
    assert fig1.exists()
    assert fig2.exists()
    assert fig3.exists()


def test_f1679_method_a_evidence_closeout_and_kinematic_verification():
    """Verify Task F1679 evidence closeout, time-resolved kinematics, and energy monotonicity."""
    # 1. Energy and solver verification JSON
    solver_path = REPO_ROOT / "results" / "validation" / "f1679_energy_and_solver_verification.json"
    assert solver_path.exists(), "f1679_energy_and_solver_verification.json not found"

    with open(str(solver_path), "r", encoding="utf-8") as f:
        data = json.load(f)

    sol = data["solver_execution"]
    assert sol["pbs_job_id"] == "1421142.mmaster02"
    assert sol["exit_code"] == 0
    assert sol["total_increments"] == 614
    assert sol["step_1_increments"] == 57
    assert sol["step_2_increments"] == 557
    assert sol["total_cutbacks"] == 18
    assert sol["numerical_problem_warnings"] == 0
    assert sol["error_messages"] == 0
    assert sol["memory_peak_gb"] == 2
    assert sol["timing_reconciliation"]["total_cpu_time_sec"] == 3580.0
    assert sol["timing_reconciliation"]["wallclock_time_sec"] == 5149.0

    eng = data["energy_verification"]
    assert eng["total_energy_records"] == 614
    assert eng["fracture_energy_monotonicity"]["monotonic"] is True
    assert eng["fracture_energy_monotonicity"]["num_decreases"] == 0
    assert eng["elastic_energy_relaxation"]["relaxation_pct"] >= 99.8
    assert eng["final_endpoint"]["residual_rel_pct"] < 1.50  # 1.489%

    # 2. Time-resolved crack summary JSON
    crack_path = REPO_ROOT / "results" / "validation" / "f1679_time_resolved_crack_summary.json"
    assert crack_path.exists(), "f1679_time_resolved_crack_summary.json not found"

    with open(str(crack_path), "r", encoding="utf-8") as f:
        states = json.load(f)

    assert len(states) == 7

    # State 1: Peak force
    s1 = states[1]
    assert s1["name"] == "step2_peak"
    assert abs(s1["rf2_top_kN"] - 0.593390) < 1e-4
    assert s1["crack_topology"]["primary_crack"]["present"] is True

    # State 2: Hole arrest
    s2 = states[2]
    assert s2["name"] == "step2_inc180"
    assert s2["crack_topology"]["primary_crack"]["reached_hole"] is True
    assert s2["crack_topology"]["primary_crack"]["dist_to_hole_perimeter_mm"] < 0.005
    assert s2["crack_topology"]["secondary_crack"]["present"] is False

    # State 3: Secondary crack nucleation
    s3 = states[3]
    assert s3["name"] == "step2_inc198"
    assert s3["crack_topology"]["secondary_crack"]["present"] is True
    assert s3["crack_topology"]["secondary_crack"]["num_elements"] >= 20
    assert s3["crack_topology"]["secondary_crack"]["nucleation_x"] >= 0.750

    # State 4: Secondary snap-through
    s4 = states[4]
    assert s4["name"] == "step2_inc220"
    assert s4["crack_topology"]["secondary_crack"]["reached_boundary"] is True
    assert s4["crack_topology"]["secondary_crack"]["tip_x"] >= 0.999

    # State 6: Final severed state
    s6 = states[6]
    assert s6["name"] == "step2_final"
    assert s6["rf2_top_kN"] < 0.001
    assert s6["damage_bounds"]["num_overshoot_elements"] <= 10
    assert s6["damage_bounds"]["max_overshoot"] < 0.002  # < 0.2% overshoot

    # 3. Time-resolved progression figure and thesis PDF
    fig_prog_png = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1679_time_resolved_crack_progression.png"
    fig_prog_pdf = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1679_time_resolved_crack_progression.pdf"
    main_pdf = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "main.pdf"
    assert fig_prog_png.exists()
    assert fig_prog_pdf.exists()
    assert main_pdf.exists()


def test_f1680_method_a_scientific_correction_and_ip_audit():
    """Verify Task F1680 scientific corrections, IP damage aggregation audit, and thesis alignment."""
    # 1. IP aggregation audit JSON
    audit_path = REPO_ROOT / "results" / "validation" / "f1680_ip_aggregation_audit.json"
    assert audit_path.exists(), "f1680_ip_aggregation_audit.json not found"

    with open(str(audit_path), "r", encoding="utf-8") as f:
        audit = json.load(f)

    mesh = audit["mesh_discretization_breakdown"]
    assert mesh["total_physical_elements"] == 20213
    assert mesh["quadrilateral_elements_cpe4"] == 19644
    assert mesh["triangular_elements_cpe3"] == 569

    prov = audit["provenance_reconciliation"]
    assert prov["total_ip_records_f1678"] == 8520
    assert prov["unique_physical_elements"] == 2169
    assert prov["damaged_quads_count"] == 2117
    assert prov["damaged_tris_count"] == 52
    assert prov["quad_ip_records"] == 8468
    assert prov["tri_ip_records"] == 52
    assert prov["reconciliation_verdict"] == "VERIFIED_EXACT_TOPOLOGICAL_IDENTITY"

    intra = audit["intracell_damage_variation"]
    assert intra["intracell_invariance"] is True
    assert intra["max_damage_spread_intracell"] == 0.0

    over = audit["overshoot_quantification"]
    assert over["unique_overshoot_elements_max_rule"] == 8
    assert over["maximum_overshoot_pct"] < 0.06

    # 2. Raw solver logs and crack state evidence files
    assert (REPO_ROOT / "results" / "validation" / "M1_HOLE_F1664_METHOD_A_PROD.sta").exists()
    assert (REPO_ROOT / "results" / "validation" / "M1_HOLE_F1664_METHOD_A_PROD.msg").exists()
    assert (REPO_ROOT / "results" / "validation" / "M1_HOLE_F1664_METHOD_A_PROD_pbs_execution.log").exists()
    assert (REPO_ROOT / "results" / "validation" / "f1679_time_resolved_crack_states.csv").exists()

    # 3. Chapter 5 text checks
    chap5_path = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "chapter05_method_a_hole_benchmark.tex"
    with open(str(chap5_path), "r", encoding="utf-8") as f:
        tex = f.read()

    # Check DOF 3 correction
    assert "d = u_3" in tex, "Phase-field DOF 3 not documented in Chapter 5"
    assert "PHASE\\_SHARED" in tex, "COMMON block PHASE_SHARED not documented in Chapter 5"
    assert "D\\_COMM" in tex, "Variable D_COMM not documented in Chapter 5"

    # Check elimination of false literature claim
    assert "within 1.1% of the 0.60" not in tex, "False literature agreement claim not eliminated"
    assert "tab:hole_pandey_kumar_comparison" in tex, "Comparison table label missing"
    assert "miehe2010a" in tex, "Correct Miehe citation missing"


def test_f1682_complete_odb_extraction_and_spatial_audit():
    """Verify Task F1682 complete ODB frame extraction and defect-free spatial audit."""
    coarse_prog = REPO_ROOT / "results" / "validation" / "f1682_coarse_all_frames_progression.csv"
    prod_prog = REPO_ROOT / "results" / "validation" / "f1682_prod_all_frames_progression.csv"
    full_damage = REPO_ROOT / "results" / "validation" / "f1682_prod_final_full_damage_field.csv"
    audit_json = REPO_ROOT / "results" / "validation" / "f1682_spatial_resolution_audit.json"
    synth_json = REPO_ROOT / "results" / "validation" / "f1682_fracture_timeline_synthesis.json"
    synth_csv = REPO_ROOT / "results" / "validation" / "f1682_fracture_timeline_comparison.csv"

    assert coarse_prog.exists(), "Coarse progression CSV missing"
    assert prod_prog.exists(), "Production progression CSV missing"
    assert full_damage.exists(), "Full damage CSV missing"
    assert audit_json.exists(), "Audit JSON missing"
    assert synth_json.exists(), "Synthesis JSON missing"
    assert synth_csv.exists(), "Synthesis CSV missing"

    # 1. Coarse progression assertions
    with open(str(coarse_prog), "r", encoding="utf-8") as f:
        coarse_rows = list(csv.DictReader(f))
    assert len(coarse_rows) == 389, f"Expected 389 coarse frames, got {len(coarse_rows)}"
    assert float(coarse_rows[-1]["u2_top"]) > 0.0095

    # 2. Production progression assertions
    with open(str(prod_prog), "r", encoding="utf-8") as f:
        prod_rows = list(csv.DictReader(f))
    assert len(prod_rows) == 616, f"Expected 616 production frames, got {len(prod_rows)}"
    final_prod = prod_rows[-1]
    assert abs(float(final_prod["u2_top"]) - 0.0120) < 1e-4, "Production solve did not reach 0.0120 mm"
    assert float(final_prod["rf2_top"]) < 0.001, "Production residual force not softened"

    # 3. Full damage coverage assertions (100% of 20,213 physical elements)
    with open(str(full_damage), "r", encoding="utf-8") as f:
        dmg_rows = list(csv.DictReader(f))
    assert len(dmg_rows) == 20213, f"Expected 20,213 physical elements, got {len(dmg_rows)}"

    # 4. Defect-free audit assertions (distinct populations)
    with open(str(audit_json), "r", encoding="utf-8") as f:
        audit = json.load(f)

    whole = audit["Whole Specimen Domain"]
    core_05 = audit["Active Fracture Core (d >= 0.50)"]
    core_08 = audit["Broken Crack Core (d >= 0.80)"]
    core_095 = audit["Fully Severed Core (d >= 0.95)"]
    far_field = audit["Intact Far-Field (d < 0.10)"]

    assert whole["element_count"] == 20213
    assert core_05["element_count"] == 3060
    assert core_08["element_count"] == 2169
    assert core_095["element_count"] == 1709
    assert far_field["element_count"] == 12250
    # Crucial F1681 defect fix: populations must NOT be identical
    assert core_05["element_count"] != core_08["element_count"], "d>=0.50 and d>=0.80 populations are identically flawed"
    assert core_08["element_count"] != core_095["element_count"]

    # 5. Synthesis timeline assertions
    with open(str(synth_json), "r", encoding="utf-8") as f:
        synth = json.load(f)

    assert synth["coarse_donor_mesh"]["n_physical_elements"] == 2906
    assert synth["refined_production_mesh"]["n_physical_elements"] == 20213
    assert abs(synth["refined_production_mesh"]["softening_reduction_pct"] - (-18.83)) < 0.1
    assert len(synth["stages"]) == 8


def test_f1682r_chronological_monotonicity_and_miseseri_spatial_integration():
    """Verify F1682R strict timeline monotonicity, spatial MISESERI area-weighted integration, and controlled recovery plan."""
    miseseri_json = REPO_ROOT / "results" / "validation" / "f1682_miseseri_spatial_integration_audit.json"
    miseseri_csv = REPO_ROOT / "results" / "validation" / "f1682_miseseri_element_level_audit.csv"
    timeline_json = REPO_ROOT / "results" / "validation" / "f1682_fracture_timeline_synthesis.json"
    disp_csv = REPO_ROOT / "results" / "validation" / "f1682_displacement_aligned_comparison.csv"
    plan_json = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "F1682R_CONTROLLED_RECOVERY_PLAN.json"

    assert miseseri_json.exists(), "F1682R MISESERI spatial integration JSON missing"
    assert miseseri_csv.exists(), "F1682R MISESERI element-level CSV missing"
    assert timeline_json.exists(), "F1682R timeline synthesis JSON missing"
    assert disp_csv.exists(), "F1682R displacement-aligned CSV missing"
    assert plan_json.exists(), "F1682R controlled recovery plan missing"

    # 1. MISESERI Area-Weighted Integration Assertions
    with open(str(miseseri_json), "r", encoding="utf-8") as f:
        m_audit = json.load(f)

    assert m_audit["total_elements"] == 2935
    assert abs(m_audit["total_domain_area_mm2"] - 0.9678) < 0.001
    assert abs(m_audit["misesavg_MPa"] - 76.3215) < 0.01

    regions = {r["group_name"]: r for r in m_audit["regions"]}
    sec = regions["Secondary Right Ligament Zone"]
    notch = regions["Notch Tip Initiation Zone (r <= 50 um)"]
    primary = regions["Primary Ligament Corridor (Notch to Hole)"]

    # Quantitative proof of secondary ligament localization
    assert sec["share_of_area_weighted_integral_pct"] > 50.0, f"Expected >50%, got {sec['share_of_area_weighted_integral_pct']}"
    assert sec["share_of_l2_norm_pct"] > 95.0, f"Expected >95%, got {sec['share_of_l2_norm_pct']}"
    assert sec["miseseri_max_MPa"] > 1400.0

    # Depleted primary / notch error
    assert notch["share_of_area_weighted_integral_pct"] < 3.0, f"Expected <3%, got {notch['share_of_area_weighted_integral_pct']}"
    assert primary["share_of_area_weighted_integral_pct"] < 10.0, f"Expected <10%, got {primary['share_of_area_weighted_integral_pct']}"

    # 2. Strict Chronological Timeline Monotonicity Assertions
    with open(str(timeline_json), "r", encoding="utf-8") as f:
        tl = json.load(f)

    event_stages = tl["event_aligned_stages"]
    assert len(event_stages) == 8

    prev_c_u = -1.0
    prev_p_u = -1.0
    prev_c_step = None
    prev_p_step = None
    prev_c_f = -1
    prev_p_f = -1

    for stg in event_stages:
        cu = stg["coarse_u2_mm"]
        pu = stg["refined_u2_mm"]
        cf = stg["coarse_frame"]
        pf = stg["refined_frame"]
        c_step = stg["coarse_step"]
        p_step = stg["refined_step"]

        # Global displacement monotonicity
        assert cu >= prev_c_u, f"Coarse non-monotonic displacement: {cu} < {prev_c_u} at {stg['stage_id']}"
        assert pu >= prev_p_u, f"Refined non-monotonic displacement: {pu} < {prev_p_u} at {stg['stage_id']}"

        # Within-step frame index monotonicity
        if prev_c_step == c_step:
            assert cf >= prev_c_f, f"Coarse non-monotonic frame in {c_step}: {cf} < {prev_c_f} at {stg['stage_id']}"
        if prev_p_step == p_step:
            assert pf >= prev_p_f, f"Refined non-monotonic frame in {p_step}: {pf} < {prev_p_f} at {stg['stage_id']}"

        prev_c_u = cu
        prev_p_u = pu
        prev_c_step = c_step
        prev_p_step = p_step
        prev_c_f = cf
        prev_p_f = pf

    # 3. Displacement-Aligned Comparison Assertions
    with open(str(disp_csv), "r", encoding="utf-8") as f:
        disp_rows = list(csv.DictReader(f))

    assert len(disp_rows) == 8
    # Elastic parity at u = 0.0020 mm (< 1%)
    r002 = next(r for r in disp_rows if abs(float(r["target_u2_mm"]) - 0.0020) < 1e-4)
    assert abs(float(r002["delta_P_pct"])) < 1.0

    # Pre-critical parity at u = 0.0050 mm (< 1.5%)
    r005 = next(r for r in disp_rows if abs(float(r["target_u2_mm"]) - 0.0050) < 1e-4)
    assert abs(float(r005["delta_P_pct"])) < 1.5

    # 4. Controlled Recovery Plan Assertions
    with open(str(plan_json), "r", encoding="utf-8") as f:
        plan = json.load(f)

    assert plan["max_new_pbs_submissions"] == 0
    assert plan["production_fracture_rerun_authorized"] is False
    cands = {c["candidate_id"]: c for c in plan["candidates"]}
    assert "Candidate_C" in cands and cands["Candidate_C"]["priority"] == 1
    assert "Candidate_D" in cands and cands["Candidate_D"]["priority"] == 2
    assert "Candidate_B" in cands and cands["Candidate_B"]["role"] == "CONTROL_EARLY_LOCALIZATION"
    assert "Candidate_Terminal_Baseline" in cands


def test_f1683_controlled_multi_frame_recovery_and_spatial_localization():
    """
    Task F1683: Regression test verifying the multi-frame controlled recovery,
    disjoint partition spatial integration, and localization correction.
    Resolves independent review HND-a9ff3c192a8e.
    """
    comp_json = REPO_ROOT / "results" / "validation" / "f1683_four_frame_spatial_comparison.json"
    comp_csv = REPO_ROOT / "results" / "validation" / "f1683_four_frame_spatial_comparison.csv"
    fig_mises_pdf = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1683_four_frame_native_miseseri_comparison.pdf"
    fig_damage_pdf = REPO_ROOT / "MA_AdaptiveRemeshing_Report_2026" / "figures" / "f1683_four_frame_donor_damage_comparison.pdf"

    assert comp_json.exists(), f"Missing {comp_json}"
    assert comp_csv.exists(), f"Missing {comp_csv}"
    assert fig_mises_pdf.exists(), f"Missing {fig_mises_pdf}"
    assert fig_damage_pdf.exists(), f"Missing {fig_damage_pdf}"

    with open(str(comp_json), "r", encoding="utf-8") as f:
        records = json.load(f)

    assert len(records) == 4, f"Expected 4 candidates, got {len(records)}"
    rec_by_id = {r["candidate_id"]: r for r in records}

    # 1. Candidate B (Frame 50, u=0.0057 mm): Notch tip dominance, negligible secondary error
    cand_b = rec_by_id["Candidate_B"]
    assert cand_b["notch_tip_sq_l2_share_pct"] > 60.0
    assert cand_b["secondary_ligament_sq_l2_share_pct"] < 2.0
    assert cand_b["diag_primary_norm_ratio_pct"] > 65.0

    # 2. Candidate C (Frame 150, u=0.0071 mm): Primary corridor deflection, zero secondary ballooning
    cand_c = rec_by_id["Candidate_C"]
    assert cand_c["notch_tip_sq_l2_share_pct"] > 55.0
    assert cand_c["secondary_ligament_sq_l2_share_pct"] < 2.5
    assert cand_c["diag_primary_norm_ratio_pct"] > 65.0

    # 3. Candidate D (Frame 200, u=0.007756 mm): Hole cavity penetration, annular concentration
    cand_d = rec_by_id["Candidate_D"]
    assert cand_d["hole_annulus_sq_l2_share_pct"] > 40.0
    assert 5.0 <= cand_d["secondary_ligament_sq_l2_share_pct"] <= 15.0

    # 4. Terminal Baseline (Frame 337, u=0.009591 mm): Overwhelming secondary ligament over-refinement
    baseline = rec_by_id["Terminal_Baseline"]
    assert baseline["secondary_ligament_sq_l2_share_pct"] > 90.0
    assert (baseline["notch_tip_sq_l2_share_pct"] + baseline["primary_corridor_sq_l2_share_pct"]) < 1.0

    # 5. Exact 100% additive partition reconciliation check across all candidates
    for r in records:
        sq_l2_sum = (
            r["notch_tip_sq_l2_share_pct"] +
            r["primary_corridor_sq_l2_share_pct"] +
            r["hole_annulus_sq_l2_share_pct"] +
            r["secondary_ligament_sq_l2_share_pct"] +
            r["far_field_sq_l2_share_pct"]
        )
        assert abs(sq_l2_sum - 100.0) < 1e-3, f"Non-100% partition sum {sq_l2_sum} for {r['candidate_id']}"


def test_f1684_multistep_recovery_and_adapted_mesh_qualification():
    """
    Task F1684 Regression Test:
    Validates:
    1. Multi-Step Auxiliary Recovery bitwise equivalence and mathematical path-independence.
    2. Direct crack-path alignment metrics for Candidate C, Terminal Baseline, and Candidate D falsification.
    3. Three-way native adapted mesh resolution audit (Baseline vs Control B vs Experiment C).
    """
    # 1. Multi-Step Recovery Equivalence Audit
    audit_equiv_path = REPO_ROOT / "results" / "validation" / "f1684_multistep_recovery_audit.json"
    assert audit_equiv_path.exists(), f"Missing {audit_equiv_path}"
    with open(audit_equiv_path, "r") as f:
        eq_data = json.load(f)

    assert eq_data["mathematical_path_independence_proven"] is True
    s1 = eq_data["step1_candidate_c_equivalence"]
    assert s1["delta_rf_N"] == 0.0
    assert s1["rel_delta_rf_pct"] == 0.0
    assert s1["max_delta_s22_MPa"] == 0.0
    assert s1["max_delta_miseseri_MPa"] == 0.0

    s2 = eq_data["step2_terminal_baseline_equivalence"]
    assert s2["delta_rf_N"] == 0.0
    assert s2["rel_delta_rf_pct"] == 0.0
    assert s2["max_delta_s22_MPa"] < 1e-6
    assert s2["max_delta_miseseri_MPa"] == 0.0

    # 2. Crack-Path Alignment Metrics
    align_path = REPO_ROOT / "results" / "validation" / "f1684_crack_path_alignment_summary.json"
    assert align_path.exists(), f"Missing {align_path}"
    with open(align_path, "r") as f:
        align_data = json.load(f)

    c_align = align_data["Candidate_C"]
    assert c_align["primary_branch"]["miseseri_median_MPa"] > 250.0
    assert c_align["secondary_branch"]["miseseri_median_MPa"] < 50.0

    t_align = align_data["Terminal_Baseline"]
    assert t_align["secondary_branch"]["miseseri_median_MPa"] > 350.0
    assert t_align["primary_branch"]["miseseri_median_MPa"] < 100.0

    d_align = align_data["Candidate_D"]
    assert d_align["min_dist_to_crack_path_mm"] > 0.50
    assert d_align["far_field_false_positive_share_pct"] > 35.0

    # 3. Three-Way Adapted Mesh Regional Resolution Audit
    mesh_audit_path = REPO_ROOT / "results" / "validation" / "f1684_adapted_mesh_resolution_audit.json"
    assert mesh_audit_path.exists(), f"Missing {mesh_audit_path}"
    with open(mesh_audit_path, "r") as f:
        mesh_data = json.load(f)

    for mk, mobj in mesh_data.items():
        assert mobj["negative_jacobians"] == 0, f"Negative Jacobians in {mk}"
        assert mobj["zero_area_elements"] == 0, f"Zero area elements in {mk}"
        assert mobj["area_conservation_pct"] > 99.85, f"Area loss in {mk}"
        assert mobj["quads_pct"] > 96.0, f"Low quad fraction in {mk}"

    # Control B (Candidate C alone): 6,171 elements, sharp tip, far-field economy
    ctrl = mesh_data["control_cand_c_alone"]
    assert ctrl["total_elements"] == 6171
    z_ctrl = ctrl["zones"]
    assert z_ctrl["notch_tip_initiation"]["h_med_um"] < 3.0
    assert z_ctrl["notch_tip_initiation"]["h_min_um"] <= 1.50
    assert z_ctrl["far_field_bulk"]["h_med_um"] > 15.0

    # Experiment C (Combined): 21,569 elements, dual-corridor resolution
    exp = mesh_data["experiment_combined"]
    assert exp["total_elements"] == 21569
    z_exp = exp["zones"]
    assert z_exp["notch_tip_initiation"]["h_med_um"] < 3.0
    assert z_exp["notch_tip_initiation"]["h_min_um"] <= 1.50
    assert z_exp["secondary_ligament"]["h_med_um"] < 2.50
    assert z_exp["crack_centerline_corridor"]["pct_le_7p5_um"] == 100.0
    assert z_exp["crack_centerline_corridor"]["h_max_um"] < 7.50

















