# -*- coding: utf-8 -*-
"""
tests/test_f1859_suite.py
=========================
Unit tests for Task F1859 Four-Benchmark Reference Comparison Suite.
"""

import os
import json
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
SUITE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "286_f1859_four_benchmark_reference_comparison")

def test_suite_receipt_exists_and_valid():
    receipt_p = os.path.join(SUITE_DIR, "f1859_suite_receipt.json")
    assert os.path.exists(receipt_p), "Missing f1859_suite_receipt.json"
    with open(receipt_p, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["task_id"] == "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON"
    assert len(data["jobs"]) == 8
    assert "step_0_f1828_check" in data
    assert data["step_0_f1828_check"]["status"] == "COMPLETED"
    assert data["step_0_f1828_check"]["usable_f1828_results_found"] is False

def test_submission_receipt_records_all_8_jobs():
    sub_p = os.path.join(SUITE_DIR, "f1859_submission_receipt.json")
    assert os.path.exists(sub_p), "Missing f1859_submission_receipt.json"
    with open(sub_p, "r", encoding="utf-8-sig") as f:
        jobs = json.load(f)
    assert len(jobs) == 8
    job_names = [j["job_name"] for j in jobs]
    expected_names = [
        "F1859_REF_C1", "F1859_REF_C2", "F1859_REF_C3", "F1859_REF_C5",
        "F1859_J2_C1", "F1859_J2_C2", "F1859_J2_C3", "F1859_J2_C5"
    ]
    assert sorted(job_names) == sorted(expected_names)
    for j in jobs:
        assert j["pbs_job_id"].endswith(".mmaster02")
        assert j["queue"] == "entry_imfdfkmq"
        assert j["walltime"] == "48:00:00"
        assert j["cpus"] == 8

def test_reference_mesh_target_accuracy():
    receipt_p = os.path.join(SUITE_DIR, "f1859_suite_receipt.json")
    with open(receipt_p, "r", encoding="utf-8") as f:
        data = json.load(f)
    ref_meshes = data["step_1_reference_meshes"]
    assert abs(ref_meshes["case_1"]["difference_percent"]) <= 1.0  # +0.14%
    assert abs(ref_meshes["case_2"]["difference_percent"]) <= 2.0  # +1.47%
    assert abs(ref_meshes["case_3"]["difference_percent"]) <= 1.0  # -0.48%
    assert abs(ref_meshes["case_5"]["difference_percent"]) <= 3.0  # +2.47%

def test_summary_json_valid():
    sum_p = os.path.join(REPO_ROOT, "results", "validation", "f1859_four_benchmark_reference_comparison_summary.json")
    assert os.path.exists(sum_p), "Missing summary JSON"
    with open(sum_p, "r", encoding="utf-8") as f:
        sum_data = json.load(f)
    assert sum_data["task_id"] == "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON"
    assert sum_data["pbs_accounting"]["submissions_consumed"] == 8
    assert sum_data["pbs_accounting"]["current_cumulative"] == 45
    assert len(sum_data["benchmarks"]) == 4

def test_image_manifest_and_figures_exist():
    img_p = os.path.join(REPO_ROOT, "results", "validation", "f1859_image_manifest.json")
    assert os.path.exists(img_p), "Missing image manifest"
    with open(img_p, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert len(manifest["images"]) == 9
    for item in manifest["images"]:
        p = os.path.join(REPO_ROOT, item["relative_path"])
        assert os.path.exists(p), f"Missing image file: {p}"
        assert os.path.getsize(p) == item["bytes"]

def test_report_exists_and_non_empty():
    rep_p = os.path.join(REPO_ROOT, "docs", "validation", "F1859_FOUR_BENCHMARK_REFERENCE_COMPARISON_REPORT.md")
    assert os.path.exists(rep_p), "Missing report"
    with open(rep_p, "r", encoding="utf-8") as f:
        text = f.read()
    assert len(text) > 3000
    assert "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON" in text
    assert "1424411.mmaster02" in text
    assert "1424418.mmaster02" in text
    assert "QUEUED / RUNNING" in text

def test_active_task_accounting():
    task_p = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_p, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    assert task["task_id"] == "F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON"
    assert task["submissions_consumed"] == 8
    assert task["cumulative_pbs_submissions"] == 45
    assert task["max_new_pbs_submissions"] == 8
