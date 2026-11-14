# -*- coding: utf-8 -*-
"""
scripts/hpc/monitor_case2_cutbacks.py
Live runtime monitoring daemon for Case 2 continuation execution.
Enforces Stop Condition 1: Aborts execution if > 50 consecutive cutbacks occur in Step 2.
"""

import sys
import time
import os
import subprocess
from pathlib import Path

def monitor_sta_file(sta_path: Path, max_cutbacks: int = 50, poll_interval: float = 5.0):
    print(f"[Monitor] Starting live cutback monitor on {sta_path} (max allowed: {max_cutbacks})")
    consecutive_cutbacks = 0
    last_step = None
    last_inc = None
    last_size = 0

    while True:
        if not sta_path.exists():
            time.sleep(poll_interval)
            continue

        try:
            current_size = sta_path.stat().st_size
            if current_size > last_size:
                with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(last_size)
                    new_lines = f.readlines()
                last_size = current_size

                for line in new_lines:
                    line_str = line.strip()
                    # Check for cutback indicators in Abaqus .sta
                    # Typical line: STEP INC ATT SEVERE EQUIL TOTAL TIME ...
                    # Or check for cutback notice
                    if "CUTBACK" in line_str.upper() or "THE MINIMUM TIME INCREMENT" in line_str.upper():
                        consecutive_cutbacks += 1
                        print(f"[Monitor] Detected cutback #{consecutive_cutbacks}: {line_str}")
                    elif re_inc := line_str.split():
                        # If a successful increment converged, reset counter
                        if len(re_inc) >= 5 and re_inc[0].isdigit() and re_inc[1].isdigit():
                            step = int(re_inc[0])
                            inc = int(re_inc[1])
                            if (step, inc) != (last_step, last_inc):
                                consecutive_cutbacks = 0
                                last_step = step
                                last_inc = inc

                    if consecutive_cutbacks >= max_cutbacks:
                        print(f"[Monitor] STOP CONDITION 1 TRIGGERED: {consecutive_cutbacks} consecutive cutbacks reached!")
                        job_name = sta_path.stem
                        print(f"[Monitor] Terminating Abaqus job {job_name}...")
                        subprocess.run(["abaqus", "terminate", f"job={job_name}"], check=False)
                        return 1

        except Exception as e:
            print(f"[Monitor] Warning: {e}")

        # Check if job completed
        msg_path = sta_path.with_suffix(".msg")
        if msg_path.exists():
            try:
                with open(msg_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                    if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in content or "ABAQUS/Standard Exit Code" in content:
                        print("[Monitor] Solver termination detected in .msg. Exiting monitor cleanly.")
                        return 0
            except Exception:
                pass

        time.sleep(poll_interval)

if __name__ == "__main__":
    sta_file = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("PK_F1752_CASE_2_CONTINUATION.sta")
    sys.exit(monitor_sta_file(sta_file))
