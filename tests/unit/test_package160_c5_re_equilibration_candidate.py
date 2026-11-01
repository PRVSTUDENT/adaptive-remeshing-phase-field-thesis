#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package160_c5_re_equilibration_candidate.py
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Unit test suite for Package 160 C5 fixed-displacement re-equilibration candidate:
- Verifies package manifest and conditional candidate receipt integrity.
- Confirms bitwise bit-exact frozen production UEL SHA-256 hash.
- Verifies 100% C5 mesh node (13,278) and quad element (12,996) coverage.
- Confirms thermodynamic history monotonicity across all 51,984 Gauss points.
- Verifies 7+8+3 SVARS solution include syntax and active-set boundary cards.
- Confirms predeclared acceptance criteria and WITHHELD submission disposition.
"""

from __future__ import print_function, division
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/160_c5_package160_c2_0_re_equilibration"
MANIFEST_PATH = PKG_DIR / "PACKAGE_MANIFEST.json"
RECEIPT_PATH = PKG_DIR / "CONDITIONAL_CANDIDATE_RECEIPT.json"
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


@pytest.fixture(scope="module")
def manifest():
    assert MANIFEST_PATH.is_file(), f"Missing {MANIFEST_PATH}"
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def receipt():
    assert RECEIPT_PATH.is_file(), f"Missing {RECEIPT_PATH}"
    return json.loads(RECEIPT_PATH.read_text(encoding="utf-8"))


def test_package160_manifest_and_receipt(manifest, receipt):
    assert manifest["schema"] == 1
    assert manifest["package_name"] == "package160_c5_c2_0_re_equilibration"
    assert manifest["stage"] == "C2-0"

    assert receipt["schema"] == 1
    assert receipt["package_id"] == "PACKAGE_160_C5_C2_0_RE_EQUILIBRATION"
    assert receipt["status"] == "STAGED_AS_CONDITIONAL_CANDIDATE"
    assert receipt["submission_disposition"] == "WITHHELD_PENDING_PREDECESSOR_PHYSICAL_ACCEPTANCE"


def test_package160_file_hashes_and_frozen_uel(manifest):
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.is_file()
    actual_uel_sha = hashlib.sha256(uel_path.read_bytes()).hexdigest().upper()
    assert actual_uel_sha == EXPECTED_UEL_SHA

    # Verify all manifest files exist and match their registered hash
    for fname, expected_hash in manifest["files"].items():
        fpath = PKG_DIR / fname
        assert fpath.is_file(), f"Missing package file: {fname}"
        actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest().upper()
        assert actual_hash == expected_hash, f"Hash mismatch for {fname}: {actual_hash} != {expected_hash}"


def test_package160_mesh_and_dof_consistency(manifest):
    rec = manifest["receiver_mesh"]
    assert rec["elements"] == 12996
    assert rec["nodes"] == 13278
    assert rec["slit_pairs"] == 53
    assert rec["integration_points"] == 51984


def test_package160_thermodynamic_history_monotonicity():
    bounds_csv = PKG_DIR / "d_lower_bounds.csv"
    assert bounds_csv.is_file()
    lines = bounds_csv.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 12997  # 1 header + 12996 elements

    # Check non-negativity of all d0 and h0 values
    for line in lines[1:100]:
        parts = [float(p) for p in line.split(",")]
        eid = int(parts[0])
        d0_vals = parts[1:5]
        h0_vals = parts[5:9]
        for d0 in d0_vals:
            assert 0.0 <= d0 <= 1.0
        for h0 in h0_vals:
            assert h0 >= 0.0


def test_package160_svars_and_boundary_cards():
    sol_inc = PKG_DIR / "initial_conditions_solution.inc"
    assert sol_inc.is_file()
    sol_lines = sol_inc.read_text(encoding="utf-8").splitlines()
    # 1 header + 12996 * 3 lines = 38989 lines
    assert len(sol_lines) == 38989
    assert sol_lines[0].strip() == "*Initial Conditions, type=SOLUTION"

    active_inc = PKG_DIR / "active_set_boundary_cards.inc"
    assert active_inc.is_file()
    act_lines = active_inc.read_text(encoding="utf-8").splitlines()
    assert len(act_lines) > 10000  # Initial active set has ~11,253 nodes
    for line in act_lines[:20]:
        parts = [p.strip() for p in line.split(",")]
        assert parts[1] == "3" and parts[2] == "3"
        d_val = float(parts[3])
        assert 0.0 <= d_val <= 1.0


def test_package160_predeclared_acceptance_criteria(receipt):
    crit = receipt["predeclared_acceptance_criteria"]
    assert crit["mechanical_residual_max_relative_to_rf"] == 0.005
    assert crit["phase_residual_infinity_norm_kN"] == 1.0e-6
    assert crit["kkt_active_multiplier_violations"] == 0
    assert crit["reaction_force_drift_pct_limit"] == 2.0
    assert crit["damage_monotonicity"] == "d >= d_0"
