# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_complex_double_notch.py
================================================
Unit test suite for Problem 2 (Double Notch Symmetrical Crack Coalescence)
Method C Adaptive Remeshing Framework.
"""

import math
import os
import sys
import json
from pathlib import Path
import pytest
import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MODEL_DIR = REPO_ROOT / "models" / "complex_double_notch"
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

import generate_double_notch_mesh as gen
import double_notch_single_job_orchestrator as orch
import double_notch_runtime as rt


def test_geometry_landmarks():
    """Verify Problem 2 geometry landmarks match the authorized double-notch specification."""
    assert gen.PLATE_W == 1.0
    assert gen.PLATE_H == 1.0

    # Left Notch
    assert gen.NOTCH1_START_X == 0.0
    assert gen.NOTCH1_START_Y == 0.50
    assert gen.NOTCH1_LEN == 0.50
    assert math.isclose(gen.NOTCH1_ANGLE_RAD, math.pi / 4.0, rel_tol=1e-6)
    assert math.isclose(gen.NOTCH1_TIP_X, 0.5 * math.cos(math.pi / 4.0), rel_tol=1e-5)
    assert math.isclose(gen.NOTCH1_TIP_Y, 0.5 + 0.5 * math.sin(math.pi / 4.0), rel_tol=1e-5)

    # Right Notch (Mirror about x = 0.5)
    assert gen.NOTCH2_START_X == 1.0
    assert gen.NOTCH2_START_Y == 0.50
    assert gen.NOTCH2_LEN == 0.50
    assert math.isclose(gen.NOTCH2_ANGLE_RAD, 3.0 * math.pi / 4.0, rel_tol=1e-6)
    assert math.isclose(gen.NOTCH2_TIP_X, 1.0 - 0.5 * math.cos(math.pi / 4.0), rel_tol=1e-5)
    assert math.isclose(gen.NOTCH2_TIP_Y, 0.5 + 0.5 * math.sin(math.pi / 4.0), rel_tol=1e-5)

    # Symmetrical properties
    assert math.isclose(gen.NOTCH1_TIP_X + gen.NOTCH2_TIP_X, 1.0, rel_tol=1e-6)
    assert math.isclose(gen.NOTCH1_TIP_Y, gen.NOTCH2_TIP_Y, rel_tol=1e-6)

    # Initial ligament between notch tips
    ligament = gen.NOTCH2_TIP_X - gen.NOTCH1_TIP_X
    assert math.isclose(ligament, 0.292893, rel_tol=1e-4)
    assert math.isclose(gen.INTER_NOTCH_LIGAMENT, ligament, rel_tol=1e-6)


def test_physics_and_material_constants():
    """Verify material constants and mesh sizing comply with Phase-Field theory."""
    assert orch.BENCHMARK_E_GPA == 210.0
    assert orch.BENCHMARK_NU == 0.30
    assert orch.BENCHMARK_L0_MM == 0.0075
    assert orch.BENCHMARK_GC_KN_MM == 0.0027
    assert orch.BENCHMARK_K_RES == 1e-7

    # Sizing
    assert gen.H_REF == 0.0035
    assert gen.H_REF <= (gen.L0 / 2.0)
    assert gen.H_BG == 0.035
    assert math.isclose(gen.BAND_HALF_WIDTH, 0.025, rel_tol=1e-6)


def test_corridor_polygons_and_refined_area():
    """Verify dual narrow bands form narrow corridors with domain area fraction < 3%."""
    spec = gen.compute_corridor_spec()
    assert spec["corridor_type"] == "DOUBLE_NOTCH_DUAL_NARROW_BAND"
    assert "left_band" in spec
    assert "right_band" in spec

    l_area = spec["left_band"]["area_mm2"]
    r_area = spec["right_band"]["area_mm2"]
    total_area = spec["total_refined_area_mm2"]

    assert l_area < 0.015, "Left band area must be < 1.5% of 1.0 mm^2 plate"
    assert r_area < 0.015, "Right band area must be < 1.5% of 1.0 mm^2 plate"
    assert total_area < 0.030, "Total refined area must be < 3.0% of 1.0 mm^2 plate"
    assert spec["domain_area_fraction_pct"] < 3.0


def test_bridged_corridor_when_tips_close():
    """Verify bridged narrow band activates when tip separation <= 0.15 mm and stays < 3.0%."""
    spec = gen.compute_corridor_spec(
        tip1_x=0.434, tip1_y=0.840,
        tip2_x=0.566, tip2_y=0.839
    )
    assert spec["corridor_type"] == "DOUBLE_NOTCH_BRIDGED_NARROW_BAND"
    assert "bridged_band" in spec
    assert spec["domain_area_fraction_pct"] < 3.0
    poly = spec["bridged_band"]["polygon_vertices"]
    # Midpoint of ligament (0.50, 0.84) must be inside the bridged corridor
    assert gen.point_in_polygon(0.50, 0.84, poly) is True


def test_point_in_polygon():
    """Verify ray-casting point-in-polygon helper."""
    poly = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert gen.point_in_polygon(0.5, 0.5, poly) is True
    assert gen.point_in_polygon(1.5, 0.5, poly) is False
    assert gen.point_in_polygon(-0.5, 0.5, poly) is False

    # Point near left notch tip inside left band
    spec = gen.compute_corridor_spec()
    assert gen.point_in_polygon(gen.NOTCH1_TIP_X + 0.01, gen.NOTCH1_TIP_Y, spec["left_band"]["polygon_vertices"]) is True
    # Point near right notch tip inside right band
    assert gen.point_in_polygon(gen.NOTCH2_TIP_X - 0.01, gen.NOTCH2_TIP_Y, spec["right_band"]["polygon_vertices"]) is True
    # Point at center of plate far from bands
    assert gen.point_in_polygon(0.5, 0.2, spec["left_band"]["polygon_vertices"]) is False
    assert gen.point_in_polygon(0.5, 0.2, spec["right_band"]["polygon_vertices"]) is False


def test_element_jacobian_and_aspect_ratio():
    """Verify quadrature Jacobian and aspect ratio formulas."""
    unit_quad = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    detJ, ar = gen.compute_element_jacobian_and_aspect(unit_quad)
    assert math.isclose(detJ, 0.25, rel_tol=1e-5)
    assert math.isclose(ar, 1.0, rel_tol=1e-5)

    unit_tri = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    detJ_tri, ar_tri = gen.compute_element_jacobian_and_aspect(unit_tri)
    assert math.isclose(detJ_tri, 1.0, rel_tol=1e-5)
    assert ar_tri <= 2.0


def test_frozen_uel_sha256():
    """Verify bitwise frozen UEL source CE8D5EDC... is preserved."""
    sub_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert sub_path.exists(), "f42_mixed_uel.for must exist"
    actual_hash = orch.compute_sha256(sub_path)
    assert actual_hash == orch.FROZEN_UEL_SHA256, (
        "Frozen UEL source hash mismatch! Expected %s, got %s" % (orch.FROZEN_UEL_SHA256, actual_hash)
    )


def test_coarse_mesh_and_quality_gates():
    """Verify generated coarse physical mesh passes all 5 quality gates."""
    audit_file = MODEL_DIR / "campaign_results" / "PK_METHOD_C_DOUBLE_NOTCH_COARSE_PHYS_audit.json"
    assert audit_file.exists(), "Coarse audit file must exist"
    with open(audit_file, "r") as f:
        audit = json.load(f)

    assert audit["gates"]["gate01_positive_jacobian"] is True
    assert audit["gates"]["gate02_quad_fraction_ge_85"] is True
    assert audit["gates"]["gate03_aspect_ratio_le_5"] is True
    assert audit["gates"]["gate04_size_le_l0_half"] is True
    assert audit["gates"]["gate05_bounded_under_35k"] is True

    assert audit["min_jacobian_det"] > 0.0
    assert audit["quad_fraction_pct"] >= 85.0
    assert audit["max_aspect_ratio"] <= 5.0
    assert audit["total_elements"] < 35000
    assert audit["corridor_spec"]["domain_area_fraction_pct"] < 3.0


def test_two_tip_tracking_and_coalescence_detector():
    """Verify two-tip tracker accurately detects tip progression and coalescence."""
    # Synthetic grid of nodes across the ligament y = 0.85, x in [0.35, 0.65]
    nodes = {}
    elements = {}
    x_coords = np.linspace(0.35, 0.65, 31)
    for i, x in enumerate(x_coords, start=1):
        nodes[i] = (x, 0.853553)

    # 1D line of connectivity
    for i in range(1, 31):
        elements[i] = [i, i + 1]

    # Case A: Disconnected cracks (tip 1 reaches x=0.42, tip 2 reaches x=0.58)
    damage_disconnected = {}
    for i, x in enumerate(x_coords, start=1):
        if x <= 0.42 or x >= 0.58:
            damage_disconnected[i] = 0.95
        else:
            damage_disconnected[i] = 0.05

    t1, t2, coalesced = rt.connected_tips(nodes, elements, damage_disconnected)
    assert coalesced is False
    assert math.isclose(t1[0], 0.42, abs_tol=0.015)
    assert math.isclose(t2[0], 0.58, abs_tol=0.015)

    # Case B: Coalesced crack (damage >= 0.5 bridging all nodes)
    damage_coalesced = {i: 0.95 for i in range(1, 32)}
    t1_c, t2_c, coalesced_c = rt.connected_tips(nodes, elements, damage_coalesced)
    assert coalesced_c is True


def test_individual_crack_arc_length():
    """Verify separate arc lengths s1 and s2 are computed without combining chord sums."""
    root1 = (orch.NOTCH1_TIP_X, orch.NOTCH1_TIP_Y)
    root2 = (orch.NOTCH2_TIP_X, orch.NOTCH2_TIP_Y)

    history1 = [(0.38, 0.85), (0.42, 0.84), (0.46, 0.83)]
    history2 = [(0.62, 0.85), (0.58, 0.84), (0.54, 0.83)]

    s1 = orch.compute_individual_crack_arc_length(history1, root1)
    s2 = orch.compute_individual_crack_arc_length(history2, root2)

    assert s1 > 0.10 and s1 < 0.20
    assert s2 > 0.10 and s2 < 0.20
    # Both cracks have symmetrical progression
    assert math.isclose(s1, s2, rel_tol=0.05)


def test_completion_criteria():
    """Verify all Problem 2 completion conditions."""
    tip1 = (0.45, 0.85)
    tip2 = (0.55, 0.85)

    # 1. Coalescence triggered
    done, reason = rt.completion(peak=0.75, force=0.50, tip1=tip1, tip2=tip2, coalesced=True)
    assert done is True
    assert reason == "CONNECTED_DAMAGE_COALESCENCE"

    # 2. Force drop triggered
    done, reason = rt.completion(peak=0.75, force=0.02, tip1=tip1, tip2=tip2, coalesced=False)
    assert done is True
    assert reason == "REACTION_FORCE_BELOW_5PCT_PEAK"

    # 3. Outer boundary reach
    tip_boundary = (0.01, 0.85)
    done, reason = rt.completion(peak=0.75, force=0.50, tip1=tip_boundary, tip2=tip2, coalesced=False)
    assert done is True
    assert reason == "CONNECTED_DAMAGE_REACHED_BOUNDARY"

    # 4. In progress
    done, reason = rt.completion(peak=0.75, force=0.60, tip1=tip1, tip2=tip2, coalesced=False)
    assert done is False
    assert reason == "IN_PROGRESS"


def test_state_transfer_ckdtree():
    """Verify cKDTree nearest-neighbor state transfer interpolates damage and history."""
    donor_nodes = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
    donor_quads = {1: [1, 2, 3, 4]}
    donor_tris = {}
    donor_d = {1: 0.1, 2: 0.2, 3: 0.8, 4: 0.9}
    donor_h_gp = {(1, 1): 10.0, (1, 2): 20.0, (1, 3): 80.0, (1, 4): 90.0}

    recip_nodes = {10: (0.05, 0.05), 20: (0.95, 0.95)}
    recip_quads = {100: [10, 10, 20, 20]}
    recip_tris = {}

    rd, rh = rt.transfer_state_fields(donor_nodes, donor_quads, donor_tris, donor_d, donor_h_gp,
                                      recip_nodes, recip_quads, recip_tris)
    assert math.isclose(rd[10], 0.1, abs_tol=1e-5)
    assert math.isclose(rd[20], 0.8, abs_tol=1e-5)
    assert (100, 1) in rh


def test_report_and_summary_file_hashes():
    """Verify Problem 2 validation report and all cycle summary file SHA-256 hashes."""
    import hashlib

    report_path = REPO_ROOT / "docs" / "validation" / "METHOD_C_COMPLEX_PROBLEM2_DOUBLE_NOTCH_REPORT.md"
    assert report_path.exists(), "Problem 2 report must exist"
    report_sha = hashlib.sha256(report_path.read_bytes()).hexdigest().upper()
    assert report_sha == "9DF9293264449AF9E7E1EBF0BDDC23893FAD388B2745C82EF4A7F394838F29D8"

    res_dir = REPO_ROOT / "models" / "complex_double_notch" / "campaign_results"
    expected_hashes = {
        "PK_METHOD_C_DOUBLE_NOTCH_COARSE_JOB1_SUMMARY.json": "05F1F467C0156F8E5582F719CAAF8DE8CEDF86B75BAB194A0C4D16A253F76FC4",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE1_SUMMARY.json": "1307F5C0F0669D96E04BD5104AB0DFD3C8D62A3F0D81CB89251D60FA36EA74A1",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE2_SUMMARY.json": "95869931CE70B2EDD08C2FC5A1BF88A50DF3AEA5E82BF8B948A6BEE943758A8B",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE3_SUMMARY.json": "246DA5E38CD6C2E251D51D66A53029A24BB8B9AF9F9B381E086F7D98D679BA32",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE4_SUMMARY.json": "A201834BBC75E93F8429082D43ABA72A245FDEB3F6D9549B49D3FFA61BC01C91",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE5_SUMMARY.json": "C217AA3166099CA0528F09A9183B8F95EC559331DCD9ADAA371020480990F640",
        "PK_METHOD_C_DOUBLE_NOTCH_CYCLE6_SUMMARY.json": "5E61BF279A39C8B802985E2796A28679C1CCD1445E36FA32A98819244C2D1D10",
    }
    for filename, expected_hash in expected_hashes.items():
        summary_file = res_dir / filename
        assert summary_file.exists(), f"Summary file {filename} must exist"
        file_sha = hashlib.sha256(summary_file.read_bytes()).hexdigest().upper()
        assert file_sha == expected_hash, f"Hash mismatch for {filename}: {file_sha} != {expected_hash}"

