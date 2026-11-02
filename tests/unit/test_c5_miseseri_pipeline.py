#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_c5_miseseri_pipeline.py
============================
Unit tests verifying the C5 companion continuum deck builder, extraction script,
and indicator-pipeline specification for causal C5->C6 adaptive remeshing.

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
COMPANION_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "168_c5_companion_miseseri"
COMPANION_INP = COMPANION_DIR / "M1_C5_COMPANION_MISESERI.inp"
COMPANION_MANIFEST = COMPANION_DIR / "PACKAGE_MANIFEST.json"
SPEC_JSON = REPO_ROOT / "results" / "validation" / "c5_miseseri_pipeline_specification.json"
BUILDER_PY = REPO_ROOT / "scripts" / "remeshing" / "build_c5_companion_deck.py"
EXTRACTOR_PY = REPO_ROOT / "scripts" / "remeshing" / "extract_c5_miseseri_distribution.py"


def test_c5_companion_deck_integrity():
    assert COMPANION_INP.is_file(), f"Missing companion deck: {COMPANION_INP}"
    assert COMPANION_MANIFEST.is_file(), f"Missing companion manifest: {COMPANION_MANIFEST}"

    with COMPANION_INP.open("r", encoding="utf-8") as f:
        text = f.read()

    # Discretization invariants
    assert "*Element, type=CPE4, elset=ALL_QUADS" in text
    assert "*Solid Section, elset=ALL_QUADS, material=STEEL" in text
    assert "210.0, 0.3" in text
    assert "*Step, name=STATIC_ELASTIC, perturb" in text
    assert "*Static" in text
    assert "S, MISESERI, MISESAVG, EVOL" in text
    assert "N_PIN, 1, 1, 0.0" in text
    assert "N_BOTTOM, 2, 2, 0.0" in text
    assert "999999, 1, 1, 0.0" in text
    assert "999999, 2, 2, 0.0018603125" in text  # Default fixture load
    assert "*Equation" in text


def test_c5_pipeline_specification_json():
    assert SPEC_JSON.is_file(), f"Missing specification JSON: {SPEC_JSON}"
    spec = json.loads(SPEC_JSON.read_text(encoding="utf-8"))

    assert spec["schema"] == 1
    assert spec["status"] == "C5_INDICATOR_PIPELINE_SPECIFIED_AND_TESTED"
    assert spec["verification_passed"] is True

    disc = spec["discretization"]
    assert disc["element_count"] == 12996
    assert disc["node_count"] == 13279  # 13,278 + RP 999999
    assert disc["duplicate_slit_pairs"] == 53
    assert disc["ligament_nodes"] == 62
    assert disc["kinematic_tie_count"] == 115
    assert disc["jacobian_validity"] is True

    # Error indicator formulation
    eif = spec["error_indicator_formulation"]
    assert eif["threshold_eta"] == 0.15
    assert eif["refinement_policy"] == "REFINEMENT_ONLY_NO_COARSENING"

    # Physical separation discipline
    psd = spec["physical_separation_discipline"]
    assert "linear-elastic, intact continuum" in psd["companion_vs_phase_field"]["companion_continuum"].lower()
    assert "damage softening" in psd["companion_vs_phase_field"]["equivalence_caution"].lower()
    assert psd["chronological_causality"]["status"] == "STRICTLY_CAUSAL"


def test_pipeline_scripts_exist():
    assert BUILDER_PY.is_file(), f"Missing builder script: {BUILDER_PY}"
    assert EXTRACTOR_PY.is_file(), f"Missing extractor script: {EXTRACTOR_PY}"
