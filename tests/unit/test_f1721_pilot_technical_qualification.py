#!/usr/bin/env python3
"""
Unit Test Suite: Task F1721 Versioned Diagnostic Pilot Technical Qualification
(tests/unit/test_f1721_pilot_technical_qualification.py)

Validates the static integrity, input deck architecture, Fortran source diffs,
and reconstructed literature increment schedule for the 13,163-element five-hole
staggered operator-split diagnostic pilot:
- Subroutine: f1721_proposed_staggered_coupling_uel.for
- Input deck: PK_F1721_ADAPTED_PILOT.inp
- Unified patch: f1721_staggered_coupling_proposed.patch
- Bitwise freeze of F1720 baselines
"""

import os
import hashlib
import pytest
import difflib

DECK_PILOT = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1721_ADAPTED_PILOT.inp")
DECK_F1720 = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PFM.inp")
FOR_F1721 = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "f1721_proposed_staggered_coupling_uel.for")
FOR_F1720 = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "f1720_direct_coupling_uel.for")
PATCH_F1721 = os.path.join("docs", "validation", "f1721_staggered_coupling_proposed.patch")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def test_01_pilot_artifacts_existence_and_non_emptiness():
    """Verify all pilot artifacts exist and have non-zero size."""
    for p in [DECK_PILOT, DECK_F1720, FOR_F1721, FOR_F1720, PATCH_F1721]:
        assert os.path.isfile(p), f"File not found: {p}"
        assert os.path.getsize(p) > 0, f"File empty: {p}"

def test_02_frozen_f1720_baselines_bitwise_integrity():
    """Verify that F1720 production input deck and Fortran source remain strictly frozen."""
    h_deck_f1720 = sha256_file(DECK_F1720).lower()
    h_for_f1720 = sha256_file(FOR_F1720).lower()
    
    # Exact bitwise SHA-256 digests
    expected_deck_f1720 = "318d0ed6f330e73f5a62e259dc3a9a9abcebd4341596eaa5c31ed58138ba42f2"
    expected_for_f1720 = "c298aca7ed2199b20e622b38e99fda9b533150eb0ad5e9f77069216f860e70fc"
    
    assert h_deck_f1720 == expected_deck_f1720, f"F1720 deck modified! Got {h_deck_f1720}"
    assert h_for_f1720 == expected_for_f1720, f"F1720 Fortran source modified! Got {h_for_f1720}"

def test_03_fortran_staggered_four_read_modifications():
    """Verify that f1721_proposed_staggered_coupling_uel.for contains exactly the 4 committed-state reads."""
    with open(FOR_F1720, "r") as f:
        lines_20 = f.readlines()
    with open(FOR_F1721, "r") as f:
        lines_21 = f.readlines()
        
    diff = list(difflib.unified_diff(lines_20, lines_21))
    
    # Extract code diff lines (excluding comment header changes)
    code_diff_sub = [l for l in diff if l.startswith("-") and not l.startswith("---") and not l.strip().startswith("-C")]
    code_diff_add = [l for l in diff if l.startswith("+") and not l.startswith("+++") and not l.strip().startswith("+C")]
    
    assert len(code_diff_sub) == 4, f"Expected 4 substituted code lines, found {len(code_diff_sub)}: {code_diff_sub}"
    assert len(code_diff_add) == 4, f"Expected 4 added code lines, found {len(code_diff_add)}: {code_diff_add}"
    
    # Verify exact substitutions
    expected_sub = [
        "-          HIST = SV_H_TRIAL(PHYSIDX, KPT)",
        "-        D_VAL = SV_PHASE_TRIAL(PHYSIDX)",
        "-        HIST = SV_H_TRIAL(PHYSIDX, 1)",
        "-        D_VAL = SV_PHASE_TRIAL(PHYSIDX)"
    ]
    expected_add = [
        "+          HIST = SV_H_COMMITTED(PHYSIDX, KPT)",
        "+        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)",
        "+        HIST = SV_H_COMMITTED(PHYSIDX, 1)",
        "+        D_VAL = SV_PHASE_COMMITTED(PHYSIDX)"
    ]
    
    for actual, exp in zip(code_diff_sub, expected_sub):
        assert actual.strip() == exp.strip(), f"Mismatch in code subtraction: {actual} vs {exp}"
    for actual, exp in zip(code_diff_add, expected_add):
        assert actual.strip() == exp.strip(), f"Mismatch in code addition: {actual} vs {exp}"

