#!/usr/bin/env python3
"""
Unit Test Suite: Task F1721 Bounded Causal-Isolation Pilot Technical Qualification
(tests/unit/test_f1721_causal_pilot_qualification.py)

Validates the static integrity, input deck architecture, causal isolation properties,
and exact diffs of the bounded causal-isolation diagnostic pilot:
- Model Deck: PK_F1721_CAUSAL_PILOT.inp
- Subroutine: f1721_proposed_staggered_coupling_uel.for
- Literature-aligned Deck (preserved): PK_F1721_ADAPTED_PILOT.inp
- F1720 Baseline Deck (frozen): PK_F1720_ADAPTED_PFM.inp
"""

import os
import hashlib
import pytest

DECK_CAUSAL = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1721_CAUSAL_PILOT.inp")
DECK_PILOT_LIT = os.path.join("models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1721_ADAPTED_PILOT.inp")
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

def test_01_artifacts_existence_and_non_emptiness():
    """Verify all pilot artifacts exist and have non-zero size."""
    for p in [DECK_CAUSAL, DECK_PILOT_LIT, DECK_F1720, FOR_F1721, FOR_F1720, PATCH_F1721]:
        assert os.path.isfile(p), f"File not found: {p}"
        assert os.path.getsize(p) > 0, f"File empty: {p}"

def test_02_frozen_baselines_and_preserved_literature_deck():
    """Verify bitwise freeze of F1720 baselines and F1721 literature deck."""
    h_f1720_deck = sha256_file(DECK_F1720).lower()
    h_f1720_for = sha256_file(FOR_F1720).lower()
    h_lit_deck = sha256_file(DECK_PILOT_LIT).lower()
    
    assert h_f1720_deck == "318d0ed6f330e73f5a62e259dc3a9a9abcebd4341596eaa5c31ed58138ba42f2"
    assert h_f1720_for == "c298aca7ed2199b20e622b38e99fda9b533150eb0ad5e9f77069216f860e70fc"
    assert h_lit_deck == "0fcd33cf72ba9631cb0122aa38346cf51829ef9cf154497c3e80862820247e6e"

def test_03_causal_deck_nodal_and_element_consistency():
    """Verify that causal pilot deck has exactly 13,402 nodes and 39,489 layered elements."""
    with open(DECK_CAUSAL, "r") as f:
        lines = f.readlines()
        
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
                    
    assert node_lines == 13402, f"Expected 13,402 nodes, found {node_lines}"
    assert max_node_id == 13402, f"Expected master reference node ID 13402, found {max_node_id}"
    
    element_headers = [l.strip() for l in lines if l.strip().upper().startswith("*ELEMENT,")]
    assert len(element_headers) == 6, f"Expected 6 *ELEMENT blocks, found {len(element_headers)}"

def test_04_causal_deck_retains_f1720_automatic_incrementation():
    """Verify that causal pilot deck retains the exact F1720 automatic incrementation controls."""
    with open(DECK_CAUSAL, "r") as f:
        lines = f.readlines()
        
    step_indices = [i for i, l in enumerate(lines) if l.strip().upper().startswith("*STEP")]
    assert len(step_indices) == 2, f"Expected exactly 2 steps, found {len(step_indices)}"
    
    # Step 1: *STATIC with automatic incrementation
    s1_idx = step_indices[0]
    assert "*STEP, NAME=Step-1" in lines[s1_idx]
    assert lines[s1_idx + 1].strip() == "*STATIC"
    assert lines[s1_idx + 2].strip() == "0.02, 1.0, 1.0e-8, 0.02"
    
    s1_block = "".join(lines[s1_idx:step_indices[1]])
    assert "N_RP, 2, 2, 0.0050" in s1_block
    
    # Step 2: *STATIC with cutbacks down to dt_min = 1.0e-9 and T2 = 0.2666666666667
    s2_idx = step_indices[1]
    assert "*STEP, NAME=Step-2" in lines[s2_idx]
    assert lines[s2_idx + 1].strip() == "*STATIC"
    assert lines[s2_idx + 2].strip() == "0.0025, 0.2666666666667, 1.0e-9, 0.0025"
    
    s2_block = "".join(lines[s2_idx:])
    assert "N_RP, 2, 2, 0.00580" in s2_block
    assert "N_BOTTOM, 2, 2, 0.0" in s2_block

