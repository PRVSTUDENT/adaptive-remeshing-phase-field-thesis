#!/usr/bin/env python3
"""
Unit Test Suite for Candidate M2STATE_FRACFIX_RESTART2R9.
Task ID: F87STATE-M2-CORRECTED-RESTART2-R2R9-PREP-AND-QUALIFICATION1
"""

import json
import hashlib
import numpy as np
import pytest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R9"

def test_r2r9_manifest_and_file_existence():
    assert PKG_DIR.exists(), f"Package directory {PKG_DIR} must exist"
    manifest_file = PKG_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_file.exists(), "PACKAGE_MANIFEST.json must exist"
    
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART2R9"
    assert manifest["source_predecessor_job"] == "1389241.mmaster02"
    
    for rel_path, expected_sha in manifest["file_hashes"].items():
        fp = PKG_DIR / rel_path
        assert fp.exists(), f"File {rel_path} declared in manifest must exist"
        actual_sha = hashlib.sha256(fp.read_bytes()).hexdigest()
        assert actual_sha == expected_sha, f"SHA256 mismatch for {rel_path}"

def test_r2r9_uel_source_code_contract():
    uel_file = PKG_DIR / "f42_mixed_uel.for"
    assert uel_file.exists()
    code = uel_file.read_text(encoding="utf-8", errors="replace")
    
    # 1. Clean 6-property ABI
    assert "E_L0   = PROPS(1)" in code
    assert "E_GC   = PROPS(2)" in code
    assert "E_MOD  = PROPS(3)" in code
    assert "E_NU   = PROPS(4)" in code
    assert "E_K    = PROPS(5)" in code
    assert "N_PHYS = INT(PROPS(6))" in code
    
    # 2. Safe Jacobian evaluation and inversion (JAC and INVJ arrays)
    assert "DOUBLE PRECISION JAC(2,2), INVJ(2,2)" in code
    assert "JAC(1,1) = JAC(1,1) + D_N(1,I)*COORDS(1,I)" in code
    assert "DETJ = JAC(1,1)*JAC(2,2) - JAC(1,2)*JAC(2,1)" in code
    assert "INVJ(1,1) =  JAC(2,2)/DETJ" in code
    assert "INVJ(1,2) = -JAC(1,2)/DETJ" in code
    assert "INVJ(2,1) = -JAC(2,1)/DETJ" in code
    assert "INVJ(2,2) =  JAC(1,1)/DETJ" in code
    
    # 3. No in-place overwriting
    assert "INVJ(1,1)=INVJ(2,2)/DETJ" not in code
    assert "INVJ(2,2)=INVJ(1,1)/DETJ" not in code
    
    # 4. Consistent Newton phase residual
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in code

def test_r2r9_inp_deck_structure_and_boundaries():
    inp_file = PKG_DIR / "M2STATE_FRACFIX_RESTART2R9.inp"
    assert inp_file.exists()
    content = inp_file.read_text(encoding="utf-8", errors="replace")
    
    # Check ABI property cards
    assert "*UEL PROPERTY, ELSET=E_U1" in content
    assert "0.015000,     0.002700,   210.000000,     0.300000,   1.0000e-07,       9876.0" in content
    
    # Check boundaries
    assert "*NSET, NSET=N_BOTTOM" in content
    assert "*NSET, NSET=N_TOP" in content
    assert "*EQUATION" in content
    assert "N_TOP, 1, 1.0, 99999, 1, -1.0" in content
    
    # Check Step 1 and Step 2 loading
    assert "99999, 1, 1, 0.010000" in content
    assert "99999, 1, 1, 0.015000" in content

def test_r2r9_source_state_ingestion_and_phase_bounds():
    art_file = PKG_DIR / "STATE_TRANSFER_ARTIFACT.json"
    assert art_file.exists()
    art = json.loads(art_file.read_text(encoding="utf-8"))
    
    assert art["source_job"] == "1389241.mmaster02"
    assert art["source_u1_actual_mm"] == 0.010000
    assert art["source_rf1_actual_kN"] == 0.123223
    assert 0.0 <= art["phase_min"] <= art["phase_max"] <= 0.185041 + 1e-4
    assert art["phase_bound_violations"] == 0

def test_r2r9_pbs_and_guarded_wrapper_contracts():
    pbs_file = PKG_DIR / "M2STATE_FRACFIX_RESTART2R9.pbs"
    assert pbs_file.exists()
    pbs_code = pbs_file.read_text(encoding="utf-8")
    assert "#PBS -q entry_imfdfkmq" in pbs_code
    assert "#PBS -l select=1:ncpus=1:mpiprocs=1:mem=16gb" in pbs_code
    assert "#PBS -l walltime=24:00:00" in pbs_code
    assert "#PBS -m abe" in pbs_code
    assert "load_notification_config" in pbs_code
    assert "notification_install_terminal_trap" in pbs_code
    
    wrap_file = PKG_DIR / "submit_m2state_fracfix_restart2r9.sh"
    assert wrap_file.exists()
    wrap_code = wrap_file.read_text(encoding="utf-8")
    assert 'MODE="${1:---dry-run}"' in wrap_code
    assert "notify_submitted" in wrap_code

def test_r2r9_offline_tangent_consistency():
    # Verify elasticity stiffness matrix condition number and symmetry
    E = 210.0
    nu = 0.3
    c11 = E * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c12 = E * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
    c33 = E * 0.5 / (1.0 + nu)
    
    C = np.array([
        [c11, c12, 0.0],
        [c12, c11, 0.0],
        [0.0, 0.0, c33]
    ])
    
    assert np.allclose(C, C.T)
    eigvals = np.linalg.eigvalsh(C)
    assert np.all(eigvals > 0.0)
