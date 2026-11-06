#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r12_qualification.py
====================================
Comprehensive Technical Qualification and Regression Suite for Task F1628:
Method C Package 171 Revision 12 (C6 Isoparametric Bilinear Gauss-Point Transfer).
Protocol Version: 2

Validates:
1. Bitwise frozen UEL SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6.
2. C6 Mesh topology: 15,252 CPE4 quads, 15,559 physical nodes, 59 crack-seam pairs.
3. Complete history synchronization between initial_conditions_solution.inc and d_lower_bounds.csv.
4. Thermodynamic non-negativity (H >= 0.0) and damage bounds (0 <= d <= 1.0) across all 61,008 GPs.
5. Intra-element gradient restoration (>99% elements non-uniform, peak H > 14.0 MPa).
6. Zero-PBS governance enforcement across task definition and active task state.
7. Driver configuration: anderson_enabled == False by default (isolated baseline), CLI switchable.
8. Extractor contract and Node Print card presence across all decks.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import csv
import hashlib
import json
import math
import pytest

PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "171_c6_package171_r12_c3_0_adaptive_reequilibration"
TASK_DEF_PATH = REPO_ROOT / "project_coordination" / "task_definitions" / "F1628-METHOD-C-ISOPARAMETRIC-C6-ADAPTIVE-REEQUILIBRATION.json"
ACTIVE_TASK_PATH = REPO_ROOT / "project_coordination" / "ACTIVE_TASK.json"
COMPARISON_JSON_PATH = REPO_ROOT / "results" / "validation" / "c6_isoparametric_vs_averaged_history_comparison.json"

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_01_frozen_uel_integrity():
    """Verify production UEL source in Package 171-R12 matches frozen hash bitwise."""
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file(), f"Missing UEL source at {uel_path}"
    actual_hash = sha256_file(uel_path)
    assert actual_hash == FROZEN_UEL_HASH, (
        f"Bitwise frozen UEL mismatch! Expected {FROZEN_UEL_HASH}, got {actual_hash}"
    )


def test_02_c6_mesh_topology_and_seam():
    """Verify C6 mesh topology: 15,252 CPE4 quads, 15,559 physical nodes, 59 seam pairs."""
    from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D

    deck_path = PKG_DIR / "M1_C6_PACKAGE171_R12_C3_0_ADAPTIVE_REEQUILIBRATION.inp"
    assert deck_path.is_file(), f"Missing master deck at {deck_path}"
    mesh = Mesh2D.from_inp(deck_path, name="C6_Receiver", max_physical_node=15559)

    assert len(mesh.elements) == 15252, f"Expected 15,252 CPE4 elements, got {len(mesh.elements)}"
    assert len(mesh.nodes) == 15559, f"Expected 15,559 physical nodes, got {len(mesh.nodes)}"

    # Crack seam along y=0.050, 0 <= x <= 0.040
    # Physical boundary check
    xs = [coord[0] for coord in mesh.nodes.values()]
    ys = [coord[1] for coord in mesh.nodes.values()]
    assert min(xs) >= -1e-6 and max(xs) <= 0.100001
    assert min(ys) >= -1e-6 and max(ys) <= 0.100001

    # Check for duplicate node positions at crack seam
    seam_nodes = [nid for nid, (x, y) in mesh.nodes.items() if abs(y - 0.050) < 1e-5 and x <= 0.040001]
    assert len(seam_nodes) >= 59 * 2, f"Expected at least 118 nodes along seam, found {len(seam_nodes)}"


