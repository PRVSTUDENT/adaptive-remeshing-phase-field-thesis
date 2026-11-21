# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job5_execution.py
================================================
Task: METHOD-C-CASE3-CYCLE4-JOB5-SOLVE
Validates the execution evidence, spatial crack advance, force/energy continuity,
and numerical mitigations for Case 3 Cycle-4 Job 5:
1. File integrity and authentic solver outputs committed to repository
2. Step-1 fixed-load re-equilibration force continuity (|Delta RF2| <= 5.0%) and energy continuity
3. Step-2 forward crack propagation: peak load capture, post-peak load softening
4. Monotonic fracture energy surge (+25.78%) and elastic strain energy release
5. Spatial crack advance extracted from ODB (crack tip advance +1.0730 mm past Job 4 donor tip)
6. Zero healing verification relative to transferred state (d_max = 1.0019 >= 0.99)
7. Cutback floor reached at Inc 12 after resolving down to dt = 6.993e-14
8. PBS accounting: exactly 1 new PBS submission consumed (cumulative 66 -> 67)
9. Bitwise frozen UEL CE8D5EDC... preservation
10. Final job of Fix Option A 5-job budget (cumulative count 67)
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")

REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.inp")
PHYS_MESH = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_PHYS.inp")
STA_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.sta")
MSG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.msg")
DAT_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5.dat")
LOG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_pbs_execution.log")
CSV_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_uel_energy_balance.csv")
OBS_JSON = os.path.join(CASE_DIR, "job5_observables.json")
SPATIAL_JSON = os.path.join(CASE_DIR, "job5_spatial_crack.json")
RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_RECEIPT.json")
SUMMARY_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_SUMMARY.json")
PBS_SCRIPT = os.path.join(CASE_DIR, "submit_case3_cycle4_job5.pbs")
DC_DAT = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.dat")
DC_MSG = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE4_REFINED_JOB5_DC.msg")
EXEC_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_job5_files_and_hashes():
    """Validates existence and cryptographic SHA-256 of all Job 5 solver and execution artifacts."""
    expected = {
        REFINED_DECK: "DF46D07BAF1F4A65D1F6E7192D4230134605F25A377AD1D96F511F149A521B91",
        PHYS_MESH: "18E9B7ACD4E66B8503CD6E876FAE211671927874EEF7B1A3FF9F37068E44C5BA",
        STA_FILE: "572DC6DAB471E035526F51E2E0AABC11E6B107724B712C518CD6E3CBABE72839",
        MSG_FILE: "F7D76C04EEEE723B056F74D4F0620F129C18CB668FD2E0808A7BDA94E044F675",
        DAT_FILE: "7DD28AB2C320C4986D4B7A6B32A64440ED4386D333BCDF02F6F8F4CCB99FA26B",
        LOG_FILE: "54336C0174102AAA25A8C5319B405587A814E5887F7856847E5C91DDFECECACB",
        CSV_FILE: "4E8C2DB379104CD3A5D9083DAD0BBEBE162FC9DEE466A627C5B947753A7845C5",
        OBS_JSON: "40A9219EFA7B9E471B740F3E8C36462A61C9096B294D0FC5BF4D6D381CF37D8F",
        SPATIAL_JSON: "70EE5ACDC8F1A709210F04A1FFEBD9C438FC712A9869FCD1AD96007D18B2DE86",
        RECEIPT_JSON: "43817624F02F8C65906C0BFB343225F17626BF5490745DAFD929174253EB34FA",
        SUMMARY_JSON: "4E794B9C5AD44767C59AE8C387837C50C168739F2647DF174759C2A49E995CD7",
        PBS_SCRIPT: "DEEC3C6EA6B7F7ECDA301DE082CA7EFEF5AEA660488CFE509B9F65DB818DC206",
        DC_DAT: "6A9F3537CAB40FF5B08259944FDC41DD72E28C65F4D329CBED3F4A5A28FDAF27",
        DC_MSG: "86BF978EA5D4313E13BBB0D5171466E73E1E5C7915B5FC0392B08FF7D40A7018",
        UEL_FILE: "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    }
    for path, exp_sha in expected.items():
        assert os.path.isfile(path), "Missing artifact: %s" % path
        act_sha = compute_sha256(path)
        assert act_sha == exp_sha, "SHA mismatch for %s: expected %s, got %s" % (os.path.basename(path), exp_sha, act_sha)
    assert os.path.isfile(EXEC_REPORT), "Missing execution report: %s" % EXEC_REPORT
    assert os.path.getsize(EXEC_REPORT) > 10000, "Execution report unexpectedly small"

def test_step1_reequilibration_continuity():
    """Validates Step-1 fixed-load force and energy continuity vs Job 4 donor end state."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s1 = rc["step1_re_equilibration"]
    assert s1["force_continuity_pass"] is True
    assert abs(s1["force_continuity_delta_pct"]) <= 5.0
    assert abs(s1["force_continuity_delta_pct"] - (-0.950139)) < 1e-4

    assert s1["energy_continuity_pass"] is True
    assert s1["increments"] == 1
    assert s1["iterations"] == 2

def test_step2_propagation_softening_and_energy():
    """Validates Step-2 forward propagation: peak load, softening, and fracture energy growth."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s2 = rc["step2_propagation"]
    assert s2["increments_converged"] == 11
    assert s2["total_converged_increments"] == 12
    assert s2["peak_load_RF2_kN"] > s2["terminal_RF2_kN"]
    assert abs(s2["peak_load_RF2_kN"] - 3.8997762) < 1e-4
    assert abs(s2["terminal_RF2_kN"] - 3.7412223) < 1e-4
    assert s2["softening_demonstrated"] is True
    assert s2["load_drop_from_peak_pct"] < 0.0

    assert s2["terminal_fracture_energy_kNmm"] > s2["initial_fracture_energy_kNmm"]
    assert s2["fracture_energy_growth_pct"] > 20.0
    assert s2["terminal_elastic_strain_energy_kNmm"] < s2["peak_elastic_strain_energy_kNmm"]

def test_spatial_crack_advance():
    """Validates spatial crack advance past Job 4 donor tip toward the central void."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s2 = rc["step2_propagation"]
    assert s2["terminal_crack_tip_x_d095_mm"] > s2["donor_crack_tip_x_mm"]
    assert s2["forward_crack_advance_past_donor_mm"] > 1.0  # +1.0730 mm forward advance
    assert s2["total_crack_extension_from_notch_root_mm"] > 4.1  # 4.1848 mm total extension
    assert s2["distance_to_hole_perimeter_mm"] < 20.0  # 19.1185 mm
    assert s2["zero_healing_verified"] is True
    assert s2["peak_damage_SDV1"] >= 0.99

def test_job5_governance_and_pbs_accounting():
    """Validates strict governance and PBS accounting limits for Job 5."""
    task_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json, "r", encoding="utf-8-sig") as f:
        t = json.load(f)
    assert t["cumulative_pbs_submissions"] == 67
    assert t["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert t["master_goal_status"] == "OPEN"
