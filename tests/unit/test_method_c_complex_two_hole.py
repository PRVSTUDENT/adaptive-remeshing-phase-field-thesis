# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_complex_two_hole.py
============================================
Unit test suite for Problem 1 (Inclined Notch + Two Holes in Series)
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
MODEL_DIR = REPO_ROOT / "models" / "complex_two_hole"
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

import generate_two_hole_mesh as gen
import two_hole_single_job_orchestrator as orch
import two_hole_runtime as rt


def test_geometry_landmarks():
    """Verify Problem 1 geometry landmarks match the authorized specification."""
    assert gen.PLATE_W == 1.0
    assert gen.PLATE_H == 1.0
    assert gen.NOTCH_START_X == 0.0
    assert gen.NOTCH_START_Y == 0.5
    assert gen.NOTCH_LEN == 0.5
    assert math.isclose(gen.NOTCH_ANGLE_RAD, math.pi / 4.0, rel_tol=1e-6)
    assert math.isclose(gen.NOTCH_TIP_X, 0.5 * math.cos(math.pi / 4.0), rel_tol=1e-5)
    assert math.isclose(gen.NOTCH_TIP_Y, 0.5 + 0.5 * math.sin(math.pi / 4.0), rel_tol=1e-5)

    # Hole 1
    assert gen.HOLE1_X == 0.65
    assert gen.HOLE1_Y == 0.65
    assert gen.HOLE1_R == 0.10

    # Hole 2
    assert gen.HOLE2_X == 0.87
    assert gen.HOLE2_Y == 0.62
    assert gen.HOLE2_R == 0.06

    # Ligament between Hole 1 and Hole 2
    dist_c = math.hypot(0.87 - 0.65, 0.62 - 0.65)
    ligament = dist_c - (0.10 + 0.06)
    assert math.isclose(dist_c, 0.222036, rel_tol=1e-4)
    assert math.isclose(ligament, 0.062036, rel_tol=1e-4)
    assert math.isclose(gen.INTER_HOLE_LIGAMENT, ligament, rel_tol=1e-6)


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
    """Verify narrow bands form narrow corridors with domain area fraction < 3%."""
    spec = gen.compute_corridor_spec()
    assert spec["corridor_type"] == "TWO_HOLE_DUAL_NARROW_BAND"
    assert "primary_band" in spec
    assert "secondary_band" in spec

    p_area = spec["primary_band"]["area_mm2"]
    s_area = spec["secondary_band"]["area_mm2"]
    total_area = spec["total_refined_area_mm2"]

    assert p_area < 0.020, "Primary band area must be < 2% of 1.0 mm^2 plate"
    assert s_area < 0.015, "Secondary band area must be < 1.5% of 1.0 mm^2 plate"
    assert total_area < 0.030, "Total refined area must be < 3% of 1.0 mm^2 plate"
    assert spec["domain_area_fraction_pct"] < 3.0


def test_point_in_polygon():
    """Verify ray-casting point-in-polygon helper."""
    poly = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    assert gen.point_in_polygon(0.5, 0.5, poly) is True
    assert gen.point_in_polygon(1.5, 0.5, poly) is False
    assert gen.point_in_polygon(-0.5, 0.5, poly) is False

    # Inside secondary band (inter-hole ligament at x=0.78, y=0.635)
    s_spec = gen.build_secondary_narrow_band_polygon()
    assert gen.point_in_polygon(0.78, 0.635, s_spec["polygon_vertices"]) is True
    # Far outside secondary band
    assert gen.point_in_polygon(0.1, 0.1, s_spec["polygon_vertices"]) is False


def test_element_jacobian_and_aspect_ratio():
    """Verify quadrature Jacobian and aspect ratio formulas."""
    # Unit quad: [0, 1] x [0, 1]
    unit_quad = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    detJ, ar = gen.compute_element_jacobian_and_aspect(unit_quad)
    assert math.isclose(detJ, 0.25, rel_tol=1e-5)
    assert math.isclose(ar, 1.0, rel_tol=1e-5)

    # Unit right triangle: (0,0), (1,0), (0,1)
    unit_tri = [(0.0, 0.0), (1.0, 0.0), (0.0, 1.0)]
    detJ_tri, ar_tri = gen.compute_element_jacobian_and_aspect(unit_tri)
    assert math.isclose(detJ_tri, 1.0, rel_tol=1e-5)
    assert ar_tri <= 2.0


