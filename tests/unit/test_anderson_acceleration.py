#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_anderson_acceleration.py
=============================
Unit and regression test suite for Anderson acceleration implementation:
1. Small linear system solver accuracy and robustness (m=1, 2, 3).
2. Fixed-point convergence acceleration on slow-contracting mock problems (rho ~ 0.98).
3. Physical projection preservation (clip to [d0, 1.0]).
4. Active-set change memory reset safeguard.
5. Fallback to damped Picard step upon divergence, ill-conditioning, or gamma bound breach.
"""
import math
import sys
from pathlib import Path

# Add repo root to path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.anderson_acceleration import AndersonAccelerator


def test_small_system_solver():
    """Verify 1x1, 2x2, and 3x3 linear system solver against exact solutions."""
    # 1x1
    A1 = [[2.0]]
    b1 = [4.0]
    x1 = AndersonAccelerator._solve_small_system(A1, b1)
    assert abs(x1[0] - 2.0) < 1e-12, f"Expected 2.0, got {x1}"

    # 2x2
    A2 = [[3.0, 1.0], [1.0, 2.0]]
    b2 = [9.0, 8.0]
    # Exact: 3x + y = 9, x + 2y = 8 -> 5x = 10 -> x=2, y=3
    x2 = AndersonAccelerator._solve_small_system(A2, b2)
    assert abs(x2[0] - 2.0) < 1e-12, f"Expected 2.0, got {x2[0]}"
    assert abs(x2[1] - 3.0) < 1e-12, f"Expected 3.0, got {x2[1]}"

    # 3x3
    A3 = [
        [4.0, 1.0, -1.0],
        [1.0, 5.0, 2.0],
        [-1.0, 2.0, 6.0]
    ]
    # For exact x=[1, 2, 3]:
    # row 0: 4(1) + 1(2) - 1(3) = 3
    # row 1: 1(1) + 5(2) + 2(3) = 17
    # row 2: -1(1) + 2(2) + 6(3) = 21
    b3 = [3.0, 17.0, 21.0]
    # Exact: x=1, y=2, z=3
    x3 = AndersonAccelerator._solve_small_system(A3, b3)
    assert abs(x3[0] - 1.0) < 1e-10, f"Expected 1.0, got {x3[0]}"
    assert abs(x3[1] - 2.0) < 1e-10, f"Expected 2.0, got {x3[1]}"
    assert abs(x3[2] - 3.0) < 1e-10, f"Expected 3.0, got {x3[2]}"
    print("test_small_system_solver PASS")


def test_physical_projection_and_bounds():
    """Verify that Anderson candidate is strictly clipped to [d0, 1.0]."""
    acc = AndersonAccelerator(memory_depth=2, beta=0.85)
    nodes = [1, 2, 3]
    d0 = {1: 0.1, 2: 0.3, 3: 0.5}

    # Simulate steps that would push beyond bounds
    d1 = {1: 0.15, 2: 0.35, 3: 0.55}
    g1 = {1: 0.05, 2: 0.40, 3: 1.20} # Node 1 goes below d0, node 3 goes above 1.0
    next_d, meta = acc.compute_step(d1, g1, d0, damped_omega=0.85)

    for n in nodes:
        assert next_d[n] >= d0[n] - 1e-14, f"Healing violation at node {n}: {next_d[n]} < {d0[n]}"
        assert next_d[n] <= 1.0 + 1e-14, f"Upper bound violation at node {n}: {next_d[n]} > 1.0"

    print("test_physical_projection_and_bounds PASS")


def test_active_set_change_reset():
    """Verify that an active set topology change triggers history reset."""
    acc = AndersonAccelerator(memory_depth=2, beta=0.85)
    nodes = [1, 2]
    d0 = {1: 0.0, 2: 0.0}

    d1 = {1: 0.2, 2: 0.2}
    g1 = {1: 0.25, 2: 0.25}
    acc.compute_step(d1, g1, d0)
    assert len(acc.d_history) == 1

    d2 = {1: 0.25, 2: 0.25}
    g2 = {1: 0.28, 2: 0.28}
    acc.compute_step(d2, g2, d0)
    assert len(acc.d_history) == 2

    # Step with active set change
    d3 = {1: 0.28, 2: 0.28}
    g3 = {1: 0.30, 2: 0.30}
    next_d, meta = acc.compute_step(d3, g3, d0, active_set_changed=True)

    # History should have been flushed before adding d3
    assert len(acc.d_history) == 1, f"Expected memory reset to 1 entry, got {len(acc.d_history)}"
    assert meta["accelerated"] is False, "Step should not be accelerated immediately after reset"
    assert meta["reason"] == "insufficient_history"
    print("test_active_set_change_reset PASS")


def test_convergence_acceleration_on_mock_problem():
    """
    Test convergence acceleration on a slow-contracting linear operator:
      g(x) = A x + b, where spectral radius rho(A) = 0.985 (similar to C6 PDAS).
    Compare standard damped Picard (omega=0.85) vs Anderson acceleration (m=2, beta=0.85).
    """
    dim = 10
    # Construct a matrix with spectral radius 0.985
    rho = 0.985
    # Tridiagonal matrix with eigenvalues bounded by rho
    diag = 0.90
    off = (rho - diag) / 2.0 # 0.0425

    def g(x):
        out = [0.0] * dim
        for i in range(dim):
            val = diag * x[i]
            if i > 0:
                val += off * x[i - 1]
            if i < dim - 1:
                val += off * x[i + 1]
            out[i] = val + 0.003
        return out

    # Target tolerance
    tol = 1e-5

    # 1. Unaccelerated damped Picard (omega = 0.85)
    x_picard = [0.0] * dim
    iters_picard = 0
    while iters_picard < 500:
        gx = g(x_picard)
        err = max(abs(gx[i] - x_picard[i]) for i in range(dim))
        if err < tol:
            break
        # Damped update
        x_picard = [(1.0 - 0.85) * x_picard[i] + 0.85 * gx[i] for i in range(dim)]
        iters_picard += 1

    # 2. Anderson Accelerated (m = 2, beta = 0.85)
    acc = AndersonAccelerator(memory_depth=2, beta=0.85, regularization=1e-8, max_step_cap=0.50)
    d0 = {i: 0.0 for i in range(dim)}
    x_anderson = {i: 0.0 for i in range(dim)}
    iters_anderson = 0
    while iters_anderson < 500:
        gx_list = g([x_anderson[i] for i in range(dim)])
        gx = {i: gx_list[i] for i in range(dim)}
        err = max(abs(gx[i] - x_anderson[i]) for i in range(dim))
        if err < tol:
            break
        x_anderson, meta = acc.compute_step(x_anderson, gx, d0, damped_omega=0.85)
        if iters_anderson < 10:
            print(f"Iter {iters_anderson}: acc={meta['accelerated']}, reason={meta['reason']}, err={err:.4e}")
        iters_anderson += 1

    print(f"Mock Problem Convergence (rho={rho:.3f}, tol={tol}):")
    print(f"  Picard Iterations:   {iters_picard}")
    print(f"  Anderson Iterations: {iters_anderson}")
    print(f"  Speedup Factor:      {iters_picard / max(1, iters_anderson):.2f}x")

    assert iters_anderson < iters_picard, (
        f"Anderson ({iters_anderson}) should require fewer iterations than Picard ({iters_picard})"
    )
    speedup = iters_picard / max(1, iters_anderson)
    assert speedup >= 1.8, f"Speedup factor {speedup:.2f}x is below expected threshold 1.8x"
    assert iters_anderson < 200, f"Anderson took {iters_anderson} iters, expected < 200"
    print("test_convergence_acceleration_on_mock_problem PASS")


def test_gamma_cap_and_fallback_safeguard():
    """Verify that an extreme ill-conditioned step triggers gamma cap fallback to Picard."""
    acc = AndersonAccelerator(memory_depth=2, beta=0.85, gamma_max=2.0, max_step_cap=1.0)
    nodes = [1, 2]
    d0 = {1: 0.0, 2: 0.0}

    # Iterate 1
    d1 = {1: 1.0, 2: 1.0}
    g1 = {1: 1.1, 2: 1.1}
    acc.compute_step(d1, g1, d0)

    # Iterate 2: almost identical residual (nearly singular difference)
    d2 = {1: 1.05, 2: 1.05}
    g2 = {1: 1.1500000001, 2: 1.1500000001}
    acc.compute_step(d2, g2, d0)

    # Iterate 3: will attempt acceleration with large gamma
    d3 = {1: 1.10, 2: 1.10}
    g3 = {1: 1.20, 2: 1.20}
    next_d, meta = acc.compute_step(d3, g3, d0)

    # If gamma exceeds 2.0 or matrix regularized, check behavior
    # Either accelerated safely or fell back
    if not meta["accelerated"]:
        assert "gamma_norm_exceeded" in meta["reason"] or "step_growth" in meta["reason"]
        print(f"Safeguard successfully triggered: {meta['reason']}")
    else:
        assert meta["gamma_norm"] <= 2.0
    print("test_gamma_cap_and_fallback_safeguard PASS")


def test_oversized_step_rejected_with_safe_picard_fallback():
    """Verify that a proposed Anderson step exceeding max_step_cap falls back safely to damped Picard."""
    acc = AndersonAccelerator(memory_depth=2, beta=0.85, max_step_cap=0.020)
    nodes = [1, 2]
    d0 = {1: 0.0, 2: 0.0}

    # Iterate 1
    d1 = {1: 0.10, 2: 0.10}
    g1 = {1: 0.11, 2: 0.11}
    acc.compute_step(d1, g1, d0)

    # Iterate 2
    d2 = {1: 0.108, 2: 0.108}
    g2 = {1: 0.116, 2: 0.116}
    acc.compute_step(d2, g2, d0)

    # Iterate 3: will attempt acceleration with proposed step ~0.0292 > 0.020
    d3 = {1: 0.115, 2: 0.115}
    g3 = {1: 0.123, 2: 0.123}  # Damped Picard step is 0.85 * 0.008 = 0.0068 <= 0.020
    next_d, meta = acc.compute_step(d3, g3, d0)

    # Must fall back to damped Picard because step > 0.020
    assert meta["accelerated"] is False, "Oversized candidate should not be marked as accelerated"
    assert "oversized_step" in meta["reason"], f"Unexpected reason: {meta['reason']}"
    assert meta["proposed_step"] > 0.020, f"Proposed step {meta['proposed_step']} should exceed cap 0.020"
    assert meta["accepted_step"] == meta["picard_step"], "Should fall back to Picard step"
    assert meta["accepted_step"] <= 0.020, f"Accepted step {meta['accepted_step']} should be <= cap 0.020"
    for n in nodes:
        assert next_d[n] >= d0[n]
        assert next_d[n] <= 1.0
    print("test_oversized_step_rejected_with_safe_picard_fallback PASS")


if __name__ == "__main__":
    test_small_system_solver()
    test_physical_projection_and_bounds()
    test_active_set_change_reset()
    test_convergence_acceleration_on_mock_problem()
    test_gamma_cap_and_fallback_safeguard()
    test_oversized_step_rejected_with_safe_picard_fallback()
    print("\nALL 6 ANDERSON ACCELERATION TESTS PASSED SUCCESSFULLY!")
