# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package130_r1_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Qualification and controlled-difference test suite for Package 130 R1:
(Candidate C4 Increment-86 Half-Step H15 Continuation).
1. Verifies manifest structure and schema.
2. Verifies local file existence and exact SHA-256 digests.
3. Verifies controlled differences vs Package 129 / 129 R1:
   - Prescribed displacement reduced by 50% to midpoint target u_RP = 0.001938410627 mm.
   - All invariant assets share bit-exact identity with Package 127 R1 / 129 / 129 R1.
   - Frozen UEL hash preserved.
4. Verifies Python syntax compatibility and write_active_set_cards function.
5. Verifies PBS directives and dual-channel notification integration.
"""

import os
import json
import hashlib
import py_compile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "130_r1_c4_inc86_halfstep_h15_continuation")
PKG129_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "129_c4_inc87_h9_continuation")
MANIFEST_PATH = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
PKG129_MANIFEST_PATH = os.path.join(PKG129_DIR, "PACKAGE_MANIFEST.json")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

@pytest.fixture(scope="module")
def manifest_data():
    assert os.path.isfile(MANIFEST_PATH), "PACKAGE_MANIFEST.json missing"
    with open(MANIFEST_PATH, "r") as f:
        return json.load(f)

@pytest.fixture(scope="module")
def pkg129_manifest_data():
    assert os.path.isfile(PKG129_MANIFEST_PATH), "Package 129 PACKAGE_MANIFEST.json missing"
    with open(PKG129_MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_manifest_structure_and_scope(manifest_data):
    assert manifest_data.get("schema") == 1
    assert manifest_data.get("package_name") == "130_r1_c4_inc86_halfstep_h15_continuation"
    assert manifest_data.get("adapter") == "mode1-experimental-12dof-v1"
    assert manifest_data.get("scientific_scope") == "MODE1"
    assert manifest_data.get("technical_stage") == "C1-2"
    assert manifest_data.get("automatic_retry") is False
    assert manifest_data.get("max_submissions") == 1
    assert len(manifest_data.get("jobs", [])) == 1

def test_local_file_hashes_exact_match(manifest_data):
    files_dict = manifest_data.get("files", {})
    assert len(files_dict) == 11
    for fname, expected_hash in files_dict.items():
        fpath = os.path.join(PKG_DIR, fname)
        assert os.path.isfile(fpath), f"Missing file: {fname}"
        actual_hash = compute_sha256(fpath)
        assert actual_hash == expected_hash.lower(), f"Hash mismatch on {fname}"

def test_invariant_assets_against_package129(manifest_data, pkg129_manifest_data):
    invariant_files = [
        "active_set_boundary_cards.inc",
        "d_lower_bounds.csv",
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "mode1_am_state_checkpoint.py",
        "nodal_displacements_initial.csv",
        "stage_a_all_d0_boundary_cards.inc"
    ]
    for fname in invariant_files:
        assert manifest_data["files"][fname] == pkg129_manifest_data["files"][fname], f"Invariant asset {fname} differed!"
    
    # Frozen UEL verification
    assert manifest_data["files"]["f42_unified_12dof_active_set_uel.for"] == "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"
    
    # Checkpoint restoration invariant (P127 R1 committed bounds)
    assert manifest_data["files"]["d_lower_bounds.csv"] == "22eff1803b31fe8c7099604dd450481e5184bd7af9828dcba1ca224c074cd745"

def test_midpoint_prescribed_displacement():
    inp_path = os.path.join(PKG_DIR, "M1_C4_INC86_H15_CONTINUATION.inp")
    assert os.path.isfile(inp_path)
    with open(inp_path, "r") as f:
        content = f.read()
    
    assert "N_RP, 2, 2, 0.001938410627" in content
    assert "0.001947309589" not in content

    disp_path = os.path.join(PKG_DIR, "nodal_displacements_initial.csv")
    with open(disp_path, "r") as f:
        for line in f:
            if line.startswith("4489,"):
                u2_init = float(line.strip().split(",")[2])
                assert pytest.approx(u2_init, 1e-10) == 0.0019295116654

    delta_u = 0.001938410627 - 0.0019295116654
    assert pytest.approx(delta_u, 1e-10) == 0.0000088989616

def test_driver_python_syntax_and_cap():
    driver_path = os.path.join(PKG_DIR, "driver_c4_inc86_h15_continuation.py")
    assert os.path.isfile(driver_path)
    py_compile.compile(driver_path, doraise=True)
    
    with open(driver_path, "r") as f:
        text = f.read()
    assert "max_am_cycles = 25" in text
    assert "c4_inc86_h15_continuation_summary.json" in text
    assert "M1_C4_INC86_H15_CYC%d_MECH" in text
    # Verify write_active_set_cards does NOT use out-of-bounds indexing or DOF 7
    assert "f.write(\"%d, 3, 3, %.8f\\n\" % (nid, d_prescribed[nid]))" in text
    assert "is_active[nid]" not in text

def test_pbs_directives_and_notification_contract():
    pbs_path = os.path.join(PKG_DIR, "submit_M1_C4_INC86_H15_CONT.pbs")
    assert os.path.isfile(pbs_path)
    with open(pbs_path, "r") as f:
        text = f.read()
    assert "#PBS -N M1_C4_INC86_H15_CONT_R1" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -m abe" in text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
    assert "#PBS -l walltime=08:00:00" in text
    assert "notification_load_config" in text
    assert "notification_install_terminal_trap" in text
    assert "notify_start" in text
