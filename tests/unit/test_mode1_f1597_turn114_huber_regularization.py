#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn114_huber_regularization.py
Unit tests verifying the Turn 114 C1-smooth Huber regularized active-set penalty
formulation in the experimental irreversible UEL.
"""

import math
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROD_UEL = REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
EXP_UEL = REPO_ROOT / "models/pandey_kumar_mode1/105_c3_irreversible_continuation/f42_experimental_irreversible_uel.for"

PROD_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def test_production_uel_bitwise_frozen():
    """Verify production UEL is 100% bitwise frozen."""
    assert PROD_UEL.exists(), f"Production UEL not found at {PROD_UEL}"
    with open(PROD_UEL, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_hash == PROD_UEL_HASH, f"Production UEL modified! Expected {PROD_UEL_HASH}, got {actual_hash}"

def test_experimental_uel_huber_regularization_present():
    """Verify experimental UEL contains calibrated Huber regularization parameters and logic."""
    assert EXP_UEL.exists(), f"Experimental UEL not found at {EXP_UEL}"
    with open(EXP_UEL, "r", encoding="utf-8") as f:
        text = f.read()

    # Parameter declarations
    assert "PARAMETER (GAMMA_PEN = 10.0D0, DELTA_PEN = 1.0D-4)" in text
    assert "DOUBLE PRECISION DIFF_D, PEN_FORCE, PEN_STIFF" in text

    # Discontinuous step penalty completely removed
    assert "1.0D8 * DIFF_D" not in text
    assert "AMATRX(I,I) + 1.0D8" not in text

    # Quad element (JTYPE 1) Huber regularization
    assert "C1-smooth quadratic transition band (delta = 1.0D-4)" in text
    assert "PEN_FORCE = (GAMMA_PEN / (TWO * DELTA_PEN)) *" in text
    assert "PEN_STIFF = (GAMMA_PEN / DELTA_PEN) * DIFF_D" in text
    assert "PEN_FORCE = GAMMA_PEN * (DIFF_D - HALF * DELTA_PEN)" in text
    assert "PEN_STIFF = GAMMA_PEN" in text

    # Both JTYPE 1 and JTYPE 3 updated
    assert text.count("PEN_FORCE = (GAMMA_PEN / (TWO * DELTA_PEN)) *") == 2
    assert text.count("PEN_STIFF = (GAMMA_PEN / DELTA_PEN) * DIFF_D") == 2

def test_huber_mathematical_continuity():
    """Verify Huber penalty force and tangent stiffness are continuous at delta."""
    gamma = 10.0
    delta = 1.0e-4

    def pen_force(diff):
        if diff <= 0.0:
            return 0.0
        elif diff < delta:
            return (gamma / (2.0 * delta)) * (diff ** 2)
        else:
            return gamma * (diff - 0.5 * delta)

    def pen_stiff(diff):
        if diff <= 0.0:
            return 0.0
        elif diff < delta:
            return (gamma / delta) * diff
        else:
            return gamma

    # Continuity at diff = 0
    eps = 1.0e-12
    assert abs(pen_force(0.0) - pen_force(eps)) < 1e-15
    assert abs(pen_stiff(0.0) - pen_stiff(eps)) < 1e-6

    # Continuity at diff = delta
    force_below = pen_force(delta - eps)
    force_above = pen_force(delta + eps)
    assert abs(force_below - force_above) < 1e-10

    stiff_below = pen_stiff(delta - eps)
    stiff_above = pen_stiff(delta + eps)
    assert abs(stiff_below - stiff_above) < 1e-6

    # Monotonicity test across [0, 2*delta]
    diffs = [i * (2.0 * delta / 100.0) for i in range(101)]
    forces = [pen_force(d) for d in diffs]
    stiffs = [pen_stiff(d) for d in diffs]
    for i in range(len(forces) - 1):
        assert forces[i+1] >= forces[i], "Penalty force must be non-decreasing"
        assert stiffs[i] >= 0.0, "Stiffness must be non-negative"
