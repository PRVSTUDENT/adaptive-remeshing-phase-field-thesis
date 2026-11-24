# -*- coding: utf-8 -*-
"""
scripts/remeshing/assemble_completed_full_run_summary.py
========================================================
Combines Cycles 0-48 (pre-arrest progression) with Fix 3 Cycles 49-56 (post-hole snap-through
and complete specimen separation) to form the full completed run record.
"""

import os
import json

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
TARGET_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
HIST_PATH = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_SUMMARY.json")
OUT_PATH = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json")

def main():
    with open(HIST_PATH, "r", encoding="utf-8") as f:
        hist_records = json.load(f)

    # Keep cycles 0 to 48 from hist_records
    completed_records = hist_records[:49]
    assert len(completed_records) == 49, "Expected 49 cycles (0 to 48), got %d" % len(completed_records)

    # Ingest cycles 49 to 56
    for c in range(49, 57):
        p = os.path.join(TARGET_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        assert os.path.isfile(p), "Missing summary for cycle %d: %s" % (c, p)
        with open(p, "r", encoding="utf-8") as f:
            rec = json.load(f)
        completed_records.append(rec)

    assert len(completed_records) == 57, "Expected 57 total cycles, got %d" % len(completed_records)

    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(completed_records, f, indent=2)

    print("Successfully assembled completed full run summary with %d cycles to %s" % (len(completed_records), OUT_PATH))

    # Print summary table
    print("\n| Cycle | u2_term (mm) | Tip (x, y) (mm) | dist_hole (mm) | d_max | Far-side d_max | RF2 (kN) | Status | Total Elem |")
    print("|-------|--------------|-----------------|----------------|-------|----------------|----------|--------|------------|")
    for r in completed_records[45:]:
        tip_str = "(%.2f, %.2f)" % (r.get("tip_x", 0.0), r.get("tip_y", 0.0))
        rf2 = r.get("terminal_rf2_kN") or r.get("step1_rf2_kN") or 0.0
        print("| %2d | %12.6f | %15s | %14.4f | %5.4f | %14.4f | %8.6f | %7s | %10d |" % (
            r["cycle_idx"],
            r.get("actual_terminal_u2") or 0.0,
            tip_str,
            r.get("dist_to_hole_boundary_mm", 0.0),
            r.get("d_max", 0.0),
            r.get("far_side_d_max", 0.0),
            rf2,
            r.get("conv_status", "N/A"),
            r.get("mesh_total_elements", 0)
        ))

if __name__ == "__main__":
    main()
