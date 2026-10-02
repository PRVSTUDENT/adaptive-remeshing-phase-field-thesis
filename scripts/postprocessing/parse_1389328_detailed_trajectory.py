#!/usr/bin/env python3
"""
Detailed Incremental Trajectory and Fracture Analysis for Job 1389328.mmaster02 (M2STATE_FRACFIX_RESTART2R14)
Task ID: F113STATE-M2-RESTART2-R2R14-EVALUATION-AND-VALIDATION1
"""

import sys
import re
import json
import csv
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
EVIDENCE_DIR = ROOT / "runs/hpc/mode_ii_state_transfer/evidence/1389328.mmaster02"
DAT_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R14.dat"
STA_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R14.sta"
MSG_PATH = EVIDENCE_DIR / "M2STATE_FRACFIX_RESTART2R14.msg"

def parse_trajectory():
    print("================================================================================")
    print("DETAILED TRAJECTORY PARSING & SCIENTIFIC EVALUATION: JOB 1389328.mmaster02")
    print("CANDIDATE: M2STATE_FRACFIX_RESTART2R14 (U1 = 0.030 -> 0.050 mm)")
    print("================================================================================")

    dat_lines = DAT_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    
    increments = []
    
    # Locate all increments by "INCREMENT <n> SUMMARY"
    inc_headers = []
    current_step = 1
    for i, l in enumerate(dat_lines):
        if "STEP    2" in l:
            current_step = 2
        if "INCREMENT" in l and "SUMMARY" in l:
            m = re.search(r"INCREMENT\s+(\d+)\s+SUMMARY", l)
            if m:
                inc_num = int(m.group(1))
                inc_headers.append((i, current_step, inc_num))

    print(f"Found {len(inc_headers)} increments in DAT file.")

    for idx, (line_idx, step_num, inc_num) in enumerate(inc_headers):
        next_line_idx = inc_headers[idx+1][0] if idx+1 < len(inc_headers) else len(dat_lines)
        inc_block = dat_lines[line_idx:next_line_idx]

        u1_rp = 0.0
        rf1_rp = 0.0
        rf1_bot = 0.0
        rf2_bot = 0.0
        d_max = 0.0
        h_max = 0.0

        in_node_table = False
        in_elem_table = False

        for l in inc_block:
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in l:
                in_node_table = True
                in_elem_table = False
                continue
            elif "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in l:
                in_elem_table = True
                in_node_table = False
                continue
            elif "MAXIMUM" in l:
                in_node_table = False
                in_elem_table = False
                continue

            if in_node_table:
                parts = l.split()
                if len(parts) >= 2 and parts[0] == "99999":
                    u1_rp = float(parts[1])
                    rf1_rp = float(parts[-1])
                elif len(parts) >= 6 and parts[0].isdigit():
                    nid = int(parts[0])
                    u3_d = float(parts[3])
                    if u3_d > d_max:
                        d_max = u3_d
                    if nid % 49 == 1:  # bottom node
                        rf1_bot += float(parts[4])
                        rf2_bot += float(parts[5])

            elif in_elem_table:
                parts = l.split()
                if len(parts) == 5 and parts[0].isdigit():
                    h_val = float(parts[4])
                    if h_val > h_max:
                        h_max = h_val

        # If u1_rp is 0.0 for step 2, calculate from step time if needed
        # But node 99999 U1 is printed directly
        global_rf1_res = rf1_rp + rf1_bot

        increments.append({
            "step": step_num,
            "inc": inc_num,
            "u1_mm": u1_rp,
            "rf1_kN": rf1_rp,
            "rf1_bottom_kN": rf1_bot,
            "global_rf1_res_kN": global_rf1_res,
            "rf2_bottom_res_kN": rf2_bot,
            "d_max": d_max,
            "h_max": h_max
        })

    # Save to CSV
    csv_path = EVIDENCE_DIR / "rf1_u1_trajectory.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "step", "inc", "u1_mm", "rf1_kN", "rf1_bottom_kN", "global_rf1_res_kN",
            "rf2_bottom_res_kN", "d_max", "h_max"
        ])
        writer.writeheader()
        writer.writerows(increments)

    print(f"\nSaved detailed trajectory ({len(increments)} points) to {csv_path.name}\n")

    # Print Table
    print(f"{'Step':<5} {'Inc':<5} {'U1 (mm)':<12} {'RF1 (kN)':<12} {'d_max':<10} {'H_max':<12} {'Global Res (kN)':<16}")
    print("-" * 76)
    for inc in increments:
        print(f"{inc['step']:<5} {inc['inc']:<5} {inc['u1_mm']:<12.6f} {inc['rf1_kN']:<12.6f} {inc['d_max']:<10.4f} {inc['h_max']:<12.6f} {inc['global_rf1_res_kN']:<16.2e}")

    # Peak Analysis
    rf1_vals = [inc["rf1_kN"] for inc in increments if inc["step"] == 2]
    u1_vals = [inc["u1_mm"] for inc in increments if inc["step"] == 2]
    d_vals = [inc["d_max"] for inc in increments if inc["step"] == 2]
    
    max_rf1 = max(rf1_vals)
    peak_idx = rf1_vals.index(max_rf1)
    peak_u1 = u1_vals[peak_idx]
    peak_d = d_vals[peak_idx]
    
    terminal_rf1 = rf1_vals[-1]
    terminal_u1 = u1_vals[-1]
    terminal_d = d_vals[-1]

    print("\n================================================================================")
    print("PEAK FORCE AND POST-PEAK SOFTENING ANALYSIS")
    print("================================================================================")
    print(f"Handoff State (Step 1, U1=0.030mm):  RF1 = {increments[0]['rf1_kN']:.6f} kN, d_max = {increments[0]['d_max']:.4f}")
    print(f"Peak Force State (Step 2 Inc {peak_idx+1}):     RF1 = {max_rf1:.6f} kN at U1 = {peak_u1:.6f} mm (d_max = {peak_d:.4f})")
    print(f"Terminal State   (Step 2 Inc {len(rf1_vals)}):    RF1 = {terminal_rf1:.6f} kN at U1 = {terminal_u1:.6f} mm (d_max = {terminal_d:.4f})")
    
    if peak_idx < len(rf1_vals) - 1:
        drop_kN = max_rf1 - terminal_rf1
        drop_pct = (max_rf1 - terminal_rf1) / max_rf1 * 100
        print(f"\nPost-Peak Softening Detected!")
        print(f"  Load Drop: {drop_kN:.6f} kN ({drop_pct:.2f}% reduction from peak)")
        print(f"  Fracture Complete: d_max reached {terminal_d:.4f}")
    else:
        print(f"\nNote: Peak force reached at terminal increment (monotonically rising).")

    return increments, max_rf1, peak_u1, terminal_rf1, terminal_u1, terminal_d

if __name__ == '__main__':
    parse_trajectory()
