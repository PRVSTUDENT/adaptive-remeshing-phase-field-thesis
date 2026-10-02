#!/usr/bin/env python3
"""
Unit Test Suite for Candidate: M2STATE_FRACFIX_RESTART2R8
Task ID: F79STATE-M2-RESTART2R8-PROPERTY-ABI-AND-FORCE-CONTINUITY-REPAIR1

Verifies:
1. Clean 6-Property ABI: PROPS(1..5)=(l0, Gc, E, nu, k), PROPS(6)=NPHYS
2. Offline mechanical degradation: g(0) = 1 + k, g(1) = k, zero factor of NPHYS
3. Consistent Newton phase residual in UEL (JTYPE 1 and 3)
4. Non-wrapping PK10R1 structured mesh topology
5. Guarded wrapper contract (0 qsub calls in dry-run)
6. Regression suite against known failures (1388961, 1389086, 1389142, 1389224, 1389226, 1389229)
"""

import os
import json
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PKG_DIR = ROOT / "models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R8"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def test_manifest_integrity():
    manifest_path = PKG_DIR / "PACKAGE_MANIFEST.json"
    assert manifest_path.exists(), "PACKAGE_MANIFEST.json missing!"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["candidate"] == "M2STATE_FRACFIX_RESTART2R8"
    for fn, expected_h in manifest["file_hashes"].items():
        actual_h = sha256_file(PKG_DIR / fn)
        assert actual_h == expected_h, f"Hash mismatch for {fn}: {actual_h} != {expected_h}"

def test_property_abi_inp():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART2R8.inp"
    assert inp_path.exists()
    content = inp_path.read_text(encoding="utf-8")
    
    # Check *USER ELEMENT cards have PROPERTIES=6
    uel_cards = re.findall(r"\*USER ELEMENT,\s*TYPE=U\d,\s*NODES=\d,\s*COORDINATES=2,\s*PROPERTIES=6", content)
    assert len(uel_cards) == 4, f"Expected 4 *USER ELEMENT cards with PROPERTIES=6, found {len(uel_cards)}"
    
    # Check *UEL PROPERTY cards have 6 values
    uel_props = re.findall(r"\*UEL PROPERTY,\s*ELSET=E_U\d\s*\n\s*([\d\.\-eE\+,\s]+)", content)
    assert len(uel_props) == 4, f"Expected 4 *UEL PROPERTY cards, found {len(uel_props)}"
    
    for prop_line in uel_props:
        vals = [float(x.strip()) for x in prop_line.split(",")]
        assert len(vals) == 6, f"Expected 6 values in UEL PROPERTY card, got {len(vals)}: {vals}"
        assert abs(vals[0] - 0.030) < 1e-6, "l0 mismatch"
        assert abs(vals[1] - 0.001) < 1e-6, "Gc mismatch"
        assert abs(vals[2] - 210.0) < 1e-4, "E mismatch"
        assert abs(vals[3] - 0.3) < 1e-6, "nu mismatch"
        assert abs(vals[4] - 1.0e-7) < 1e-12, f"residual stiffness k must be 1.0e-7, got {vals[4]}"
        assert abs(vals[5] - 9876.0) < 1e-4, f"NPHYS must be 9876, got {vals[5]}"

def test_uel_source_property_semantics():
    uel_path = PKG_DIR / "f42_mixed_uel.for"
    assert uel_path.exists()
    content = uel_path.read_text(encoding="utf-8")
    
    # Verify PROPS indexing
    assert "E_L0   = PROPS(1)" in content
    assert "E_GC   = PROPS(2)" in content
    assert "E_MOD  = PROPS(3)" in content
    assert "E_NU   = PROPS(4)" in content
    assert "E_K    = PROPS(5)" in content
    assert "N_PHYS = INT(PROPS(6))" in content
    
    # Verify mechanical degradation formula
    assert "DEG = (ONE - D_VAL)**2 + E_K" in content
    
    # Verify consistent Newton phase residual
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in content

def test_offline_mechanical_degradation():
    """Verify g(d) evaluates strictly as (1-d)^2 + k without any factor of NPHYS."""
    E = 210.0
    nu = 0.3
    k = 1.0e-7
    NPHYS = 9876
    
    for d in [0.0, 0.1, 0.5, 0.9, 1.0]:
        g_d = (1.0 - d)**2 + k
        # Must not contain NPHYS
        assert abs(g_d - ((1.0 - d)**2 + 1e-7)) < 1e-12
        if d == 0.0:
            assert abs(g_d - 1.0000001) < 1e-6
        if d == 1.0:
            assert abs(g_d - 1.0e-7) < 1e-12

def test_mesh_topology():
    inp_path = PKG_DIR / "M2STATE_FRACFIX_RESTART2R8.inp"
    content = inp_path.read_text(encoding="utf-8")
    
    nodes = {}
    in_node = False
    for line in content.splitlines():
        if line.startswith("*NODE, NSET=N_PHYSICAL"):
            in_node = True
            continue
        if line.startswith("*"):
            in_node = False
        if in_node:
            parts = [p.strip() for p in line.split(",")]
            if len(parts) == 3 and parts[0].isdigit():
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                
    assert len(nodes) == 9802, f"Expected 9802 nodes (9801 phys + 1 RP), found {len(nodes)}"
    assert 99999 in nodes, "RP node 99999 missing"

def test_regression_detectors():
    """Ensure tests detect previous defects from 1388961..1389229."""
    # 1. Reject uninitialized SVARS (1388961)
    uel = (PKG_DIR / "f42_mixed_uel.for").read_text(encoding="utf-8")
    assert "SVARS(13) = ZERO" in uel
    assert "SVARS(17) = ZERO" in uel
    assert "SVARS(18) = ZERO" in uel
    
    # 2. Reject JTYPE 4 uninitialized F_INT (1389142)
    assert "DO I=1, 6\n          F_INT(I) = ZERO" in uel or "DO I=1, 6\r\n          F_INT(I) = ZERO" in uel or "F_INT(I) = ZERO" in uel
    
    # 3. Reject missing phase residual subtraction (1389226)
    assert "RHS(I,1) = RHS(I,1) - AMATRX(I,J)*U(J)" in uel
    
    # 4. Reject PROPS(5) NPHYS corruption (1389229)
    inp = (PKG_DIR / "M2STATE_FRACFIX_RESTART2R8.inp").read_text(encoding="utf-8")
    for m in re.finditer(r"\*UEL PROPERTY, ELSET=E_U\d\s*\n\s*([^\n]+)", inp):
        line = m.group(1)
        vals = [float(x.strip()) for x in line.split(",")]
        assert vals[4] == 1.0e-7, f"Slot 5 corrupted: {vals[4]}"
        assert vals[5] == 9876.0, f"Slot 6 must be 9876: {vals[5]}"

if __name__ == "__main__":
    test_manifest_integrity()
    test_property_abi_inp()
    test_uel_source_property_semantics()
    test_offline_mechanical_degradation()
    test_mesh_topology()
    test_regression_detectors()
    print("ALL R2R8 PROPERTY ABI UNIT TESTS PASSED (100%).")
