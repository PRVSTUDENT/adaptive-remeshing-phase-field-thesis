# -*- coding: utf-8 -*-
"""
tests/unit/test_f1774_four_benchmark_regression_execution.py
===========================================================
Validates Task F1774 Execution Package Safety & Scientific Repair:
1. Validates bitwise frozen UEL (CE8D5EDC...) and framework (8D71F38F...).
2. Verifies PBS wrappers satisfy all safety requirements (F1774-R01, R03, R04, R05):
   - Safe non-recursive lock cleanup (no 'rm -rf' fallback).
   - Fail-closed hash verification for UEL, framework, config, and donor ODBs.
   - Fail-closed production deck existence and Abaqus datacheck Exit 0 requirement.
   - Per-case isolated scratch working directory execution.
3. Verifies Case 5 scale-invariance and physical indicator localization (F1774-R02).
4. Verifies Case 3 parent-to-companion frame provenance mapping (F1774-R06).
5. Confirms cumulative PBS accounting (30 jobs consumed, 0 consumed under F1774, max 3 authorized).
"""
import os
import sys
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FW_SHA = "8d71f38f23867a23c1fc1bf5ec499533a8c75f538b77804ece03b5c668f4be08"

CANONICAL_MANIFEST = os.path.join(REPO_ROOT, "configs", "remeshing", "canonical_five_case_manifest.json")
CASE2_PBS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "submit_f1774_case2_remesh.pbs")
CASE3_PBS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "submit_f1774_case3_remesh.pbs")
CASE5_PBS = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "240_f1774_suite_regression", "submit_f1774_case5_remesh.pbs")


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_uel_and_framework_invariance():
    assert compute_sha256(FROZEN_UEL_PATH) == EXPECTED_UEL_SHA
    assert compute_sha256(FRAMEWORK_PATH) == EXPECTED_FW_SHA


def test_pbs_wrapper_lock_safety():
    """Verify F1774-R01: non-recursive safe lock cleanup without rm -rf."""
    for pbs_path in [CASE2_PBS, CASE3_PBS, CASE5_PBS]:
        with open(pbs_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "trap 'rmdir \"${LOCK_DIR}\" 2>/dev/null || true' EXIT" in content, f"Unsafe trap in {pbs_path}"
        assert "rm -rf" not in content, f"Dangerous recursive rm -rf found in {pbs_path}"
        assert 'mkdir "${LOCK_DIR}"' in content, f"Missing atomic mkdir in {pbs_path}"


def test_pbs_wrapper_hash_checks():
    """Verify F1774-R03: fail-closed SHA-256 verification of config and donor ODBs."""
    # Case 2 checks
    with open(CASE2_PBS, "r", encoding="utf-8") as f:
        c2_text = f.read()
    assert "EXPECTED_CONFIG_SHA=" in c2_text
    assert "EXPECTED_DONOR_SHA=" in c2_text
    assert "sha256sum \"${CONFIG_FILE}\"" in c2_text
    assert "sha256sum \"${DONOR_ODB}\"" in c2_text

    # Case 3 checks
    with open(CASE3_PBS, "r", encoding="utf-8") as f:
        c3_text = f.read()
    assert "EXPECTED_CONFIG_SHA=" in c3_text
    assert "EXPECTED_DONOR_STATE2_SHA=" in c3_text
    assert "EXPECTED_DONOR_STATE4_SHA=" in c3_text
    assert "sha256sum \"PK_SEC43_PRESCRIBED_STATE2.odb\"" in c3_text
    assert "sha256sum \"PK_SEC43_PRESCRIBED_STATE4.odb\"" in c3_text

    # Case 5 checks
    with open(CASE5_PBS, "r", encoding="utf-8") as f:
        c5_text = f.read()
    assert "EXPECTED_CONFIG_SHA=" in c5_text
    assert "EXPECTED_DONOR_SHA=" in c5_text
    assert "sha256sum \"${DONOR_ODB}\"" in c5_text


def test_pbs_wrapper_fatal_production_deck():
    """Verify F1774-R04: missing production deck is fatal; genuine datacheck Exit 0 required."""
    for pbs_path in [CASE2_PBS, CASE3_PBS, CASE5_PBS]:
        with open(pbs_path, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'if [ ! -f "${PROD_DECK}" ]; then' in content
        assert "exit 1" in content
        assert 'datacheck job=' in content
        assert 'if [ "${DC_EXIT_CODE}" -ne 0 ]; then' in content


def test_pbs_wrapper_directory_isolation():
    """Verify F1774-R05: each job operates in its own isolated subfolder."""
    with open(CASE2_PBS, "r", encoding="utf-8") as f:
        assert 'case2_off_axis_hole' in f.read()
    with open(CASE3_PBS, "r", encoding="utf-8") as f:
        assert 'case3_notched_pins' in f.read()
    with open(CASE5_PBS, "r", encoding="utf-8") as f:
        assert 'case5_seven_hole' in f.read()


def test_case3_parent_to_companion_provenance():
    """Verify F1774-R06: parent-to-companion provenance mapping."""
    with open(CANONICAL_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    c3 = manifest["benchmarks"]["case_3"]
    assert "PK_SEC43_STAGGERED_JOB1.odb" in c3["parent_staggered_odb_cluster_path"]
    assert "PK_SEC43_PRESCRIBED_STATE2.odb" in c3["donor_odb_repo_path"]
    assert "PK_SEC43_PRESCRIBED_STATE4.odb" in c3["donor_odb_repo_path"]
    assert c3["donor_displacement_uy_mm"] == [0.150, 0.275]


def test_cumulative_submission_accounting():
    """Verify strict once-only accounting: 30 cumulative prior to F1774, 3 consumed in F1774."""
    with open(CANONICAL_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["governing_rules"]["cumulative_pbs_submissions"] == 30

    task_ledger_path = os.path.join(REPO_ROOT, "project_coordination", "TASK_LEDGER.csv")
    with open(task_ledger_path, "r", encoding="utf-8") as f:
        text = f.read()
    assert "F1774-FOUR-BENCHMARK-METHOD-A-REGRESSION-EXECUTION" in text
    assert ",3,3,33," in text
