"""Unit test verifying Package 163 (Job 1419488) convergence diagnosis findings.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
"""

import json
from pathlib import Path
import pytest


def test_package163_convergence_diagnosis_artifact():
    diag_path = Path("results/validation/package163_convergence_diagnosis.json")
    assert diag_path.is_file(), f"Missing diagnosis artifact: {diag_path}"

    with open(diag_path, "r", encoding="utf-8") as f:
        diag = json.load(f)

    assert diag["schema"] == 1
    assert diag["job_id"] == "1419488.mmaster02"
    assert diag["total_outer_iterations"] == 100

    # KKT residual bounds: both dual and free residuals strictly meet tolerances (< 1e-6)
    kkt = diag["kkt_residuals_final"]
    assert kkt["dual_converged"] is True
    assert kkt["free_converged"] is True
    assert kkt["dual_error"] < 1.0e-6
    assert kkt["free_error"] < 1.0e-6

    # Convergence status at iteration 100:
    # All 3 coupled variables were still above tolerance, confirming physical non-convergence
    stats = diag["last_30_stats"]
    assert stats["delta_d"]["converged"] is False
    assert stats["delta_u"]["converged"] is False
    assert stats["delta_h"]["converged"] is False

    # Monotonic contraction test:
    # The active set and delta_d contracted monotonically in late iterations (no limit cycles)
    osc = diag["oscillation_signature"]
    assert osc["is_plateau_or_cycle"] is False
    counts = osc["last_20_pdas_counts"]
    # Verify strictly non-increasing active set counts
    for i in range(len(counts) - 1):
        assert counts[i] >= counts[i + 1]

    # Verify linear contraction rate rho is in [0.95, 0.98]
    dd_vals = [float(x) for x in osc["last_10_delta_d"]]
    rates = [dd_vals[i+1] / dd_vals[i] for i in range(len(dd_vals)-1)]
    avg_rate = sum(rates) / len(rates)
    assert 0.95 <= avg_rate <= 0.98
