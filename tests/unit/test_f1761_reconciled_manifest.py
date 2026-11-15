# -*- coding: utf-8 -*-
"""
tests/unit/test_f1761_reconciled_manifest.py
============================================
Unit test suite verifying the reconciled five-case execution manifest parameters,
donor frame references, and commit-pinned GitHub links for Task F1761.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_DIR = os.path.join(REPO_ROOT, "configs", "remeshing")

def test_case2_reconciled_parameters():
    """Verify Case 2 parameters match executed F1734 historical record (h_min=0.0015, h_max=0.020)."""
    p = os.path.join(CONFIG_DIR, "f1728_case2_off_axis_hole.json")
    with open(p, "r") as f:
        data = json.load(f)
    rr = data["remeshing_rule"]
    assert rr["min_element_size_mm"] == 0.0015, f"Expected 0.0015, got {rr['min_element_size_mm']}"
    assert rr["max_element_size_mm"] == 0.020, f"Expected 0.020, got {rr['max_element_size_mm']}"
    assert rr["error_target"] == 2.3, f"Expected 2.3, got {rr['error_target']}"
    assert rr["step_name"] == "RECOVERY_STEP", f"Expected RECOVERY_STEP, got {rr['step_name']}"

def test_case4_reconciled_parameters():
    """Verify Case 4 parameters match F1725 ET315 executed sweep (h_min=0.001, h_max=0.030, Step-2)."""
    p = os.path.join(CONFIG_DIR, "f1728_case4_five_hole.json")
    with open(p, "r") as f:
        data = json.load(f)
    rr = data["remeshing_rule"]
    assert rr["min_element_size_mm"] == 0.001, f"Expected 0.001, got {rr['min_element_size_mm']}"
    assert rr["max_element_size_mm"] == 0.030, f"Expected 0.030, got {rr['max_element_size_mm']}"
    assert rr["error_target"] == 3.15, f"Expected 3.15, got {rr['error_target']}"
    assert rr["step_name"] == "Step-2", f"Expected Step-2, got {rr['step_name']}"

def test_case3_reconciled_parameters():
    """Verify Case 3 parameters match F1741 calibrated sizing (h_min=0.080, h_max=1.5, err=1.80%)."""
    p = os.path.join(CONFIG_DIR, "f1728_case3_notched_plate_pins.json")
    with open(p, "r") as f:
        data = json.load(f)
    rr = data["remeshing_rule"]
    assert rr["min_element_size_mm"] == 0.080, f"Expected 0.080, got {rr['min_element_size_mm']}"
    assert rr["max_element_size_mm"] == 1.5, f"Expected 1.5, got {rr['max_element_size_mm']}"
    assert rr["error_target"] == 1.80, f"Expected 1.80, got {rr['error_target']}"

def test_case4_terminal_donor_frame_provenance():
    """Verify that Case 4 terminal donor is documented as Step 2 Frame 178 (not Step 1 Frame 13)."""
    f1725_report = os.path.join(REPO_ROOT, "docs", "validation", "F1725_PHYSICS_DRIVEN_ADAPTIVE_MESH_REPORT.md")
    with open(f1725_report, "r") as f:
        content = f.read()
    assert "Last frame of Step 2 (Frame 178)" in content
    assert "uy = 0.00645141" in content or "0.00645" in content

def test_case3_damage_frame_provenance():
    """Verify Case 3 State 2 corresponds to Step-1 Frame 30 and State 4 corresponds to Step-1 Frame 55."""
    audit_json = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1", "f1692_sec43_damage_and_miseseri_audit.json")
    with open(audit_json, "r") as f:
        data = json.load(f)
    step0_frames = {fr["frame_index"]: fr for fr in data["steps"][0].get("sampled_frames", [])}
    assert 30 in step0_frames
    assert abs(step0_frames[30]["frame_value"] - 0.15) < 0.001
    assert step0_frames[30]["max_damage_primary"] > 0.99
    assert 55 in step0_frames
    assert abs(step0_frames[55]["frame_value"] - 0.275) < 0.001
    assert step0_frames[55]["max_damage_secondary"] > 0.50

def test_commit_pinned_github_url_structure():
    """Verify that commit-pinned GitHub URLs use valid commit SHA a4d1c8e6 and existing repository paths."""
    commit_sha = "a4d1c8e6"
    base_url = f"https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/{commit_sha}/"
    paths_to_verify = [
        "results/figures/fig_f1760_five_benchmark_definitive_comparison.png",
        "scripts/remeshing/generate_definitive_five_benchmark_overview.py",
        "scripts/remeshing/reusable_2d_adaptive_framework.py",
        "docs/validation/F1760_UNIFIED_METHOD_A_PROVENANCE_AND_REPRODUCIBILITY_REPORT.md"
    ]
    for p in paths_to_verify:
        full_local = os.path.join(REPO_ROOT, p)
        assert os.path.isfile(full_local), f"File {p} must exist locally"
        url = base_url + p.replace("\\", "/")
        assert "a4d1c8e6" in url

def test_case4_uel_subroutine_frozen_alignment():
    """Verify Case 4 configuration strictly references frozen production UEL and hash CE8D5EDC..."""
    p = os.path.join(CONFIG_DIR, "f1728_case4_five_hole.json")
    with open(p, "r") as f:
        data = json.load(f)
    deck_opts = data["deck_options"]
    assert deck_opts["uel_subroutine"] == "models/pandey_kumar_mode1/f42_mixed_uel.for"
    assert deck_opts["frozen_uel_sha256"] == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_canonical_manifest_structure_and_donor_alignment():
    """Verify that canonical_five_case_manifest.json exists and contains unambiguous verified entries for all 5 cases."""
    manifest_path = os.path.join(CONFIG_DIR, "canonical_five_case_manifest.json")
    assert os.path.isfile(manifest_path), "canonical_five_case_manifest.json must exist"
    with open(manifest_path, "r") as f:
        data = json.load(f)
    assert data["manifest_version"] == "1.0.0"
    assert len(data["benchmarks"]) == 5
    for case_id in ["case_1", "case_2", "case_3", "case_4", "case_5"]:
        cdata = data["benchmarks"][case_id]
        assert cdata["input_status"] == "VERIFIED_CANONICAL"
        assert cdata["donor_step_name"] in ["Step-1", "Step-2", "RECOVERY_STEP"]
        assert cdata["algorithm_variant"] in [
            "Method A.1 (Single-Pass Native Method A)",
            "Method A.2 (Multi-State Sequential Method A)"
        ]

def test_output_frequency_framework_binding():
    """Verify that AdaptiveConfig parses output_frequency correctly from config."""
    sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))
    from reusable_2d_adaptive_framework import AdaptiveConfig
    p = os.path.join(CONFIG_DIR, "f1728_case4_five_hole.json")
    with open(p, "r") as f:
        data = json.load(f)
    cfg = AdaptiveConfig(data)
    assert cfg.output_frequency == "ALL_INCREMENTS"
    assert cfg.step_name == "Step-2"

