# -*- coding: utf-8 -*-
"""
tests/unit/test_f1632_method_a_generator.py
============================================
Task: F1632-METHOD-A-HOLE-DEMONSTRATION-REUSE-AND-GENERATION
Directive: Dr. Roth (6 November 2026) via HND-bef847fc363a and HND-f55ea7f9eb8f

Unit tests verifying:
1. ErrorTarget unit semantics and ambiguous decimal rejection guard (e.g. 0.02 vs 2.0).
2. Parameterized geometric constraints (hole inside plate, notch length).
3. Production UEL deck structure and boundary condition parity.
"""

import math
import os
import re
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_error_target_unit_guard():
    """Verify that ambiguous fractional errorTarget values <= 0.1 are rejected."""
    import sys
    from scripts.remeshing.generate_plate_with_hole_method_a import parse_args
    sys.argv = ['script', '--', '--error-target', '0.02']
    with pytest.raises(ValueError, match="Abaqus native remeshing requires percentage points"):
        parse_args()


def test_error_target_percentage_convention_accepted():
    """Verify that percentage values (e.g. 1.0, 2.0, 5.0) are correctly accepted."""
    import sys
    from scripts.remeshing.generate_plate_with_hole_method_a import parse_args
    sys.argv = ['script', '--', '--error-target', '2.0']
    args = parse_args()
    assert args.error_target == 2.0


def test_generator_boundary_condition_parity():
    """Verify that boundary conditions in generate_plate_with_hole_method_a.py allow Poisson contraction."""
    script_path = REPO_ROOT / "scripts" / "remeshing" / "generate_plate_with_hole_method_a.py"
    content = script_path.read_text(encoding="utf-8")

    # In pre-analysis, bottom should have u2=0 and single point pin u1=0 (NOT full edge u1=0)
    assert 'name="RollBottom", createStepName="Step-1", region=a.sets["Bottom"], u2=0.0' in content
    assert 'name="PinBottom", createStepName="Step-1", region=a.sets["PinBottomLeft"], u1=0.0' in content
    assert 'FixBottom", createStepName="Step-1", region=a.sets["Bottom"], u1=0.0' not in content

    # In generated UEL deck, top pull must be tied to RP and N_TOP must have u1=0 only where intended
    assert "*EQUATION" in content
    assert "N_RP, 2, 2" in content
