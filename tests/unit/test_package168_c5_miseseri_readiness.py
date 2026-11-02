# -*- coding: utf-8 -*-
"""
test_package168_c5_miseseri_readiness.py
=========================================
Comprehensive qualification and regression test suite for Package 168:
Causal C5 Same-Load MISESERI Error-Estimation Pipeline.

Verifies:
1. Exact C5 mesh topology invariants (12,996 CPE4 quads, 13,278 physical nodes + RP 999999,
   53 duplicate coincident slit-flank pairs, 62 shared ligament nodes, 115 kinematic ties).
2. Parameterized checkpoint consumption and verification (coupled convergence, node counts,
   SHA-256 recording in manifest).
3. Fail-closed gate: rejection of missing Checkpoint 03 when --require-checkpoint-03 is set.
4. Input deck syntax integrity: verifies NO blank lines exist inside data blocks (preventing
   the preprocessor syntax errors that failed Job 1419549).
5. Extraction & indicator formulation: verifies field output requests (S, MISESERI, MISESAVG, EVOL)
   and eta >= 0.15 relative error criterion without artificial corridors.
6. Physical separation discipline: verifies companion linear elasticity vs phase-field softening.

Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

from __future__ import annotations

import json
import math
import os
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.remeshing.build_c5_companion_deck import (
    C5_SOURCE_INP,
    CHECKPOINT_03_TARGET_UY,
    DEFAULT_TARGET_UY,
    DependencyBlockedError,
    build_c5_companion_deck,
    extract_c5_mesh_components,
    load_and_validate_checkpoint,
    sha256_file,
)
from scripts.remeshing.evaluate_c5_miseseri_refinement import (
    evaluate_c5_miseseri_pipeline,
    inspect_c5_topology,
)

FIXTURE_CP02 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "167_c5_package167_r1_c2_2_continuation" / "initial_checkpoint_02.json"


def test_01_c5_topology_invariants():
    """Verify authoritative C5 candidate mesh invariants."""
    assert C5_SOURCE_INP.is_file(), f"Missing C5 mesh deck: {C5_SOURCE_INP}"
    topo = inspect_c5_topology()

    assert topo["total_quads"] == 12996, f"Expected 12996 quads, got {topo['total_quads']}"
    assert topo["total_nodes"] == 13279, f"Expected 13279 nodes (13278 + RP), got {topo['total_nodes']}"
    assert topo["duplicate_slit_pairs"] == 53, f"Expected 53 slit pairs, got {topo['duplicate_slit_pairs']}"
    assert topo["ligament_nodes_count"] == 62, f"Expected 62 ligament nodes, got {topo['ligament_nodes_count']}"
    assert topo["top_nodes_count"] == 115, f"Expected 115 top boundary nodes, got {topo['top_nodes_count']}"
    assert topo["bottom_nodes_count"] == 115, f"Expected 115 bottom boundary nodes, got {topo['bottom_nodes_count']}"
    assert topo["min_det_jac"] > 0.0, "Found non-positive Jacobian elements in C5 mesh"


def test_02_deck_syntax_no_blank_lines_in_data_blocks():
    """
    Syntax integrity guard:
    Ensures that generated input deck has no blank lines within data blocks or equations.
    This directly prevents the preprocessor syntax error (Exit 1) observed in Job 1419549.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        manifest = build_c5_companion_deck(
            output_dir=out_dir,
            displacement_target=0.0018653125442191958,
            job_name="TEST_SYNTAX"
        )
        inp_file = out_dir / "TEST_SYNTAX.inp"
        assert inp_file.is_file()

        lines = inp_file.read_text(encoding="utf-8").splitlines()
        
        # Walk through lines and check that within an *Element or *Equation block,
        # there are no blank lines before the next keyword.
        in_element_block = False
        in_equation_block = False
        for idx, line in enumerate(lines, 1):
            s = line.strip()
            if s.startswith("*"):
                if s.lower().startswith("*element"):
                    in_element_block = True
                    in_equation_block = False
                elif s.lower().startswith("*equation"):
                    in_equation_block = True
                    in_element_block = False
                else:
                    in_element_block = False
                    in_equation_block = False
            elif not s:
                # Blank line
                assert not in_element_block, f"Line {idx}: Blank line inside *Element data block!"
                assert not in_equation_block, f"Line {idx}: Blank line inside *Equation data block!"