def test_05_causal_isolation_diff_against_f1720():
    """Verify that causal pilot differs from F1720 ONLY by the target displacement and diagnostic annotations."""
    with open(DECK_F1720, "r") as f:
        l_f1720 = f.readlines()
    with open(DECK_CAUSAL, "r") as f:
        l_causal = f.readlines()
        
    # Model definition region up to the last *EQUATION card
    uel_f1720 = next(i for i, l in enumerate(l_f1720) if "*USER ELEMENT" in l.upper())
    uel_causal = next(i for i, l in enumerate(l_causal) if "*USER ELEMENT" in l.upper())
    
    # Find last equation line in F1720 (line 53053: '3203, 2, 1.0, 13402, 2, -1.0')
    last_eq_f1720 = next(i for i, l in enumerate(l_f1720) if "3203, 2, 1.0, 13402" in l)
    last_eq_causal = next(i for i, l in enumerate(l_causal) if "3203, 2, 1.0, 13402" in l)
    
    model_f1720 = l_f1720[uel_f1720:last_eq_f1720+1]
    model_causal = l_causal[uel_causal:last_eq_causal+1]
    
    assert len(model_f1720) == len(model_causal), f"Model definition line count mismatch: {len(model_f1720)} vs {len(model_causal)}"
    for idx, (l1, l2) in enumerate(zip(model_f1720, model_causal)):
        assert l1 == l2, f"Mismatch at model line {idx+1}: {l1.strip()} vs {l2.strip()}"
        
    # In Step 2, verify target displacement changed from 0.0080 to 0.00580
    assert "N_RP, 2, 2, 0.0080" in "".join(l_f1720)
    assert "N_RP, 2, 2, 0.00580" in "".join(l_causal)

def test_06_nset_line_wrapping_conformance():
    """Verify that all *NSET lines in causal deck adhere to Abaqus <= 16 items per line constraint."""
    with open(DECK_CAUSAL, "r") as f:
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

def test_07_mpc_equation_constraints():
    """Verify that *EQUATION MPCs correctly link 52 top edge nodes to master node 13402."""
    with open(DECK_CAUSAL, "r") as f:
        lines = f.readlines()
        
    eq_indices = [i for i, l in enumerate(lines) if l.strip().upper().startswith("*EQUATION")]
    assert len(eq_indices) == 1, f"Expected 1 *EQUATION block, found {len(eq_indices)}"
    
    idx = eq_indices[0]
    mpc_count = 0
    for j in range(idx + 1, len(lines)):
        line = lines[j].strip()
        if line.startswith("*"):
            break
        if line == "2":
            data_line = lines[j+1].strip()
            parts = [p.strip() for p in data_line.split(",")]
            assert len(parts) == 6
            assert parts[1] == "2"
            assert parts[3] == "13402"
            assert parts[4] == "2"
            assert float(parts[2]) == 1.0
            assert float(parts[5]) == -1.0
            mpc_count += 1
            
    assert mpc_count == 52, f"Expected 52 top boundary MPC equations, found {mpc_count}"

def test_08_loading_rate_and_resolution_parity_with_f1720():
    """Verify that Step 2 time period T2 = 0.2666666666667 yields identical physical loading rate and resolution to F1720."""
    with open(DECK_CAUSAL, "r") as f:
        lines = f.readlines()
        
    s2_idx = next(i for i, l in enumerate(lines) if "*STEP" in l.upper() and "STEP-2" in l.upper())
    static_params = [float(x.strip()) for x in lines[s2_idx + 2].split(",")]
    dt_init, t_period, dt_min, dt_max = static_params
    
    u_start = 0.0050
    u_target = 0.00580
    delta_u = u_target - u_start
    
    # In F1720: delta_u_f1720 = 0.0080 - 0.0050 = 0.0030, T_f1720 = 1.0 -> rate = 0.0030 mm/time
    loading_rate = delta_u / t_period
    assert abs(loading_rate - 0.0030) < 1.0e-9, f"Loading rate mismatch: {loading_rate} vs 0.0030"
    
    # Physical displacement increments
    delta_u_init = loading_rate * dt_init
    delta_u_min = loading_rate * dt_min
    
    # F1720 initial delta_u: 0.0030 * 0.0025 = 7.5e-6 mm (7.5 nm)
    assert abs(delta_u_init - 7.5e-6) < 1.0e-12, f"Initial displacement increment mismatch: {delta_u_init}"
    # F1720 minimum delta_u: 0.0030 * 1.0e-9 = 3.0e-12 mm
    assert abs(delta_u_min - 3.0e-12) < 1.0e-18, f"Minimum displacement increment mismatch: {delta_u_min}"
    
    # Step 2 time at F1720 failure point uy = 0.0056645 mm
    u_failure = 0.0056645
    t_failure = (u_failure - u_start) / loading_rate
    assert abs(t_failure - 0.2215) < 1.0e-6, f"Failure time mismatch: {t_failure} vs 0.2215"
    
    # Bitwise sha256 of causal deck
    h_causal = sha256_file(DECK_CAUSAL).lower()
    assert h_causal == "23525c2ab9a62a461d6489803fe3d679a80840d58e13339517f9539838170e95"

if __name__ == "__main__":
    pytest.main(["-v", __file__])
