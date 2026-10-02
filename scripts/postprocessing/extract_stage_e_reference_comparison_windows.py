#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract Largest Scientifically Valid Comparison Windows & Reference Comparison States:
1. Refined Target Baseline 1391277.mmaster02 (33.6k quads, h_min=0.002000 mm)
2. Coarsened Target Baseline 1391279.mmaster02 (8.2k quads, h_min=0.005000 mm)
"""

import os
import sys
import json
import numpy as np

def analyze_window(csv_path, label):
    data = np.genfromtxt(csv_path, delimiter=',', names=True)
    frames = data['Frame'].astype(int)
    step_times = data['StepTime']
    u1s = data['U1_mm']
    rf1s = data['RF1_kN']
    dmaxs = data['d_max']
    
    target_handoff_u1 = 0.01051289
    h_idx = int(np.argmin(np.abs(u1s - target_handoff_u1)))
    
    peak_idx = int(np.argmax(rf1s))
    
    # Extract states from handoff onwards
    post_handoff_states = []
    for i in range(h_idx, len(frames)):
        post_handoff_states.append({
            "frame": int(frames[i]),
            "step_time": float(step_times[i]),
            "u1_mm": float(u1s[i]),
            "rf1_kN": float(rf1s[i]),
            "rf1_N": float(rf1s[i] * 1000.0),
            "d_max": float(dmaxs[i]),
            "is_handoff": (i == h_idx),
            "is_peak": (i == peak_idx),
            "is_terminal": (i == len(frames) - 1)
        })
        
    return {
        "label": label,
        "total_frames": len(frames),
        "valid_comparison_window": {
            "u1_start_mm": float(u1s[0]),
            "u1_end_mm": float(u1s[-1]),
            "step_time_start": float(step_times[0]),
            "step_time_end": float(step_times[-1])
        },
        "handoff_state": {
            "frame": int(frames[h_idx]),
            "step_time": float(step_times[h_idx]),
            "u1_mm": float(u1s[h_idx]),
            "rf1_kN": float(rf1s[h_idx]),
            "d_max": float(dmaxs[h_idx])
        },
        "peak_state": {
            "frame": int(frames[peak_idx]),
            "step_time": float(step_times[peak_idx]),
            "u1_mm": float(u1s[peak_idx]),
            "rf1_kN": float(rf1s[peak_idx]),
            "d_max": float(dmaxs[peak_idx])
        },
        "terminal_state": {
            "frame": int(frames[-1]),
            "step_time": float(step_times[-1]),
            "u1_mm": float(u1s[-1]),
            "rf1_kN": float(rf1s[-1]),
            "d_max": float(dmaxs[-1])
        },
        "available_post_handoff_frames": len(post_handoff_states),
        "post_handoff_states": post_handoff_states
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    
    csv_ref = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/force_displacement_curve.csv")
    csv_coarse = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/force_displacement_curve.csv")
    
    res_ref = analyze_window(csv_ref, "Refined Baseline 1391277 (33.6k quads, h_min=0.002000 mm)")
    res_coarse = analyze_window(csv_coarse, "Coarsened Baseline 1391279 (8.2k quads, h_min=0.005000 mm)")
    
    print("================================================================================")
    print("SCIENTIFICALLY VALID COMPARISON WINDOWS FOR STAGE-E TRANSFER VALIDATION:")
    print("================================================================================")
    
    for r in [res_ref, res_coarse]:
        print("\n--- %s ---" % r["label"])
        print("  Total Converged Frames    : %d" % r["total_frames"])
        print("  Valid Comparison Window   : U1 = %.6f mm to %.6f mm" % (r["valid_comparison_window"]["u1_start_mm"], r["valid_comparison_window"]["u1_end_mm"]))
        print("  Handoff State (Frame %d)  : U1 = %.8f mm, RF1 = %.6f kN, d_max = %.6f" % (
            r["handoff_state"]["frame"], r["handoff_state"]["u1_mm"], r["handoff_state"]["rf1_kN"], r["handoff_state"]["d_max"]))
        print("  Peak State (Frame %d)     : U1 = %.8f mm, RF1 = %.6f kN, d_max = %.6f" % (
            r["peak_state"]["frame"], r["peak_state"]["u1_mm"], r["peak_state"]["rf1_kN"], r["peak_state"]["d_max"]))
        print("  Terminal State (Frame %d) : U1 = %.8f mm, RF1 = %.6f kN, d_max = %.6f" % (
            r["terminal_state"]["frame"], r["terminal_state"]["u1_mm"], r["terminal_state"]["rf1_kN"], r["terminal_state"]["d_max"]))
        print("  Post-Handoff Frames Avail : %d frames" % r["available_post_handoff_frames"])
        
    out_json = os.path.join(base_dir, "stage_e_reference_comparison_windows.json")
    with open(out_json, "w") as fp:
        json.dump({"refined_1391277": res_ref, "coarsened_1391279": res_coarse}, fp, indent=2)
    print("\nSaved comparison windows JSON to: %s" % out_json)

if __name__ == "__main__":
    main()
