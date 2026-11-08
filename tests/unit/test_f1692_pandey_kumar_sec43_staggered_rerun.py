# -*- coding: utf-8 -*-
"""
test_f1692_pandey_kumar_sec43_staggered_rerun.py
================================================
Unit test suite for Task F1692:
Method A Pandey-Kumar Section 4.3 Job-1 Staggered-Solver Rerun.

Validates:
1. Production UEL bitwise inviolability and staggered variant integrity.
2. Geometry datum and 3-layer input deck parameters.
3. Staggered constitutive local verification (C1-C5 pass).
4. Full solver completion across Step 1 and Step 2 (4,500 direct increments).
5. Dual-branch physical crack propagation (primary and secondary severance d=1.0).
6. Native Abaqus one-rule adaptive remeshing metrics.
7. HPC job execution accounting in HPC_JOB_LEDGER.csv.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

VARIANT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
VARIANT_UEL_PATH = os.path.join(VARIANT_DIR, "f42_staggered_variant_uel.for")
EXPECTED_VARIANT_UEL_SHA256 = "a0ebb58ddc0309d2afc2bf45c2ea3b74a8d2aba5719c05af1b69b57086afa633"

INP_PATH = os.path.join(VARIANT_DIR, "PK_SEC43_STAGGERED_JOB1.inp")
EXPECTED_INP_SHA256 = "be1d4174af0bb415f3183a98f95fb30022731d0b900127a28810790537cc83d0"

LOCAL_VERIF_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1692_staggered_local_verification.json")
ADAPTED_METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1692_sec43_adapted_mesh_metrics.json")
DAMAGED_ELS_JSON = os.path.join(VARIANT_DIR, "f1692_damaged_elements.json")
HPC_LEDGER_CSV = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def test_f1692_uel_inviolability_and_variant_integrity():
    """Verify production UEL is strictly untouched and staggered variant hash matches."""
    assert os.path.exists(FROZEN_UEL_PATH), "Production UEL not found"
    prod_sha = compute_sha256(FROZEN_UEL_PATH)
    assert prod_sha == EXPECTED_FROZEN_UEL_SHA256, (
        "Production UEL modified! Expected %s, got %s" % (EXPECTED_FROZEN_UEL_SHA256, prod_sha)
    )

    assert os.path.exists(VARIANT_UEL_PATH), "Staggered variant UEL not found"
    var_sha = compute_sha256(VARIANT_UEL_PATH)
    assert var_sha == EXPECTED_VARIANT_UEL_SHA256, (
        "Staggered variant UEL hash mismatch! Expected %s, got %s" % (EXPECTED_VARIANT_UEL_SHA256, var_sha)
    )

def test_f1692_input_deck_and_parameters():
    """Verify input deck hash, node count, element count, and direct increment schedule."""
    assert os.path.exists(INP_PATH), "Input deck not found: %s" % INP_PATH
    inp_sha = compute_sha256(INP_PATH)
    assert inp_sha == EXPECTED_INP_SHA256, (
        "Input deck hash mismatch! Expected %s, got %s" % (EXPECTED_INP_SHA256, inp_sha)
    )

    with open(INP_PATH, "r") as f:
        content = f.read()

    assert "*STATIC, DIRECT" in content, "Missing *STATIC, DIRECT in input deck"
    assert "0.0005, 1." in content, "Step 1 missing 0.0005, 1.0 schedule"
    assert "0.0002, 0.5" in content, "Step 2 missing 0.0002, 0.5 schedule"
    assert "MISESERI, MISESAVG" in content, "Missing MISESERI output in input deck"

def test_f1692_local_constitutive_verification():
    """Verify local verification results (C1-C5 criteria passed)."""
    assert os.path.exists(LOCAL_VERIF_JSON), "Missing %s" % LOCAL_VERIF_JSON
    with open(LOCAL_VERIF_JSON, "r") as f:
        data = json.load(f)

    assert data.get("overall_stage_a_status") == "PASS", "Local constitutive verification failed"
    criteria = data.get("acceptance_criteria", {})
    assert criteria.get("C1_strict_irreversibility_no_healing") == "PASS"
    assert criteria.get("C2_damage_bounds_zero_to_one") == "PASS"
    assert criteria.get("C3_physical_peak_and_softening") == "PASS"
    assert criteria.get("C4_direct_incrementation_configured") == "PASS"
    assert criteria.get("C5_frozen_production_uel_untouched") == "PASS"

def test_f1692_dual_branch_crack_propagation():
    """Verify that both primary and secondary ligaments underwent full damage (d = 1.0)."""
    cand_paths = [
        DAMAGED_ELS_JSON,
        os.path.join(REPO_ROOT, "results", "validation", "f1692_damaged_elements.json")
    ]
    path = None
    for p in cand_paths:
        if os.path.exists(p):
            path = p
            break

    assert path is not None, "Damaged elements record not found"
    with open(path, "r") as f:
        d = json.load(f)
    els = d["damaged_elements"]
    assert len(els) > 50, "Insufficient damaged elements (%d)" % len(els)

    prim = [e for e in els if e["cx"] <= 36.5]
    sec = [e for e in els if e["cx"] > 36.5]

    assert len(prim) > 0, "No primary corridor damage"
    assert len(sec) > 0, "No secondary corridor damage"

    assert max(e["damage"] for e in prim) >= 0.99, "Primary damage did not reach full severance"
    assert max(e["damage"] for e in sec) >= 0.99, "Secondary damage did not reach full severance"

    sec_xs = [e["cx"] for e in sec]
    assert min(sec_xs) <= 47.0, "Secondary crack did not nucleate at hole flank"
    assert max(sec_xs) >= 63.0, "Secondary crack did not reach right boundary"

def test_f1692_hpc_job_ledger_completion():
    """Verify PBS Job 1421286.mmaster02 completed Exit 0 in HPC_JOB_LEDGER.csv."""
    assert os.path.exists(HPC_LEDGER_CSV), "Missing %s" % HPC_LEDGER_CSV
    found_completed = False
    with open(HPC_LEDGER_CSV, "r") as f:
        for line in f:
            if "1421286.mmaster02" in line and "COMPLETED,0" in line:
                found_completed = True
                assert "4500_INCS" in line
                break
    assert found_completed, "Job 1421286.mmaster02 not recorded as COMPLETED,0 in ledger"

def test_f1692_adapted_mesh_metrics():
    """Verify native Abaqus remeshing metrics on Section 4.3."""
    cand_paths = [
        ADAPTED_METRICS_JSON,
        os.path.join(REPO_ROOT, "f1692_sec43_adapted_mesh_metrics.json"),
        os.path.join(VARIANT_DIR, "f1692_sec43_adapted_mesh_metrics.json")
    ]
    path = None
    for p in cand_paths:
        if os.path.exists(p):
            path = p
            break

    assert path is not None, "Adapted mesh metrics not found"
    with open(path, "r") as f:
        data = json.load(f)

    assert data["elements_total"] > 10000, "Unexpected adapted element count: %d" % data["elements_total"]
    assert data["pct_quads"] >= 90.0, "Quad percentage below 90%: %.2f" % data["pct_quads"]
    assert data["primary_corridor"]["pct_l0_half"] > 0.0, "Primary corridor unrefined"
    # Secondary corridor is unrefined under single-rule, proving thesis falsification finding
    assert data["secondary_corridor"]["pct_l0_half"] == 0.0, (
        "Secondary corridor unexpectedly refined under single rule (expected 0.0%%, got %.2f%%)" %
        data["secondary_corridor"]["pct_l0_half"]
    )
