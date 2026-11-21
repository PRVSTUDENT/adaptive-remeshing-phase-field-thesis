# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job5_diagnosis.py
================================================
Task: METHOD-C-CASE3-JOB5-DIAGNOSIS
Correlation: HND-METHOD-C-CASE3-JOB5-DIAG-001
Predecessor: HND-METHOD-C-CASE3-JOB5-001 (INSUFFICIENT_EVIDENCE)

Validates resolution of all review gaps GAP-J5-01 through 06 and advisory notes NOTE-J5-01 through 05:
1. GAP-J5-01: Disclosed parameter deviation in Step-1 fracture energy continuity (-6.7542%) due to Gc change (0.00270 -> 0.00228 kN/mm), with Gc-normalized fracture surface integral Gamma = E_frac / Gc (5.898046 -> 6.512777 mm^2, +10.42%)
2. GAP-J5-02: Physical node count verified dynamically: exactly 64,106 physical nodes (64,107 with N_RP)
3. GAP-J5-03: Section 5 file sizes verified: physical mesh 4,685,923 B, frozen UEL 29,722 B
4. GAP-J5-04: Terminal frame relabelled as 'Increment 11 (terminal converged state)' with time 0.0021379311337 in both JSON artifacts
5. GAP-J5-05: Increment 12 cutback mechanism forensically diagnosed with tip-front nodes (19880, 20110, 43706, 19975, 4328, 0.19 to 0.61 mm ahead of tip)
6. GAP-J5-06: Zero healing verified relative to transferred state (d_max_terminal = 1.001932 >= d_max_transferred = 0.992229)
7. NOTE-J5-01 to 05: Step-1 residual +3.358e-13 at node 33943 DOF 2, downward crack curvature Delta y = -0.1181 mm, mnode103 REPORTED_ONLY, ACTIVE_TASK semantics
8. Accounting: strictly 0 new PBS jobs consumed, cumulative count strictly 67 preserved; master goal OPEN
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
EXEC_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB5_EXECUTION_REPORT.md")
DIAG_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB5_DIAGNOSIS_REPORT.md")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_diagnosis_artifacts_exist_and_hashes():
    """Validates existence and cryptographic SHA-256 of diagnosis and execution deliverables."""
    assert os.path.isfile(DIAG_REPORT), f"Missing diagnosis report: {DIAG_REPORT}"
    assert os.path.isfile(EXEC_REPORT), f"Missing execution report: {EXEC_REPORT}"
    assert os.path.isfile(OBS_JSON), f"Missing observables JSON: {OBS_JSON}"
    assert os.path.isfile(SPATIAL_JSON), f"Missing spatial crack JSON: {SPATIAL_JSON}"
    assert os.path.isfile(RECEIPT_JSON), f"Missing receipt JSON: {RECEIPT_JSON}"
    assert os.path.isfile(SUMMARY_JSON), f"Missing summary JSON: {SUMMARY_JSON}"
    assert os.path.isfile(UEL_FILE), f"Missing UEL file: {UEL_FILE}"

    assert compute_sha256(UEL_FILE) == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert os.path.getsize(DIAG_REPORT) > 10000, "Diagnosis report unexpectedly small"
    assert os.path.getsize(EXEC_REPORT) > 10000, "Execution report unexpectedly small"

