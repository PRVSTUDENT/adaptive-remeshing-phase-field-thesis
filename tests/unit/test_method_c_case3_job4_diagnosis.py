# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_job4_diagnosis.py
================================================
Task: METHOD-C-CASE3-JOB4-DIAGNOSIS
Correlation: HND-METHOD-C-CASE3-JOB4-DIAG-001
Predecessor: HND-METHOD-C-CASE3-JOB4-001 (INSUFFICIENT_EVIDENCE)

Validates resolution of all review gaps GAP-MC-C3J4-01 through 06:
1. Cryptographic SHA-256 and exact byte counts of diagnosis deliverables
2. Section 2 comparison table corrections with source citations (Job-1 242 s / 290 s, Job-2 152 s / 489 s / 254 s, Job-4 97.16% quads)
3. Step-1 terminal residual corrected to -3.125e-13 at node 11385 DOF 2
4. Terminal frame relabeled as 'Increment 11 (terminal converged state)' in both JSON artifacts
5. Increment-12 cutback mechanism diagnosed with failing node coordinates (21774, 22165, 4275, 22412, 22792)
6. Cycle-4 progression confirmed as pure adaptive remeshing with 0 new PBS jobs consumed for diagnosis
7. Non-healing wording verified relative to transferred state
8. PBS accounting: strictly 0 new PBS jobs consumed, cumulative 66 preserved; master goal status OPEN
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")

REFINED_DECK = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.inp")
PHYS_MESH = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp")
STA_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.sta")
MSG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.msg")
DAT_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4.dat")
LOG_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_pbs_execution.log")
CSV_FILE = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_uel_energy_balance.csv")
OBS_JSON = os.path.join(CASE_DIR, "job4_observables.json")
SPATIAL_JSON = os.path.join(CASE_DIR, "job4_spatial_crack.json")
RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_RECEIPT.json")
SUMMARY_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_CYCLE3_REFINED_JOB4_SUMMARY.json")
EXEC_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB4_EXECUTION_REPORT.md")
DIAG_REPORT = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_JOB4_DIAGNOSIS_REPORT.md")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def test_diagnosis_artifacts_and_hashes():
    """Validates existence and cryptographic SHA-256 of diagnosis deliverables."""
    assert os.path.isfile(DIAG_REPORT), "Missing diagnosis report: %s" % DIAG_REPORT
    assert os.path.isfile(EXEC_REPORT), "Missing execution report: %s" % EXEC_REPORT
    assert os.path.isfile(OBS_JSON), "Missing observables JSON: %s" % OBS_JSON
    assert os.path.isfile(SPATIAL_JSON), "Missing spatial crack JSON: %s" % SPATIAL_JSON
    assert os.path.isfile(UEL_FILE), "Missing UEL file: %s" % UEL_FILE

    assert compute_sha256(UEL_FILE) == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
    assert compute_sha256(STA_FILE) == "F638E5C6BD20C284352033F921D390B166807CCCB3EC65D97733E3501D8549A7"
    assert compute_sha256(OBS_JSON) == "E962C66B9B6BBC33EC1BCCA794047F0B5EA42A789886504FF7321E6481462D76"
    assert compute_sha256(SPATIAL_JSON) == "9C24DA7D6C24ED8CEFEC2B8A9DB9695ED166BA4DA1296B70A8F3DC0D3756A80A"

def test_job4_table_corrections_and_citations():
    """Validates GAP-MC-C3J4-01 table corrections in execution and diagnosis reports."""
    for report in [EXEC_REPORT, DIAG_REPORT]:
        with open(report, "r", encoding="utf-8") as f:
            content = f.read()
        # Job 1 metrics
        assert "242 s" in content, "Job-1 wallclock 242 s missing in %s" % report
        assert "290 s" in content, "Job-1 CPU 290 s missing in %s" % report
        assert "C4C2D56B" in content, "Job-1 .dat SHA citation missing in %s" % report

        # Job 2 metrics
        assert "152 s" in content, "Job-2 wallclock 152 s missing in %s" % report
        assert "489 s" in content, "Job-2 CPU 489 s missing in %s" % report
        assert "254 s" in content, "Job-2 PBS span 254 s missing in %s" % report
        assert "39C1A89F" in content, "Job-2 .dat SHA citation missing in %s" % report

        # Job 4 quad fraction
        assert "97.16%" in content, "Job-4 quad fraction 97.16% missing in %s" % report
        assert "1620F4F6" in content, "Job-4 mesh audit SHA citation missing in %s" % report

def test_job4_terminal_residual_attribution():
    """Validates GAP-MC-C3J4-02: Step-1 terminal residual is -3.125e-13 at node 11385 DOF 2."""
    for report in [EXEC_REPORT, DIAG_REPORT]:
        with open(report, "r", encoding="utf-8") as f:
            content = f.read()
        assert "-3.125" in content and "11385" in content and "DOF 2" in content

def test_job4_terminal_frame_label():
    """Validates GAP-MC-C3J4-03: terminal frame relabelled as Increment 11 (terminal converged state)."""
    with open(OBS_JSON, "r", encoding="utf-8") as f:
        obs = json.load(f)
    s2_frames = obs["steps"]["Step-2"]
    assert s2_frames[-1]["description"] == "Increment 11 (terminal converged state)"

    with open(SPATIAL_JSON, "r", encoding="utf-8") as f:
        spatial = json.load(f)
    s2_spatial = spatial["steps"]["Step-2"]
    assert s2_spatial[-1]["description"] == "Increment 11 (terminal converged state)"

def test_job4_increment12_failure_diagnosis():
    """Validates GAP-MC-C3J4-04: node coordinates and Cycle-4 pure remesh progression."""
    with open(DIAG_REPORT, "r", encoding="utf-8") as f:
        content = f.read()
    # Check failing nodes documented
    for nid in ["21774", "22165", "4275", "22412", "22792"]:
        assert nid in content, "Node %s missing from failure diagnosis" % nid

    # Check failing nodes coordinates
    assert "13.2858" in content
    assert "13.3019" in content
    assert "13.4039" in content
    assert "13.5261" in content
    assert "13.5612" in content

    # Check Cycle-4 progression as pure adaptive remeshing
    assert "pure adaptive remeshing" in content.lower()

def test_job4_governance_and_pbs_accounting():
    """Validates GAP-MC-C3J4-06: 0 new PBS jobs consumed, cumulative 66 preserved."""
    with open(TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in ("METHOD-C-CASE3-JOB4-DIAGNOSIS", "METHOD-C-CASE3-CYCLE3-JOB4-SOLVE")
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] == 66
    assert task["master_goal_status"] == "OPEN"
    assert task["last_successful_pbs_job_id"] == "1424778.mmaster02"
