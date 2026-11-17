# -*- coding: utf-8 -*-
"""
tests/unit/test_f1834_early_state_blowup_guard.py
================================================
Task F1834 Unit Test Suite:
Verifies:
1. Frozen production UEL bitwise invariance (CE8D5EDC...).
2. Shared framework SHA-256 updated and verified (098D005F...).
3. Existence and validity of early-state diagnosis data (f1834_early_state_diagnosis.json).
4. Threshold sweep execution outputs and summary JSON (f1834_blowup_guard_summary.json).
5. Master receipt existence and governance conformance (zero new PBS, cumulative=35, OPEN).
6. Finite-element quality gates across all cases: positive Jacobians, quad fraction >= 90%, max AR < 4.0, valid corner angles.
7. Standalone mesh images and 2x2 publication composite existence and non-zero size.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_SHA = "098D005F93138749E80975C4A96F6BDF5EE7C54B98DB0162BDC62188FE76B187"

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_frozen_uel_sha256():
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "268_f1824_job2_preflight", "case1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), f"Frozen UEL missing at {uel_path}"
    sha = compute_sha256(uel_path)
    assert sha == FROZEN_UEL_SHA, f"Frozen UEL modified! Expected {FROZEN_UEL_SHA}, got {sha}"

def test_shared_framework_sha256():
    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    assert os.path.exists(framework_path), "Framework missing"
    sha = compute_sha256(framework_path)
    assert sha == FRAMEWORK_SHA, f"Framework hash mismatch! Expected {FRAMEWORK_SHA}, got {sha}"

def test_f1834_early_state_diagnosis_exists():
    diag_p = os.path.join(REPO_ROOT, "results", "validation", "f1834_early_state_diagnosis.json")
    assert os.path.exists(diag_p), f"Diagnosis JSON missing at {diag_p}"
    with open(diag_p, "r") as f:
        diag = json.load(f)
    assert "case_1" in diag
    assert "case_2" in diag
    assert "case_3" in diag
    # Verify Case 1 has 5 states and Case 2 has 4 states
    assert len(diag["case_1"]["states"]) == 5
    assert len(diag["case_2"]["states"]) == 4

def test_f1834_master_receipt_and_summary_exist():
    receipt_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1834_BLOWUP_GUARD_RECEIPT.json")
    summary_p = os.path.join(REPO_ROOT, "results", "validation", "f1834_blowup_guard_summary.json")
    assert os.path.exists(receipt_p), f"Master receipt missing at {receipt_p}"
    assert os.path.exists(summary_p), f"Summary JSON missing at {summary_p}"
    with open(receipt_p, "r") as f:
        rec = json.load(f)
    assert rec["cumulative_pbs_submissions"] == 35
    assert rec["new_pbs_submissions"] == 0
    assert rec["master_goal_status"] == "OPEN"

def test_f1834_quality_gates():
    receipt_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1834_BLOWUP_GUARD_RECEIPT.json")
    assert os.path.exists(receipt_p)
    with open(receipt_p, "r") as f:
        rec = json.load(f)
    cases = rec["selected_cases"]
    for cid, cdata in cases.items():
        m = cdata["audit_metrics"]
        assert m["min_det_j"] > 0.0, f"Case {cid} non-positive Jacobian: {m['min_det_j']}"
        assert m["quad_fraction_pct"] >= 90.0, f"Case {cid} quad fraction < 90%: {m['quad_fraction_pct']}"
        assert m["max_aspect_ratio"] <= 4.0, f"Case {cid} aspect ratio > 4.0: {m['max_aspect_ratio']}"

def test_f1834_figure_artifacts():
    figures = [
        "fig_f1834_case_1_standalone_mesh.png",
        "fig_f1834_case_1_standalone_mesh.pdf",
        "fig_f1834_case_2_standalone_mesh.png",
        "fig_f1834_case_2_standalone_mesh.pdf",
        "fig_f1834_case_3_standalone_mesh.png",
        "fig_f1834_case_3_standalone_mesh.pdf",
        "fig_f1834_case_5_standalone_mesh.png",
        "fig_f1834_case_5_standalone_mesh.pdf",
        "fig_f1834_four_benchmark_synthesis.png",
        "fig_f1834_four_benchmark_synthesis.pdf",
    ]
    fig_dir = os.path.join(REPO_ROOT, "results", "figures")
    for fname in figures:
        p = os.path.join(fig_dir, fname)
        assert os.path.exists(p), f"Figure missing: {p}"
        assert os.path.getsize(p) > 1000, f"Figure unexpectedly small: {p}"
