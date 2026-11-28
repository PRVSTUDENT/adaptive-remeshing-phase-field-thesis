# -*- coding: utf-8 -*-
"""
models/complex_mixed_load/stall_watchdog.py
===========================================
Stall watchdog for Problem 3 (Combined Tension + Shear):
Checks advancement in .sta file and cycle elapsed time.
"""

from __future__ import print_function, division
import os
import sys
import time
from pathlib import Path


class StallWatchdog(object):
    def __init__(self, check_interval_sec=300, max_increment_stall_sec=7200, max_cycle_sec=28800):
        self.check_interval_sec = check_interval_sec
        self.max_increment_stall_sec = max_increment_stall_sec  # 2 hours
        self.max_cycle_sec = max_cycle_sec                      # 8 hours
        self.cycle_start_time = None
        self.last_sta_mod_time = None
        self.last_increment_count = 0

    def start_cycle(self):
        self.cycle_start_time = time.time()
        self.last_sta_mod_time = time.time()
        self.last_increment_count = 0

    def record_agent_progress(self):
        self.last_sta_mod_time = time.time()

    def check_simulation_stall(self, sta_file_path):
        """
        Returns: (is_stalled, reason, details)
        """
        now = time.time()
        if self.cycle_start_time and (now - self.cycle_start_time > self.max_cycle_sec):
            return True, "CYCLE_TIMEOUT_8H", {
                "elapsed_sec": now - self.cycle_start_time,
                "limit_sec": self.max_cycle_sec
            }

        sta = Path(sta_file_path)
        if not sta.exists():
            return False, "INITIALIZING", {}

        try:
            mtime = sta.stat().st_mtime
            lines = [l for l in sta.read_text(errors="replace").splitlines() if l.strip()]
            inc_lines = [l for l in lines if l[0].isdigit() or (len(l) > 1 and l[:2].strip().isdigit())]
            inc_count = len(inc_lines)

            if inc_count > self.last_increment_count:
                self.last_increment_count = inc_count
                self.last_sta_mod_time = now
            elif (now - self.last_sta_mod_time) > self.max_increment_stall_sec:
                return True, "STA_INCREMENT_STALLED_2H", {
                    "stall_sec": now - self.last_sta_mod_time,
                    "last_inc_count": inc_count,
                    "limit_sec": self.max_increment_stall_sec
                }
        except Exception:
            pass

        return False, "PROGRESSING", {"inc_count": self.last_increment_count}
