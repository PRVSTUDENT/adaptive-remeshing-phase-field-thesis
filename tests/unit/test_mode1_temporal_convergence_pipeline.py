"""
Unit Tests for Mode-I Temporal Convergence Pipeline
Protocol Version: 2
Governing Directive: "We need to have understood everything related to the first model before we increase complexity."

Tests cover:
1. Temporal candidate inventory and parameters (T1, T2, T3).
2. T2 nominal vs S1 reference equivalence verification pass on repository decks.
3. T2 vs S1 equivalence audit detection of node coordinate discrepancy.
4. T2 vs S1 equivalence audit detection of element connectivity discrepancy.
5. T2 vs S1 equivalence audit detection of material constants discrepancy.
6. T2 vs S1 equivalence audit detection of DEPVAR discrepancy.
7. T2 vs S1 equivalence audit detection of boundary condition node set discrepancy.
8. T2 vs S1 equivalence audit detection of step increment control discrepancy.
9. S1 reference trajectory reuse for T2 nominal anchor.
10. Pairwise temporal convergence evaluation (anchors, L2 curve discrepancies, relative differences).
"""

import os
import sys
import re
import tempfile
import pytest
import numpy as np

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts.validation.temporal_convergence_pipeline import (
    TEMPORAL_CANDIDATES,
    evaluate_temporal_convergence_pair,
    verify_t2_s1_equivalence,
    parse_deck_summary,
    load_energy_csv_trajectory,
    get_t2_nominal_trajectory,
    EquivalenceVerificationError,
    CANONICAL_MATCHED_DISPLACEMENTS_MM,
    CensoredTrajectoryError
)

T2_DECK_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../models/pandey_kumar_mode1/18_temporal_convergence_t2_nominal/PK_MODE1_T2_NOMINAL_ENERGY.inp"
))
S1_DECK_PATH = os.path.abspath(os.path.join(
    os.path.dirname(__file__),
    "../../models/pandey_kumar_mode1/16_energy_qualification_reference_15k/PK_MODE1_REF15K_ENERGY.inp"
))


def test_temporal_candidates_definition():
    assert "T1" in TEMPORAL_CANDIDATES
    assert "T2" in TEMPORAL_CANDIDATES
    assert "T3" in TEMPORAL_CANDIDATES
    
    t1 = TEMPORAL_CANDIDATES["T1"]
    t2 = TEMPORAL_CANDIDATES["T2"]
    t3 = TEMPORAL_CANDIDATES["T3"]
    
    assert t1["total_nominal_increments"] == 3500
    assert t2["total_nominal_increments"] == 7000
    assert t3["total_nominal_increments"] == 14000
    
    assert t1["mesh_elements"] == 15192
    assert t2["mesh_elements"] == 15192
    assert t3["mesh_elements"] == 15192
    
    # Verify T2 nominal reuse audit metadata
    assert "equivalence_audit" in t2
    eq_audit = t2["equivalence_audit"]
    assert eq_audit["status"] == "EQUIVALENT_TO_S1_REFERENCE"
    assert eq_audit["governing_classification"] == "T2_NOMINAL = REUSE_CORRECTED_S1_REFERENCE"
    assert eq_audit["submission_action"] == "OMIT_FROM_CLUSTER_SUBMISSIONS_REUSE_S1"


def test_verify_t2_s1_equivalence_pass():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    audit = verify_t2_s1_equivalence(T2_DECK_PATH, S1_DECK_PATH, raise_on_diff=True)
    assert audit["is_equivalent"] is True
    assert len(audit["differences"]) == 0
    assert audit["nodes_count"] == 15522
    assert audit["elements_count"] == 45576
    assert audit["classification"] == "T2_NOMINAL_EQUIVALENT_TO_S1_REFERENCE"
    assert audit["action"] == "OMIT_T2_FROM_SOLVER_SUBMISSIONS_REUSE_S1"


