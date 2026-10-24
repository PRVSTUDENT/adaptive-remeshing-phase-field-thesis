#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn105_c3_acceptance.py
Unit tests verifying Turn 105 three-state C3 acceptance evidence table,
State 1 gate failure diagnosis, and bounded corrective history investigation.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn105_c3_state1_acceptance_audit.json"
INV_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn105_history_investigation.json"

def test_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"
    assert INV_JSON.exists(), f"Investigation file not found: {INV_JSON}"

def test_three_state_evidence_table():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    tbl = data["three_state_acceptance_evidence_table"]

    sA = tbl["state_A_c2_donor"]
    assert sA["u_prescribed_mm"] == pytest.approx(0.00196510735, rel=1e-6)
    assert sA["rf2_N"] == pytest.approx(189.5358, rel=1e-3)
    assert sA["d_max"] == pytest.approx(0.478622, rel=1e-3)

    sB = tbl["state_B_c3_state0"]
    assert sB["diff_rf2_pct"] == pytest.approx(0.0007, abs=1e-2)
    assert sB["diff_ef_pct"] == pytest.approx(0.0002, abs=1e-2)
    assert sB["interpolation_parity_verdict"] == "PASS"

    sC = tbl["state_C_c3_state1"]
    assert sC["diff_rf2_pct"] == pytest.approx(-29.51, abs=0.5)
    assert sC["diff_ef_pct"] == pytest.approx(104.50, abs=1.0)
    assert sC["d_max"] > 0.99
    assert sC["converged"] is False
    assert sC["state1_parity_verdict"] == "FAIL"

def test_transfer_gates_verdicts():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    gates = data["gates"]
    # State 0 passes continuity
    assert gates["gate1_force_continuity"]["state0_pass"] is True
    assert gates["gate2_fracture_energy_continuity"]["state0_pass"] is True
    # State 1 fails continuity
    assert gates["gate1_force_continuity"]["state1_pass"] is False
    assert gates["gate2_fracture_energy_continuity"]["state1_pass"] is False
    # Residuals and irreversibility
    assert gates["gate4_mechanical_equilibrium"]["state1_pass"] is True
    assert gates["gate5_kkt_complementarity"]["pass"] is True
    assert gates["gate6_damage_healing"]["pass"] is True
    assert gates["gate7_damage_overshoot"]["pass"] is True
    assert gates["gate8_coupled_iterations"]["pass"] is False

def test_corrective_history_investigation():
    with open(INV_JSON, "r", encoding="utf-8") as f:
        inv = json.load(f)
    assert inv["max_h_donor"] == pytest.approx(1.297688, rel=1e-4)
    assert inv["max_h_recipient_pure"] == pytest.approx(1.297688, rel=1e-4)
    assert inv["state0_phase_res_pure"] <= 1.0e-6

    fixed = inv["fixed_H_reequilibration"]
    assert abs(fixed["diff_rf2_pct"]) <= 5.0
    assert fixed["d_max"] < 0.60
    assert fixed["res_u_kN"] <= 1.0e-4

def test_scientific_governance_verdicts():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    concl = data["scientific_conclusions"]
    assert concl["transfer_gate_classification"] == "PROVISIONALLY_QUALIFIED_INTERPOLATION_ONLY"
    assert concl["gate_c1_1_status"] == "PROVISIONALLY_QUALIFIED_INTERPOLATION_ONLY"
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert concl["forward_increment_decision"] == "BLOCKED_PENDING_INCREMENTAL_STABILIZATION"
