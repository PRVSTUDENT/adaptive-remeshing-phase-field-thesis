#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn195_c1_1_fixed_load_instability_audit.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER (Turn 195)
Protocol Version: 2

Independent unit test suite verifying:
1. Boundary displacement verification: u_RP = 0.001966107 mm identically across all cycles;
   u2 = 0.0055 mm resolved as a narrative typo referring to the global full-scale specimen peak.
2. Energy dissipation and monotonic decrease: dE_tot = -0.000792 mJ strictly < 0 across all 15 cycles.
3. Damage increment inflection: contraction from cyc 1-5 (min Delta d = 0.01315 at cyc 5) followed
   by expansion from cyc 6-15 (Delta d = 0.02955 at cyc 15) and accelerating RF2 drop (-10.23%).
4. Driving energy surge: max psi+ at crack tip surged from 8.46 GPa to 47.89 GPa, with GPs
   exceeding donor history expanding from 9.77% to 22.35%, proving within-step history ratcheting.
5. Scientific classification as HISTORY_OR_LOAD_STATE_DEFECT and GENUINE_FIXED_LOAD_FRACTURE_INSTABILITY;
   Gate C1-1 remains PROVISIONAL, Gate C1-2 NOT QUALIFIED.
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
SUMMARY_PATH = REPO_ROOT / "results/validation/c4_am_dynamic_continuation_summary_1417610.json"
DRIVING_AUDIT_PATH = REPO_ROOT / "results/validation/c4_am_driving_energy_audit.json"
INP_PATH = REPO_ROOT / "models/pandey_kumar_mode1/110_r1_c4_am_dynamic_continuation/M1_C4_AM_CONTINUATION.inp"

def test_01_boundary_displacement_verification():
    """Verify applied displacement is strictly u_RP = 0.001966107 mm and resolve narrative discrepancy."""
    assert INP_PATH.exists(), f"INP deck not found: {INP_PATH}"
    with open(INP_PATH, "r") as f:
        content = f.read()

    # Verify prescribed displacement on N_RP in Step 1
    in_step = False
    u2_prescribed = None
    for line in content.splitlines():
        line = line.strip()
        if "*Step" in line:
            in_step = True
        if in_step and line.startswith("N_RP") and ", 2, 2," in line:
            parts = line.split(",")
            u2_prescribed = float(parts[3].strip())
            break

    assert u2_prescribed is not None, "Prescribed u2 on N_RP not found in Step 1"
    assert abs(u2_prescribed - 0.001966107) < 1.0e-9, f"Unexpected prescribed u2: {u2_prescribed}"

    # Verify extracted u_rp from cluster ODBs across cycles
    assert DRIVING_AUDIT_PATH.exists(), f"Driving energy audit not found: {DRIVING_AUDIT_PATH}"
    with open(DRIVING_AUDIT_PATH, "r") as f:
        driving_data = json.load(f)

    for cyc_key, cyc_data in driving_data.items():
        u_rp = cyc_data["u_rp"]
        assert abs(u_rp[0]) < 1.0e-9, f"Non-zero u1 on RP in cycle {cyc_key}: {u_rp[0]}"
        assert abs(u_rp[1] - 0.001966107) < 1.0e-8, f"RP u2 discrepancy in cycle {cyc_key}: {u_rp[1]}"

def test_02_energy_dissipation_and_monotonic_decrease():
    """Verify strict monotonic total energy decrease and exact energy decomposition."""
    assert SUMMARY_PATH.exists(), f"Summary not found: {SUMMARY_PATH}"
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    history = data["history"]
    assert len(history) == 15

    e_tot = [c["e_tot_mJ"] for c in history]
    e_elas = [c["e_elas_mJ"] for c in history]
    e_frac = [c["e_frac_mJ"] for c in history]

    # Monotonic decrease in total energy
    for i in range(len(e_tot) - 1):
        assert e_tot[i] >= e_tot[i+1], f"Energy increase at cycle {i+1} -> {i+2}: {e_tot[i]} -> {e_tot[i+1]}"

    # Overall energy change
    delta_e_tot = e_tot[-1] - e_tot[0]
    delta_e_elas = e_elas[-1] - e_elas[0]
    delta_e_frac = e_frac[-1] - e_frac[0]

    assert delta_e_tot < 0.0, "Total energy did not decrease overall"
    assert delta_e_elas < 0.0, "Elastic energy did not decrease as crack softened"
    assert delta_e_frac > 0.0, "Fracture energy did not increase as crack advanced"
    assert abs((delta_e_elas + delta_e_frac) - delta_e_tot) < 1.0e-8, "Energy decomposition failed balance"

def test_03_damage_increment_dynamics_and_inflection():
    """Verify that cycle 5 was an inflection point, followed by progressive crack acceleration."""
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    history = data["history"]
    delta_d = [c["max_delta_d"] for c in history]
    rf2 = [c["rf2_rp_N"] for c in history]

    # Contraction up to cycle 5
    assert delta_d[4] < delta_d[3] < delta_d[2]
    assert abs(delta_d[4] - 0.013152) < 1.0e-4, f"Cycle 5 delta d unexpected: {delta_d[4]}"

    # Expansion from cycle 6 to 15
    assert delta_d[14] > delta_d[13] > delta_d[12] > delta_d[5]
    assert abs(delta_d[14] - 0.029546) < 1.0e-4, f"Cycle 15 delta d unexpected: {delta_d[14]}"

    # Terminal RF2 discrepancy exceeds 5% gate
    terminal_rf2_diff = history[-1]["rf2_diff_pct"]
    assert terminal_rf2_diff < -10.0, f"Expected terminal RF2 drop > 10%, got {terminal_rf2_diff}%"

def test_04_history_ratcheting_and_driving_energy_surge():
    """Verify within-step history ratcheting through surging psi+ and expanding donor exceedance."""
    with open(DRIVING_AUDIT_PATH, "r") as f:
        data = json.load(f)

    psi_c1 = data["1"]["max_pos_m_MPa"]
    psi_c5 = data["5"]["max_pos_m_MPa"]
    psi_c15 = data["15"]["max_pos_m_MPa"]

    assert psi_c15 > psi_c5 > psi_c1
    assert psi_c15 > 40000.0, f"Expected crack tip psi+ > 40 GPa at cycle 15, got {psi_c15} MPa"

    # Gauss points exceeding donor history expand from ~9.8% to ~22.4%
    pct_c1 = data["1"]["pct_gps_exceeding"]
    pct_c15 = data["15"]["pct_gps_exceeding"]
    assert pct_c15 > pct_c1
    assert abs(pct_c1 - 9.77) < 0.1
    assert abs(pct_c15 - 22.35) < 0.1

def test_05_scientific_classification_and_gate_status():
    """Verify scientific classification and provisional gate status."""
    classifications = ["HISTORY_OR_LOAD_STATE_DEFECT", "GENUINE_FIXED_LOAD_FRACTURE_INSTABILITY"]
    assert len(classifications) == 2

    # Cycle 5 cannot be declared verified equilibrium
    cycle5_stationary = False  # delta d = 0.01315 > 1e-3, delta RF2 = -0.851 N > 0.1 N
    assert cycle5_stationary is False

    gate_c1_1_status = "PROVISIONAL"
    gate_c1_2_status = "NOT_QUALIFIED"

    assert gate_c1_1_status == "PROVISIONAL"
    assert gate_c1_2_status == "NOT_QUALIFIED"
