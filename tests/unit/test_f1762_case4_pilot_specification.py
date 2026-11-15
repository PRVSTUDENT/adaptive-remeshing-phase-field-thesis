# -*- coding: utf-8 -*-
"""
tests/unit/test_f1762_case4_pilot_specification.py
==================================================
Unit test suite verifying the Case 4 single-pass adaptive remeshing pilot
specification, geometry adapter, configuration binding, and frozen UEL integrity.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_DIR = os.path.join(REPO_ROOT, "configs", "remeshing")
DOCS_DIR = os.path.join(REPO_ROOT, "docs", "validation")

sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))
from reusable_2d_adaptive_framework import AdaptiveConfig, FiveHolePlateAdapter

def test_case4_pilot_specification_report_exists():
    """Verify that F1762_CASE4_PILOT_SPECIFICATION_REPORT.md exists and contains required sections."""
    rep_path = os.path.join(DOCS_DIR, "F1762_CASE4_PILOT_SPECIFICATION_REPORT.md")
    assert os.path.isfile(rep_path), "F1762 pilot specification report must exist"
    with open(rep_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "F1762-CASE4-COMMON-FRAMEWORK-PILOT-SPECIFICATION" in content
    assert "F1761-R01" in content
    assert "F1761-R02" in content
    assert "F1761-R03" in content
    assert "12,944" in content
    assert "ALL_INCREMENTS" in content

def test_case4_pilot_configuration_binding():
    """Verify that f1728_case4_five_hole.json binds cleanly to AdaptiveConfig with exact parameters."""
    p = os.path.join(CONFIG_DIR, "f1728_case4_five_hole.json")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = AdaptiveConfig(data)
    assert cfg.case_id == "case_4"
    assert cfg.geometry_type == "FIVE_HOLE_PLATE"
    assert cfg.output_frequency == "ALL_INCREMENTS"
    assert cfg.step_name == "Step-2"
    assert abs(cfg.error_target - 3.15) < 1e-4
    assert abs(cfg.min_h - 0.001) < 1e-4
    assert abs(cfg.max_h - 0.030) < 1e-4
    assert cfg.coarsening_factor == "DEFAULT_LIMIT"
    assert cfg.expected_uel_sha256.upper() == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_case4_adapter_geometry_definitions():
    """Verify that FiveHolePlateAdapter defines 3 internal circular voids and 2 boundary arc cutouts."""
    p = os.path.join(CONFIG_DIR, "f1728_case4_five_hole.json")
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)
    cfg = AdaptiveConfig(data)
    adapter = FiveHolePlateAdapter(cfg)
    holes = adapter.get_hole_definitions()
    assert len(holes) == 3, f"Expected 3 circular voids, got {len(holes)}"
    # Verify radii
    radii = sorted([h[2] for h in holes])
    assert abs(radii[0] - 0.05) < 1e-4
    assert abs(radii[1] - 0.075) < 1e-4
    assert abs(radii[2] - 0.10) < 1e-4
    # Verify edge cutouts
    assert len(cfg.edge_cutouts) == 2, f"Expected 2 edge cutouts, got {len(cfg.edge_cutouts)}"

def test_case4_canonical_manifest_alignment():
    """Verify that canonical_five_case_manifest.json specifies Step-2, Frame 178, and ALL_INCREMENTS for Case 4."""
    m_path = os.path.join(CONFIG_DIR, "canonical_five_case_manifest.json")
    with open(m_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    c4 = manifest["benchmarks"]["case_4"]
    assert c4["donor_step_name"] == "Step-2"
    assert c4["donor_frame_index"] == 178
    assert "ALL_INCREMENTS" in c4["donor_frame_selection_mechanism"]
    assert c4["algorithm_variant"] == "Method A.1 (Single-Pass Native Method A)"
    assert c4["input_status"] == "VERIFIED_CANONICAL"

def test_frozen_uel_subroutine_hash():
    """Verify that f42_mixed_uel.for matches the bitwise frozen SHA-256 hash CE8D5EDC..."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), "f42_mixed_uel.for must exist"
    h = hashlib.sha256(open(uel_path, "rb").read()).hexdigest().upper()
    assert h == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
