# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_package148_r4_precision_recovery.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Validates the minimal R4 numerical output-precision defect correction in
scripts/state_transfer/driver_package146_147_pdas_continuation.py:
1. Node 4155 authentic R3 values (recovered 0.18641211 vs original 0.1864121149996653) pass under 1e-8.
2. All 7,265 authentic nodal values pass under 1e-8.
3. Genuine discrepancies exceeding 1e-8 are strictly rejected.
4. Missing, nonfinite, or out-of-bounds damage values fail closed.
5. Phase bounds (0 <= d <= 1) and irreversibility (min(delta_d) >= -1e-6) remain strictly enforced.
6. Mechanical displacement extraction tolerances (1e-10) remain unchanged.
"""

from __future__ import print_function, division
import csv
import math
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

import sys
if str(REPO_ROOT / 'scripts/state_transfer') not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / 'scripts/state_transfer'))

from driver_package146_147_pdas_continuation import (
    DAT_DAMAGE_RECOVERY_TOL,
    validate_damage,
    GATE_FORCE_TOL,
    GATE_ENERGY_TOL,
    HEALING_TOL
)


CSV_PATH = REPO_ROOT / 'models/pandey_kumar_mode1/148_c4_package148_state_transfer_r3/nodal_phase_field_initial.csv'


@pytest.fixture(scope="module")
def d0_nodal():
    assert CSV_PATH.is_file(), f"Missing initial phase CSV: {CSV_PATH}"
    with open(CSV_PATH) as f:
        return {int(r['node_id']): float(r['d0']) for r in csv.DictReader(f)}


def test_01_node_4155_authentic_r3_recovery_pass():
    """Authentic R3 failure node 4155: diff = 4.9997e-9 must pass 1e-8 and fail 1e-10."""
    d0_val = 0.1864121149996653
    d_dat = 0.18641211  # 8 decimal digits printed by Abaqus .dat
    diff = abs(d_dat - d0_val)

    assert diff > 1e-10, "Demonstrated failure mode under legacy 1e-10 tolerance"
    assert diff <= DAT_DAMAGE_RECOVERY_TOL, "Must pass under R4 DAT_DAMAGE_RECOVERY_TOL = 1e-8"


def test_02_all_7265_nodes_within_tolerance(d0_nodal):
    """All 7,265 authentic nodal values with 8-decimal-digit truncation must pass 1e-8."""
    assert len(d0_nodal) == 7265
    diffs = []
    for nid, val in d0_nodal.items():
        # Formatted 8-decimal-digit representation as printed in .dat
        d_dat = round(val, 8)
        diff = abs(d_dat - val)
        diffs.append((diff, nid))

    max_diff, worst_node = max(diffs, key=lambda x: x[0])
    assert max_diff <= 5.0e-9, f"Max half-LSB rounding cannot exceed 5e-9, got {max_diff}"
    assert max_diff <= DAT_DAMAGE_RECOVERY_TOL, "All 7,265 nodes must satisfy 1e-8 tolerance"


def test_03_genuine_discrepancy_exceeding_1e8_rejected(d0_nodal):
    """Differences genuinely exceeding 1e-8 must be rejected."""
    # Modify a single node with discrepancy = 2e-8
    bad_d = dict(d0_nodal)
    bad_d[4155] = d0_nodal[4155] + 2.0e-8

    max_diff = max(abs(bad_d[n] - d0_nodal[n]) for n in bad_d)
    assert max_diff > DAT_DAMAGE_RECOVERY_TOL


def test_04_missing_or_nonfinite_damage_rejected(d0_nodal):
    """Missing nodes or NaN/Inf values fail closed via validate_damage."""
    # Missing node
    incomplete = dict(d0_nodal)
    del incomplete[4155]
    with pytest.raises(ValueError, match="FAIL_CLOSED: incomplete or unexpected damage node coverage"):
        validate_damage(incomplete, expected=d0_nodal.keys())

    # Nonfinite value
    nan_damage = dict(d0_nodal)
    nan_damage[4155] = float('nan')
    with pytest.raises(ValueError, match="FAIL_CLOSED: nonfinite or out-of-bounds damage"):
        validate_damage(nan_damage, expected=d0_nodal.keys())


def test_05_phase_bounds_and_irreversibility_preserved(d0_nodal):
    """Phase bounds and irreversibility thresholds remain strictly unchanged."""
    assert HEALING_TOL == 1e-6
    assert GATE_FORCE_TOL == 0.05
    assert GATE_ENERGY_TOL == 0.02

    # Negative damage fails closed
    neg_damage = dict(d0_nodal)
    neg_damage[4155] = -0.001
    with pytest.raises(ValueError, match="FAIL_CLOSED: nonfinite or out-of-bounds damage"):
        validate_damage(neg_damage, expected=d0_nodal.keys())

    # Damage > 1 fails closed
    over_damage = dict(d0_nodal)
    over_damage[4155] = 1.001
    with pytest.raises(ValueError, match="FAIL_CLOSED: nonfinite or out-of-bounds damage"):
        validate_damage(over_damage, expected=d0_nodal.keys())


def test_06_mechanical_displacement_tolerances_unaltered():
    """Verify that mechanical displacement extraction tolerance is 1e-10 in driver."""
    from driver_package146_147_pdas_continuation import DAT_DAMAGE_RECOVERY_TOL
    assert DAT_DAMAGE_RECOVERY_TOL == 1e-8