def test_04_fortran_state_writes_and_commons_preservation():
    """Verify that trial-state writes, SAVE attributes, and COMMON blocks are fully preserved."""
    with open(FOR_F1721, "r") as f:
        src = f.read()
        
    # 4 trial-state writes preserved
    assert "SV_PHASE_TRIAL(PHYSIDX) = D_AVG" in src, "Missing Phase trial write"
    assert "SV_H_TRIAL(PHYSIDX, KPT) = POS_M" in src, "Missing Quad Mech H trial write"
    assert "SV_H_TRIAL(PHYSIDX, 1) = POS_M" in src, "Missing Tri Mech H trial write"
    
    # LOP=2 commitment
    assert "SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)" in src, "Missing Phase LOP=2 commit"
    assert "SV_H_COMMITTED(I, K) = SV_H_TRIAL(I, K)" in src, "Missing H LOP=2 commit"
    
    # COMMON blocks and SAVE attributes
    assert "COMMON /CB_F1720_STRESS/" in src, "Missing CB_F1720_STRESS common block"
    assert "COMMON /CB_STATE_TRANS/" in src, "Missing CB_STATE_TRANS common block"
    assert "SAVE /CB_F1720_STRESS/" in src, "Missing SAVE on CB_F1720_STRESS"
    assert "SAVE /CB_STATE_TRANS/" in src, "Missing SAVE on CB_STATE_TRANS"
    
    # Mechanical neutrality dummy modulus scaling
    assert "SCALE_FACTOR = 1.D-11 / 210.D0" in src, "Missing dummy modulus scaling factor"
    
    # Fail-closed NaN guards
    assert "FATAL_NAN_GUARD" in src, "Missing fail-closed NaN guards"
    assert "PNEWDT = 0.25D0" in src, "Missing PNEWDT cutback requests"

def test_05_pilot_deck_nodal_and_element_consistency():
    """Verify node counts, element counts, and layered architecture of PK_F1721_ADAPTED_PILOT.inp."""
    with open(DECK_PILOT, "r") as f:
        lines = f.readlines()
        
    # Count nodes
    in_nodes = False
    node_lines = 0
    max_node_id = 0
    for line in lines:
        if line.strip().upper().startswith("*NODE"):
            in_nodes = True
            continue
        elif in_nodes and line.strip().startswith("*"):
            in_nodes = False
        elif in_nodes:
            parts = line.strip().split(",")
            if len(parts) >= 3:
                node_lines += 1
                try:
                    nid = int(parts[0])
                    if nid > max_node_id:
                        max_node_id = nid
                except ValueError:
                    pass
                    
    assert node_lines == 13402, f"Expected exactly 13,402 nodes, found {node_lines}"
    assert max_node_id == 13402, f"Expected reference node ID 13402, found {max_node_id}"
    
    # Count elements
    element_headers = [l.strip() for l in lines if l.strip().upper().startswith("*ELEMENT,")]
    assert len(element_headers) == 6, f"Expected 6 *ELEMENT blocks (3 layers x 2 element types), found {len(element_headers)}"
    
    # Layer 1: U1 (quad) + U3 (tri)
    assert any("TYPE=U1" in h and "ELSET=PHASE_QUADS" in h for h in element_headers)
    assert any("TYPE=U3" in h and "ELSET=PHASE_TRIS" in h for h in element_headers)
    # Layer 2: U2 (quad) + U4 (tri)
    assert any("TYPE=U2" in h and "ELSET=MECH_QUADS" in h for h in element_headers)
    assert any("TYPE=U4" in h and "ELSET=MECH_TRIS" in h for h in element_headers)
    # Layer 3: CPE4 (quad) + CPE3 (tri)
    assert any("TYPE=CPE4" in h and "ELSET=UMAT_QUADS" in h for h in element_headers)
    assert any("TYPE=CPE3" in h and "ELSET=UMAT_TRIS" in h for h in element_headers)