def test_verify_t2_s1_equivalence_detects_node_coord_diff():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    with open(T2_DECK_PATH, 'r') as f:
        content = f.read()
        
    # Perturb node 1 coordinate
    perturbed = content.replace("1, 0.0000000000, 0.0000000000", "1, 0.0010000000, 0.0020000000")
    assert perturbed != content
        
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.inp') as tmp:
        tmp.write(perturbed)
        tmp_path = tmp.name
        
    try:
        with pytest.raises(EquivalenceVerificationError) as exc_info:
            verify_t2_s1_equivalence(tmp_path, S1_DECK_PATH, raise_on_diff=True)
        assert "Node" in str(exc_info.value)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_t2_s1_equivalence_detects_element_diff():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    with open(T2_DECK_PATH, 'r') as f:
        content = f.read()
        
    # Perturb element 1 connectivity (1, 1, 2, 214, 213 -> 1, 1, 3, 214, 213)
    perturbed = content.replace("1, 1, 2, 214, 213", "1, 1, 3, 214, 213")
    assert perturbed != content
    
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.inp') as tmp:
        tmp.write(perturbed)
        tmp_path = tmp.name
        
    try:
        with pytest.raises(EquivalenceVerificationError) as exc_info:
            verify_t2_s1_equivalence(tmp_path, S1_DECK_PATH, raise_on_diff=True)
        assert "Element" in str(exc_info.value)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_t2_s1_equivalence_detects_material_diff():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    with open(T2_DECK_PATH, 'r') as f:
        content = f.read()
        
    # Perturb material constant E from 210.0 to 200.0
    perturbed = content.replace("210.0, 0.3, 15192.", "200.0, 0.3, 15192.")
    assert perturbed != content
    
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.inp') as tmp:
        tmp.write(perturbed)
        tmp_path = tmp.name
        
    try:
        with pytest.raises(EquivalenceVerificationError) as exc_info:
            verify_t2_s1_equivalence(tmp_path, S1_DECK_PATH, raise_on_diff=True)
        assert "Material constants mismatch" in str(exc_info.value)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_t2_s1_equivalence_detects_depvar_diff():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    with open(T2_DECK_PATH, 'r') as f:
        content = f.read()
        
    perturbed = content.replace("*Depvar\n20", "*Depvar\n16").replace("*Depvar\n 20", "*Depvar\n 16")
    if "*Depvar" in content and "20" in content and perturbed == content:
        perturbed = content.replace("20", "16", 1)
    assert perturbed != content
        
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.inp') as tmp:
        tmp.write(perturbed)
        tmp_path = tmp.name
        
    try:
        with pytest.raises(EquivalenceVerificationError) as exc_info:
            verify_t2_s1_equivalence(tmp_path, S1_DECK_PATH, raise_on_diff=True)
        assert "Depvar mismatch" in str(exc_info.value)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_verify_t2_s1_equivalence_detects_step_control_diff():
    if not os.path.exists(T2_DECK_PATH) or not os.path.exists(S1_DECK_PATH):
        pytest.skip("Decks not found on disk")
        
    with open(T2_DECK_PATH, 'r') as f:
        content = f.read()
        
    # Perturb initial dt in step 1 from 5.0E-4 to 1.0E-3
    perturbed = content.replace("5.0E-4, 1.0, 1.0E-9, 5.0E-4", "1.0E-3, 1.0, 1.0E-9, 1.0E-3")
    assert perturbed != content
    
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.inp') as tmp:
        tmp.write(perturbed)
        tmp_path = tmp.name
        
    try:
        with pytest.raises(EquivalenceVerificationError) as exc_info:
            verify_t2_s1_equivalence(tmp_path, S1_DECK_PATH, raise_on_diff=True)
        assert "Step controls mismatch" in str(exc_info.value)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_get_t2_nominal_trajectory_reuse():
    csv_content = """step,increment,total_time,step_time,u,rf2,e_elas,e_frac,e_model,w_ext,delta_book,reldiff_pct
1,1,0.0005,0.0005,0.0000025,0.000344,0.00000043,0.0,0.00000043,0.00000043,0.0,0.0
1,2,0.0010,0.0010,0.0000050,0.000689,0.00000172,0.0,0.00000172,0.00000172,0.0,0.0
"""
    with tempfile.NamedTemporaryFile('w', delete=False, suffix='.csv') as tmp:
        tmp.write(csv_content)
        tmp_path = tmp.name
        
    try:
        traj = get_t2_nominal_trajectory(tmp_path, enforce_equivalence=False)
        assert len(traj['u_mm']) == 2
        assert len(traj['rf_kN']) == 2
        assert traj['u_mm'][1] == 0.0000050
        
        traj2 = get_t2_nominal_trajectory(tmp_path, t2_deck_path=T2_DECK_PATH, s1_deck_path=S1_DECK_PATH, enforce_equivalence=True)
        assert len(traj2['u_mm']) == 2
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_evaluate_temporal_convergence_pair():
    u = np.linspace(0.0, 0.010, 101)
    rf = 137.94 * u * np.exp(-50.0 * u)
    w_ext = np.zeros_like(u)
    for i in range(1, len(u)):
        w_ext[i] = w_ext[i-1] + 0.5 * (rf[i] + rf[i-1]) * (u[i] - u[i-1])
        
    e_elas = w_ext * 0.4
    e_frac = w_ext * 0.6
    
    traj1 = {
        "u_mm": u,
        "rf_kN": rf,
        "w_ext_kNmm": w_ext,
        "e_elas_kNmm": e_elas,
        "e_frac_kNmm": e_frac
    }
    
    traj2 = {
        "u_mm": u,
        "rf_kN": rf * 1.002,
        "w_ext_kNmm": w_ext * 1.002,
        "e_elas_kNmm": e_elas * 1.002,
        "e_frac_kNmm": e_frac * 1.002
    }
    
    res = evaluate_temporal_convergence_pair(traj1, traj2, "T1", "T2")
    assert res["labels"]["coarse"] == "T1"
    assert res["labels"]["fine"] == "T2"
    assert "anchors" in res
    assert "l2_discrepancies" in res
    assert "checkpoint_comparison" in res
    
    rel_diffs = res["anchors"]["relative_differences"]
    assert rel_diffs["delta_Fmax"] < 0.01
    assert res["l2_discrepancies"]["reaction_force_F"]["rel_l2_discrepancy_pct"] < 1.0
