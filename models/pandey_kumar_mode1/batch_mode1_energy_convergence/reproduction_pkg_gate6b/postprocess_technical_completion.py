"""
postprocess_technical_completion.py
Deterministic technical-completion and log auditor for Abaqus UEL diagnostic jobs.
"""
import os
import sys
import json
import re

def audit_technical_completion(sta_path, msg_path=None, dat_path=None, csv_paths=None):
    results = {
        "status": "UNKNOWN",
        "steps_completed": 0,
        "total_increments": 0,
        "total_cutbacks": 0,
        "total_iterations": 0,
        "step_details": [],
        "warnings": [],
        "errors": [],
        "persisted_csvs": {}
    }
    
    if not os.path.exists(sta_path):
        results["status"] = "FAIL_MISSING_STA"
        results["errors"].append(f"Status file not found: {sta_path}")
        return results

    with open(sta_path, "r", encoding="utf-8", errors="ignore") as f:
        sta_lines = f.readlines()

    inc_count = 0
    cutback_count = 0
    current_step = 0
    completed_step_times = {}

    for line in sta_lines:
        line_s = line.strip()
        if not line_s or line_s.startswith("SUMMARY") or line_s.startswith("STEP"):
            continue
        parts = line_s.split()
        if len(parts) >= 6 and parts[0].isdigit() and parts[1].isdigit():
            step_id = int(parts[0])
            inc_id = int(parts[1])
            att_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
            inc_count += 1
            if att_id > 1:
                cutback_count += (att_id - 1)
            current_step = step_id
            try:
                step_time = float(parts[5]) if len(parts) > 5 else 0.0
                completed_step_times[step_id] = step_time
            except ValueError:
                pass
        elif "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in line:
            results["status"] = "SUCCESS_COMPLETED"
        elif "THE ANALYSIS HAS NOT BEEN COMPLETED" in line:
            results["status"] = "ABORTED"

    results["total_increments"] = inc_count
    results["total_cutbacks"] = cutback_count
    results["steps_completed"] = len(completed_step_times)
    results["completed_step_times"] = completed_step_times

    if results["status"] == "UNKNOWN":
        if results["steps_completed"] >= 2 and completed_step_times.get(2, 0.0) >= 1.0:
            results["status"] = "SUCCESS_COMPLETED"
        else:
            results["status"] = "INCOMPLETE"

    # Check diagnostic CSVs
    if csv_paths:
        for name, p in csv_paths.items():
            if os.path.exists(p):
                results["persisted_csvs"][name] = {
                    "exists": True,
                    "size_bytes": os.path.getsize(p)
                }
            else:
                results["persisted_csvs"][name] = {
                    "exists": False,
                    "size_bytes": 0
                }

    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python postprocess_technical_completion.py <path_to_sta> [path_to_msg]")
        sys.exit(1)
    sta_file = sys.argv[1]
    res = audit_technical_completion(sta_file)
    print(json.dumps(res, indent=2))
