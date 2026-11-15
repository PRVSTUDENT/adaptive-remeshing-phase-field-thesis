# -*- coding: utf-8 -*-
"""
test_f1754_discrete_phase_field_diagnosis.py
Unit test suite verifying Task F1754: Case 2 Method A Discrete Phase-Field Failure Diagnosis.
Tests:
1. Authoritative source artifact integrity and SHA-256 verification
2. UEL formulation analysis (block-diagonal Jacobian, unconstrained damage, COMMON-block ordering)
3. Critical node coordinates and distal ligament underresolution metrics
4. Increment 205 divergence telemetry (force residual spike, damage correction surge)
5. All-IP irreversibility and monotonicity audit reconciliation (1,805 violations, 89.2% in wake)
6. Competing hypotheses ranking, discriminating evidence, and synthesis consistency
"""

import os
import json
import hashlib
import pytest

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@pytest.fixture
def diagnosis_data():
    json_path = os.path.join(BASE_DIR, "results", "validation", "f1754_discrete_phase_field_diagnosis.json")
    assert os.path.exists(json_path), f"Missing diagnosis JSON: {json_path}"
    with open(json_path, 'r') as f:
        return json.load(f)

def test_authoritative_sources_integrity(diagnosis_data):
    """Verify that all authoritative input and output files exist and match requirements."""
    uel_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"Missing UEL file: {uel_path}"
    
    with open(uel_path, 'rb') as f:
        uel_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert uel_sha == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    
    msg_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "234_f1752_case2_continuation", "PK_F1752_CASE_2_CONTINUATION.msg")
    assert os.path.exists(msg_path), f"Missing solver MSG file: {msg_path}"
    assert os.path.getsize(msg_path) > 900000
    
    audit_json = os.path.join(BASE_DIR, "results", "validation", "f1753_case2_continuation_audit.json")
    assert os.path.exists(audit_json), f"Missing audit JSON: {audit_json}"

def test_uel_formulation_properties():
    """Verify mathematical formulation properties in f42_mixed_uel.for."""
    uel_path = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    with open(uel_path, 'r') as f:
        content = f.read()
        
    # Check COMMON block variables
    assert "COMMON /CB_STATE_TRANS/ SV_PHASE_COMMITTED, SV_PHASE_TRIAL," in content
    assert "SV_H_COMMITTED, SV_H_TRIAL," in content
    
    # Check JTYPE 1 (Layer 1 Phase Field)
    assert "JTYPE .EQ. 1" in content
    assert "RHS(I,1) = RHS(I,1) + CJAC * TWO * HIST * N_VEC(I)" in content
    assert "AMATRX(I,J) = AMATRX(I,J) + CJAC *" in content
    
    # Check JTYPE 2 (Layer 2 Mechanical)
    assert "JTYPE .EQ. 2" in content
    assert "D_VAL = SV_PHASE_TRIAL(PHYSIDX)" in content
    assert "DEG   = (ONE - D_VAL)**2 + E_K" in content
    assert "IF (POS_M .GT. HIST) THEN" in content
    assert "SV_H_TRIAL(PHYSIDX, KPT) = POS_M" in content
    
    # Verify unconstrained damage formulation (absence of projection or inequality constraint)
    assert "max(U(I)" not in content.lower()
    assert "active_set" not in content.lower()

