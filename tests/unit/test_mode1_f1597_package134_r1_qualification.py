# -*- coding: utf-8 -*-
import os
import json
import hashlib
import pytest
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PKG_DIR = os.path.join(REPO, "models", "pandey_kumar_mode1", "134_r1_c4_inc87_h20_underrelaxed_am_continuation")

def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_p134_r1_uel_invariant():
    uel_path = os.path.join(PKG_DIR, "f42_unified_12dof_active_set_uel.for")
    expected = "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"
    assert get_sha256(uel_path) == expected, "Production UEL must be 100% bit-exact"

def test_p134_r1_checkpoint_companions():
    bounds_csv = os.path.join(PKG_DIR, "d_lower_bounds.csv")
    cards_inc = os.path.join(PKG_DIR, "stage_a_all_d0_boundary_cards.inc")
    disp_csv = os.path.join(PKG_DIR, "nodal_displacements_initial.csv")

    assert get_sha256(bounds_csv) == "BF250B09CAC2479DD9590AD4A0918B7D3BEBF0F94BD5972383305580983B376A"
    assert get_sha256(cards_inc) == "E62E1574C03FF1FD5DC4C406BC03D27B013B4B9E07A3637D586CEC70563D109B"
    assert get_sha256(disp_csv) == "554610895B86D559F02FF195F892BEE15F0790CC378EC76CDF905B9A40073D18"

def test_p134_r1_repaired_history_loading():
    driver_path = os.path.join(PKG_DIR, "driver_c4_inc87_h20_continuation_r1.py")
    with open(driver_path, "r") as f:
        code = f.read()

    # Repaired driver MUST look for H0_ columns
    assert 'h_idx = [i for i, h in enumerate(header) if h.startswith("H0_")]' in code
    # Repaired driver must NOT contain the buggy hardcoded parts[1:5]
    assert 'h_vals = [float(parts[1].strip()), float(parts[2].strip()),' not in code

    # Execute driver's load_committed_history_and_d0 on d_lower_bounds.csv
    import sys
    sys.path.insert(0, PKG_DIR)
    import driver_c4_inc87_h20_continuation_r1 as drv
    h_dict = drv.load_committed_history_and_d0(os.path.join(PKG_DIR, "d_lower_bounds.csv"))
    assert len(h_dict) == 4422, "Must load all 4,422 elements"
    # Element 1 H0 values should be ~ 9.77e-4, not D0 ~ 3.95e-3
    e1_h = h_dict[1]
    assert pytest.approx(e1_h[0], 1e-6) == 9.77434232e-04
    assert pytest.approx(e1_h[1], 1e-6) == 7.61722964e-04

def test_p134_r1_manifest_consistency():
    manifest_path = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    assert manifest["package_name"] == "134_r1_c4_inc87_h20_underrelaxed_am_continuation"
    assert manifest["batch_name"] == "MODE1_C4_INC87_H20_CONT_R1"
    assert manifest["jobs"][0]["id"] == "M1_C4_INC87_H20_CONT_R1"

    # All files in manifest must match actual file hashes
    for fname, sha in manifest["files"].items():
        fpath = os.path.join(PKG_DIR, fname)
        assert os.path.exists(fpath), "Manifest file %s must exist" % fname
        assert get_sha256(fpath).lower() == sha.lower(), "Hash mismatch for %s" % fname
