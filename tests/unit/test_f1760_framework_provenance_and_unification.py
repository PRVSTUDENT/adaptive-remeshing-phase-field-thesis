# -*- coding: utf-8 -*-
"""
tests/unit/test_f1760_framework_provenance_and_unification.py
=============================================================
Unit test suite verifying Phase 1 and Phase 2 provenance audit and unified
framework interface compliance across all five benchmark configurations.
"""

import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig, get_geometry_adapter,
    StraightNotchMode1Adapter, OffAxisHoleMode1Adapter,
    NotchedPlateWithPinHolesAdapter, FiveHolePlateAdapter,
    SevenHolePlateAdapter
)

CONFIG_DIR = os.path.join(REPO_ROOT, "configs", "remeshing")

CONFIG_FILES = {
    "case_1": "f1728_case1_mode1_edge_crack.json",
    "case_2": "f1728_case2_off_axis_hole.json",
    "case_3": "f1728_case3_notched_plate_pins.json",
    "case_4": "f1728_case4_five_hole.json",
    "case_5": "f1728_case5_seven_hole.json",
}

EXPECTED_ADAPTERS = {
    "case_1": StraightNotchMode1Adapter,
    "case_2": OffAxisHoleMode1Adapter,
    "case_3": NotchedPlateWithPinHolesAdapter,
    "case_4": FiveHolePlateAdapter,
    "case_5": SevenHolePlateAdapter,
}

EXPECTED_TARGET_ELEMENTS = {
    "case_1": 13941,
    "case_2": 23618,
    "case_3": 12168,
    "case_4": 12944,
    "case_5": 15714,
}

def test_all_five_config_files_exist():
    for case_key, filename in CONFIG_FILES.items():
        full_path = os.path.join(CONFIG_DIR, filename)
        assert os.path.isfile(full_path), f"Missing configuration file for {case_key}: {full_path}"

def test_adaptive_config_parsing_and_adapter_binding():
    for case_key, filename in CONFIG_FILES.items():
        full_path = os.path.join(CONFIG_DIR, filename)
        with open(full_path, "r") as f:
            data = json.load(f)
        cfg = AdaptiveConfig(data)
        assert cfg.case_id == case_key, f"Case ID mismatch in {filename}: {cfg.case_id} vs {case_key}"
        adapter = get_geometry_adapter(cfg)
        expected_cls = EXPECTED_ADAPTERS[case_key]
        assert isinstance(adapter, expected_cls), f"Adapter class mismatch for {case_key}: {type(adapter)} vs {expected_cls}"

def test_case1_f1738_hybrid_corridor_provenance_isolation():
    """Verify that Case 1 F1738 script used manual partitioning and NOT native RemeshingRule."""
    f1738_script = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "226_f1738_case1_ligament_refinement", "run_case1_ligament_remesh.py")
    assert os.path.isfile(f1738_script), f"Missing F1738 script at {f1738_script}"
    with open(f1738_script, "r") as f:
        src = f.read()
    # Confirms manual geometric corridor partitioning
    assert "PartitionFaceByShortestPath" in src
    assert "seedEdgeBySize" in src
    assert "w_corr = 0.020" in src  # Corresponds to y in [0.48, 0.52]
    # Confirms NO native adaptive remeshing was called in F1738
    assert "adaptiveRemesh" not in src
    assert "RemeshingRule" not in src

def test_case2_f1734_reusable_framework_provenance():
    """Verify that Case 2 F1734 script invoked reusable_2d_adaptive_framework.py."""
    f1734_pbs = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "224_f1734_case2_distal_refinement", "submit_f1734_case2_distal_refinement.pbs")
    assert os.path.isfile(f1734_pbs), f"Missing F1734 PBS script at {f1734_pbs}"
    with open(f1734_pbs, "r") as f:
        src = f.read()
    assert "reusable_2d_adaptive_framework.py" in src
    assert "abaqus cae noGUI" in src

def test_case4_and_case5_native_remeshing_provenance():
    """Verify that Case 4 and 5 used native RemeshingRule with MISESERI variable."""
    f1725_script = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_f1725_physics_study.py")
    f1726_script = os.path.join(REPO_ROOT, "scripts", "remeshing", "run_seven_hole_fine_parity.py")
    assert os.path.isfile(f1725_script)
    assert os.path.isfile(f1726_script)
    for p in [f1725_script, f1726_script]:
        with open(p, "r") as f:
            src = f.read()
        assert "RemeshingRule" in src
        assert "adaptiveRemesh" in src
        assert "MISESERI" in src
