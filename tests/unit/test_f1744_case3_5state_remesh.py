# -*- coding: utf-8 -*-
"""
test_f1744_case3_5state_remesh.py
=================================
Unit tests for Task F1744 Case 3 5-State Sequential Native Remeshing:
  - Manifest structure, 5-state sequence, and remeshing controls
  - Frozen UEL hash preservation
  - Dual-channel notification and PBS execution script directives
  - HPC ledger accounting integrity (cumulative submissions)
  - 5-state donor sequence completeness
"""
import os
import json
import hashlib
import csv
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "230_f1744_case3_5state_remesh")
MANIFEST_PATH = os.path.join(PKG_DIR, "f1744_case3_5state_remesh.json")
UEL_PATH = os.path.join(PKG_DIR, "f42_mixed_uel.for")
PBS_PATH = os.path.join(PKG_DIR, "submit_f1744_case3_5state_remesh.pbs")
REMESH_SCRIPT_PATH = os.path.join(PKG_DIR, "run_case3_5state_remesh.py")
AUDIT_SCRIPT_PATH = os.path.join(PKG_DIR, "audit_case3_5state_resolution.py")
LEDGER_PATH = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1744_manifest_integrity():
    assert os.path.isfile(MANIFEST_PATH), "Manifest must exist"
    with open(MANIFEST_PATH, "r") as f:
        data = json.load(f)
    assert data["task_id"] == "F1744-CASE3-5STATE-REMESHING-EXECUTION"
    assert data["material_properties"]["length_scale_l0_mm"] == 0.285
    assert len(data["remeshing_sequence"]) == 5
    expected_states = ["T1", "T2", "T3", "State2", "State4"]
    actual_states = [s["state_id"] for s in data["remeshing_sequence"]]
    assert actual_states == expected_states
    assert data["remeshing_controls"]["refinement_factor"] == "DEFAULT_LIMIT"
    assert data["remeshing_controls"]["coarsening_factor"] == "NOT_ALLOWED"
    assert data["remeshing_controls"]["error_target_percent"] == 1.80
    assert data["remeshing_controls"]["min_element_size_mm"] == 0.080

def test_f1744_frozen_uel_preservation():
    assert os.path.isfile(UEL_PATH), "Frozen UEL must exist in package"
    with open(UEL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest()
    assert actual_sha == EXPECTED_UEL_SHA, "Subroutine f42_mixed_uel.for must match canonical hash"

def test_f1744_pbs_script_directives():
    assert os.path.isfile(PBS_PATH), "PBS script must exist"
    with open(PBS_PATH, "r") as f:
        content = f.read()
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content
    assert "job_notifications.sh" in content
    assert "notification_install_terminal_trap" in content
    assert "run_case3_5state_remesh.py" in content
    assert "audit_case3_5state_resolution.py" in content
    assert "abaqus datacheck" in content
    assert EXPECTED_UEL_SHA in content

def test_f1744_scripts_syntax():
    assert os.path.isfile(REMESH_SCRIPT_PATH), "Remesh script must exist"
    assert os.path.isfile(AUDIT_SCRIPT_PATH), "Audit script must exist"
    assert os.path.isfile(os.path.join(PKG_DIR, "PK_SEC43_COMPANION_T1.inp")), "Companion T1 deck must exist"
    assert os.path.isfile(os.path.join(PKG_DIR, "PK_SEC43_COMPANION_T2.inp")), "Companion T2 deck must exist"
    assert os.path.isfile(os.path.join(PKG_DIR, "PK_SEC43_COMPANION_T3.inp")), "Companion T3 deck must exist"
    with open(REMESH_SCRIPT_PATH, "r") as f:
        remesh_src = f.read()
    assert "coarseningFactor=NOT_ALLOWED" in remesh_src
    assert "PK_F1744_CASE_3_ADAPT_PHYS" in remesh_src
    assert "PK_F1744_CASE_3_PROD" in remesh_src
    with open(AUDIT_SCRIPT_PATH, "r") as f:
        audit_src = f.read()
    assert "L0_HALF_MM = L0_MM / 2.0" in audit_src
    assert "has_transverse_coarse_barrier" in audit_src

def test_f1744_accounting_and_ledger_integrity():
    assert os.path.isfile(ACTIVE_TASK_PATH), "ACTIVE_TASK.json must exist"
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in ["F1744-CASE3-5STATE-REMESHING-EXECUTION", "F1745-CASE3-5STATE-ENVELOPE-QUALIFICATION"]
    assert task["cumulative_pbs_submissions"] in [20, 21, 22, 23, 24, 25]
    assert task["max_new_pbs_submissions"] in [0, 1, 2, 3, 4, 5]
    assert task["frozen_uel_sha256"] == EXPECTED_UEL_SHA.upper()
    assert len(task["historical_pbs_job_ids"]) in [20, 21, 22, 23, 24, 25]

    # Check HPC_JOB_LEDGER.csv
    assert os.path.isfile(LEDGER_PATH), "HPC_JOB_LEDGER.csv must exist"
    with open(LEDGER_PATH, "r") as f:
        reader = list(csv.reader(f))
    # Must have header + >= 20 job entries
    assert len(reader) >= 21