def test_frozen_uel_sha256():
    """Verify bitwise frozen UEL source CE8D5EDC... is preserved."""
    sub_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert sub_path.exists()
    uel_hash = orch.compute_sha256(str(sub_path))
    assert uel_hash == orch.FROZEN_UEL_SHA256


def test_tip_tracking_and_completion_criteria():
    """Verify crack tip tracking and completion evaluation."""
    # Peak force 0.80 kN
    peak = 0.80

    # 1. In-progress state
    tip1_info = ((0.45, 0.75), False)
    tip2_info = (None, False)
    is_done, reason = rt.completion(peak, 0.70, tip1_info, tip2_info)
    assert is_done is False
    assert reason == "IN_PROGRESS"

    # 2. Crack 2 reaches Hole 2
    tip1_info = ((0.625, 0.747), True)  # Crack 1 entered Hole 1
    tip2_info = ((0.81, 0.62), True)   # Crack 2 entered Hole 2 boundary
    is_done, reason = rt.completion(peak, 0.40, tip1_info, tip2_info)
    assert is_done is True
    assert reason == "CONNECTED_DAMAGE_ENTERED_HOLE2"

    # 3. Load drop below 5% of peak
    tip1_info = ((0.50, 0.70), False)
    tip2_info = (None, False)
    is_done, reason = rt.completion(peak, 0.03, tip1_info, tip2_info)
    assert is_done is True
    assert reason == "REACTION_FORCE_BELOW_5PCT_PEAK"

    # 4. Crack reaches plate boundary
    tip1_info = ((0.99, 0.65), False)
    tip2_info = (None, False)
    is_done, reason = rt.completion(peak, 0.30, tip1_info, tip2_info)
    assert is_done is True
    assert reason == "CONNECTED_DAMAGE_REACHED_BOUNDARY"


def test_state_transfer_ckdtree():
    """Verify cKDTree nearest-neighbor interpolation preserves values."""
    donor_nodes = {1: (0.0, 0.0), 2: (0.1, 0.0), 3: (0.1, 0.1), 4: (0.0, 0.1)}
    donor_quads = {1: [1, 2, 3, 4]}
    donor_tris = {}
    donor_d = {1: 0.1, 2: 0.2, 3: 0.95, 4: 0.8}
    donor_h = {(1, 1): 1e-4, (1, 2): 2e-4, (1, 3): 5e-4, (1, 4): 4e-4}

    recip_nodes = {10: (0.095, 0.095), 20: (0.01, 0.01)}
    recip_quads = {100: [10, 20, 20, 10]}
    recip_tris = {}

    r_d, r_h = rt.transfer_state_fields(
        donor_nodes, donor_quads, donor_tris, donor_d, donor_h,
        recip_nodes, recip_quads, recip_tris
    )

    # Node 10 is very close to Node 3 (d=0.95)
    assert math.isclose(r_d[10], 0.95, rel_tol=1e-5)
    # Node 20 is very close to Node 1 (d=0.10)
    assert math.isclose(r_d[20], 0.10, rel_tol=1e-5)


