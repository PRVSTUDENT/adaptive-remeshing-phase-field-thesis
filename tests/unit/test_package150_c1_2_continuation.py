# -*- coding: utf-8 -*-
"""
test_package150_c1_2_continuation.py
Unit tests for Package 150 Stage C1-2 forward continuation generation and integrity.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
import json
import csv
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "150_c4_package150_c1_2_continuation"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
CHECKPOINT_SHA256 = "5D627B0340ADB3099D5C8980F733160FFA134787704DEAEBC93D67AB55B8D81C"


def test_package150_manifest_and_file_existence():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.is_file(), "Missing PACKAGE_MANIFEST.json"

    with open(str(manifest_path), "r") as f:
        manifest = json.load(f)

    assert manifest["package_id"] == "PACKAGE_150_C1_2_CONTINUATION"
    assert manifest["stage"] == "STAGE_C1_2"
    assert manifest["predecessor_checkpoint_sha256"] == CHECKPOINT_SHA256

    # Verify all manifest files exist on disk
    for fname, expected_hash in manifest["files"].items():
        fpath = PKG_DIR / fname
        assert fpath.is_file(), "Manifest file missing: %s" % fname
        h = hashlib.sha256(fpath.read_bytes()).hexdigest().lower()
        assert h == expected_hash.lower(), "Hash mismatch for %s: expected %s, got %s" % (fname, expected_hash, h)


def test_package150_discretization_and_serialization():
    # Displacements CSV
    disp_csv = PKG_DIR / "nodal_displacements_initial.csv"
    with open(str(disp_csv), "r") as f:
        disp_rows = list(csv.DictReader(f))
    assert len(disp_rows) == 7265, "Expected 7,265 continuum displacement rows, got %d" % len(disp_rows)

    # Damage CSV
    damage_csv = PKG_DIR / "nodal_phase_field_initial.csv"
    with open(str(damage_csv), "r") as f:
        damage_rows = list(csv.DictReader(f))
    assert len(damage_rows) == 7265, "Expected 7,265 continuum damage rows, got %d" % len(damage_rows)

    for r in damage_rows:
        d = float(r["d"])
        assert 0.0 <= d <= 1.0, "Damage out of bounds: %f" % d

    # History baseline CSV
    bounds_csv = PKG_DIR / "d_lower_bounds.csv"
    with open(str(bounds_csv), "r") as f:
        bounds_rows = list(csv.DictReader(f))
    assert len(bounds_rows) == 7056, "Expected 7,056 element history rows, got %d" % len(bounds_rows)

    # 7+8+3 solution card include
    inc_file = PKG_DIR / "initial_conditions_solution.inc"
    with open(str(inc_file), "r") as f:
        lines = [l.strip() for l in f if l.strip()]

    # Header line + 7056 * 3 lines = 21,169 lines
    assert lines[0] == "*Initial Conditions, type=SOLUTION"
    assert len(lines) == 1 + 7056 * 3, "Expected %d lines in solution include, got %d" % (1 + 7056 * 3, len(lines))


def test_package150_reference_point_and_frozen_uel():
    # Frozen UEL verification
    uel_file = PKG_DIR / "f42_mixed_uel.for"
    uel_hash = hashlib.sha256(uel_file.read_bytes()).hexdigest().upper()
    assert uel_hash == FROZEN_UEL_SHA256, "Frozen UEL hash corrupted"

    # Reference point 999999 verification in master deck
    master_inp = PKG_DIR / "M1_C4_PACKAGE150_C1_2_CONTINUATION.inp"
    inp_text = master_inp.read_text()
    assert "999999," in inp_text or "999999" in inp_text, "Node 999999 missing from master deck"
    assert "*EQUATION" in inp_text, "MPC equations missing from master deck"
    assert "N_RP, 2, 2, 0.002" in inp_text or "0.0020000000000000000" in inp_text, "Target displacement not set in master deck"


def test_package150_loading_schedule_monotonicity():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    with open(str(manifest_path), "r") as f:
        manifest = json.load(f)

    schedule = manifest["loading_schedule"]
    steps = schedule["steps"]
    assert len(steps) == 4, "Expected 4 continuation steps, got %d" % len(steps)

    current_u = schedule["initial_uy_mm"]
    assert abs(current_u - 0.0018003125442191958) < 1e-12

    for s in steps:
        target_u = s["target_uy"]
        delta_u = s["delta_uy"]
        assert target_u > current_u, "Non-monotonic displacement increment in step %d" % s["step"]
        assert delta_u <= 0.000050000001, "Displacement increment exceeds 0.00005 mm limit: %g" % delta_u
        current_u = target_u

    assert abs(current_u - 0.0020000000000000000) < 1e-12, "Final displacement does not match target 0.002 mm"
