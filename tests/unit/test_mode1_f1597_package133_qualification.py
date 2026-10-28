# -*- coding: utf-8 -*-
"""
test_mode1_f1597_package133_qualification.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Qualification and controlled-difference test suite for Package 133:
(Candidate C4 Increment-87 Second Quarter-Step H18 Continuation).
1. Verifies manifest structure and schema.
2. Verifies local file existence and exact SHA-256 digests.
3. Verifies controlled differences vs Package 132:
   - Initial state restored from authentic committed Increment-86.75 checkpoint.
   - Prescribed displacement reaches Increment-87 target u_RP = 0.001947309589 mm (Delta u = 4.449481 nm).
   - Invariant assets share bit-exact identity with Package 132.
   - Frozen UEL hash preserved bit-exact (AB0A5A71...).
4. Verifies Python syntax compatibility, driver input deck path, and reference point filtering.
5. Verifies PBS directives and dual-channel notification integration.
"""

import os
import json
import hashlib
import py_compile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "133_c4_inc87_h18_second_quarterstep_continuation")
PKG132_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "132_c4_inc86_75_h17_quarterstep_continuation")
MANIFEST_PATH = os.path.join(PKG_DIR, "PACKAGE_MANIFEST.json")
PKG132_MANIFEST_PATH = os.path.join(PKG132_DIR, "PACKAGE_MANIFEST.json")

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
def pkg132_manifest_data():
    assert os.path.isfile(PKG132_MANIFEST_PATH), "Package 132 PACKAGE_MANIFEST.json missing"
    with open(PKG132_MANIFEST_PATH, "r") as f:
        return json.load(f)

def test_manifest_structure_and_scope(manifest_data):
    assert manifest_data.get("schema") == 1
    assert manifest_data.get("package_name") == "133_c4_inc87_h18_second_quarterstep_continuation"
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
        assert os.path.isfile(fpath), "Missing file: %s" % fname
        actual_hash = compute_sha256(fpath)
        assert actual_hash == expected_hash.lower(), "Hash mismatch on %s" % fname

def test_invariant_assets_against_package132(manifest_data, pkg132_manifest_data):
    invariant_files = [
        "f42_unified_12dof_active_set_uel.for",
        "job_notifications.sh",
        "mode1_am_state_checkpoint.py"
    ]
    for fname in invariant_files:
        assert manifest_data["files"][fname] == pkg132_manifest_data["files"][fname], "Invariant asset %s differed!" % fname

    # Frozen UEL verification
    assert manifest_data["files"]["f42_unified_12dof_active_set_uel.for"] == "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"

def test_increment_86_75_checkpoint_provenance(manifest_data):
    assert manifest_data["files"]["d_lower_bounds.csv"] == "bf250b09cac2479dd9590ad4a0918b7d3bebf0f94bd5972383305580983b376a"
    assert manifest_data["files"]["nodal_displacements_initial.csv"] == "554610895b86d559f02ff195f892bee15f0790cc378ec76cdf905b9a40073d18"
    assert manifest_data["files"]["active_set_boundary_cards.inc"] == "e62e1574c03ff1fd5dc4c406bc03d27b013b4b9e07a3637d586cec70563d109b"
    assert manifest_data["files"]["stage_a_all_d0_boundary_cards.inc"] == "e62e1574c03ff1fd5dc4c406bc03d27b013b4b9e07a3637d586cec70563d109b"

def test_increment_87_prescribed_displacement():
    inp_path = os.path.join(PKG_DIR, "M1_C4_INC87_H18_SECOND_QUARTERSTEP_CONTINUATION.inp")
    assert os.path.isfile(inp_path)
    with open(inp_path, "r") as f:
        content = f.read()

    assert "N_RP, 2, 2, 0.001947309589" in content

    u_target = 0.001947309589
    u_source = 0.001942860108
    delta_u = u_target - u_source
    assert pytest.approx(delta_u, 1e-10) == 0.000004449481

def test_driver_python_syntax_and_cap():
    driver_path = os.path.join(PKG_DIR, "driver_c4_inc87_h18_continuation.py")
    assert os.path.isfile(driver_path)
    py_compile.compile(driver_path, doraise=True)

    with open(driver_path, "r") as f:
        text = f.read()
    assert "max_am_cycles = 25" in text
    assert "c4_inc87_h18_continuation_summary.json" in text
    assert "M1_C4_INC87_H18_CYC%d_MECH" in text
    assert "M1_C4_INC87_H18_SECOND_QUARTERSTEP_CONTINUATION.inp" in text
    assert "f.write(\"%d, 3, 3, %.8f\\n\" % (nid, d_prescribed[nid]))" in text
    assert "is_active[nid]" not in text
    assert "if nid != 999999:" in text

def test_pbs_directives_and_notification_contract():
    pbs_path = os.path.join(PKG_DIR, "submit_M1_C4_INC87_H18_CONT.pbs")
    assert os.path.isfile(pbs_path)
    with open(pbs_path, "r") as f:
        text = f.read()
    assert "#PBS -N M1_C4_INC87_H18_CONT" in text
    assert "#PBS -q entry_imfdfkmq" in text
    assert "#PBS -m abe" in text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in text
    assert "#PBS -l walltime=08:00:00" in text
    assert "notification_load_config" in text
    assert "notification_install_terminal_trap" in text
    assert "notify_start" in text
