# -*- coding: utf-8 -*-
"""
Generates summary JSONs and copies validation deliverables for Phase 1(b) Cycles 49-52.
"""

import os
import sys
import re
import json
import shutil

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, REPO_ROOT)
from tests.unit.test_method_c_framework_phase1a import parse_dat_rf2
from tests.unit.test_method_c_framework_phase1b import parse_inp_element_count

VAL_DIR = r"D:\mc3_local\validation_phase1b"
DEST_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "phase1b_wake_preserving_validation")
os.makedirs(DEST_DIR, exist_ok=True)

# Parse .sta for increments and cutbacks
def parse_sta(sta_path):
    if not os.path.isfile(sta_path):
        return {"step1_incs": 1, "step2_incs": 0, "total_incs": 1, "cutbacks": 0, "completed": False}
    step1_incs = 0
    step2_incs = 0
    cutbacks = 0
    completed = False
    with open(sta_path, "r") as f:
        for line in f:
            if "COMPLETED SUCCESSFULLY" in line.upper():
                completed = True
            parts = line.split()
            if len(parts) >= 6:
                try:
                    step = int(parts[0])
                    att = int(parts[2])
                    if step == 1:
                        step1_incs += 1
                    elif step == 2:
                        step2_incs += 1
                    if att > 1:
                        cutbacks += (att - 1)
                except (ValueError, IndexError):
                    continue
    return {
        "step1_incs": step1_incs,
        "step2_incs": step2_incs,
        "total_incs": step1_incs + step2_incs,
        "cutbacks": cutbacks,
        "completed": completed
    }

summaries = {}
nominal_u2 = {49: 0.54, 50: 0.55, 51: 0.56, 52: 0.57}

for c in [49, 50, 51, 52]:
    phys_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}_PHYS.inp")
    state_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}_state.json")
    dat_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}.dat")
    sta_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}.sta")
    msg_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}.msg")
    
    counts = parse_inp_element_count(phys_p)
    rf2_info = parse_dat_rf2(dat_p)
    sta_info = parse_sta(sta_p)
    
    with open(state_p, "r") as f:
        state = json.load(f)
        
    if c == 49:
        donor_rf2 = 2.31174
    else:
        prev_dat = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c-1}.dat")
        donor_rf2 = parse_dat_rf2(prev_dat)["terminal_rf2"]
        
    hold_jump = ((rf2_info["step1_rf2"] - donor_rf2) / donor_rf2) * 100.0 if rf2_info["step1_rf2"] else 0.0
    
    # Calculate distance to hole boundary: hole center (36.5, 51.0), radius 10.0
    import math
    dist_to_center = math.sqrt((state["tip_x"] - 36.5)**2 + (state["tip_y"] - 51.0)**2)
    dist_to_hole = dist_to_center - 10.0
    
    summary = {
        "cycle_idx": c,
        "job_name": f"PK_METHOD_C_CASE3_CYCLE{c}",
        "nominal_target_u2": nominal_u2[c],
        "actual_terminal_u2": rf2_info.get("terminal_u2"),
        "tip_x": round(state["tip_x"], 4),
        "tip_y": round(state["tip_y"], 4),
        "dist_to_hole_boundary_mm": round(dist_to_hole, 4),
        "d_max": round(state.get("max_damage", 1.0), 4),
        "step1_rf2_kN": round(rf2_info["step1_rf2"], 6) if rf2_info["step1_rf2"] else None,
        "peak_rf2_kN": round(rf2_info["peak_rf2"], 6) if rf2_info["peak_rf2"] else None,
        "terminal_rf2_kN": round(rf2_info["terminal_rf2"], 6) if rf2_info["terminal_rf2"] else None,
        "step1_incs": sta_info["step1_incs"],
        "step2_incs": sta_info["step2_incs"],
        "total_incs": sta_info["total_incs"],
        "cutbacks": sta_info["cutbacks"],
        "solver_completed": sta_info["completed"],
        "conv_status": "CONV" if sta_info["completed"] else "FAIL",
        "mesh_total_elements": counts["total"],
        "mesh_quads": counts["cpe4"],
        "mesh_tris": counts["cpe3"],
        "mesh_quad_pct": round(counts["quad_fraction"] * 100.0, 2),
        "step1_hold_jump_pct": round(hold_jump, 4),
        "framework_mode": "PHASE1B_WAKE_PRESERVING_DYNAMIC_ADVANCE"
    }
    
    sum_p = os.path.join(VAL_DIR, f"PK_METHOD_C_CASE3_CYCLE{c}_SUMMARY.json")
    with open(sum_p, "w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote {sum_p}")
    
    # Copy deliverables to repo folder
    for fname in [f"PK_METHOD_C_CASE3_CYCLE{c}_SUMMARY.json",
                  f"PK_METHOD_C_CASE3_CYCLE{c}_state.json",
                  f"PK_METHOD_C_CASE3_CYCLE{c}.sta",
                  f"PK_METHOD_C_CASE3_CYCLE{c}.dat",
                  f"PK_METHOD_C_CASE3_CYCLE{c}.msg"]:
        src = os.path.join(VAL_DIR, fname)
        dst = os.path.join(DEST_DIR, fname)
        if os.path.isfile(src):
            shutil.copy2(src, dst)
            print(f"Copied {fname} -> {DEST_DIR}")

print("All Phase 1b validation summaries generated and copied successfully.")
