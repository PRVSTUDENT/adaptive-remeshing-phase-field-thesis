# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_novel_inclined_notch_hole.py
=====================================================
Unit tests for the Method C Novel Complex Problem:
- Inclined Notch + Hole Mixed-Mode Curved Crack Benchmark
- Tests geometry, UEL source integrity, mesh quality gates,
  coupled deck assembly, cKDTree state transfer, and tip tracking.
"""

from __future__ import print_function, division
import os
import sys
import math
import json
import pytest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NOVEL_DIR = ROOT / "models" / "novel_inclined_notch_hole"
if str(NOVEL_DIR) not in sys.path:
    sys.path.insert(0, str(NOVEL_DIR))

import novel_single_job_orchestrator as orch
import generate_novel_inclined_notch_hole_mesh as mesh_gen
import novel_runtime as runtime


def test_frozen_uel_source_integrity():
    uel_path = ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for must exist"
    sha = orch.compute_sha256(uel_path)
    assert sha == orch.FROZEN_UEL_SHA256, (
        "Frozen UEL source SHA256 mismatch: got %s, expected %s" % (sha, orch.FROZEN_UEL_SHA256)
    )


def test_novel_geometry_specifications():
    assert orch.PLATE_W == 1.0
    assert orch.PLATE_H == 1.0
    assert orch.NOTCH_START_X == 0.0
    assert orch.NOTCH_START_Y == 0.5
    assert math.isclose(orch.NOTCH_TIP_X, 0.5 * math.cos(math.pi / 4.0), rel_tol=1e-6)
    assert math.isclose(orch.NOTCH_TIP_Y, 0.5 + 0.5 * math.sin(math.pi / 4.0), rel_tol=1e-6)
    assert orch.HOLE_X == 0.65
    assert orch.HOLE_Y == 0.65
    assert orch.HOLE_R == 0.10

    # Distance from notch tip to hole center
    dx = orch.HOLE_X - orch.NOTCH_TIP_X
    dy = orch.HOLE_Y - orch.NOTCH_TIP_Y
    dist_to_center = math.hypot(dx, dy)
    dist_to_boundary = dist_to_center - orch.HOLE_R
    assert 0.35 < dist_to_center < 0.37
    assert 0.25 < dist_to_boundary < 0.27


def test_material_parameters_and_resolution():
    assert orch.BENCHMARK_E_GPA == 210.0
    assert orch.BENCHMARK_NU == 0.30
    assert orch.BENCHMARK_L0_MM == 0.0075
    assert orch.BENCHMARK_GC_KN_MM == 0.0027
    assert orch.BENCHMARK_K_RES == 1.0e-7
    assert orch.H_REF_MM == 0.0035
    assert orch.H_REF_MM <= orch.BENCHMARK_L0_MM / 2.0, "h_ref must resolve l0/2"


def test_corridor_specification_and_wake_preservation():
    # Initial state at notch root (narrow damage-following band)
    spec0 = mesh_gen.compute_corridor_spec(orch.NOTCH_TIP_X, orch.NOTCH_TIP_Y)
    assert spec0["x_min"] <= orch.NOTCH_TIP_X
    assert spec0["x_max"] >= orch.NOTCH_TIP_X
    assert spec0["y_min"] <= orch.NOTCH_TIP_Y
    assert spec0["y_max"] >= orch.NOTCH_TIP_Y
    assert spec0["domain_area_fraction_pct"] < 2.0, "Narrow band must occupy < 2.0% of domain"
    assert spec0["half_width"] == 0.025, "Band half-width must be 0.025 mm (~3.3 * l0)"

    # Advancing state curving down-right towards hole
    adv_tip_x = 0.50
    adv_tip_y = 0.75
    history = [(orch.NOTCH_TIP_X, orch.NOTCH_TIP_Y), (0.42, 0.80)]
    spec1 = mesh_gen.compute_corridor_spec(adv_tip_x, adv_tip_y, tip_history=history)

    # Wake preservation: initial notch root must remain enclosed
    assert spec1["x_min"] <= orch.NOTCH_TIP_X
    assert spec1["y_max"] >= orch.NOTCH_TIP_Y
    # Forward advance: ahead of new tip
    assert spec1["x_max"] >= adv_tip_x
    assert spec1["domain_area_fraction_pct"] < 2.0, "Advancing band must remain < 2.0% of domain"


def test_physical_mesh_quality_audit():
    audit_file = NOVEL_DIR / "PK_METHOD_C_NOVEL_COARSE_PHYS_audit.json"
    assert audit_file.exists(), "Physical mesh audit file must exist"
    data = json.loads(audit_file.read_text())

    assert data["total_elements"] < 35000, "Element count must be bounded < 35,000"
    assert data["quad_fraction_pct"] >= 85.0, "Quad fraction must be >= 85%"
    assert data["min_jacobian_det"] > 0.0, "Minimum Jacobian det must be strictly positive"
    assert data["max_aspect_ratio"] <= 5.0, "Aspect ratio must be <= 5.0"
    assert data["median_h_corridor_mm"] <= orch.BENCHMARK_L0_MM / 2.0 + 1e-4

    gates = data["gates"]
    assert gates["gate01_positive_jacobian"] is True
    assert gates["gate02_quad_fraction_ge_85"] is True
    assert gates["gate03_aspect_ratio_le_5"] is True
    assert gates["gate04_size_le_l0_half"] is True
    assert gates["gate05_bounded_under_35k"] is True


def test_coupled_input_deck_assembly(tmp_path):
    phys_file = NOVEL_DIR / "PK_METHOD_C_NOVEL_COARSE_PHYS.inp"
    assert phys_file.exists(), "Coarse physical mesh file must exist"
    nodes, quads, tris, _ = orch.parse_physical_mesh(str(phys_file))
    assert len(nodes) > 1000
    assert len(quads) > 1000

    test_deck = tmp_path / "TEST_NOVEL_COUPLED.inp"
    orch.assemble_novel_coupled_deck(
        str(test_deck), nodes, quads, tris,
        donor_uy=0.0, target_uy=0.0045, is_coarse=True
    )
    assert test_deck.exists()

    content = test_deck.read_text()
    assert "*USER ELEMENT, NODES=4, TYPE=U1" in content
    assert "*USER ELEMENT, NODES=4, TYPE=U2" in content
    assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in content
    assert "*NSET, NSET=N_BOTTOM" in content
    assert "*NSET, NSET=N_TOP" in content
    assert "*NSET, NSET=N_PIN" in content
    assert "*NSET, NSET=N_RP" in content
    assert "*EQUATION" in content
    assert "999999, 2, -1.0" in content
    assert "*STEP, NAME=Step-1" in content

    # Check property order
    runtime.validate_uel_properties(str(test_deck), len(quads) + len(tris))


def test_ckdtree_state_transfer():
    # Donor grid
    donor_nodes = {
        1: (0.35, 0.85),
        2: (0.36, 0.85),
        3: (0.36, 0.86),
        4: (0.35, 0.86),
    }
    donor_quads = {1: [1, 2, 3, 4]}
    donor_tris = {}
    donor_d = {1: 0.95, 2: 0.90, 3: 0.85, 4: 0.80}
    donor_h_gp = {(1, 1): 0.05, (1, 2): 0.04, (1, 3): 0.03, (1, 4): 0.02}

    # Receiver grid (slightly shifted)
    recip_nodes = {
        10: (0.351, 0.851),
        11: (0.359, 0.851),
        12: (0.359, 0.859),
        13: (0.351, 0.859),
    }
    recip_quads = {100: [10, 11, 12, 13]}
    recip_tris = {}

    rd, rh = runtime.transfer_state_fields(
        donor_nodes, donor_quads, donor_tris, donor_d, donor_h_gp,
        recip_nodes, recip_quads, recip_tris
    )

    assert len(rd) == 4
    assert max(rd.values()) == 0.95
    assert len(rh) == 4
    for v in rh.values():
        assert 0.02 <= v <= 0.05


def test_connected_tip_tracking():
    nodes = {
        1: (0.353553, 0.853553),
        2: (0.36, 0.85),
        3: (0.38, 0.84),
        4: (0.42, 0.82),
        5: (0.46, 0.79),
        10: (0.1, 0.1)  # Unconnected damaged artifact
    }
    elements = {
        1: [1, 2],
        2: [2, 3],
        3: [3, 4],
        4: [4, 5],
        5: [10]
    }
    # Crack along 1 -> 2 -> 3 -> 4 -> 5
    damage = {1: 0.99, 2: 0.98, 3: 0.95, 4: 0.92, 5: 0.91, 10: 0.99}

    tip, boundary = runtime.connected_tip(nodes, elements, damage, threshold=0.90)
    assert tip == (0.46, 0.79), "Tip should be the farthest connected damaged node from root"
    assert boundary is False, "Tip has not reached boundary yet"


def test_novel_campaign_results_and_transfer_gates():
    results_dir = NOVEL_DIR / "campaign_results"
    assert results_dir.exists(), "campaign_results directory must exist"

    # All 9 cycles must exist
    for c in range(9):
        job = "PK_METHOD_C_NOVEL_COARSE_JOB1" if c == 0 else "PK_METHOD_C_NOVEL_CYCLE%d" % c
        sum_file = results_dir / (job + "_SUMMARY.json")
        assert sum_file.exists(), "%s summary must exist" % job
        data = json.loads(sum_file.read_text())
        assert data["status"] == "CONVERGED_AUDITED"
        assert data["cycle"] == c

        if c > 0:
            gr = data["gate_results"]
            assert gr["force_continuity_pass"] is True, "Cycle %d force continuity failed" % c
            assert abs(gr["force_continuity_delta_pct"]) <= 5.0, "Cycle %d force delta > 5%%" % c
            assert gr["global_max_damage_nonhealing_pass"] is True

    # Terminal cycle checks
    term_file = results_dir / "PK_METHOD_C_NOVEL_CYCLE8_SUMMARY.json"
    term = json.loads(term_file.read_text())
    assert term["completion"] is True
    assert term["completion_reason"] == "CONNECTED_DAMAGE_REACHED_BOUNDARY"
    assert term["peak_rf2_kn"] >= 0.80
    assert term["terminal_rf2_kn"] <= 0.35  # >50% post-peak load drop
    assert term["max_damage"] >= 0.999

    # Hole penetration check: tip must be at hole boundary (r ~ 0.10 mm from (0.65, 0.65))
    tip_x, tip_y = term["tip_mm"]
    dist_to_hole = math.hypot(tip_x - orch.HOLE_X, tip_y - orch.HOLE_Y)
    assert abs(dist_to_hole - orch.HOLE_R) <= 0.005, (
        "Tip should reach hole boundary: got dist %.4f, expected %.4f" % (dist_to_hole, orch.HOLE_R)
    )


def test_novel_campaign_image_manifest_provenance():
    manifest_path = NOVEL_DIR / "campaign_results" / "image_manifest.json"
    assert manifest_path.exists(), "image_manifest.json must exist"
    entries = json.loads(manifest_path.read_text())
    assert len(entries) == 9, "Must contain all 9 cycle image entries (Cycles 0 to 8)"

    for entry in entries:
        assert "cycle" in entry
        assert "path" in entry
        assert "commit" in entry
        assert "url" in entry
        assert "image_sha256" in entry
        assert entry["source_sha256"] == orch.FROZEN_UEL_SHA256
        assert (ROOT / entry["path"]).exists(), "Image file must exist: " + entry["path"]

