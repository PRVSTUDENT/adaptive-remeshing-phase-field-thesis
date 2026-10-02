#!/usr/bin/env python3
"""
Unit Tests for Candidate M2STATE_FRACFIX_RESTART2R14
Task ID: F111STATE-M2-RESTART2-R2R14-CONTINUATION-PREP-AND-QUALIFICATION1
"""

import pytest
import json
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def test_package_files_exist():
    assert PKG_DIR.exists()
    required_files = [
        "M2STATE_FRACFIX_RESTART2R14.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R14.pbs",
        "submit_m2state_fracfix_restart2r14.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json"
    ]
    for fn in required_files:
        p = PKG_DIR / fn
        assert p.exists(), f"Missing required file: {fn}"
        assert p.stat().st_size > 0, f"File is empty: {fn}"

def test_package_manifest_integrity():
    manifest_p = PKG_DIR / "PACKAGE_MANIFEST.json"
    manifest = json.loads(manifest_p.read_text())
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART2R14"
    files = manifest.get("file_hashes", manifest.get("files", {}))
    for fn, exp_hash in files.items():
        act_hash = sha256_file(PKG_DIR / fn)
        assert act_hash.lower() == exp_hash.lower(), f"Hash mismatch for {fn}"

def test_fortran_uel_staggered_and_residual_contract():
    uel_text = (PKG_DIR / "f42_mixed_uel.for").read_text()
    assert "PROPS(6)" in uel_text
    assert "N_PHYS = INT(PROPS(6))" in uel_text
    assert "COMMON /CB_STATE_TRANSFER/ SV_PHASE, SV_H" in uel_text
    assert "SV_PHASE(PHYSIDX) = D_AVG" in uel_text
    assert "RHS(I,1) = -F_INT(I)" in uel_text

def test_inp_boundary_conditions_and_equations():
    inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R14.inp").read_text()
    assert "*EQUATION" in inp_text
    assert "N_TOP, 1, 1.0, 99999, 1, -1.0" in inp_text
    assert "N_BOTTOM, 1, 2, 0.00" in inp_text
    assert "99999, 1, 1, 0.030000" in inp_text  # Step 1 handoff
    assert "99999, 1, 1, 0.050000" in inp_text  # Step 2 continuation

def test_state_transfer_artifact_fidelity():
    art = json.loads((PKG_DIR / "STATE_TRANSFER_ARTIFACT.json").read_text())
    assert art["source_job_id"] == "1389325.mmaster02"
    assert art["physical_elements"] == 9612
    assert art["checkpoint_u1_mm"] == 0.030000
    assert art["checkpoint_rf1_kN"] == 0.654334
    assert art["statistics"]["d_max"] > 0.70
    assert art["statistics"]["H_max"] > 0.40

def test_pbs_notifications_and_resources():
    pbs_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R14.pbs").read_text()
    assert "#PBS -m abe" in pbs_text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_text
    assert "notify_start" in pbs_text
    assert "notification_install_terminal_trap" in pbs_text
    assert "select=1:ncpus=1:mem=16gb" in pbs_text
    assert "walltime=24:00:00" in pbs_text
    assert "entry_imfdfkmq" in pbs_text
