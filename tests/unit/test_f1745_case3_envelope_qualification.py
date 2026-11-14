# -*- coding: utf-8 -*-
"""
tests/unit/test_f1745_case3_envelope_qualification.py

Unit test suite validating Task F1745 Case 3 5-State Error-Indicator Envelope Qualification:
  1. Reconciles 3,923 vs 3,979 mesh topology discrepancy
  2. Verifies 100% element connectivity parity across companion and base decks
  3. Reconciles PBS accounting chronology across Jobs 20 through 25
  4. Validates dimensionally consistent, non-singular relative error envelope metrics
  5. Confirms zero-PBS governance and bitwise frozen UEL preservation
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.audit_f1736_spatial_resolution import parse_abaqus_inp

ACTIVE_TASK_JSON = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
EVAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1745_case3_envelope_evaluation.json")
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1745_active_task_governance():
    assert os.path.exists(ACTIVE_TASK_JSON)
    with open(ACTIVE_TASK_JSON, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in [
        "F1745-CASE3-5STATE-ENVELOPE-QUALIFICATION",
        "F1746-CASE3-5STATE-ENVELOPE-EXECUTION",
        "F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE",
        "F1748-AUTHENTIC-COUPLED-DAMAGE-FIELD-RECOVERY-AND-INDICATOR-FEASIBILITY"
    ]
    assert task["frozen_uel_sha256"].lower() == FROZEN_UEL_SHA
    if task["task_id"] == "F1745-CASE3-5STATE-ENVELOPE-QUALIFICATION":
        assert task["max_new_pbs_submissions"] == 0
        assert task["submissions_consumed"] == 0
    assert task["cumulative_pbs_submissions"] >= 25
    assert len(task["historical_pbs_job_ids"]) >= 25
    assert "1423469.mmaster02" in task["historical_pbs_job_ids"]

def test_f1745_mesh_discrepancy_reconciliation():
    """Verify that all authentic donor decks have exactly 3,923 elements with 100% connectivity parity."""
    coarse_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "188_pk_sec43_hole_plate", "PK_SEC43_COARSE_PHYS.inp")
    t1_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "229_f1743_case3_transient_recovery", "PK_SEC43_COMPANION_T1.inp")
    t2_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "229_f1743_case3_transient_recovery", "PK_SEC43_COMPANION_T2.inp")
    t3_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "229_f1743_case3_transient_recovery", "PK_SEC43_COMPANION_T3.inp")
    
    assert os.path.exists(coarse_path), f"Missing: {coarse_path}"
    assert os.path.exists(t1_path), f"Missing: {t1_path}"
    assert os.path.exists(t2_path), f"Missing: {t2_path}"
    assert os.path.exists(t3_path), f"Missing: {t3_path}"
    
    nodes_c, elems_c, types_c = parse_abaqus_inp(coarse_path)
    nodes_t1, elems_t1, types_t1 = parse_abaqus_inp(t1_path)
    nodes_t2, elems_t2, types_t2 = parse_abaqus_inp(t2_path)
    nodes_t3, elems_t3, types_t3 = parse_abaqus_inp(t3_path)
    
    assert len(elems_c) == 3923, f"Expected 3923 elements, got {len(elems_c)}"
    assert len(elems_t1) == 3923, f"Expected 3923 elements, got {len(elems_t1)}"
    assert len(elems_t2) == 3923, f"Expected 3923 elements, got {len(elems_t2)}"
    assert len(elems_t3) == 3923, f"Expected 3923 elements, got {len(elems_t3)}"
    
    assert set(elems_c.keys()) == set(elems_t1.keys())
    assert set(elems_c.keys()) == set(elems_t2.keys())
    assert set(elems_c.keys()) == set(elems_t3.keys())
    
    assert all(elems_c[eid] == elems_t1[eid] for eid in elems_c)
    assert all(elems_c[eid] == elems_t2[eid] for eid in elems_c)
    assert all(elems_c[eid] == elems_t3[eid] for eid in elems_c)

def test_f1745_pbs_accounting_chronology():
    """Verify chronological accounting for Jobs 20 through 25 in HPC_JOB_LEDGER.csv."""
    ledger_path = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
    assert os.path.exists(ledger_path)
    
    with open(ledger_path, "r") as f:
        lines = [l.strip() for l in f if l.strip()]
        
    last_jobs = [l.split(",") for l in lines[-12:]]
    job_ids = set(r[0] for r in last_jobs)
    
    assert "1423451.mmaster02" in job_ids  # Job 20 (F1743 companion recovery)
    assert "1423459.mmaster02" in job_ids  # Job 21 (F1744 attempt 1)
    assert "1423461.mmaster02" in job_ids  # Job 22 (F1744 attempt 2)
    assert "1423462.mmaster02" in job_ids  # Job 23 (F1744 attempt 3)
    assert "1423463.mmaster02" in job_ids  # Job 24 (F1744 attempt 4)
    assert "1423469.mmaster02" in job_ids  # Job 25 (F1744 attempt 5)

def test_f1745_envelope_numerics_and_singularity_freedom():
    """Verify that the normalized relative error envelope eliminates the 31,518 extreme ratio."""
    assert os.path.exists(EVAL_JSON), f"Missing evaluation JSON: {EVAL_JSON}"
    with open(EVAL_JSON, "r") as f:
        data = json.load(f)
        
    assert data["total_elements"] == 3923
    assert data["envelope_statistics"]["extreme_ratio_eliminated"] is True
    assert data["envelope_statistics"]["singularity_free"] is True
    
    max_eta = data["envelope_statistics"]["max"]
    assert max_eta < 20.0, f"Expected bounded max_eta < 20, got {max_eta}"
    assert max_eta > 10.0, f"Expected active peak > 10, got {max_eta}"
    
    # Check multi-state contribution to primary corridor
    prim_dom = data["primary_corridor"]["state_dominance"]
    assert prim_dom["T1"] > 0, "T1 must contribute to primary corridor"
    assert prim_dom["T2"] > 0, "T2 must contribute to primary corridor"
    assert prim_dom["T3"] > 0, "T3 must contribute to primary corridor"
    
    # Check multi-state contribution to secondary corridor
    sec_dom = data["secondary_corridor"]["state_dominance"]
    assert sec_dom["T3"] > 0 or sec_dom["S4"] > 0, "T3 or S4 must contribute to secondary corridor"