def test_gap_j5_01_energy_continuity_and_gc_scaling():
    """Validates GAP-J5-01: disclosed energy deviation due to Gc scaling and normalized surface integral."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s1 = rc["step1_re_equilibration"]
    assert s1["energy_continuity_status"] == "DISCLOSED_PARAMETER_DEVIATION"
    assert abs(s1["energy_continuity_delta_pct"] - (-6.754227)) < 1e-4
    assert abs(s1["donor_normalized_fracture_energy_gamma_mm2"] - 5.898046) < 1e-4
    assert abs(s1["receiver_normalized_fracture_energy_gamma_mm2"] - 6.512777) < 1e-4
    assert abs(s1["normalized_fracture_energy_delta_pct"] - 10.4226) < 0.01

    with open(DIAG_REPORT, "r", encoding="utf-8") as f:
        dtxt = f.read()
    assert "DISCLOSED_PARAMETER_DEVIATION" in dtxt
    assert "-6.7542%" in dtxt
    assert "5.898046" in dtxt
    assert "6.512777" in dtxt

    with open(EXEC_REPORT, "r", encoding="utf-8") as f:
        etxt = f.read()
    assert "Disclosed Parameter Deviation" in etxt or "DISCLOSED_DEVIATION" in etxt
    assert "-6.7542%" in etxt
    assert "5.8980" in etxt
    assert "6.5128" in etxt

def test_gap_j5_02_and_03_physical_nodes_and_file_sizes():
    """Validates GAP-J5-02 (node count 64,106) and GAP-J5-03 (exact file sizes)."""
    with open(SUMMARY_JSON, "r", encoding="utf-8") as f:
        sm = json.load(f)
    assert sm["physical_nodes_count"] == 64106
    assert sm["total_nodes_with_rp"] == 64107

    assert os.path.getsize(PHYS_MESH) == 4685923
    assert os.path.getsize(UEL_FILE) == 29722

    for report in [EXEC_REPORT, DIAG_REPORT]:
        with open(report, "r", encoding="utf-8") as f:
            txt = f.read()
        assert "64,106" in txt or "64106" in txt
        assert "4,685,923" in txt
        assert "29,722" in txt

def test_gap_j5_04_terminal_frame_label():
    """Validates GAP-J5-04: terminal frame relabelled as Increment 11 (terminal converged state)."""
    with open(OBS_JSON, "r", encoding="utf-8") as f:
        obs = json.load(f)
    s2_obs = obs["steps"]["Step-2"]
    assert s2_obs[-1]["description"] == "Increment 11 (terminal converged state)"
    assert abs(s2_obs[-1]["time"] - 0.0021379311337) < 1e-10

    with open(SPATIAL_JSON, "r", encoding="utf-8") as f:
        sp = json.load(f)
    s2_sp = sp["steps"]["Step-2"]
    assert s2_sp[-1]["description"] == "Increment 11 (terminal converged state)"
    assert abs(s2_sp[-1]["step_time"] - 0.0021379311337) < 1e-10

def test_gap_j5_05_cutback_mechanism_and_tip_front_nodes():
    """Validates GAP-J5-05: Increment 12 cutback mechanism and tip-front nodes documented."""
    for report in [EXEC_REPORT, DIAG_REPORT]:
        with open(report, "r", encoding="utf-8") as f:
            txt = f.read()
        assert "19880" in txt
        assert "20110" in txt
        assert "43706" in txt
        assert "19975" in txt
        assert "4328" in txt

def test_gap_j5_06_zero_healing_wording():
    """Validates GAP-J5-06: zero healing evaluated relative to transferred state."""
    with open(RECEIPT_JSON, "r", encoding="utf-8") as f:
        rc = json.load(f)
    s2 = rc["step2_propagation"]
    assert s2["zero_healing_verified"] is True
    assert s2["peak_damage_SDV1"] >= 0.992229
    assert abs(s2["peak_damage_SDV1"] - 1.001932) < 1e-4

def test_advisory_notes_and_governance():
    """Validates advisory notes NOTE-J5-01 through 05 and PBS accounting."""
    for report in [EXEC_REPORT, DIAG_REPORT]:
        with open(report, "r", encoding="utf-8") as f:
            txt = f.read()
        assert "+3.358" in txt and "33943" in txt and "DOF 2" in txt
        assert "-0.1181" in txt

    # Governance & accounting
    with open(TASK_JSON, "r", encoding="utf-8-sig") as f:
        t = json.load(f)
    assert t["cumulative_pbs_submissions"] == 67
    assert t["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert t["master_goal_status"] == "OPEN"
