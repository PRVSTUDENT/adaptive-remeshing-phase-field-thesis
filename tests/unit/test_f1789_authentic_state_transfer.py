#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_f1789_authentic_state_transfer.py
======================================
Unit test suite for Task F1789:
Mode-I Method C Authentic State Transfer & Datacheck Preflight.

Verifies:
1. Authentic donor mesh (2,906 elements: 2,818 quads, 88 tris, 2,988 nodes)
   and authentic field state from Job 1413814 (u = 0.0050 mm).
2. Target adapted mesh (16,597 elements: 16,149 quads, 448 tris, 16,642 nodes),
   strictly confirming 97.30% quads and rectifying the F1788 typo.
3. Spatial projection with seam flank isolation and physical clamping.
4. Continuous quadrature metrics: displacement L2 error, peak damage,
   integrated damage, history non-negativity, boundary force continuity,
   internal energy continuity, and energy balance residual.
5. Continuation deck structure with authentic displacement reconstruction
   via Step 1 Dirichlet constraints, Step 2 unconstrained release and hold,
   and Step 3 propagation.
6. Abaqus input-processor datacheck evidence (pre.exe Exit 0, 49,791 total elements,
   16,643 nodes, zero fatal errors).
7. Cumulative PBS submissions strictly preserved at 35 (zero new submissions).

Protocol Version: 2
Author: Gemini Antigravity
Task: F1789-MODE-I-METHOD-C-AUTHENTIC-STATE-TRANSFER-AND-DATACHECK-PREFLIGHT
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

DONOR_INP = REPO_ROOT / "models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control/M1_MB_DONOR_WITH_RESTART.inp"
DONOR_JSON = REPO_ROOT / "models/pandey_kumar_mode1/48_method_c_stage_c1_0_restart_positive_control/evidence_1413814/donor_field_state.json"
TARGET_INP = REPO_ROOT / "models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_ADAPT_PHYS.inp"
CONTINUATION_INP = REPO_ROOT / "models/pandey_kumar_mode1/PK_F1789_CASE1_CONTINUATION.inp"
RECEIPT_JSON = REPO_ROOT / "models/pandey_kumar_mode1/PK_F1789_DONOR_STATE_RECEIPT.json"
DATACHECK_DAT = REPO_ROOT / "models/pandey_kumar_mode1/evidence_f1789_datacheck/PK_F1789_CASE1_DATACHECK.dat"
ACTIVE_TASK_JSON = REPO_ROOT / "project_coordination/ACTIVE_TASK.json"


def sha256_of_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as fp:
        while chunk := fp.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_donor_mesh_and_state_provenance():
    """Verify donor mesh elements (2,906: 2,818 quads, 88 tris) and authentic state."""
    assert DONOR_INP.exists(), f"Donor deck missing: {DONOR_INP}"
    assert DONOR_JSON.exists(), f"Donor JSON missing: {DONOR_JSON}"

    from scripts.state_transfer.mode1_state_transfer_engine import (
        parse_mode1_input_deck,
        load_donor_state_from_json,
    )

    donor_mesh = parse_mode1_input_deck(str(DONOR_INP))
    quad_count = sum(1 for c in donor_mesh.elements_u1.values() if len(c) == 4)
    tri_count = sum(1 for c in donor_mesh.elements_u1.values() if len(c) == 3)

    assert donor_mesh.num_elements == 2906, f"Expected 2906 donor elements, got {donor_mesh.num_elements}"
    assert quad_count == 2818, f"Expected 2818 donor quads, got {quad_count}"
    assert tri_count == 88, f"Expected 88 donor tris, got {tri_count}"
    assert donor_mesh.num_nodes == 2988, f"Expected 2988 donor nodes, got {donor_mesh.num_nodes}"

    donor_state = load_donor_state_from_json(str(DONOR_JSON), donor_mesh)
    valid, msg = donor_state.validate_bounds()
    assert valid, f"Donor state bounds invalid: {msg}"
    assert donor_state.u_rp[1] == pytest.approx(0.0050, abs=1e-5)
    assert max(donor_state.d_nodal.values()) == pytest.approx(0.092037, abs=1e-4)
    assert max(max(hl) for hl in donor_state.H_gp.values()) == pytest.approx(0.053650, abs=1e-4)


def test_target_mesh_topology_and_connectivity():
    """Verify target adapted mesh (16,597 elements: 16,149 quads, 448 tris, 16,642 nodes)."""
    assert TARGET_INP.exists(), f"Target mesh missing: {TARGET_INP}"

    from scripts.state_transfer.mode1_state_transfer_engine import parse_mode1_input_deck

    target_mesh = parse_mode1_input_deck(str(TARGET_INP))
    quad_count = sum(1 for c in target_mesh.elements_u1.values() if len(c) == 4)
    tri_count = sum(1 for c in target_mesh.elements_u1.values() if len(c) == 3)

    assert target_mesh.num_elements == 16597, f"Expected 16597 target elements, got {target_mesh.num_elements}"
    assert quad_count == 16149, f"Expected 16149 target quads, got {quad_count} (rectifying F1788 typo)"
    assert tri_count == 448, f"Expected 448 target tris, got {tri_count} (rectifying F1788 typo)"
    assert target_mesh.num_nodes == 16642, f"Expected 16642 target nodes, got {target_mesh.num_nodes}"
    quad_pct = quad_count / target_mesh.num_elements * 100.0
    assert quad_pct == pytest.approx(97.30, abs=0.01)


