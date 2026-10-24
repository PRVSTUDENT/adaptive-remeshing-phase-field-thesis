#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn106_c3_continuation.py
Unit tests verifying Turn 106 Candidate C2 -> Candidate C3 state transfer,
corrected coupled re-equilibration with evolving history, same-load acceptance gates,
and forward displacement continuation.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn106_c3_coupled_continuation_audit.json"

def test_turn106_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"

def test_donor_and_state0_parity():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    donor = data["donor_c2_benchmark"]
    s0 = data["recipient_c3_state0"]

    assert donor["u_mm"] == pytest.approx(0.00196510735, rel=1e-6)
    assert donor["rf2_N"] == pytest.approx(189.5358, rel=1e-3)
    assert donor["e_frac_mJ"] == pytest.approx(0.052266, rel=1e-3)

    assert abs(s0["diff_rf2_pct"]) <= 0.05
    assert abs(s0["diff_ef_pct"]) <= 0.05
    assert s0["res_d_max_kN_mm"] <= 1.0e-6
    assert s0["res_u_max_kN"] <= 1.0e-4

def test_coupled_state1_gates():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    s1 = data["recipient_c3_state1_coupled"]
    gates = data["gates"]

    assert gates["gate4_mechanical_equilibrium"]["pass"] is True
    assert gates["gate5_kkt_complementarity"]["pass"] is True
    assert gates["gate6_damage_healing"]["pass"] is True
    assert gates["gate7_damage_overshoot"]["pass"] is True
    assert s1["min_healing"] >= -1.0e-12
    assert s1["kkt_violations"] == 0

def test_scientific_governance_verdicts():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    concl = data["scientific_conclusions"]
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert "gate_c1_1_status" in concl
