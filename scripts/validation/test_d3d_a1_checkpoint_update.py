#!/usr/bin/env python3
"""Synthetic and fixture tests for the D3D-A1 offline checkpoint update."""

from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.solve_d3d_a1_checkpoint_obstacle import (  # noqa: E402
    solve_primal_dual,
)
from scripts.validation.validate_d3d_a1_checkpoint_update import (  # noqa: E402
    evaluate,
    prepare_package,
)


def write_csv(path: Path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fixture():
    source = {
        "initial_active_nodes": 6446,
        "initial_free_nodes": 155,
        "negative_active_multipliers": 30,
        "endpoint_union_used_as_release_set": False,
    }
    kkt = {
        "source_phase_coverage": 6601,
        "source_H_coverage": 25600,
        "final_H_coverage": 25600,
        "H_changes": 0,
        "non_positive_detJ": 0,
        "deterministic_convergence_status": True,
        "free_residual_infinity_norm": 1.0e-12,
        "minimum_active_multiplier": -9.0e-9,
        "active_bound_error": 0.0,
        "minimum_lower_bound_margin": 0.0,
        "phase_decrease_violations": 0,
        "lower_bound_violations": 0,
        "state_reset": False,
        "spatial_variation_retained": True,
    }
    functional = {"functional_nonincrease": True, "functional_change": -1.0e-12}
    updated = [{"d_D3D_A1": "0.2", "d_F3": "0.1"}] * 6601
    history = [{"H_F3": "1.0"}] * 25600
    return source, kkt, functional, updated, history


def assert_fails(mutator, expected):
    source, kkt, functional, updated, history = fixture()
    mutator(source, kkt, functional, updated, history)
    _, failures = evaluate(source, kkt, functional, updated, history)
    assert expected in failures, (expected, failures)


def test_actual_seed_and_endpoint_guard():
    path = REPO_ROOT / "runs/hpc/stage_d3/fracture_continuation/d3d_active_set_segment/D3D_ACTIVE_MULTIPLIER_CANDIDATES.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    seeds = {int(r["node"]) for r in rows if r["frame_tag"] == "F4_segment_initial"}
    endpoint = {int(r["node"]) for r in rows if r["frame_tag"] == "F4_segment_end"}
    assert len(seeds) == 30
    assert len(endpoint) == 3157
    assert seeds != endpoint


def test_solver_tie_break_and_release():
    k = csr_matrix(np.eye(3))
    lower = np.array([1.0, 1.0, 1.0])
    # residual at lower = [0, -0.5, 0]; only node 1 should release.
    f = np.array([1.0, 1.5, 1.0])
    d, active, _, converged, _ = solve_primal_dual(
        k, f, lower, np.ones(3, dtype=bool), max_iterations=10
    )
    assert converged
    assert active.tolist() == [True, False, True]
    assert np.allclose(d, [1.0, 1.5, 1.0])


def test_gate_failures_and_pass():
    assert_fails(
        lambda s, k, f, u, h: k.update(source_phase_coverage=6600),
        "source_phase_coverage",
    )
    assert_fails(
        lambda s, k, f, u, h: k.update(source_H_coverage=25599),
        "source_H_coverage",
    )
    assert_fails(
        lambda s, k, f, u, h: k.update(minimum_active_multiplier=-1.1e-8),
        "active_multiplier",
    )
    assert_fails(
        lambda s, k, f, u, h: k.update(free_residual_infinity_norm=1.1e-8),
        "free_residual",
    )
    assert_fails(
        lambda s, k, f, u, h: u.__setitem__(0, {"d_D3D_A1": "0.0", "d_F3": "0.1"}),
        "all_final_d_above_F3",
    )
    assert_fails(
        lambda s, k, f, u, h: k.update(H_changes=1),
        "H_unchanged",
    )
    assert_fails(
        lambda s, k, f, u, h: f.update(functional_nonincrease=False, functional_change=1e-5),
        "functional_nonincrease",
    )
    source, kkt, functional, updated, history = fixture()
    _, failures = evaluate(source, kkt, functional, updated, history)
    assert failures == []


def test_repeat_package_hashes():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        target = root / "target"
        package_a = root / "package_a"
        package_b = root / "package_b"
        target.mkdir()
        write_csv(
            target / "D3D_A1_UPDATED_NODAL_D.csv",
            ["node", "x", "y", "d_D3D_A1"],
            [{"node": 1, "x": 0, "y": 0, "d_D3D_A1": 0.2}],
        )
        write_csv(
            target / "D3D_A1_SOURCE_NODAL_LOWER_BOUND.csv",
            ["node", "x", "y", "d_lower_bound_F3"],
            [{"node": 1, "x": 0, "y": 0, "d_lower_bound_F3": 0.1}],
        )
        write_csv(
            target / "D3D_A1_SOURCE_IP_H.csv",
            ["element", "integration_point", "H_F3"],
            [{"element": 1, "integration_point": 1, "H_F3": 0.3}],
        )
        write_csv(
            target / "D3D_A1_UPDATED_ACTIVE_SET_BY_NODE.csv",
            ["node", "x", "y", "active_lower_bound", "d_D3D_A1", "d_lb_F3",
             "bound_margin", "residual_Kd_minus_f"],
            [{
                "node": 1, "x": 0, "y": 0, "active_lower_bound": False,
                "d_D3D_A1": 0.2, "d_lb_F3": 0.1, "bound_margin": 0.1,
                "residual_Kd_minus_f": 0.0,
            }],
        )
        manifest_a, _ = prepare_package(target, package_a)
        manifest_b, _ = prepare_package(target, package_b)
        assert manifest_a["file_sha256"] == manifest_b["file_sha256"]


def main():
    tests = [
        test_actual_seed_and_endpoint_guard,
        test_solver_tie_break_and_release,
        test_gate_failures_and_pass,
        test_repeat_package_hashes,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print("D3D_A1_TESTS_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
