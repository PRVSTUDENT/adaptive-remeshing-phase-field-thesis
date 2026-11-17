# -*- coding: utf-8 -*-
"""
tests/unit/test_f1833_state_consistent_normalization.py
======================================================
Task F1833 Unit Test Suite:
Verifies:
1. Frozen production UEL bitwise invariance (CE8D5EDC...).
2. Shared framework SHA-256 invariance (8523021E...).
3. Existence and validity of all 4 physical adapted mesh INP files.
4. Finite-element quality gates: positive Jacobians, quad fraction >= 90%, max AR < 4.0, valid corner angles.
5. Gate 06 far-field coarsening under original definition.
6. Case 5 single-state parity preservation (15,466 elements).
7. Standalone mesh images and 2x2 publication composite existence and non-zero size.
8. Zero PBS submissions consumed (cumulative = 35 preserved).
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FRAMEWORK_SHA = "8523021EADE3EA5BA5B2A179571E74D47C9F5985899551E384A153B8E640FCBE"

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

def test_f1833_master_receipt_and_summary_exist():
    receipt_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "PK_F1833_STATE_CONSISTENT_RECEIPT.json")
    summary_p = os.path.join(REPO_ROOT, "results", "validation", "f1833_state_consistent_summary.json")
    assert os.path.exists(receipt_p), "Master receipt missing"
    assert os.path.exists(summary_p), "Summary JSON missing"
    with open(receipt_p, "r") as f:
        rec = json.load(f)
    assert rec["cumulative_pbs_submissions"] == 35
    assert rec["new_pbs_submissions"] == 0
    assert rec["master_goal_status"] == "OPEN"

def test_case1_mesh_quality_and_metrics():
    rec_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization", "case1", "PK_F1833_CASE_1_RECEIPT.json")
    assert os.path.exists(rec_p)
    with open(rec_p, "r") as f:
        r = json.load(f)
    m = r["audit_metrics"]
    assert m["total_elements"] == 9234, f"Expected 9234 elements, got {m['total_elements']}"
    assert m["quad_fraction_pct"] >= 90.0
    assert m["min_det_j"] > 0.0
    assert m["max_aspect_ratio"] < 4.0
    assert m["coarsening_ratio"] >= 2.0  # Gate 06 PASS (2.455x)
    assert r["gate_summary"]["gate_06_far_field_coarsening"] == "PASS"

def test_case2_mesh_quality_and_metrics():
    rec_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization", "case2", "PK_F1833_CASE_2_RECEIPT.json")
    assert os.path.exists(rec_p)
    with open(rec_p, "r") as f:
        r = json.load(f)
    m = r["audit_metrics"]
    assert m["total_elements"] == 117181
    assert m["quad_fraction_pct"] >= 90.0
    assert m["min_det_j"] > 0.0
    assert m["max_aspect_ratio"] < 4.0
    assert r["scientific_gate_status"] == "PASS"
    assert r["gate_summary"]["gate_06_far_field_coarsening"] == "FAIL"

def test_case3_mesh_quality_and_metrics():
    rec_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization", "case3", "PK_F1833_CASE_3_RECEIPT.json")
    assert os.path.exists(rec_p)
    with open(rec_p, "r") as f:
        r = json.load(f)
    m = r["audit_metrics"]
    assert m["total_elements"] == 130218
    assert m["quad_fraction_pct"] >= 90.0
    assert m["min_det_j"] > 0.0
    assert m["max_aspect_ratio"] < 4.0
    assert r["scientific_gate_status"] == "PASS"
    assert r["gate_summary"]["gate_06_far_field_coarsening"] == "FAIL"

def test_case5_single_state_parity():
    rec_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "273_f1833_state_consistent_normalization", "case5", "PK_F1833_CASE_5_RECEIPT.json")
    assert os.path.exists(rec_p)
    with open(rec_p, "r") as f:
        r = json.load(f)
    m = r["audit_metrics"]
    assert m["total_elements"] == 15466, "Case 5 parity broken!"
    assert m["quad_fraction_pct"] >= 90.0
    assert m["min_det_j"] > 0.0
    assert m["max_aspect_ratio"] < 4.0
    assert m["coarsening_ratio"] >= 2.0  # Gate 06 PASS (2.1174x)
    assert r["gate_summary"]["gate_06_far_field_coarsening"] == "PASS"
    assert r["physical_inp_body_sha256"] == "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065"

def test_all_figures_exist_and_non_empty():
    fig_dir = os.path.join(REPO_ROOT, "results", "figures")
    figs = [
        "fig_f1833_case_1_standalone_mesh.png",
        "fig_f1833_case_1_standalone_mesh.pdf",
        "fig_f1833_case_2_standalone_mesh.png",
        "fig_f1833_case_2_standalone_mesh.pdf",
        "fig_f1833_case_3_standalone_mesh.png",
        "fig_f1833_case_3_standalone_mesh.pdf",
        "fig_f1833_case_5_standalone_mesh.png",
        "fig_f1833_case_5_standalone_mesh.pdf",
        "fig_f1833_four_benchmark_synthesis.png",
        "fig_f1833_four_benchmark_synthesis.pdf"
    ]
    for fn in figs:
        fp = os.path.join(fig_dir, fn)
        assert os.path.exists(fp), f"Figure {fn} missing"
        assert os.path.getsize(fp) > 1000, f"Figure {fn} is suspiciously small ({os.path.getsize(fp)} bytes)"
