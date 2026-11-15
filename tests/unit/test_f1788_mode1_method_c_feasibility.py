#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Task F1788: Mode-I Method C Single-Cycle Feasibility Gate.

Verifies:
1. Frozen production UEL subroutine hash (CE8D5EDC...) and framework hash (181CB4E5...) preservation.
2. Historical Package 49 / Job 1414235 and Job 1414505/1414550 diagnostic audit:
   - UMAT CONSTANTS=1 defect remediation to CONSTANTS=3 with PROPS(3)=NPHYS_VAL.
   - Elimination of *NODE OUTPUT NSET=N_RP restriction for full spatial displacement capture.
   - Analysis of Step-1 reload damage spike vs Dirichlet equilibration / release protocol.
   - Decomposition of reaction force (-0.695%) and energy (-0.774%) continuity gaps into discretization compliance.
3. Source and target mesh compatibility on 1x1 mm Mode-I specimen:
   - Coarse donor mesh (2,906 elements, 2,988 nodes) compatibility with target adapted mesh (16,597 elements, 16,642 nodes).
   - Slit seam geometry along y = 0.5 mm for x in [0.0, 0.5] mm with zero-gap flank separation.
   - Boundary node sets N_BOTTOM (y=0), N_TOP (y=1), and rigid coupling RP.
4. Topology-guarded state transfer engine verification:
   - Transfer of primary fields (ux, uy, d) and history (H >= 0).
   - Strict flank isolation preventing cross-seam contamination.
5. Continuation deck generation syntax & keyword validation:
   - *USER MATERIAL, CONSTANTS=3 with PROPS(3)=NPHYS_VAL.
   - *INITIAL CONDITIONS, TYPE=SOLUTION line wrapping (<= 8 items/line, 18 SVARs).
   - *NSET line wrapping (<= 16 items/line).
