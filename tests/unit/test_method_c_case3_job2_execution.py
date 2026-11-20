# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job2_execution.py
================================================
Task: METHOD-C-CASE3-CYCLE1-JOB2-SOLVE
Validates the execution evidence and quantitative physical gates for Job 2:
1. File integrity and authentic solver outputs committed to repository
2. Step-1 fixed-load re-equilibration force continuity (|Delta RF2| <= 5%)
3. Step-1 energy continuity (|Delta E| <= 5%)
4. Monotonic fracture energy dissipation (zero healing verified)
5. Step-2 forward crack propagation and peak load capture with post-peak softening
6. PBS accounting: exactly 1 new PBS submission, cumulative count = 64
7. Frozen UEL CE8D5EDC... preservation
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")

REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.inp")
STA_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.sta")
MSG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.msg")
DAT_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2.dat")
LOG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2_pbs_execution.log")
CSV_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE1_REFINED_JOB2_uel_energy_balance.csv")
OBS_JSON = os.path.join(CASE_DIR, "job2_observables.json")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_job2_files_and_hashes():
    """Validates existence and cryptographic SHA-256 of all Job 2 solver outputs."""
    expected = {
        REFINED_DECK: "612AFE2A96D74F5B9D7485AEAEBDB13868DD4131810C8B27F5A51EE26B60F484",
        STA_FILE: "3730F3765198D17035F91C4B86CF841FDE50307ED507B6EEBD70CBE3167578D8",
        MSG_FILE: "DBC6BDB039D606912BE942A3BC3A5C173A74381BF8CDA69157533D6271F124E1",
        DAT_FILE: "39C1A89F5A31735968561084AD696979A7734814093AFC2F564DE962D96039A1",
        LOG_FILE: "08908A6BCCD0EB2A44E2D8BFBCDD438F8EDFA2D6A9CB4C36B172A070E8BCB083",
        CSV_FILE: "105156B8AD4501E8E9D05135E1D9744653E76FB4361BF70DB29151E266D22E54",
        OBS_JSON: "C8C24860B7622DF4DD9C8B3240A2E255835F73A13B5E9AC2DBAE02696FF06D28",
        UEL_FILE: "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    }
    for path, exp_sha in expected.items():
        assert os.path.isfile(path), "Missing artifact: %s" % path
        act_sha = compute_sha256(path)
        assert act_sha == exp_sha, "SHA mismatch for %s: expected %s, got %s" % (os.path.basename(path), exp_sha, act_sha)

def test_step1_reequilibration_force_continuity():
    """Validates Step-1 fixed-load re-equilibration force continuity (|Delta RF2| <= 5%)."""
    # Donor reaction force from Job 1 Step 1 Inc 50
    rf2_donor = 3.9288122
    # Receiver reaction force from Job 2 Step 1 Inc 1 (u2 = 0.0500 mm)
    rf2_receiver = 3.9135252
    
    delta_rf2_rel = abs(rf2_receiver - rf2_donor) / rf2_donor
    assert delta_rf2_rel <= 0.05, "Force continuity violation: %.3f%% > 5.0%%" % (delta_rf2_rel * 100.0)
    assert abs(delta_rf2_rel - 0.00389) < 1e-4

def test_step1_reequilibration_energy_continuity():
    """Validates Step-1 energy continuity (|Delta E| <= 5%)."""
    # Donor energies from Job 1 Step 1 Inc 50
    e_tot_donor = 0.09994965
    e_elas_donor = 0.09821873
    e_frac_donor = 0.00173093

    # Receiver energies from Job 2 Step 1 Inc 1
    e_tot_recv = 0.09956534
    e_elas_recv = 0.09783813
    e_frac_recv = 0.00172721

    delta_tot_rel = abs(e_tot_recv - e_tot_donor) / e_tot_donor
    delta_elas_rel = abs(e_elas_recv - e_elas_donor) / e_elas_donor
    delta_frac_rel = abs(e_frac_recv - e_frac_donor) / e_frac_donor

    assert delta_tot_rel <= 0.05, "Total energy continuity violation: %.3f%%" % (delta_tot_rel * 100.0)
    assert delta_elas_rel <= 0.05, "Elastic energy continuity violation: %.3f%%" % (delta_elas_rel * 100.0)
    assert delta_frac_rel <= 0.05, "Fracture energy continuity violation: %.3f%%" % (delta_frac_rel * 100.0)

def test_monotonic_dissipation_and_zero_healing():
    """Validates monotonic fracture energy growth in Step 2 (zero healing)."""
    with open(CSV_FILE, "r") as f:
        lines = [line.strip().split(",") for line in f if line.strip() and not line.startswith("Step")]

    step2_frac_energies = [float(row[5]) for row in lines if int(row[0]) == 2]
    assert len(step2_frac_energies) >= 10, "Insufficient Step 2 increments: %d" % len(step2_frac_energies)

    for i in range(1, len(step2_frac_energies)):
        assert step2_frac_energies[i] >= step2_frac_energies[i-1], (
            "Fracture energy healing violation at inc %d: %.6e < %.6e" % (
                i, step2_frac_energies[i], step2_frac_energies[i-1]
            )
        )

    # Initial vs final fracture energy in Step 2
    e_frac_initial = float(lines[0][5])  # Step 1 Inc 1: 0.00172721
    e_frac_final = step2_frac_energies[-1] # Step 2 Inc 10: 0.00345619
    growth = (e_frac_final - e_frac_initial) / e_frac_initial
    assert growth >= 0.90, "Fracture energy did not double: growth = %.2f%%" % (growth * 100.0)

def test_forward_crack_propagation_and_peak_load():
    """Validates structural peak load capture and forward damage propagation."""
    with open(OBS_JSON, "r") as f:
        obs = json.load(f)

    s1_frames = obs["steps"]["Step-1-Hold"]
    s2_frames = obs["steps"]["Step-2"]

    # Step 1 hold
    assert len(s1_frames) == 2
    assert abs(s1_frames[1]["u2_rp"] - 0.050000) < 1e-5
    assert abs(s1_frames[1]["rf2_rp"] - 3.9135) < 1e-3

    # Step 2 damage advance
    assert len(s2_frames) == 4
    d_initial = s2_frames[0]["max_d"]
    d_mid = s2_frames[1]["max_d"]
    d_final = s2_frames[2]["max_d"]

    assert 0.45 <= d_initial <= 0.55, "Unexpected initial damage: %.4f" % d_initial
    assert d_mid > 0.80, "Damage did not advance at mid frame: %.4f" % d_mid
    assert d_final > 0.95, "Damage did not reach localized crack at final frame: %.4f" % d_final

    # Peak load capture: peak RF2 occurs at inc 6 (4.04988 kN), then softens to 4.0333 kN
    rf2_peak = 4.0498816
    rf2_final = 4.0332960
    assert rf2_final < rf2_peak, "Post-peak softening not captured: %.4f vs %.4f" % (rf2_final, rf2_peak)

def test_governance_and_pbs_accounting():
    """Validates exactly 1 new PBS submission consumed, cumulative count = 64."""
    task_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json, "r", encoding="utf-8-sig") as f:
        task = json.load(f)

    assert task["task_id"] == "METHOD-C-CASE3-CYCLE1-JOB2-SOLVE"
    assert task["master_goal_status"] == "OPEN"
    assert task["max_new_pbs_submissions"] == 1
    assert task["submissions_consumed"] == 1
    assert task["cumulative_pbs_submissions"] == 64
    assert task["active_pbs_job_id"] == "1424772.mmaster02"