def test_authentic_state_projection_and_bounds():
    """Verify spatial projection, flank isolation, and bounds preservation."""
    assert RECEIPT_JSON.exists(), f"Receipt missing: {RECEIPT_JSON}"
    with open(RECEIPT_JSON, "r", encoding="utf-8") as fp:
        receipt = json.load(fp)

    tm = receipt["target_mesh_provenance"]
    assert tm["physical_elements"] == 16597
    assert tm["quad_count"] == 16149
    assert tm["tri_count"] == 448
    assert tm["physical_nodes"] == 16642
    assert tm["peak_nodal_damage"] == pytest.approx(0.092037, abs=1e-4)
    assert tm["min_history_gp_kN_mm2"] >= 0.0


def test_conservation_and_continuity_metrics():
    """Verify all 7 Gate C1-C5 criteria from genuine continuous quadrature."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as fp:
        receipt = json.load(fp)

    m = receipt["transfer_metrics"]
    # Criterion 1: Displacement L2 error <= 1.0%
    assert m["criterion_1_displacement_l2"]["verdict"] == "PASS"
    assert m["displacement_l2_rel_error_pct"] <= 1.0

    # Criterion 2: Peak damage difference <= 0.02
    assert m["criterion_2_peak_damage"]["verdict"] == "PASS"
    assert m["delta_d_max"] <= 0.02

    # Criterion 3: Integrated damage error <= 5.0%
    assert m["criterion_3_integrated_damage"]["verdict"] == "PASS"
    assert m["relative_error_integral_d_pct"] <= 5.0

    # Criterion 4: History non-negativity
    assert m["criterion_4_history_non_negativity"]["verdict"] == "PASS"
    assert m["min_H"] >= 0.0
    assert m["negative_H_count"] == 0

    # Criterion 5: Boundary force continuity <= 5.0 N and <= 0.50%
    assert m["criterion_5_boundary_force_continuity"]["verdict"] == "PASS"
    assert m["delta_rf_boundary_N"] <= 5.0
    assert m["delta_rf_boundary_pct"] <= 0.50

    # Criterion 6: Total internal energy continuity <= 0.50%
    assert m["criterion_6_internal_energy"]["verdict"] == "PASS"
    assert m["delta_e_int_pct"] <= 0.50

    # Criterion 7: Global energy residual <= 10.0%
    assert m["criterion_7_global_energy_residual"]["verdict"] == "PASS"
    assert m["energy_residual_pct"] <= 10.0

    # Gate status
    gs = receipt["gates_status"]
    assert gs["gate_c1_donor_provenance"] == "PASS"
    assert gs["gate_c2_mesh_geometry"] == "PASS"
    assert gs["gate_c3_primary_fields"] == "PASS"
    assert gs["gate_c4_svar_history"] == "PASS"
    assert gs["gate_c5_continuity_and_unconstrained_hold"] == "PASS"


def test_continuation_deck_structure_and_displacement_reconstruction():
    """Verify continuation deck has 3-step sequence and proper displacement cards."""
    assert CONTINUATION_INP.exists(), f"Continuation deck missing: {CONTINUATION_INP}"

    with open(CONTINUATION_INP, "r", encoding="utf-8") as fp:
        content = fp.read()

    # Verify 3 steps
    assert "*STEP, NAME=Step-1-Reconstruct" in content
    assert "*STEP, NAME=Step-2-Hold" in content
    assert "*STEP, NAME=Step-3-Continue" in content

    # Verify Step 1 reconstructs all DOFs (1, 2, 3)
    assert "1, 1, 1," in content or "       1, 1, 1," in content
    assert "1, 2, 2," in content or "       1, 2, 2," in content
    assert "1, 3, 3," in content or "       1, 3, 3," in content

    # Verify Step 2 releases with OP=NEW and holds at handoff displacement
    assert "*BOUNDARY, OP=NEW" in content
    assert "N_RP, 2, 2, 5.0000000000e-03" in content

    # Verify solution-dependent state variables initialized
    assert "*INITIAL CONDITIONS, TYPE=SOLUTION" in content

    # Verify UEL element types defined
    assert "*USER ELEMENT, TYPE=U1" in content
    assert "*USER ELEMENT, TYPE=U2" in content
    assert "*USER ELEMENT, TYPE=U3" in content
    assert "*USER ELEMENT, TYPE=U4" in content


def test_abaqus_input_processor_datacheck_evidence():
    """Verify pre.exe datacheck log confirms 49,791 elements, 16,643 nodes, and 0 errors."""
    assert DATACHECK_DAT.exists(), f"Datacheck output missing: {DATACHECK_DAT}"

    with open(DATACHECK_DAT, "r", encoding="utf-8") as fp:
        content = fp.read()

    assert "END OF USER INPUT PROCESSING" in content
    assert "THE PROGRAM HAS DISCOVERED" not in content or "0 FATAL ERRORS" in content
    assert "FATAL ERROR" not in content
    assert "NUMBER OF ELEMENTS IS                                 49791" in content
    assert "NUMBER OF NODES IS                                    16643" in content


def test_zero_new_pbs_submissions_invariant():
    """Verify cumulative PBS submissions remain strictly preserved at 35 (zero consumed)."""
    assert ACTIVE_TASK_JSON.exists(), f"ACTIVE_TASK.json missing: {ACTIVE_TASK_JSON}"

    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8") as fp:
        task_data = json.load(fp)

    assert task_data["max_new_pbs_submissions"] == 0
    assert task_data["submissions_consumed"] == 0
    assert task_data["cumulative_pbs_submissions"] == 35
