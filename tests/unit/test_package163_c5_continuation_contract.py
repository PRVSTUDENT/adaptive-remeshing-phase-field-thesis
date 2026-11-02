# -*- coding: utf-8 -*-
"""
test_package163_c5_continuation_contract.py
Unit tests for Package 163 (+5 nm C5 Forward Continuation) Candidate Builder & State Contracts.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2
"""

import copy
import hashlib
import json
import math
import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package163_c5_continuation import (
    validate_checkpoint_schema, build_package163_candidate,
    BASELINE_UY_MM, TARGET_UY_MM, DELTA_UY_MM,
    C4_R6_REFERENCE_FORCE_KN, C4_R6_REFERENCE_TOTAL_ENERGY_KNMM,
    FROZEN_UEL_SHA256, compute_sha256
)


def create_synthetic_c5_checkpoint():
    """Generates valid synthetic Checkpoint 01 conforming strictly to Stage C2-0 interface."""
    # 13,278 nodes
    disp = [[nid, 0.0, 0.0018603125442191958 * (nid / 13278.0)] for nid in range(1, 13279)]
    dam = [[nid, min(0.95, 0.05 + 0.9 * (nid / 13278.0))] for nid in range(1, 13279)]
    # 12,996 elements x 4 GPs = 51,984
    hist = []
    for eid in range(1, 12997):
        for g in range(1, 5):
            hist.append([eid, g, 0.001 * (eid % 50 + g)])

    return {
        "schema": 1,
        "stage": "C2-0",
        "step": 1,
        "target_uy_mm": BASELINE_UY_MM,
        "outer_iteration": 4,
        "coupled_convergence": True,
        "physical_acceptance": "PASS",
        "reaction_force_kN": 0.1845419145,
        "total_energy_kNmm": 0.00022454112,
        "displacement": disp,
        "damage": dam,
        "history": hist
    }


def test_checkpoint_schema_validation():
    chkpt = create_synthetic_c5_checkpoint()
    assert validate_checkpoint_schema(chkpt) is True

    # Test rejection of un-converged checkpoint
    bad_chkpt = copy.deepcopy(chkpt)
    bad_chkpt["coupled_convergence"] = False
    with pytest.raises(ValueError, match="un-converged checkpoint"):
        validate_checkpoint_schema(bad_chkpt)

    # Test rejection of incorrect baseline displacement
    bad_chkpt = copy.deepcopy(chkpt)
    bad_chkpt["target_uy_mm"] = 0.0020
    with pytest.raises(ValueError, match="baseline uy mismatch"):
        validate_checkpoint_schema(bad_chkpt)

    # Test rejection of incomplete node coverage
    bad_chkpt = copy.deepcopy(chkpt)
    bad_chkpt["displacement"] = bad_chkpt["displacement"][:1000]
    with pytest.raises(ValueError, match="Displacement node coverage violation"):
        validate_checkpoint_schema(bad_chkpt)

    # Test rejection of negative damage
    bad_chkpt = copy.deepcopy(chkpt)
    bad_chkpt["damage"][0][1] = -0.5
    with pytest.raises(ValueError, match="Invalid damage"):
        validate_checkpoint_schema(bad_chkpt)

    # Test rejection of negative history
    bad_chkpt = copy.deepcopy(chkpt)
    bad_chkpt["history"][0][2] = -1.0
    with pytest.raises(ValueError, match="Invalid history"):
        validate_checkpoint_schema(bad_chkpt)


def test_target_load_level_and_increment():
    # Verify exact +5 nm forward step
    assert math.isclose(TARGET_UY_MM - BASELINE_UY_MM, 5.0e-6, rel_tol=1e-12)
    assert math.isclose(DELTA_UY_MM, 5.0e-6, rel_tol=1e-12)
    assert TARGET_UY_MM == 0.0018653125442191958

    # Verify exact agreement with C4 R6 reference load level
    r6_acceptance_file = REPO_ROOT / "results/validation/package157_r6_checkpoint_acceptance.json"
    if r6_acceptance_file.is_file():
        r6_data = json.loads(r6_acceptance_file.read_text(encoding="utf-8"))
        # R6 measurements
        assert "target_uy_mm" in r6_data["measurements"]


def test_builder_mock_execution(tmp_path):
    chkpt = create_synthetic_c5_checkpoint()
    target_dir = tmp_path / "mock_package163"

    manifest = build_package163_candidate(chkpt, target_dir)

    assert manifest["package_name"] == "163_c5_package163_c2_1_continuation"
    assert manifest["stage"] == "C2-1"
    assert manifest["target_uy_mm"] == TARGET_UY_MM
    assert manifest["total_quads"] == 12996
    assert manifest["total_nodes"] == 13278
    assert manifest["total_gps"] == 51984

    # Verify presence of essential files
    assert (target_dir / "nodal_displacements_initial.csv").is_file()
    assert (target_dir / "nodal_phase_field_initial.csv").is_file()
    assert (target_dir / "d_lower_bounds.csv").is_file()
    assert (target_dir / "initial_conditions_solution.inc").is_file()
    assert (target_dir / "active_set_boundary_cards.inc").is_file()
    assert (target_dir / "M1_C5_PACKAGE163_C2_1_CONTINUATION.inp").is_file()
    assert (target_dir / "P163_MECHANICAL_DC.inp").is_file()
    assert (target_dir / "P163_PHASE_DC.inp").is_file()
    assert (target_dir / "run_datacheck.sh").is_file()
    assert (target_dir / "submit_M1_C5_P163_C2_1.pbs").is_file()
    assert (target_dir / "PACKAGE_MANIFEST.json").is_file()
    assert (target_dir / "EXECUTION_MANIFEST.json").is_file()

    # Verify execution manifest technical stage and command digest
    exec_data = json.loads((target_dir / "EXECUTION_MANIFEST.json").read_text(encoding="utf-8"))
    assert exec_data["technical_stage"] == "MODE1_BASELINE"
    assert exec_data["adapter"] == "mode1-qualified-batch-v2"
    expected_cmd = " ".join(exec_data["jobs"][0]["command"].strip().split())
    assert exec_data["jobs"][0]["command_sha256"] == hashlib.sha256(expected_cmd.encode()).hexdigest()

    # Verify frozen UEL integrity
    uel_h = compute_sha256(target_dir / "f42_mixed_uel.for")
    assert uel_h == FROZEN_UEL_SHA256

    # Verify deck target displacement
    deck_text = (target_dir / "M1_C5_PACKAGE163_C2_1_CONTINUATION.inp").read_text(encoding="utf-8")
    assert f"N_RP, 2, 2, {TARGET_UY_MM:.17g}" in deck_text
    assert "*Step, name=C2_1_Step1" in deck_text


def test_driver_source_hashes():
    driver_path = REPO_ROOT / "scripts/state_transfer/driver_package163_c5_continuation.py"
    builder_path = REPO_ROOT / "scripts/state_transfer/build_package163_c5_continuation.py"

    assert driver_path.is_file()
    assert builder_path.is_file()

    h_driver = compute_sha256(driver_path)
    h_builder = compute_sha256(builder_path)

    assert len(h_driver) == 64
    assert len(h_builder) == 64
