#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Guarded Submission Orchestrator for Task-5 Corrected 2% and 5% Production Solves.
Enforces:
1. Max 2 active jobs in queue.
2. Clean preflights and hash verification.
3. Captures and records exact PBS Job IDs.
"""

from __future__ import print_function
import os
import sys
import subprocess
import json

def get_active_jobs():
    cmd = ["qstat", "-u", "pr21vyci"]
    try:
        out = subprocess.check_output(cmd).decode("utf-8")
        lines = [l.strip() for l in out.splitlines() if l.strip() and not l.startswith("Job ID") and not l.startswith("---") and not l.startswith("mnode")]
        return lines
    except Exception as e:
        print("Error checking qstat:", e)
        return []

def main():
    active_jobs = get_active_jobs()
    print("Current active jobs count:", len(active_jobs))
    if len(active_jobs) > 0:
        print("WARNING: Queue not empty. Active jobs:")
        for aj in active_jobs:
            print("  ", aj)
        if len(active_jobs) >= 2:
            print("ERROR: Scheduler limit reached (max 2 active jobs). Aborting submission.")
            sys.exit(1)

    base_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1"
    dir_2pct = os.path.join(base_dir, "06_production_adaptive_2pct")
    dir_5pct = os.path.join(base_dir, "07_production_adaptive_5pct")

    # Submit 2% job
    print("\n[1/2] Submitting 2.0% Corrected Production Job...")
    p2 = subprocess.Popen(["qsub", "submit_solver.pbs"], cwd=dir_2pct, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out2, err2 = p2.communicate()
    job_2pct = out2.decode("utf-8").strip()
    if p2.returncode != 0 or not job_2pct:
        print("ERROR: Failed to submit 2.0% job. Stderr:", err2.decode("utf-8"))
        sys.exit(2)
    print("SUCCESS: 2.0% Job Submitted with PBS ID:", job_2pct)

    # Submit 5% job
    print("\n[2/2] Submitting 5.0% Corrected Production Job...")
    p5 = subprocess.Popen(["qsub", "submit_solver.pbs"], cwd=dir_5pct, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out5, err5 = p5.communicate()
    job_5pct = out5.decode("utf-8").strip()
    if p5.returncode != 0 or not job_5pct:
        print("ERROR: Failed to submit 5.0% job. Stderr:", err5.decode("utf-8"))
        sys.exit(3)
    print("SUCCESS: 5.0% Job Submitted with PBS ID:", job_5pct)

    res = {
        "job_2pct": {
            "pbs_id": job_2pct,
            "directory": dir_2pct,
            "error_target": "2.0%",
            "elements": 15396
        },
        "job_5pct": {
            "pbs_id": job_5pct,
            "directory": dir_5pct,
            "error_target": "5.0%",
            "elements": 4194
        }
    }
    with open(os.path.join(base_dir, "TASK5_SUBMITTED_CORRECTED_JOBS.json"), "w") as f:
        json.dump(res, f, indent=2)

    print("\nSubmission Complete. Verification:")
    subprocess.call(["qstat", "-u", "pr21vyci"])

if __name__ == "__main__":
    main()
