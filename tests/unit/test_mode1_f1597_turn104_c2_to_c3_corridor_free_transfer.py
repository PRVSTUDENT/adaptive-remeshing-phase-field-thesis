#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn104_c2_to_c3_corridor_free_transfer.py
Unit tests verifying Turn 104 Candidate C2 -> Candidate C3 corridor-free nonmatching FE state transfer,
evaluating State 0 (immediate post-projection), State 1 (bound-constrained re-equilibration),
and all 8 transfer acceptance gates.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
AUDIT_JSON = REPO_ROOT / "results/validation/mode1_f1597/turn104_c2_to_c3_corridor_free_transfer_audit.json"

def test_transfer_audit_json_exists():
    assert AUDIT_JSON.exists(), f"Audit file not found: {AUDIT_JSON}"

def test_donor_and_recipient_metadata():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    donor = data["donor_c2"]
    recip = data["recipient_c3"]
    assert donor["checkpoint"] == "Package 89 Frame 88"
    assert donor["u_prescribed_mm"] == pytest.approx(0.00196510735, rel=1e-6)
    assert donor["elements"] == 2300
    assert donor["nodes"] == 2413
    assert recip["elements"] == 2650
    assert recip["nodes"] == 2769

def test_state0_projection_continuity():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    s0 = data["state0_post_projection"]
    # Gate 1: Force continuity <= 5%
    assert abs(s0["diff_rf2_pct"]) <= 5.0
    # Gate 2: Fracture energy continuity <= 2%
    assert abs(s0["diff_ef_pct"]) <= 2.0
    assert s0["d_max"] <= 1.0
    assert s0["d_max"] >= 0.0

def test_state1_reequilibration_and_all_gates():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    s1 = data["state1_reequilibrated"]
    assert s1["kkt_violations"] == 0
    assert s1["min_healing"] >= -1.0e-12
    assert s1["max_d"] <= 1.0
    assert s1["iterations"] <= 25

    gates = data["gates"]
    assert gates["gate1_force_continuity"]["state0_pass"] is True
    assert gates["gate2_fracture_energy_continuity"]["state0_pass"] is True
    assert gates["gate3_phase_field_equilibrium"]["pass"] is True
    assert gates["gate4_mechanical_equilibrium"]["pass"] is True
    assert gates["gate5_kkt_complementarity"]["pass"] is True
    assert gates["gate6_damage_healing"]["pass"] is True
    assert gates["gate7_damage_overshoot"]["pass"] is True
    assert gates["gate8_coupled_iterations"]["pass"] is True

def test_scientific_governance_conclusions():
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    concl = data["scientific_conclusions"]
    assert concl["transfer_qualification_status"] == "QUALIFIED"
    assert concl["gate_c1_1_status"] == "QUALIFIED_AT_FRAME88"
    assert concl["gate_c1_2_status"] == "NOT_QUALIFIED"
    assert concl["package94_status"] == "BENCHMARK-REPRODUCTION-ONLY"
    assert concl["hpc_decision"] == "C2_TO_C3_TRANSFER_BENCHMARK_PROVEN"
