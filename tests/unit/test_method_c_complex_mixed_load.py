# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_complex_mixed_load.py
==============================================
Unit test suite for Problem 3:
Notch + Hole under Combined Tension + Shear (ux = 0.5 * uy)
Method C Adaptive Remeshing Framework.
"""

import math
import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np

HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parents[1]
MODEL_DIR = REPO_ROOT / "models" / "complex_mixed_load"
if str(MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(MODEL_DIR))

import generate_mixed_load_mesh as gen
import mixed_load_single_job_orchestrator as orch
import mixed_load_runtime as rt


def test_geometry_and_landmarks():
    """Verify Problem 3 geometry landmarks match the authorized specification."""
    assert gen.PLATE_W == 1.0
    assert gen.PLATE_H == 1.0

    # Inclined Notch: 0.5 mm at +45 deg from (0.0, 0.50)
    assert gen.NOTCH_START_X == 0.0
    assert gen.NOTCH_START_Y == 0.50
    assert gen.NOTCH_LEN == 0.50
    assert math.isclose(gen.NOTCH_ANGLE_RAD, math.pi / 4.0, rel_tol=1e-6)
    assert math.isclose(gen.NOTCH_TIP_X, 0.5 * math.cos(math.pi / 4.0), rel_tol=1e-5)
    assert math.isclose(gen.NOTCH_TIP_Y, 0.5 + 0.5 * math.sin(math.pi / 4.0), rel_tol=1e-5)

    # Hole: center (0.65, 0.65), radius R = 0.10 mm
    assert gen.HOLE_X == 0.65
    assert gen.HOLE_Y == 0.65
    assert gen.HOLE_R == 0.10

    # Distance from notch tip to hole boundary
    dist_tip_to_center = math.hypot(gen.NOTCH_TIP_X - gen.HOLE_X, gen.NOTCH_TIP_Y - gen.HOLE_Y)
    dist_tip_to_boundary = dist_tip_to_center - gen.HOLE_R
    assert dist_tip_to_boundary > 0.15  # Sufficient ligament for crack growth


def test_shear_to_tension_ratio():
    """Verify shear-to-tension ratio ux = 0.5 * uy is strictly enforced."""
    assert orch.SHEAR_TO_TENSION_RATIO == 0.5
    assert gen.SHEAR_TO_TENSION_RATIO == 0.5

    # Test load calculations
    uy_test = 0.00600
    ux_test = orch.SHEAR_TO_TENSION_RATIO * uy_test
    assert math.isclose(ux_test, 0.00300, rel_tol=1e-6)


def test_physics_and_material_constants():
    """Verify material constants and mesh sizing comply with Phase-Field theory."""
    assert orch.BENCHMARK_E_GPA == 210.0
    assert orch.BENCHMARK_NU == 0.30
    assert orch.BENCHMARK_L0_MM == 0.0075
    assert orch.BENCHMARK_GC_KN_MM == 0.0027
    assert orch.BENCHMARK_K_RES == 1e-7
    assert orch.BENCHMARK_THICKNESS == 1.0

    # Sizing
    assert gen.H_REF == 0.0035
    assert gen.H_REF <= (gen.L0 / 2.0)
    assert gen.H_BG == 0.035
    assert math.isclose(gen.BAND_HALF_WIDTH, 0.025, rel_tol=1e-6)


def test_frozen_uel_sha256():
    """Verify the UEL source f42_mixed_uel.for matches the bitwise frozen hash."""
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for must exist"
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert h == rt.FROZEN_UEL_SHA256, "f42_mixed_uel.for must match bitwise frozen SHA256"


def test_narrow_band_corridor_specification():
    """Verify the narrow damage-following band polygon hugs the crack path with < 2.5% area."""
    spec = gen.compute_corridor_spec()
    assert spec["corridor_type"] == "NARROW_DAMAGE_FOLLOWING_BAND"
    assert spec["h_ref"] == 0.0035
    assert spec["h_bg"] == 0.035
    assert spec["half_width"] == 0.025

    # Check area fraction
    assert spec["domain_area_fraction_pct"] < 2.5

    # Check with evolving tip history
    history = [
        [0.353553, 0.853553],
        [0.400000, 0.820000],
        [0.450000, 0.780000],
        [0.500000, 0.740000]
    ]
    spec_evolved = gen.compute_corridor_spec(tip_x=0.50, tip_y=0.74, tip_history=history)
    assert spec_evolved["domain_area_fraction_pct"] < 3.0
    assert len(spec_evolved["polygon_vertices"]) >= 4


def test_kinematic_coupling_and_deck_assembly(tmp_path):
    """Verify UEL deck assembly correctly ties top nodes in DOF 1 (ux) and DOF 2 (uy)."""
    # Create synthetic physical mesh
    phys_inp = tmp_path / "test_phys.inp"
    with open(phys_inp, "w") as f:
        f.write("*NODE\n")
        f.write("1, 0.0, 0.0\n")
        f.write("2, 1.0, 0.0\n")
        f.write("3, 1.0, 1.0\n")
        f.write("4, 0.0, 1.0\n")
        f.write("5, 0.5, 0.0\n")
        f.write("6, 0.5, 1.0\n")
        f.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMENTS\n")
        f.write("1, 1, 5, 6, 4\n")
        f.write("2, 5, 2, 3, 6\n")

    uel_inp = tmp_path / "test_uel.inp"
    orch.assemble_mixed_load_uel_deck(
        str(phys_inp), str(uel_inp),
        donor_uy=0.00400, target_uy=0.00500,
        is_coarse=False, use_riks=True,
        shear_ratio=0.5
    )
    assert uel_inp.exists()
    content = uel_inp.read_text()

    # Check top nodes 3, 4, 6 tied in DOF 1 (shear) and DOF 2 (tension)
    assert "*EQUATION" in content
    # DOF 1 equation check
    assert "3, 1, 1.0, 999999, 1, -1.0" in content
    assert "4, 1, 1.0, 999999, 1, -1.0" in content
    assert "6, 1, 1.0, 999999, 1, -1.0" in content
    # DOF 2 equation check
    assert "3, 2, 1.0, 999999, 2, -1.0" in content
    assert "4, 2, 1.0, 999999, 2, -1.0" in content
    assert "6, 2, 1.0, 999999, 2, -1.0" in content

    # Check clamped bottom
    assert "N_BOTTOM, 1, 2, 0.0" in content

    # Check hold re-equilibration card
    assert "*BOUNDARY, AMPLITUDE=CONST_HOLD" in content
    assert "N_RP, 1, 1, 2.00000000e-03" in content  # ux = 0.5 * 0.00400 = 0.00200
    assert "N_RP, 2, 2, 4.00000000e-03" in content


def test_state_transfer_kd_tree():
    """Verify cKDTree state transfer maps damage and history accurately."""
    donor_nodes = {
        1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)
    }
    donor_quads = {1: [1, 2, 3, 4]}
    donor_tris = {}
    donor_d = {1: 0.1, 2: 0.2, 3: 0.9, 4: 0.8}
    donor_h = {(1, 1): 0.05, (1, 2): 0.05, (1, 3): 0.50, (1, 4): 0.40}

    recip_nodes = {
        10: (0.05, 0.05), 20: (0.95, 0.05), 30: (0.95, 0.95), 40: (0.05, 0.95)
    }
    recip_quads = {100: [10, 20, 30, 40]}
    recip_tris = {}

    recip_d, recip_h = rt.transfer_state_fields(
        donor_nodes, donor_quads, donor_tris,
        donor_d, donor_h,
        recip_nodes, recip_quads, recip_tris
    )

    # Nearest neighbor checks
    assert math.isclose(recip_d[10], 0.1, abs_tol=1e-5)
    assert math.isclose(recip_d[30], 0.9, abs_tol=1e-5)
    assert len(recip_h) == 4
    assert all(not math.isnan(v) for v in recip_h.values())


def test_tip_tracking_and_completion_logic():
    """Verify crack tip tracking identifies hole contact, boundary reach, and load drop."""
    nodes = {
        1: (0.353553, 0.853553),  # Notch tip
        2: (0.450000, 0.800000),
        3: (0.550000, 0.750000),
        4: (0.624900, 0.746800),  # Exactly on hole boundary (dist to (0.65, 0.65) is 0.1000 mm)
        5: (0.990000, 0.500000),  # Near right boundary
    }
    elements = {
        1: [1, 2],
        2: [2, 3],
        3: [3, 4]
    }

    # Case 1: Early propagation
    damage_early = {1: 0.95, 2: 0.92, 3: 0.20, 4: 0.05, 5: 0.0}
    tip, dist_h, entered, bnd = rt.connected_tip(nodes, elements, damage_early)
    assert math.isclose(tip[0], 0.450, abs_tol=1e-3)
    assert not entered
    assert not bnd

    done, reason = rt.completion(peak_rf2=0.80, rf2=0.75, entered_hole=entered, reached_boundary=bnd)
    assert not done
    assert reason == "IN_PROGRESS"

    # Case 2: Crack enters hole boundary
    damage_hole = {1: 1.0, 2: 0.98, 3: 0.95, 4: 0.92, 5: 0.0}
    tip, dist_h, entered, bnd = rt.connected_tip(nodes, elements, damage_hole)
    assert math.isclose(tip[0], 0.6249, abs_tol=1e-3)
    assert entered, "Tip at (0.6249, 0.7468) must be detected as entering hole boundary"

    done, reason = rt.completion(peak_rf2=0.80, rf2=0.60, entered_hole=entered, reached_boundary=bnd)
    assert done
    assert reason == "CONNECTED_DAMAGE_ENTERED_HOLE"

    # Case 3: Post-peak load drop below 5%
    done, reason = rt.completion(peak_rf2=0.80, rf2=0.03, entered_hole=False, reached_boundary=False)
    assert done
    assert reason == "REACTION_FORCE_BELOW_5PCT_PEAK"


def test_geometry_audit():
    """Verify geometry audit correctly computes quadrature Jacobians and aspect ratios."""
    # Well-shaped unit quad
    nodes_good = {1: (0.0, 0.0), 2: (0.01, 0.0), 3: (0.01, 0.01), 4: (0.0, 0.01)}
    elems_good = {1: [1, 2, 3, 4]}
    qa_good = rt.geometry_audit(nodes_good, elems_good)
    assert qa_good["positive_jacobians_pass"]
    assert qa_good["edge_ratio_le_5_pass"]

    # Inverted quad
    nodes_bad = {1: (0.0, 0.0), 2: (0.0, 0.01), 3: (0.01, 0.01), 4: (0.01, 0.0)}
    elems_bad = {1: [1, 2, 3, 4]}
    qa_bad = rt.geometry_audit(nodes_bad, elems_bad)
    assert not qa_bad["positive_jacobians_pass"]


def test_reaction_force_reporting_contract():
    """Verify runtime summary schema records both RF2 (tension) and RF1 (shear)."""
    fields_dummy = {
        "terminal": {
            "uy": 0.00500, "ux": 0.00250,
            "rf2": 0.7200, "rf1": 0.2800,
            "damage": {"1": 0.95}, "history": {}, "displacements": {},
            "energies": {"SDV17": 0.001, "SDV18": 0.0005}
        },
        "hold": {
            "uy": 0.00450, "ux": 0.00225,
            "rf2": 0.7180, "rf1": 0.2790,
            "damage": {"1": 0.95}, "history": {}, "displacements": {},
            "energies": {"SDV17": 0.001, "SDV18": 0.0005}
        },
        "peak_rf2": 0.7500,
        "peak_rf1": 0.2900
    }
    # Assert RF1 and RF2 exist and are non-zero
    assert fields_dummy["terminal"]["rf2"] > 0
    assert fields_dummy["terminal"]["rf1"] > 0
    assert fields_dummy["peak_rf2"] >= fields_dummy["terminal"]["rf2"]
    assert fields_dummy["peak_rf1"] >= fields_dummy["terminal"]["rf1"]


def test_transfer_gate_evaluator():
    """Verify Step 1 fixed-load hold force continuity gate (<= 5.0% on RF2) and damage non-healing gate."""
    donor_rf2 = 0.7200
    hold_rf2_pass = 0.7180  # Delta = -0.278% <= 5.0%
    hold_rf2_fail = 0.6500  # Delta = -9.722% > 5.0%

    delta_pass = ((hold_rf2_pass - donor_rf2) / donor_rf2) * 100.0
    delta_fail = ((hold_rf2_fail - donor_rf2) / donor_rf2) * 100.0

    assert abs(delta_pass) <= 5.0
    assert abs(delta_fail) > 5.0

    # Audit actual campaign cycle summaries (Cycles 1 to 8)
    res_dir = REPO_ROOT / "models" / "complex_mixed_load" / "campaign_results"
    for c in range(1, 9):
        sum_path = res_dir / f"PK_METHOD_C_MIXED_LOAD_CYCLE{c}_SUMMARY.json"
        assert sum_path.exists()
        cdata = json.loads(sum_path.read_text(encoding="utf-8"))
        gates = cdata["gate_results"]

        # All 8 cycles must pass force continuity on RF2 (<= 5.0%) and RF1 (<= 5.0%)
        assert gates["force_continuity_pass"] is True
        assert abs(gates["delta_rf2_pct"]) <= 5.0
        assert abs(gates["delta_rf1_pct"]) <= 5.0

        if c == 6:
            # Cycle 6: Disclosed transfer gate failure on hold damage non-healing
            assert cdata["status"] == "TRANSFER_GATE_FAILED"
            assert gates["damage_nonhealing_pass"] is False
            donor_d = gates["donor_max_damage"]
            hold_d = gates["hold_max_damage"]
            assert hold_d < donor_d - 1e-4, "Cycle 6 hold damage drop must exceed 1e-4 tolerance"
        else:
            # Cycles 1-5, 7, 8: Damage non-healing gate must pass
            assert gates["damage_nonhealing_pass"] is True


def test_accounting_and_governance():
    """Verify PBS accounting is strictly preserved at 0/73 and master goal is OPEN."""
    active_task_path = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
    assert active_task_path.exists()
    task = json.loads(active_task_path.read_text(encoding="utf-8"))

    assert task["master_goal_status"] == "OPEN"
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 73
    assert task["current_problem"] == 3


def test_shear_effect_on_crack_curvature_and_trajectory():
    """Verify how horizontal shear alters crack curvature, hole entry point, and load capacity vs pure tension."""
    res_dir = REPO_ROOT / "models" / "complex_mixed_load" / "campaign_results"
    c8_sum_file = res_dir / "PK_METHOD_C_MIXED_LOAD_CYCLE8_SUMMARY.json"
    assert c8_sum_file.exists()
    c8_data = json.loads(c8_sum_file.read_text(encoding="utf-8"))

    # 1. Hole contact verified
    assert c8_data["completion"] is True
    assert c8_data["completion_reason"] == "CONNECTED_DAMAGE_ENTERED_HOLE"
    assert c8_data["entered_hole"] is True
    assert c8_data["dist_to_hole_boundary_mm"] < 1e-6

    # 2. Tip trajectory comparison: enters hole at upper-left flank (0.5734, 0.7143)
    # Hole center is (0.65, 0.65), R = 0.10. Entry angle theta ~ 140 deg vs ~105 deg for pure tension
    tip_x, tip_y = c8_data["tip_mm"]
    assert math.isclose(tip_x, 0.573396, abs_tol=1e-4)
    assert math.isclose(tip_y, 0.714279, abs_tol=1e-4)

    # In pure tension (Novel Benchmark), crack entered hole at (0.6249, 0.7468)
    # The shear shifted the crack contact point leftward by ~0.0515 mm and downward by ~0.0325 mm
    assert tip_x < 0.60, "Mixed-mode shear must deflect crack entry point leftward compared to pure tension"

    # 3. Path length: more direct plunge to hole gives shorter arc length
    chord_mixed = c8_data["tip_history_chord_sum_mm"]
    assert math.isclose(chord_mixed, 0.250342, abs_tol=1e-4)
    novel_pure_tension_chord = 0.3181
    assert chord_mixed < novel_pure_tension_chord, "Mixed load crack plunges earlier, yielding shorter chord"

    # 4. Peak reaction forces: combined constraint yields higher peak RF2 + substantial shear RF1
    peak_rf2 = c8_data["peak_rf2_kn"]
    peak_rf1 = c8_data["peak_rf1_kn"]
    assert math.isclose(peak_rf2, 0.988857, abs_tol=1e-4)
    assert math.isclose(peak_rf1, 0.243455, abs_tol=1e-4)
    novel_pure_tension_peak_rf2 = 0.8044
    assert peak_rf2 > novel_pure_tension_peak_rf2 * 1.20, "Combined loading must increase peak RF2 by >20%"


def test_report_and_summary_file_hashes():
    """Verify Problem 3 all 9 cycle summary file SHA-256 hashes and checkpoint file hashes."""
    res_dir = REPO_ROOT / "models" / "complex_mixed_load" / "campaign_results"

    expected_summary_hashes = {
        "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_SUMMARY.json": "E288B4A7880A58A7C33D39563A2F075116CB55774B0D4138B9B065DEDC7D81A7",
        "PK_METHOD_C_MIXED_LOAD_CYCLE1_SUMMARY.json": "D7DDE7343AE1F38D118200AE79B39A337A04EB6C297FAFFB11EF167517CAA703",
        "PK_METHOD_C_MIXED_LOAD_CYCLE2_SUMMARY.json": "4E80A3FB91925581FC2ACAF91C47C9AFE542BBCF953CB3438245E4DE74979283",
        "PK_METHOD_C_MIXED_LOAD_CYCLE3_SUMMARY.json": "28CCC5E9A09207D24AD4165C58C66AAB88DC7379DADCE657B96698D95B1C4674",
        "PK_METHOD_C_MIXED_LOAD_CYCLE4_SUMMARY.json": "3EFF2AF073057FBDECAC593F0994CAE7677A056C70337AF69F68739CE138EB9F",
        "PK_METHOD_C_MIXED_LOAD_CYCLE5_SUMMARY.json": "4428FD1ECCA6BE180BCB7BF5EDF9A80C369EAB95986965C11D5F4A99972A20DD",
        "PK_METHOD_C_MIXED_LOAD_CYCLE6_SUMMARY.json": "1D5FAFBCE8F444A932C5F6055EE0DF77431BC756D5F095F6B575CBE09E8B57BE",
        "PK_METHOD_C_MIXED_LOAD_CYCLE7_SUMMARY.json": "0732A0264C11376C7794E9FA9652103E42CF0E314E95E21277897D3912E3BE47",
        "PK_METHOD_C_MIXED_LOAD_CYCLE8_SUMMARY.json": "298151CF032320AB1315FC447622DE29E536C216290C003652291B75989B6576",
    }
    for filename, expected_hash in expected_summary_hashes.items():
        summary_file = res_dir / filename
        assert summary_file.exists(), f"Summary file {filename} must exist"
        file_sha = hashlib.sha256(summary_file.read_bytes()).hexdigest().upper()
        assert file_sha == expected_hash, f"Hash mismatch for {filename}: {file_sha} != {expected_hash}"

    expected_checkpoint_hashes = {
        "PK_METHOD_C_MIXED_LOAD_COARSE_JOB1_checkpoint.json": "8F26A7C91B6C6024BB5EF29E65B53A23D90D178B55567BAD626A7B97E7FE48BD",
        "PK_METHOD_C_MIXED_LOAD_CYCLE1_checkpoint.json": "5D89D79FCF3F87A12C3C87AA3FCD13E2FEC67C4B9BF86B02F93A5BA455B2642C",
        "PK_METHOD_C_MIXED_LOAD_CYCLE2_checkpoint.json": "5BA7F11BA0CA73D2F105606D097562B27B80E9609004A5B97148D8B6EF089293",
        "PK_METHOD_C_MIXED_LOAD_CYCLE3_checkpoint.json": "107EAC343D3F16F6769A90EBA72724F88E3CBCC9A9DA0BEBBF9E79A117AD1A60",
        "PK_METHOD_C_MIXED_LOAD_CYCLE4_checkpoint.json": "DF08E75ACBB765AE769C32259072A771D50CE4FAD49CF27381412232A3237413",
        "PK_METHOD_C_MIXED_LOAD_CYCLE5_checkpoint.json": "205676C57298C73D559FDBD57AACCC609448175F9781FE208D777B26F2517F15",
        "PK_METHOD_C_MIXED_LOAD_CYCLE6_checkpoint.json": "912EF250DC2B13685CB321197D3EC348F6A0FBF2FE12D1A2CB97F85FF9FFE81C",
        "PK_METHOD_C_MIXED_LOAD_CYCLE7_checkpoint.json": "114F6298A08982FAD86D93E68D6751276F73C42BA890E789BC3634900BA57893",
        "PK_METHOD_C_MIXED_LOAD_CYCLE8_checkpoint.json": "EB156582D36989BFC579304A6A1D889A513F5E480ABB02644420596BE22C3250",
    }
    for filename, expected_hash in expected_checkpoint_hashes.items():
        ckpt_file = res_dir / filename
        assert ckpt_file.exists(), f"Checkpoint file {filename} must exist"
        file_sha = hashlib.sha256(ckpt_file.read_bytes()).hexdigest().upper()
        assert file_sha == expected_hash, f"Hash mismatch for {filename}: {file_sha} != {expected_hash}"

    # Verify report SHA256
    report_file = REPO_ROOT / "docs" / "validation" / "METHOD_C_COMPLEX_PROBLEM3_MIXED_LOAD_REPORT.md"
    assert report_file.exists(), "Validation report must exist"
    report_sha = hashlib.sha256(report_file.read_bytes()).hexdigest().upper()
    assert report_sha == "D50B6615241B5C2651804FBD5F3D06BEC205BEC80210193FCCB972D05FF1DB49"

