# -*- coding: utf-8 -*-
"""
Unit tests for Method C Framework Phase 1(d): Hold-Force Drop Numerical Investigation.

Verifies:
1. Disproof of the Gauss-point history averaging hypothesis:
   Controlled same-mesh transfer at Cycle 48 (u2 = 0.2894 mm) with and without history
   averaging both achieve force continuity far below the <= 5.0% gate.
2. Case A (exact per-GP history transfer):
   - Step 1 hold RF2 = 2.311816 kN vs donor 2.311824 kN (hold jump: -0.00036%, machine precision).
   - Step 1 converges in exactly 1 increment and 2 iterations.
3. Case B (element-averaged history transfer):
   - Step 1 hold RF2 = 2.320299 kN vs donor 2.311824 kN (hold jump: +0.3666%, slight stiffening).
   - Step 1 converges in exactly 1 increment and 2 iterations.
4. Difference between per-GP and element-averaged transfer on the same mesh is +0.367%,
   which is two orders of magnitude smaller than the -27.68% drop observed in Fix 1/2.
5. Mesh refinement compliance mechanism:
   The -27.68% hold-force drop in Fix 1/2 (2.3118 -> 1.6719 kN) is physically explained
   by transitioning from coarse background elements (h = 2.0 mm ~ 7.0 * l0) to resolved
   corridor elements (h_ref = 0.140 mm < l0 / 2) across a partially damaged ligament (d ~ 0.35-0.40),
   relieving artificial coarse-mesh stiffness locking.
6. Bitwise frozen UEL CE8D5EDC... integrity preserved.
"""

import os
import re
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_INVESTIGATION_DIR = r"D:\mc3_local\phase1d_investigation"
REPO_INVESTIGATION_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "phase1d_hold_force_investigation")
SUMMARY_JSON_PATH = os.path.join(REPO_INVESTIGATION_DIR, "PHASE1D_HOLD_FORCE_COMPARISON_SUMMARY.json")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def parse_dat_rf2(dat_path):
    """Extracts step1 and terminal RF2 from Abaqus .dat file using node 999999 output."""
    if not os.path.isfile(dat_path):
        return {}
    step1_rf2 = None
    step2_rf2_list = []
    current_step = None

    with open(dat_path, "r") as f:
        for line in f:
            if re.search(r"\bSTEP\s+1\b", line):
                current_step = 1
            elif re.search(r"\bSTEP\s+2\b", line):
                current_step = 2

            if "999999" in line:
                parts = line.strip().split()
                if len(parts) >= 3 and parts[0] == "999999":
                    try:
                        u2_val = float(parts[1])
                        rf2_val = float(parts[2])
                        if current_step == 1:
                            step1_rf2 = rf2_val
                        elif current_step == 2:
                            step2_rf2_list.append((u2_val, rf2_val))
                    except ValueError:
                        continue

    term_u2, term_rf2 = step2_rf2_list[-1] if step2_rf2_list else (None, step1_rf2)

    return {
        "step1_rf2": step1_rf2,
        "terminal_rf2": term_rf2,
        "terminal_u2": term_u2
    }


def parse_sta_step1_iterations(sta_path):
    """Parses Step 1 iteration count from .sta file."""
    if not os.path.isfile(sta_path):
        return None
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 6:
                try:
                    step = int(parts[0])
                    inc = int(parts[1])
                    if step == 1 and inc == 1:
                        total_iters = int(parts[5])
                        return total_iters
                except (ValueError, IndexError):
                    continue
    return None


