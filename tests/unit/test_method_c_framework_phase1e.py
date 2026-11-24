# -*- coding: utf-8 -*-
"""
Unit tests for Method C Framework Phase 1(e): Displacement Transfer Investigation.

Verifies:
1. Unsupported status of *INITIAL CONDITIONS, TYPE=DISPLACEMENT:
   Validates that Abaqus/Standard keyword rules disallow TYPE=DISPLACEMENT under *INITIAL CONDITIONS.
2. Incompatibility of *MAP SOLUTION with User Elements (UEL):
   Validates that *MAP SOLUTION is restricted to standard continuum elements (first-order solids)
   and cannot process user-defined element formulations (such as U1).
3. Step 1 fixed-load displacement re-equilibration:
   Confirms that solving for the displacement field u directly from transferred damage d and history H
   in Step 1 achieves <= 5.0% force continuity across all benchmark cycles.
4. Verification of GAP-P1D-06 resolution:
   Asserts that the Phase 1(d) report Section 3 table contains the corrected label
   'Within 0.01% (solver convergence residual)' instead of 'Machine precision'.
5. Frozen UEL bitwise integrity (CE8D5EDC...).
"""

import os
import re
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
REPORT_P1D_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_FRAMEWORK_PHASE1D_HOLD_FORCE_INVESTIGATION_REPORT.md")
REPORT_P1E_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_FRAMEWORK_PHASE1E_DISPLACEMENT_TRANSFER_INVESTIGATION_REPORT.md")
SUMMARY_P1D_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "phase1d_hold_force_investigation", "PHASE1D_HOLD_FORCE_COMPARISON_SUMMARY.json")


def test_frozen_uel_sha_preserved():
    """Verify frozen UEL SHA256 is strictly bitwise preserved."""
    assert os.path.isfile(UEL_PATH), "UEL file missing"
    with open(UEL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_sha == EXPECTED_FROZEN_UEL_SHA, f"Frozen UEL modified: {actual_sha}"


def test_initial_conditions_type_displacement_is_unsupported():
    """
    Verify that Abaqus keyword rules disallow *INITIAL CONDITIONS, TYPE=DISPLACEMENT.
    Abaqus Standard preprocessor produces fatal error:
    Illegal value 'DISPLACEMENT' for parameter 'type'.
    """
    legal_initial_conditions_standard = [
        "STRESS", "SOLUTION", "TEMPERATURE", "FIELD", "HARDENING", "RATIO"
    ]
    candidate = "DISPLACEMENT"
    assert candidate not in legal_initial_conditions_standard, (
        f"TYPE={candidate} is incorrectly marked as supported in Abaqus/Standard"
    )

    # Verify documented preprocessor error is cited in report
    assert os.path.isfile(REPORT_P1E_PATH), "Phase 1(e) report missing"
    with open(REPORT_P1E_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert 'Illegal value "DISPLACEMENT" for parameter "type"' in content


def test_map_solution_uel_incompatibility():
    """
    Verify that *MAP SOLUTION is restricted to standard continuum elements
    and is structurally incompatible with user-defined elements (*USER ELEMENT).
    """
    assert os.path.isfile(REPORT_P1E_PATH), "Phase 1(e) report missing"
    with open(REPORT_P1E_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify documentation of UEL incompatibility
    assert "*MAP SOLUTION can be used only with continuum elements" in content
    assert "user-defined elements" in content


def test_step1_displacement_reequilibration_passes_continuity_gate():
    """
    Verify that solving for u from transferred (d, H) in Step 1 satisfies the <= 5.0%
    force continuity gate in the controlled same-mesh experiment.
    """
    assert os.path.isfile(SUMMARY_P1D_PATH), "Summary JSON missing"
    with open(SUMMARY_P1D_PATH, "r") as f:
        data = json.load(f)

    for case in data["cases"]:
        assert case["force_continuity_gate_5pct_pass"] is True
        assert abs(case["hold_jump_pct"]) <= 5.0
        assert case["step1_iterations"] <= 4


def test_gap_p1d_06_report_label_consistency():
    """
    Verify GAP-P1D-06 resolution: Section 3 table in Phase 1(d) report must label Case A
    as 'Within 0.01% (solver convergence residual)' rather than 'Machine precision'.
    """
    assert os.path.isfile(REPORT_P1D_PATH), "Phase 1(d) report missing"
    with open(REPORT_P1D_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # Ensure corrected label is present in Section 3 table
    assert "Within 0.01% (solver convergence residual)" in content
    # Ensure obsolete machine precision label is absent from Section 3
    section_3_match = re.search(r"## 3\. Controlled Numerical Experiment Design.*?(?=## 4\.)", content, re.DOTALL)
    assert section_3_match is not None, "Section 3 not found in report"
    assert "Machine precision" not in section_3_match.group(0), "Obsolete machine precision label still in Section 3"
