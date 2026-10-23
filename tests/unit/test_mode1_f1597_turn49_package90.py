#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn49_package90.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: 69fe4a09-36cd-47d1-80f9-46c9879fd0d4

Unit tests for Package 90: Candidate C2 -> Candidate C3 Second-Cycle Nonmatching State Transfer.
"""

import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG90_DIR = REPO_ROOT / "models/pandey_kumar_mode1/90_c3_package90_second_cycle_transfer"
TELEMETRY_JSON = REPO_ROOT / "results/validation/mode1_f1597/pkg90_telemetry_summary.json"
PREP_JSON = REPO_ROOT / "results/validation/preparation-69fe4a09-36cd-47d1-80f9-46c9879fd0d4.json"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_frozen_uel_bitwise_identity():
    uel_path = PKG90_DIR / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for missing"
    h = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert h == FROZEN_UEL_HASH, f"Frozen UEL hash mismatch: {h}"

def test_package90_files_exist():
    expected_files = [
        "M1_C3_PACKAGE90_TRANSFER.inp",
        "f42_mixed_uel.for",
        "submit_M1_C3_PACKAGE90_TRANSFER.pbs",
        "run_pkg90_datacheck.sh",
        "PACKAGE_MANIFEST.json",
        "M1_C3_PACKAGE90_TRANSFER_AUTHORIZATION.json",
        "candidate_c3_frame89_mapped_state_table.csv",
        "candidate_crack_band_mesh_c3.inp",
        "M1_C3_PACKAGE90_TRANSFER.sta",
        "M1_C3_PACKAGE90_TRANSFER.dat",
        "uel_energy_balance.csv",
        "pbs_execution.log"
    ]
    for fn in expected_files:
        assert (PKG90_DIR / fn).exists(), f"Package 90 file missing: {fn}"

def test_force_continuity_under_5pct():
    data = json.loads(TELEMETRY_JSON.read_text(encoding="utf-8"))
    step1 = data["step1_state_injection"]
    assert step1["meets_5pct_force_gate"] is True
    assert abs(step1["discrepancy_vs_pkg89_pct"]) < 0.05, f"Discrepancy {step1['discrepancy_vs_pkg89_pct']}% exceeds 0.05%"
    assert abs(step1["rf2_N"] - 169.5991) < 0.05

def test_energy_continuity():
    data = json.loads(TELEMETRY_JSON.read_text(encoding="utf-8"))
    step1 = data["step1_state_injection"]
    assert abs(step1["delta_fracture_energy_pct"]) < 0.05, f"Fracture energy discrepancy {step1['delta_fracture_energy_pct']}% exceeds 0.05%"

def test_mechanical_reequilibration_and_frozen_damage():
    data = json.loads(TELEMETRY_JSON.read_text(encoding="utf-8"))
    step2 = data["step2_mech_reequilibration"]
    assert step2["meets_5pct_force_gate"] is True
    assert abs(step2["discrepancy_vs_pkg89_pct"]) < 0.05

    # Check damage was frozen during Step 2
    step2_frames = data["steps"]["MECH_REEQUIL_FROZEN_DAMAGE"]["frames"]
    for f in step2_frames:
        assert abs(f["d_max"] - 0.856958) < 1e-4

def test_active_set_zero_healing():
    data = json.loads(TELEMETRY_JSON.read_text(encoding="utf-8"))
    step3_dmax = data["step3_staggered_phase"]["d_max"]
    assert step3_dmax >= 0.856958, "Damage healed in active set step!"

def test_forward_continuation_softening():
    data = json.loads(TELEMETRY_JSON.read_text(encoding="utf-8"))
    fwd = data["step4_forward_continuation"]
    assert fwd["softening_observed"] is True
    assert fwd["final_rf2_N"] < 169.5, "Softening did not occur"
    assert fwd["final_d_max"] >= 1.0, "Full damage d=1 not attained"
    assert abs(fwd["final_u2_mm"] - 0.0020651) < 1e-6

def test_preparation_checkpoint_validity():
    assert PREP_JSON.exists(), "Preparation checkpoint JSON missing"
    prep = json.loads(PREP_JSON.read_text(encoding="utf-8"))
    assert prep["schema"] == 1
    assert prep["status"] == "PREPARATION_COMPLETE"
    assert prep["verification_passed"] is True
    assert len(prep["finding"]) >= 20
    assert "M1_C3_PACKAGE90_TRANSFER.inp" in str(prep["evidence_sources"])
