#!/usr/bin/env python3
"""
Mode-II Dual Validation Exact Scientific Extraction and Evaluation Tool:
Task ID: F218EVAL-M2-DUAL-VALIDATION-BATCH-INGESTION-AND-SCIENTIFIC-EVALUATION1

Evaluates:
  1. Job 1: M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7 (PBS: 1390042.mmaster02)
  2. Job 2: M2CORR_PK10R2_TOPOLOGY_CORRECTED (PBS: 1390043.mmaster02)
"""

import os
import sys
import re
import csv
import json
import math

def parse_dat_rp_reactions(dat_path):
    """
    Parses Node 99999 (RP) reactions and displacements from Abaqus .dat file across all steps.
    """
    if not os.path.exists(dat_path):
        return []

    records = []
    current_step = None
    current_inc = None
    current_time = None
    step_time = None

    # Regex patterns for .dat parsing
    step_pattern = re.compile(r"S T E P\s+(\d+)", re.IGNORECASE)
    inc_pattern = re.compile(r"INCREMENT\s+(\d+)\s+SUMMARY", re.IGNORECASE)
    time_pattern = re.compile(r"TIME COMPLETED IN THIS STEP\s+([\d\.E\+\-]+)", re.IGNORECASE)
    total_time_pattern = re.compile(r"TOTAL TIME COMPLETED\s+([\d\.E\+\-]+)", re.IGNORECASE)

    with open(dat_path, "r", errors="ignore") as f:
        lines = f.readlines()

    mode = None
    u_vals = {}
    rf_vals = {}

    for line in lines:
        s = line.strip()
        if not s:
            continue

        sm = step_pattern.search(s)
        if sm:
            current_step = int(sm.group(1))
            continue

        im = inc_pattern.search(s)
        if im:
            current_inc = int(im.group(1))
            continue

        tm = time_pattern.search(s)
        if tm:
            step_time = float(tm.group(1))
            continue

        ttm = total_time_pattern.search(s)
        if ttm:
            current_time = float(ttm.group(1))
            continue

        if "NODE OUTPUT" in s:
            mode = "NODE_TABLE"
            continue

        if mode == "NODE_TABLE":
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in s or "END OF FILE" in s:
                mode = None
                continue
            parts = s.split()
            if len(parts) >= 4:
                try:
                    nid = int(parts[0])
                    if nid == 99999: # RP Node
                        v1 = float(parts[1])
                        v2 = float(parts[2])
                        v3 = float(parts[3])
                        # Check header type from previous context or store generically
                        records.append({
                            "step": current_step,
                            "increment": current_inc,
                            "step_time": step_time,
                            "total_time": current_time,
                            "nid": nid,
                            "raw_parts": [float(p) for p in parts[1:]]
                        })
                except (ValueError, IndexError):
                    pass

    return records

def parse_sta_file_detailed(sta_path):
    if not os.path.exists(sta_path):
        return {"exists": False, "completed": False, "increments": []}

    completed = False
    incs = []
    with open(sta_path, "r") as f:
        for line in f:
            if "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line:
                completed = True
            parts = line.strip().split()
            if len(parts) >= 8:
                try:
                    s_num = int(parts[0])
                    inc_num = int(parts[1])
                    att_num = int(parts[2])
                    step_time = float(parts[7])
                    incs.append({
                        "step": s_num,
                        "inc": inc_num,
                        "att": att_num,
                        "step_time": step_time
                    })
                except (ValueError, IndexError):
                    pass

    return {
        "exists": True,
        "completed": completed,
        "total_increments": len(incs),
        "increments": incs
    }

def run_extraction():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    r7_dir = os.path.join(base_dir, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7")
    pk10r2_dir = os.path.join(base_dir, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED")

    print("================================================================================")
    print("MODE-II DUAL VALIDATION SCIENTIFIC INGESTION & EVALUATION")
    print("================================================================================")

    # 1. Evaluate Job 1: R7
    print("\n--- 1. JOB 1: M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7 (1390042.mmaster02) ---")
    r7_sta = os.path.join(r7_dir, "M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.sta")
    r7_sta_info = parse_sta_file_detailed(r7_sta)
    print(f"STA File Completed: {r7_sta_info['completed']}, Total Incs: {r7_sta_info['total_increments']}")

    # 2. Evaluate Job 2: PK10R2
    print("\n--- 2. JOB 2: M2CORR_PK10R2_TOPOLOGY_CORRECTED (1390043.mmaster02) ---")
    pk10r2_sta = os.path.join(pk10r2_dir, "M2CORR_PK10R2_TOPOLOGY_CORRECTED.sta")
    pk10r2_sta_info = parse_sta_file_detailed(pk10r2_sta)
    print(f"STA File Completed: {pk10r2_sta_info['completed']}, Total Incs: {pk10r2_sta_info['total_increments']}")

if __name__ == "__main__":
    run_extraction()
