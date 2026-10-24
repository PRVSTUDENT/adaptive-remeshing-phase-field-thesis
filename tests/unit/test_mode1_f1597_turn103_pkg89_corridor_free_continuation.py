#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn103_pkg89_corridor_free_continuation.py
Unit tests verifying the Turn 103 Package 89 Frame 88 corridor-free continuation audit,
variational-inequality acceptance gates, and physical re-equilibration.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn103_pkg89_corridor_free_continuation_audit.json"

def test_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"

def test_checkpoint_initial_state():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    ckpt = data["checkpoint"]
    assert ckpt["u_checkpoint_mm"] == pytest.approx(0.00196510735, rel=1e-6)
    assert ckpt["initial_rf2_N"] == pytest.approx(189.5358, rel=1e-3)
    assert ckpt["initial_e_frac_mJ"] == pytest.approx(0.052266, rel=1e-3)
    # Check that initial phase residual is on the order of 1e-6 or lower
    assert ckpt["initial_phase_res_max"] < 1.0e-5

def test_all_predeclared_gates():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    gates = data["gates"]
    assert gates["gate1_phase_equilibrium"]["pass"] is True
    assert gates["gate2_mechanical_equilibrium"]["pass"] is True
    assert gates["gate3_kkt_complementarity"]["pass"] is True
    assert gates["gate4_damage_healing"]["pass"] is True
    assert gates["gate5_damage_overshoot"]["pass"] is True
    assert gates["gate6_history_monotonicity"]["pass"] is True
    assert gates["gate7_coupled_iterations"]["pass"] is True

def test_step_convergence_and_metrics():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    stepA = data["stepA_reequilibration"]
    stepB = data["stepB_continuation"]
    concl = data["scientific_conclusions"]
    assert stepA["converged"] is True
    assert stepB["converged"] is True
    assert concl["all_predeclared_gates_pass"] is True
    assert concl["wake_tearing_absent_at_frame88"] is True
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
