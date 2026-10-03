"""
Unit tests for audit_mode1_architecture_isolation.py
"""

import os
import sys
import json
import pathlib
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from scripts.audit.audit_mode1_architecture_isolation import (
    parse_deck,
    perform_architecture_isolation_audit,
    export_audit_artifacts
)

P89_DECK = pathlib.Path(r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\89_mode1_preanalysis_uel_canonical_2906\PK_M1_JOB1_UEL_2906.inp")
P90_DECK = pathlib.Path(r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\90_mode1_preanalysis_continuum_matched_2906\PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp")
P89_SUB = pathlib.Path(r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\89_mode1_preanalysis_uel_canonical_2906\f42_mixed_uel.for")
P89_PBS = pathlib.Path(r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\89_mode1_preanalysis_uel_canonical_2906\submit_solver.pbs")
P90_PBS = pathlib.Path(r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode1\90_mode1_preanalysis_continuum_matched_2906\submit_solver.pbs")


def test_architecture_isolation_audit_verdict_valid():
    summary = perform_architecture_isolation_audit(P89_DECK, P90_DECK, P89_SUB, P89_PBS, P90_PBS)
    assert summary["verdict"] == "ARCHITECTURE_ISOLATION_CONTROL_VALID"
    assert len(summary["confounds"]) == 0
    assert summary["classification_counts"]["UNINTENDED_CONFOUNDING_DIFFERENCE"] == 0
    assert summary["classification_counts"]["IDENTICAL"] >= 25
    assert summary["classification_counts"]["EQUIVALENT_BY_CONSTRUCTION"] >= 5


def test_node_and_seam_topology_bit_identical():
    d89 = parse_deck(P89_DECK)
    d90 = parse_deck(P90_DECK)
    
    nodes89 = d89["nodes"]
    nodes90 = d90["nodes"]
    
    assert len(nodes89) == 2989
    assert len(nodes90) == 2989
    assert set(nodes89.keys()) == set(nodes90.keys())
    
    for nid in nodes89:
        c89 = nodes89[nid]
        c90 = nodes90[nid]
        assert abs(c89[0] - c90[0]) < 1e-12
        assert abs(c89[1] - c90[1]) < 1e-12
        assert abs(c89[2] - c90[2]) < 1e-12
        
    assert nodes89[999999] == (0.5, 1.0, 0.0)
    assert nodes90[999999] == (0.5, 1.0, 0.0)
    assert nodes89[25] == (0.0, 0.0, 0.0)
    assert nodes90[25] == (0.0, 0.0, 0.0)


def test_rp_coupling_and_lateral_kinematics():
    d89 = parse_deck(P89_DECK)
    d90 = parse_deck(P90_DECK)
    
    assert len(d89["equations"]) == 51
    assert len(d90["equations"]) == 51
    assert d89["equations"] == d90["equations"]
    
    # Check that DOF 1 (u_x) is never constrained in equations
    for header, lines in d89["equations"]:
        for line in lines:
            parts = [p.strip() for p in line.split(",") if p.strip()]
            if len(parts) >= 2:
                # Format: node, dof, coeff, ...
                dof1 = int(parts[1])
                assert dof1 == 2, f"Expected DOF 2 in equation line: {line}"


def test_material_and_stiffness_contract():
    d89 = parse_deck(P89_DECK)
    d90 = parse_deck(P90_DECK)
    
    # Package 90: steel elastic
    assert "*MATERIAL, NAME=STEEL" in d90["materials"]
    
    # Package 89: subroutine tangent
    sub_text = P89_SUB.read_text(encoding="utf-8")
    assert "DDSDDE(I,I) = 1.D-11" in sub_text
    assert "DDSDDE(I,J) = ZERO" in sub_text


def test_terminal_comparison_manifest_contract(tmp_path):
    summary = perform_architecture_isolation_audit(P89_DECK, P90_DECK, P89_SUB, P89_PBS, P90_PBS)
    export_audit_artifacts(summary, tmp_path)
    
    manifest_file = tmp_path / "TERMINAL_COMPARISON_MANIFEST_89_VS_90.json"
    assert manifest_file.exists()
    
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest["isolation_verdict"] == "ARCHITECTURE_ISOLATION_CONTROL_VALID"
    assert manifest["evaluator_governance_rules"]["displacement_rescaling_allowed"] is False
    assert manifest["evaluator_governance_rules"]["arbitrary_localization_thresholds_allowed"] is False
    assert len(manifest["matched_evaluation_states"]) == 2
    assert manifest["matched_evaluation_states"][0]["target_displacement_mm"] == 0.0050
    assert manifest["matched_evaluation_states"][1]["target_displacement_mm"] == 0.0100