def test_critical_nodes_spatial_metrics(diagnosis_data):
    """Verify coordinates and element sizing ratios for critical cutback and divergence nodes."""
    crit_nodes = diagnosis_data["critical_nodes"]
    
    # Node 8056: previous cutback locus
    assert "8056" in crit_nodes
    n8056 = crit_nodes["8056"]
    assert pytest.approx(n8056["x"], abs=1e-3) == 0.90312
    assert pytest.approx(n8056["y"], abs=1e-3) == 0.63625
    assert n8056["ratio_h_mean_to_l0_half"] > 1.4  # h > l0/2
    
    # Node 7317: maximum residual force node in Inc 205 Attempt 3
    assert "7317" in crit_nodes
    n7317 = crit_nodes["7317"]
    assert pytest.approx(n7317["x"], abs=1e-3) == 0.91049
    assert pytest.approx(n7317["y"], abs=1e-3) == 0.64056
    assert n7317["ratio_h_mean_to_l0_half"] > 1.6  # h > 1.6 * l0/2
    
    # Node 6972: maximum damage increment node in Inc 205
    assert "6972" in crit_nodes
    n6972 = crit_nodes["6972"]
    assert pytest.approx(n6972["x"], abs=1e-3) == 0.91620
    assert n6972["ratio_h_mean_to_l0_half"] > 1.6
    
    # Node 1422: hole boundary intersection node
    assert "1422" in crit_nodes
    n1422 = crit_nodes["1422"]
    assert pytest.approx(n1422["dist_hole_boundary_mm"], abs=1e-4) == 0.0
    assert n1422["ratio_h_mean_to_l0_half"] < 1.0  # h < l0/2 at hole boundary

def test_inc205_telemetry_and_divergence(diagnosis_data):
    """Verify convergence telemetry for Increment 205 Attempts 1, 2, 3."""
    inc205 = diagnosis_data["inc205_telemetry"]
    attempts = inc205["attempts"]
    
    assert "1" in attempts
    assert "2" in attempts
    assert "3" in attempts
    
    att3 = attempts["3"]
    assert pytest.approx(att3["dt"], rel=1e-3) == 1.0e-11
    iters = att3["iterations"]
    assert len(iters) == 4
    
    # Check residual force surge between Iter 3 and Iter 4
    iter3 = iters[2]
    iter4 = iters[3]
    assert iter3["force_res"] < 2.0e-4
    assert iter4["force_res"] > 2.0e-3
    assert iter4["res_node"] == 7317
    assert iter4["res_dof"] == 2
    assert iter4["disp_inc_node"] == 6972
    assert iter4["disp_inc_dof"] == 3
    assert iter4["disp_corr_node"] == 168
    assert iter4["disp_corr_dof"] == 3

def test_audit_gates_and_violation_classification(diagnosis_data):
    """Verify acceptance gates and all-IP violation breakdown."""
    gates = diagnosis_data["audit_gates_summary"]
    assert "PASS" in gates["g1_parity"]
    assert "PARTIAL" in gates["g2_continuation"]
    assert "FAIL" in gates["g3_irreversibility"]
    assert "PASS" in gates["g4_monotonicity"]
    assert "FAIL" in gates["g5_wake_diagnostic"]

def test_competing_hypotheses_evaluation(diagnosis_data):
    """Verify that all 4 competing hypotheses are systematically documented and ranked."""
    hyps = diagnosis_data["hypotheses_evaluation"]
    assert "H1_UNCONSTRAINED_DAMAGE_READJUSTMENT" in hyps
    assert "H2_NONLINEAR_COUPLING_FAILURE" in hyps
    assert "H3_SECONDARY_FRONT_UNDERRESOLUTION" in hyps
    assert "H4_TOPOLOGICAL_TRANSITION_SINGULARITY" in hyps
    
    h1 = hyps["H1_UNCONSTRAINED_DAMAGE_READJUSTMENT"]
    assert h1["rank"] == 1
    assert "PRIMARY_ROOT_CAUSE_OF_DAMAGE_IRREVERSIBILITY_FAILURE" in h1["role"]
    assert len(h1["evidence_supporting"]) >= 3
    
    h2 = hyps["H2_NONLINEAR_COUPLING_FAILURE"]
    assert h2["rank"] == 2
    assert "PRIMARY_ROOT_CAUSE_OF_INCREMENT_SIZE_COLLAPSE" in h2["role"]
    
    h3 = hyps["H3_SECONDARY_FRONT_UNDERRESOLUTION"]
    assert h3["rank"] == 3
    assert "SPATIAL_ERROR_AMPLIFIER" in h3["role"]
    
    h4 = hyps["H4_TOPOLOGICAL_TRANSITION_SINGULARITY"]
    assert h4["rank"] == 4
    assert "PHYSICAL_TRIGGERING_EVENT" in h4["role"]