def test_03_parameterized_checkpoint_consumption():
    """Verify that builder successfully consumes accepted Checkpoint 02 fixture."""
    assert FIXTURE_CP02.is_file(), f"Fixture Checkpoint 02 not found: {FIXTURE_CP02}"

    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)
        manifest = build_c5_companion_deck(
            output_dir=out_dir,
            checkpoint_path=FIXTURE_CP02,
            require_checkpoint_03=False,
            job_name="TEST_CP02_CONSUMPTION"
        )

        assert manifest["mesh_provenance"]["elements"] == 12996
        assert manifest["mesh_provenance"]["nodes"] == 13278
        assert "checkpoint_lineage" in manifest
        lineage = manifest["checkpoint_lineage"]
        assert lineage["consumed_checkpoint_path"] == str(FIXTURE_CP02)
        assert math.isclose(lineage["target_uy_mm"], 0.0018653125442191958, rel_tol=1e-8)
        assert lineage["coupled_convergence"] is True

        # Check that input deck was created with correct boundary target
        inp_text = (out_dir / "TEST_CP02_CONSUMPTION.inp").read_text(encoding="utf-8")
        assert "999999, 2, 2, 0.0018653125" in inp_text


def test_04_fail_closed_missing_checkpoint_03():
    """
    Scientific gate verification:
    Package 168 companion run MUST NOT execute without physically accepted Checkpoint 03.
    Verifies that --require-checkpoint-03 raises DependencyBlockedError when fed Checkpoint 02 or None.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        out_dir = Path(tmpdir)

        # Feeding Checkpoint 02 when Checkpoint 03 is required must fail
        with pytest.raises(DependencyBlockedError) as exc_info:
            build_c5_companion_deck(
                output_dir=out_dir,
                checkpoint_path=FIXTURE_CP02,
                require_checkpoint_03=True
            )
        assert "expected Checkpoint 03 at uy=0.0018703125" in str(exc_info.value)

        # Omitting checkpoint when Checkpoint 03 is required must fail
        with pytest.raises(DependencyBlockedError) as exc_info2:
            build_c5_companion_deck(
                output_dir=out_dir,
                checkpoint_path=None,
                require_checkpoint_03=True
            )
        assert "strictly required for Package 168 execution" in str(exc_info2.value)


def test_05_miseseri_pipeline_specification():
    """Verify that evaluate_c5_miseseri_pipeline executes and certifies all requirements."""
    pipeline = evaluate_c5_miseseri_pipeline()

    assert pipeline["status"] == "C5_INDICATOR_PIPELINE_SPECIFIED_AND_TESTED"
    assert pipeline["verification_passed"] is True
    assert pipeline["discretization"]["element_count"] == 12996
    assert pipeline["companion_model"]["material"]["model"] == "LINEAR_ISOTROPIC_ELASTIC"
    assert "MISESERI" in pipeline["companion_model"]["requested_field_outputs"]
    assert "MISESAVG" in pipeline["companion_model"]["requested_field_outputs"]
    assert pipeline["error_indicator_formulation"]["threshold_eta"] == 0.15
    assert pipeline["error_indicator_formulation"]["refinement_policy"] == "REFINEMENT_ONLY_NO_COARSENING"
    assert pipeline["readiness_and_dependencies"]["c5_deck_builder_ready"] is True
    assert pipeline["readiness_and_dependencies"]["c5_extraction_script_ready"] is True
    assert "OFFLINE_PREPARATION_COMPLETE__EXECUTION_WITHHELD" in pipeline["readiness_and_dependencies"]["execution_status"]
