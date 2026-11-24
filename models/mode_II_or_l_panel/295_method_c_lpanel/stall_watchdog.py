# -*- coding: utf-8 -*-
"""
models/pandey_kumar_mode2/294_method_c_mode2/stall_watchdog.py
=============================================================
Stall-Check Watchdog Module for Method C Mode-II and L-Panel Campaign
Governing Protocol: INDEPENDENT_STRUCTURED_REVIEW_V1
Correlation ID: HND-METHOD-C-MODE2-LPANEL-002
Goal ID: METHOD_C_MODE2_LPANEL_V1

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
            if cycle_elapsed >= self.max_cycle_seconds:
                hours = cycle_elapsed / 3600.0
                return (True, "CYCLE_TIMEOUT_EXCEEDED_8_HOURS",
                        "Cycle has been running for %.2f hours without completion (max 8.0 hr)" % hours)

        # Check (a): .sta increment advance
        if not os.path.exists(sta_path):
            # If sta does not exist yet, allow initial compilation/startup time up to 30 mins
            if self.cycle_start_time and (current_time - self.cycle_start_time) > 1800.0:
                return (True, "STA_FILE_MISSING_AFTER_30_MINUTES",
                        ".sta file has not been created after 30 minutes")
            return (False, "NORMAL", "Waiting for .sta creation")

        latest_inc = self.parse_sta_last_increment(sta_path)
        if latest_inc is None and self.last_increment_time is not None:
            if current_time - self.last_increment_time >= self.max_sta_stall_seconds:
                return (True, "SIMULATION_STALL_NO_INCREMENT_FOR_2_HOURS",
                        "Existing .sta contains no valid converged increment after 2 hours")
        if latest_inc is not None:
            inc_id = (latest_inc[0], latest_inc[1], latest_inc[2])
            if inc_id != self.last_increment_seen:
                # Advancing! Update tracking
                self.last_increment_seen = inc_id
                self.last_increment_time = current_time
                return (False, "ADVANCING", "Increment %d (step %d) active" % (latest_inc[1], latest_inc[0]))
            else:
                # Same increment as before: check elapsed time since advance
                if self.last_increment_time is not None:
                    idle_seconds = current_time - self.last_increment_time
                    if idle_seconds >= self.max_sta_stall_seconds:
                        hours = idle_seconds / 3600.0
                        return (True, "SIMULATION_STALL_NO_INCREMENT_FOR_2_HOURS",
                                "No new increment record in .sta for %.2f hours (stalled on step %d inc %d)" %
                                (hours, latest_inc[0], latest_inc[1]))

        return (False, "NORMAL", "Simulation within normal limits")

    def check_agent_stall(self, current_time=None):
        """
        Evaluates whether AGY has stalled without progress or handoff.
        Returns: (is_stalled, stall_reason, stall_details)
        """
        if current_time is None:
            current_time = time.time()

        elapsed = current_time - self.last_agent_progress_time
        if elapsed >= self.max_agent_seconds:
            hours = elapsed / 3600.0
            return (True, "AGENT_STALL_NO_PROGRESS_FOR_4_HOURS",
                    "AGY has not committed/pushed progress or issued a handoff for %.2f hours" % hours)

        return (False, "NORMAL", "Agent activity within normal cadence")

    def extract_tail_lines(self, filepath, n_lines=50):
        """Extracts the last n lines of a file safely."""
        if not os.path.exists(filepath):
            return ["(File does not exist: %s)" % filepath]
        try:
            with open(filepath, "r") as f:
                lines = f.readlines()
            return lines[-n_lines:]
        except Exception as e:
            return ["(Error reading %s: %s)" % (filepath, str(e))]

    def terminate_process_cleanly(self, job_name):
        """Cleanly terminates an Abaqus job without kill -9."""
        try:
            cmd = "abaqus terminate job=%s" % job_name
            subprocess.call(cmd, shell=True)
            time.sleep(5)
        except Exception as e:
            print("[Watchdog] Warning during clean termination: %s" % str(e))

    def build_stall_handoff_payload(self,
                                    case_name,
                                    cycle_index,
                                    job_name,
                                    last_completed_cycle_summary,
                                    sta_path,
                                    dat_path,
                                    log_path,
                                    what_was_tried,
                                    exact_blocker):
        """
        Builds the structured handoff payload to report a stall to Muse.
        """
        last_inc = self.parse_sta_last_increment(sta_path)
        last_inc_str = "None"
        if last_inc:
            last_inc_str = "Step %d, Increment %d, Attempt %d (Step time: %s, Total: %s)" % (
                last_inc[0], last_inc[1], last_inc[2], last_inc[4], last_inc[3])

        sta_tail = "".join(self.extract_tail_lines(sta_path, 50))
        dat_tail = "".join(self.extract_tail_lines(dat_path, 50))
        log_tail = "".join(self.extract_tail_lines(log_path, 50))

        payload = {
            "stall_notification": True,
            "case_name": case_name,
            "running_cycle": cycle_index,
            "job_name": job_name,
            "last_completed_cycle": last_completed_cycle_summary.get("cycle_index") if last_completed_cycle_summary else None,
            "last_completed_cycle_summary": last_completed_cycle_summary,
            "last_sta_increment": last_inc_str,
            "last_sta_timestamp": time.ctime(os.path.getmtime(sta_path)) if os.path.exists(sta_path) else "MISSING",
            "log_tails": {
                "sta_tail": sta_tail,
                "dat_tail": dat_tail,
                "log_tail": log_tail
            },
            "what_agy_tried": what_was_tried,
            "exact_blocker_diagnosis": exact_blocker
        }
        return payload
