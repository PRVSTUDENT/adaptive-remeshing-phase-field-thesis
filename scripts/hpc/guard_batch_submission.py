#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HPC Concurrency Guard for Batch Submissions:
Enforces that no more than 2 simultaneous RUNNING jobs ('R') exist for the project.
Available execution slots = max(0, 2 - running_count).
"""

import os
import sys
import json
import subprocess

MAX_CONCURRENT_RUNNING_JOBS = 2

def get_hpc_job_states(qstat_output_text):
    """
    Parses qstat text output and returns lists of running ('R'), queued ('Q'), and other jobs.
    """
    running = []
    queued = []
    other = []
    
    for line in qstat_output_text.splitlines():
        line = line.strip()
        if not line or line.startswith("Job id") or line.startswith("---"):
            continue
        parts = line.split()
        if len(parts) >= 5:
            job_id = parts[0]
            state = parts[4]
            if state == "R":
                running.append(job_id)
            elif state in ("Q", "H"):
                queued.append(job_id)
            else:
                other.append((job_id, state))
    return {
        "running": running,
        "queued": queued,
        "other": other,
        "running_count": len(running),
        "queued_count": len(queued)
    }

def calculate_submission_plan(running_count, approved_job_list, max_running=MAX_CONCURRENT_RUNNING_JOBS):
    """
    Deterministically calculates which jobs can be submitted directly into execution
    and which jobs must be submitted on hold (-h u) or queued.
    """
    available_slots = max(0, max_running - running_count)
    immediate_submit = approved_job_list[:available_slots]
    held_or_staged = approved_job_list[available_slots:]
    
    # Check if newly submitted jobs will cause a breach (excluding pre-existing over-capacity)
    new_running_total = min(max_running, running_count) + len(immediate_submit)
    plan_breaches = new_running_total > max_running
    
    return {
        "running_count": running_count,
        "available_slots": available_slots,
        "immediate_submit_count": len(immediate_submit),
        "immediate_submit_jobs": immediate_submit,
        "held_or_staged_count": len(held_or_staged),
        "held_or_staged_jobs": held_or_staged,
        "submission_plan_causes_breach": plan_breaches
    }

if __name__ == "__main__":
    mock_approved = ["Job_A", "Job_B", "Job_C"]
    for r in [0, 1, 2, 3]:
        plan = calculate_submission_plan(r, mock_approved)
        print("Existing R: %d -> Immediate: %s, Held: %s, Plan Causes Breach: %s" % (
            r, plan["immediate_submit_jobs"], plan["held_or_staged_jobs"], plan["submission_plan_causes_breach"]))
