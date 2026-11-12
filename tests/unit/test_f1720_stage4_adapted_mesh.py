"""
tests/unit/test_f1720_stage4_adapted_mesh.py
============================================
Unit tests for Task F1720 Stage 4: Native Abaqus CAE Adaptive Remeshing
Reproduction of the Five-Hole Benchmark (Target: 12,944 Elements).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1720_adapted_mesh_metrics.json")
ADAPTED_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh")
PHYS_INP = os.path.join(ADAPTED_DIR, "PK_F1720_ADAPTED_PHYS.inp")


@pytest.fixture(scope="module")
def mesh_metrics():
    assert os.path.exists(METRICS_JSON), f"Metrics JSON missing: {METRICS_JSON}"
    with open(METRICS_JSON, "r") as f:
        return json.load(f)


def test_physical_adapted_inp_exists():
    """Verify that the primary physical adapted mesh input deck exists and is non-empty."""
    assert os.path.exists(PHYS_INP), f"Physical adapted INP missing: {PHYS_INP}"
    assert os.path.getsize(PHYS_INP) > 100 * 1024, "Adapted INP size too small (< 100 KB)"


def test_target_element_count_parity(mesh_metrics):
    """
    CRITICAL ACCEPTANCE GATE:
    Verify that the selected best candidate reproduces the published 12,944 target
    within a strict +/- 5% tolerance.
    """
    best_m = mesh_metrics["best_candidate_metrics"]
    n_elems = best_m["num_elements"]
    target = mesh_metrics["published_target_elements"]  # 12,944

    diff_pct = abs(n_elems - target) / float(target) * 100.0
    assert diff_pct < 5.0, f"Element count {n_elems} deviates by {diff_pct:.2f}% from target {target} (limit 5%)"
    # For ET350, diff is +1.69% (13,163 elements)
    assert 12000 <= n_elems <= 14000, f"Element count {n_elems} outside valid range [12000, 14000]"


def test_positive_jacobians_and_quality(mesh_metrics):
    """Verify that all elements have positive Jacobians and valid aspect ratios."""
    best_m = mesh_metrics["best_candidate_metrics"]
    assert best_m["positive_jacobians"] is True, "Adapted mesh contains negative or zero Jacobians"
    assert best_m["ar_max"] < 3.0, f"Maximum aspect ratio {best_m['ar_max']:.2f} exceeds threshold 3.0"
    assert best_m["ar_mean"] < 1.5, f"Mean aspect ratio {best_m['ar_mean']:.2f} exceeds threshold 1.5"


def test_quad_dominance(mesh_metrics):
    """Verify that the adapted mesh is overwhelmingly quad-dominated (> 95% quads)."""
    best_m = mesh_metrics["best_candidate_metrics"]
    assert best_m["quad_percentage"] > 95.0, f"Quad percentage {best_m['quad_percentage']:.2f}% is below 95%"


def test_fracture_ligament_resolution(mesh_metrics):
    """
    CRITICAL ACCEPTANCE GATE:
    Verify that 100% of elements in the critical fracture ligament satisfy
    h <= l0/2 = 0.004 mm to guarantee objective phase-field regularization.
    """
    best_m = mesh_metrics["best_candidate_metrics"]
    assert best_m["pct_le_l0_in_ligament"] == 100.0, "Not all ligament elements satisfy h <= l0"
    assert best_m["pct_le_half_l0_in_ligament"] == 100.0, "Not all ligament elements satisfy h <= l0/2"
    assert best_m["ligament_h3_h4_min_h"] >= 0.0010, "Minimum element size violated user floor of 0.001 mm"
