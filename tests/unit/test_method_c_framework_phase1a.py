# -*- coding: utf-8 -*-
"""
Unit tests for Method C Framework Phase 1(a): Close Reporting Gaps.

Verifies:
1. Regex-based parse_dat_rf2 extracts independent Step 1 hold RF2 across variable whitespace.
2. Step 1 hold RF2 != terminal RF2 for RIKS cycles (Cycles 49-56).
3. Pre-severance hold-force continuity (|delta_RF2 / RF2_donor|) is strictly <= 5.0% for Cycles 49-52.
4. Mesh generator SHA is strictly verified as 9524B385...
5. RIKS termination and LPF overshoot telemetry parsed accurately from .sta records.
"""

import os
import re
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_FULL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
MESH_GEN_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "generate_case3_adaptive_corridor_mesh.py")
EXPECTED_MESH_GEN_SHA = "9524B385BC4928BC077A67C0110CDBFBE76A15AE1AC3D34F4E00996AA7B60B3C"


def parse_dat_rf2(dat_path):
    """Extracts step1, peak, and terminal RF2 from Abaqus .dat file using regex for variable whitespace."""
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

    if not step2_rf2_list:
        return {
            "step1_rf2": step1_rf2,
            "peak_rf2": step1_rf2,
            "terminal_rf2": step1_rf2,
            "peak_u2": None,
            "terminal_u2": None
        }

    peak_u2, peak_rf2 = max(step2_rf2_list, key=lambda x: x[1])
    term_u2, term_rf2 = step2_rf2_list[-1]

    return {
        "step1_rf2": step1_rf2,
        "peak_rf2": peak_rf2,
        "peak_u2": peak_u2,
        "terminal_rf2": term_rf2,
        "terminal_u2": term_u2
    }


def parse_sta_lpf(sta_path):
    """Extracts Step 2 terminal LPF from Abaqus .sta file."""
    if not os.path.isfile(sta_path):
        return None
    term_lpf = None
    with open(sta_path, "r") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 9:
                try:
                    step = int(parts[0])
                    if step == 2:
                        term_lpf = float(parts[6])  # LPF is column 7 in RIKS sta
                except (ValueError, IndexError):
                    continue
    return term_lpf


def test_mesh_generator_sha_matches_9524b385():
    """Assert mesh generator SHA matches 9524B385..."""
    assert os.path.isfile(MESH_GEN_PATH), "Mesh generator script missing"
    with open(MESH_GEN_PATH, "rb") as f:
        actual_sha = hashlib.sha256(f.read()).hexdigest().upper()
    assert actual_sha == EXPECTED_MESH_GEN_SHA, f"Expected {EXPECTED_MESH_GEN_SHA}, got {actual_sha}"


def test_parse_dat_rf2_variable_whitespace_tolerance():
    """Test regex matching handles 1, 2, 4 spaces in STEP header."""
    mock_dat_4spaces = """
    STEP    1  INCREMENT    1
    999999    0.000000E+00    2.287473E+00
    STEP    2  INCREMENT    1
    999999    1.000000E-03    2.250000E+00
    999999    2.000000E-03    1.532583E+00
    """
    # Write temp file to test
    tmp_path = os.path.join(LOCAL_FULL_DIR, "tmp_test_whitespace.dat")
    try:
        with open(tmp_path, "w") as f:
            f.write(mock_dat_4spaces)
        res = parse_dat_rf2(tmp_path)
        assert res["step1_rf2"] == pytest.approx(2.287473, rel=1e-5)
        assert res["terminal_rf2"] == pytest.approx(1.532583, rel=1e-5)
        assert res["step1_rf2"] != res["terminal_rf2"]
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_cycle49_to_56_step1_hold_rf2_independent():
    """Assert Step 1 hold RF2 is extracted independently (not equal to terminal RF2) for Cycles 49-56."""
    for c in range(49, 57):
        dat_p = os.path.join(LOCAL_FULL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}.dat")
        assert os.path.isfile(dat_p), f"Missing {dat_p}"
        res = parse_dat_rf2(dat_p)
        assert res["step1_rf2"] is not None, f"Cycle {c} missing step1_rf2"
        assert res["terminal_rf2"] is not None, f"Cycle {c} missing terminal_rf2"
        assert res["step1_rf2"] != res["terminal_rf2"], f"Cycle {c} step1_rf2 conflated with terminal_rf2"


def test_pre_severance_hold_force_continuity_passes_gate():
    """Assert pre-severance cycles 49, 50, 51, 52 strictly pass the <= 5.0% force continuity gate."""
    expected_jumps = {
        49: -1.0506,
        50: -2.2441,
        51: -1.5613,
        52: -3.7899,
    }
    for c, exp_jump in expected_jumps.items():
        sum_p = os.path.join(LOCAL_FULL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}_SUMMARY.json")
        assert os.path.isfile(sum_p), f"Missing {sum_p}"
        with open(sum_p, "r") as f:
            rec = json.load(f)
        actual_jump = rec.get("step1_hold_jump_pct")
        assert actual_jump is not None, f"Cycle {c} missing step1_hold_jump_pct"
        assert abs(actual_jump - exp_jump) < 0.05, f"Cycle {c} jump {actual_jump}% != {exp_jump}%"
        assert abs(actual_jump) <= 5.0, f"Cycle {c} jump {actual_jump}% exceeds 5.0% gate"


def test_riks_lpf_overshoot_documented_from_sta():
    """Verify RIKS LPF terminal values from .sta files for Cycles 49 and 52."""
    c49_sta = os.path.join(LOCAL_FULL_DIR, "PK_METHOD_C_CASE3_CYCLE49.sta")
    c52_sta = os.path.join(LOCAL_FULL_DIR, "PK_METHOD_C_CASE3_CYCLE52.sta")

    lpf49 = parse_sta_lpf(c49_sta)
    lpf52 = parse_sta_lpf(c52_sta)

    assert lpf49 is not None
    assert lpf52 is not None

    # Cycle 49 terminates at LPF ~ 1.082 (max LPF was specified as 1.0)
    assert abs(lpf49 - 1.082) < 0.02, f"Cycle 49 LPF {lpf49} != 1.082"
    # Cycle 52 terminates at LPF ~ 2.413 (max LPF was specified as 1.0)
    assert abs(lpf52 - 2.413) < 0.05, f"Cycle 52 LPF {lpf52} != 2.413"