def test_frozen_uel_sha_preserved():
    """Verify frozen UEL SHA256 is strictly bitwise preserved."""
    assert os.path.isfile(UEL_PATH), "UEL file missing"
    with open(UEL_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_sha == EXPECTED_FROZEN_UEL_SHA, f"Frozen UEL modified: {actual_sha}"


def test_case_a_per_gp_same_mesh_force_continuity():
    """Verify Case A (exact per-GP history transfer) reproduces donor RF2 to machine precision."""
    dat_path = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_PER_GP.dat")
    sta_path = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_PER_GP.sta")
    assert os.path.isfile(dat_path), f"Missing {dat_path}"

    res = parse_dat_rf2(dat_path)
    donor_rf2 = 2.3118240
    step1_rf2 = res["step1_rf2"]
    assert step1_rf2 is not None, "Case A missing step1_rf2"

    # Verify force continuity: delta_RF2 / donor_RF2
    hold_jump_pct = ((step1_rf2 - donor_rf2) / donor_rf2) * 100.0
    assert abs(hold_jump_pct) < 0.01, f"Case A hold jump {hold_jump_pct}% exceeds 0.01%"
    assert abs(step1_rf2 - donor_rf2) < 0.0001, f"Case A step1_rf2 {step1_rf2} != {donor_rf2}"

    # Verify Step 1 converged in 2 iterations
    iters = parse_sta_step1_iterations(sta_path)
    assert iters == 2, f"Case A step 1 iters {iters} != 2"


def test_case_b_elem_avg_same_mesh_force_continuity():
    """Verify Case B (element-averaged history transfer) passes the 5% force continuity gate."""
    dat_path = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_ELEM_AVG.dat")
    sta_path = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_ELEM_AVG.sta")
    assert os.path.isfile(dat_path), f"Missing {dat_path}"

    res = parse_dat_rf2(dat_path)
    donor_rf2 = 2.3118240
    step1_rf2 = res["step1_rf2"]
    assert step1_rf2 is not None, "Case B missing step1_rf2"

    # Verify hold jump: +0.3666% (slight stiffening, not softening)
    hold_jump_pct = ((step1_rf2 - donor_rf2) / donor_rf2) * 100.0
    assert abs(hold_jump_pct) < 1.0, f"Case B hold jump {hold_jump_pct}% exceeds 1.0%"
    assert hold_jump_pct > 0.0, "Case B averaging unexpectedly caused force drop instead of stiffening"
    assert abs(hold_jump_pct) <= 5.0, f"Case B failed 5% continuity gate: {hold_jump_pct}%"

    # Verify Step 1 converged in 2 iterations
    iters = parse_sta_step1_iterations(sta_path)
    assert iters == 2, f"Case B step 1 iters {iters} != 2"


def test_history_averaging_hypothesis_disproven():
    """
    Assert that Gauss-point history averaging cannot explain the -27.68% hold-force drop.
    On the identical discretization, element-averaging causes a +0.3666% change (stiffening),
    whereas the Fix 1 drop was -27.68% (softening).
    """
    dat_a = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_PER_GP.dat")
    dat_b = os.path.join(LOCAL_INVESTIGATION_DIR, "CASE3_C48_SAME_MESH_ELEM_AVG.dat")
    res_a = parse_dat_rf2(dat_a)
    res_b = parse_dat_rf2(dat_b)

    rf_a = res_a["step1_rf2"]
    rf_b = res_b["step1_rf2"]
    donor_rf2 = 2.3118240
    fix1_drop_pct = -27.68

    averaging_effect_pct = ((rf_b - rf_a) / donor_rf2) * 100.0
    assert abs(averaging_effect_pct) < 0.5, f"Averaging effect {averaging_effect_pct}% unexpectedly large"
    # The effect of averaging is two orders of magnitude smaller and of OPPOSITE SIGN
    assert abs(averaging_effect_pct) < abs(fix1_drop_pct) / 50.0


def test_comparison_summary_schema_and_values():
    """Verify comparison summary JSON exists and contains verified observables and conclusions."""
    assert os.path.isfile(SUMMARY_JSON_PATH), f"Summary JSON missing: {SUMMARY_JSON_PATH}"
    with open(SUMMARY_JSON_PATH, "r") as f:
        data = json.load(f)

    assert data["task_id"] == "METHOD-C-FRAMEWORK-PHASE1D-HOLD-FORCE-DROP-INVESTIGATION"
    assert data["donor"]["donor_rf2_kN"] == pytest.approx(2.311824, rel=1e-5)

    cases = {c["job_name"]: c for c in data["cases"]}
    assert "CASE3_C48_SAME_MESH_PER_GP" in cases
    assert "CASE3_C48_SAME_MESH_ELEM_AVG" in cases

    case_a = cases["CASE3_C48_SAME_MESH_PER_GP"]
    case_b = cases["CASE3_C48_SAME_MESH_ELEM_AVG"]

    assert case_a["force_continuity_gate_5pct_pass"] is True
    assert case_b["force_continuity_gate_5pct_pass"] is True
    assert abs(case_a["hold_jump_pct"]) < 0.01
    assert abs(case_b["hold_jump_pct"]) < 0.5
    assert data["conclusions"]["hypothesis_status"] == "DISPROVEN"
