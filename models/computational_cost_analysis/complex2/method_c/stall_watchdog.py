# -*- coding: utf-8 -*-
"""
models/complex_two_hole/stall_watchdog.py
=========================================
Stall-Check Watchdog Module for Method C Complex Models Campaign
Governing Protocol: INDEPENDENT_STRUCTURED_REVIEW_V1
Task ID: METHOD-C-COMPLEX-MODELS
Goal ID: METHOD_C_COMPLEX_MODELS_V1

Implements the mandatory Stall-Check Clause:
- simulation_stall:
  (a) .sta shows no new increment record for 2 consecutive hours, OR
  (b) no cycle has completed within 8 hours of previous cycle's completion.
- agent_stall:
  AGY has not committed/pushed progress or issued a handoff for 4 consecutive hours.
- not_a_stall:
  A cycle that is legitimately long but whose .sta IS advancing is progress, not a stall.
- on_stall protocol:
  * Do NOT retry or restart blindly.
  * Preserve state: commit/push current cycle summary, .sta, .dat, logs.
  * Terminate running Abaqus process cleanly.
  * Issue structured bridge handoff to Muse.
  * Wait for bridge response.
"""

from __future__ import print_function, division
import os
import sys
import time
import datetime
import subprocess
import json


class StallWatchdog(object):
    """
    Watches Abaqus simulation and agent execution state for stalls.
    """

    def __init__(self,
                 max_sta_stall_hours=2.0,
                 max_cycle_hours=8.0,
                 max_agent_hours=4.0):
        self.max_sta_stall_seconds = float(max_sta_stall_hours) * 3600.0
        self.max_cycle_seconds = float(max_cycle_hours) * 3600.0
        self.max_agent_seconds = float(max_agent_hours) * 3600.0

        # State tracking
        self.last_increment_seen = None
        self.last_increment_time = None
        self.cycle_start_time = None
        self.last_agent_progress_time = time.time()

    def record_agent_progress(self):
        """Call whenever a commit, push, or handoff is executed."""
        self.last_agent_progress_time = time.time()

    def start_cycle(self):
        """Call when a new cycle starts."""
        self.cycle_start_time = time.time()
        self.last_increment_seen = None
        self.last_increment_time = time.time()

    def parse_sta_last_increment(self, sta_path):
        """
        Parses the last valid increment line from an Abaqus .sta file.
        Returns: (step_num, inc_num, att_num, total_time, step_time, inc_time) or None
        """
        if not os.path.exists(sta_path):
            return None

        last_inc = None
        try:
            with open(sta_path, "r") as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        try:
                            step = int(parts[0])
                            inc = int(parts[1])
                            att = int(parts[2])
                            last_inc = (step, inc, att, parts[3], parts[4], parts[5])
                        except ValueError:
                            continue
        except Exception:
            return None

        return last_inc

    def check_simulation_stall(self, sta_path, current_time=None):
        """
        Evaluates whether the running simulation is stalled.
        Returns: (is_stalled, stall_reason, stall_details)
        """
        if current_time is None:
            current_time = time.time()

        # Check (b): cycle runtime exceeded 8 hours
        if self.cycle_start_time is not None:
            cycle_elapsed = current_time - self.cycle_start_time
            if cycle_elapsed > self.max_cycle_seconds:
                return (True,
                        "CYCLE_RUNTIME_EXCEEDED_8_HOURS",
                        {"cycle_elapsed_hours": round(cycle_elapsed / 3600.0, 3),
                         "max_cycle_hours": round(self.max_cycle_seconds / 3600.0, 1),
                         "sta_path": sta_path})

        # Check (a): .sta increment stall
        if not os.path.exists(sta_path):
            # File may not exist in initial seconds of solver startup
            return (False, "STA_FILE_NOT_YET_CREATED", {})

        last_inc = self.parse_sta_last_increment(sta_path)
        if last_inc is None:
            # File exists but no increments recorded yet
            return (False, "NO_INCREMENTS_RECORDED_YET", {})

        # If we see a new increment, update timestamp
        if last_inc != self.last_increment_seen:
            self.last_increment_seen = last_inc
            self.last_increment_time = current_time
            return (False, "SIMULATION_PROGRESSING",
                    {"last_increment": last_inc,
                     "updated_at": datetime.datetime.fromtimestamp(current_time).isoformat()})

        # Same increment seen: check how long it has been unchanging
        if self.last_increment_time is not None:
            stall_duration = current_time - self.last_increment_time
            if stall_duration > self.max_sta_stall_seconds:
                return (True,
                        "STA_INCREMENT_UNCHANGED_FOR_2_HOURS",
                        {"last_increment": last_inc,
                         "stall_duration_hours": round(stall_duration / 3600.0, 3),
                         "max_sta_stall_hours": round(self.max_sta_stall_seconds / 3600.0, 1),
                         "sta_path": sta_path})

        return (False, "SIMULATION_ACTIVE",
                {"last_increment": last_inc,
                 "elapsed_on_current_inc_seconds": round(current_time - self.last_increment_time, 1)
                 if self.last_increment_time else 0.0})

    def check_agent_stall(self, current_time=None):
        """
        Evaluates whether AGY has stalled (no commit/push/handoff for 4 hours).
        Returns: (is_stalled, stall_reason, stall_details)
        """
        if current_time is None:
            current_time = time.time()

        elapsed = current_time - self.last_agent_progress_time
        if elapsed > self.max_agent_seconds:
            return (True,
                    "AGENT_INACTIVE_FOR_4_HOURS",
                    {"inactive_hours": round(elapsed / 3600.0, 3),
                     "max_agent_hours": round(self.max_agent_seconds / 3600.0, 1)})

        return (False, "AGENT_ACTIVE",
                {"inactive_hours": round(elapsed / 3600.0, 3)})

    def kill_process_cleanly(self, pid, job_name=None, abaqus_cmd="abaqus"):
        """
        Terminates the running Abaqus process cleanly.
        Tries 'abaqus terminate job=...', then SIGTERM/taskkill, then SIGKILL.
        """
        results = []

        if job_name:
            try:
                cmd = [abaqus_cmd, "terminate", "job=%s" % job_name]
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                results.append({"method": "abaqus_terminate", "returncode": p.returncode, "stdout": p.stdout})
                time.sleep(5)
            except Exception as e:
                results.append({"method": "abaqus_terminate", "error": str(e)})

        # Windows taskkill
        if pid:
            try:
                cmd = ["taskkill", "/PID", str(pid), "/T", "/F"]
                p = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
                results.append({"method": "taskkill", "returncode": p.returncode, "stdout": p.stdout})
            except Exception as e:
                results.append({"method": "taskkill", "error": str(e)})

        return results
