import os
import re
import json
import hashlib
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R13"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def test_package_files_exist():
    expected_files = [
        "M2STATE_FRACFIX_RESTART2R13.inp",
        "f42_mixed_uel.for",
        "M2STATE_FRACFIX_RESTART2R13.pbs",
        "submit_m2state_fracfix_restart2r13.sh",
        "validate_package_manifest.py",
        "job_notifications.sh",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "PACKAGE_MANIFEST.json"
    ]
    for fn in expected_files:
        assert (PKG_DIR / fn).exists(), f"Missing required file: {fn}"

def test_manifest_hashes_match():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for rel_fn, exp_hash in manifest["file_hashes"].items():
        fp = PKG_DIR / rel_fn
        assert fp.exists(), f"File {rel_fn} does not exist"
        act_hash = sha256_file(fp)
        assert act_hash.lower() == exp_hash.lower(), f"Hash mismatch for {rel_fn}"

def test_uel_definitions_in_inp():
    inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp").read_text(encoding="utf-8")
    
    # Check U1 (Quad Phase): DOF 3
    assert "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0\n3" in inp_text
    # Check U2 (Quad Mech): DOFs 1, 2
    assert "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0\n1, 2" in inp_text
    # Check U3 (Tri Phase): DOF 3
    assert "*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0\n3" in inp_text
    # Check U4 (Tri Mech): DOFs 1, 2
    assert "*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, IPROPERTIES=0\n1, 2" in inp_text

def test_property_abi_cards():
    inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp").read_text(encoding="utf-8")
    lines = inp_text.splitlines()
    uel_prop_lines = [l.strip() for l in lines if l.strip().startswith("0.015, 0.0027, 210.0, 0.3, 1e-07, 9612.0")]
    assert len(uel_prop_lines) == 9612 * 2, f"Expected 19224 property lines, got {len(uel_prop_lines)}"

def test_boundary_and_equations():
    inp_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.inp").read_text(encoding="utf-8")
    assert "*EQUATION\n2\nN_TOP, 1, 1.0, 99999, 1, -1.0" in inp_text
    assert "N_BOTTOM, 1, 2, 0.00" in inp_text
    assert "99999, 1, 1, 0.010000" in inp_text

def test_fortran_residual_loop_structure():
    fortran_text = (PKG_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
    assert "COMMON /CB_STATE_TRANSFER/ SV_PHASE, SV_H" in fortran_text
    assert "SV_PHASE(PHYSIDX) = D_AVG" in fortran_text
    assert "D_VAL = SV_PHASE(PHYSIDX)" in fortran_text
    assert "DEG   = (ONE - D_VAL)**2 + E_K" in fortran_text
    
    # Check that in JTYPE=2 and JTYPE=4, RHS is set outside the Gauss loop
    # For JTYPE=2:
    assert "DO I=1, 8\n          RHS(I,1) = -F_INT(I)\n        ENDDO" in fortran_text
    # For JTYPE=4:
    assert "DO I=1, 6\n          RHS(I,1) = -F_INT(I)\n        ENDDO" in fortran_text

def test_pbs_and_notifications():
    pbs_text = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R13.pbs").read_text(encoding="utf-8")
    assert "#PBS -N M2STATE_FRACFIX_RESTART2R13" in pbs_text
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs_text
    assert "#PBS -l walltime=24:00:00" in pbs_text
    assert "#PBS -q entry_imfdfkmq" in pbs_text
    assert "#PBS -m abe" in pbs_text
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs_text
    assert "notify_start" in pbs_text
    assert "notification_install_terminal_trap" in pbs_text
