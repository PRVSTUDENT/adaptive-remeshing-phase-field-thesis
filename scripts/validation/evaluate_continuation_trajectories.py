#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Rigorous evaluation of Step 4 (CONTINUATION) trajectories:
- Tracks physical U1 monotonically from RP node (Node 12383 for Native, Node 99999 for Stage-D)
- Tracks signed RP RF1 (the authoritative external shear load applied to the specimen)
- Tracks signed bottom clamped boundary reaction force sum
- Tracks primary nodal d_max and process-zone evolution
- Compares matched physical U1 points strictly within the continuation step
"""

from odbAccess import openOdb
import os
import sys
import json
import csv

def evaluate_continuation():
    h1_path = "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    ctrl_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb"
    trans_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb"

    def get_continuation_frames(odb_path, rp_id):
        odb = openOdb(odb_path, readOnly=True)
        inst = odb.rootAssembly.instances['PART-1-1'] if 'PART-1-1' in odb.rootAssembly.instances else odb.rootAssembly.instances[list(odb.rootAssembly.instances.keys())[0]]
        
        bot_nids = set()
        for n in inst.nodes:
            if abs(n.coordinates[1] - 0.0) < 1e-4 and n.label != rp_id:
                bot_nids.add(n.label)
                
        frames = []
        if 'CONTINUATION' in odb.steps:
            step = odb.steps['CONTINUATION']
            for f_idx, f in enumerate(step.frames):
                inc_num = f.incrementNumber
                step_time = float(f.frameValue)
                
                rp_u1 = 0.0
                max_u1 = 0.0
                d_max = 0.0
                if 'U' in f.fieldOutputs:
                    for v in f.fieldOutputs['U'].values:
                        if v.nodeLabel == rp_id:
                            rp_u1 = float(v.data[0])
                        if float(v.data[0]) > max_u1:
                            max_u1 = float(v.data[0])
                        if len(v.data) >= 3 and float(v.data[2]) > d_max:
                            d_max = float(v.data[2])
                            
                phys_u1 = rp_u1 if rp_u1 > 0.0 else max_u1
                
                rp_rf1 = 0.0
                bot_rf1_sum = 0.0
                if 'RF' in f.fieldOutputs:
                    for v in f.fieldOutputs['RF'].values:
                        if v.nodeLabel == rp_id:
                            rp_rf1 = float(v.data[0])
                        elif v.nodeLabel in bot_nids:
                            bot_rf1_sum += float(v.data[0])
                            
                frames.append({
                    'frame_idx': f_idx,
                    'increment': inc_num,
                    'step_time': step_time,
                    'phys_u1': phys_u1,
                    'rp_rf1': rp_rf1,
                    'bot_rf1_sum': bot_rf1_sum,
                    'd_max': d_max
                })
        odb.close()
        return frames

    frames_ctrl = get_continuation_frames(ctrl_path, rp_id=12383)
    frames_trans = get_continuation_frames(trans_path, rp_id=99999)
    
    print("=== EVALUATION OF STEP 4 (CONTINUATION) TRAJECTORIES ===")
    print("Native Control Continuation Frames: %d" % len(frames_ctrl))
    print("Stage-D Transfer Continuation Frames: %d" % len(frames_trans))
    
    # 1. Monotonicity & Extrema
    print("\n--- 1. FIRST, PEAK, AND LAST CONVERGED CONTINUATION FRAMES ---")
    
    def print_frame_summary(name, frames):
        f_first = frames[0]
        f_last = frames[-1]
        f_peak_rp = max(frames, key=lambda x: x['rp_rf1'])
        f_peak_bot = max(frames, key=lambda x: abs(x['bot_rf1_sum']))
        print("%s:" % name)
        print("  First Frame (Inc %d): Phys U1 = %.6f mm | RP RF1 = %.6f kN | Bot RF1 = %.6f kN | d_max = %.6f" % (
            f_first['increment'], f_first['phys_u1'], f_first['rp_rf1'], f_first['bot_rf1_sum'], f_first['d_max']))
        print("  Peak RP Load (Inc %d): Phys U1 = %.6f mm | RP RF1 = %.6f kN | Bot RF1 = %.6f kN | d_max = %.6f" % (
            f_peak_rp['increment'], f_peak_rp['phys_u1'], f_peak_rp['rp_rf1'], f_peak_rp['bot_rf1_sum'], f_peak_rp['d_max']))
        print("  Peak Bot Load (Inc %d): Phys U1 = %.6f mm | RP RF1 = %.6f kN | Bot RF1 = %.6f kN | d_max = %.6f" % (
            f_peak_bot['increment'], f_peak_bot['phys_u1'], f_peak_bot['rp_rf1'], f_peak_bot['bot_rf1_sum'], f_peak_bot['d_max']))
        print("  Last Converged (Inc %d): Phys U1 = %.6f mm | RP RF1 = %.6f kN | Bot RF1 = %.6f kN | d_max = %.6f" % (
            f_last['increment'], f_last['phys_u1'], f_last['rp_rf1'], f_last['bot_rf1_sum'], f_last['d_max']))
        return f_first, f_peak_rp, f_last

    f1_c, peak_c, end_c = print_frame_summary("Native Bounded Control (1390278)", frames_ctrl)
    print("")
    f1_t, peak_t, end_t = print_frame_summary("Stage-D Nonmatching Transfer (1390279)", frames_trans)
    
    # 2. Corrected Common-Interval Matched Displacement Comparison
    print("\n--- 2. CORRECTED MATCHED DISPLACEMENT COMPARISON OVER COMMON INTERVAL ---")
    u_start = max(f1_c['phys_u1'], f1_t['phys_u1'])
    u_end = min(end_c['phys_u1'], end_t['phys_u1'])
    print("Common Physical U1 Domain: [%.6f mm, %.6f mm]" % (u_start, u_end))
    
    def interpolate_cont(frames, u_target):
        for i in range(len(frames)-1):
            u_a, u_b = frames[i]['phys_u1'], frames[i+1]['phys_u1']
            if (u_a <= u_target <= u_b) or (u_b <= u_target <= u_a):
                frac = (u_target - u_a) / (u_b - u_a) if abs(u_b - u_a) > 1e-12 else 0.0
                rp_interp = frames[i]['rp_rf1'] + frac * (frames[i+1]['rp_rf1'] - frames[i]['rp_rf1'])
                bot_interp = frames[i]['bot_rf1_sum'] + frac * (frames[i+1]['bot_rf1_sum'] - frames[i]['bot_rf1_sum'])
                d_interp = frames[i]['d_max'] + frac * (frames[i+1]['d_max'] - frames[i]['d_max'])
                return rp_interp, bot_interp, d_interp
        return frames[-1]['rp_rf1'], frames[-1]['bot_rf1_sum'], frames[-1]['d_max']

    n_pts = 10
    du = (u_end - u_start) / (n_pts - 1)
    
    print("\nA. Reference Point Reaction Force (Authoritative External Shear Load):")
    print("%-12s | %-16s | %-16s | %-12s | %-12s | %-12s" % (
        "Phys U1 mm", "Native RP RF1 kN", "Stage-D RP RF1", "RP Diff %", "Native d_max", "Stage-D d_max"))
    print("-" * 88)
    
    for k in range(n_pts):
        u_k = u_start + k * du
        rp_c, bot_c, d_c = interpolate_cont(frames_ctrl, u_k)
        rp_t, bot_t, d_t = interpolate_cont(frames_trans, u_k)
        diff_rp = (rp_t - rp_c) / rp_c * 100.0 if rp_c != 0 else 0.0
        print("%-12.6f | %+16.6f | %+16.6f | %+11.2f%% | %-12.6f | %-12.6f" % (
            u_k, rp_c, rp_t, diff_rp, d_c, d_t))
            
    print("\nB. Bottom Clamped Boundary Reaction Sum:")
    print("%-12s | %-16s | %-16s | %-12s" % (
        "Phys U1 mm", "Native Bot RF1", "Stage-D Bot RF1", "Bot Diff %"))
    print("-" * 65)
    for k in range(n_pts):
        u_k = u_start + k * du
        rp_c, bot_c, d_c = interpolate_cont(frames_ctrl, u_k)
        rp_t, bot_t, d_t = interpolate_cont(frames_trans, u_k)
        diff_bot = (abs(bot_t) - abs(bot_c)) / abs(bot_c) * 100.0 if bot_c != 0 else 0.0
        print("%-12.6f | %+16.6f | %+16.6f | %+11.2f%%" % (
            u_k, bot_c, bot_t, diff_bot))

if __name__ == "__main__":
    evaluate_continuation()
