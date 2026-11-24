# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_lpanel.py
==================================
Unit test suite for Method C L-Panel Benchmark Setup and Verification:
- Frozen UEL bitwise integrity (CE8D5EDC...)
- Mesh generation & corridor geometric audit (5 quality gates)
- Boundary nodes, re-entrant corner (250, 250), and loading point (470, 250)
- Coupled 3-layer deck structure, UEL ABI (6 properties, 18 SVARs)
- Single-increment Step 1 re-equilibration card (*STATIC\n1.0, 1.0, 1.0E-08, 1.0)
- Cumulative crack arc length progression metric
- Completion criteria (load drop < 5% or geometric boundary severance)
- Embedded stall-check watchdog
"""

import os
import sys
import math
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

LPANEL_DIR = os.path.join(REPO_ROOT, "models", "mode_II_or_l_panel", "295_method_c_lpanel")
if LPANEL_DIR not in sys.path:
    sys.path.insert(0, LPANEL_DIR)

import lpanel_single_job_orchestrator as orch
import lpanel_runtime
from generate_lpanel_adaptive_corridor_mesh import evaluate_corridor_audit, compute_corridor_spec


def test_frozen_uel_source_integrity():
    """UEL source must match CE8D5EDC bitwise."""
    source_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(source_path)
    with open(source_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest().upper()
    assert digest == orch.FROZEN_UEL_SHA256


def test_lpanel_mesh_quality_gates():
    """Coarse physical mesh must pass all 5 quality gates."""
    mesh_path = os.path.join(LPANEL_DIR, "PK_METHOD_C_LPANEL_COARSE_PHYS.inp")
    assert os.path.exists(mesh_path), "Coarse physical mesh must exist"

    nodes, quads, tris, _ = orch.parse_physical_mesh(mesh_path)
    total_elements = len(quads) + len(tris)
    assert total_elements > 0
    assert total_elements < 35000, "Element count must be strictly < 35,000"

    elem_types = {e: "QUAD" for e in quads}
    elem_types.update({e: "TRI" for e in tris})

    audit = evaluate_corridor_audit(nodes, {**quads, **tris}, elem_types, 250.0, 250.0)
    gates = audit["gates"]

    assert gates["gate01_positive_jacobian"] is True, "Gate 01: Positive Jacobians required"
    assert gates["gate02_quad_fraction_ge_85"] is True, "Gate 02: Quad fraction >= 85% required"
    assert gates["gate03_aspect_ratio_le_5"] is True, "Gate 03: Aspect ratio <= 5.0 required"
    assert gates["gate04_size_le_l0_half"] is True, "Gate 04: Corridor size <= l0/2 required"
    assert gates["gate05_bounded_under_35k"] is True, "Gate 05: Total elements < 35k required"


def test_lpanel_boundary_and_loading_landmarks():
    """Verifies bottom clamped edge, corner at (250, 250), and exact loading point at (470, 250)."""
    mesh_path = os.path.join(LPANEL_DIR, "PK_METHOD_C_LPANEL_COARSE_PHYS.inp")
    nodes, _, _, _ = orch.parse_physical_mesh(mesh_path)

    # 1. Corner node at (250, 250)
    corner_nodes = [nid for nid, (x, y) in nodes.items() if math.hypot(x - 250.0, y - 250.0) < 1e-3]
    assert len(corner_nodes) >= 1, "Must have an exact node at re-entrant corner (250, 250)"

    # 2. Loading node at (470, 250)
    load_nodes = [nid for nid, (x, y) in nodes.items() if math.hypot(x - 470.0, y - 250.0) < 1e-3]
    assert len(load_nodes) >= 1, "Must have an exact node at loading point (470, 250)"

    # 3. Bottom clamped boundary at y = 0, x in [0, 250]
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y) < 1e-4 and x <= 250.0 + 1e-4]
    assert len(bottom_nodes) >= 20, "Must have clamped nodes along bottom edge y=0, x in [0, 250]"
    min_x = min(nodes[n][0] for n in bottom_nodes)
    max_x = max(nodes[n][0] for n in bottom_nodes)
    assert abs(min_x - 0.0) < 1e-4
    assert abs(max_x - 250.0) < 1e-4


def test_lpanel_deck_assembly_and_uel_properties(tmp_path):
    """Verifies input deck structure, UEL properties, and single-increment re-equilibration card."""
    mesh_path = os.path.join(LPANEL_DIR, "PK_METHOD_C_LPANEL_COARSE_PHYS.inp")
    nodes, quads, tris, _ = orch.parse_physical_mesh(mesh_path)

    deck_path = str(tmp_path / "test_lpanel_deck.inp")
    dummy_damage = {n: 0.15 for n in nodes}
    dummy_history = {}

    orch.assemble_lpanel_coupled_deck(
        deck_path, nodes, quads, tris,
        donor_uy=0.20, target_uy=0.23,
        transferred_damage=dummy_damage,
        transferred_history=dummy_history,
        is_coarse=False, use_riks=True
    )

    assert os.path.exists(deck_path)
    lpanel_runtime.validate_uel_properties(deck_path, len(quads) + len(tris))

    content = open(deck_path, "r").read()

    # Verify UEL cards
    assert "*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM" in content
    assert "*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM" in content
    assert "*SOLID SECTION, ELSET=All_elem, MATERIAL=M_COMPANION\n100.0" in content

    # Verify canonical single-increment re-equilibration card in Step 1
    assert "*STEP, NAME=Step-1, NLGEOM=NO, INC=100\n*STATIC\n1.0, 1.0, 1.0E-08, 1.0" in content
    assert "*NODE OUTPUT\nU" in content

    # Verify steel bearing collar constraint on DOF 3
    assert "*NSET, NSET=N_LOAD_COLLAR" in content
    assert "N_LOAD_COLLAR, 3, 3, 0.0" in content

    # Verify Step 2 RIKS card
    assert "*STEP, NAME=Step-2, NLGEOM=NO, INC=1000\n*STATIC, RIKS" in content


def test_lpanel_steel_collar_constraint(tmp_path):
    """Verifies that the steel collar nodes in [455, 485] along y=250 are constrained to d=0 on DOF 3."""
    mesh_path = os.path.join(LPANEL_DIR, "PK_METHOD_C_LPANEL_COARSE_PHYS.inp")
    nodes, quads, tris, _ = orch.parse_physical_mesh(mesh_path)

    # 1. Identify collar nodes
    collar_nodes = [nid for nid, (x, y) in nodes.items() if 455.0 - 1e-4 <= x <= 485.0 + 1e-4 and abs(y - 250.0) <= 1e-3]
    assert len(collar_nodes) >= 3, "Collar must contain multiple nodes across bearing zone"
    assert any(math.hypot(nodes[n][0] - 470.0, nodes[n][1] - 250.0) < 1e-3 for n in collar_nodes), "Loading node (470, 250) must be in collar"

    # 2. Test coarse deck assembly
    coarse_deck = str(tmp_path / "coarse_collar.inp")
    orch.assemble_lpanel_coupled_deck(
        coarse_deck, nodes, quads, tris,
        donor_uy=0.0, target_uy=0.20,
        is_coarse=True
    )
    coarse_content = open(coarse_deck, "r").read()
    assert "*NSET, NSET=N_LOAD_COLLAR" in coarse_content
    assert "N_LOAD_COLLAR, 3, 3, 0.0" in coarse_content

    # 3. Test adaptive deck assembly with initial damage
    adapt_deck = str(tmp_path / "adapt_collar.inp")
    damage_with_puncture = {n: 0.90 for n in nodes}  # synthetic high damage
    orch.assemble_lpanel_coupled_deck(
        adapt_deck, nodes, quads, tris,
        donor_uy=0.20, target_uy=0.22,
        transferred_damage=damage_with_puncture,
        transferred_history={},
        is_coarse=False, use_riks=True
    )
    adapt_content = open(adapt_deck, "r").read()
    assert "*NSET, NSET=N_LOAD_COLLAR" in adapt_content
    assert "N_LOAD_COLLAR, 3, 3, 0.0" in adapt_content



def test_lpanel_arc_length_progression():
    """Verifies cumulative arc length calculation along crack path."""
    corner = (250.0, 250.0)
    tip_history = [
        (240.0, 252.0),
        (220.0, 258.0),
        (180.0, 272.0),
        (100.0, 295.0),
        (0.0, 310.0)
    ]
    s = orch.compute_cumulative_crack_arc_length(tip_history, corner=corner)
    # Expected arc length ~ 250-260 mm
    assert s > 250.0
    assert s < 270.0


def test_lpanel_completion_criteria():
    """Verifies completion logic under load drop and geometric severance."""
    # 1. In progress
    done, reason = orch.check_lpanel_completion(
        current_cycle=1, peak_rf2=10.0, terminal_rf2=9.5,
        tip_x=240.0, tip_y=252.0, arc_length_s=10.0, max_damage=0.45
    )
    assert not done
    assert reason == "IN_PROGRESS"

    # 2. Load drop < 5%
    done, reason = orch.check_lpanel_completion(
        current_cycle=3, peak_rf2=10.0, terminal_rf2=0.40,
        tip_x=50.0, tip_y=300.0, arc_length_s=210.0, max_damage=0.99
    )
    assert done
    assert "COMPLETE_LOAD_DROP_BELOW_5PCT" in reason

    # 3. Geometric severance to left edge
    done, reason = orch.check_lpanel_completion(
        current_cycle=4, peak_rf2=10.0, terminal_rf2=1.50,
        tip_x=1.0, tip_y=310.0, arc_length_s=255.0, max_damage=0.99
    )
    assert done
    assert "COMPLETE_SPECIMEN_SEVERED_TO_LEFT_EDGE" in reason


def test_lpanel_stall_watchdog():
    """Verifies stall watchdog functions properly."""
    watch = orch.StallWatchdog(max_sta_stall_hours=2.0, max_cycle_hours=8.0, max_agent_hours=4.0)
    watch.start_cycle()
    watch.record_agent_progress()

    stalled, reason, details = watch.check_agent_stall()
    assert not stalled


def test_lpanel_collar_run_evidence_and_gates():
    """
    Verifies that the steel collar run evidence across Cycles 0 to 10
    satisfies all physical transfer gates, zero-healing, and authentic tip propagation.
    """
    run_dir = os.path.join(REPO_ROOT, "models", "mode_II_or_l_panel", "295_method_c_lpanel", "local_windows_full_run")
    assert os.path.isdir(run_dir), "Run directory must exist"

    manifest_path = os.path.join(run_dir, "image_manifest.json")
    assert os.path.isfile(manifest_path), "Image manifest must exist"
    with open(manifest_path, "r") as f:
        manifest = json.load(f)
    assert len(manifest) == 11, f"Must have 11 cycles recorded, found {len(manifest)}"

    # Audit every cycle
    prev_dmax = 0.0
    for entry in manifest:
        cycle = entry["cycle"]
        job = "PK_METHOD_C_LPANEL_COARSE_JOB1" if cycle == 0 else f"PK_METHOD_C_LPANEL_CYCLE{cycle}"
        sum_path = os.path.join(run_dir, f"{job}_SUMMARY.json")
        assert os.path.isfile(sum_path)
        with open(sum_path, "r") as f:
            summary = json.load(f)

        assert summary["status"] == "CONVERGED_AUDITED"
        assert summary["source_sha256"] == orch.FROZEN_UEL_SHA256
        assert summary["mesh_elements"] < 35000

        # Monotonic damage (zero healing)
        assert summary["max_damage"] >= prev_dmax - 1e-4
        prev_dmax = summary["max_damage"]

        # Transfer gates for adaptive cycles
        if cycle > 0:
            gates = summary["gate_results"]
            assert gates["force_continuity_pass"] is True
            assert abs(gates["force_continuity_delta_pct"]) <= 5.0
            assert gates["global_max_damage_nonhealing_pass"] is True

        # Commit-pinned URL verification
        assert entry["commit"] in entry["url"]
        assert entry["image_sha256"] is not None

    # Cycle 10 check: deep curved penetration across vertical column
    c10_sum_path = os.path.join(run_dir, "PK_METHOD_C_LPANEL_CYCLE10_SUMMARY.json")
    with open(c10_sum_path, "r") as f:
        c10 = json.load(f)
    assert c10["tip_mm"][0] < 100.0  # tip traversed from 250 mm to < 100 mm (x = 97.87 mm)
    assert c10["tip_mm"][1] > 280.0  # tip curved upward above y = 280 mm
    assert c10["tip_history_chord_sum_mm"] > 150.0  # cumulative chord > 150 mm (157.51 mm)
    assert c10["terminal_rf2_kn"] < 0.035  # load softened below 0.035 kN (> 81% load drop from 0.15907 kN)


def test_lpanel_cycle11_cutback_diagnosis():
    """
    Verifies that the Cycle 11 solver output is preserved with authentic dt_min diagnostics:
    Step 1 re-equilibrated in 1 increment, Step 2 advanced 145 RIKS increments reaching
    uy = 0.4152 mm with RF2 = 0.02695 kN (83.1% load drop) before cutback termination.
    """
    run_dir = os.path.join(REPO_ROOT, "models", "mode_II_or_l_panel", "295_method_c_lpanel", "local_windows_full_run")
    if not os.path.isfile(os.path.join(run_dir, "PK_METHOD_C_LPANEL_CYCLE11.sta")):
        run_dir = os.path.join(REPO_ROOT, "models", "mode_II_or_l_panel", "295_method_c_lpanel", "run_campaign_continuation")

    sta_path = os.path.join(run_dir, "PK_METHOD_C_LPANEL_CYCLE11.sta")
    msg_path = os.path.join(run_dir, "PK_METHOD_C_LPANEL_CYCLE11.msg")
    dat_path = os.path.join(run_dir, "PK_METHOD_C_LPANEL_CYCLE11.dat")

    assert os.path.isfile(sta_path), "Cycle 11 .sta must be preserved"
    assert os.path.isfile(msg_path), "Cycle 11 .msg must be preserved"
    assert os.path.isfile(dat_path), "Cycle 11 .dat must be preserved"

    msg_text = open(msg_path, "r").read()
    assert "TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED" in msg_text

    dat_text = open(dat_path, "r").read()
    assert "INCREMENT   145 SUMMARY" in dat_text
    assert "4.1522659E-01" in dat_text  # terminal uy = 0.4152 mm
    assert "2.6946296E-02" in dat_text  # terminal RF2 = 0.02695 kN (83.1% load drop)


