# -*- coding: utf-8 -*-
"""
scripts/remeshing/extract_f1735_case2_odb_sdv.py
Ultra-fast Abaqus Python script using bulkDataBlocks to audit authentic field outputs:
- Extracts final frame elementwise SDV1 (phase field d) and SDV2 (history H)
- Audits damage bounds (0 <= d <= 1) across ALL 252 converged frames
- Audits damage irreversibility (Delta d >= -1e-6) across ALL 252 converged frames
- Audits history monotonicity (Delta H >= -1e-6) across ALL 252 converged frames
"""

import sys
import json
import numpy as np
from odbAccess import openOdb

def extract_all_sdv(odb_path, out_final_csv, out_summary_json):
    print("Opening ODB: %s" % odb_path)
    odb = openOdb(odb_path, readOnly=True)
    
    step_names = list(odb.steps.keys())
    print("Found steps: %s" % str(step_names))
    
    # Trackers across all frames
    global_min_d = 1.0e9
    global_max_d = -1.0e9
    global_min_delta_d = 1.0e9
    global_min_delta_h = 1.0e9
    
    total_d_lower_bound_violations = 0
    total_d_upper_bound_violations = 0
    total_d_irreversibility_violations = 0
    total_h_monotonicity_violations = 0
    
    frame_metrics = []
    
    prev_d_arr = None
    prev_h_arr = None
    
    final_d_dict = {}
    final_h_dict = {}
    
    total_frames_processed = 0
    
    for s_idx, s_name in enumerate(step_names):
        step = odb.steps[s_name]
        n_frames = len(step.frames)
        print("Processing step %s (%d frames)..." % (s_name, n_frames))
        
        for f_idx, frame in enumerate(step.frames):
            # Frame 0 is typically initial condition without field outputs
            if 'SDV1' not in frame.fieldOutputs:
                continue
                
            total_frames_processed += 1
            f_time = float(frame.frameValue)
            
            sdv1 = frame.fieldOutputs['SDV1']
            sdv2 = frame.fieldOutputs['SDV2']
            
            # Block 0: Triangles (665 elements, 1 IP each)
            b0_sdv1 = sdv1.bulkDataBlocks[0]
            b0_sdv2 = sdv2.bulkDataBlocks[0]
            b0_labels = b0_sdv1.elementLabels - 47930
            b0_d = b0_sdv1.data.flatten()
            b0_h = b0_sdv2.data.flatten()
            
            # Block 1: Quads (23,300 elements, 4 IPs each)
            b1_sdv1 = sdv1.bulkDataBlocks[1]
            b1_sdv2 = sdv2.bulkDataBlocks[1]
            b1_labels = b1_sdv1.elementLabels[::4] - 47930
            b1_d = b1_sdv1.data[::4].flatten()
            b1_h = b1_sdv2.data[::4].flatten()
            
            # Combine
            cur_labels = np.concatenate([b0_labels, b1_labels])
            cur_d = np.concatenate([b0_d, b1_d])
            cur_h = np.concatenate([b0_h, b1_h])
            
            min_d = float(np.min(cur_d))
            max_d = float(np.max(cur_d))
            
            if min_d < global_min_d: global_min_d = min_d
            if max_d > global_max_d: global_max_d = max_d
            
            # Check bounds (allowing tiny tolerance 1e-6 for numerical precision)
            n_below_0 = int(np.sum(cur_d < -1.0e-6))
            n_above_1 = int(np.sum(cur_d > 1.0 + 1.0e-6))
            
            total_d_lower_bound_violations += n_below_0
            total_d_upper_bound_violations += n_above_1
            
            n_ge_050 = int(np.sum(cur_d >= 0.50))
            n_ge_075 = int(np.sum(cur_d >= 0.75))
            n_ge_090 = int(np.sum(cur_d >= 0.90))
            n_ge_095 = int(np.sum(cur_d >= 0.95))
            
            min_del_d = 0.0
            n_irrev_viol = 0
            if prev_d_arr is not None:
                del_d = cur_d - prev_d_arr
                min_del_d = float(np.min(del_d))
                n_irrev_viol = int(np.sum(del_d < -1.0e-6))
                
                if min_del_d < global_min_delta_d:
                    global_min_delta_d = min_del_d
                total_d_irreversibility_violations += n_irrev_viol
                
                del_h = cur_h - prev_h_arr
                min_del_h = float(np.min(del_h))
                n_hist_viol = int(np.sum(del_h < -1.0e-6))
                if min_del_h < global_min_delta_h:
                    global_min_delta_h = min_del_h
                total_h_monotonicity_violations += n_hist_viol
                
            prev_d_arr = cur_d
            prev_h_arr = cur_h
            
            # Record sampled frames for reporting
            if f_idx % 10 == 0 or f_idx == n_frames - 1:
                frame_metrics.append({
                    "step": s_name,
                    "frame_idx": f_idx,
                    "time": f_time,
                    "min_d": min_d,
                    "max_d": max_d,
                    "n_below_0": n_below_0,
                    "n_above_1": n_above_1,
                    "n_ge_050": n_ge_050,
                    "n_ge_075": n_ge_075,
                    "n_ge_090": n_ge_090,
                    "n_ge_095": n_ge_095,
                    "min_delta_d": min_del_d,
                    "irrev_viol_count": n_irrev_viol
                })
                
            # If final frame of Step 2, store full elementwise arrays
            if s_idx == len(step_names) - 1 and f_idx == n_frames - 1:
                print("Extracting full final frame elementwise arrays...")
                for eid, d_val, h_val in zip(cur_labels, cur_d, cur_h):
                    final_d_dict[int(eid)] = float(d_val)
                    final_h_dict[int(eid)] = float(h_val)

    odb.close()
    
    print("Writing final frame CSV (%d physical elements)..." % len(final_d_dict))
    with open(out_final_csv, 'w') as f:
        f.write("physical_element_id,damage_d,history_h\n")
        for eid in sorted(final_d_dict.keys()):
            f.write("%d,%.8e,%.8e\n" % (eid, final_d_dict[eid], final_h_dict.get(eid, 0.0)))
            
    summary_results = {
        "odb_path": odb_path,
        "total_frames_audited": total_frames_processed,
        "total_physical_elements": len(final_d_dict),
        "global_damage_bounds": {
            "min_d": float(global_min_d),
            "max_d": float(global_max_d),
            "lower_bound_violations_count": total_d_lower_bound_violations,
            "upper_bound_violations_count": total_d_upper_bound_violations,
            "bounds_satisfied": (total_d_lower_bound_violations == 0 and total_d_upper_bound_violations == 0)
        },
        "global_damage_irreversibility": {
            "min_delta_d": float(global_min_delta_d),
            "irreversibility_violations_count": total_d_irreversibility_violations,
            "irreversibility_satisfied": (total_d_irreversibility_violations == 0)
        },
        "global_history_monotonicity": {
            "min_delta_h": float(global_min_delta_h),
            "monotonicity_violations_count": total_h_monotonicity_violations,
            "monotonicity_satisfied": (total_h_monotonicity_violations == 0)
        },
        "final_frame_damage_counts": {
            "count_d_ge_050": int(np.sum(np.array(list(final_d_dict.values())) >= 0.50)),
            "count_d_ge_075": int(np.sum(np.array(list(final_d_dict.values())) >= 0.75)),
            "count_d_ge_090": int(np.sum(np.array(list(final_d_dict.values())) >= 0.90)),
            "count_d_ge_095": int(np.sum(np.array(list(final_d_dict.values())) >= 0.95))
        },
        "sampled_frames_history": frame_metrics
    }
    
    with open(out_summary_json, 'w') as f:
        json.dump(summary_results, f, indent=2)
        
    print("Done! Summary written to %s" % out_summary_json)
    print("ALL FRAMES AUDIT: min_d = %.4e, max_d = %.4f, d_violations = %d" % (
        global_min_d, global_max_d, total_d_lower_bound_violations + total_d_upper_bound_violations))
    print("ALL FRAMES IRREVERSIBILITY: min_delta_d = %.4e, violations = %d" % (
        global_min_delta_d, total_d_irreversibility_violations))
    print("ALL FRAMES HISTORY MONOTONICITY: min_delta_h = %.4e, violations = %d" % (
        global_min_delta_h, total_h_monotonicity_violations))

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: abaqus python extract_f1735_case2_odb_sdv.py <odb_path> <out_final_csv> <out_summary_json>")
        sys.exit(1)
    extract_all_sdv(sys.argv[1], sys.argv[2], sys.argv[3])
