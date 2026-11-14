# -*- coding: utf-8 -*-
"""
tests/unit/test_f1746_case3_envelope_execution_readiness.py

Unit test suite for Task F1746 Case 3 Single-Pass 5-State Envelope Remeshing Execution Readiness:
  - Manifest and frozen UEL verification
  - Python scripts syntax and parameters
  - PBS execution script directives, preflight checks, and dual-channel notifications
  - Seven predeclared physical and spatial gates
  - Coordination and finite PBS accounting integrity
"""
import os
import sys
import json
import hashlib
import ast

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "231_f1746_case3_envelope_remesh")
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1746_manifest_and_uel_preservation():
    manifest_path = os.path.join(PKG_DIR, "f1746_case3_envelope_remesh.json")
    assert os.path.isfile(manifest_path), "Manifest must exist"
    with open(manifest_path, "r") as f:
        m = json.load(f)
    assert m["task_id"] == "F1746-CASE3-5STATE-ENVELOPE-EXECUTION"
    assert m["correlation_id"] in ["HND-F1746-CASE3-AUTH-001", "HND-F1746-CASE3-AUTH-002"]
    assert m["predecessor_correlation_id"] == "HND-F1745-CASE3-QUAL-001"
    assert m["governance"]["max_new_pbs_submissions"] == 1
    assert m["governance"]["cumulative_pbs_submissions"] == 25
    assert m["governance"]["prospective_submission_number"] == 26

    # Verify bitwise frozen UEL
    uel_path = os.path.join(PKG_DIR, "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), "UEL source must exist"
    with open(uel_path, "rb") as f:
        h = hashlib.sha256(f.read()).hexdigest().lower()
    assert h == FROZEN_UEL_SHA, "Frozen UEL hash mismatch"

def test_f1746_scripts_syntax_and_structure():
    scripts = [
        "build_case3_5state_envelope_donor.py",
        "run_case3_envelope_remesh.py",
        "audit_case3_envelope_resolution.py"
    ]
    for s in scripts:
        sp = os.path.join(PKG_DIR, s)
        assert os.path.isfile(sp), "Script %s must exist" % s
        with open(sp, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code)

    # Check that build script contains S_base = 100.0 and zero-norm guard
    with open(os.path.join(PKG_DIR, "build_case3_5state_envelope_donor.py"), "r") as f:
        src = f.read()
    assert "S_base = 100.0" in src
    assert "epsilon_tol" in src

    # Check that remesh script contains calibrated error_target and single pass
    with open(os.path.join(PKG_DIR, "run_case3_envelope_remesh.py"), "r") as f:
        src = f.read()
    assert "error_target = 0.30" in src or "error_target = 0.035" in src
    assert "coarseningFactor=NOT_ALLOWED" in src
    assert "EnvelopeRemeshRule" in src

def test_f1746_pbs_script_directives_and_preflight():
    pbs_path = os.path.join(PKG_DIR, "submit_f1746_case3_envelope_remesh.pbs")
    assert os.path.isfile(pbs_path), "PBS script must exist"
    with open(pbs_path, "r", encoding="utf-8") as f:
        pbs = f.read()

    assert "#PBS -N F1746_C3_REMESH" in pbs
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in pbs
    assert "#PBS -l walltime=01:00:00" in pbs
    assert "#PBS -q entry_imfdfkmq" in pbs
    assert "#PBS -m abe" in pbs
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in pbs
    assert "job_notifications.sh" in pbs
    assert "notify_start" in pbs
    assert "notification_install_terminal_trap" in pbs
    assert "EXPECTED_UEL_SHA=" in pbs
    assert "${JOB_NAME}.lck" in pbs

def test_f1746_coordination_and_ledger_integrity():
    task_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] in [
        "F1746-CASE3-5STATE-ENVELOPE-EXECUTION",
        "F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE",
        "F1748-AUTHENTIC-COUPLED-DAMAGE-FIELD-RECOVERY-AND-INDICATOR-FEASIBILITY"
    ]
    assert task["cumulative_pbs_submissions"] == 25
    assert len(task["historical_pbs_job_ids"]) == 25
    assert task["frozen_uel_sha256"] == FROZEN_UEL_SHA.upper()

    session_json = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_SESSION.json")
    with open(session_json, "r", encoding="utf-8-sig") as f:
        sess = json.load(f)
    assert sess["active"] is True
    assert sess["agent"] == "gemini-antigravity"
    assert sess["task_id"] in [
        "F1746-CASE3-5STATE-ENVELOPE-EXECUTION",
        "F1747-CASE3-CONTRAST-TRANSFORMATION-PROTOTYPE",
        "F1748-AUTHENTIC-COUPLED-DAMAGE-FIELD-RECOVERY-AND-INDICATOR-FEASIBILITY"
    ]

def test_f1746_seven_predeclared_gates_defined():
    manifest_path = os.path.join(PKG_DIR, "f1746_case3_envelope_remesh.json")
    with open(manifest_path, "r") as f:
        m = json.load(f)
    gates = m["predeclared_execution_gates"]
    assert "Gate_1_Inversion_Safety" in gates
    assert "Gate_2_Element_Quality" in gates
    assert "Gate_3_Primary_Corridor_Compliance" in gates
    assert "Gate_4_Secondary_Corridor_Compliance" in gates
    assert "Gate_5_Transverse_Coarse_Barrier" in gates
    assert "Gate_6_Production_Datacheck" in gates
    assert "Gate_7_Strict_Governance" in gates
