# -*- coding: utf-8 -*-
"""
scripts/remeshing/assemble_completed_full_run_summary.py
========================================================
Combines Cycles 0-48 with Fix 3 Cycles 49-56 to form the full completed run record.
Extracts independent Step 1 hold RF2 from .dat using regex whitespace matching,
computes hold force jump percentage for all cycles, updates per-cycle SUMMARY.json,
and generates METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json.
"""

import os
import re
import json

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
TARGET_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
RUN_DIR = r"D:\mc3_local\full_run"
HIST_PATH = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_SUMMARY.json")
OUT_PATH = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json")


def parse_dat_rf2(dat_path):
    """Extracts step1, peak, and terminal RF2 from Abaqus .dat file using regex to support variable whitespace."""
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


def main():
    with open(HIST_PATH, "r", encoding="utf-8") as f:
        hist_records = json.load(f)

    # Keep cycles 0 to 48 from hist_records
    completed_records = hist_records[:49]
    assert len(completed_records) == 49, "Expected 49 cycles (0 to 48), got %d" % len(completed_records)

    # Ensure Cycles 0-48 have step1_hold_jump_pct populated correctly
    for idx in range(1, len(completed_records)):
        rec = completed_records[idx]
        prev = completed_records[idx - 1]
        step1_f = rec.get("step1_rf2_kN")
        prev_term = prev.get("terminal_rf2_kN")
        if step1_f is not None and prev_term is not None and prev_term > 0:
            rec["step1_hold_jump_pct"] = round(((step1_f - prev_term) / prev_term) * 100.0, 4)
        else:
            rec["step1_hold_jump_pct"] = None

    # Ingest and update cycles 49 to 56
    for c in range(49, 57):
        p = os.path.join(TARGET_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        assert os.path.isfile(p), "Missing summary for cycle %d: %s" % (c, p)
        with open(p, "r", encoding="utf-8") as f:
            rec = json.load(f)

        # Parse .dat independently
        dat_p = os.path.join(TARGET_DIR, "PK_METHOD_C_CASE3_CYCLE%d.dat" % c)
        if not os.path.isfile(dat_p):
            dat_p = os.path.join(RUN_DIR, "PK_METHOD_C_CASE3_CYCLE%d.dat" % c)

        if os.path.isfile(dat_p):
            dat_data = parse_dat_rf2(dat_p)
            step1_rf2 = dat_data.get("step1_rf2")
            if step1_rf2 is not None:
                rec["step1_rf2_kN"] = round(step1_rf2, 6)

        prev_rec = completed_records[-1]
        prev_term_rf2 = prev_rec.get("terminal_rf2_kN")
        step1_rf2_val = rec.get("step1_rf2_kN")

        if step1_rf2_val is not None and prev_term_rf2 is not None and prev_term_rf2 > 0:
            hold_jump = round(((step1_rf2_val - prev_term_rf2) / prev_term_rf2) * 100.0, 4)
            rec["step1_hold_jump_pct"] = hold_jump
        else:
            rec["step1_hold_jump_pct"] = None

        # Write updated per-cycle summary back to TARGET_DIR and RUN_DIR
        with open(p, "w", encoding="utf-8") as f:
            json.dump(rec, f, indent=2)

        run_p = os.path.join(RUN_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        if os.path.isdir(RUN_DIR):
            with open(run_p, "w", encoding="utf-8") as f:
                json.dump(rec, f, indent=2)

        completed_records.append(rec)

    assert len(completed_records) == 57, "Expected 57 total cycles, got %d" % len(completed_records)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(completed_records, f, indent=2)

    print("Successfully assembled completed full run summary with %d cycles to %s" % (len(completed_records), OUT_PATH))

    # Print summary table
    print("\n| Cycle | u2_term (mm) | Tip (x, y) (mm) | Step1 RF2 (kN) | Hold Jump (%) | Term RF2 (kN) | Status | Total Elem |")
    print("|-------|--------------|-----------------|----------------|---------------|---------------|--------|------------|")
    for r in completed_records[45:]:
        tip_str = "(%.2f, %.2f)" % (r.get("tip_x", 0.0), r.get("tip_y", 0.0))
        rf1 = r.get("step1_rf2_kN")
        rf1_str = "%.6f" % rf1 if rf1 is not None else "N/A"
        hj = r.get("step1_hold_jump_pct")
        hj_str = "%+.2f%%" % hj if hj is not None else "N/A"
        rf2 = r.get("terminal_rf2_kN") or 0.0
        print("| %2d | %12.6f | %15s | %14s | %13s | %13.6f | %7s | %10d |" % (
            r["cycle_idx"],
            r.get("actual_terminal_u2") or 0.0,
            tip_str,
            rf1_str,
            hj_str,
            rf2,
            r.get("conv_status", "N/A"),
            r.get("mesh_total_elements", 0)
        ))


if __name__ == "__main__":
    main()
