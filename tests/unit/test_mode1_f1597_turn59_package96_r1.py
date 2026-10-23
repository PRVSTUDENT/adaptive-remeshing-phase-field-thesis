#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn59_package96_r1.py
Unit and Qualification Test Suite for Package 96-R1.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""

import os
import sys
import json
import hashlib
from pathlib import Path
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.diagnose_c4_c5_energy_transfer import load_mesh_and_damage, compute_fracture_energy

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/96_r1_c5_package96_r1_consistent_transfer"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
TARGET_E_FRAC = 0.00013773671

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_integrity():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.exists(), "f42_mixed_uel.for missing"
    assert sha256_file(uel_path) == FROZEN_UEL_HASH, "Frozen UEL bitwise hash altered!"

def test_c5_mesh_resolution_and_geometry():
    c5_mesh_inp = PKG_DIR / "candidate_crack_band_mesh_c5.inp"
    assert c5_mesh_inp.exists(), "candidate_crack_band_mesh_c5.inp missing"

    nodes, elems, _ = load_mesh_and_damage(c5_mesh_inp, PKG_DIR / "candidate_c5_frame7_mapped_state_table.csv", is_mapped_csv=True)
    assert len(elems) == 4440, f"Expected 4440 quads, got {len(elems)}"
    assert len(nodes) == 4610, f"Expected 4610 physical nodes, got {len(nodes)}"

def test_energy_consistent_fracture_energy():
    c5_mesh_inp = PKG_DIR / "candidate_crack_band_mesh_c5.inp"
    mapped_csv = PKG_DIR / "candidate_c5_frame7_mapped_state_table.csv"
    nodes, elems, dam = load_mesh_and_damage(c5_mesh_inp, mapped_csv, is_mapped_csv=True)

    res = compute_fracture_energy(nodes, elems, dam)
    mismatch_pct = abs(res['e_total'] - TARGET_E_FRAC) / TARGET_E_FRAC * 100.0

    assert mismatch_pct <= 0.01, f"Fracture energy mismatch {mismatch_pct:.6f}% exceeds 0.01%!"
    assert min(dam.values()) >= 0.0, "Negative damage detected!"
    assert max(dam.values()) <= 1.00000, f"Damage overshoot detected: {max(dam.values())}"
    assert sum(1 for d in dam.values() if d > 1.00000) == 0, "Overshoot nodes detected!"

def test_deck_step_definitions_and_active_set():
    deck_path = PKG_DIR / "M1_C5_PACKAGE96_R1_TRANSFER.inp"
    assert deck_path.exists(), "Input deck missing"

    text = deck_path.read_text(encoding="utf-8")
    assert "*Step, name=STATE_INJECTION" in text
    assert "*Step, name=MECH_REEQUIL_FROZEN_DAMAGE" in text
    assert "*Step, name=STAGGERED_PHASE_SUBPROBLEM" in text
    assert "*Step, name=FORWARD_CONTINUATION" in text

    # Check that Step 3 clamps all nodes to d_corr
    step3_idx = text.find("*Step, name=STAGGERED_PHASE_SUBPROBLEM")
    step4_idx = text.find("*Step, name=FORWARD_CONTINUATION")
    step3_block = text[step3_idx:step4_idx]

    # In Step 3, every physical node should have a boundary condition nid, 3, 3, d
    step3_bcs = [line.strip() for line in step3_block.splitlines() if line.strip() and not line.startswith("*")]
    # Format: nid, 3, 3, d
    step3_d_bcs = [b for b in step3_bcs if ", 3, 3," in b]
    assert len(step3_d_bcs) == 4610, f"Expected 4610 clamped damage nodes in Step 3, got {len(step3_d_bcs)}"

def test_step4_crack_corridor_active_set():
    deck_path = PKG_DIR / "M1_C5_PACKAGE96_R1_TRANSFER.inp"
    text = deck_path.read_text(encoding="utf-8")

    step4_idx = text.find("*Step, name=FORWARD_CONTINUATION")
    step4_block = text[step4_idx:]
    step4_bcs = [line.strip() for line in step4_block.splitlines() if line.strip() and not line.startswith("*")]
    step4_d_bcs = [b for b in step4_bcs if ", 3, 3," in b]

    # Clamped nodes in Step 4 = 4164, free advancing = 446
    assert len(step4_d_bcs) == 4164, f"Expected 4164 clamped nodes in Step 4, got {len(step4_d_bcs)}"

def test_manifest_and_authorization_parity():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    auth_path = PKG_DIR / "M1_C5_PACKAGE96_R1_TRANSFER_AUTHORIZATION.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        man = json.load(f)
    with open(auth_path, "r", encoding="utf-8") as f:
        auth = json.load(f)

    deck_path = PKG_DIR / "M1_C5_PACKAGE96_R1_TRANSFER.inp"
    actual_hash = sha256_file(deck_path)
    assert man["files"]["M1_C5_PACKAGE96_R1_TRANSFER.inp"] == actual_hash
    assert auth["files"]["M1_C5_PACKAGE96_R1_TRANSFER.inp"] == actual_hash.lower()

def test_pbs_lf_line_endings_and_notifications():
    pbs_path = PKG_DIR / "submit_M1_C5_PACKAGE96_R1_TRANSFER.pbs"
    raw_bytes = pbs_path.read_bytes()
    assert b"\r\n" not in raw_bytes, "PBS script contains Windows CRLF!"

    text = raw_bytes.decode("utf-8")
    assert "#PBS -m abe" in text
    assert "job_notifications.sh" in text
    assert "notification_install_terminal_trap" in text

if __name__ == "__main__":
    pytest.main(["-v", __file__])