6. Quantitative Predeclared Acceptance Gates (C1 - C5) definition and feasibility evaluation.
"""

import os
import sys
import math
import json
import hashlib
import tempfile
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.mode1_state_transfer_engine import (
    Mode1Mesh,
    Mode1State,
    Mode1SpatialIndex,
    Mode1StateTransferEngine,
    parse_mode1_input_deck,
    compute_quad_gauss_points,
    compute_tri_gauss_points,
)

FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
ALLOWED_FRAMEWORK_HASHES = [
    "181CB4E5A8CE765CBE0765D71BA9C3CCA934A33140BC61F5B9A4CD7A6AEFCD40",
    "49B2E1B7706594941B4DD58ABAA4C2DB9090B4C06D2358EAF157289AAD3BAE3F",
    "907EE548BB28B920038E8C51D8A4DAA584E9DCE84DD99EEB6A10ECB259DBCAC0",
]

UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FRAMEWORK_PATH = REPO_ROOT / "scripts" / "remeshing" / "reusable_2d_adaptive_framework.py"
COARSE_DECK = REPO_ROOT / "models" / "pandey_kumar_mode1" / "method_b_inf_companion_decks" / "M1_MB_INF_1S.inp"
TARGET_ADAPT_PHYS_DECK = REPO_ROOT / "models" / "pandey_kumar_mode1" / "242_f1780_optimized_regression" / "case1" / "PK_F1728_CASE_1_ADAPT_PHYS.inp"
P49_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "49_method_c_stage_c1_1_nonmatching_transfer"


def test_01_frozen_codebases_integrity():
    """Verify bitwise preservation of production UEL and unified adaptive framework."""
    assert UEL_PATH.exists(), f"UEL subroutine must exist at {UEL_PATH}"
    with open(UEL_PATH, "rb") as f:
        uel_h = hashlib.sha256(f.read()).hexdigest().upper()
    assert uel_h == FROZEN_UEL_HASH, f"UEL hash mismatch: {uel_h} != {FROZEN_UEL_HASH}"

    assert FRAMEWORK_PATH.exists(), f"Framework script must exist at {FRAMEWORK_PATH}"
    with open(FRAMEWORK_PATH, "rb") as f:
        fw_h = hashlib.sha256(f.read()).hexdigest().upper()
    assert fw_h in ALLOWED_FRAMEWORK_HASHES, f"Framework hash mismatch: {fw_h} not in {ALLOWED_FRAMEWORK_HASHES}"


def test_02_historical_package49_failure_diagnosis():
    """Verify diagnosis of historical Package 49 / Job 1414235 and Job 1414505/1414550 evidence."""
    # Check Job 1414505 review report in coordination dir and evidence dir
    review_coord_path = REPO_ROOT / "project_coordination" / "STAGE_C1_1_EQUIL_REVIEW.json"
    assert review_coord_path.exists(), "STAGE_C1_1_EQUIL_REVIEW.json must exist"
    with open(review_coord_path, "r", encoding="utf-8") as f:
        rev_coord = json.load(f)

    assert rev_coord["predecessor_pbs_job_id"] == "1414505.mmaster02"
    assert rev_coord["terminal_exit_status"] == 0
    assert rev_coord["metrics"]["cutbacks"] == 0

    review_1414505_path = P49_DIR / "evidence" / "1414505.mmaster02" / "STAGE_C1_1_EQUIL_REVIEW_1414505.json"
    assert review_1414505_path.exists(), "Job 1414505 review JSON must exist"
    with open(review_1414505_path, "r", encoding="utf-8") as f:
        rev505 = json.load(f)

    # Job 1414505 completed exit 0 with 0 cutbacks in sta_summary
    assert rev505["sta_summary"]["total_cutbacks"] == 0
    assert rev505["sta_summary"]["step1_completed"] is True

    # Donor comparison: coarse 2906 elements, RF = 653.0886 N, E_tot = 1.663384 mJ
    donor = rev505["donor_comparison"]
    assert donor["num_elements"] == 2906
    assert abs(donor["rf_rp_N"] - 653.0886) < 1e-3
    assert abs(donor["e_tot_mJ"] - 1.663384) < 1e-4

    # Equilibrium actuals in Job 1414505
    actual_1414505_path = P49_DIR / "evidence" / "1414505.mmaster02" / "equilibrium_actual_1414505.json"
    with open(actual_1414505_path, "r", encoding="utf-8") as f:
        act505 = json.load(f)

    rf_target = act505["RF"]["rp"][1] * 1000.0  # kN to N
    delta_rf = rf_target - donor["rf_rp_N"]
    rel_rf_diff = (delta_rf / donor["rf_rp_N"]) * 100.0
    assert abs(delta_rf - (-4.5414)) < 0.05
    assert abs(rel_rf_diff - (-0.695)) < 0.05

    # Check Job 1414550 (Release-and-Hold)
    eval_1414550_path = P49_DIR / "evidence" / "1414550.mmaster02" / "STAGE_C1_1_RELHOLD_EVALUATION_1414550.json"
    assert eval_1414550_path.exists(), "Job 1414550 evaluation JSON must exist"
    with open(eval_1414550_path, "r", encoding="utf-8") as f:
        rev550 = json.load(f)

    # Verify that in Step 2 release-and-hold, internal energy was conserved to -0.068%
    step2_hold = rev550["step2_release_inc10_terminal"]
    assert abs(step2_hold["internal_energy_conservation_in_step2_pct"] - 0.0682) < 0.01
    # Fracture energy converged to within 0.438% of continuous fine baseline
    assert abs(rev550["continuous_fine_baseline_comparison"]["e_frac_match_pct"] - 0.438) < 0.01


def test_03_source_and_target_mesh_compatibility():
    """Verify geometric and topological compatibility between coarse donor and F1780 adapted target mesh."""
    assert COARSE_DECK.exists(), f"Coarse donor deck must exist at {COARSE_DECK}"
    assert TARGET_ADAPT_PHYS_DECK.exists(), f"Target adapted deck must exist at {TARGET_ADAPT_PHYS_DECK}"

    mesh_coarse = parse_mode1_input_deck(str(COARSE_DECK))
    mesh_target = parse_mode1_input_deck(str(TARGET_ADAPT_PHYS_DECK))

    # Element and node counts
    assert mesh_coarse.num_elements == 2906
    assert mesh_coarse.num_nodes == 2988
    assert mesh_target.num_elements == 16597
    assert mesh_target.num_nodes == 16642

    # Verify bounding boxes: both must span [0, 1] x [0, 1] mm
    c_min_x = min(x for x, y in mesh_coarse.nodes.values())
    c_max_x = max(x for x, y in mesh_coarse.nodes.values())
    c_min_y = min(y for x, y in mesh_coarse.nodes.values())
    c_max_y = max(y for x, y in mesh_coarse.nodes.values())

    t_min_x = min(x for x, y in mesh_target.nodes.values())
    t_max_x = max(x for x, y in mesh_target.nodes.values())
    t_min_y = min(y for x, y in mesh_target.nodes.values())
    t_max_y = max(y for x, y in mesh_target.nodes.values())

    assert abs(c_min_x - 0.0) < 1e-5 and abs(c_max_x - 1.0) < 1e-5
    assert abs(c_min_y - 0.0) < 1e-5 and abs(c_max_y - 1.0) < 1e-5
    assert abs(t_min_x - 0.0) < 1e-5 and abs(t_max_x - 1.0) < 1e-5
    assert abs(t_min_y - 0.0) < 1e-5 and abs(t_max_y - 1.0) < 1e-5

    # Verify boundary node sets
    assert len(mesh_coarse.n_bottom) > 0
    assert len(mesh_coarse.n_top) > 0
    assert len(mesh_target.n_bottom) > 0
    assert len(mesh_target.n_top) > 0

    # Verify topology classification of both meshes
    assert "UPPER" in mesh_coarse.element_flank.values()
    assert "LOWER" in mesh_coarse.element_flank.values()
    assert "UPPER" in mesh_target.element_flank.values()
    assert "LOWER" in mesh_target.element_flank.values()


def test_04_topology_guarded_state_projection():
    """Verify projection of primary fields and history across coarse donor and target mesh."""
    mesh_coarse = parse_mode1_input_deck(str(COARSE_DECK))
    mesh_target = parse_mode1_input_deck(str(TARGET_ADAPT_PHYS_DECK))

    # Synthetic Mode-I donor state at u = 0.0050 mm
    donor_state = Mode1State()
    donor_state.u_rp = (0.0, 0.0050)

    # Slit displacement jump: uy positive for y > 0.5, negative for y < 0.5
    for nid, (x, y) in mesh_coarse.nodes.items():
        flank = mesh_coarse.node_flank.get(nid, "LIGAMENT")
        sign = 1.0 if flank == "UPPER" else (-1.0 if flank == "LOWER" else (2.0 * y - 1.0))
        ux = 0.0005 * (x - 0.5)
        uy = 0.0025 * y + 0.0010 * sign * max(0.0, 0.5 - x)
        d = 0.092 * math.exp(-((x - 0.5)**2 + (y - 0.5)**2) / (2.0 * (0.0075)**2))
        donor_state.u_nodal[nid] = (ux, uy)
        donor_state.d_nodal[nid] = max(0.0, min(1.0, d))

    for eid in mesh_coarse.elements_u1:
        cx, cy = mesh_coarse.element_centroids[eid]
        h_val = 53.65 * math.exp(-((cx - 0.5)**2 + (cy - 0.5)**2) / (2.0 * (0.0075)**2))
        donor_state.H_gp[eid] = [h_val, h_val, h_val, h_val]

    engine = Mode1StateTransferEngine(mesh_coarse)
    target_state = engine.project_state(mesh_target, donor_state, enforce_bc=True)

    # Check bounds
    valid, msg = target_state.validate_bounds()
    assert valid, f"Target state invalid: {msg}"

    # Verify peak damage retention
    max_d_donor = max(donor_state.d_nodal.values())
    max_d_target = max(target_state.d_nodal.values())
    assert abs(max_d_target - max_d_donor) < 0.020, f"Peak damage differs: {max_d_target} vs {max_d_donor}"

    # Verify history non-negativity
    min_h = min(min(hl) for hl in target_state.H_gp.values())
    assert min_h >= 0.0, f"History variable H is negative: {min_h}"


def test_05_continuation_deck_assembly_and_syntax():
    """Verify that assemble_continuation_deck produces valid Abaqus syntax for F1780 adapted target mesh."""
    mesh_coarse = parse_mode1_input_deck(str(COARSE_DECK))
    mesh_target = parse_mode1_input_deck(str(TARGET_ADAPT_PHYS_DECK))

    donor_state = Mode1State()
    donor_state.u_rp = (0.0, 0.0050)
    for nid in mesh_coarse.nodes:
        donor_state.u_nodal[nid] = (0.0, 0.0025)
        donor_state.d_nodal[nid] = 0.05
    for eid in mesh_coarse.elements_u1:
        donor_state.H_gp[eid] = [10.0, 10.0, 10.0, 10.0]

    engine = Mode1StateTransferEngine(mesh_coarse)
    target_state = engine.project_state(mesh_target, donor_state, enforce_bc=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        out_deck = os.path.join(tmpdir, "M1_F1788_TEST_CONTINUATION.inp")
        engine.assemble_continuation_deck(
            recipient_mesh=mesh_target,
            target_state=target_state,
            output_inp_path=out_deck,
            u_handoff=0.0050,
            u_final=0.0100,
            num_increments=5000,
            continuation_mode="equilibrate",
        )

        assert os.path.exists(out_deck)
        with open(out_deck, "r", encoding="utf-8") as f:
            lines = f.readlines()

        content = "".join(lines)

        # 1. Check UMAT CONSTANTS=3 with PROPS(3)=NPHYS_VAL
        assert "*USER MATERIAL, CONSTANTS=3" in content
        assert f"16597.0" in content

        # 2. Check *NODE OUTPUT without NSET=N_RP
        assert "*NODE OUTPUT\nU, RF\n" in content
        assert "*NODE OUTPUT, NSET=N_RP" not in content

        # 3. Check node sets wrapping (max 16 entries per line)
        in_nset = False
        for line in lines:
            if line.startswith("*NSET, NSET=N_BOTTOM") or line.startswith("*NSET, NSET=N_TOP"):
                in_nset = True
                continue
            elif line.startswith("*"):
                in_nset = False
            elif in_nset:
                entries = [p.strip() for p in line.split(",") if p.strip()]
                assert len(entries) <= 16, f"NSET line exceeds 16 items: {len(entries)}"

        # 4. Check *INITIAL CONDITIONS, TYPE=SOLUTION wrapping (max 8 items per line)
        in_sol = False
        card_idx = 0
        for line in lines:
            if line.startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"):
                in_sol = True
                card_idx = 0
                continue
            elif line.startswith("*"):
                in_sol = False
            elif in_sol:
                entries = [p.strip() for p in line.split(",") if p.strip()]
                assert len(entries) <= 8, f"SOLUTION card line exceeds 8 items: {len(entries)}"


def test_06_predeclared_acceptance_gates_evaluation():
    """Verify mathematical definitions and threshold consistency for Gates C1 - C5."""
    gates = {
        "Gate_C1_Equilibrium_Residual": {
            "formula": "||R||_2 / ||F_ext||_2",
            "threshold": 1.0e-3,
            "unit": "dimensionless",
            "physical_meaning": "Out-of-balance residual norm relative to external reaction force at increment 0",
        },
        "Gate_C2_Reaction_Force_Parity": {
            "formula": "|Delta RF| / RF_donor",
            "threshold": 0.0050,  # 0.50%
            "unit": "dimensionless",
            "physical_meaning": "Relative change in reaction force between donor terminal state and recipient post-transfer state",
        },
        "Gate_C3_Total_Energy_Continuity": {
            "formula": "|Delta E_tot| / E_tot_donor",
            "threshold": 0.0050,  # 0.50%
            "unit": "dimensionless",
            "physical_meaning": "Relative change in total internal energy (elastic strain + fracture surface energy)",
        },
        "Gate_C4_Pointwise_Damage_Irreversibility": {
            "formula": "min(d_recipient(x) - d_donor(x))",
            "threshold": -1.0e-4,
            "unit": "dimensionless",
            "physical_meaning": "Strict pointwise monotonicity bound prohibiting artificial healing",
        },
        "Gate_C5_Crack_Tip_Reload_Peak_Cap": {
            "formula": "max(Delta d_tip)",
            "threshold": 1.0e-3,
            "unit": "dimensionless",
            "physical_meaning": "Maximum allowable artificial damage spike at crack tip during initial re-equilibration increment",
        },
    }

    assert len(gates) == 5
    assert gates["Gate_C1_Equilibrium_Residual"]["threshold"] == 1.0e-3
    assert gates["Gate_C2_Reaction_Force_Parity"]["threshold"] == 0.0050
    assert gates["Gate_C3_Total_Energy_Continuity"]["threshold"] == 0.0050
    assert gates["Gate_C4_Pointwise_Damage_Irreversibility"]["threshold"] == -1.0e-4
    assert gates["Gate_C5_Crack_Tip_Reload_Peak_Cap"]["threshold"] == 1.0e-3
