# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_mode2_stall_check.py
============================================
Unit tests for the Stall-Check Clause implementation (HND-METHOD-C-MODE2-LPANEL-002).
Verifies:
1. Increments advancing in .sta -> NO stall (progress).
2. No new increment in .sta for 2 hours -> SIMULATION STALL flagged.
3. Cycle runtime exceeding 8 hours -> CYCLE TIMEOUT STALL flagged.
4. Agent silence exceeding 4 hours -> AGENT STALL flagged.
5. Handshake payload generation contains all 6 required items for Muse.
"""

import os
import sys
import time
import pytest
import tempfile

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "294_method_c_mode2"))

from stall_watchdog import StallWatchdog


def test_simulation_advancing_is_not_a_stall():
    """Verify that a running cycle whose .sta advances increments is recognized as progress."""
    watchdog = StallWatchdog(max_sta_stall_hours=2.0, max_cycle_hours=8.0, max_agent_hours=4.0)
    watchdog.start_cycle()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sta") as f:
        f.write("   1     1     1  0.0005  0.0005  0.0005     1\n")
        f.write("   1     2     1  0.0010  0.0005  0.0005     1\n")
        sta_path = f.name

    try:
        t0 = time.time()
        is_stalled, reason, details = watchdog.check_simulation_stall(sta_path, current_time=t0)
        assert not is_stalled, "Advancing simulation must not be flagged as stalled"
        assert reason == "ADVANCING"

        # Append new increment after 1.5 hours
        with open(sta_path, "a") as f:
            f.write("   1     3     1  0.0015  0.0005  0.0005     1\n")

        t1 = t0 + 1.5 * 3600.0  # 1.5 hours later
        is_stalled, reason, details = watchdog.check_simulation_stall(sta_path, current_time=t1)
        assert not is_stalled, "Simulation advancing within 1.5 hours is progress, not stall"
        assert reason == "ADVANCING"
    finally:
        if os.path.exists(sta_path):
            os.remove(sta_path)


def test_simulation_sta_stalled_after_two_hours():
    """Verify that no new increment in .sta for 2 consecutive hours triggers simulation stall."""
    watchdog = StallWatchdog(max_sta_stall_hours=2.0, max_cycle_hours=8.0, max_agent_hours=4.0)
    watchdog.start_cycle()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sta") as f:
        f.write("   1    10     1  0.0050  0.0005  0.0005     1\n")
        sta_path = f.name

    try:
        t0 = time.time()
        # Initial check records increment 10
        is_stalled, reason, details = watchdog.check_simulation_stall(sta_path, current_time=t0)
        assert not is_stalled

        # Check after 2 hours and 5 minutes with NO new increment in .sta
        t_stall = t0 + 2.08 * 3600.0
        is_stalled, reason, details = watchdog.check_simulation_stall(sta_path, current_time=t_stall)
        assert is_stalled, "Simulation must be flagged stalled when .sta idle > 2 hours"
        assert reason == "SIMULATION_STALL_NO_INCREMENT_FOR_2_HOURS"
        assert "stalled on step 1 inc 10" in details
    finally:
        if os.path.exists(sta_path):
            os.remove(sta_path)


def test_cycle_timeout_exceeded_eight_hours():
    """Verify that a cycle running longer than 8 hours without completion is flagged as stalled."""
    watchdog = StallWatchdog(max_sta_stall_hours=2.0, max_cycle_hours=8.0, max_agent_hours=4.0)
    watchdog.start_cycle()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sta") as f:
        f.write("   1     1     1  0.0005  0.0005  0.0005     1\n")
        sta_path = f.name

    try:
        t0 = time.time()
        # Check after 8.1 hours
        t_timeout = t0 + 8.1 * 3600.0
        is_stalled, reason, details = watchdog.check_simulation_stall(sta_path, current_time=t_timeout)
        assert is_stalled, "Cycle runtime > 8.0 hours must trigger stall"
        assert reason == "CYCLE_TIMEOUT_EXCEEDED_8_HOURS"
    finally:
        if os.path.exists(sta_path):
            os.remove(sta_path)


def test_agent_stall_exceeded_four_hours():
    """Verify that AGY is flagged stalled if no commit/push/handoff occurs for 4 consecutive hours."""
    watchdog = StallWatchdog(max_sta_stall_hours=2.0, max_cycle_hours=8.0, max_agent_hours=4.0)

    t0 = time.time()
    watchdog.last_agent_progress_time = t0

    # At 3.5 hours: normal
    is_stalled, reason, details = watchdog.check_agent_stall(current_time=t0 + 3.5 * 3600.0)
    assert not is_stalled

    # At 4.2 hours: agent stall
    is_stalled, reason, details = watchdog.check_agent_stall(current_time=t0 + 4.2 * 3600.0)
    assert is_stalled, "Agent silence > 4.0 hours must trigger agent stall"
    assert reason == "AGENT_STALL_NO_PROGRESS_FOR_4_HOURS"

    # Resetting agent progress clears the stall
    watchdog.record_agent_progress()
    is_stalled, reason, details = watchdog.check_agent_stall()
    assert not is_stalled, "Recording progress must clear agent stall"


def test_stall_handoff_payload_contains_all_required_items():
    """Verify that stall handoff payload formats all 6 required items for Muse."""
    watchdog = StallWatchdog()

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".sta") as f_sta:
        f_sta.write("   1    45     2  0.0225  0.0005  0.00025    1\n")
        sta_path = f_sta.name

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".dat") as f_dat:
        f_dat.write("LINE 1\nLINE 2\n")
        dat_path = f_dat.name

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".log") as f_log:
        f_log.write("Abaqus job running\n")
        log_path = f_log.name

    try:
        last_summary = {"cycle_index": 2, "terminal_rf2_kn": 0.45}
        payload = watchdog.build_stall_handoff_payload(
            case_name="MODE2_SHEAR",
            cycle_index=3,
            job_name="PK_M2_CYCLE3",
            last_completed_cycle_summary=last_summary,
            sta_path=sta_path,
            dat_path=dat_path,
            log_path=log_path,
            what_was_tried="Step 2 quasi-static advance with dt=5e-4",
            exact_blocker="dt_min cutback failure near bottom boundary"
        )

        assert payload["stall_notification"] is True
        assert payload["case_name"] == "MODE2_SHEAR"
        assert payload["running_cycle"] == 3
        assert payload["job_name"] == "PK_M2_CYCLE3"
        assert payload["last_completed_cycle"] == 2
        assert "Increment 45" in payload["last_sta_increment"]
        assert len(payload["log_tails"]["sta_tail"]) > 0
        assert len(payload["log_tails"]["dat_tail"]) > 0
        assert payload["what_agy_tried"] == "Step 2 quasi-static advance with dt=5e-4"
        assert payload["exact_blocker_diagnosis"] == "dt_min cutback failure near bottom boundary"
    finally:
        for p in [sta_path, dat_path, log_path]:
            if os.path.exists(p):
                os.remove(p)