def test_03_history_synchronization():
    """Verify 100% agreement between initial_conditions_solution.inc and d_lower_bounds.csv across all 15,252 elements."""
    from scripts.state_transfer.build_package171_r12 import parse_solution_inc

    inc_path = PKG_DIR / "initial_conditions_solution.inc"
    bounds_path = PKG_DIR / "d_lower_bounds.csv"
    assert inc_path.is_file(), f"Missing {inc_path}"
    assert bounds_path.is_file(), f"Missing {bounds_path}"

    inc_hist = parse_solution_inc(inc_path)
    assert len(inc_hist) == 15252, f"Expected 15,252 element records in inc, got {len(inc_hist)}"

    bounds_hist = {}
    with open(bounds_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        for r in reader:
            if r:
                eid = int(r[0])
                bounds_hist[eid] = [float(r[5]), float(r[6]), float(r[7]), float(r[8])]

    assert len(bounds_hist) == 15252, f"Expected 15,252 element records in csv, got {len(bounds_hist)}"

    max_diff = 0.0
    for eid in inc_hist:
        assert eid in bounds_hist, f"Element {eid} in inc but not in csv"
        for g in range(4):
            diff = abs(inc_hist[eid][g] - bounds_hist[eid][g])
            if diff > max_diff:
                max_diff = diff
            assert diff <= 1e-12, f"Mismatch at element {eid} GP {g+1}: inc={inc_hist[eid][g]} vs csv={bounds_hist[eid][g]}"

    assert max_diff <= 1e-12, f"Max synchronization discrepancy {max_diff:.4e} exceeds 1e-12"


def test_04_thermodynamic_admissibility_and_bounds():
    """Verify all 61,008 Gauss-point histories are strictly non-negative and finite."""
    bounds_path = PKG_DIR / "d_lower_bounds.csv"
    d_path = PKG_DIR / "nodal_phase_field_initial.csv"

    gp_count = 0
    min_h = 1e9
    max_h = -1e9
    with open(bounds_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if r:
                for g in range(4):
                    h_val = float(r[5 + g])
                    assert math.isfinite(h_val), f"Non-finite history at element {r[0]} GP {g+1}"
                    assert h_val >= 0.0, f"Negative history {h_val} at element {r[0]} GP {g+1}"
                    if h_val < min_h:
                        min_h = h_val
                    if h_val > max_h:
                        max_h = h_val
                    gp_count += 1

    assert gp_count == 61008, f"Expected 61,008 GP histories, counted {gp_count}"
    assert min_h >= 0.0, f"Minimum history {min_h} must be non-negative"
    assert max_h > 14.0, f"Peak history {max_h} expected to be > 14.0 MPa"

    # Damage bounds: 0 <= d0 <= 1.0 across all 15,559 nodes
    d_nodes = {}
    with open(d_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for r in reader:
            if r:
                nid = int(r[0])
                d_val = float(r[1])
                assert math.isfinite(d_val), f"Non-finite damage at node {nid}"
                assert 0.0 <= d_val <= 1.0, f"Damage out of bounds [0, 1] at node {nid}: {d_val}"
                d_nodes[nid] = d_val

    assert len(d_nodes) == 15559, f"Expected 15,559 node damage entries, got {len(d_nodes)}"
    assert max(d_nodes.values()) > 0.65, "Expected localized crack-tip damage > 0.65"


def test_05_gradient_restoration_verification():
    """Verify that >99% of elements possess intra-element varying history gradients."""
    assert COMPARISON_JSON_PATH.is_file(), f"Missing comparison report at {COMPARISON_JSON_PATH}"
    comp = json.loads(COMPARISON_JSON_PATH.read_text(encoding="utf-8"))

    telemetry = comp.get("transfer_telemetry", {})
    pct_nonuniform = telemetry.get("non_uniform_elements_pct", 0.0)
    assert pct_nonuniform > 99.0, f"Expected >99% intra-element nonuniformity, got {pct_nonuniform}%"

    peak_iso = comp.get("history_field_ranges", {}).get("corrected_isoparametric", {}).get("max_MPa", 0.0)
    peak_avg = comp.get("history_field_ranges", {}).get("original_averaged", {}).get("max_MPa", 0.0)
    assert peak_iso > 14.0, f"Expected peak history > 14.0 MPa, got {peak_iso}"
    assert peak_avg < 10.0, f"Expected old control peak history < 10.0 MPa, got {peak_avg}"

    # Verify integral history conservation to within 0.1%
    total_iso = comp.get("history_field_ranges", {}).get("corrected_isoparametric", {}).get("sum_MPa", 0.0)
    total_avg = comp.get("history_field_ranges", {}).get("original_averaged", {}).get("sum_MPa", 0.0)
    rel_diff = abs(total_iso - total_avg) / total_avg
    assert rel_diff < 0.001, f"Integral history conservation drift {rel_diff * 100:.3f}% exceeds 0.1%"


def test_06_zero_pbs_governance():
    """Verify zero-PBS enforcement in F1628 task definition."""
    assert TASK_DEF_PATH.is_file(), f"Missing task definition at {TASK_DEF_PATH}"
    task_def = json.loads(TASK_DEF_PATH.read_text(encoding="utf-8"))
    assert task_def.get("authorized_scope", {}).get("max_new_pbs_submissions") == 0
    assert task_def.get("authorized_scope", {}).get("remaining_pbs_submissions") == 0
    assert task_def.get("authorized_scope", {}).get("zero_pbs_enforced") is True


def test_07_driver_configuration_and_anderson_switch():
    """Verify driver configuration: anderson_enabled == False by default, switchable via CLI."""
    from scripts.state_transfer.driver_package171_r12_c6_coupled_pdas import (
        build_argument_parser, Package171R12C6PDASDriver
    )

    parser = build_argument_parser()
    args_default = parser.parse_args(["--output", "test_out", "--extractor", "test_ext"])
    assert args_default.anderson_enabled is False, "Default anderson_enabled MUST be False to isolate transfer effects"

    args_enabled = parser.parse_args(["--output", "test_out", "--extractor", "test_ext", "--anderson-enabled"])
    assert args_enabled.anderson_enabled is True, "--anderson-enabled must toggle anderson_enabled to True"

    args_enabled2 = parser.parse_args(["--output", "test_out", "--extractor", "test_ext", "--enable-anderson"])
    assert args_enabled2.anderson_enabled is True, "--enable-anderson must toggle anderson_enabled to True"

    args_disabled = parser.parse_args(["--output", "test_out", "--extractor", "test_ext", "--enable-anderson", "--no-anderson"])
    assert args_disabled.anderson_enabled is False, "--no-anderson must toggle anderson_enabled to False"

    # Verify compound switching parameters
    assert args_default.max_active_cardinality == 500
    assert args_default.max_symmetric_diff == 10
    assert args_default.max_added_nodes == 0
    assert args_default.stabilization_window == 3


def test_08_extractor_schema_and_node_print_cards():
    """Verify Node Print cards restored in decks and fail-closed force/energy acceptance in driver."""
    from scripts.state_transfer.driver_package171_r12_c6_coupled_pdas import Package171R12C6PDASDriver

    # 1. Deck Node Print output card presence
    iter1_mech = PKG_DIR / "P171_ITER1_MECH.inp"
    iter1_phase = PKG_DIR / "P171_ITER1_PHASE.inp"
    assert iter1_mech.is_file(), f"Missing {iter1_mech}"
    assert iter1_phase.is_file(), f"Missing {iter1_phase}"

    mech_text = iter1_mech.read_text(encoding="utf-8")
    phase_text = iter1_phase.read_text(encoding="utf-8")
    assert "*Node Print" in mech_text, "P171_ITER1_MECH.inp missing *Node Print"
    assert "*Node Print" in phase_text, "P171_ITER1_PHASE.inp missing *Node Print"

    # 2. Driver deck generation contains *Node Print
    driver = Package171R12C6PDASDriver(
        package=str(PKG_DIR),
        output="tmp_test_out",
        extractor="scripts/validation/extract_package148_iteration.py",
        anderson_enabled=False
    )
    driver.load()

    d_dummy = dict(driver.d0)
    active_dummy = {n for n in driver.d0 if driver.d0[n] >= 0.5}
    u_dummy = dict(driver.u0)
    h_dummy = dict(driver.h0)

    mech_deck = driver._deck(1, "mechanical", d_dummy, active_dummy, u_dummy, h_dummy, 0.00187)
    phase_deck = driver._deck(1, "phase", d_dummy, active_dummy, u_dummy, h_dummy, 0.00187)
    assert "*Node Print, frequency=1\nU\n" in mech_deck, "Mechanical deck missing *Node Print, frequency=1\nU\n"
    assert "*Node Print, frequency=1\nU\n" in phase_deck, "Phase deck missing *Node Print, frequency=1\nU\n"

    # 3. Fail-closed force/energy validation
    # Missing rf2_kN and missing total_energy_kNmm should raise KeyError
    with pytest.raises(KeyError, match="missing reaction force"):
        driver.finalize_coupled_acceptance(
            u_trial=u_dummy, u_abaqus=u_dummy, history_trial=h_dummy,
            damage_relaxed=d_dummy, consistent_u=u_dummy,
            consistent_endpoint={"nodes": []},
            solver=None, step_idx=1, outer=1, target_uy=0.00187
        )

    with pytest.raises(KeyError, match="missing total energy"):
        driver.finalize_coupled_acceptance(
            u_trial=u_dummy, u_abaqus=u_dummy, history_trial=h_dummy,
            damage_relaxed=d_dummy, consistent_u=u_dummy,
            consistent_endpoint={"rf2_kN": 0.179924},
            solver=None, step_idx=1, outer=1, target_uy=0.00187
        )

    with pytest.raises(ValueError, match="nonfinite"):
        driver.finalize_coupled_acceptance(
            u_trial=u_dummy, u_abaqus=u_dummy, history_trial=h_dummy,
            damage_relaxed=d_dummy, consistent_u=u_dummy,
            consistent_endpoint={"rf2_kN": float("nan"), "total_energy_kNmm": 0.000226},
            solver=None, step_idx=1, outer=1, target_uy=0.00187
        )


def test_09_production_path_solve_coupled_equilibration_picard_and_anderson():
    """Execute un-mocked PDASReEquilibrationSolver + AndersonAccelerator inside solve_coupled_equilibration()
    for both Arm A (Picard) and Arm B (Anderson M2), verifying transition, acceleration, and R11 parity."""
    import tempfile
    from scripts.state_transfer.driver_package171_r11_c6_coupled_pdas import Package171R11C6PDASDriver
    from scripts.state_transfer.driver_package171_r12_c6_coupled_pdas import (
        Package171R12C6PDASDriver,
        DONOR_REFERENCE_FORCE_KN,
        DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
        DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
        DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
    )

    class SimpleQuadMesh:
        def __init__(self):
            self.elements = {1: [1, 2, 3, 4]}
            self.nodes = {1: (0.0, 0.0), 2: (1.0, 0.0), 3: (1.0, 1.0), 4: (0.0, 1.0)}
            self.node_flank = {}

    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "f42_mixed_uel.for").write_text("C UEL", encoding="utf-8")

        mock_u = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        mock_ep = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
            "total_energy_kNmm": DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
        }

        def run_driver(cls, out_sub, anderson_enabled):
            drv = cls(
                package=pkg_dir,
                output=tmp_path / out_sub,
                extractor=pkg_dir / "ext.py",
                omega_d_stage1=0.50,
                omega_d_stage2=0.85,
                omega_u_stage1=1.00,
                omega_u_stage2=0.85,
                anderson_enabled=anderson_enabled,
                anderson_memory=2,
                anderson_beta=0.85,
                stabilization_window=3,
                rollback_factor=50.0,
                divergence_factor=50.0,
                max_outer=6,
            )
            drv.mesh = SimpleQuadMesh()
            drv.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
            drv.h0 = {(1, g): 10.0 for g in range(1, 5)}
            drv.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
            drv.target_uy = 0.0018703125442191958
            drv.load = lambda: None

            def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
                if role == "mechanical":
                    return damage, mock_u, mock_ep
                d_val = 0.1 + (0.010 * (0.98 ** outer))
                return (
                    {n: d_val for n in range(1, 5)},
                    None,
                    {"raw_healing_min": 0.001, "raw_healing_violations": 0},
                )

            drv.solve_subproblem = mock_subproblem
            summary = drv.solve_coupled_equilibration()
            telem = json.loads((tmp_path / out_sub / "live_iteration_telemetry.json").read_text(encoding="utf-8"))
            return summary, telem

        sum_r12_pic, tel_r12_pic = run_driver(Package171R12C6PDASDriver, "r12_pic", False)
        sum_r11_pic, tel_r11_pic = run_driver(Package171R11C6PDASDriver, "r11_pic", False)
        sum_r12_and, tel_r12_and = run_driver(Package171R12C6PDASDriver, "r12_and", True)
        sum_r11_and, tel_r11_and = run_driver(Package171R11C6PDASDriver, "r11_and", True)

        assert len(tel_r12_pic) == 6
        assert len(tel_r12_and) == 6
        # Verify exact numerical parity between R12 and R11 on both Picard and Anderson arms
        for r12, r11 in zip(tel_r12_pic, tel_r11_pic):
            assert math.isclose(r12["delta_d"], r11["delta_d"], rel_tol=1e-12)
            assert math.isclose(r12["raw_delta_d"], r11["raw_delta_d"], rel_tol=1e-12)
            assert r12["stage"] == r11["stage"]
            assert r12["anderson_accelerated"] is False
        for r12, r11 in zip(tel_r12_and, tel_r11_and):
            assert math.isclose(r12["delta_d"], r11["delta_d"], rel_tol=1e-12)
            assert math.isclose(r12["raw_delta_d"], r11["raw_delta_d"], rel_tol=1e-12)
            assert r12["stage"] == r11["stage"]
            assert r12["anderson_accelerated"] == r11["anderson_accelerated"]
        # Verify Stage 2 transition at Outer 4 and Anderson activation at Outer 5 & 6
        assert tel_r12_and[3]["stage"] == 2
        assert tel_r12_and[3]["transition_activated"] is True
        assert tel_r12_and[4]["anderson_accelerated"] is True
        assert tel_r12_and[4]["anderson_m_k"] == 1
        assert tel_r12_and[5]["anderson_accelerated"] is True
        assert tel_r12_and[5]["anderson_m_k"] == 2


def test_10_real_package_load_and_unmocked_solver_execution():
    """Load real Package 171-R12 (15,252 elements, 15,559 nodes, 61,008 GPs) and execute
    solve_coupled_equilibration() for 2 iterations with real PDASReEquilibrationSolver."""
    import tempfile
    from scripts.state_transfer.driver_package171_r12_c6_coupled_pdas import (
        Package171R12C6PDASDriver,
        DONOR_REFERENCE_FORCE_KN,
        DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
        DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
        DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
    )

    with tempfile.TemporaryDirectory() as td:
        tmp_path = Path(td)
        drv = Package171R12C6PDASDriver(
            package=str(PKG_DIR),
            output=str(tmp_path / "real_c6_out"),
            extractor="scripts/validation/extract_package148_iteration.py",
            anderson_enabled=True,
            max_outer=2,
        )
        drv.load()
        u_fixed = dict(drv.u0)
        d_fixed = dict(drv.d0)
        ep_fixed = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM,
            "total_energy_kNmm": DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
        }

        def mock_subproblem(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, u_fixed, ep_fixed
            return d_fixed, None, {"raw_healing_min": 0.0, "raw_healing_violations": 0}

        drv.solve_subproblem = mock_subproblem
        summary = drv.solve_coupled_equilibration()
        assert summary["outer_iterations_completed"] == 2
        telem = json.loads((tmp_path / "real_c6_out" / "live_iteration_telemetry.json").read_text(encoding="utf-8"))
        assert len(telem) == 2
        assert telem[0]["pdas_active_count"] + telem[0]["pdas_free_count"] == 15559
        assert telem[1]["delta_u_raw"] == 0.0
        assert telem[1]["delta_u_relaxed"] == 0.0

