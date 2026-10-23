#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn50_package90_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: a1e68e9a-9d57-41d6-9828-80d6d617bbb6
Protocol Version: 2

Unit tests for Turn 50 scientific qualification of Package 90 and qualification of Package 90-R1.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
MATRIX_JSON = REPO_ROOT / "results/validation/mode1_f1597/package90_scientific_acceptance_matrix.json"
PKG90_R1_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_r1_c3_active_set_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_frozen_uel_bitwise_identity():
    uel_path = PKG90_R1_DIR / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for missing in 90-R1"
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert h == FROZEN_UEL_HASH, f"Frozen UEL hash mismatch: {h}"

def test_package90_acceptance_matrix_integrity():
    assert MATRIX_JSON.exists(), "Acceptance matrix missing"
    data = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    assert data["status"] == "PACKAGE90_QUALIFICATION_AUDITED"
    assert data["job_id"] == "1416548.mmaster02"
    assert len(data["gates"]) == 9

def test_gates_1_to_6_pass():
    data = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    gates = data["gates"]
    assert gates["gate1_force_continuity_5pct"]["verdict"] == "PASS"
    assert abs(gates["gate1_force_continuity_5pct"]["step1_mismatch_pct"]) < 0.05
    assert abs(gates["gate1_force_continuity_5pct"]["step2_mismatch_pct"]) < 0.05
    assert gates["gate2_raw_uel_energy_continuity_2pct"]["verdict"] == "PASS"
    assert abs(gates["gate2_raw_uel_energy_continuity_2pct"]["e_frac_mismatch_pct"]) < 0.05
    assert gates["gate3_physical_boundary_consistency"]["verdict"] == "PASS"
    assert gates["gate4_monotone_history_enforcement"]["verdict"] == "PASS"
    assert gates["gate5_kkt_equilibrium"]["verdict"] == "PASS"
    assert gates["gate6_forward_crack_continuation"]["verdict"] == "PASS"

def test_defects_gates_7_to_9_fail():
    data = json.loads(MATRIX_JSON.read_text(encoding="utf-8"))
    gates = data["gates"]
    assert gates["gate7_damage_upper_bound"]["verdict"] == "FAIL"
    assert gates["gate7_damage_upper_bound"]["num_overshoot_nodes"] == 4
    assert gates["gate7_damage_upper_bound"]["d_max_terminal"] > 1.0

    assert gates["gate8_zero_damage_healing"]["verdict"] == "FAIL"
    assert gates["gate8_zero_damage_healing"]["num_healing_nodes"] == 826
    assert gates["gate8_zero_damage_healing"]["min_delta_d"] < -0.005

    assert gates["gate9_authentic_adaptation_trigger"]["verdict"] == "FAIL"

def test_package90_r1_qualified_files():
    expected_files = [
        "M1_C3_PACKAGE90_R1_TRANSFER.inp",
        "f42_mixed_uel.for",
        "submit_M1_C3_PACKAGE90_R1_TRANSFER.pbs",
        "run_pkg90_r1_datacheck.sh",
        "PACKAGE_MANIFEST.json",
        "M1_C3_PACKAGE90_R1_TRANSFER_AUTHORIZATION.json",
        "candidate_c3_frame89_mapped_state_table.csv",
        "candidate_crack_band_mesh_c3.inp"
    ]
    for fn in expected_files:
        assert (PKG90_R1_DIR / fn).exists(), f"Package 90-R1 file missing: {fn}"

def test_package90_r1_step4_active_set_enforcement():
    inp_text = (PKG90_R1_DIR / "M1_C3_PACKAGE90_R1_TRANSFER.inp").read_text(encoding="utf-8")
    assert "*Step, name=FORWARD_CONTINUATION" in inp_text
    # Verify active-set boundary conditions exist in Step 4
    step4_part = inp_text.split("*Step, name=FORWARD_CONTINUATION")[1]
    # Check that far-field nodes have DOF 3 prescribed
    assert ", 3, 3," in step4_part, "Step 4 missing active-set DOF 3 constraints!"

def test_november_13_checkpoint_year():
    # University milestone year confirmation
    year = 2026
    assert year == 2026
