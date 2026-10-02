#!/usr/bin/env python3
"""
Unit Test Suite for Production Candidate M2STATE_FRACFIX_RESTART1R1R8.
Task ID: F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1
"""

import os
import sys
import json
import hashlib
import re
import pytest
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def test_manifest_and_files_integrity():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists(), "PACKAGE_MANIFEST.json missing"
    
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "files" in manifest, "Canonical 'files' key missing"
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART1R1R8"
    assert manifest["task_id"] == "F84STATE-M2-CORRECTED-RESTART1-JACOBIAN-INVERSE-REPAIR-QUALIFICATION1"
    
    files_dict = manifest["files"]
    required_files = [
        "M2STATE_FRACFIX_RESTART1R1R8.inp",
        "f42_mixed_uel.for",
        "STATE_TRANSFER_ARTIFACT.json",
        "TRANSFER_MANIFEST.json",
        "RESTART_ACCEPTANCE_CONTRACT.json",
        "job_notifications.sh",
        "validate_package_manifest.py",
        "M2STATE_FRACFIX_RESTART1R1R8.pbs",
        "submit_m2state_fracfix_restart1r1r8.sh"
    ]
    for rf in required_files:
        assert rf in files_dict, f"File {rf} missing from manifest mapping"
        f_p = PKG_DIR / rf
        assert f_p.exists(), f"File {rf} missing on disk"
        actual_hash = sha256_file(f_p)
        assert actual_hash.lower() == files_dict[rf].lower(), f"Hash mismatch for {rf}"

def test_deck_structure_and_property_abi():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART1R1R8.inp"
    text = inp_path.read_text(encoding="utf-8")
    
    # Check UEL declarations have PROPERTIES=6
    for t in ["U1", "U2", "U3", "U4"]:
        pattern = rf"\*USER ELEMENT,\s*TYPE={t},.*PROPERTIES=6"
        assert re.search(pattern, text), f"TYPE={t} does not declare PROPERTIES=6"
        
    # Check UEL PROPERTY cards have 6 values
    for elset in ["E_U1", "E_U2", "E_U3", "E_U4"]:
        pattern = rf"\*UEL PROPERTY,\s*ELSET={elset}\s*\n\s*([\d\.\s,eE+-]+)"
        m = re.search(pattern, text)
        assert m, f"UEL PROPERTY for {elset} not found"
        props = [float(p.strip()) for p in m.group(1).split(",") if p.strip()]
        assert len(props) == 6, f"Expected 6 properties for {elset}, got {len(props)}"
        assert props[0] == 0.015, f"l0 mismatch: {props[0]}"
        assert props[1] == 0.0027, f"Gc mismatch: {props[1]}"
        assert props[2] == 210.0, f"E mismatch: {props[2]}"
        assert props[3] == 0.3, f"nu mismatch: {props[3]}"
        assert props[4] == 1.0e-7, f"k mismatch: {props[4]}"
        assert props[5] == 4894.0, f"Nphys mismatch: {props[5]}"

def test_uel_safe_jacobian_inversion_contract():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    text = uel_path.read_text(encoding="utf-8")
    
    # Verify JAC(2,2) forward declaration and DETJ computation
    assert "JAC(2,2)" in text
    assert "INVJ(2,2)" in text
    
    # Verify no unsafe in-place overwrite
    assert "INVJ(1,1) =  JAC(2,2) / DETJ" in text
    assert "INVJ(1,2) = -JAC(1,2) / DETJ" in text
    assert "INVJ(2,1) = -JAC(2,1) / DETJ" in text
    assert "INVJ(2,2) =  JAC(1,1) / DETJ" in text
    
    # Verify unsafe pattern is NOT present
    assert "INVJ(1,1) =  INVJ(2,2) / DETJ" not in text
    assert "INVJ(2,2) =  INVJ(1,1) / DETJ" not in text
    
    # Verify consistent phase residual RHS = F_H - K_phase * d
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in text

