# -*- coding: utf-8 -*-
"""
Turn 266: Qualification Test Suite for Package 129 (Candidate C4 Increment-87 H9 Forward Continuation).
====================================================================================================
Validates manifest integrity, file hashes, frozen UEL parity, Python 2.7 driver compatibility,
input deck displacement increment (Increment 87: 0.001947309589 mm), and PBS directives.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "129_c4_inc87_h9_continuation")
MANIFEST_PATH = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")

FROZEN_UEL_SHA = "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
CHECKPOINT_PY_SHA = "426357112153f33e84ab6ac7f4d9b6bb41e0b86a95de960996cbd4f81e39ebfb"
BOUNDS_CSV_SHA = "22eff1803b31fe8c7099604dd450481e5184bd7af9828dcba1ca224c074cd745"
CARDS_INC_SHA = "fd36071113c3af81872953ead05a1a4128ae9a1947b00e524947bee31d8304bd"
DISP_CSV_SHA = "c19b19644822ccfa51ca87a3d08934dce8e4b8026ba6593357cba65cd8b4b18e"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def test_manifest_structure_and_files_exist():
    assert os.path.isfile(MANIFEST_PATH), "PACKAGE_MANIFEST.json missing"
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    assert manifest.get("schema") == 1
    assert manifest.get("package_name") == "129_c4_inc87_h9_continuation"
    assert manifest.get("remote_run_dir") == "/scratch9/pr21vyci/runs/mode1_c4_inc87_h9_continuation"
    assert manifest.get("scientific_scope") == "MODE1"
    assert manifest.get("technical_stage") == "C1-2"

    files_dict = manifest.get("files", {})
    assert len(files_dict) >= 11

    for fname, expected_hash in files_dict.items():
        fpath = os.path.join(PKG_DIR, fname)
        assert os.path.isfile(fpath), "Missing manifest file: %s" % fname
        actual_hash = compute_sha256(fpath)
        assert actual_hash == expected_hash, (
            "Hash mismatch for %s: expected %s, got %s" % (fname, expected_hash, actual_hash)
        )

def test_frozen_uel_and_checkpoint_state_hashes():
    uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
    assert compute_sha256(uel_path) == FROZEN_UEL_SHA

    ckpt_py_path = os.path.join(PKG_DIR, "mode1_am_state_checkpoint.py")
    assert compute_sha256(ckpt_py_path) == CHECKPOINT_PY_SHA

    bounds_path = os.path.join(PKG_DIR, "d_lower_bounds.csv")
    assert compute_sha256(bounds_path) == BOUNDS_CSV_SHA

    cards_path = os.path.join(PKG_DIR, "active_set_boundary_cards.inc")
    assert compute_sha256(cards_path) == CARDS_INC_SHA

    disp_path = os.path.join(PKG_DIR, "nodal_displacements_initial.csv")
    assert compute_sha256(disp_path) == DISP_CSV_SHA

def test_input_deck_increment87_prescribed_displacement():
    inp_path = os.path.join(PKG_DIR, "M1_C4_INC87_H9_CONTINUATION.inp")
    assert os.path.isfile(inp_path)
    with open(inp_path, "r") as f:
        content = f.read()

    assert "N_RP, 2, 2, 0.001947309589" in content
    assert "0.001929511665" not in content

def test_driver_python_compatibility():
    driver_path = os.path.join(PKG_DIR, "driver_c4_inc87_h9_continuation.py")
    assert os.path.isfile(driver_path)

    with open(driver_path, "r") as f:
        content = f.read()

    assert "math.isfinite" not in content, "Found forbidden math.isfinite call in driver"
    assert "def is_finite(val):" in content, "Missing is_finite definition in driver"
    assert "target_rf2_ref = 185.682431" in content
    assert "target_etot_ref = 0.23197697" in content
    assert "max_am_cycles = 25" in content

    # Syntax compile check
    compile(content, driver_path, "exec")

def test_pbs_script_directives_and_run_dir():
    pbs_path = os.path.join(PKG_DIR, "submit_M1_C4_INC87_H9_CONT.pbs")
    with open(pbs_path, "r") as f:
        lines = f.readlines()

    text = "".join(lines)
    assert "#PBS -N M1_C4_INC87_H9_CONT" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -m abe" in text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
    assert "#PBS -l walltime=08:00:00" in text
    assert "mode1_c4_inc87_h9_continuation" in text
    assert "driver_c4_inc87_h9_continuation.py" in text