def test_06_pilot_deck_reconstructed_increment_schedule():
    """Verify reconstructed literature increment schedule (*STATIC, DIRECT) in pilot deck."""
    with open(DECK_PILOT, "r") as f:
        lines = f.readlines()
        
    step_indices = [i for i, l in enumerate(lines) if l.strip().upper().startswith("*STEP")]
    assert len(step_indices) == 2, f"Expected exactly 2 steps, found {len(step_indices)}"
    
    # Inspect Step 1
    s1_idx = step_indices[0]
    assert "*STEP, NAME=Step-1" in lines[s1_idx]
    assert "INC=2500" in lines[s1_idx]
    assert lines[s1_idx + 1].strip() == "*STATIC, DIRECT"
    assert lines[s1_idx + 2].strip() == "1.0e-4, 0.20"
    
    # Check Step 1 boundary cards
    s1_block = "".join(lines[s1_idx:step_indices[1]])
    assert "N_BOTTOM, 2, 2, 0.0" in s1_block
    assert "N_PIN, 1, 1, 0.0" in s1_block
    assert "N_RP, 1, 1, 0.0" in s1_block
    assert "N_RP, 2, 2, 0.0050" in s1_block
    
    # Inspect Step 2
    s2_idx = step_indices[1]
    assert "*STEP, NAME=Step-2" in lines[s2_idx]
    assert "INC=6000" in lines[s2_idx]
    assert lines[s2_idx + 1].strip() == "*STATIC, DIRECT"
    assert lines[s2_idx + 2].strip() == "5.0e-5, 0.25"
    
    # Check Step 2 boundary cards
    s2_block = "".join(lines[s2_idx:])
    assert "N_BOTTOM, 2, 2, 0.0" in s2_block
    assert "N_PIN, 1, 1, 0.0" in s2_block
    assert "N_RP, 1, 1, 0.0" in s2_block
    assert "N_RP, 2, 2, 0.0100" in s2_block

def test_07_nset_line_wrapping_conformance():
    """Verify that all *NSET lines adhere to Abaqus <= 16 items per line constraint."""
    with open(DECK_PILOT, "r") as f:
        lines = f.readlines()
        
    in_nset = False
    for i, line in enumerate(lines):
        txt = line.strip()
        if txt.upper().startswith("*NSET"):
            in_nset = True
            continue
        elif in_nset and txt.startswith("*"):
            in_nset = False
        elif in_nset:
            if not txt:
                continue
            entries = [e.strip() for e in txt.split(",") if e.strip()]
            assert len(entries) <= 16, f"Line {i+1} in NSET has {len(entries)} entries (>16): {txt}"

def test_08_equation_constraints_integrity():
    """Verify that *EQUATION MPCs correctly link top edge nodes to reference node 13402."""
    with open(DECK_PILOT, "r") as f:
        lines = f.readlines()
        
    eq_indices = [i for i, l in enumerate(lines) if l.strip().upper().startswith("*EQUATION")]
    assert len(eq_indices) == 1, f"Expected 1 *EQUATION card block, found {len(eq_indices)}"
    
    idx = eq_indices[0]
    # Check MPC lines
    mpc_count = 0
    for j in range(idx + 1, len(lines)):
        line = lines[j].strip()
        if line.startswith("*"):
            break
        if line == "2":
            data_line = lines[j+1].strip()
            parts = [p.strip() for p in data_line.split(",")]
            assert len(parts) == 6, f"Malformed equation line: {data_line}"
            assert parts[1] == "2", "Degree of freedom must be 2 (uy)"
            assert parts[3] == "13402", "Master node must be reference node 13402"
            assert parts[4] == "2", "Master degree of freedom must be 2"
            assert float(parts[2]) == 1.0, "Slave coefficient must be +1.0"
            assert float(parts[5]) == -1.0, "Master coefficient must be -1.0"
            mpc_count += 1
            
    assert mpc_count == 52, f"Expected 52 top boundary MPC equations, found {mpc_count}"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
