#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Package 62 Cycle 4 Qualification.
Verifies Cycle 4 native mesh topology, frozen UEL subroutine integrity,
manifest parameters, and transfer metrics.
"""

import sys
import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_01_cycle4_native_mesh_topology():
    raw_inp = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle4_continuation" / "M1_CYCLE4_RAW_ADAPT_2PCT.inp"
    assert raw_inp.exists(), f"Raw adapted mesh missing: {raw_inp}"

    summary_file = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle4_continuation" / "ADAPTIVE_REMESH_CYCLE4_RESULT_2PCT.json"
    assert summary_file.exists(), f"Remesh summary missing: {summary_file}"

    with open(summary_file, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["status"] == "NATIVE_ADAPTIVE_REMESH_CYCLE4_SUCCESS"
    assert summary["adapted_elements"] == 29293
    assert summary["adapted_nodes"] == 29210
    assert summary["adapted_quads"] == 28493
    assert summary["adapted_tris"] == 800

def test_02_package_62_frozen_subroutine():
    uel_file = REPO_ROOT / "models" / "pandey_kumar_mode1" / "62_method_c_stage_c1_2_cycle4_continuation" / "f42_mixed_uel.for"
    if uel_file.exists():
        sha = hashlib.sha256(uel_file.read_bytes()).hexdigest().lower()
        assert sha == FROZEN_UEL_SHA, f"Frozen UEL subroutine altered: {sha}"

def test_03_package_62_manifest_structure():
    manifest_file = REPO_ROOT / "models" / "pandey_kumar_mode1" / "62_method_c_stage_c1_2_cycle4_continuation" / "METHOD_C_STAGE_C1_2_CYCLE4_AUTHORIZATION.json"
    assert manifest_file.exists(), f"Manifest missing: {manifest_file}"
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["scientific_scope"] == "MODE1"
    assert manifest["technical_stage"] == "C1-2"
    assert manifest["jobs"][0]["id"] == "M1_MC_STAGE_C1_2_CYCLE4_CONT"
    assert manifest["jobs"][0]["memory_gb"] <= 16
    assert manifest["jobs"][0]["cpus"] == 1

def test_04_gate_6c_transfer_metrics_pass():
    metrics_file = REPO_ROOT / "models" / "pandey_kumar_mode1" / "62_method_c_stage_c1_2_cycle4_continuation" / "STAGE_C1_2_CYCLE4_TRANSFER_METRICS.json"
    assert metrics_file.exists(), f"Metrics file missing: {metrics_file}"
    with open(metrics_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    for k in [
        "criterion_1_displacement_l2",
        "criterion_2_peak_damage",
        "criterion_3_integrated_damage",
        "criterion_4_history_non_negativity",
        "criterion_5_boundary_force_continuity",
        "criterion_6_internal_energy",
        "criterion_7_global_energy_residual"
    ]:
        assert metrics[k]["verdict"] == "PASS", f"Gate 6C criterion {k} failed: {metrics[k]}"

def test_05_package_62_deck_lineage_and_size():
    deck_file = REPO_ROOT / "models" / "pandey_kumar_mode1" / "62_method_c_stage_c1_2_cycle4_continuation" / "M1_MC_STAGE_C1_2_CYCLE4_CONT.inp"
    assert deck_file.exists(), f"Continuation deck missing: {deck_file}"
    size = deck_file.stat().st_size
    assert size > 15_000_000, f"Deck size smaller than expected: {size} bytes"
    assert hashlib.sha256(deck_file.read_bytes()).hexdigest().lower() == "37399e4d957441946c5ecf272b154a479d3534454cb78d0411c35b3b7534a7cf"
