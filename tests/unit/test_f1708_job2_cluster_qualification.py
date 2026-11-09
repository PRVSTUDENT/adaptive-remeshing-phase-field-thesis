# -*- coding: utf-8 -*-
"""
tests/unit/test_f1708_job2_cluster_qualification.py
==================================================
Unit test suite for Task F1708: Section 4.3 Job-2 Phase-Field Fracture Simulation
HPC Staging, Cluster Datacheck Qualification, and Execution Readiness.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "204_pk_sec43_job2_adapted")
TASK_DEF_DIR = os.path.join(REPO_ROOT, "project_coordination", "task_definitions")
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1708_job2_compatibility_audit.json")


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().lower()


def test_01_job2_production_deck_integrity():
    """Verifies that PK_SEC43_JOB2_ADAPTED_PROD.inp has expected line count and exact frozen hash."""
    inp_path = os.path.join(PKG_DIR, "PK_SEC43_JOB2_ADAPTED_PROD.inp")
    assert os.path.exists(inp_path), f"Input deck missing: {inp_path}"
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = len(f.readlines())
    assert lines == 40448, f"Line count {lines} != expected 40,448"
    deck_hash = sha256_file(inp_path)
    assert deck_hash == "417e749dd934d67c127d1e4b67e9fb32caafb384726ccb58169892855907c68b"


def test_02_frozen_uel_subroutine_integrity():
    """Verifies that f42_mixed_uel.for has exactly 907 lines and matches the bitwise frozen hash."""
    uel_path = os.path.join(PKG_DIR, "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"Subroutine missing: {uel_path}"
    with open(uel_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = len(f.readlines())
    assert lines == 907, f"Line count {lines} != expected 907"
    uel_hash = sha256_file(uel_path)
    assert uel_hash == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_03_cluster_datacheck_artifact_verification():
    """Verifies that M1_PK_SEC43_JOB2_CLUSTER_DATACHECK.dat exists, contains complete status, and matches hash."""
    dat_path = os.path.join(PKG_DIR, "M1_PK_SEC43_JOB2_CLUSTER_DATACHECK.dat")
    assert os.path.exists(dat_path), f"Cluster datacheck artifact missing: {dat_path}"
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    assert "ANALYSIS DATACHECK COMPLETE" in content, "Missing 'ANALYSIS DATACHECK COMPLETE' in .dat"
    dat_hash = sha256_file(dat_path)
    assert dat_hash == "7bbda5778819b9c50267bd0c8fe2162e3f9c89256ab0cf462bf633726e53e401"


def test_04_pbs_script_and_notification_contract():
    """Verifies PBS submission script directives, resource requests, and notification hooks."""
    pbs_path = os.path.join(PKG_DIR, "submit_M1_PK_SEC43_JOB2_ADAPTED.pbs")
    assert os.path.exists(pbs_path), f"PBS script missing: {pbs_path}"
    with open(pbs_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    content = "".join(lines)
    assert "#PBS -N M1_PK_SEC43_JOB2_ADAPTED" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=08:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "job_notifications.sh" in content
    assert "notification_install_terminal_trap" in content
    assert "notify_start" in content


def test_05_mode1_authorization_manifest():
    """Verifies that the Mode-I authorization manifest is properly formatted and hashes match."""
    manifest_path = os.path.join(PKG_DIR, "F1708_PK_SEC43_JOB2_ADAPTED_AUTHORIZATION.json")
    assert os.path.exists(manifest_path), f"Manifest missing: {manifest_path}"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["batch_name"] == "MODE1_PK_SEC43_JOB2_ADAPTED"
    assert manifest["max_submissions"] == 1
    assert manifest["automatic_retry"] is False
    files = manifest["files"]
    assert files["PK_SEC43_JOB2_ADAPTED_PROD.inp"] == "417e749dd934d67c127d1e4b67e9fb32caafb384726ccb58169892855907c68b"
    assert files["f42_mixed_uel.for"] == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
    assert files["M1_PK_SEC43_JOB2_CLUSTER_DATACHECK.dat"] == "7bbda5778819b9c50267bd0c8fe2162e3f9c89256ab0cf462bf633726e53e401"
    jobs = manifest["jobs"]
    assert len(jobs) == 1
    assert jobs[0]["id"] == "job2_adapted_prod"
    assert jobs[0]["cpus"] == 1
    assert jobs[0]["memory_gb"] == 16
    assert jobs[0]["walltime_hours"] == 8


def test_06_task_f1708_registration():
    """Verifies that Task F1708 is registered with max_new_pbs_submissions = 1."""
    task_def_path = os.path.join(TASK_DEF_DIR, "F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE.json")
    assert os.path.exists(task_def_path), f"Task definition missing: {task_def_path}"
    with open(task_def_path, "r", encoding="utf-8") as f:
        task_def = json.load(f)
    assert task_def["task_id"] == "F1708-PK-SEC43-JOB2-ADAPTED-MESH-SOLVE"
    assert task_def["max_new_pbs_submissions"] == 1
    assert task_def["scope_boundaries"]["production_uel_untouched"] is True
    assert task_def["scope_boundaries"]["once_only_accounting"] is True


def test_07_compatibility_audit_report():
    """Verifies that the compatibility audit confirms qualified status across all four findings."""
    assert os.path.exists(AUDIT_JSON), f"Audit JSON missing: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r", encoding="utf-8") as f:
        audit = json.load(f)
    assert audit["audit_task"] == "F1708_JOB2_COMPATIBILITY_AUDIT"
    assert audit["governing_uel"]["status"] == "FROZEN_AUTHORITATIVE_PRODUCTION_UEL"
    assert audit["loading_schedule"]["cumulative_terminal_displacement_mm"] == 1.5
    assert audit["distorted_elements_audit"]["28658"]["positive_jacobian"] is True
    assert audit["distorted_elements_audit"]["29490"]["positive_jacobian"] is True
    assert audit["crack_corridor_resolution"]["secondary_corridor_centerline_le_l0_pct"] == 100.0