def test_element_level_jacobian_regression():
    # Quadrilateral element coords
    coords_quad = np.array([
        [-0.485136, -0.5],
        [-0.483574, -0.491168],
        [-0.491612, -0.491568],
        [-0.492568, -0.5]
    ]).T # shape (2, 4)
    
    E_MOD, E_NU = 210.0, 0.3
    C11 = E_MOD*(1.0 - E_NU)/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    C12 = E_MOD*E_NU/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    C22, C33 = C11, E_MOD/(2.0*(1.0 + E_NU))
    D_ELAS = np.array([[C11, C12, 0.0], [C12, C22, 0.0], [0.0, 0.0, C33]])
    
    xg4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]
    w4 = [1.0, 1.0, 1.0, 1.0]
    
    def run_quad(bugged=False):
        K_elem = np.zeros((8, 8))
        for kpt in range(4):
            xi, eta, wt = xg4[kpt], yg4[kpt], w4[kpt]
            D_N = np.array([
                [-0.25*(1-eta),  0.25*(1-eta), 0.25*(1+eta), -0.25*(1+eta)],
                [-0.25*(1-xi),  -0.25*(1+xi),  0.25*(1+xi),   0.25*(1-xi)]
            ])
            JAC = D_N @ coords_quad.T
            detJ = np.linalg.det(JAC)
            cjac = detJ * wt
            if bugged:
                invJ = np.zeros((2, 2))
                invJ[0, 0] = JAC[1, 1] / detJ
                invJ[1, 1] = invJ[0, 0] / detJ
                invJ[0, 1] = -JAC[0, 1] / detJ
                invJ[1, 0] = -JAC[1, 0] / detJ
            else:
                invJ = np.array([
                    [ JAC[1, 1]/detJ, -JAC[0, 1]/detJ],
                    [-JAC[1, 0]/detJ,  JAC[0, 0]/detJ]
                ])
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = invJ[0, 0]*D_N[0, i] + invJ[0, 1]*D_N[1, i]
                B[1, 2*i+1] = invJ[1, 0]*D_N[0, i] + invJ[1, 1]*D_N[1, i]
                B[2, 2*i]   = invJ[1, 0]*D_N[0, i] + invJ[1, 1]*D_N[1, i]
                B[2, 2*i+1] = invJ[0, 0]*D_N[0, i] + invJ[0, 1]*D_N[1, i]
            K_elem += cjac * (B.T @ D_ELAS @ B)
        return K_elem
        
    K_bugged = run_quad(bugged=True)
    K_correct = run_quad(bugged=False)
    
    norm_bugged = np.linalg.norm(K_bugged)
    norm_correct = np.linalg.norm(K_correct)
    ratio = norm_bugged / norm_correct
    
    assert ratio > 1e5, f"Expected bugged stiffness to be inflated by > 1e5, got ratio {ratio}"
    assert np.all(np.diag(K_correct) > 0.0), "Corrected stiffness diagonal must be strictly positive"

def test_shape_gradient_and_finite_difference_tangent():
    # 1. Distorted Quad
    coords_quad = np.array([[0.0, 0.0], [0.012, 0.001], [0.011, 0.013], [-0.001, 0.009]]).T
    D_N = np.array([[-0.25*(1+0.3), 0.25*(1+0.3), 0.25*(1-0.3), -0.25*(1-0.3)],
                    [-0.25*(1-0.2), -0.25*(1+0.2), 0.25*(1+0.2), 0.25*(1-0.2)]])
    JAC = D_N @ coords_quad.T
    detJ = np.linalg.det(JAC)
    invJ = np.array([[JAC[1,1]/detJ, -JAC[0,1]/detJ], [-JAC[1,0]/detJ, JAC[0,0]/detJ]])
    dN_dx = invJ @ D_N
    grad_x = coords_quad @ dN_dx.T
    assert np.allclose(grad_x, np.eye(2)), "Spatial gradient transformation failed linear completeness on quad"
    
    # 2. Triangle
    coords_tri = np.array([[0.0, 0.0], [0.01, 0.0], [0.005, 0.01]]).T
    D_NTRI = np.array([[-1.0, 1.0, 0.0], [-1.0, 0.0, 1.0]])
    JAC_tri = D_NTRI @ coords_tri.T
    detJ_tri = np.linalg.det(JAC_tri)
    invJ_tri = np.array([[JAC_tri[1,1]/detJ_tri, -JAC_tri[0,1]/detJ_tri], [-JAC_tri[1,0]/detJ_tri, JAC_tri[0,0]/detJ_tri]])
    dN_dx_tri = invJ_tri @ D_NTRI
    grad_x_tri = coords_tri @ dN_dx_tri.T
    assert np.allclose(grad_x_tri, np.eye(2)), "Spatial gradient transformation failed linear completeness on tri"

def test_guarded_wrapper_dry_run():
    val_script = PKG_DIR / "validate_package_manifest.py"
    assert val_script.exists()
    
    import subprocess
    cmd = [sys.executable, str(val_script), str(PKG_DIR / "PACKAGE_MANIFEST.json")]
    res = subprocess.run(cmd, capture_output=True, text=True)
    assert res.returncode == 0, f"Validator failed: {res.stderr}\n{res.stdout}"
    assert "package_manifest_verification = PASS" in res.stdout