def test_input_deck_generation_syntax(tmp_path):
    """Verify assemble_two_hole_coupled_deck generates compliant 3-layer Abaqus cards."""
    deck_path = tmp_path / "test_two_hole.inp"
    r_nodes = {
        1: (0.0, 0.0),
        2: (0.5, 0.0),
        3: (1.0, 0.0),
        4: (0.0, 1.0),
        5: (0.5, 1.0),
        6: (1.0, 1.0)
    }
    r_quads = {
        1: [1, 2, 5, 4],
        2: [2, 3, 6, 5]
    }
    r_tris = {}

    orch.assemble_two_hole_coupled_deck(
        str(deck_path),
        r_nodes,
        r_quads,
        r_tris,
        donor_uy=0.0045,
        target_uy=0.0050,
        is_coarse=False,
        transferred_damage={1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1, 6: 0.1},
        transferred_history={(1, 1): 1e-4, (1, 2): 1e-4, (1, 3): 1e-4, (1, 4): 1e-4,
                             (2, 1): 1e-4, (2, 2): 1e-4, (2, 3): 1e-4, (2, 4): 1e-4}
    )

    assert deck_path.exists()
    content = deck_path.read_text()
    assert "*HEADING" in content
    assert "*USER ELEMENT, NODES=4, TYPE=U1" in content
    assert "*USER ELEMENT, NODES=4, TYPE=U2" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in content
    assert "*NSET, NSET=N_BOTTOM" in content
    assert "*NSET, NSET=N_TOP" in content
    assert "*NSET, NSET=N_PIN" in content
    assert "*NSET, NSET=N_RP" in content
    assert "*EQUATION" in content
    assert "*STATIC" in content
    assert "*STATIC, RIKS" in content


def test_campaign_execution_evidence_and_gate_compliance():
    """Verify that all 6 cycle summaries exist, pass the <=5% gate, and complete via Hole 2."""
    results_dir = REPO_ROOT / "models" / "complex_two_hole" / "campaign_results"
    assert results_dir.exists()

    coarse_sum = results_dir / "PK_METHOD_C_TWO_HOLE_COARSE_JOB1_SUMMARY.json"
    assert coarse_sum.exists()
    with open(coarse_sum, "r") as f:
        c0 = json.load(f)
    assert c0["status"] == "CONVERGED_AUDITED"
    assert c0["mesh_elements"] == 6348

    # Cycles 1 to 5
    for c in range(1, 6):
        sum_path = results_dir / f"PK_METHOD_C_TWO_HOLE_CYCLE{c}_SUMMARY.json"
        assert sum_path.exists()
        with open(sum_path, "r") as f:
            data = json.load(f)
        assert data["status"] == "CONVERGED_AUDITED"
        delta_pct = data["gate_results"]["force_continuity_delta_pct"]
        assert abs(delta_pct) <= 5.0, f"Cycle {c} force jump exceeded 5%: {delta_pct}"
        assert data["gate_results"]["force_continuity_pass"] is True
        assert data["gate_results"]["global_max_damage_nonhealing_pass"] is True
        assert data["mesh_elements"] < 35000

    # Terminal Cycle 5 stopping criterion
    with open(results_dir / "PK_METHOD_C_TWO_HOLE_CYCLE5_SUMMARY.json", "r") as f:
        c5 = json.load(f)
    assert c5["completion_reason"] == "CONNECTED_DAMAGE_ENTERED_HOLE2"
    assert c5["tip2_mm"] is not None
    # Distance to Hole 2 center (0.87, 0.62) must be <= Hole 2 radius (0.06 mm)
    t2_x, t2_y = c5["tip2_mm"]
    dist_h2 = math.hypot(t2_x - 0.87, t2_y - 0.62)
    assert dist_h2 <= 0.061, f"Tip 2 ({t2_x}, {t2_y}) not inside Hole 2 radius: dist={dist_h2}"


def test_campaign_synthesis_figures_and_manifest():
    """Verify presence and validity of publication synthesis figures and image manifest."""
    import json
    results_dir = REPO_ROOT / "models" / "complex_two_hole" / "campaign_results"
    
    grid_img = results_dir / "fig_two_hole_progression_grid.png"
    synth_img = results_dir / "fig_two_hole_synthesis.png"
    gif_img = results_dir / "two_hole_progression.gif"
    manifest_f = results_dir / "image_manifest.json"

    assert grid_img.exists() and grid_img.stat().st_size > 50000
    assert synth_img.exists() and synth_img.stat().st_size > 50000
    assert gif_img.exists() and gif_img.stat().st_size > 50000
    assert manifest_f.exists()

    with open(manifest_f, "r") as f:
        manifest = json.load(f)
    assert len(manifest) == 6
    for entry in manifest:
        assert entry["commit"] != "PENDING"
        assert len(entry["commit"]) == 40
        assert len(entry["image_sha256"]) == 64
        assert len(entry["mesh_sha256"]) == 64
        assert entry["source_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

