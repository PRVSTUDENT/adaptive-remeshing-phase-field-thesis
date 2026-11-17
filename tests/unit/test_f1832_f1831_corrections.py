# -*- coding: utf-8 -*-
"""
tests/unit/test_f1832_f1831_corrections.py
=========================================
Unit test suite for Task F1832:
Verification of corrections to the F1831 matched donor experiment report and evidence.
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FRAMEWORK_SHA = "80b41aa253e5b36b2bcf5d716b88843d29355141171c60aff6e7134a0312932c"

SUMMARY_PATH = os.path.join(REPO_ROOT, "results", "validation", "f1831_matched_donor_summary.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1831_MATCHED_DONOR_EXPERIMENT_REPORT.md")


def sha256_mesh_body(filepath):
    h = hashlib.sha256()
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            if not line.strip().startswith("**"):
                h.update(line.strip().encode("utf-8") + b"\n")
    return h.hexdigest().upper()


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_uel_and_framework_hashes():
    assert sha256_file(FROZEN_UEL_PATH).lower() == EXPECTED_UEL_SHA
    assert sha256_file(FRAMEWORK_PATH).lower() == EXPECTED_FRAMEWORK_SHA


def test_f1831_summary_reconciled_values():
    with open(SUMMARY_PATH, "r") as f:
        summary = json.load(f)

    # Case 1 A.1
    c1_a1 = summary["matched_cases"]["case_1"]["a1_single_state"]
    assert c1_a1["total_elements"] == 4384
    assert c1_a1["gate06_status"] == "FAIL"

    # Case 3 A.1
    c3_a1 = summary["matched_cases"]["case_3"]["a1_single_state"]
    assert c3_a1["total_elements"] == 44534
    assert c3_a1["gate06_coarsening"] == 1.05
    assert c3_a1["gate06_status"] == "FAIL"

    # Inflation
    audit = summary["aggregation_audit"]
    assert audit["case_1"]["mean_inflation_pct"] == -13.99
    assert audit["case_1"]["max_inflation_pct"] == 150.23
    assert audit["case_2"]["mean_inflation_pct"] == 24.63
    assert audit["case_2"]["max_inflation_pct"] == 36.90
    assert audit["case_3"]["mean_inflation_pct"] == -0.67
    assert audit["case_3"]["max_inflation_pct"] == 198.68
    assert audit["case_5"]["mean_inflation_pct"] == 0.0
    assert audit["case_5"]["max_inflation_pct"] == 0.0


def test_a1_mesh_files_and_body_hashes():
    expected_meshes = {
        "case1_a1": ("models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/case1/PK_F1831_CASE_1_A1_PHYS.inp", "A3FAE74F81182719DD6EFCA23010D71D08D5E278299785551CB76EC4738ACD14"),
        "case2_a1": ("models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/case2/PK_F1831_CASE_2_A1_PHYS.inp", "6F3B6A2B893F7C09EC53ED38F74F827976CD80F22AD5726868AA6523F34C3033"),
        "case3_a1": ("models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/case3/PK_F1831_CASE_3_A1_PHYS.inp", "2AE60F59B6611D38BF7BC6BFE55258E9F589B0E69E77158ABBC6C264F06D79C4"),
        "case5_a1": ("models/pandey_kumar_mode1/272_f1831_matched_donor_experiment/case5/PK_F1831_CASE_5_A1_PHYS.inp", "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065"),
    }
    for cid, (rel_path, exp_body_sha) in expected_meshes.items():
        abs_path = os.path.join(REPO_ROOT, rel_path)
        assert os.path.exists(abs_path), f"Mesh {cid} at {rel_path} must exist"
        actual_body_sha = sha256_mesh_body(abs_path)
        assert actual_body_sha == exp_body_sha, f"Mesh {cid} body SHA mismatch: expected {exp_body_sha}, got {actual_body_sha}"


def test_image_manifest_file_hashes():
    expected_images = {
        "case1": ("results/figures/fig_f1831_case_1_matched_mesh.png", "8E0665D3A1A9ADEA0AA8F4AE91391D3951D90CD9180D58CC98BC1A74C67D89E0"),
        "case2": ("results/figures/fig_f1831_case_2_matched_mesh.png", "A5B40D10DA9196CFEB04BCE2C5217BA28EA1F2F708FD0863CE63C48C341DA139"),
        "case3": ("results/figures/fig_f1831_case_3_matched_mesh.png", "9D12195BB4FCADA4D8D4C0B31548685CA7A465F7D11E41CB091446C247D34709"),
        "case5": ("results/figures/fig_f1831_case_5_matched_mesh.png", "3D4D01311F0DC9A6154390BA685C2A236CA92680E8AFCC73F61CC0A558501869"),
        "composite": ("results/figures/fig_f1831_matched_donor_synthesis.png", "C3517971343C9F30A46691FDF2F845B4442320999E54FB106B2350AD78163B62"),
    }
    for cid, (rel_path, exp_sha) in expected_images.items():
        abs_path = os.path.join(REPO_ROOT, rel_path)
        assert os.path.exists(abs_path), f"Image {cid} at {rel_path} must exist"
        actual_sha = sha256_file(abs_path)
        assert actual_sha == exp_sha, f"Image {cid} SHA mismatch: expected {exp_sha}, got {actual_sha}"


def test_report_contains_verified_baselines_and_no_false_pass():
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Reconciled Gate 06 baselines
    assert "2.3867x (PASS)" in content
    assert "1.9349x (FAIL)" in content
    assert "1.4462x (FAIL)" in content
    assert "2.1174x (PASS)" in content

    # Check that Cases 2 and 3 F1812 are NOT marked as PASS
    assert "1.9349x (PASS)" not in content
    assert "1.4462x (PASS)" not in content

    # Check Case 1 A.1 element count
    assert "4,384" in content
    assert "8,412" not in content

    # Check commit SHA pinned
    assert "eabb2a884ec955f3dc00ba2a67307e4419f7fa0f" in content
