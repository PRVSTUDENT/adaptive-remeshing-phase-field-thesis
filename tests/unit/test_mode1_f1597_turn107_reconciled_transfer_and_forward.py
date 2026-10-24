#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn107_reconciled_transfer_and_forward.py
Unit tests verifying Turn 107 three-way transfer reconciliation,
matched-equilibrated state qualification, and authentic forward displacement continuation on C3.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn107_c3_reconciled_transfer_and_forward_audit.json"

def test_turn107_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"

def test_comparison_A_projection_accuracy():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    compA = data["comparison_A_projection_accuracy"]
    assert abs(compA["diff_rf2_pct"]) <= 0.05
    assert abs(compA["diff_ef_pct"]) <= 0.05
    assert compA["res_d_s0"] <= 1.0e-6
    assert compA["res_u_s0"] <= 1.0e-4
    assert compA["verdict"] == "PASS"

def test_comparison_B_matched_equilibrated_consistency():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    compB = data["comparison_B_matched_equilibrated_consistency"]
    assert abs(compB["diff_rf2_pct"]) <= 5.0
    assert abs(compB["diff_ef_pct"]) <= 2.0
    assert abs(compB["c3_d_max"] - compB["c2_d_max"]) <= 0.02
    assert compB["res_d_max_kN_mm"] <= 1.0e-6
    assert compB["res_u_max_kN"] <= 1.0e-4
    assert compB["kkt_violations"] == 0
    assert compB["converged"] is True
    assert compB["iterations"] <= 25
    assert compB["verdict"] == "QUALIFIED"

def test_comparison_C_relaxation_dynamics():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    compC = data["comparison_C_relaxation_dynamics"]
    assert abs(compC["difference_rf2_relaxation_pct"]) <= 1.0
    assert abs(compC["difference_ef_evolution_pct"]) <= 1.5

def test_first_forward_increment_continuation():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    fwd = data["forward_increment"]
    assert fwd["attempted"] is True
    assert fwd["converged"] is True
    assert fwd["iterations"] <= 25
    assert fwd["u_target_mm"] == pytest.approx(0.00197010735, rel=1e-6)
    # Monotonic softening: delta RF2 must be negative
    assert fwd["delta_rf2_N"] < 0.0
    # Fracture dissipation: delta E_frac must be positive
    assert fwd["delta_ef_mJ"] > 0.0
    assert fwd["res_d_max_kN_mm"] <= 1.0e-6
    assert fwd["res_u_max_kN"] <= 1.0e-4
    assert fwd["kkt_violations"] == 0
    assert fwd["min_healing"] >= -1.0e-12

def test_scientific_governance_conclusions():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    concl = data["scientific_conclusions"]
    assert concl["gate_c1_1_status"] == "QUALIFIED_AT_FRAME88"
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert concl["continuation_passed"] is True
